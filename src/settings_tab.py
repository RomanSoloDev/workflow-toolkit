"""Settings: idle threshold, starting with Windows, and screenshot shortcut keys.

Every change is saved straight away to settings.json in AppData.
"""
import os
import string

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QCheckBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

import autostart
from idle import DEFAULT_IDLE_MINUTES
from paths import DATA_DIR
from settings import get_setting, set_setting

DEFAULT_KEYS = {"full_screen_key": "F", "region_key": "R"}


class NumberBox(QSpinBox):
    def __init__(self, minimum, maximum, value):
        super().__init__()
        self.setRange(minimum, maximum)
        self.setValue(value)
        self.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.setKeyboardTracking(False)
        self.setFixedWidth(60)

    def wheelEvent(self, event):
        event.ignore()  # stop the mouse wheel changing the number by accident

class LetterBox(QLineEdit):
    letter_chosen = Signal(str)

    def __init__(self, letter):
        super().__init__(letter)
        self.setFixedWidth(40)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.setToolTip("Click here and press a letter")

    def keyPressEvent(self, event):
        letter = event.text().upper()
        if len(letter) == 1 and letter in string.ascii_uppercase:
            self.setText(letter)
            self.letter_chosen.emit(letter)

class SettingsTab(QWidget):
    def __init__(self, idle_monitor):
        super().__init__()
        self.idle_monitor = idle_monitor

        self.idle_minutes = NumberBox(1, 120, get_setting("idle_minutes", DEFAULT_IDLE_MINUTES))
        self.idle_minutes.valueChanged.connect(self.on_idle_changed)
        idle_row = QHBoxLayout()
        idle_row.addWidget(self.idle_minutes)
        idle_row.addWidget(QLabel("minutes"))
        idle_row.addStretch()
        idle_box = QGroupBox("Idle detection")
        idle_form = QFormLayout(idle_box)
        idle_form.addRow("Count me as away after:", idle_row)
        idle_form.addRow(QLabel("Type a number from 1 to 120, then press Enter."))

        self.autostart_box = QCheckBox("Start when I log in to Windows (in the tray)")
        self.autostart_box.setChecked(autostart.is_enabled())
        self.autostart_box.toggled.connect(self.on_autostart_toggled)
        startup_box = QGroupBox("Startup")
        startup_layout = QVBoxLayout(startup_box)
        startup_layout.addWidget(self.autostart_box)

        self.full_key = LetterBox(get_setting("full_screen_key", DEFAULT_KEYS["full_screen_key"]))
        self.region_key = LetterBox(get_setting("region_key", DEFAULT_KEYS["region_key"]))
        self.full_key.letter_chosen.connect(lambda letter: self.on_letter_changed("full_screen_key", letter))
        self.region_key.letter_chosen.connect(lambda letter: self.on_letter_changed("region_key", letter))
        shortcuts_box = QGroupBox("Screenshot shortcuts")
        shortcuts_form = QFormLayout(shortcuts_box)
        shortcuts_form.addRow("Full screen:  Ctrl+Alt +", self.full_key)
        shortcuts_form.addRow("Region:  Ctrl+Alt +", self.region_key)
        shortcuts_form.addRow(QLabel("Click a box and press a letter. Changes apply next time the app starts."))

        open_data = QPushButton("Open data folder")
        open_data.clicked.connect(lambda: os.startfile(DATA_DIR))
        data_box = QGroupBox("Your data (stored only on this PC)")
        data_layout = QVBoxLayout(data_box)
        data_layout.addWidget(open_data)

        layout = QVBoxLayout(self)
        for box in (idle_box, startup_box, shortcuts_box, data_box):
            layout.addWidget(box)
        layout.addStretch()

    def on_idle_changed(self, minutes):
        set_setting("idle_minutes", minutes)
        self.idle_monitor.threshold_seconds = minutes * 60  # takes effect straight away

    def on_autostart_toggled(self, enabled):
        try:
            autostart.set_enabled(enabled)
        except OSError as error:
            QMessageBox.warning(self, "Start with Windows", f"Couldn't change this setting:\n{error}")
        self.autostart_box.blockSignals(True)
        self.autostart_box.setChecked(autostart.is_enabled())
        self.autostart_box.blockSignals(False)

    def on_letter_changed(self, key, letter):
        box = self.full_key if key == "full_screen_key" else self.region_key
        other = self.region_key if key == "full_screen_key" else self.full_key
        if letter == other.text():
            QMessageBox.warning(self, "Shortcuts", "Full screen and Region need different letters.")
            box.setText(get_setting(key, DEFAULT_KEYS[key]))
            return
        set_setting(key, letter)