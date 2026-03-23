PROMPT_PREFIX = "❯ "  # noqa: RUF001


class Box:
    def __init__(  # noqa: PLR0913
        self,
        top_left: str,
        top_right: str,
        bottom_left: str,
        bottom_right: str,
        horizontal: str,
        vertical: str,
        left_connector: str = "├",
        right_connector: str = "┤",
    ) -> None:
        self.top_left = top_left
        self.top_right = top_right
        self.bottom_left = bottom_left
        self.bottom_right = bottom_right
        self.horizontal = horizontal
        self.vertical = vertical
        self.left_connector = left_connector
        self.right_connector = right_connector


rounded = Box("╭", "╮", "╰", "╯", "─", "│", "├", "┤")
squared = Box("┌", "┐", "└", "┘", "─", "│", "├", "┤")
double = Box("╔", "╗", "╚", "╝", "═", "║", "╠", "╣")
