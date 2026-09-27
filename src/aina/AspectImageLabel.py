from PySide6.QtWidgets import QLabel, QWidget, QSizePolicy
from PySide6.QtGui import QPixmap, QResizeEvent
from PySide6.QtCore import Qt


class AspectImageLabel(QLabel):
    """
    A custom QLabel that preserves the original aspect ratio of an image (QPixmap)
    when scaled or resized, preventing distortion.
    """

    def __init__(
        self, pixmap_path: str = "", parent: QWidget | None = None
    ) -> None:
        """
        Initializes the AspectImageLabel with an image from the given path.

        Args:
            pixmap_path (str, optional): Path to the image file to load.
            parent (QWidget, optional): Parent widget. Defaults to None.
        """
        super().__init__(parent)
        self._pixmap = QPixmap(pixmap_path) if pixmap_path else None
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.setMinimumSize(200, 200)

    def set_pixmap(self, pixmap: QPixmap) -> None:
        """
        Updates the original pixmap and refreshes the displayed image.

        Args:
            pixmap (QPixmap): The new pixmap to display.
        """
        self._pixmap = pixmap
        self.update_pixmap()

    def resizeEvent(self, event: QResizeEvent) -> None:
        """
        Handles widget resize events by re-scaling the pixmap with KeepAspectRatio.
        """
        super().resizeEvent(event)
        self.update_pixmap()

    def update_pixmap(self) -> None:
        """
        Scales the original pixmap to fit the current label size while
        maintaining the original aspect ratio and using smooth transformation.
        """
        if self._pixmap and not self._pixmap.isNull():
            scaled = self._pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            super().setPixmap(scaled)
