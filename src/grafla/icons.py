"""Ícones do Grafla inspirados no legado, com contornos e silhuetas preenchidas."""

from functools import lru_cache

from PyQt6.QtCore import QByteArray, QEasingCurve, QEvent, QObject, Qt, QVariantAnimation
from PyQt6.QtGui import QIcon, QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import QGraphicsOpacityEffect

# Ícones na grade de 24 unidades, com pontas arredondadas e contorno de 1,65.
# Mão, borracha e sinais de adição seguem os desenhos originais do projeto.
HAND = '<path d="M7 13V7a1.25 1.25 0 0 1 2.5 0v4.3q.75.7 1.5 0V4.5a1.25 1.25 0 0 1 2.5 0V11q.75.7 1.5 0V6a1.25 1.25 0 0 1 2.5 0v6q.5.5 1 0V9a1.25 1.25 0 0 1 2.5 0v6c0 4.1-2.7 6.5-6.8 6.5-3.2 0-5.5-1.6-7.5-4l-3.5-4a1.6 1.6 0 0 1 2.4-2.1L7 13Z"/>'
PATHS = {
    "select": '<path d="M5 3.5 19.5 13 13 14.5 10 21Z"/>',
    "hand": HAND,
    "vertex": '<path d="M15.7 9.1a7.2 7.2 0 1 1-5.6-2.6"/><path d="M18 3v7m-3.5-3.5h7"/>',
    "edge": '<circle cx="5" cy="6" r="2.3"/><circle cx="18" cy="19" r="2.3"/><path d="m6.8 7.8 9.4 9.4M18 3v7m-3.5-3.5h7"/>',
    "delete": '<path d="m3.7 12.8 9.1-9.1a2.3 2.3 0 0 1 3.2 0l4.3 4.3a2.3 2.3 0 0 1 0 3.2L11.5 20H8l-4.3-4a2.3 2.3 0 0 1 0-3.2ZM9 7.5l7.5 7.5M10 21h11"/>',
    "undo": '<path d="M8.5 4 3 9.5 8.5 15M3.5 9.5H14a6 6 0 0 1 0 12h-3"/>',
    "redo": '<path d="m15.5 4 5.5 5.5-5.5 5.5m5-5.5H10a6 6 0 0 0 0 12h3"/>',
    "fit": '<path d="M8 3H3v5m13-5h5v5M3 16v5h5m13-5v5h-5"/><circle cx="12" cy="12" r="3.5"/>',
    "physics": '<path d="m6 6 12 1-6 12Z"/><circle cx="6" cy="6" r="3"/><circle cx="18" cy="7" r="3"/><circle cx="12" cy="19" r="3"/>',
    "save": '<path d="M4 3h12l5 5v13H3V3Zm3 0v7h10V4M7 21v-7h10v7"/><path d="M14 5v2"/>',
    "open": '<path d="M3 10V5h7l3 3h7v3M3 11h19l-4 10H3Z"/>',
    "new": '<path d="M5 3h9l5 5v13H5Zm9 0v6h5M8 15h8m-4-4v8"/>',
    "search": '<circle cx="10" cy="10" r="6.5"/><path d="m15 15 6 6"/>',
    "play": '<path d="m7 4 13 8-13 8Z"/>',
    "pause": '<rect x="5" y="4" width="4" height="16" rx="1"/><rect x="15" y="4" width="4" height="16" rx="1"/>',
    "settings": '<path d="M4 6h16M4 12h16M4 18h16"/><rect x="7" y="3" width="4" height="6" rx="1"/><rect x="14" y="9" width="4" height="6" rx="1"/><rect x="6" y="15" width="4" height="6" rx="1"/>',
    "grid": '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M9 3v18m6-18v18M3 9h18M3 15h18"/>',
    "export": '<path d="M4 13v8h16v-8M12 16V3m-5 5 5-5 5 5"/>',
    "layout": '<circle cx="12" cy="4" r="2.5"/><circle cx="5" cy="17" r="2.5"/><circle cx="19" cy="17" r="2.5"/><path d="m10.5 6-4 8.5M13.5 6l4 8.5M8 17h8"/>',
}

FILLED = {
    "select": '<path d="M4 2.5 21 13.6 13.6 15.2 10 23Z"/>',
    "hand": HAND,
    "vertex": '<path d="M14.2 7.2a7.7 7.7 0 1 0 3.1 5.5h-1.1a2 2 0 0 1-2-2Z"/><path d="M17 3h2v2.5h2.5v2H19V10h-2V7.5h-2.5v-2H17Z"/>',
    "edge": '<circle cx="5" cy="6" r="3"/><circle cx="18" cy="19" r="3"/><path d="m5.1 8.6 2.1-2.1 11.7 11.9-2.1 2.1ZM17 3h2v2.5h2.5v2H19V10h-2V7.5h-2.5v-2H17Z"/>',
    "delete": '<path d="m10.2 6.3 2.6-2.6a2.3 2.3 0 0 1 3.2 0l4.3 4.3a2.3 2.3 0 0 1 0 3.2l-2.6 2.6ZM8.8 7.7l7.5 7.5-4.8 4.8H8l-4.3-4a2.3 2.3 0 0 1 0-3.2ZM10 20h11v2H10Z"/>',
    "physics": '<path d="m5.4 6.7 1.2-1.4L18.8 7l-6.1 13-1.8-.1Zm2.2 1.4 4.5 8.7 4.3-8.1Z" fill-rule="evenodd"/><circle cx="6" cy="6" r="3.2"/><circle cx="18" cy="7" r="3.2"/><circle cx="12" cy="19" r="3.2"/>',
    "play": '<path d="m6 3 15 9-15 9Z"/>',
    "pause": '<rect x="5" y="4" width="4" height="16" rx="1"/><rect x="15" y="4" width="4" height="16" rx="1"/>',
}


def _svg(name, color, filled):
    if filled and name in FILLED:
        body = f'<g fill="{color}" stroke="none">{FILLED[name]}</g>'
    else:
        body = f'<g fill="none" stroke="{color}" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round">{PATHS.get(name, PATHS["vertex"])}</g>'
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">{body}</svg>'


@lru_cache(maxsize=256)
def icon(
    name: str,
    color: str,
    active: bool = False,
    hover_color: str | None = None,
    disabled_color: str | None = None,
) -> QIcon:
    result = QIcon()
    rendered = {}
    for mode, ink in (
        (QIcon.Mode.Normal, color),
        (QIcon.Mode.Active, hover_color or color),
        (QIcon.Mode.Selected, hover_color or color),
        (QIcon.Mode.Disabled, disabled_color or "#697585"),
    ):
        for state in (QIcon.State.Off, QIcon.State.On):
            filled = active or state == QIcon.State.On
            for size in (16, 24, 32, 48, 64, 96):
                key = (ink, filled, size)
                if key not in rendered:
                    renderer = QSvgRenderer(QByteArray(_svg(name, ink, filled).encode()))
                    pixmap = QPixmap(size, size)
                    pixmap.fill(Qt.GlobalColor.transparent)
                    painter = QPainter(pixmap)
                    renderer.render(painter)
                    painter.end()
                    rendered[key] = pixmap
                result.addPixmap(rendered[key], mode, state)
    return result


class ToolFeedback(QObject):
    """Transição curta que pode ser interrompida; timer e efeito param ao terminar."""

    def __init__(self, button):
        super().__init__(button)
        self.button = button
        self.effect = QGraphicsOpacityEffect(button)
        button.setGraphicsEffect(self.effect)
        self.effect.setEnabled(False)
        self.animation = QVariantAnimation(self)
        self.animation.setDuration(110)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animation.valueChanged.connect(self.effect.setOpacity)
        self.animation.finished.connect(lambda: self.effect.setEnabled(False))
        button.installEventFilter(self)
        button.defaultAction().toggled.connect(self.pulse)

    def pulse(self, *_):
        self.animation.stop()
        if self.button.property("animate") is False or not self.button.isVisible():
            self.effect.setEnabled(False)
            return
        self.effect.setEnabled(True)
        self.animation.setStartValue(0.65)
        self.animation.setEndValue(1.0)
        self.animation.start()

    def eventFilter(self, watched, event):
        if event.type() in (QEvent.Type.Enter, QEvent.Type.FocusIn):
            self.pulse()
        return super().eventFilter(watched, event)
