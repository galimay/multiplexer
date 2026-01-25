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

        if num_panes == 1:
            # Single pane takes full screen
            panes[0].x = 0
            panes[0].y = 0
            panes[0].width = term_width
            panes[0].height = term_height
        elif num_panes == MAX_TWO_PANES:
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
        elif num_panes <= MAX_GRID_PANES:
            # 2x2 grid
            half_width = term_width // 2
            half_height = term_height // 2
            positions = [
                (0, 0, half_width, half_height),
                (half_width, 0, term_width - half_width, half_height),
                (0, half_height, half_width, term_height - half_height),
                (
                    half_width,
                    half_height,
                    term_width - half_width,
                    term_height - half_height,
                ),
            ]
            for i, pane in enumerate(panes):
                pane.x, pane.y, pane.width, pane.height = positions[i]
        else:
            # Grid layout for more than 4 panes
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
