import math

from blessed import Terminal

from .pane import Pane

MAX_TWO_PANES = 2
MAX_GRID_PANES = 4


class LayoutManager:
    """
    Manages the layout of panes in the terminal.
    """

    def __init__(self, terminal: Terminal, status_bar_height: int = 1):
        self.terminal = terminal
        self.status_bar_height = status_bar_height

    def update_layout(self, panes: list[Pane]) -> None:
        """
        Update the layout of all panes based on the number of panes and terminal size.

        Args:
            panes: List of panes to layout.
        """
        if not panes:
            return

        term_width, term_height = (
            self.terminal.width,
            self.terminal.height - self.status_bar_height,
        )

        num_panes = len(panes)
        rows = math.ceil(math.sqrt(num_panes))
        columns = math.ceil(num_panes / rows)
        pane_width = term_width // columns
        pane_height = term_height // rows
        for i, pane in enumerate(panes):
            row = i // columns
            col = i % columns
            pane.x = col * pane_width
            pane.y = row * pane_height
            pane.width = (
                pane_width if col < columns - 1 else term_width - col * pane_width
            )
            pane.height = (
                pane_height if row < rows - 1 else term_height - row * pane_height
            )
