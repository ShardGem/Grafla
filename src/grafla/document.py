"""Alterações validadas do documento, histórico e controle de modificações."""

from __future__ import annotations

import copy
from collections.abc import Callable
from dataclasses import dataclass, replace
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
    origin: str = "edit"
    affects_physics: bool = True


class GraphCommand(QUndoCommand):
    def __init__(
        self, document: Document, label: str, before: Graph, after: Graph, origin: str = "edit"
    ):
        super().__init__(label)
        self.document = document
        self.origin = origin
        self._first_redo = True
        if origin == "physics":
            # A física altera só x/y; os demais atributos e a estrutura são preservados.
            self.vertices = {
                key: (
                    replace(
                        after.vertices[key], x=before.vertices[key].x, y=before.vertices[key].y
                    ),
                    copy.copy(after.vertices[key]),
                )
                for key in before.vertices.keys() & after.vertices.keys()
                if (before.vertices[key].x, before.vertices[key].y)
                != (after.vertices[key].x, after.vertices[key].y)
            }
            self.edges = {}
        else:
            self.vertices = {
                key: (
                    copy.deepcopy(before.vertices.get(key)),
                    copy.deepcopy(after.vertices.get(key)),
                )
                for key in before.vertices.keys() | after.vertices.keys()
                if before.vertices.get(key) != after.vertices.get(key)
            }
            self.edges = {
                key: (copy.deepcopy(before.edges.get(key)), copy.deepcopy(after.edges.get(key)))
                for key in before.edges.keys() | after.edges.keys()
                if before.edges.get(key) != after.edges.get(key)
            }
        self.sequences = (
            (after.next_vertex, after.next_edge)
            if origin == "physics"
            else (before.next_vertex, before.next_edge),
            (after.next_vertex, after.next_edge),
        )
        self.affects_physics = any(
            a is None or b is None or (a.x, a.y, a.pinned) != (b.x, b.y, b.pinned)
            for a, b in self.vertices.values()
        ) or any(
            a is None or b is None or (a.source, a.target) != (b.source, b.target)
            for a, b in self.edges.values()
        )

    def _apply(self, side: int, origin: str) -> None:
        graph = self.document.graph
        # O primeiro registro guarda o movimento que já está na tela.
        # As coordenadas só precisam ser reaplicadas ao desfazer ou refazer.
        patches = (
            ()
            if origin == "physics"
            else ((graph.edges, self.edges), (graph.vertices, self.vertices))
        )
        for collection, changes in patches:
            for key, pair in changes.items():
                target: Edge | Vertex | None = pair[side]
                other = pair[1 - side]
                if target is None:
                    collection.pop(key, None)
                elif other is None or key not in collection:
                    collection[key] = copy.deepcopy(target)
                else:
                    # Cada edição altera só os campos que lhe pertencem.
                    # Desfazer um rótulo não deve trazer de volta posições antigas.
                    for name, value in vars(target).items():
                        if value != getattr(other, name):
                            setattr(collection[key], name, copy.deepcopy(value))
        graph.next_vertex, graph.next_edge = self.sequences[side]
        self.document.revision += 1
        labels = any(
            a is None or b is None or a.label != b.label for a, b in self.vertices.values()
        )
        self.document.changed.emit(
            Change(
                set(self.vertices),
                set(self.edges),
                vertex_labels=labels,
                origin=origin,
                affects_physics=self.affects_physics,
            )
        )

    def redo(self) -> None:
        self._apply(1, self.origin if self._first_redo else "history")
        self._first_redo = False

    def undo(self) -> None:
        self._apply(0, "history")


class Document(QObject):
    changed = pyqtSignal(object)
    dirty_changed = pyqtSignal(bool)
    path_changed = pyqtSignal()
    before_edit = pyqtSignal()
    before_history = pyqtSignal()

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
        after = self.graph.clone()
        mutate(after)
        after.validate()
        self._push(label, self.graph, after)

    def _push(self, label: str, before: Graph, after: Graph, origin: str = "edit") -> None:
        command = GraphCommand(self, label, before, after, origin)
        if command.vertices or command.edges:
            if origin == "edit" and command.affects_physics:
                self.before_edit.emit()
            self.undo_stack.push(command)

    def replace(self, label: str, graph: Graph) -> None:
        graph.validate()
        self._push(label, self.graph, graph)

    def finish_preview(self, label: str, before: Graph) -> None:
        self.graph.validate()
        # Rótulos e estilos podem ser editados durante a simulação.
        # O comando da física guarda apenas as coordenadas.
        self._push(label, before, self.graph, origin="physics")

    def reset(self, graph: Graph | None = None, path: Path | None = None) -> None:
        self.before_edit.emit()
        graph = graph if graph is not None else Graph()
        graph.validate()
        changed = Change(
            set(self.graph.vertices) | set(graph.vertices),
            set(self.graph.edges) | set(graph.edges),
            origin="reset",
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
        self.before_history.emit()
        self.undo_stack.undo()

    def redo(self) -> None:
        self.before_history.emit()
        self.undo_stack.redo()
