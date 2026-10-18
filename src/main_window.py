from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QMainWindow, QTabWidget
from timer_tab import TimerTab 

TABS = ["Screenshots", "Files", "Notes", "Clipboard"]

def placeholder(name):
    label = QLabel(f"{name}\n\nComing soon")
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return label

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Workflow Toolkit")
        self.resize(380, 520)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)

        tabs = QTabWidget()
        self.timer_tab = TimerTab()
        tabs.addTab(self.timer_tab, "Timer")
        for name in TABS:
            tabs.addTab(placeholder(name), name)
        self.setCentralWidget(tabs)

    def set_always_on_top(self, enabled):
        was_visible = self.isVisible()
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, enabled)
        if was_visible:
            self.show()

    def closeEvent(self, event):
        event.ignore()
        self.hide()