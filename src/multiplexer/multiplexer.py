from __future__ import annotations

import asyncio
import contextlib
from itertools import cycle
from typing import TYPE_CHECKING, Any, cast

from blessed import Terminal

from . import styles
from .layout import LayoutManager
from .pane import Pane

if TYPE_CHECKING:
    import threading

# Set event loop policy for better performance
try:
    import uvloop

    uvloop.install()
except ImportError:
    try:
        import winuvloop

        winuvloop.install()
    except ImportError:
        pass  # Use default asyncio event loop

_PANE_LABEL_MAX_LEN = 16
_CMD_INFO_MAX_LEN = 12


class TerminalMultiplexer:
    """
    Main class for the terminal multiplexer.

    Manages multiple panes, each running a command, and handles the layout.
    """

    def __init__(self, terminal: Terminal | None = None):
        self.terminal = terminal or Terminal()
        self.panes: list[Pane] = []
        self.layout_manager = LayoutManager(self.terminal)
        self.running = False
        self.thread: threading.Thread | None = None
        # track terminal size to detect resize events
        self._prev_width = getattr(self.terminal, "width", 0)
        self._prev_height = getattr(self.terminal, "height", 0)
        self.box_style = styles.rounded
        self.color_cycle = cycle(
            [
                self.terminal.red,
                self.terminal.green,
                self.terminal.blue,
                self.terminal.magenta,
                self.terminal.cyan,
            ],
        )
        self.total_panes_created = 0
        self.last_finished_command: str | None = None
        self.last_exit_code: int | None = None
        self.selected_pane_index = 0

    def run_command(self, command: str) -> None:
        """
        Run a command in a new pane.

        Args:
            command: The command to run.
        """
        pane = Pane(
            command,
            self.terminal,
            box=self.box_style,
            color=next(self.color_cycle),
        )
        self.panes.append(pane)
        self.total_panes_created += 1
        self.layout_manager.update_layout(self.panes)

    async def start(self) -> None:
        """
        Start the multiplexer, displaying all panes.
        """
        self.running = True
        # Start all panes asynchronously
        await asyncio.gather(*[pane.start() for pane in self.panes])
        # Run the render loop
        await self._render_loop()

    async def stop(self) -> None:
        """
        Stop the multiplexer and all panes.
        """
        self.running = False
        await asyncio.gather(*[pane.stop() for pane in self.panes])

    async def _render_loop(self) -> None:
        """
        Main render loop to update the display.
        """
        with self.terminal.fullscreen(), self.terminal.cbreak():
            while self.running:
                # detect terminal resize and update layout if changed
                width = getattr(self.terminal, "width", self._prev_width)
                height = getattr(self.terminal, "height", self._prev_height)
                if width != self._prev_width or height != self._prev_height:
                    self._prev_width, self._prev_height = width, height
                    self.layout_manager.update_layout(self.panes)
                    # Trim each pane's output buffer to the new content height
                    for pane in self.panes:
                        ch = max(1, pane.height - 3)
                        while len(pane.output) > ch:
                            pane.output.pop(0)

                # Check for finished processes
                for pane in self.panes:
                    if (
                        not pane.finished
                        and pane.process
                        and pane.process.returncode is not None
                    ):
                        pane.finished = True
                        pane.exit_code = pane.process.returncode

                # Check for finished panes
                await self._cleanup_finished_panes()

                # Handle input
                await self._handle_input()

                # ensure layout is up-to-date every frame (safe and cheap)
                self.layout_manager.update_layout(self.panes)
                self._render()
                await asyncio.sleep(0.1)  # Refresh rate

    async def _handle_input(self) -> None:
        """
        Handle keyboard input.

        Printable characters are buffered in the selected pane's prompt bar.
        Enter commits the buffer to the process; Backspace edits it; Escape
        clears it.  Ctrl+C / Ctrl+D are forwarded directly to the process.
        Tab cycles focus between panes.
        """
        with contextlib.suppress(Exception):
            key = self.terminal.inkey(timeout=0.01)
            if key:
                if key.name == "KEY_TAB":
                    self.selected_pane_index = (
                        (self.selected_pane_index + 1) % len(self.panes)
                        if self.panes
                        else 0
                    )
                elif key.name == "MOUSE":
                    key_any = cast("Any", key)
                    if key_any.button == 1:  # left click
                        mouse_x, mouse_y = key_any.x - 1, key_any.y - 1
                        for i, pane in enumerate(self.panes):
                            if (
                                pane.x <= mouse_x < pane.x + pane.width
                                and pane.y <= mouse_y < pane.y + pane.height
                            ):
                                self.selected_pane_index = i
                                break
                elif self.panes:
                    await self._process_pane_key_input(key)

    async def _process_pane_key_input(self, key: Any) -> None:
        """Route a keystroke to the selected pane's prompt buffer or process."""
        selected = self.panes[self.selected_pane_index]
        key_str = str(key)
        if key.name in ("KEY_ENTER",) or key_str in ("\n", "\r"):
            await selected.send_input(selected.input_buffer + "\n")
            selected.input_buffer = ""
        elif key.name in ("KEY_BACKSPACE", "KEY_DELETE") or key_str == "\x7f":
            selected.input_buffer = selected.input_buffer[:-1]
        elif key.name == "KEY_ESCAPE" or key_str == "\x1b":
            selected.input_buffer = ""
        elif key_str in ("\x03", "\x04"):  # Ctrl+C / Ctrl+D — send directly
            await selected.send_input(key_str)
        elif not key.is_sequence and len(key_str) == 1:
            selected.input_buffer += key_str

    async def _cleanup_finished_panes(self) -> None:
        """
        Remove finished panes and update status.
        """
        finished_panes = [pane for pane in self.panes if pane.finished]
        for pane in finished_panes:
            index = self.panes.index(pane)
            self.panes.remove(pane)
            self.last_finished_command = pane.command
            self.last_exit_code = pane.exit_code
            await pane.stop()  # Ensure stopped
            if self.selected_pane_index >= len(self.panes) and self.panes:
                self.selected_pane_index = len(self.panes) - 1
            elif index <= self.selected_pane_index and self.selected_pane_index > 0:
                self.selected_pane_index -= 1

    def _render(self) -> None:
        """
        Render all panes to the terminal.
        """
        # Clear screen and render panes
        output = self.terminal.mouse + self.terminal.clear()
        for i, pane in enumerate(self.panes):
            output += pane.render(selected=(i == self.selected_pane_index))

        # Render status bar
        status_line = self._get_status_line()
        output += self.terminal.move(self.terminal.height - 1, 0) + status_line  # type: ignore[arg-type]

        # Use print so that terminal control sequences are respected
        self.terminal.stream.write(output)
        self.terminal.stream.flush()

    def _get_status_line(self) -> str:
        """
        Generate the status bar line.
        """
        width = self.terminal.width

        # Pane list with selection indicator
        pane_parts: list[str] = []
        for i, pane in enumerate(self.panes):
            marker = "●" if i == self.selected_pane_index else "○"
            label = (
                pane.command
                if len(pane.command) <= _PANE_LABEL_MAX_LEN
                else pane.command[: _PANE_LABEL_MAX_LEN - 3] + "…"
            )
            pane_parts.append(f" {marker} {label}")
        panes_str = "  ".join(pane_parts)

        # Last finished command info
        if self.last_finished_command:
            cmd = self.last_finished_command
            if len(cmd) > _CMD_INFO_MAX_LEN:
                cmd = cmd[: _CMD_INFO_MAX_LEN - 3] + "…"
            last_str = f" │ ✓ {cmd} [{self.last_exit_code}]"
        else:
            last_str = ""

        hints = "  TAB:▶next  ENTER:send  ESC:clear  "

        left = panes_str + last_str
        # Right-align hints, fill gap with spaces
        gap = width - len(left) - len(hints)
        status = left + " " * gap + hints if gap >= 1 else (left + " " + hints)[:width]

        status = status[:width].ljust(width)
        return self.terminal.reverse(status)
