from PySide6.QtWidgets import QLineEdit
from PySide6.QtCore import QObject


class StylishLineEdit(QLineEdit):
    """
    A custom QLineEdit with placeholder support and a default light theme.

    This input field allows for theme-based styling using Qt's property system.
    """

    def __init__(
        self, placeholder_text: str = "", parent: QObject = None
    ) -> None:
        """
        Initializes the StylishLineEdit with optional placeholder text.

        Args:
            placeholder_text (str, optional): Text to display as a placeholder.
                Defaults to an empty string.
            parent (QObject, optional): The parent widget. Defaults to None.
        """

        super().__init__(parent)
        self.setPlaceholderText(placeholder_text)
        self.setProperty("theme", "light")  # Set default theme
