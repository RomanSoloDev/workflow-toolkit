import sys
from pathlib import Path

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QGuiApplication, QImage, QPainter, QPen

SIZE = 256
OUT_DIR = Path(__file__).resolve().parent.parent / "assets"
DARK = QColor(30, 30, 30)
GREEN = QColor(46, 204, 113)

app = QGuiApplication(sys.argv)
image = QImage(SIZE, SIZE, QImage.Format.Format_ARGB32)
image.fill(Qt.GlobalColor.transparent)

painter = QPainter(image)
painter.setRenderHint(QPainter.RenderHint.Antialiasing)
painter.setPen(Qt.PenStyle.NoPen)

painter.setBrush(DARK)
painter.drawRoundedRect(8, 8, SIZE - 16, SIZE - 16, 48, 48)

centre = QPointF(128, 142)
painter.setBrush(GREEN)
painter.drawRoundedRect(110, 26, 36, 28, 6, 6)
painter.drawEllipse(centre, 84, 84)

pen = QPen(DARK)
pen.setWidth(14)
pen.setCapStyle(Qt.PenCapStyle.RoundCap)
painter.setPen(pen)
painter.drawLine(centre, QPointF(128, 84))
painter.drawLine(centre, QPointF(174, 116))
painter.setPen(Qt.PenStyle.NoPen)
painter.setBrush(DARK)
painter.drawEllipse(centre, 10, 10)
painter.end()

OUT_DIR.mkdir(exist_ok=True)
image.save(str(OUT_DIR / "icon.png"))
print("Saved", OUT_DIR / "icon.png")