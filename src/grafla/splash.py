from PyQt6.QtCore import QPropertyAnimation, QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import QApplication, QWidget

from grafla import __version__


class Splash(QWidget):
    """A lightweight painted bootstrap surface; it never enforces a minimum duration."""

    def __init__(self, animate=True):
        super().__init__(None, Qt.WindowType.SplashScreen | Qt.WindowType.FramelessWindowHint)
        self.setFixedSize(620, 340)
        self.setAccessibleName("Inicialização do Grafla")
        self.status = "Inicializando…"
        self.progress = 0
        self.animation = None
        if animate and QApplication.platformName() not in {"offscreen", "minimal"}:
            self.animation = QPropertyAnimation(self, b"windowOpacity", self)
            self.animation.setDuration(140)
            self.animation.setStartValue(0.0)
            self.animation.setEndValue(1.0)
            self.animation.start()

    def report(self, status, progress):
        self.status, self.progress = status, progress
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#11161e"))
        painter.setPen(QPen(QColor("#303d4e"), 1))
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))
        nodes = [(406, 74), (530, 74), (406, 148), (468, 148), (530, 148), (406, 222), (530, 222)]
        painter.setPen(QPen(QColor("#775744"), 1.5))
        for a, b in ((0, 1), (0, 2), (2, 3), (3, 4), (2, 5), (5, 6), (4, 6)):
            painter.drawLine(*nodes[a], *nodes[b])
        for index, (x, y) in enumerate(nodes):
            painter.setPen(QPen(QColor("#ffad78" if index in {0, 2, 5, 6} else "#596b83"), 2))
            painter.setBrush(QColor("#11161e"))
            painter.drawEllipse(QRectF(x - 7, y - 7, 14, 14))
        font = QFont()
        font.setPointSize(29)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor("#ffad78"))
        painter.drawText(34, 112, "GRAFLA")
        font.setPointSize(11)
        font.setBold(False)
        painter.setFont(font)
        painter.setPen(QColor("#edf2f8"))
        painter.drawText(36, 146, "Construir. Explorar. Compreender.")
        painter.setPen(QColor("#aebacc"))
        painter.drawText(36, 174, f"Editor de grafos · {__version__}")
        font.setPointSize(9)
        painter.setFont(font)
        painter.drawText(36, 280, self.status)
        painter.fillRect(QRectF(36, 301, 548, 2), QColor("#303d4e"))
        painter.fillRect(QRectF(36, 301, 548 * self.progress, 2), QColor("#ffad78"))
