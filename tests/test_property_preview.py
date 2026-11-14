from PyQt6.QtCore import QPoint, QPointF, Qt, QTimer
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QApplication

from grafla.color_picker import ColorPicker
from grafla.persistence import load


def select_vertex(window, graph):
    window.document.reset(graph)
    window.canvas.vertices[1].setSelected(True)
    return window.inspector


def test_properties_preview_cancel_and_one_undoable_commit(window, graph, qtbot):
    panel = select_vertex(window, graph)
    panel.vertex_label.setText("Minha origem")
    panel.vertex_color.setText("#43b8ac")
    panel.vertex_radius.setValue(41)
    panel.vertex_x.setValue(72)
    panel.vertex_y.setValue(-30)
    panel.vertex_pinned.setChecked(True)
    drawn = window.canvas.vertices[1]
    assert drawn.vertex.label == "Minha origem"
    assert drawn.vertex.color == "#43b8ac"
    assert drawn.vertex.radius == 41 and drawn.vertex.pinned
    assert drawn.pos().x() == 72 and drawn.pos().y() == -30
    assert window.document.graph == graph
    assert not window.document.dirty
    assert window.document.undo_stack.count() == 0
    qtbot.mouseClick(panel.cancel_button, Qt.MouseButton.LeftButton)
    assert drawn.vertex == graph.vertices[1]
    assert panel.vertex_label.text() == graph.vertices[1].label
    panel.vertex_label.setText("Confirmado")
    panel.vertex_color.setText("#43b8ac")
    panel.submit()
    assert window.document.graph.vertices[1].label == "Confirmado"
    assert window.document.undo_stack.count() == 1
    panel.submit()
    assert window.document.undo_stack.count() == 1
    window.document.undo()
    assert window.document.graph == graph
    window.document.redo()
    assert window.document.graph.vertices[1].color == "#43b8ac"


def test_edge_preview_changes_geometry_but_cancels_without_history(window, graph):
    window.document.reset(graph)
    window.canvas.edges[1].setSelected(True)
    panel = window.inspector
    panel.edge_label.setText("Viagem")
    panel.edge_weight.setValue(2.5)
    panel.edge_directed.setChecked(False)
    panel.edge_weighted.setChecked(False)
    panel.edge_color.setText("#a155de")
    item = window.canvas.edges[1]
    assert item.edge.label == "Viagem"
    assert item.arrow_path.isEmpty()
    assert item.label == "Viagem"
    assert window.document.graph == graph
    panel.cancel_requested.emit()
    assert item.edge == graph.edges[1]
    assert not item.arrow_path.isEmpty()
    assert window.document.undo_stack.count() == 0


def test_group_preview_and_cancel_restore_each_individual_color(window, graph):
    graph.vertices[1].color = "#aabbcc"
    graph.vertices[2].color = "#ddeeff"
    panel = select_vertex(window, graph)
    window.canvas.vertices[2].setSelected(True)
    panel.multi_color.setText("#123456")
    assert all(window.canvas.vertices[key].vertex.color == "#123456" for key in (1, 2))
    assert window.document.graph == graph
    panel.cancel_requested.emit()
    assert panel.multi_color.text() == ""
    assert all(window.canvas.vertices[key].vertex == graph.vertices[key] for key in (1, 2))
    panel.multi_color.setText("#654321")
    panel.submit()
    assert window.document.undo_stack.count() == 1
    window.document.undo()
    assert window.document.graph == graph


def test_selection_change_discards_unconfirmed_properties(window, graph):
    panel = select_vertex(window, graph)
    panel.vertex_label.setText("Só uma prévia")
    window.canvas.graph_scene.clearSelection()
    window.canvas.vertices[2].setSelected(True)
    assert window.document.graph == graph
    assert window.canvas.vertices[1].vertex.label == graph.vertices[1].label
    assert panel.vertex_label.text() == graph.vertices[2].label


def test_invalid_draft_does_not_modify_document_or_previous_valid_preview(window, graph):
    panel = select_vertex(window, graph)
    panel.vertex_color.setText("#123456")
    panel.vertex_color.setText("inválida")
    panel.submit()
    assert window.document.graph == graph
    assert window.canvas.vertices[1].vertex.color == "#123456"
    assert "Cor inválida" in panel.feedback.text()
    panel.cancel_requested.emit()
    assert window.canvas.vertices[1].vertex.color == graph.vertices[1].color


def test_autosave_and_save_never_record_unconfirmed_properties(window, graph, tmp_path):
    panel = select_vertex(window, graph)
    window.document.edit(
        "Confirmado", lambda current: setattr(current.vertices[2], "label", "Salvo")
    )
    panel.vertex_label.setText("Não confirmado")
    window.files.autosave()
    recovered = load(window.files.recovery)
    assert recovered.vertices[1].label == graph.vertices[1].label
    assert recovered.vertices[2].label == "Salvo"
    window.document.write(tmp_path / "confirmado.grafla")
    assert load(tmp_path / "confirmado.grafla") == recovered
    assert window.canvas.vertices[1].vertex.label == graph.vertices[1].label


def test_physics_and_preview_keep_current_positions_and_separate_history(window, graph):
    panel = select_vertex(window, graph)
    window.physics.set_enabled(True)
    window.physics.tick()
    panel.vertex_label.setText("Em movimento")
    for _ in range(4):
        window.physics.tick()
    current = {key: (vertex.x, vertex.y) for key, vertex in window.document.graph.vertices.items()}
    assert window.canvas.vertices[1].vertex.label == "Em movimento"
    assert window.document.graph.vertices[1].label == ""
    assert abs(panel.vertex_x.value() - current[1][0]) < 0.01
    assert abs(panel.vertex_y.value() - current[1][1]) < 0.01
    panel.submit()
    assert window.document.graph.vertices[1].label == "Em movimento"
    assert {
        key: (vertex.x, vertex.y) for key, vertex in window.document.graph.vertices.items()
    } == current
    window.physics.pause(suspend=True)
    window.document.undo()
    assert window.document.graph.vertices[1].label == "Em movimento"
    window.document.undo()
    assert window.document.graph.vertices[1].label == ""


def test_wheel_previews_color_and_cancel_restores_only_the_color(window, graph, qtbot):
    panel = select_vertex(window, graph)
    panel.vertex_label.setText("Rótulo em edição")
    original = panel.vertex_color.text()
    seen = []

    def choose_and_cancel():
        dialog = QApplication.activeModalWidget()
        try:
            assert isinstance(dialog, ColorPicker)
            qtbot.mouseClick(dialog.wheel, Qt.MouseButton.LeftButton, pos=QPoint(220, 124))
            seen.append(panel.vertex_color.text())
            assert seen[-1] != original
            assert window.canvas.vertices[1].vertex.color == seen[-1]
            assert window.document.graph == graph
        finally:
            dialog.reject()

    QTimer.singleShot(0, choose_and_cancel)
    panel.vertex_color.choose_action.trigger()
    assert seen
    assert panel.vertex_color.text() == original
    assert window.canvas.vertices[1].vertex.label == "Rótulo em edição"
    assert window.canvas.vertices[1].vertex.color == original


def test_wheel_acceptance_still_waits_for_apply_properties(window, graph, qtbot):
    panel = select_vertex(window, graph)

    def choose_and_accept():
        dialog = QApplication.activeModalWidget()
        try:
            qtbot.mouseClick(dialog.wheel, Qt.MouseButton.LeftButton, pos=QPoint(124, 30))
            dialog.brightness.setValue(220)
            dialog.accept()
        except BaseException:
            dialog.reject()
            raise

    QTimer.singleShot(0, choose_and_accept)
    panel.vertex_color.choose_action.trigger()
    color = panel.vertex_color.text()
    assert color != graph.vertices[1].color
    assert window.document.graph == graph
    panel.submit()
    assert window.document.graph.vertices[1].color == color
    window.document.undo()
    assert window.document.graph == graph


def test_coordinates_share_a_row_and_do_not_expand_the_dock(window, graph, qtbot):
    panel = select_vertex(window, graph)
    window.resize(1024, 768)
    qtbot.wait(20)
    x, y = panel.vertex_x, panel.vertex_y
    assert x.mapTo(window, QPoint()).y() == y.mapTo(window, QPoint()).y()
    assert abs(x.width() - y.width()) <= 2
    assert window.workspace.width() < 450
    assert panel.horizontalScrollBar().maximum() == 0


def test_selected_vertex_displays_the_chosen_color_in_the_actual_render(window, graph, qtbot):
    panel = select_vertex(window, graph)
    panel.vertex_color.setText("#43b8ac")
    qtbot.wait(20)
    canvas = window.canvas
    item = canvas.vertices[1]
    point = canvas.mapFromScene(item.pos() + QPointF(item.vertex.radius, 0))
    image = canvas.viewport().grab().toImage()
    ratio = canvas.devicePixelRatioF()
    x, y = round(point.x() * ratio), round(point.y() * ratio)
    pixels = [image.pixelColor(x + dx, y + dy) for dx in range(-2, 3) for dy in range(-2, 3)]
    assert QColor("#43b8ac") in pixels


def test_brand_focus_and_about_do_not_leave_a_pressed_outline(window, qtbot):
    button = window.brand_button
    qtbot.mouseMove(window.canvas.viewport(), QPoint(10, 10))
    button.clearFocus()
    qtbot.wait(20)
    normal = button.grab().toImage()
    button.setFocus()
    qtbot.wait(20)
    assert button.grab().toImage() == normal
    QTimer.singleShot(0, lambda: QApplication.activeModalWidget().reject())
    qtbot.mouseClick(button, Qt.MouseButton.LeftButton)
    qtbot.mouseMove(window.canvas.viewport(), QPoint(12, 12))
    qtbot.wait(20)
    assert button.grab().toImage() == normal
    qtbot.mouseMove(button, button.rect().center())
    qtbot.wait(20)
    assert button.grab().toImage() != normal
