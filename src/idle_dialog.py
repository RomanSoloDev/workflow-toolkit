"""The 'welcome back' popup shown after an idle period.

A slider (15-second steps) and a time box let the user choose how much of the
idle time was actually work.
"""

import math
from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSlider,
    QVBoxLayout,
)

STEP_SECONDS = 15


def format_duration(seconds):
    minutes, secs = divmod(int(round(seconds)), 60)
    return f"{minutes}:{secs:02}"

def parse_duration(text):
    parts = text.strip().split(":")
    if not all(part.isdigit() for part in parts):
        return None
    numbers = [int(part) for part in parts]
    if len(numbers) == 2:
        minutes, secs = numbers
        if secs < 60:
            return minutes * 60 + secs
    elif len(numbers) == 3:
        hours, minutes, secs = numbers
        if minutes < 60 and secs < 60:
            return hours * 3600 + minutes * 60 + secs
    return None


class IdleDialog(QDialog):
    def __init__(self, started_at, ended_at, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Welcome back")
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)

        self.total = max(ended_at - started_at, 0.0)
        self.kept = self.total
        self.steps = math.ceil(self.total / STEP_SECONDS)

        from_text = datetime.fromtimestamp(started_at).strftime("%H:%M")
        to_text = datetime.fromtimestamp(ended_at).strftime("%H:%M")
        heading = QLabel(
            f"You were away for <b>{format_duration(self.total)}</b> "
            f"({from_text} to {to_text}).<br>How much of it was work time?"
        )
        heading.setWordWrap(True)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, self.steps)
        self.slider.valueChanged.connect(self.on_slider_moved)

        self.time_box = QLineEdit()
        self.time_box.setFixedWidth(70)
        self.time_box.setPlaceholderText("m:ss")
        self.time_box.editingFinished.connect(self.on_time_typed)

        slider_row = QHBoxLayout()
        slider_row.addWidget(self.slider)
        slider_row.addWidget(self.time_box)

        self.summary = QLabel()

        remove_all = QPushButton("Remove all")
        keep_all = QPushButton("Keep all")
        save = QPushButton("Save")
        remove_all.setAutoDefault(False)
        keep_all.setAutoDefault(False)
        save.setDefault(True)
        remove_all.clicked.connect(lambda: self.finish(0.0))
        keep_all.clicked.connect(lambda: self.finish(self.total))
        save.clicked.connect(lambda: self.finish(self.kept))

        buttons = QHBoxLayout()
        buttons.addWidget(remove_all)
        buttons.addWidget(keep_all)
        buttons.addStretch()
        buttons.addWidget(save)

        layout = QVBoxLayout(self)
        layout.addWidget(heading)
        layout.addLayout(slider_row)
        layout.addWidget(self.summary)
        layout.addLayout(buttons)

        self.update_display()

    def on_slider_moved(self, position):
        self.kept = min(position * STEP_SECONDS, self.total)
        self.update_display()

    def on_time_typed(self):
        seconds = parse_duration(self.time_box.text())
        if seconds is not None:
            self.kept = min(seconds, self.total)
        self.update_display()

    def update_display(self):
        self.time_box.setText(format_duration(self.kept))
        if self.kept >= self.total:
            position = self.steps
        else:
            position = min(round(self.kept / STEP_SECONDS), self.steps)
        self.slider.blockSignals(True)
        self.slider.setValue(position)
        self.slider.blockSignals(False)
        removed = self.total - self.kept
        self.summary.setText(
            f"Counted as work: {format_duration(self.kept)}    "
            f"Removed: {format_duration(removed)}"
        )

    def finish(self, kept):
        self.kept = kept
        self.accept()