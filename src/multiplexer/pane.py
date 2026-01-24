import subprocess
import threading
from typing import List, Optional
from blessed import Terminal


class Pane:
    """
    Represents a single pane running a command.
    """

    def __init__(self, command: str, terminal: Terminal, x: int = 0, y: int = 0, width: int = 80, height: int = 24, box=None, color=None):
        self.command = command
        self.terminal = terminal
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.process: Optional[subprocess.Popen] = None
        self.output: List[str] = []
        self.thread: Optional[threading.Thread] = None
        self.running = False
        self.box = box
        self.color = color

    def start(self) -> None:
        """
        Start the command in this pane.
        """
        self.running = True
        self.process = subprocess.Popen(
            self.command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        self.thread = threading.Thread(target=self._read_output)
        self.thread.start()

    def stop(self) -> None:
        """
        Stop the command in this pane.
        """
        self.running = False
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
        if self.thread:
            self.thread.join()

    def _read_output(self) -> None:
        """
        Read output from the subprocess and store it.
        """
        if self.process and self.process.stdout:
            for line in iter(self.process.stdout.readline, ''):
                if not self.running:
                    break
                self.output.append(line.rstrip())
                # Keep only the last N lines
                if len(self.output) > self.height - 2:  # Leave space for border
                    self.output.pop(0)

    def colorize(self, text):
        if self.color:
            return self.color(text)
        return text

    def render(self) -> str:
        """
        Render the pane's content.

        Returns:
            The rendered string for this pane.
        """
        content = []
        
        # Prepare title (command) line
        title = f" {self.command} "[: max(0, self.width - 2)]
        title = title.center(max(0, self.width - 2))

        # Draw top border with title
        top = self.colorize(self.box.top_left + self.box.horizontal * (self.width - 2) + self.box.top_right)
        content.append(self.terminal.move(self.y, self.x) + top)
        
        # Draw content area
        for i in range(1, self.height - 1):
            line = self.terminal.move(self.y + i, self.x)
            if i == 1:
                line_content = title
                line += self.colorize(self.box.vertical) + line_content + self.colorize(self.box.vertical)
            else:
                if i - 2 < len(self.output):
                    line_content = self.output[i - 2][:self.width - 2]
                    line += self.colorize(self.box.vertical) + line_content.ljust(self.width - 2) + self.colorize(self.box.vertical)
                else:
                    line += self.colorize(self.box.vertical) + ' ' * (self.width - 2) + self.colorize(self.box.vertical)
            content.append(line)
        
        # Draw bottom border
        bottom = self.colorize(self.box.bottom_left + self.box.horizontal * (self.width - 2) + self.box.bottom_right)
        content.append(self.terminal.move(self.y + self.height - 1, self.x) + bottom)

        return '\n'.join(content)