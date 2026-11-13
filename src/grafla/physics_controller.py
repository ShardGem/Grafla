from __future__ import annotations

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from grafla.document import Change, Document
from grafla.domain import Graph, GraphError
from grafla.physics import PhysicsParameters, step


class PhysicsController(QObject):
    state_changed = pyqtSignal()

    def __init__(self, document: Document, parent: QObject | None = None):
        super().__init__(parent)
        self.document = document
        self.enabled = False
        self.paused = False
        self.parameters = PhysicsParameters()
        self.center = (0.0, 0.0)
        self.preview_pending = False
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
        self.document.before_history.connect(self.prepare_history)
        self.document.changed.connect(self.on_change)

    @property
    def state(self) -> str:
        if not self.enabled:
            return "Desativada"
        if self.paused:
            return "Pausada"
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
        self.paused = False
        if enabled:
            self.wake()
        self.state_changed.emit()

    def on_change(self, change: Change) -> None:
        if change.origin == "history":
            # A navegação pelo histórico não pode criar comandos nem reativar a física.
            self.timer.stop()
            self.before = None
            self.preview_pending = False
            self.velocities.clear()
            self.paused = self.enabled
            self.state_changed.emit()
            return
        if not change.preview and not self._stepping and not self._finishing:
            if len(self.document.graph.vertices) > 1000 or len(self.document.graph.edges) > 5000:
                self.set_enabled(False)
            elif self.enabled and change.affects_physics and change.origin != "physics":
                self.wake()

    def wake(self) -> None:
        if (
            self.enabled
            and not self.paused
            and self.document.graph.vertices
            and not self.timer.isActive()
        ):
            self.before = self.document.graph.clone()
            nodes = self.document.graph.vertices.values()
            count = len(self.document.graph.vertices)
            self.center = (sum(v.x for v in nodes) / count, sum(v.y for v in nodes) / count)
            self.velocities.clear()
            self.preview_pending = False
            self.iterations = self.stable_ticks = 0
            self.timer.start()
            self.state_changed.emit()

    def prepare_history(self) -> None:
        self.pause(suspend=True)

    def resume(self) -> None:
        self.paused = False
        self.wake()
        self.state_changed.emit()

    def toggle_paused(self) -> None:
        if self.timer.isActive():
            self.pause(suspend=True)
        elif self.enabled:
            self.resume()

    def set_parameters(self, parameters: PhysicsParameters) -> None:
        if parameters != self.parameters:
            self.parameters = parameters
            # Alterar os parâmetros mantém as posições, as velocidades e a sessão atual.
            self.wake()
            self.state_changed.emit()

    def pause(self, *, suspend: bool = False) -> None:
        self.timer.stop()
        if suspend:
            self.paused = self.enabled
        if self.before is not None:
            before, self.before = self.before, None
            self._finishing = True
            try:
                self.document.finish_preview("Organizar com física", before)
            finally:
                self._finishing = False
        self.velocities.clear()
        self.preview_pending = False
        self.state_changed.emit()

    def tick(self) -> None:
        if not self.enabled or self.paused or not self.timer.isActive():
            return
        self._stepping = True
        try:
            moved, speed = step(self.document.graph, self.velocities, self.parameters, self.center)
            for key, (x, y) in moved.items():
                self.document.graph.vertices[key].x = x
                self.document.graph.vertices[key].y = y
            if moved:
                self.document.revision += 1
                self.document.changed.emit(Change(set(moved), set(), preview=True))
                if not self.preview_pending:
                    self.preview_pending = True
                    self.state_changed.emit()
            self.iterations += 1
            self.stable_ticks = self.stable_ticks + 1 if speed < self.parameters.stability else 0
            if self.stable_ticks >= 12 or self.iterations >= 500:
                self.pause()
        finally:
            self._stepping = False
