"""The mutation boundary: validated patches, undo, dirty state and notifications."""

from __future__ import annotations

import copy
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QUndoCommand, QUndoStack

from grafla.domain import Edge, Graph, Vertex
from grafla.persistence import save


@dataclass
class Change:
    vertices: set[int]
    edges: set[int]
    preview: bool = False
    vertex_labels: bool = True


class GraphCommand(QUndoCommand):
    def __init__(self, document: Document, label: str, before: Graph, after: Graph):
        super().__init__(label)
        self.document = document
        self.vertices = {
            key: (copy.deepcopy(before.vertices.get(key)), copy.deepcopy(after.vertices.get(key)))
            for key in before.vertices.keys() | after.vertices.keys()
            if before.vertices.get(key) != after.vertices.get(key)
        }
        self.edges = {
            key: (copy.deepcopy(before.edges.get(key)), copy.deepcopy(after.edges.get(key)))
            for key in before.edges.keys() | after.edges.keys()
            if before.edges.get(key) != after.edges.get(key)
        }
        self.sequences = (
            (before.next_vertex, before.next_edge),
            (after.next_vertex, after.next_edge),
        )

    def _apply(self, side: int) -> None:
        graph = self.document.graph
        for key, pair in self.edges.items():
            edge: Edge | None = pair[side]
            if edge is None:
                graph.edges.pop(key, None)
            else:
                graph.edges[key] = copy.deepcopy(edge)
        for key, values in self.vertices.items():
            vertex: Vertex | None = values[side]
            if vertex is None:
                graph.vertices.pop(key, None)
            else:
                graph.vertices[key] = copy.deepcopy(vertex)
        graph.next_vertex, graph.next_edge = self.sequences[side]
        self.document.revision += 1
        labels = any(
            a is None or b is None or a.label != b.label for a, b in self.vertices.values()
        )
        self.document.changed.emit(
            Change(set(self.vertices), set(self.edges), vertex_labels=labels)
        )

    def redo(self) -> None:
        self._apply(1)

    def undo(self) -> None:
        self._apply(0)


class Document(QObject):
    changed = pyqtSignal(object)
    dirty_changed = pyqtSignal(bool)
    path_changed = pyqtSignal()
    before_edit = pyqtSignal()

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self.graph = Graph()
        self.path: Path | None = None
        self.revision = 0
        self.undo_stack = QUndoStack(self)
        self.undo_stack.setUndoLimit(60)
        self.undo_stack.cleanChanged.connect(self._clean_changed)

    @pyqtSlot(bool)
    def _clean_changed(self, clean: bool) -> None:
        self.dirty_changed.emit(not clean)

    @property
    def dirty(self) -> bool:
        return not self.undo_stack.isClean()

    def edit(self, label: str, mutate: Callable[[Graph], object]) -> None:
        self.before_edit.emit()
        after = self.graph.clone()
        mutate(after)
        after.validate()
        self._push(label, self.graph, after)

    def _push(self, label: str, before: Graph, after: Graph) -> None:
        command = GraphCommand(self, label, before, after)
        if command.vertices or command.edges:
            self.undo_stack.push(command)

    def replace(self, label: str, graph: Graph) -> None:
        self.before_edit.emit()
        graph.validate()
        self._push(label, self.graph, graph)

    def finish_preview(self, label: str, before: Graph) -> None:
        self.graph.validate()
        self._push(label, before, self.graph)

    def reset(self, graph: Graph | None = None, path: Path | None = None) -> None:
        self.before_edit.emit()
        graph = graph if graph is not None else Graph()
        graph.validate()
        changed = Change(
            set(self.graph.vertices) | set(graph.vertices), set(self.graph.edges) | set(graph.edges)
        )
        self.graph = graph.clone()
        self.path = path
        self.revision += 1
        self.undo_stack.clear()
        self.changed.emit(changed)
        self.dirty_changed.emit(False)
        self.path_changed.emit()

    def write(self, path: Path) -> None:
        self.before_edit.emit()
        save(path, self.graph)
        self.path = path
        self.undo_stack.setClean()
        self.path_changed.emit()

    def undo(self) -> None:
        self.before_edit.emit()
        self.undo_stack.undo()

    def redo(self) -> None:
        self.before_edit.emit()
        self.undo_stack.redo()
