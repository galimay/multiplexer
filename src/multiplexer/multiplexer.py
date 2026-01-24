import threading
import time
from typing import List, Optional
from blessed import Terminal
from .pane import Pane
from .layout import LayoutManager


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

    def run_command(self, command: str) -> None:
        """
        Run a command in a new pane.

        Args:
            command: The command to run.
        """
        pane = Pane(command, self.terminal)
        self.panes.append(pane)
        self.layout_manager.update_layout(self.panes)

    def start(self) -> None:
        """
        Start the multiplexer, displaying all panes.
        """
        self.running = True
        for pane in self.panes:
            pane.start()
        self.thread = threading.Thread(target=self._render_loop)
        self.thread.start()

    def stop(self) -> None:
        """
        Stop the multiplexer and all panes.
        """
        self.running = False
        for pane in self.panes:
            pane.stop()
        if self.thread:
            self.thread.join()

    def _render_loop(self) -> None:
        """
        Main render loop to update the display.
        """
        with self.terminal.fullscreen(), self.terminal.cbreak():
            while self.running:
                self._render()
                time.sleep(0.1)  # Refresh rate

    def _render(self) -> None:
        """
        Render all panes to the terminal.
        """
        output = self.terminal.clear()
        for pane in self.panes:
            output += pane.render()
        print(output, end='')