from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QMainWindow, QTabWidget

from timer_tab import TimerTab
from history_tab import HistoryTab
from screenshots_tab import ScreenshotsTab
from files_tab import FilesTab
from notes_tab import NotesTab

TABS = ["Clipboard"]

def placeholder(name):
    label = QLabel(f"{name}\n\nComing soon")
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return label

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Workflow Toolkit")
        self.resize(460, 520)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)

        tabs = QTabWidget()
        self.timer_tab = TimerTab()
        tabs.addTab(self.timer_tab, "Timer")

        self.history_tab = HistoryTab(self.timer_tab.tracker)
        tabs.addTab(self.history_tab, "History")

        self.screenshots_tab = ScreenshotsTab(self.timer_tab.tracker)
        tabs.addTab(self.screenshots_tab, "Screenshots")

        self.files_tab = FilesTab()
        tabs.addTab(self.files_tab, "Files")

        self.notes_tab = NotesTab(self.timer_tab.tracker)
        tabs.addTab(self.notes_tab, "Notes")

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