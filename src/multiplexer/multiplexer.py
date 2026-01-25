import asyncio
import threading
import time
from typing import List, Optional
from blessed import Terminal
from itertools import cycle
from .pane import Pane
from .layout import LayoutManager
from . import styles

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


class TerminalMultiplexer:
    """
    Main class for the terminal multiplexer.

    Manages multiple panes, each running a command, and handles the layout.
    """

    def __init__(self, terminal: Optional[Terminal] = None):
        self.terminal = terminal or Terminal()
        self.panes: List[Pane] = []
        self.layout_manager = LayoutManager(self.terminal)
        self.running = False
        self.thread: Optional[threading.Thread] = None
        # track terminal size to detect resize events
        self._prev_width = getattr(self.terminal, 'width', 0)
        self._prev_height = getattr(self.terminal, 'height', 0)
        self.box_style = styles.rounded
        self.color_cycle = cycle([
            self.terminal.red,
            self.terminal.green,
            self.terminal.blue,
            self.terminal.magenta,
            self.terminal.cyan,
        ])
        self.total_panes_created = 0
        self.last_finished_command = None
        self.last_exit_code = None
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
                width = getattr(self.terminal, 'width', self._prev_width)
                height = getattr(self.terminal, 'height', self._prev_height)
                if width != self._prev_width or height != self._prev_height:
                    self._prev_width, self._prev_height = width, height
                    self.layout_manager.update_layout(self.panes)

                # Check for finished processes
                for pane in self.panes:
                    if not pane.finished and pane.process and pane.process.returncode is not None:
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
        """
        try:
            key = self.terminal.inkey(timeout=0.01)
            if key:
                if key.name == 'KEY_TAB':
                    self.selected_pane_index = (self.selected_pane_index + 1) % len(self.panes) if self.panes else 0
                elif key.name == 'MOUSE' and key.button == 1:  # Left mouse click
                    # Mouse coordinates are 1-based, pane coordinates are 0-based
                    mouse_x, mouse_y = key.x - 1, key.y - 1
                    for i, pane in enumerate(self.panes):
                        if (pane.x <= mouse_x < pane.x + pane.width and
                            pane.y <= mouse_y < pane.y + pane.height):
                            self.selected_pane_index = i
                            break
                elif self.panes:
                    await self.panes[self.selected_pane_index].send_input(str(key))
        except:
            pass  # Ignore input errors

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
        output += self.terminal.move(self.terminal.height - 1, 0) + status_line

        # Use print so that terminal control sequences are respected
        self.terminal.stream.write(output)
        self.terminal.stream.flush()

    def _get_status_line(self) -> str:
        """
        Generate the status bar line.
        """
        width = self.terminal.width
        current_panes = len(self.panes)
        total_created = self.total_panes_created
        status = f"Panes: {current_panes}/{total_created}"
        if self.last_finished_command:
            status += f" | Last: {self.last_finished_command} (exit {self.last_exit_code})"
        # Truncate if too long
        if len(status) > width:
            status = status[:width]
        else:
            status = status.ljust(width)
        return self.terminal.reverse(status)  # Reverse video for status bar