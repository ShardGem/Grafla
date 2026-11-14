from PyQt6.QtCore import QElapsedTimer, QPointF, QPropertyAnimation, QRectF, Qt, QTimer
from PyQt6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import QApplication, QWidget

from grafla import __version__
from grafla.branding import application_icon, brand_pixmap

DEFAULT_SPLASH_DURATION_MS = 3000


def splash_duration(settings):
    """Atualiza o padrão antigo uma vez e preserva os tempos personalizados."""
    if settings.value("splash_default_ms", 0, type=int) != DEFAULT_SPLASH_DURATION_MS:
        if settings.value("splash_duration_ms", DEFAULT_SPLASH_DURATION_MS, type=int) == 1800:
            settings.setValue("splash_duration_ms", DEFAULT_SPLASH_DURATION_MS)
        settings.setValue("splash_default_ms", DEFAULT_SPLASH_DURATION_MS)
    return settings.value("splash_duration_ms", DEFAULT_SPLASH_DURATION_MS, type=int)


class Splash(QWidget):
    """Mostra as etapas da abertura sem bloquear o editor ou somar uma espera extra."""

    def __init__(self, animate=True, minimum_ms=DEFAULT_SPLASH_DURATION_MS):
        super().__init__(None, Qt.WindowType.SplashScreen | Qt.WindowType.FramelessWindowHint)
        self.setFixedSize(660, 420)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowIcon(application_icon())
        self.setAccessibleName("Inicialização do Grafla")
        self.status = "Inicializando…"
        self.progress = 0.0
        self.animation = None
        self.minimum_ms = max(0, min(5000, minimum_ms))
        self.elapsed = QElapsedTimer()
        self.hold = QTimer(self)
        self.hold.setSingleShot(True)
        self.hold.setTimerType(Qt.TimerType.PreciseTimer)
        self.callback = None
        self.hold.timeout.connect(self.release)
        if animate and QApplication.platformName() not in {"offscreen", "minimal"}:
            self.animation = QPropertyAnimation(self, b"windowOpacity", self)
            self.animation.setDuration(180)
            self.animation.setStartValue(0.0)
            self.animation.setEndValue(1.0)
            self.animation.start()

    def showEvent(self, event):
        self.elapsed.start()
        super().showEvent(event)

    def finish_when_ready(self, callback):
        self.callback = callback
        self.report("Pronto para explorar.", 1.0)
        remaining = max(0, self.minimum_ms - self.elapsed.elapsed())
        if remaining:
            self.hold.start(remaining)
        else:
            self.release()

    def release(self):
        remaining = max(0, self.minimum_ms - self.elapsed.elapsed())
        if self.callback is not None and remaining:
            self.hold.start(remaining)
            return
        callback, self.callback = self.callback, None
        if callback is not None:
            callback()

    def closeEvent(self, event):
        self.hold.stop()
        if self.animation is not None:
            self.animation.stop()
        self.callback = None
        super().closeEvent(event)

    def report(self, status, progress):
        self.status = status
        self.progress = max(0.0, min(1.0, progress))
        self.setAccessibleDescription(f"{status} · {self.progress:.0%}")
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        card = QRectF(8, 8, self.width() - 16, self.height() - 16)
        shape = QPainterPath()
        shape.addRoundedRect(card, 18, 18)
        background = QLinearGradient(card.topLeft(), card.bottomRight())
        background.setColorAt(0, QColor("#242f3f"))
        background.setColorAt(0.6, QColor("#192330"))
        background.setColorAt(1, QColor("#131b26"))
        painter.fillPath(shape, background)
        painter.setClipPath(shape)

        # A malha fica ao fundo para não disputar espaço com a marca.
        painter.setPen(QPen(QColor("#344153"), 1))
        nodes = [(491, 23), (574, 71), (574, 166), (657, 214), (657, 23)]
        for a, b in ((0, 1), (1, 2), (2, 3), (1, 4)):
            painter.drawLine(QPointF(*nodes[a]), QPointF(*nodes[b]))
        painter.setBrush(QColor("#263344"))
        for x, y in nodes:
            painter.drawEllipse(QPointF(x, y), 4, 4)

        font = QFont(self.font())
        font.setPixelSize(11)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.6)
        font.setWeight(QFont.Weight.DemiBold)
        painter.setFont(font)
        painter.setPen(QColor("#aebdd0"))
        painter.drawText(QRectF(42, 38, 260, 20), Qt.AlignmentFlag.AlignVCenter, "EDITOR DE GRAFOS")
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 0)
        painter.setFont(font)
        painter.drawText(
            QRectF(516, 38, 102, 20),
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
            f"v{__version__}",
        )

        logo = brand_pixmap("horizontal", 480, 176, self.devicePixelRatioF())
        painter.drawPixmap(QPointF(90, 91), logo)
        font.setPixelSize(16)
        font.setWeight(QFont.Weight.Normal)
        painter.setFont(font)
        painter.setPen(QColor("#dce5ef"))
        painter.drawText(
            QRectF(42, 277, 576, 26),
            Qt.AlignmentFlag.AlignCenter,
            "Construir. Explorar. Compreender.",
        )

        painter.setPen(QPen(QColor("#303d4f"), 1))
        painter.drawLine(QPointF(42, 326), QPointF(618, 326))
        font.setPixelSize(12)
        painter.setFont(font)
        painter.setPen(QColor("#aebdd0"))
        status = painter.fontMetrics().elidedText(self.status, Qt.TextElideMode.ElideRight, 520)
        painter.drawText(QRectF(42, 343, 520, 24), Qt.AlignmentFlag.AlignVCenter, status)
        painter.drawText(
            QRectF(568, 343, 50, 24),
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
            f"{self.progress:.0%}",
        )
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#303d4f"))
        painter.drawRoundedRect(QRectF(42, 379, 576, 4), 2, 2)
        progress = QLinearGradient(42, 0, 618, 0)
        progress.setColorAt(0, QColor("#fa5846"))
        progress.setColorAt(1, QColor("#fa892e"))
        painter.setBrush(progress)
        if self.progress > 0:
            painter.drawRoundedRect(QRectF(42, 379, 576 * self.progress, 4), 2, 2)
        painter.setClipping(False)
        painter.setPen(QPen(QColor("#3a485c"), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(shape)
