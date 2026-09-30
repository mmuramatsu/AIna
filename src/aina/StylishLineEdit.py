from PySide6.QtWidgets import QLineEdit, QWidget
from PySide6.QtGui import QKeyEvent
from PySide6.QtCore import Qt


class StylishLineEdit(QLineEdit):
    """
    A custom QLineEdit with placeholder support, theme-based styling,
    and message history recall via Up/Down arrow keys.
    """

    def __init__(
        self, placeholder_text: str = "", parent: QWidget | None = None
    ) -> None:
        """
        Initializes the StylishLineEdit with optional placeholder text.

        Args:
            placeholder_text (str, optional): Text to display as a placeholder.
                Defaults to an empty string.
            parent (QWidget, optional): The parent widget. Defaults to None.
        """

        super().__init__(parent)
        self.setPlaceholderText(placeholder_text)
        self.setProperty("theme", "light")  # Set default theme

        self._history: list[str] = []
        self._history_index: int = -1

    def add_to_history(self, text: str) -> None:
        """
        Adds a message to the input history for Up/Down arrow recall.

        Args:
            text (str): The message text to record in history.
        """
        stripped = text.strip()
        if stripped:
            if not self._history or self._history[-1] != stripped:
                self._history.append(stripped)
            self._history_index = -1

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """
        Handles key events, providing Up/Down arrow navigation through message history.
        """
        if event.key() == Qt.Key.Key_Up:
            if self._history:
                if self._history_index == -1:
                    self._history_index = len(self._history) - 1
                elif self._history_index > 0:
                    self._history_index -= 1

                self.setText(self._history[self._history_index])
                self.selectAll()
                return

        elif event.key() == Qt.Key.Key_Down:
            if self._history_index != -1:
                if self._history_index < len(self._history) - 1:
                    self._history_index += 1
                    self.setText(self._history[self._history_index])
                    self.selectAll()
                else:
                    self._history_index = -1
                    self.clear()
                return

        super().keyPressEvent(event)
