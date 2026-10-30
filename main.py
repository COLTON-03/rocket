import sys

from PyQt6.QtWidgets import QApplication

from ui.main_window import MainWindow
from ui.theme import apply_dark_theme


def main() -> int:
    app = QApplication(sys.argv)
    apply_dark_theme(app)

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())