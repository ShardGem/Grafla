import pytest
from PyQt6.QtCore import QPoint, QPointF, Qt
from PyQt6.QtGui import QImage, QWheelEvent
from PyQt6.QtTest import QSignalSpy
from PyQt6.QtWidgets import QFileDialog, QMessageBox

from grafla.dialogs import GenerateDialog, MatrixDialog, PreferencesDialog, SearchDialog
from grafla.domain import Graph
from grafla.exporting import export_graph
from grafla.items import EdgeItem
from grafla.persistence import load


def populate(window, graph):
    window.document.reset(graph)
    window.canvas.fit_graph()


def test_canvas_creation_connection_and_delete_are_real_mouse_actions(window, qtbot):
    canvas = window.canvas
    canvas.setFocus()
    qtbot.keyClick(canvas, Qt.Key.Key_N)
    assert canvas.mode == "vertex"
    point1 = canvas.viewport().rect().center() - QPoint(100, 0)
    point2 = point1 + QPoint(200, 0)
    qtbot.mouseClick(canvas.viewport(), Qt.MouseButton.LeftButton, pos=point1)
    qtbot.mouseClick(canvas.viewport(), Qt.MouseButton.LeftButton, pos=point2)
    assert len(window.document.graph.vertices) == 2
    qtbot.keyClick(canvas, Qt.Key.Key_E)
    qtbot.mouseClick(canvas.viewport(), Qt.MouseButton.LeftButton, pos=point1)
    qtbot.mouseClick(canvas.viewport(), Qt.MouseButton.LeftButton, pos=point2)
    assert len(window.document.graph.edges) == 1
    qtbot.keyClick(canvas, Qt.Key.Key_V)
    mid = (point1 + point2) / 2
    qtbot.mouseClick(canvas.viewport(), Qt.MouseButton.LeftButton, pos=mid)
    assert canvas.selection()[1] == {1}
    qtbot.keyClick(canvas, Qt.Key.Key_Delete)
    assert not canvas.edges
    assert not window.document.graph.edges
    window.document.undo()
    assert len(canvas.edges) == len(window.document.graph.edges) == 1


def test_multiselection_and_group_move_is_one_undo(window, qtbot, graph):
    populate(window, graph)
    canvas = window.canvas
    canvas.setFocus()
    first = canvas.mapFromScene(canvas.vertices[1].pos())
    second = canvas.mapFromScene(canvas.vertices[2].pos())
    qtbot.mouseClick(canvas.viewport(), Qt.MouseButton.LeftButton, pos=first)
    qtbot.mouseClick(
        canvas.viewport(),
        Qt.MouseButton.LeftButton,
        modifier=Qt.KeyboardModifier.ControlModifier,
        pos=second,
    )
    assert canvas.selection()[0] == {1, 2}
    before = window.document.graph.clone()
    qtbot.mousePress(canvas.viewport(), Qt.MouseButton.LeftButton, pos=first)
    qtbot.mouseMove(canvas.viewport(), first + QPoint(30, 40), delay=20)
    qtbot.mouseRelease(canvas.viewport(), Qt.MouseButton.LeftButton, pos=first + QPoint(30, 40))
    assert window.document.graph.vertices[1].x != before.vertices[1].x
    assert window.document.graph.vertices[2].x != before.vertices[2].x
    assert window.document.undo_stack.count() == 1
    window.document.undo()
    assert window.document.graph == before


def test_property_edit_and_text_shortcuts_do_not_change_tools(window, qtbot, graph):
    populate(window, graph)
    window.canvas.vertices[1].setSelected(True)
    window.focus_inspector()
    field = window.inspector.vertex_label
    field.setFocus()
    qtbot.keyClicks(field, "NEHV")
    assert field.text() == "NEHV"
    assert window.canvas.mode == "select"
    assert len(window.document.graph.vertices) == 3
    qtbot.mouseClick(window.inspector.apply_button, Qt.MouseButton.LeftButton)
    assert window.document.graph.vertices[1].label == "NEHV"
    window.document.undo()
    assert window.document.graph.vertices[1].label == ""


def test_edge_inspector_updates_model_and_rejects_invalid_color(window, qtbot, graph):
    populate(window, graph)
    window.canvas.edges[1].setSelected(True)
    window.inspector.edge_weight.setValue(9)
    qtbot.mouseClick(window.inspector.apply_button, Qt.MouseButton.LeftButton)
    assert window.document.graph.edges[1].weight == 9
    assert window.canvas.edges[1].edge.weight == 9
    window.inspector.edge_color.setText("invalid")
    qtbot.mouseClick(window.inspector.apply_button, Qt.MouseButton.LeftButton)
    assert window.document.graph.edges[1].color != "invalid"
    assert "Cor inválida" in window.statusBar().currentMessage()


def test_unrelated_property_edit_does_not_round_persisted_values(window, graph):
    graph.vertices[1].x = 0.123456789
    graph.edges[1].weight = 0.00123456789
    populate(window, graph)
    window.canvas.vertices[1].setSelected(True)
    window.inspector.vertex_label.setText("Precisão")
    window.inspector.submit()
    assert window.document.graph.vertices[1].x == 0.123456789
    window.canvas.graph_scene.clearSelection()
    window.canvas.edges[1].setSelected(True)
    window.inspector.edge_label.setText("Peso preservado")
    window.inspector.submit()
    assert window.document.graph.edges[1].weight == 0.00123456789


def test_only_incident_edges_recompute_after_one_vertex_moves(window, graph, monkeypatch):
    populate(window, graph)
    calls = []
    original = EdgeItem.update_geometry

    def update(item):
        calls.append(item.edge.id)
        original(item)

    monkeypatch.setattr(EdgeItem, "update_geometry", update)
    window.document.edit("Mover", lambda g: setattr(g.vertices[1], "x", -40))
    assert calls == [1]
    for edge in window.canvas.edges.values():
        assert edge.boundingRect().contains(edge.arrow_path.boundingRect())


def test_removing_opposite_edge_straightens_survivor_and_undo_recurves(window, graph):
    graph.add_edge(2, 1, True)
    populate(window, graph)
    survivor = window.canvas.edges[1]
    assert abs(survivor.line_path.pointAtPercent(0.5).y()) > 1
    window.document.edit("Excluir oposta", lambda g: g.remove(set(), {3}))
    assert survivor.line_path.pointAtPercent(0.5).y() == 0
    window.document.undo()
    assert abs(survivor.line_path.pointAtPercent(0.5).y()) > 1


def test_idle_canvas_has_no_continuous_scene_updates(window, graph, qtbot):
    populate(window, graph)
    qtbot.wait(60)
    spy = QSignalSpy(window.canvas.graph_scene.changed)
    qtbot.wait(100)
    assert len(spy) == 0


def test_cursor_zoom_and_space_pan(window, qtbot, graph):
    populate(window, graph)
    canvas = window.canvas
    point = canvas.viewport().rect().center() + QPoint(70, 30)
    before = canvas.mapToScene(point)
    event = QWheelEvent(
        QPointF(point),
        QPointF(canvas.viewport().mapToGlobal(point)),
        QPoint(),
        QPoint(0, 120),
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.ControlModifier,
        Qt.ScrollPhase.NoScrollPhase,
        False,
    )
    window.canvas.wheelEvent(event)
    after = canvas.mapToScene(point)
    assert (after - before).manhattanLength() < 2
    old_center = canvas.mapToScene(canvas.viewport().rect().center())
    canvas.setFocus()
    qtbot.keyPress(canvas, Qt.Key.Key_Space)
    qtbot.mousePress(canvas.viewport(), Qt.MouseButton.LeftButton, pos=point)
    qtbot.mouseMove(canvas.viewport(), point + QPoint(70, 30), delay=20)
    qtbot.mouseRelease(canvas.viewport(), Qt.MouseButton.LeftButton, pos=point + QPoint(70, 30))
    qtbot.keyRelease(canvas, Qt.Key.Key_Space)
    new_center = canvas.mapToScene(canvas.viewport().rect().center())
    assert (new_center - old_center).manhattanLength() > 10
    assert canvas.mode == "select"


def test_physics_toggle_freezes_positions_and_undo_restores(window, graph, qtbot):
    populate(window, graph)
    before = window.document.graph.clone()
    window.commands["physics"].trigger()
    assert window.physics.enabled and window.physics.timer.isActive()
    qtbot.waitUntil(
        lambda: window.document.graph.vertices[1].x != before.vertices[1].x, timeout=1000
    )
    window.commands["physics"].trigger()
    assert not window.physics.enabled and not window.physics.timer.isActive()
    frozen = window.document.graph.clone()
    qtbot.wait(100)
    assert window.document.graph == frozen
    window.document.undo()
    assert window.document.graph == before
    window.commands["physics"].trigger()
    assert window.physics.timer.isActive()
    window.commands["physics"].trigger()


def test_physics_sleeps_at_equilibrium_without_disabling_control(window, qtbot):
    graph = Graph()
    graph.add_vertex(0, 0)
    populate(window, graph)
    window.physics.set_enabled(True)
    qtbot.waitUntil(lambda: not window.physics.timer.isActive(), timeout=1500)
    assert window.physics.enabled
    assert window.physics.state == "Em repouso"
    window.document.edit("Criar", lambda g: g.add_vertex(60, 0))
    assert window.physics.timer.isActive()


def test_label_edit_during_physics_does_not_restore_stale_coordinates(window, graph, qtbot):
    populate(window, graph)
    window.canvas.vertices[1].setSelected(True)
    window.physics.set_enabled(True)
    qtbot.waitUntil(
        lambda: window.document.graph.vertices[1].x != graph.vertices[1].x, timeout=1000
    )
    current = window.document.graph.vertices[1].x
    window.inspector.vertex_label.setText("Nova origem")
    window.inspector.submit()
    window.physics.set_enabled(False)
    assert window.document.graph.vertices[1].label == "Nova origem"
    assert window.document.graph.vertices[1].x == current


def test_save_open_cancel_and_invalid_open_preserve_document(
    window, graph, qtbot, tmp_path, monkeypatch
):
    window.document.replace("Criar", graph)
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *a, **k: ("", ""))
    assert not window.files.save()
    assert window.document.dirty
    path = tmp_path / "saved.grafla"
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *a, **k: (str(path), ""))
    assert window.files.save()
    assert load(path) == graph
    window.document.edit("Rótulo", lambda g: setattr(g.vertices[1], "label", "dirty"))
    before = window.document.graph.clone()
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Cancel)
    assert not window.files.open(path)
    assert window.document.graph == before
    assert not window.files.open(tmp_path / "missing.grafla")
    assert window.document.graph == before
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Discard)
    assert window.files.open(path)
    assert window.document.graph == graph
    assert not window.document.dirty


def test_native_window_states_and_close_cancel(window, graph, qtbot, monkeypatch):
    assert not window.windowFlags() & Qt.WindowType.FramelessWindowHint
    window.showMaximized()
    assert window.isMaximized()
    window.showNormal()
    assert not window.isMaximized()
    window.showMinimized()
    assert window.isMinimized()
    window.showNormal()
    window.document.replace("Criar", graph)
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Cancel)
    assert not window.close()
    assert window.isVisible()


def test_generate_cancel_and_matrix_import_undo(window, graph, monkeypatch):
    populate(window, graph)
    monkeypatch.setattr(GenerateDialog, "exec", lambda dialog: 0)
    window.generate()
    assert window.document.graph == graph

    def accept_matrix(dialog):
        dialog.count.setValue(2)
        dialog.model.setData(dialog.model.index(0, 1), "1")
        dialog.accept()
        return 1

    monkeypatch.setattr(MatrixDialog, "exec", accept_matrix)
    window.matrix(True)
    assert len(window.document.graph.vertices) == 2
    assert len(window.document.graph.edges) == 1
    window.document.undo()
    assert window.document.graph == graph


def test_background_algorithm_playback_and_invalidation(window, graph, qtbot):
    populate(window, graph)
    window.tabs.setCurrentIndex(1)
    panel = window.analysis
    panel.destination.setCurrentIndex(2)
    qtbot.mouseClick(panel.run, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: window.runner.result is not None, timeout=3000)
    assert window.runner.result.costs == [3]
    assert "Custo: 3" in window.results.toPlainText()
    window.document.edit(
        "Não direcionado", lambda g: [setattr(e, "directed", False) for e in g.edges.values()]
    )
    panel.algorithm.setCurrentIndex(panel.algorithm.findData("mst"))
    window.runner.run_analysis()
    qtbot.waitUntil(lambda: window.runner.result is not None, timeout=3000)
    assert window.canvas.highlight_edges == {1, 2}
    assert not panel.play.isEnabled()
    assert "Custo total: 3" in window.results.toPlainText()
    panel.algorithm.setCurrentIndex(panel.algorithm.findData("bfs"))
    window.runner.run_analysis()
    qtbot.waitUntil(lambda: window.runner.result is not None, timeout=3000)
    assert window.runner.result.steps == [[1], [2], [3]]
    window.runner.navigate_result(1)
    assert window.canvas.highlight_vertices == {1, 2}
    assert window.canvas.highlight_edges == {1}
    window.runner.restart()
    assert window.canvas.highlight_vertices == {1}
    window.runner.toggle_playback()
    assert window.runner.playback.isActive()
    window.document.edit("Mudar", lambda g: setattr(g.vertices[2], "label", "novo"))
    assert window.runner.result is None
    assert not window.runner.playback.isActive()
    assert "mudou" in panel.status.text()


def test_background_result_cannot_attach_to_edited_document(window, qtbot):
    from grafla.domain import generate_graph

    populate(window, generate_graph(9, 72, True, False))
    window.analysis.algorithm.setCurrentIndex(window.analysis.algorithm.findData("all"))
    window.analysis.destination.setCurrentIndex(8)
    window.runner.run_analysis()
    window.document.edit("Excluir destino", lambda g: g.remove({9}, set()))
    qtbot.wait(150)
    assert window.runner.result is None
    assert not window.canvas.highlight_vertices


@pytest.mark.parametrize(
    "suffix,signature",
    [("png", b"\x89PNG"), ("jpg", b"\xff\xd8"), ("svg", b"<?xml"), ("pdf", b"%PDF")],
)
def test_export_produces_real_file_and_restores_selection(
    window, graph, tmp_path, suffix, signature
):
    populate(window, graph)
    window.canvas.vertices[1].setSelected(True)
    window.canvas.highlight_path([1, 2, 3])
    path = tmp_path / f"export.{suffix}"
    export_graph(window.canvas, path, 800, transparent=True)
    assert path.read_bytes().startswith(signature)
    assert window.canvas.selection()[0] == {1}
    assert window.canvas.highlight_vertices == {1, 2, 3}
    if suffix == "png":
        image = QImage(str(path))
        assert image.width() == 800
        assert image.pixelColor(0, 0).alpha() == 0


def test_failed_export_restores_items(window, graph, tmp_path):
    populate(window, graph)
    window.canvas.vertices[1].setSelected(True)
    with pytest.raises(OSError):
        export_graph(window.canvas, tmp_path / "absent" / "image.svg", 800, selection=True)
    assert all(item.isVisible() for item in window.canvas.vertices.values())
    assert window.canvas.selection()[0] == {1}


def test_preferences_search_clipboard_and_recovery_are_integrated(
    window, graph, tmp_path, monkeypatch
):
    populate(window, graph)
    window.canvas.vertices[1].setSelected(True)
    window.canvas.vertices[2].setSelected(True)
    window.copy_selection()
    window.paste_selection()
    assert len(window.document.graph.vertices) == 5
    assert len(window.document.graph.edges) == 3
    window.document.undo()
    assert window.document.graph == graph
    window.document.edit("Dirty", lambda g: setattr(g.vertices[1], "label", "recuperável"))
    window.files.autosave()
    assert window.files.recovery.exists()
    assert load(window.files.recovery) == window.document.graph
    assert window.document.dirty
    dialog = PreferencesDialog(window.settings, window)
    dialog.theme.setCurrentIndex(dialog.theme.findData("light"))
    dialog.snap.setChecked(True)
    dialog.accept()
    window.apply_preferences()
    assert window.theme.canvas == "#fafbfd" and window.canvas.snap
    palette = SearchDialog(list(window.commands.values()), graph.vertices.values(), window)
    palette.search.setText("vértice #2")
    assert palette.list.count() == 1
    palette.choose_current()
    assert palette.chosen == 2


def test_recovery_is_dirty_new_document_and_does_not_overwrite_original(window, graph, monkeypatch):
    populate(window, graph)
    window.document.edit("Editar", lambda g: setattr(g.vertices[1], "label", "Recuperar"))
    window.files.autosave()
    window.document.reset()
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Yes)
    window.files.offer_recovery()
    assert window.document.path is None
    assert window.document.graph.vertices[1].label == "Recuperar"
    assert window.document.dirty
