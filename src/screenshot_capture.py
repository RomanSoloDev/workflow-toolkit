"""Taking and saving screenshots.

Screenshots are saved as PNGs in AppData, in a folder per session
"""

from datetime import datetime

from PySide6.QtCore import QRect, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QCursor, QGuiApplication, QPainter, QPen
from PySide6.QtWidgets import QLabel, QWidget

from paths import SCREENSHOTS_DIR

def session_folder(session_id):
    name = f"session-{session_id}" if session_id else "no-session"
    folder = SCREENSHOTS_DIR / name
    folder.mkdir(parents=True, exist_ok=True)
    return folder

def save_screenshot(pixmap, session_id):
    now = datetime.now()
    filename = now.strftime("%Y-%m-%d_%H-%M-%S") + f"-{now.microsecond // 1000:03}.png"
    path = session_folder(session_id) / filename
    pixmap.save(str(path), "PNG")
    QGuiApplication.clipboard().setPixmap(pixmap)
    return path

def screen_under_cursor():
    return QGuiApplication.screenAt(QCursor.pos()) or QGuiApplication.primaryScreen()

def grab_screen(screen):
    return screen.grabWindow(0)

class RegionSelector(QWidget):
    selected = Signal(object)  # the cropped screenshot
    cancelled = Signal()

    def __init__(self, screen):
        super().__init__()
        self.shot = grab_screen(screen)  # freeze the screen as it was
        self.start = None
        self.end = None
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setGeometry(screen.geometry())
        self.show()
        self.raise_()
        self.activateWindow()

    def to_pixels(self, area):
        ratio = self.shot.devicePixelRatio()
        return QRect(
            round(area.x() * ratio),
            round(area.y() * ratio),
            round(area.width() * ratio),
            round(area.height() * ratio),
        )

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(self.rect(), self.shot)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 110))  # dim everything
        if self.start is not None and self.end is not None:
            area = QRect(self.start, self.end).normalized()
            painter.drawPixmap(area, self.shot, self.to_pixels(area))
            painter.setPen(QPen(QColor(0, 170, 255), 2))
            painter.drawRect(area)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self.cancel()
            return
        self.start = self.end = event.position().toPoint()
        self.update()

    def mouseMoveEvent(self, event):
        if self.start is not None:
            self.end = event.position().toPoint()
            self.update()

    def mouseReleaseEvent(self, event):
        if self.start is None:
            return
        area = QRect(self.start, event.position().toPoint()).normalized()
        self.close()
        if area.width() < 5 or area.height() < 5:
            self.cancelled.emit()  # too small, probably a stray click
            return
        self.selected.emit(self.shot.copy(self.to_pixels(area)))

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.cancel()

    def cancel(self):
        self.close()
        self.cancelled.emit()


class Toast(QLabel):
    def __init__(self, text, screen, millis=1500):
        super().__init__(text)
        self.setWindowFlags(
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setStyleSheet("background-color: #222; color: white; padding: 10px 14px;")
        self.adjustSize()
        area = screen.availableGeometry()
        self.move(area.right() - self.width() - 20, area.bottom() - self.height() - 20)
        self.show()
        QTimer.singleShot(millis, self.close)