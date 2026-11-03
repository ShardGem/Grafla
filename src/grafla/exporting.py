"""Render graph content without editor chrome, preview lines or selection handles."""

import math
from pathlib import Path

from PyQt6.QtCore import QBuffer, QByteArray, QIODevice, QMarginsF, QRectF, QSize, QSizeF
from PyQt6.QtGui import QColor, QImage, QPageSize, QPainter, QPdfWriter
from PyQt6.QtSvg import QSvgGenerator

from grafla.domain import GraphError


def export_graph(canvas, path: Path, width=1600, selection=False, transparent=False):
    selected = set(canvas.graph_scene.selectedItems())
    all_items = list(canvas.vertices.values()) + list(canvas.edges.values())
    items = [item for item in all_items if not selection or item in selected]
    if not items:
        raise GraphError("Não há elementos para exportar nessa região.")
    source = QRectF()
    for item in items:
        source = source.united(item.sceneBoundingRect())
    source = source.adjusted(-24, -24, 24, 24)
    height = max(1, math.ceil(width * source.height() / source.width()))
    if not 128 <= width <= 4096 or height > 8192:
        raise GraphError(
            "Resolução acima do limite: largura 128–4.096, altura até 8.192. Reduza a largura."
        )
    suffix = path.suffix.lower()
    if suffix not in {".png", ".svg", ".pdf", ".jpg", ".jpeg"}:
        raise GraphError("Formato de imagem não suportado.")
    visibility = {item: item.isVisible() for item in all_items}
    highlights = (
        canvas.highlight_vertices.copy(),
        canvas.highlight_edges.copy(),
        canvas.current_vertex,
    )
    canvas._syncing = True
    canvas.graph_scene.clearSelection()
    canvas.highlight(set(), set())
    canvas._preview.hide()
    for item in all_items:
        item.setVisible(item in items)
    raw = QByteArray()
    buffer = QBuffer(raw)
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    try:
        if suffix == ".svg":
            device = QSvgGenerator()
            device.setOutputDevice(buffer)
            device.setSize(QSize(width, height))
            device.setViewBox(QRectF(0, 0, width, height))
            device.setTitle("Grafla — grafo exportado")
        elif suffix == ".pdf":
            device = QPdfWriter(buffer)
            device.setResolution(96)
            device.setPageSize(
                QPageSize(QSizeF(width * 25.4 / 96, height * 25.4 / 96), QPageSize.Unit.Millimeter)
            )
            device.setPageMargins(QMarginsF(0, 0, 0, 0))
        else:
            device = QImage(width, height, QImage.Format.Format_ARGB32_Premultiplied)
            device.fill(
                QColor("transparent" if transparent and suffix == ".png" else canvas.theme.canvas)
            )
        painter = QPainter(device)
        if not painter.isActive():
            raise OSError("Não foi possível iniciar a renderização.")
        painter.setRenderHints(
            QPainter.RenderHint.Antialiasing | QPainter.RenderHint.TextAntialiasing
        )
        try:
            if not transparent or suffix in {".pdf", ".jpg", ".jpeg"}:
                painter.fillRect(QRectF(0, 0, width, height), QColor(canvas.theme.canvas))
            canvas.graph_scene.render(painter, QRectF(0, 0, width, height), source)
        finally:
            painter.end()
        if suffix in {".png", ".jpg", ".jpeg"}:
            if not device.save(buffer, "PNG" if suffix == ".png" else "JPG"):
                raise OSError("Não foi possível codificar a imagem.")
        buffer.close()
        from PyQt6.QtCore import QSaveFile

        target = QSaveFile(str(path))
        if not target.open(QIODevice.OpenModeFlag.WriteOnly) or target.write(raw) != raw.size():
            target.cancelWriting()
            raise OSError(target.errorString())
        if not target.commit():
            raise OSError(target.errorString())
    finally:
        for item, visible in visibility.items():
            item.setVisible(visible)
        for item in selected:
            item.setSelected(True)
        canvas._preview.show()
        canvas.highlight(*highlights)
        canvas._syncing = False
    return width, height
