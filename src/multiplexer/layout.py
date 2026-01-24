from typing import List
from blessed import Terminal
from .pane import Pane


class LayoutManager:
    """
    Manages the layout of panes in the terminal.
    """

    def __init__(self, terminal: Terminal, status_bar_height: int = 1):
        self.terminal = terminal
        self.status_bar_height = status_bar_height

    def update_layout(self, panes: List[Pane]) -> None:
        """
        Update the layout of all panes based on the number of panes and terminal size.

        Args:
            panes: List of panes to layout.
        """
        if not panes:
            return

        term_width, term_height = self.terminal.width, self.terminal.height - self.status_bar_height

        num_panes = len(panes)

        if num_panes == 1:
            # Single pane takes full screen
            panes[0].x = 0
            panes[0].y = 0
            panes[0].width = term_width
            panes[0].height = term_height
        elif num_panes == 2:
            # Split vertically
            half_width = term_width // 2
            panes[0].x = 0
            panes[0].y = 0
            panes[0].width = half_width
            panes[0].height = term_height
            panes[1].x = half_width
            panes[1].y = 0
            panes[1].width = term_width - half_width
            panes[1].height = term_height
        elif num_panes <= 4:
            # 2x2 grid
            half_width = term_width // 2
            half_height = term_height // 2
            positions = [
                (0, 0, half_width, half_height),
                (half_width, 0, term_width - half_width, half_height),
                (0, half_height, half_width, term_height - half_height),
                (half_width, half_height, term_width - half_width, term_height - half_height),
            ]
            for i, pane in enumerate(panes):
                pane.x, pane.y, pane.width, pane.height = positions[i]
        else:
            # For more panes, implement a more complex layout or stack them
            # For simplicity, stack vertically
            pane_height = term_height // num_panes
            for i, pane in enumerate(panes):
                pane.x = 0
                pane.y = i * pane_height
                pane.width = term_width
                pane.height = pane_height if i < num_panes - 1 else term_height - i * pane_height