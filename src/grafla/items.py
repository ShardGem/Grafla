from __future__ import annotations

import math
from typing import TYPE_CHECKING

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import (
    QColor,
    QFont,
    QFontMetricsF,
    QPainter,
    QPainterPath,
    QPainterPathStroker,
    QPen,
)
from PyQt6.QtWidgets import QGraphicsEllipseItem, QGraphicsItem, QGraphicsPathItem

from grafla.domain import Edge, Vertex

if TYPE_CHECKING:
    from grafla.canvas import Canvas


class VertexItem(QGraphicsEllipseItem):
    def __init__(self, vertex: Vertex, canvas: Canvas):
        self.vertex, self.canvas = vertex, canvas
        super().__init__()
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setAcceptHoverEvents(True)
        self.setZValue(2)
        self.refresh(vertex)

    def refresh(self, vertex: Vertex):
        self.prepareGeometryChange()
        self.vertex = vertex
        r = vertex.radius
        self.setRect(-r, -r, 2 * r, 2 * r)
        self.setPen(QPen(Qt.GlobalColor.transparent, 10))  # includes selection ring in bounds
        self.setPos(vertex.x, vertex.y)
        self.setToolTip(
            f"{vertex.label or vertex.id} · Vértice #{vertex.id}"
            + (" · fixado" if vertex.pinned else "")
        )
        self.update()

    def paint(self, painter, option, widget=None):
        theme = self.canvas.theme
        key = self.vertex.id
        active = (
            self.isSelected()
            or key in self.canvas.highlight_vertices
            or key in self.canvas.neighbor_vertices
        )
        hovered = self.isUnderMouse()
        dimmed = (
            (self.canvas.highlight_vertices or self.canvas.highlight_edges)
            and not active
            and not hovered
        )
        if dimmed:
            painter.setOpacity(0.45)
        highlight_color = (
            theme.visited
            if self.canvas.current_vertex is not None
            and key != self.canvas.current_vertex
            and not self.isSelected()
            else theme.accent
        )
        color = QColor(highlight_color if active else self.vertex.color)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(color, 2 if active or hovered else 1.4))
        fill = QColor(theme.panel)
        painter.setBrush(fill)
        painter.drawEllipse(self.rect())
        if self.canvas.current_vertex == key:
            painter.setPen(QPen(QColor(theme.accent), 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(self.rect().adjusted(-3, -3, 3, 3))
        if self.isSelected() or self.canvas.edge_start == key:
            painter.setPen(QPen(QColor(theme.accent), 1.4, Qt.PenStyle.DashLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(self.rect().adjusted(-4, -4, 4, 4))
        painter.setOpacity(1)
        painter.setPen(
            QColor(highlight_color if active else (theme.muted if dimmed else theme.text))
        )
        font = QFont()
        font.setPointSizeF(10)
        font.setBold(active)
        painter.setFont(font)
        label = self.vertex.label or str(key)
        label = QFontMetricsF(font).elidedText(
            label, Qt.TextElideMode.ElideRight, self.rect().width() - 8
        )
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, label)
        if self.vertex.pinned:
            painter.drawText(
                QRectF(-6, -self.vertex.radius - 18, 12, 14), Qt.AlignmentFlag.AlignCenter, "•"
            )

    def boundingRect(self):
        return super().boundingRect().adjusted(0, -16 if self.vertex.pinned else 0, 0, 0)

    def itemChange(self, change, value):
        result = super().itemChange(change, value)
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self.canvas.update_incident(self.vertex.id)
        return result

    def hoverEnterEvent(self, event):
        self.canvas.hover_vertex(self.vertex.id)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.canvas.hover_vertex(None)
        super().hoverLeaveEvent(event)


class EdgeItem(QGraphicsPathItem):
    def __init__(self, edge: Edge, canvas: Canvas):
        super().__init__()
        self.edge, self.canvas = edge, canvas
        self.line_path, self.arrow_path = QPainterPath(), QPainterPath()
        self.label_rect = QRectF()
        self.label = ""
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setAcceptHoverEvents(True)
        self.setZValue(-1)

    def refresh(self, edge: Edge):
        self.edge = edge
        self.setToolTip(
            f"Aresta #{edge.id} · {edge.source} {'→' if edge.directed else '—'} {edge.target}"
            + (f" · peso {edge.weight:g}" if edge.weighted else "")
        )
        self.update_geometry()

    def update_geometry(self):
        a = self.canvas.vertices.get(self.edge.source)
        b = self.canvas.vertices.get(self.edge.target)
        if a is None or b is None:
            return
        p, q = a.pos(), b.pos()
        path = QPainterPath()
        if a is b:
            r = a.vertex.radius
            path.moveTo(p + QPointF(-r * 0.7, -r * 0.7))
            path.cubicTo(
                p + QPointF(-r * 3, -r * 4),
                p + QPointF(r * 3, -r * 4),
                p + QPointF(r * 0.7, -r * 0.7),
            )
        else:
            dx, dy = q.x() - p.x(), q.y() - p.y()
            distance = max(0.001, math.hypot(dx, dy))
            direction = QPointF(dx / distance, dy / distance)
            start = p + direction * a.vertex.radius
            end = q - direction * b.vertex.radius
            path.moveTo(start)
            opposite = (self.edge.target, self.edge.source) in self.canvas.pairs
            if opposite:
                control = (p + q) * 0.5 + QPointF(-direction.y(), direction.x()) * 44
                path.quadTo(control, end)
            else:
                path.lineTo(end)
        arrow = QPainterPath()
        if self.edge.directed:
            tip = path.pointAtPercent(1)
            near = path.pointAtPercent(0.94)
            dx, dy = tip.x() - near.x(), tip.y() - near.y()
            length = max(0.001, math.hypot(dx, dy))
            unit = QPointF(dx / length, dy / length)
            normal = QPointF(-unit.y(), unit.x())
            arrow.moveTo(tip)
            arrow.lineTo(tip - unit * 12 + normal * 5)
            arrow.lineTo(tip - unit * 12 - normal * 5)
            arrow.closeSubpath()
        label = self.edge.label
        if self.edge.weighted:
            label = f"{label} · {self.edge.weight:g}" if label else f"{self.edge.weight:g}"
        middle = path.pointAtPercent(0.5)
        font = QFont()
        font.setPointSizeF(9)
        label = QFontMetricsF(font).elidedText(label, Qt.TextElideMode.ElideRight, 140)
        width = QFontMetricsF(font).horizontalAdvance(label) + 14 if label else 0
        self.prepareGeometryChange()
        self.label_rect = QRectF(middle.x() - width / 2, middle.y() - 12, width, 24)
        self.label = label
        self.line_path, self.arrow_path = path, arrow
        combined = QPainterPath(path)
        combined.addPath(arrow)
        self.setPath(combined)
        self.update()

    def shape(self):
        stroker = QPainterPathStroker()
        stroker.setWidth(14)
        shape = stroker.createStroke(self.path())
        if self.label:
            shape.addRect(self.label_rect)
        return shape

    def boundingRect(self):
        return self.shape().boundingRect().adjusted(-2, -2, 2, 2)

    def paint(self, painter, option, widget=None):
        theme = self.canvas.theme
        active = (
            self.isSelected()
            or self.edge.id in self.canvas.highlight_edges
            or self.edge.id in self.canvas.neighbor_edges
        )
        if (
            (self.canvas.highlight_vertices or self.canvas.highlight_edges)
            and not active
            and not self.isUnderMouse()
        ):
            painter.setOpacity(0.25)
        highlight_color = (
            theme.visited
            if self.canvas.current_vertex is not None and not self.isSelected()
            else theme.accent
        )
        color = QColor(highlight_color if active or self.isUnderMouse() else self.edge.color)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(color, 3 if active else 1.8)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(self.line_path)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.drawPath(self.arrow_path)
        if self.label:
            painter.setOpacity(1)
            painter.setBrush(QColor(theme.canvas))
            painter.drawRoundedRect(self.label_rect, 4, 4)
            painter.setPen(QColor(theme.text))
            font = QFont()
            font.setPointSizeF(9)
            painter.setFont(font)
            painter.drawText(self.label_rect, Qt.AlignmentFlag.AlignCenter, self.label)
