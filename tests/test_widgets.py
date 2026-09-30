from pathlib import Path
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap
from src.aina.StylishLineEdit import StylishLineEdit
from src.aina.AspectImageLabel import AspectImageLabel
from src.aina.AnimatedButton import AnimatedButton


def test_stylish_line_edit_history_and_up_down_arrow(qtbot):
    edit = StylishLineEdit(placeholder_text="Say something...")
    qtbot.addWidget(edit)

    # Empty history does not crash on Up key
    qtbot.keyClick(edit, Qt.Key.Key_Up)
    assert edit.text() == ""

    # Add messages to history
    edit.add_to_history("First message")
    edit.add_to_history("Second message")

    # Up arrow recalls most recent message
    qtbot.keyClick(edit, Qt.Key.Key_Up)
    assert edit.text() == "Second message"

    # Up arrow again recalls previous message
    qtbot.keyClick(edit, Qt.Key.Key_Up)
    assert edit.text() == "First message"

    # Further Up arrow stays at the oldest message
    qtbot.keyClick(edit, Qt.Key.Key_Up)
    assert edit.text() == "First message"

    # Down arrow navigates forward
    qtbot.keyClick(edit, Qt.Key.Key_Down)
    assert edit.text() == "Second message"

    # Down arrow past latest clears the input
    qtbot.keyClick(edit, Qt.Key.Key_Down)
    assert edit.text() == ""


def test_stylish_line_edit_ignores_empty_or_duplicate(qtbot):
    edit = StylishLineEdit()
    qtbot.addWidget(edit)

    edit.add_to_history("   ")
    assert len(edit._history) == 0

    edit.add_to_history("Hello")
    edit.add_to_history("Hello")
    assert len(edit._history) == 1


def test_aspect_image_label_scaling(qtbot, tmp_path: Path):
    # Create a test 100x100 png image
    test_img = tmp_path / "test.png"
    pix = QPixmap(100, 100)
    pix.fill(Qt.GlobalColor.blue)
    pix.save(str(test_img))

    label = AspectImageLabel(str(test_img))
    qtbot.addWidget(label)
    label.show()

    # Resize widget to wider aspect ratio
    label.resize(400, 200)
    # The rendered pixmap width should be constrained by height (200x200), keeping 1:1 ratio
    scaled = label.pixmap()
    assert scaled is not None
    assert scaled.width() <= 200
    assert scaled.height() <= 200


def test_animated_button_creation(qtbot, project_root: Path):
    icon_path = str(project_root / "assets" / "icons" / "repeat.png")
    btn = AnimatedButton(icon_path, icon_size=24, size=40)
    qtbot.addWidget(btn)

    assert btn.icon_size == 24
    assert btn.property("theme") == "light"
    assert btn.size() == QSize(40, 40)
