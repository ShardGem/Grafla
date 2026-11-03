"""Small vector icons, rendered and cached at multiple device resolutions."""

from functools import lru_cache

from PyQt6.QtCore import QByteArray, Qt
from PyQt6.QtGui import QIcon, QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer

PATHS = {
    "select": '<path d="M5 3l14 10-7 1-3 7z"/>',
    "hand": '<path d="M8 12V6a2 2 0 014 0v6-8a2 2 0 014 0v8-5a2 2 0 014 0v9c0 4-3 6-7 6-3 0-5-2-7-5l-3-5a2 2 0 013-2l3 3"/>',
    "vertex": '<circle cx="10" cy="12" r="7"/><path d="M19 3v6m-3-3h6"/>',
    "edge": '<circle cx="4" cy="18" r="2"/><circle cx="20" cy="5" r="2"/><path d="M6 16L17 7m-6 0h6v6"/>',
    "delete": '<path d="M4 6h16M9 6V3h6v3M6 6l1 15h10l1-15M10 10v7m4-7v7"/>',
    "undo": '<path d="M8 5L3 10l5 5M3 10h11a6 6 0 010 12"/>',
    "redo": '<path d="M16 5l5 5-5 5m5-5H10a6 6 0 000 12"/>',
    "fit": '<path d="M9 3H3v6m12-6h6v6M3 15v6h6m12-6v6h-6"/><circle cx="12" cy="12" r="3"/>',
    "physics": '<circle cx="5" cy="6" r="2"/><circle cx="19" cy="7" r="2"/><circle cx="12" cy="19" r="2"/><path d="M7 6l10 1M6 8l5 9m7-8l-5 8"/>',
    "save": '<path d="M4 3h13l4 4v14H3V3h1zm3 0v7h10V3M7 21v-7h10v7"/>',
    "open": '<path d="M3 7V4h7l3 3h8v13H3l3-10h15"/>',
    "new": '<path d="M5 3h9l5 5v13H5V3zm9 0v6h5M8 14h8m-4-4v8"/>',
    "search": '<circle cx="10" cy="10" r="6"/><path d="M15 15l6 6"/>',
    "play": '<path d="M7 3l14 9-14 9z"/>',
    "grid": '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M9 3v18m6-18v18M3 9h18M3 15h18"/>',
}


@lru_cache(maxsize=128)
def icon(name: str, color: str) -> QIcon:
    body = PATHS.get(name, PATHS["vertex"])
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><g fill="none" stroke="{color}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">{body}</g></svg>'
    renderer = QSvgRenderer(QByteArray(svg.encode()))
    result = QIcon()
    for size in (16, 24, 32, 48, 64, 96):
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        result.addPixmap(pixmap)
    return result
