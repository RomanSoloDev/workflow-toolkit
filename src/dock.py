"""Docked mode: the window tucks away into a slim bar on the right edge of the screen.
"""
import ctypes
from ctypes import wintypes

from PySide6.QtCore import QObject, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QCursor, QFont, QGuiApplication, QPainter
from PySide6.QtWidgets import QApplication, QWidget

from settings import get_setting, set_setting
from timer_tab import format_seconds

BAR_WIDTH = 112
BAR_HEIGHT = 30
HOVER_DELAY_MS = 300  # how long to hover before the window pops out
COLLAPSE_CHECKS = 3  # checks (every 200 ms) the mouse must be away before tucking in

GREEN = QColor(46, 204, 113)
AMBER = QColor(241, 196, 15)
GREY = QColor(150, 150, 150)

WDA_EXCLUDEFROMCAPTURE = 0x11
_user32 = ctypes.windll.user32
_user32.SetWindowDisplayAffinity.argtypes = [wintypes.HWND, wintypes.DWORD]

def exclude_from_capture(widget):
    _user32.SetWindowDisplayAffinity(int(widget.winId()), WDA_EXCLUDEFROMCAPTURE)

class DockBar(QWidget):
    expand_requested = Signal(bool)

    def __init__(self, tracker):
        super().__init__()
        self.tracker = tracker
        self.drag_offset = None
        self.dragged = False
        self.setWindowFlags(
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(BAR_WIDTH, BAR_HEIGHT)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Hover to peek, click to open. Drag up or down to move.")
        exclude_from_capture(self)

        self.hover_timer = QTimer(self)
        self.hover_timer.setSingleShot(True)
        self.hover_timer.setInterval(HOVER_DELAY_MS)
        self.hover_timer.timeout.connect(self.on_hovered)

        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.update)
        self.refresh_timer.start(500)

    def place(self):
        area = QGuiApplication.primaryScreen().availableGeometry()
        y = get_setting("dock_y", area.top() + area.height() // 3)
        y = max(area.top(), min(y, area.bottom() - self.height()))
        self.move(area.right() - self.width() + 1, y)

    def paintEvent(self, event):
        tracker = self.tracker
        if tracker.session_id is None:
            colour, text = GREY, "--:--:--"
        else:
            text = format_seconds(tracker.elapsed())
            if tracker.is_idle:
                colour = AMBER
            elif tracker.is_running:
                colour = GREEN
            else:
                colour = GREY  # paused

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(30, 30, 30, 235))
        painter.drawRoundedRect(self.rect(), 8, 8)

        painter.setBrush(colour)
        painter.drawEllipse(10, self.height() // 2 - 4, 8, 8)

        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor("white"))
        painter.drawText(26, self.height() // 2 + 5, text)

    def enterEvent(self, event):
        self.hover_timer.start()

    def leaveEvent(self, event):
        self.hover_timer.stop()

    def on_hovered(self):
        if self.underMouse() and self.drag_offset is None:
            self.expand_requested.emit(False)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.hover_timer.stop()
            self.drag_offset = event.globalPosition().toPoint().y() - self.y()
            self.dragged = False

    def mouseMoveEvent(self, event):
        if self.drag_offset is None:
            return
        new_y = event.globalPosition().toPoint().y() - self.drag_offset
        if abs(new_y - self.y()) > 2:
            self.dragged = True
        if self.dragged:
            area = self.screen().availableGeometry()
            new_y = max(area.top(), min(new_y, area.bottom() - self.height()))
            self.move(self.x(), new_y)

    def mouseReleaseEvent(self, event):
        if self.drag_offset is None:
            return
        self.drag_offset = None
        if self.dragged:
            set_setting("dock_y", self.y())  # remember where it was moved to
        else:
            self.expand_requested.emit(True)  # a click, not a drag

class DockController(QObject):
    def __init__(self, window, tracker):
        super().__init__()
        self.window = window
        self.enabled = False
        self.away_checks = 0
        self.bar = DockBar(tracker)
        self.bar.expand_requested.connect(self.expand)
        self.collapse_timer = QTimer(self)
        self.collapse_timer.setInterval(200)
        self.collapse_timer.timeout.connect(self.check_collapse)

    def set_enabled(self, enabled):
        self.enabled = enabled
        set_setting("docked_mode", enabled)
        if enabled:
            self.window.hide()
            self.bar.place()
            self.bar.show()
        else:
            self.collapse_timer.stop()
            self.bar.hide()
            self.window.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, False)
            self.window.show()
            self.window.raise_()
            self.window.activateWindow()

    def expand(self, activate):
        if not self.enabled:
            return
        area = self.bar.screen().availableGeometry()
        size = self.window.frameGeometry()
        x = self.bar.x() - size.width() - 4
        y = max(area.top(), min(self.bar.y() - 20, area.bottom() - size.height()))
        self.window.move(x, y)
        self.window.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, not activate)
        self.window.show()
        self.window.raise_()
        if activate:
            self.window.activateWindow()
        self.away_checks = 0
        self.collapse_timer.start()

    def check_collapse(self):
        if not self.enabled or not self.window.isVisible():
            self.collapse_timer.stop()
            return
        mouse = QCursor.pos()
        over_us = self.window.frameGeometry().contains(mouse) or self.bar.geometry().contains(mouse)
        in_use = self.window.isActiveWindow() or QApplication.activeModalWidget() is not None
        if over_us or in_use:
            self.away_checks = 0
            return
        self.away_checks += 1
        if self.away_checks >= COLLAPSE_CHECKS:
            self.window.hide()
            self.collapse_timer.stop()