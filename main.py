import sys
from PySide6.QtWidgets import QApplication
from src.aina.main_window import MainWindow, load_config, get_config_path

if __name__ == "__main__":
    app = QApplication(sys.argv)
    config_path = get_config_path("AIna")
    config = load_config(config_path)
    window = MainWindow(config)
    window.show()
    sys.exit(app.exec())
