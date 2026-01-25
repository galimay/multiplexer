class Box:
    def __init__(
        self,
        top_left: str,
        top_right: str,
        bottom_left: str,
        bottom_right: str,
        horizontal: str,
        vertical: str,
    ) -> None:
        self.top_left = top_left
        self.top_right = top_right
        self.bottom_left = bottom_left
        self.bottom_right = bottom_right
        self.horizontal = horizontal
        self.vertical = vertical


rounded = Box("╭", "╮", "╰", "╯", "─", "│")
squared = Box("┌", "┐", "└", "┘", "─", "│")
double = Box("╔", "╗", "╚", "╝", "═", "║")
