"""Regressões de interação, histórico e ajustes da física."""

from dataclasses import asdict

import pytest
from PyQt6.QtCore import QPoint, QPointF, Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtTest import QSignalSpy

from grafla.document import Document
from grafla.domain import Graph
from grafla.icons import icon
from grafla.main_window import MainWindow
from grafla.physics import PhysicsParameters


def populate(window, graph):
    window.document.reset(graph)
    window.canvas.fit_graph()
    window.canvas.setFocus()


def click_vertex(qtbot, canvas, key):
    qtbot.mouseClick(
        canvas.viewport(),
        Qt.MouseButton.LeftButton,
        pos=canvas.mapFromScene(canvas.vertices[key].pos()),
    )


@pytest.mark.parametrize("double", [False, True])
def test_repeated_vertex_click_in_edge_mode_creates_loop_without_selection(
    window, graph, qtbot, double
):
    populate(window, graph)
    canvas = window.canvas
    canvas.vertices[2].setSelected(True)
    canvas.set_mode("edge")
    inspector = QSignalSpy(canvas.inspect_requested)
    click_vertex(qtbot, canvas, 1)
    assert canvas.edge_start == 1
    assert canvas.selection() == (set(), set())
    point = canvas.mapFromScene(canvas.vertices[1].pos())
    action = qtbot.mouseDClick if double else qtbot.mouseClick
    action(canvas.viewport(), Qt.MouseButton.LeftButton, pos=point)
    assert len(window.document.graph.edges) == 3
    assert window.document.graph.edges[3].source == window.document.graph.edges[3].target == 1
    assert canvas.edge_start is None
    assert canvas.selection() == (set(), set())
    assert not inspector
    assert canvas.mode == "edge"


def test_disallowed_loop_cancels_origin_and_background_escape_cancel_preview(window, graph, qtbot):
    populate(window, graph)
    canvas = window.canvas
    window.inspector.allow_loops.setChecked(False)
    canvas.set_mode("edge")
    click_vertex(qtbot, canvas, 1)
    click_vertex(qtbot, canvas, 1)
    assert len(window.document.graph.edges) == 2
    assert canvas.edge_start is None
    click_vertex(qtbot, canvas, 1)
    qtbot.mouseMove(canvas.viewport(), canvas.viewport().rect().center() + QPoint(0, 100))
    assert not canvas._preview.path().isEmpty()
    qtbot.keyClick(canvas, Qt.Key.Key_Escape)
    assert canvas.edge_start is None and canvas._preview.path().isEmpty()
    click_vertex(qtbot, canvas, 1)
    qtbot.mouseClick(canvas.viewport(), Qt.MouseButton.LeftButton, pos=QPoint(20, 20))
    assert canvas.edge_start is None
    assert not window.cancel_connection.isVisible()


def test_chain_mode_continues_only_after_successful_connection(window, graph, qtbot):
    populate(window, graph)
    canvas = window.canvas
    window.inspector.chain_edges.setChecked(True)
    window.inspector.create_directed.setChecked(True)
    canvas.set_mode("edge")
    click_vertex(qtbot, canvas, 1)
    click_vertex(qtbot, canvas, 3)
    assert canvas.edge_start == 3
    click_vertex(qtbot, canvas, 2)
    assert canvas.edge_start == 2
    assert (window.document.graph.edges[4].source, window.document.graph.edges[4].target) == (3, 2)
    # A conexão 2 → 3 já existe; a tentativa não pode deixar origem ou seleção pendente.
    click_vertex(qtbot, canvas, 3)
    assert len(window.document.graph.edges) == 4
    assert canvas.edge_start is None
    assert canvas.selection() == (set(), set())
    assert "já existe" in window.statusBar().currentMessage()


@pytest.mark.parametrize("mode", ["vertex", "edge", "hand"])
def test_construction_and_navigation_never_drag_or_inspect_vertices(window, graph, qtbot, mode):
    populate(window, graph)
    canvas = window.canvas
    canvas.set_mode(mode)
    spy = QSignalSpy(canvas.inspect_requested)
    point = canvas.mapFromScene(canvas.vertices[1].pos())
    qtbot.mousePress(canvas.viewport(), Qt.MouseButton.LeftButton, pos=point)
    qtbot.mouseMove(canvas.viewport(), point + QPoint(25, 25))
    qtbot.mouseRelease(canvas.viewport(), Qt.MouseButton.LeftButton, pos=point + QPoint(25, 25))
    point = canvas.mapFromScene(canvas.vertices[2].pos())
    qtbot.mouseDClick(canvas.viewport(), Qt.MouseButton.LeftButton, pos=point)
    assert not spy
    assert canvas.selection() == (set(), set())
    for key, vertex in graph.vertices.items():
        assert (window.document.graph.vertices[key].x, window.document.graph.vertices[key].y) == (
            vertex.x,
            vertex.y,
        )
    assert not canvas._dragging


def test_switching_modes_clears_connection_and_pan_restores_mode_cursor(window, graph, qtbot):
    populate(window, graph)
    canvas = window.canvas
    canvas.set_mode("edge")
    click_vertex(qtbot, canvas, 1)
    canvas.set_mode("vertex")
    assert canvas.edge_start is None and canvas._preview.path().isEmpty()
    point = canvas.viewport().rect().center()
    qtbot.keyPress(canvas, Qt.Key.Key_Space)
    qtbot.mousePress(canvas.viewport(), Qt.MouseButton.LeftButton, pos=point)
    qtbot.mouseMove(canvas.viewport(), point + QPoint(30, 20))
    qtbot.mouseRelease(canvas.viewport(), Qt.MouseButton.LeftButton, pos=point + QPoint(30, 20))
    qtbot.keyRelease(canvas, Qt.Key.Key_Space)
    assert canvas.mode == "vertex"
    assert canvas.cursor().shape() == Qt.CursorShape.CrossCursor
    assert len(window.document.graph.vertices) == 3


def test_selection_toggles_clears_and_box_selects(window, graph, qtbot):
    populate(window, graph)
    canvas = window.canvas
    click_vertex(qtbot, canvas, 1)
    point = canvas.mapFromScene(canvas.vertices[2].pos())
    qtbot.mouseClick(
        canvas.viewport(),
        Qt.MouseButton.LeftButton,
        modifier=Qt.KeyboardModifier.ControlModifier,
        pos=point,
    )
    assert canvas.selection()[0] == {1, 2}
    qtbot.mouseClick(
        canvas.viewport(),
        Qt.MouseButton.LeftButton,
        modifier=Qt.KeyboardModifier.ControlModifier,
        pos=point,
    )
    assert canvas.selection()[0] == {1}
    qtbot.mouseClick(canvas.viewport(), Qt.MouseButton.LeftButton, pos=QPoint(20, 20))
    assert canvas.selection() == (set(), set())
    start = canvas.mapFromScene(QPointF(-55, -55))
    end = canvas.mapFromScene(QPointF(235, 55))
    qtbot.mousePress(canvas.viewport(), Qt.MouseButton.LeftButton, pos=start)
    qtbot.mouseMove(canvas.viewport(), end, delay=20)
    qtbot.mouseRelease(canvas.viewport(), Qt.MouseButton.LeftButton, pos=end)
    assert canvas.selection()[0] == {1, 2}


def test_snap_does_not_move_untouched_vertices_on_click_or_drag(window, graph, qtbot):
    for vertex in graph.vertices.values():
        vertex.x += 13
        vertex.y = 7
    populate(window, graph)
    canvas = window.canvas
    window.set_snap(True)
    click_vertex(qtbot, canvas, 1)
    assert window.document.graph == graph
    assert window.document.undo_stack.count() == 0
    point = canvas.mapFromScene(canvas.vertices[1].pos())
    qtbot.mousePress(canvas.viewport(), Qt.MouseButton.LeftButton, pos=point)
    qtbot.mouseMove(canvas.viewport(), point + QPoint(30, 35), delay=20)
    qtbot.mouseRelease(canvas.viewport(), Qt.MouseButton.LeftButton, pos=point + QPoint(30, 35))
    assert window.document.graph.vertices[1].x % 40 == 0
    assert window.document.graph.vertices[2] == graph.vertices[2]
    assert window.document.graph.vertices[3] == graph.vertices[3]
    assert window.document.undo_stack.count() == 1


def test_undo_redo_during_physics_restores_once_and_keeps_redo_available(window, graph, qtbot):
    populate(window, graph)
    physics, document = window.physics, window.document
    physics.set_enabled(True)
    for _ in range(6):
        physics.tick()
    moved = document.graph.clone()
    assert moved != graph
    assert window.commands["undo"].isEnabled()  # antes de gravar o primeiro movimento no histórico
    window.commands["undo"].trigger()
    assert document.graph == graph
    assert physics.enabled and physics.paused
    assert not physics.timer.isActive()
    assert not physics.velocities and physics.before is None
    assert document.undo_stack.canRedo()
    count, index = document.undo_stack.count(), document.undo_stack.index()
    qtbot.wait(130)
    assert document.graph == graph
    assert (document.undo_stack.count(), document.undo_stack.index()) == (count, index)
    window.commands["redo"].trigger()
    assert document.graph == moved
    qtbot.wait(100)
    assert document.graph == moved
    assert physics.paused and not physics.timer.isActive()
    window.commands["physics_pause"].trigger()
    assert physics.timer.isActive() and not physics.paused
    assert physics.before == moved


def test_repeated_history_navigation_preserves_topology_and_stays_paused(window, graph, qtbot):
    populate(window, graph)
    document, physics = window.document, window.physics
    document.edit("Vértice", lambda g: g.add_vertex(100, 200))
    document.edit("Aresta", lambda g: g.add_edge(1, 4))
    before_physics = document.graph.clone()
    physics.set_enabled(True)
    physics.tick()
    after_physics = document.graph.clone()
    document.undo()
    assert document.graph == before_physics
    document.undo()
    assert len(document.graph.edges) == 2
    document.undo()
    assert document.graph == graph
    for _ in range(3):
        document.redo()
        assert physics.paused and not physics.timer.isActive()
    assert document.graph == after_physics
    qtbot.wait(100)
    assert document.graph == after_physics


def test_attribute_patch_does_not_own_unrelated_coordinates(qapp, graph):
    document = Document()
    document.reset(graph)
    document.edit("Rótulo", lambda g: setattr(g.vertices[1], "label", "Origem"))
    # As posições podem mudar depois de um comando que só editou um atributo.
    document.graph.vertices[1].x = 123.456
    document.undo()
    assert document.graph.vertices[1].label == ""
    assert document.graph.vertices[1].x == 123.456
    document.redo()
    assert document.graph.vertices[1].label == "Origem"
    assert document.graph.vertices[1].x == 123.456


def test_live_tuning_preserves_momentum_timer_and_history(window, graph):
    populate(window, graph)
    physics = window.physics
    physics.set_enabled(True)
    physics.tick()
    before = physics.before
    velocities = physics.velocities.copy()
    iterations, timer = physics.iterations, physics.timer.timerId()
    window.physics_panel.controls["damping"].spin.setValue(0.45)
    assert physics.parameters.damping == 0.45
    assert physics.before is before
    assert physics.velocities == velocities
    assert physics.iterations == iterations and physics.timer.timerId() == timer
    assert window.document.undo_stack.count() == 0
    assert window.settings.value("physics/damping", type=float) == 0.45


def test_attribute_edits_do_not_interrupt_motion_or_leak_into_physics_history(window, graph):
    populate(window, graph)
    physics, document = window.physics, window.document
    physics.set_enabled(True)
    physics.tick()
    timer, before = physics.timer.timerId(), physics.before
    velocities = physics.velocities.copy()
    document.edit("Rótulo", lambda g: setattr(g.vertices[1], "label", "Origem"))
    assert physics.timer.isActive() and physics.timer.timerId() == timer
    assert physics.before is before and physics.velocities == velocities
    assert document.undo_stack.count() == 1
    physics.tick()
    physics.pause(suspend=True)
    assert document.undo_stack.count() == 2
    document.undo()
    assert document.graph.vertices[1].label == "Origem"
    assert document.graph.vertices[1].x == graph.vertices[1].x
    document.undo()
    assert document.graph == graph
    document.redo()
    assert document.graph.vertices[1].label == "Origem"


def test_explicit_pause_survives_edits_preferences_and_resume(window, graph, qtbot):
    populate(window, graph)
    window.show_physics()
    panel, physics = window.physics_panel, window.physics
    qtbot.mouseClick(panel.enable, Qt.MouseButton.LeftButton)
    physics.tick()
    qtbot.mouseClick(panel.pause, Qt.MouseButton.LeftButton)
    frozen = window.document.graph.clone()
    assert physics.paused and panel.pause.text() == "Retomar"
    panel.controls["speed"].spin.setValue(1.5)
    window.document.edit("Rótulo", lambda g: setattr(g.vertices[1], "label", "A"))
    qtbot.wait(100)
    assert physics.paused and not physics.timer.isActive()
    assert window.document.graph.vertices[1].x == frozen.vertices[1].x
    qtbot.mouseClick(panel.pause, Qt.MouseButton.LeftButton)
    assert physics.timer.isActive() and not physics.paused


def test_label_change_does_not_wake_resting_simulation(window):
    graph = Graph()
    graph.add_vertex(80, 20)
    populate(window, graph)
    physics = window.physics
    physics.set_enabled(True)
    for _ in range(12):
        physics.tick()
    assert not physics.timer.isActive() and physics.enabled
    window.document.edit("Rótulo", lambda g: setattr(g.vertices[1], "label", "A"))
    assert not physics.timer.isActive()
    window.document.edit("Mover", lambda g: g.add_vertex(100, 20))
    assert physics.timer.isActive()


def test_physics_and_connection_preferences_survive_window_recreation(window, graph, qtbot):
    populate(window, graph)
    window.physics_panel.choose_preset("Suave")
    window.inspector.chain_edges.setChecked(True)
    window.inspector.allow_loops.setChecked(False)
    window.inspector.create_directed.setChecked(True)
    window.inspector.create_weighted.setChecked(True)
    window.inspector.create_weight.setValue(7)
    window.settings.sync()
    reopened = MainWindow(window.data_dir / "reopened", window.settings)
    qtbot.addWidget(reopened)
    assert reopened.physics.parameters == window.physics.parameters
    assert reopened.canvas.chain_edges and not reopened.canvas.allow_loops
    assert reopened.inspector.create_directed.isChecked()
    assert reopened.inspector.create_weighted.isChecked()
    assert reopened.inspector.create_weight.value() == 7
    reopened.close()


@pytest.mark.parametrize("name", ["select", "hand", "vertex", "edge", "delete"])
def test_selected_tool_icons_have_substantial_solid_fill(qapp, name):
    outline = icon(name, "#ffffff").pixmap(64, 64, QIcon.Mode.Normal, QIcon.State.Off).toImage()
    filled = icon(name, "#ffffff", True).pixmap(64, 64, QIcon.Mode.Normal, QIcon.State.On).toImage()

    def area(image):
        return sum(image.pixelColor(x, y).alpha() > 128 for x in range(64) for y in range(64))

    assert area(filled) > area(outline) * 1.15


def test_invalid_persisted_physics_values_fall_back_individually():
    parameters = PhysicsParameters.from_mapping({"damping": "nan", "speed": "bad", "gravity": 0.5})
    assert parameters.damping == PhysicsParameters().damping
    assert parameters.speed == 1
    assert parameters.gravity == 0.5
    assert PhysicsParameters.from_mapping(asdict(parameters)) == parameters


def test_reset_clears_selection_and_history_cancels_pending_connection(window, graph, qtbot):
    populate(window, graph)
    window.canvas.vertices[1].setSelected(True)
    window.document.reset(graph)
    assert window.canvas.selection() == (set(), set())
    window.document.edit("Rótulo", lambda g: setattr(g.vertices[1], "label", "A"))
    window.canvas.set_mode("edge")
    click_vertex(qtbot, window.canvas, 1)
    window.document.undo()
    assert window.canvas.edge_start is None
    assert window.canvas._preview.path().isEmpty()


def test_physics_preview_reuses_labels_and_item_geometry(window, graph, monkeypatch):
    from grafla.items import EdgeItem, VertexItem

    populate(window, graph)
    calls = []
    monkeypatch.setattr(VertexItem, "refresh", lambda *args: calls.append("vertex"))
    monkeypatch.setattr(EdgeItem, "refresh", lambda *args: calls.append("edge"))
    window.physics.set_enabled(True)
    window.physics.tick()
    assert not calls
    for key, item in window.canvas.vertices.items():
        vertex = window.document.graph.vertices[key]
        assert item.pos() == QPointF(vertex.x, vertex.y)
    window.physics.pause(suspend=True)
    assert not calls  # gravar o movimento não deve reaplicá-lo
    # Remove os interceptadores antes de o histórico precisar atualizar os itens.
    monkeypatch.undo()


@pytest.mark.parametrize("theme", ["dark", "light"])
def test_physics_numeric_values_remain_visible_after_theming(window, qtbot, theme):
    window.settings.setValue("theme", theme)
    window.apply_preferences()
    window.show_physics()
    window.physics_panel.advanced.setChecked(True)
    qtbot.wait(20)
    for control in window.physics_panel.controls.values():
        editor = control.spin.lineEdit()
        assert editor.width() >= editor.fontMetrics().horizontalAdvance(editor.text()) + 8
