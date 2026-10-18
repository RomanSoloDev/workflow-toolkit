from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from time_tracker import HEARTBEAT_SECONDS, TimeTracker

def format_seconds(seconds):
    seconds = int(seconds)
    hours, rest = divmod(seconds, 3600)
    minutes, secs = divmod(rest, 60)
    return f"{hours:02}:{minutes:02}:{secs:02}"


class TimerTab(QWidget):
    def __init__(self):
        super().__init__()
        self.tracker = TimeTracker()

        self.session_label = QLabel()
        self.session_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.time_label = QLabel("00:00:00")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(36)
        font.setBold(True)
        self.time_label.setFont(font)

        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.start_button = QPushButton("Start")
        self.pause_button = QPushButton("Pause")
        self.stop_button = QPushButton("Stop")
        self.start_button.clicked.connect(self.on_start)
        self.pause_button.clicked.connect(self.on_pause_resume)
        self.stop_button.clicked.connect(self.on_stop)

        buttons = QHBoxLayout()
        for button in (self.start_button, self.pause_button, self.stop_button):
            button.setMinimumHeight(36)
            buttons.addWidget(button)

        layout = QVBoxLayout(self)
        layout.addStretch()
        layout.addWidget(self.session_label)
        layout.addWidget(self.time_label)
        layout.addWidget(self.status_label)
        layout.addSpacing(16)
        layout.addLayout(buttons)
        layout.addStretch()

        self.display_timer = QTimer(self)
        self.display_timer.timeout.connect(self.refresh)
        self.display_timer.start(200)

        self.heartbeat_timer = QTimer(self)
        self.heartbeat_timer.timeout.connect(self.tracker.heartbeat)
        self.heartbeat_timer.start(HEARTBEAT_SECONDS * 1000)

        # Quitting from the tray pauses the timer so time isn't over-counted
        QApplication.instance().aboutToQuit.connect(self.tracker.pause)

        self.refresh()
        if self.tracker.recovered:
            QTimer.singleShot(0, self.show_recovery_message)

    def on_start(self):
        self.tracker.start()
        self.refresh()

    def on_pause_resume(self):
        if self.tracker.is_running:
            self.tracker.pause()
        else:
            self.tracker.resume()
        self.refresh()

    def on_stop(self):
        answer = QMessageBox.question(
            self,
            "End session",
            f"End Session {self.tracker.session_id} at "
            f"{format_seconds(self.tracker.elapsed())}?",
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.tracker.stop()
            self.refresh()

    def refresh(self):
        tracker = self.tracker
        self.time_label.setText(format_seconds(tracker.elapsed()))

        if tracker.session_id is None:
            self.session_label.setText("No active session")
            self.status_label.setText("Stopped")
        else:
            self.session_label.setText(f"Session {tracker.session_id}")
            self.status_label.setText("Running" if tracker.is_running else "Paused")

        self.start_button.setEnabled(tracker.session_id is None)
        self.pause_button.setEnabled(tracker.session_id is not None)
        self.pause_button.setText("Resume" if tracker.is_paused else "Pause")
        self.stop_button.setEnabled(tracker.session_id is not None)

    def show_recovery_message(self):
        QMessageBox.information(
            self,
            "Session recovered",
            f"Session {self.tracker.session_id} was still running when the app "
            "last closed.\n\nIt's been paused at the last moment the app was "
            "running. Press Resume to carry on.",
        )