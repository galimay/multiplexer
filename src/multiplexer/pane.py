import asyncio

from blessed import Terminal

from . import styles


class Pane:
    """
    Represents a single pane running a command.
    """

    def __init__(
        self,
        command: str,
        terminal: Terminal,
        x: int = 0,
        y: int = 0,
        width: int = 80,
        height: int = 24,
        box=None,
        color=None,
    ):
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

    async def start(self) -> None:
        """
        Start the command in this pane.
        """
        self.running = True
        self.process = await asyncio.create_subprocess_shell(
            self.command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            stdin=asyncio.subprocess.PIPE,
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
            try:
                await self.task
            except asyncio.CancelledError:
                pass

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
                # Keep only the last N lines
                if len(self.output) > self.height - 2:  # Leave space for border
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

    def colorize(self, text):
        if self.color:
            return self.color(text)
        return text

    def render(self, selected: bool = False) -> str:
        """
        Render the pane's content.

        Returns:
            The rendered string for this pane.
        """
        content = []

        # Choose box style based on selection
        box_style = styles.double if selected else self.box

        # Prepare title (command) line
        title = f" {self.command} "[: max(0, self.width - 2)]
        title = title.center(max(0, self.width - 2))

        # Draw top border with title
        if selected:
            border_color = self.terminal.bold_yellow
        else:
            border_color = self.colorize
        top = border_color(
            box_style.top_left
            + box_style.horizontal * (self.width - 2)
            + box_style.top_right,
        )
        content.append(self.terminal.move(self.y, self.x) + top)

        # Draw content area
        for i in range(1, self.height - 1):
            line = self.terminal.move(self.y + i, self.x)
            if i == 1:
                line_content = title
                line += (
                    border_color(box_style.vertical)
                    + line_content
                    + border_color(box_style.vertical)
                )
            elif i - 2 < len(self.output):
                line_content = self.output[i - 2][: self.width - 2]
                line += (
                    border_color(box_style.vertical)
                    + line_content.ljust(self.width - 2)
                    + border_color(box_style.vertical)
                )
            else:
                line += (
                    border_color(box_style.vertical)
                    + " " * (self.width - 2)
                    + border_color(box_style.vertical)
                )
            content.append(line)

        # Draw bottom border
        bottom = border_color(
            box_style.bottom_left
            + box_style.horizontal * (self.width - 2)
            + box_style.bottom_right,
        )
        content.append(self.terminal.move(self.y + self.height - 1, self.x) + bottom)

        return "\n".join(content)
