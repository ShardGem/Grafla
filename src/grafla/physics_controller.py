from __future__ import annotations

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from grafla.document import Change, Document
from grafla.domain import Graph, GraphError
from grafla.physics import step


class PhysicsController(QObject):
    state_changed = pyqtSignal()

    def __init__(self, document: Document, parent: QObject | None = None):
        super().__init__(parent)
        self.document = document
        self.enabled = False
        self.timer = QTimer(self)
        self.timer.setInterval(30)
        self.timer.timeout.connect(self.tick)
        self.velocities: dict[int, tuple[float, float]] = {}
        self.before: Graph | None = None
        self.iterations = 0
        self.stable_ticks = 0
        self._stepping = False
        self._finishing = False
        self.document.before_edit.connect(self.pause)
        self.document.changed.connect(self.on_change)

    @property
    def state(self) -> str:
        if not self.enabled:
            return "Desativada"
        return "Em movimento" if self.timer.isActive() else "Em repouso"

    def set_enabled(self, enabled: bool) -> None:
        if enabled and (
            len(self.document.graph.vertices) > 1000 or len(self.document.graph.edges) > 5000
        ):
            raise GraphError(
                "Física interativa limitada a 1.000 vértices e 5.000 arestas. Use layouts para grafos maiores."
            )
        if not enabled:
            self.pause()
        self.enabled = enabled
        if enabled:
            self.wake()
        self.state_changed.emit()

    def on_change(self, change: Change) -> None:
        if not change.preview and not self._stepping and not self._finishing:
            if len(self.document.graph.vertices) > 1000 or len(self.document.graph.edges) > 5000:
                self.set_enabled(False)
            elif self.enabled:
                self.wake()

    def wake(self) -> None:
        if self.enabled and self.document.graph.vertices and not self.timer.isActive():
            self.before = self.document.graph.clone()
            self.velocities.clear()
            self.iterations = self.stable_ticks = 0
            self.timer.start()
            self.state_changed.emit()

    def pause(self) -> None:
        self.timer.stop()
        if self.before is not None:
            before, self.before = self.before, None
            self._finishing = True
            try:
                self.document.finish_preview("Organizar com física", before)
            finally:
                self._finishing = False
        self.velocities.clear()
        self.state_changed.emit()

    def tick(self) -> None:
        if not self.enabled:
            self.pause()
            return
        self._stepping = True
        try:
            moved, speed = step(self.document.graph, self.velocities)
            for key, (x, y) in moved.items():
                self.document.graph.vertices[key].x = x
                self.document.graph.vertices[key].y = y
            if moved:
                self.document.revision += 1
                self.document.changed.emit(Change(set(moved), set(), preview=True))
            self.iterations += 1
            self.stable_ticks = self.stable_ticks + 1 if speed < 0.07 else 0
            if self.stable_ticks >= 12 or self.iterations >= 500:
                self.pause()
        finally:
            self._stepping = False
