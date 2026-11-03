from __future__ import annotations

import math

from PyQt6.QtCore import QPoint, QPointF, QRectF, Qt, pyqtSignal
from PyQt6.QtGui import (
    QColor,
    QPainter,
    QPainterPath,
    QPen,
    QPolygonF,
)
from PyQt6.QtWidgets import (
    QGraphicsPathItem,
    QGraphicsScene,
    QGraphicsView,
    QLabel,
    QMenu,
    QVBoxLayout,
)

from grafla.document import Change, Document
from grafla.domain import GraphError
from grafla.items import EdgeItem, VertexItem
from grafla.theme import DARK, Theme


class Canvas(QGraphicsView):
    selection_changed = pyqtSignal(object)
    edge_requested = pyqtSignal(int, int)
    inspect_requested = pyqtSignal()
    zoom_changed = pyqtSignal(float)
    interaction_started = pyqtSignal()
    mode_changed = pyqtSignal(str)
    message = pyqtSignal(str)

    def __init__(self, document: Document, parent=None):
        super().__init__(parent)
        self.document = document
        self.theme: Theme = DARK
        self.graph_scene = QGraphicsScene(self)
        self.setScene(self.graph_scene)
        self.setSceneRect(-1e7, -1e7, 2e7, 2e7)
        self.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.TextAntialiasing)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.NoAnchor)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.MinimalViewportUpdate)
        self.setAccessibleName("Editor de grafos")
        self.setAccessibleDescription(
            "V selecionar; N criar vértice; E conectar; Espaço e arrastar para navegar."
        )
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.vertices: dict[int, VertexItem] = {}
        self.edges: dict[int, EdgeItem] = {}
        self.incident: dict[int, set[int]] = {}
        self.pairs: dict[tuple[int, int], int] = {}
        self.highlight_vertices: set[int] = set()
        self.highlight_edges: set[int] = set()
        self.neighbor_vertices: set[int] = set()
        self.neighbor_edges: set[int] = set()
        self.current_vertex: int | None = None
        self.mode = "select"
        self.edge_start: int | None = None
        self.show_grid = True
        self.snap = False
        self._syncing = False
        self._dragging = False
        self._pan: QPoint | None = None
        self._space = False
        self._preview = QGraphicsPathItem()
        self._preview.setZValue(-2)
        self.graph_scene.addItem(self._preview)
        self.empty = QLabel(
            "<h2>Uma ideia. Muitas conexões.</h2><p>Pressione <b>N</b> e clique para criar seu primeiro vértice.</p><p>Ctrl+O · abrir grafo &nbsp;&nbsp; Ctrl+K · buscar comandos</p>",
            self.viewport(),
        )
        self.empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty.setWordWrap(True)
        self.empty.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.empty.setProperty("muted", True)
        overlay = QVBoxLayout(self.viewport())
        overlay.addWidget(self.empty, alignment=Qt.AlignmentFlag.AlignCenter)
        self.document.changed.connect(self.reconcile)
        self.graph_scene.selectionChanged.connect(self.emit_selection)
        self.centerOn(0, 0)

    def selection(self) -> tuple[set[int], set[int]]:
        nodes, edges = set(), set()
        for item in self.graph_scene.selectedItems():
            if isinstance(item, VertexItem):
                nodes.add(item.vertex.id)
            elif isinstance(item, EdgeItem):
                edges.add(item.edge.id)
        return nodes, edges

    def emit_selection(self):
        if not self._syncing:
            self.selection_changed.emit(self.selection())

    def reconcile(self, change: Change):
        self._syncing = True
        graph = self.document.graph
        affected = set(change.edges)
        for key in change.edges:
            old = self.edges.get(key)
            if old is not None:
                # Removing an opposite edge also changes the survivor's curvature.
                affected.update(
                    self.incident.get(old.edge.source, set())
                    & self.incident.get(old.edge.target, set())
                )
        for key in change.vertices:
            affected.update(self.incident.get(key, set()))
        try:
            for key in list(self.edges):
                if key not in graph.edges:
                    self.graph_scene.removeItem(self.edges.pop(key))
            for key in list(self.vertices):
                if key not in graph.vertices:
                    self.graph_scene.removeItem(self.vertices.pop(key))
            for key in change.vertices:
                if key not in graph.vertices:
                    continue
                if key not in self.vertices:
                    item = VertexItem(graph.vertices[key], self)
                    self.vertices[key] = item
                    self.graph_scene.addItem(item)
                else:
                    self.vertices[key].refresh(graph.vertices[key])
            if change.edges or set(self.incident) != set(graph.vertices):
                self.pairs = {(e.source, e.target): e.id for e in graph.edges.values()}
                self.incident = {key: set() for key in graph.vertices}
                for edge in graph.edges.values():
                    self.incident[edge.source].add(edge.id)
                    self.incident[edge.target].add(edge.id)
                for key in change.edges:
                    edge = graph.edges.get(key)
                    if edge:
                        affected.update(self.incident[edge.source] & self.incident[edge.target])
            for key in affected:
                if key not in graph.edges:
                    continue
                if key not in self.edges:
                    item = EdgeItem(graph.edges[key], self)
                    self.edges[key] = item
                    self.graph_scene.addItem(item)
                self.edges[key].refresh(graph.edges[key])
            if self.edge_start not in graph.vertices:
                self.edge_start = None
            self.empty.setVisible(not graph.vertices)
        finally:
            self._syncing = False
        if not change.preview:
            self.emit_selection()

    def update_incident(self, key: int):
        if not self._syncing:
            for edge_id in self.incident.get(key, set()):
                if edge_id in self.edges:
                    self.edges[edge_id].update_geometry()

    def set_theme(self, theme: Theme):
        self.theme = theme
        self.setBackgroundBrush(QColor(theme.canvas))
        self._preview.setPen(QPen(QColor(theme.accent), 1.8, Qt.PenStyle.DashLine))
        self.graph_scene.update()
        self.viewport().update()

    def set_mode(self, mode: str):
        self.cancel_edge()
        self.mode = mode
        self.setDragMode(
            QGraphicsView.DragMode.RubberBandDrag
            if mode == "select"
            else QGraphicsView.DragMode.NoDrag
        )
        cursor = (
            Qt.CursorShape.OpenHandCursor
            if mode == "hand"
            else (
                Qt.CursorShape.CrossCursor
                if mode in {"vertex", "edge"}
                else Qt.CursorShape.ArrowCursor
            )
        )
        self.setCursor(cursor)
        self.mode_changed.emit(mode)

    def cancel_edge(self):
        old, self.edge_start = self.edge_start, None
        self._preview.setPath(QPainterPath())
        if old in self.vertices:
            self.vertices[old].update()

    def object_at(self, point: QPoint):
        item = self.itemAt(point)
        return item if isinstance(item, (VertexItem, EdgeItem)) else None

    def mousePressEvent(self, event):
        self.setFocus()
        if event.button() == Qt.MouseButton.MiddleButton or (
            event.button() == Qt.MouseButton.LeftButton and (self._space or self.mode == "hand")
        ):
            self._pan = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return
        if event.button() != Qt.MouseButton.LeftButton:
            super().mousePressEvent(event)
            return
        self.interaction_started.emit()
        item = self.object_at(event.pos())
        position = self.mapToScene(event.pos())
        if self.mode == "vertex" and item is None:
            self.create_vertex(position)
            return
        if self.mode == "delete":
            if item:
                self.graph_scene.clearSelection()
                item.setSelected(True)
                self.delete_selection()
            return
        if self.mode == "edge":
            if isinstance(item, VertexItem):
                if self.edge_start is None:
                    self.edge_start = item.vertex.id
                    item.update()
                else:
                    start = self.edge_start
                    self.cancel_edge()
                    self.edge_requested.emit(start, item.vertex.id)
            return
        self._dragging = isinstance(item, VertexItem)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._pan is not None:
            delta = event.pos() - self._pan
            self._pan = event.pos()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            return
        if self.edge_start in self.vertices:
            path = QPainterPath(self.vertices[self.edge_start].pos())
            path.lineTo(self.mapToScene(event.pos()))
            self._preview.setPath(path)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._pan is not None:
            self._pan = None
            self.setCursor(
                Qt.CursorShape.OpenHandCursor if self.mode == "hand" else Qt.CursorShape.ArrowCursor
            )
            return
        super().mouseReleaseEvent(event)
        if self._dragging:
            positions = {}
            for key, item in self.vertices.items():
                vertex = self.document.graph.vertices[key]
                x, y = item.pos().x(), item.pos().y()
                if self.snap:
                    x, y = round(x / 40) * 40, round(y / 40) * 40
                if (x, y) != (vertex.x, vertex.y):
                    positions[key] = (x, y)
            self.move_vertices(positions, "Mover vértices")
            self._dragging = False

    def move_vertices(self, positions: dict[int, tuple[float, float]], label="Mover vértices"):
        def move(graph):
            for key, (x, y) in positions.items():
                graph.vertices[key].x, graph.vertices[key].y = x, y

        if positions:
            try:
                self.document.edit(label, move)
            except GraphError as error:
                self.reconcile(Change(set(positions), set()))
                self.message.emit(str(error))

    def create_vertex(self, position: QPointF):
        x, y = position.x(), position.y()
        if self.snap:
            x, y = round(x / 40) * 40, round(y / 40) * 40
        try:
            self.document.edit("Criar vértice", lambda graph: graph.add_vertex(x, y))
        except GraphError as error:
            self.message.emit(str(error))

    def delete_selection(self):
        nodes, edges = self.selection()
        if nodes or edges:
            self.document.edit("Excluir seleção", lambda graph: graph.remove(nodes, edges))
            self.message.emit(
                f"{len(nodes)} vértice(s) e {len(edges)} aresta(s) selecionados removidos."
            )

    def mouseDoubleClickEvent(self, event):
        item = self.object_at(event.pos())
        if item is not None:
            self.graph_scene.clearSelection()
            item.setSelected(True)
            self.inspect_requested.emit()
        elif self.mode == "select":
            self.create_vertex(self.mapToScene(event.pos()))
        event.accept()

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        item = self.object_at(event.pos())
        if item and not item.isSelected():
            self.graph_scene.clearSelection()
            item.setSelected(True)
        if item:
            menu.addAction("Editar propriedades", self.inspect_requested.emit)
            menu.addAction("Excluir seleção", self.delete_selection)
        else:
            position = self.mapToScene(event.pos())
            menu.addAction("Criar vértice aqui", lambda: self.create_vertex(position))
        menu.addSeparator()
        menu.addAction("Ajustar grafo", self.fit_graph)
        menu.addAction("Selecionar tudo", self.select_all)
        menu.exec(event.globalPos())

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Space and not event.isAutoRepeat():
            self._space = True
            self.setCursor(Qt.CursorShape.OpenHandCursor)
            event.accept()
        elif event.key() == Qt.Key.Key_Escape:
            self.cancel_edge()
            self.graph_scene.clearSelection()
        elif event.key() == Qt.Key.Key_Delete:
            self.delete_selection()
        else:
            super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key.Key_Space and not event.isAutoRepeat():
            self._space = False
            self._pan = None
            self.setCursor(
                Qt.CursorShape.OpenHandCursor if self.mode == "hand" else Qt.CursorShape.ArrowCursor
            )
        else:
            super().keyReleaseEvent(event)

    def focusOutEvent(self, event):
        self._space = False
        self._pan = None
        super().focusOutEvent(event)

    def zoom(self, factor: float, point: QPoint | None = None):
        point = point if point is not None else self.viewport().rect().center()
        before = self.mapToScene(point)
        old = self.transform().m11()
        target = min(4.0, max(0.02, old * factor))
        self.scale(target / old, target / old)
        after = self.mapToScene(point)
        delta = after - before
        self.translate(delta.x(), delta.y())
        self.zoom_changed.emit(target)

    def wheelEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.zoom(1.15 if event.angleDelta().y() > 0 else 1 / 1.15, event.position().toPoint())
            event.accept()
        else:
            super().wheelEvent(event)

    def fit_graph(self):
        items = list(self.vertices.values()) + list(self.edges.values())
        if not items:
            self.reset_view()
            return
        bounds = QRectF()
        for item in items:
            bounds = bounds.united(item.sceneBoundingRect())
        self.fitInView(bounds.adjusted(-70, -70, 70, 70), Qt.AspectRatioMode.KeepAspectRatio)
        if self.transform().m11() > 2:
            self.zoom(2 / self.transform().m11())
        self.zoom_changed.emit(self.transform().m11())

    def fit_selection(self):
        items = self.graph_scene.selectedItems()
        if not items:
            return
        bounds = QRectF()
        for item in items:
            bounds = bounds.united(item.sceneBoundingRect())
        self.fitInView(bounds.adjusted(-80, -80, 80, 80), Qt.AspectRatioMode.KeepAspectRatio)
        if self.transform().m11() > 2:
            self.zoom(2 / self.transform().m11())
        self.zoom_changed.emit(self.transform().m11())

    def reset_view(self):
        self.resetTransform()
        if self.vertices:
            bounds = self.graph_scene.itemsBoundingRect()
            self.centerOn(bounds.center())
        else:
            self.centerOn(0, 0)
        self.zoom_changed.emit(1.0)

    def select_all(self):
        self.graph_scene.blockSignals(True)
        try:
            for item in self.vertices.values():
                item.setSelected(True)
            for item in self.edges.values():
                item.setSelected(True)
        finally:
            self.graph_scene.blockSignals(False)
        self.emit_selection()

    def hover_vertex(self, key: int | None):
        old_nodes, old_edges = self.neighbor_vertices, self.neighbor_edges
        self.neighbor_vertices, self.neighbor_edges = set(), set()
        if key is not None and not self.highlight_vertices and not self.highlight_edges:
            self.neighbor_edges = self.incident.get(key, set()).copy()
            self.neighbor_vertices = {key}
            for edge_id in self.neighbor_edges:
                edge = self.document.graph.edges[edge_id]
                self.neighbor_vertices.update((edge.source, edge.target))
        for node in old_nodes | self.neighbor_vertices:
            if node in self.vertices:
                self.vertices[node].update()
        for edge_id in old_edges | self.neighbor_edges:
            if edge_id in self.edges:
                self.edges[edge_id].update()

    def highlight(self, nodes: set[int], edges: set[int], current: int | None = None):
        old_mask = bool(self.highlight_vertices or self.highlight_edges)
        changed_nodes = self.highlight_vertices | nodes
        changed_edges = self.highlight_edges | edges
        self.highlight_vertices, self.highlight_edges = nodes, edges
        self.current_vertex = current
        if nodes or edges:
            self.hover_vertex(None)
        if old_mask != bool(nodes or edges):
            self.graph_scene.update()
        for key in changed_nodes:
            if key in self.vertices:
                self.vertices[key].update()
        for key in changed_edges:
            if key in self.edges:
                self.edges[key].update()

    def highlight_path(self, path: list[int]):
        edges = set()
        for a, b in zip(path, path[1:], strict=False):
            key = self.pairs.get((a, b))
            if key is None:
                reverse = self.pairs.get((b, a))
                if (
                    reverse in self.document.graph.edges
                    and not self.document.graph.edges[reverse].directed
                ):
                    key = reverse
            if key is not None:
                edges.add(key)
        self.highlight(set(path), edges)

    def drawBackground(self, painter: QPainter, rect: QRectF):
        super().drawBackground(painter, rect)
        if not self.show_grid:
            return
        step = 40
        while step * self.transform().m11() < 18:
            step *= 2
        points = QPolygonF(
            [
                QPointF(x, y)
                for x in range(math.floor(rect.left() / step) * step, math.ceil(rect.right()), step)
                for y in range(math.floor(rect.top() / step) * step, math.ceil(rect.bottom()), step)
            ]
        )
        pen = QPen(QColor(self.theme.grid), 1.5)
        pen.setCosmetic(True)
        painter.setPen(pen)
        painter.drawPoints(points)
