from __future__ import annotations

import logging
from pathlib import Path

from PyQt6.QtCore import QByteArray, QMimeData, QSettings, Qt, QTimer
from PyQt6.QtGui import QAction, QActionGroup, QKeySequence
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QSpinBox,
    QVBoxLayout,
)

from grafla import __version__
from grafla.analysis_controller import AnalysisController
from grafla.canvas import Canvas
from grafla.dialogs import PreferencesDialog, SearchDialog, buttons
from grafla.document import Change, Document
from grafla.domain import GraphError, layout_positions
from grafla.exporting import export_graph
from grafla.file_actions import FileActions
from grafla.icons import icon
from grafla.persistence import DocumentError, decode, encode
from grafla.physics_controller import PhysicsController
from grafla.theme import apply, resolve

logger = logging.getLogger(__name__)
TOOL_NAMES = {
    "select": "Selecionar",
    "hand": "Mão",
    "vertex": "Vértice",
    "edge": "Aresta",
    "delete": "Apagar",
}


class MainWindow(QMainWindow):
    def __init__(self, data_dir: Path, settings: QSettings | None = None):
        super().__init__()
        self.setObjectName("GraflaWindow")
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.settings = settings if settings is not None else QSettings()
        self.resize(1366, 820)
        self.document = Document(self)
        self.physics = PhysicsController(self.document, self)
        self.canvas = Canvas(self.document)
        self.commands: dict[str, QAction] = {}
        self.command_icons: dict[str, str] = {}
        self.files = FileActions(self, data_dir)
        self._build_actions()
        self._build_shell()
        self.runner = AnalysisController(self)
        self.document.changed.connect(self.on_document_change)
        self.document.dirty_changed.connect(self.update_title)
        self.document.path_changed.connect(self.update_title)
        self.physics.state_changed.connect(self.physics_state)
        self.canvas.selection_changed.connect(self.on_selection)
        self.canvas.edge_requested.connect(self.add_edge)
        self.canvas.interaction_started.connect(self.physics.pause)
        self.canvas.inspect_requested.connect(self.focus_inspector)
        self.canvas.message.connect(self.notify)
        self.canvas.zoom_changed.connect(self.update_zoom)
        self.canvas.mode_changed.connect(self.update_status)
        self.inspector.apply_requested.connect(self.apply_properties)
        self.analysis.run_requested.connect(self.runner.run_analysis)
        self.analysis.cancel_requested.connect(self.runner.stop_execution)
        self.analysis.clear_requested.connect(self.runner.clear_analysis)
        self.analysis.next_requested.connect(self.runner.navigate_result)
        self.analysis.play_requested.connect(self.runner.toggle_playback)
        self.analysis.restart_requested.connect(self.runner.restart)
        self.analysis.speed.valueChanged.connect(self.runner.update_speed)
        self.analysis.browser.index_selected.connect(self.runner.select_result)
        self.analysis.algorithm.currentIndexChanged.connect(self.runner.parameters_changed)
        self.analysis.origin.currentIndexChanged.connect(self.runner.parameters_changed)
        self.analysis.destination.currentIndexChanged.connect(self.runner.parameters_changed)
        self.autosave_timer = QTimer(self)
        self.autosave_timer.setInterval(60_000)
        self.autosave_timer.timeout.connect(self.files.autosave)
        self.autosave_timer.start()
        self.apply_preferences()
        self.canvas.set_mode("select")
        self.on_document_change(Change(set(), set()))
        geometry = self.settings.value("geometry")
        if isinstance(geometry, QByteArray):
            self.restoreGeometry(geometry)
        state = self.settings.value("window_state")
        if isinstance(state, QByteArray):
            self.restoreState(state, 1)
        self.physics_state()
        self.update_title()
        self.physics.set_enabled(self.settings.value("physics", False, type=bool))
        QApplication.styleHints().colorSchemeChanged.connect(self.system_theme_changed)

    def action(
        self, key, title, callback, shortcut=None, image=None, canvas_only=False, checkable=False
    ):
        action = QAction(title, self)
        action.setObjectName(key)
        action.setCheckable(checkable)
        if shortcut:
            action.setShortcuts(
                [QKeySequence(s) for s in shortcut]
                if isinstance(shortcut, list)
                else [QKeySequence(shortcut)]
            )
        if canvas_only:
            action.setShortcutContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
            self.canvas.addAction(action)
        else:
            self.addAction(action)
        action.triggered.connect(callback)
        action.setToolTip(f"{title}  {action.shortcut().toString()}".strip())
        self.commands[key] = action
        if image:
            self.command_icons[key] = image
        return action

    def _build_actions(self):
        self.action("new", "Novo", self.files.new, "Ctrl+N", "new")
        self.action("open", "Abrir…", lambda: self.files.open(), "Ctrl+O", "open")
        self.action("save", "Salvar", lambda: self.files.save(), "Ctrl+S", "save")
        self.action("save_as", "Salvar como…", lambda: self.files.save(True), "Ctrl+Shift+S")
        self.action("export", "Exportar imagem…", self.export_dialog, "Ctrl+Shift+E")
        self.action("quit", "Sair", self.close, "Ctrl+Q")
        self.action("undo", "Desfazer", self.document.undo, "Ctrl+Z", "undo")
        self.action("redo", "Refazer", self.document.redo, ["Ctrl+Shift+Z", "Ctrl+Y"], "redo")
        self.document.undo_stack.canUndoChanged.connect(self.commands["undo"].setEnabled)
        self.document.undo_stack.canRedoChanged.connect(self.commands["redo"].setEnabled)
        self.commands["undo"].setEnabled(False)
        self.commands["redo"].setEnabled(False)
        self.action("copy", "Copiar subgrafo", self.copy_selection, "Ctrl+C", canvas_only=True)
        self.action("paste", "Colar subgrafo", self.paste_selection, "Ctrl+V", canvas_only=True)
        self.action(
            "select_all", "Selecionar tudo", self.canvas.select_all, "Ctrl+A", canvas_only=True
        )
        self.action(
            "delete_selection",
            "Excluir seleção",
            self.canvas.delete_selection,
            "Delete",
            canvas_only=True,
        )
        self.action("clear", "Limpar grafo", self.clear_graph)
        self.action("preferences", "Preferências…", self.preferences, "Ctrl+,")
        self.action(
            "search", "Buscar comandos e vértices…", self.search, ["Ctrl+K", "Ctrl+F"], "search"
        )
        self.action("fit", "Ajustar grafo", self.canvas.fit_graph, "Ctrl+0", "fit")
        self.action(
            "fit_selection", "Ajustar seleção", self.canvas.fit_selection, "F", canvas_only=True
        )
        self.action("reset_view", "Zoom 100%", self.canvas.reset_view, "Ctrl+1")
        self.action("zoom_in", "Aproximar", lambda: self.canvas.zoom(1.2), "Ctrl++")
        self.action("zoom_out", "Afastar", lambda: self.canvas.zoom(1 / 1.2), "Ctrl+-")
        self.action("generate", "Gerar grafo…", self.generate, "Ctrl+G", "physics")
        for key, label in (("circular", "Circular"), ("grid", "Grade"), ("random", "Aleatório")):
            self.action(
                f"layout_{key}",
                f"Layout {label}",
                lambda checked=False, kind=key: self.apply_layout(kind),
            )
        self.action("to_matrix", "Grafo → matriz…", lambda: self.matrix(False), image="grid")
        self.action("from_matrix", "Matriz → grafo…", lambda: self.matrix(True))
        self.action(
            "physics", "Física", self.toggle_physics, "Ctrl+Shift+P", "physics", checkable=True
        )
        self.action("about", "Sobre o Grafla", self.about)
        self.tool_group = QActionGroup(self)
        self.tool_group.setExclusive(True)
        for key, shortcut in (
            ("select", "V"),
            ("hand", "H"),
            ("vertex", "N"),
            ("edge", "E"),
            ("delete", "B"),
        ):
            action = self.action(
                f"tool_{key}",
                TOOL_NAMES[key],
                lambda checked=False, mode=key: self.canvas.set_mode(mode),
                shortcut,
                key,
                canvas_only=True,
                checkable=True,
            )
            self.tool_group.addAction(action)
        self.commands["tool_select"].setChecked(True)

    def _build_shell(self):
        from grafla.shell import build_shell

        build_shell(self)

    def notify(self, message: str, error=False):
        self.statusBar().showMessage(message, 10_000 if error else 5000)
        if error:
            self.analysis.status.setText(message)
            logger.warning(message)

    def update_title(self, *args):
        name = self.document.path.name if self.document.path else "Sem título.grafla"
        self.setWindowTitle(f"{name}[*] — Grafla")
        self.setWindowModified(self.document.dirty)
        self.document_name.setText(name + ("  ·  Modificado" if self.document.dirty else ""))
        self.document_name.setToolTip(name)
        self.saved_state.setText(
            "● Modificado" if self.document.dirty else ("Salvo" if self.document.path else "Local")
        )

    def update_status(self, *args):
        graph = self.document.graph
        self.graph_status.setText(
            f"  {len(graph.vertices)} vértices  ·  {len(graph.edges)} arestas  ·  {graph.kind}  ·  {TOOL_NAMES[self.canvas.mode]}"
        )
        for key in TOOL_NAMES:
            action = self.commands[f"tool_{key}"]
            action.setChecked(key == self.canvas.mode)
            if hasattr(self, "theme"):
                action.setIcon(
                    icon(
                        key,
                        self.theme.accent if action.isChecked() else self.theme.text,
                        action.isChecked(),
                    )
                )

    def update_zoom(self, scale):
        self.zoom_controls.set_scale(scale)

    def on_document_change(self, change):
        if not change.preview:
            self.runner.clear_analysis(stale=True)
            if change.vertex_labels:
                self.analysis.refresh_vertices(self.document.graph)
            self.on_selection(self.canvas.selection())
            self.building.matrix.set_graph(self.document.graph)
            self.update_title()
        self.update_status()

    def on_selection(self, selection):
        self.inspector.refresh(self.document.graph, selection)
        self.commands["delete_selection"].setEnabled(any(selection))
        self.commands["copy"].setEnabled(any(selection))

    def focus_inspector(self):
        self.workspace.show()
        self.tabs.setCurrentWidget(self.inspector)
        self.inspector.vertex_label.setFocus() if self.inspector.stack.currentIndex() == 1 else self.inspector.setFocus()

    def add_edge(self, source, target):
        try:
            self.document.edit(
                "Criar aresta",
                lambda graph: graph.add_edge(
                    source,
                    target,
                    self.inspector.create_directed.isChecked(),
                    self.inspector.create_weighted.isChecked(),
                    self.inspector.create_weight.value(),
                ),
            )
        except GraphError as error:
            self.notify(str(error), error=True)

    def apply_properties(self, values):
        nodes, edges = self.canvas.selection()
        values = dict(values)
        if self.physics.timer.isActive():
            # Coordinates shown before the simulation are not a requested move.
            values.pop("x", None)
            values.pop("y", None)

        def update(graph):
            for item in [graph.vertices[key] for key in nodes] + [
                graph.edges[key] for key in edges
            ]:
                for key, value in values.items():
                    setattr(item, key, value)

        try:
            self.document.edit("Atualizar propriedades", update)
            self.notify("Propriedades atualizadas.")
        except GraphError as error:
            self.notify(str(error), error=True)

    def clear_graph(self):
        if self.document.graph.vertices:
            self.document.edit(
                "Limpar grafo", lambda graph: graph.remove(set(graph.vertices), set(graph.edges))
            )

    def generate(self):
        self.physics.pause()
        self.workspace.show()
        self.tabs.setCurrentIndex(2)
        self.building.setCurrentIndex(0)

    def matrix(self, importing):
        self.physics.pause()
        self.workspace.show()
        self.tabs.setCurrentIndex(2)
        self.building.setCurrentIndex(1)
        self.building.matrix.set_graph(self.document.graph)
        self.building.matrix.mode.setCurrentIndex(1 if importing else 0)
        self.building.matrix.rebuild()

    def replace_graph(self, label, graph):
        self.document.replace(label, graph)
        self.canvas.fit_graph()
        self.notify("Grafo atualizado. Ctrl+Z desfaz a operação.")

    def set_grid(self, enabled):
        self.canvas.show_grid = enabled
        self.settings.setValue("grid", enabled)
        self.canvas.viewport().update()

    def set_snap(self, enabled):
        self.canvas.snap = enabled
        self.settings.setValue("snap", enabled)

    def apply_layout(self, kind):
        self.physics.pause()
        self.canvas.move_vertices(layout_positions(self.document.graph, kind), "Aplicar layout")
        self.canvas.fit_graph()

    def toggle_physics(self, checked):
        try:
            self.physics.set_enabled(checked)
            self.settings.setValue("physics", checked)
        except GraphError as error:
            self.physics_state()
            self.notify(str(error), error=True)

    def physics_state(self):
        action = self.commands["physics"]
        action.blockSignals(True)
        action.setChecked(self.physics.enabled)
        action.blockSignals(False)
        self.physics_label.setText(f"  {self.physics.state}  ")
        for spin in (self.inspector.vertex_x, self.inspector.vertex_y):
            spin.setEnabled(not self.physics.timer.isActive())

    def apply_preferences(self):
        self.theme = resolve(self.settings.value("theme", "dark"))
        apply(QApplication.instance(), self.theme)
        self.canvas.set_theme(self.theme)
        self.canvas.show_grid = self.settings.value("grid", True, type=bool)
        self.canvas.snap = self.settings.value("snap", False, type=bool)
        for control, checked in (
            (self.zoom_controls.grid, self.canvas.show_grid),
            (self.zoom_controls.snap, self.canvas.snap),
        ):
            control.blockSignals(True)
            control.setChecked(checked)
            control.blockSignals(False)
        for key, name in self.command_icons.items():
            self.commands[key].setIcon(icon(name, self.theme.text))
        self.update_status()

    def preferences(self):
        dialog = PreferencesDialog(self.settings, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.apply_preferences()

    def system_theme_changed(self, *args):
        if self.settings.value("theme", "dark") == "system":
            self.apply_preferences()

    def search(self):
        dialog = SearchDialog(
            list(self.commands.values()), self.document.graph.vertices.values(), self
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            if isinstance(dialog.chosen, QAction):
                dialog.chosen.trigger()
            elif isinstance(dialog.chosen, int) and dialog.chosen in self.canvas.vertices:
                self.canvas.graph_scene.clearSelection()
                item = self.canvas.vertices[dialog.chosen]
                item.setSelected(True)
                self.canvas.centerOn(item)
                self.canvas.setFocus()

    def populate_recent(self):
        self.recent_menu.clear()
        for name in self.files.recent_paths():
            self.recent_menu.addAction(
                name, lambda checked=False, path=name: self.files.open(Path(path))
            )
        if not self.recent_menu.actions():
            self.recent_menu.addAction("Nenhum arquivo recente").setEnabled(False)

    def copy_selection(self):
        vertices, edges = self.canvas.selection()
        graph = self.document.graph.clone()
        for key in edges:
            edge = graph.edges[key]
            vertices.update((edge.source, edge.target))
        graph.remove(set(graph.vertices) - vertices, set())
        mime = QMimeData()
        raw = encode(graph)
        mime.setData("application/x-grafla-subgraph", QByteArray(raw))
        mime.setText(raw.decode())
        QApplication.clipboard().setMimeData(mime)
        self.notify("Subgrafo copiado.")

    def paste_selection(self):
        mime = QApplication.clipboard().mimeData()
        raw = (
            bytes(mime.data("application/x-grafla-subgraph"))
            if mime.hasFormat("application/x-grafla-subgraph")
            else mime.text().encode()
        )
        try:
            source = decode(raw)

            def paste(graph):
                mapping = {}
                for vertex in source.vertices.values():
                    new = graph.add_vertex(vertex.x + 40, vertex.y + 40, vertex.label)
                    new.color, new.radius, new.pinned = vertex.color, vertex.radius, vertex.pinned
                    mapping[vertex.id] = new.id
                for edge in source.edges.values():
                    new = graph.add_edge(
                        mapping[edge.source],
                        mapping[edge.target],
                        edge.directed,
                        edge.weighted,
                        edge.weight,
                    )
                    new.color, new.label = edge.color, edge.label

            self.document.edit("Colar subgrafo", paste)
        except (DocumentError, GraphError) as error:
            self.notify(f"Não foi possível colar: {error}", error=True)

    def export_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Exportar grafo")
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("Largura em pixels (SVG e PDF permanecem vetoriais)"))
        width = QSpinBox()
        width.setRange(128, 4096)
        width.setValue(1600)
        selection = QCheckBox("Somente seleção")
        transparent = QCheckBox("Fundo transparente (PNG/SVG)")
        for widget in (width, selection, transparent):
            layout.addWidget(widget)
        layout.addWidget(buttons(dialog, "Escolher arquivo…"))
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        name, chosen = QFileDialog.getSaveFileName(
            self,
            "Exportar imagem",
            "grafo.png",
            "PNG (*.png);;SVG (*.svg);;PDF (*.pdf);;JPEG (*.jpg)",
        )
        if not name:
            return
        path = Path(name)
        if not path.suffix:
            path = path.with_suffix(
                {"SVG": ".svg", "PDF": ".pdf", "JPEG": ".jpg"}.get(chosen.split()[0], ".png")
            )
        try:
            export_graph(
                self.canvas, path, width.value(), selection.isChecked(), transparent.isChecked()
            )
            self.notify("Imagem exportada.")
        except (OSError, GraphError) as error:
            self.notify(str(error), error=True)

    def about(self):
        QMessageBox.about(
            self,
            "Sobre o Grafla",
            f"<h2>Grafla {__version__}</h2><p>Construir. Explorar. Compreender.</p><p>Editor de grafos com Python, PyQt6 e NetworkX.</p><p>PyQt6: GPLv3 / licença comercial. Qt: termos por módulo. NetworkX: BSD-3-Clause.</p><p>V selecionar · H mão · N vértice · E aresta<br>Ctrl+K buscar · Ctrl+Z desfazer · Ctrl+Shift+P física</p>",
        )

    def closeEvent(self, event):
        if not self.files.maybe_save():
            event.ignore()
            return
        self.runner.cancel_analysis()
        self.physics.set_enabled(False)
        self.autosave_timer.stop()
        self.files.clear_recovery()
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("window_state", self.saveState(1))
        self.settings.sync()
        self.runner.pool.waitForDone(2500)
        event.accept()
