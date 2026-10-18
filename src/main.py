import sys

from PySide6.QtWidgets import QApplication

from main_window import MainWindow
from paths import ensure_data_dirs
from tray import TrayIcon

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Workflow Toolkit")
    app.setQuitOnLastWindowClosed(False)

    ensure_data_dirs()

    window = MainWindow()
    tray = TrayIcon(window)
    tray.show()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()