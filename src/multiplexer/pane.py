import asyncio
import contextlib
import os
from collections.abc import Callable

from blessed import Terminal

from . import styles
from .styles import Box


class Pane:
    """
    Represents a single pane running a command.
    """

    def __init__(  # noqa: PLR0913
        self,
        command: str,
        terminal: Terminal,
        x: int = 0,
        y: int = 0,
        width: int = 80,
        height: int = 24,
        box: Box | None = None,
        color: Callable[[str], str] | None = None,
    ) -> None:
        self.command = command
        self.terminal = terminal
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.process: asyncio.subprocess.Process | None = None
        self.output: list[str] = []
        self.task: asyncio.Task | None = None
        self.running = False
        self.box = box
        self.color = color
        self.finished = False
        self.exit_code: int | None = None
        self.input_buffer: str = ""

    @property
    def content_width(self) -> int:
        """Usable columns inside the border."""
        return max(0, self.width - 2)

    @property
    def content_height(self) -> int:
        """Usable rows inside the border (excludes title row on border + prompt row)."""
        return max(0, self.height - 3)

    async def start(self) -> None:
        """
        Start the command in this pane.
        """
        self.running = True
        env = os.environ.copy()
        env["COLUMNS"] = str(max(1, self.content_width))
        env["LINES"] = str(max(1, self.content_height))
        env.setdefault("TERM", "xterm-256color")
        self.process = await asyncio.create_subprocess_shell(
            self.command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            stdin=asyncio.subprocess.PIPE,
            env=env,
        )
        self.task = asyncio.create_task(self._read_output())

    async def stop(self) -> None:
        """
        Stop the command in this pane.
        """
        self.running = False
        if self.process and self.process.returncode is None:
            self.process.terminate()
            try:
                await asyncio.wait_for(self.process.wait(), timeout=5.0)
            except TimeoutError:
                self.process.kill()
        if self.task and not self.task.done():
            self.task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self.task

    async def _read_output(self) -> None:
        """
        Read output from the subprocess and store it.
        """
        if self.process and self.process.stdout:
            while self.running:
                line = await self.process.stdout.readline()
                if not line:
                    break
                self.output.append(line.decode("utf-8", errors="ignore").rstrip())
                # Keep only lines that fit the content area
                max_lines = max(1, self.height - 3)
                while len(self.output) > max_lines:
                    self.output.pop(0)
            # Check if process has finished
            if self.process.returncode is not None:
                self.finished = True
                self.exit_code = self.process.returncode

    async def send_input(self, input_str: str) -> None:
        """
        Send input to the pane's process.
        """
        if self.process and self.process.stdin and not self.finished:
            self.process.stdin.write(input_str.encode())
            await self.process.stdin.drain()

    def colorize(self, text: str) -> str:
        if self.color:
            return self.color(text)
        return text

    def _render_prompt(self, *, selected: bool, width: int) -> str:
        """Render the prompt bar content, padded/truncated to *width* columns."""
        raw = styles.PROMPT_PREFIX + (self.input_buffer + "█" if selected else "")
        return raw[:width].ljust(width)

    def render(self, *, selected: bool = False) -> str:
        """
        Render the pane's content.

        Layout (top→bottom):
          row 0            : top border with title embedded
          rows 1..height-3 : process output lines
          row height-2     : prompt bar
          row height-1     : bottom border

        Returns:
            The rendered string for this pane.
        """
        if self.width < 2 or self.height < 2:  # noqa: PLR2004
            return ""

        content: list[str] = []

        # Choose box style based on selection
        box_style = styles.double if selected else (self.box or styles.rounded)

        # Border colour: bold yellow for selected pane, pane colour otherwise
        border_color: Callable[[str], str] = (
            self.terminal.bold_yellow if selected else (self.color or (lambda s: s))
        )

        # --- Top border with title embedded ---
        title_text = f" {self.command} "
        inner_width = self.width - 2
        max_title = max(0, inner_width - 2)
        title_text = title_text[:max_title]
        dashes_total = inner_width - len(title_text)
        left_dashes = dashes_total // 2
        right_dashes = dashes_total - left_dashes
        top = border_color(
            box_style.top_left
            + box_style.horizontal * left_dashes
            + title_text
            + box_style.horizontal * right_dashes
            + box_style.top_right,
        )
        content.append(self.terminal.move(self.y, self.x) + top)  # type: ignore[arg-type]

        # --- Content rows + prompt bar ---
        content_rows = max(0, self.height - 3)
        for i in range(1, self.height - 1):
            line = self.terminal.move(self.y + i, self.x)  # type: ignore[arg-type]
            if i <= content_rows:
                # Process output line
                output_idx = i - 1
                line_content = (
                    self.output[output_idx][: self.width - 2]
                    if output_idx < len(self.output)
                    else ""
                )
                line += (
                    border_color(box_style.vertical)
                    + line_content.ljust(self.width - 2)
                    + border_color(box_style.vertical)
                )
            else:
                # Prompt bar (row height-2)
                prompt = self._render_prompt(selected=selected, width=self.width - 2)
                # Use string concatenation for styling — avoids calling ParameterizingString
                # (e.g. `dim`) with a string arg, which fails on some Windows terminals.
                if selected:
                    styled_prompt = (
                        str(self.terminal.bold) + prompt + str(self.terminal.normal)
                    )
                else:
                    styled_prompt = prompt
                line += (
                    border_color(box_style.vertical)
                    + styled_prompt
                    + border_color(box_style.vertical)
                )
            content.append(line)

        # --- Bottom border ---
        bottom = border_color(
            box_style.bottom_left
            + box_style.horizontal * (self.width - 2)
            + box_style.bottom_right,
        )
        content.append(self.terminal.move(self.y + self.height - 1, self.x) + bottom)  # type: ignore[arg-type]

        return "\n".join(content)
