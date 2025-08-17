from PySide6.QtWidgets import QPushButton, QWidget
from PySide6.QtGui import QIcon
from PySide6.QtCore import QSize


class AnimatedButton(QPushButton):
    """
    A custom QPushButton with support for animated styling and dynamic icon
    updates.

    The button can be rendered as a "ColorButton" or "ColorlessButton" based on
    the `colorless` flag, applying different QSS styles accordingly.
    """

    def __init__(
        self,
        icon_path: str,
        parent: QWidget | None = None,
        icon_size: int = 32,
        size: int = 50,
        colorless: bool = False,
    ) -> None:
        """
        Initializes the custom button with styling and icon configuration.

        Args:
            icon_path (str): Path to the initial icon to be displayed on the
                          button.
            parent (QWidget, optional): Parent widget for the button. Defaults
                                     to None.
            icon_size (int, optional): Size (in pixels) for the icon. Defaults
                                    to 32.
            size (int, optional): Size (in pixels) for the button itself.
                               Defaults to 50.
            colorless (bool, optional): If True, applies the "ColorlessButton"
                                     style; otherwise, applies the "ColorButton"
                                     style. Defaults to False.
        """

        super().__init__(parent)

        self.icon_size = icon_size

        self.setIcon(QIcon(icon_path))
        self.setIconSize(QSize(self.icon_size, self.icon_size))
        self.setFixedSize(size, size)
        self.setProperty("theme", "light")  # Set default theme

        self.setObjectName("ColorlessButton" if colorless else "ColorButton")

    def set_icon(self, icon_path: str, icon_size: int = 32) -> None:
        """
        Sets or updates the button's icon.

        Args:
            icon_path (str): Path to the new icon image.
            icon_size (int, optional): Size (in pixels) for the icon. Defaults
                                    to 32.
        """

        self.setIcon(QIcon(icon_path))
        self.setIconSize(QSize(icon_size, icon_size))
