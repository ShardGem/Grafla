"""Escolha visual de cores, com roda de matiz/saturação e ajuste de brilho."""

import math

from PyQt6.QtCore import QPointF, QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QConicalGradient, QIcon, QPainter, QPen, QPixmap, QRadialGradient
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSlider,
    QVBoxLayout,
    QWidget,
)


class ColorWheel(QWidget):
    color_changed = pyqtSignal(QColor)

    def __init__(self, color, parent=None):
        super().__init__(parent)
        self.color = QColor(color)
        self.setFixedSize(248, 248)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAccessibleName("Roda de cores")

    def set_color(self, color):
        self.color = QColor(color)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        center = QPointF(self.width() / 2, self.height() / 2)
        radius = self.width() / 2 - 10
        circle = QRectF(center.x() - radius, center.y() - radius, 2 * radius, 2 * radius)
        hue = QConicalGradient(center, 0)
        for i in range(7):
            hue.setColorAt(i / 6, QColor.fromHsvF((i % 6) / 6, 1, 1))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(hue)
        painter.drawEllipse(circle)
        saturation = QRadialGradient(center, radius)
        saturation.setColorAt(0, QColor("white"))
        saturation.setColorAt(1, QColor(255, 255, 255, 0))
        painter.setBrush(saturation)
        painter.drawEllipse(circle)
        painter.setBrush(QColor(0, 0, 0, 255 - self.color.value()))
        painter.drawEllipse(circle)
        angle = max(0, self.color.hsvHueF()) * math.tau
        distance = radius * self.color.hsvSaturationF()
        point = center + QPointF(math.cos(angle) * distance, -math.sin(angle) * distance)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor("#202733"), 4))
        painter.drawEllipse(point, 5, 5)
        painter.setPen(QPen(QColor("white"), 2))
        painter.drawEllipse(point, 5, 5)

    def choose(self, position):
        dx, dy = position.x() - self.width() / 2, position.y() - self.height() / 2
        hue = (math.atan2(-dy, dx) / math.tau) % 1
        saturation = min(1.0, math.hypot(dx, dy) / (self.width() / 2 - 10))
        self.color = QColor.fromHsvF(hue, saturation, self.color.valueF())
        self.update()
        self.color_changed.emit(self.color)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.choose(event.position())

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.choose(event.position())

    def keyPressEvent(self, event):
        hue, saturation, value, _ = self.color.getHsvF()
        hue = max(0, hue)
        if event.key() == Qt.Key.Key_Left:
            hue = (hue - 1 / 360) % 1
        elif event.key() == Qt.Key.Key_Right:
            hue = (hue + 1 / 360) % 1
        elif event.key() == Qt.Key.Key_Up:
            saturation = min(1, saturation + 0.02)
        elif event.key() == Qt.Key.Key_Down:
            saturation = max(0, saturation - 0.02)
        else:
            super().keyPressEvent(event)
            return
        self.color = QColor.fromHsvF(hue, saturation, value)
        self.update()
        self.color_changed.emit(self.color)


class ColorPicker(QDialog):
    color_changed = pyqtSignal(QColor)

    def __init__(self, color, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Escolher cor")
        color = color if color.isValid() else QColor("#ffad78")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        self.wheel = ColorWheel(color)
        layout.addWidget(self.wheel, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(QLabel("Brilho"))
        self.brightness = QSlider(Qt.Orientation.Horizontal)
        self.brightness.setRange(0, 255)
        self.brightness.setValue(color.value())
        self.brightness.setAccessibleName("Brilho da cor")
        layout.addWidget(self.brightness)
        row = QHBoxLayout()
        row.addWidget(QLabel("Hexadecimal"))
        self.hex = QLineEdit(color.name())
        self.hex.setAccessibleName("Código hexadecimal da cor")
        row.addWidget(self.hex)
        layout.addLayout(row)
        box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        box.button(QDialogButtonBox.StandardButton.Ok).setText("Usar cor")
        box.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        box.accepted.connect(self.accept)
        box.rejected.connect(self.reject)
        layout.addWidget(box)
        self.wheel.color_changed.connect(self.publish)
        self.brightness.valueChanged.connect(self.change_brightness)
        self.hex.textEdited.connect(self.change_hex)

    def publish(self, color):
        self.wheel.set_color(color)
        self.hex.setText(color.name())
        self.brightness.blockSignals(True)
        self.brightness.setValue(color.value())
        self.brightness.blockSignals(False)
        self.color_changed.emit(color)

    def change_brightness(self, value):
        color = self.wheel.color
        self.publish(QColor.fromHsv(max(0, color.hsvHue()), color.hsvSaturation(), value))

    def change_hex(self, text):
        color = QColor(text)
        if color.isValid() and len(text) == 7 and text.startswith("#"):
            self.publish(color)


class ColorField(QLineEdit):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setPlaceholderText("#RRGGBB")
        self.choose_action = self.addAction(QIcon(), QLineEdit.ActionPosition.TrailingPosition)
        self.choose_action.setText("Escolher cor na roda")
        self.choose_action.setToolTip("Abrir roda de cores")
        self.choose_action.triggered.connect(self.choose_color)
        self.textChanged.connect(self.refresh_swatch)
        self.refresh_swatch()

    def refresh_swatch(self):
        color = QColor(self.text())
        image = QPixmap(40, 40)
        image.fill(Qt.GlobalColor.transparent)
        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor("#899bb2"), 2))
        painter.setBrush(color if color.isValid() else QColor("#899bb2"))
        painter.drawEllipse(QRectF(5, 5, 30, 30))
        painter.end()
        self.choose_action.setIcon(QIcon(image))

    def choose_color(self):
        original = self.text()
        dialog = ColorPicker(QColor(original), self)
        dialog.color_changed.connect(lambda color: self.setText(color.name()))
        if dialog.exec() != QDialog.DialogCode.Accepted:
            self.setText(original)
