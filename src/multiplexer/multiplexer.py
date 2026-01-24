import threading
import time
from typing import List, Optional
from blessed import Terminal
from itertools import cycle
from .pane import Pane
from .layout import LayoutManager
from . import styles


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
                # detect terminal resize and update layout if changed
                width = getattr(self.terminal, 'width', self._prev_width)
                height = getattr(self.terminal, 'height', self._prev_height)
                if width != self._prev_width or height != self._prev_height:
                    self._prev_width, self._prev_height = width, height
                    self.layout_manager.update_layout(self.panes)

                # ensure layout is up-to-date every frame (safe and cheap)
                self.layout_manager.update_layout(self.panes)
                self._render()
                time.sleep(0.1)  # Refresh rate

    def _render(self) -> None:
        """
        Render all panes to the terminal.
        """
        # Clear screen and render panes
        output = self.terminal.clear()
        for pane in self.panes:
            output += pane.render()
        # Use print so that terminal control sequences are respected
        print(output, end='')