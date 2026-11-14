"""Prévia das propriedades, separada dos dados confirmados e do histórico."""

import copy

from PyQt6.QtCore import QObject

from grafla.domain import GraphError


class PropertyEditor(QObject):
    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.selection = None
        self.pending = {}
        window.inspector.preview_requested.connect(self.preview)
        window.inspector.cancel_requested.connect(self.cancel)
        window.document.before_edit.connect(self.cancel)
        window.document.before_history.connect(self.cancel)
        window.document.changed.connect(self.document_changed)
        window.canvas.interaction_started.connect(self.cancel)
        window.canvas.mode_changed.connect(self.cancel)
        window.tabs.currentChanged.connect(lambda index: self.cancel() if index != 0 else None)
        window.workspace.visibilityChanged.connect(
            lambda visible: None if visible else self.cancel()
        )

    def preview(self, values):
        window = self.window
        selection = window.canvas.selection()
        if self.selection is not None and selection != self.selection:
            self.cancel(refresh=False)
        self.selection = selection
        self.pending = dict(values)
        if window.physics.timer.isActive():
            self.pending.pop("x", None)
            self.pending.pop("y", None)
        vertices, edges = selection
        # Copia só os elementos editados; o restante continua sendo apenas lido.
        graph = copy.copy(window.document.graph)
        graph.vertices = dict(graph.vertices)
        graph.edges = dict(graph.edges)
        for key in vertices:
            graph.vertices[key] = copy.copy(graph.vertices[key])
        for key in edges:
            graph.edges[key] = copy.copy(graph.edges[key])
        try:
            for item in [graph.vertices[key] for key in vertices] + [
                graph.edges[key] for key in edges
            ]:
                for key, value in self.pending.items():
                    setattr(item, key, value)
            graph.validate()
        except GraphError as error:
            window.inspector.feedback.setText(str(error))
            window.inspector.feedback.show()
            return
        window.inspector.feedback.setText(
            "Prévia · Aplicar confirma; Cancelar restaura." if values else ""
        )
        window.inspector.feedback.setVisible(bool(values))
        window.canvas.show_property_preview(graph, vertices, edges)

    def cancel(self, *args, refresh=True):
        if self.selection is None:
            return
        selection, self.selection = self.selection, None
        self.pending = {}
        window = self.window
        window.canvas.show_property_preview(window.document.graph, *selection)
        if refresh:
            window.inspector.refresh(window.document.graph, window.canvas.selection())

    def document_changed(self, change):
        if self.selection is None:
            return
        if change.preview or change.origin == "physics":
            vertices, edges = self.selection
            if len(vertices) == 1 and not edges:
                vertex = self.window.document.graph.vertices[next(iter(vertices))]
                self.window.inspector.follow_position(vertex, self.pending)
            self.preview(self.pending)
        else:
            self.cancel(refresh=False)
