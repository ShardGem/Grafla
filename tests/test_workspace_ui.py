import pytest
from PyQt6.QtCore import QElapsedTimer, Qt, QTimer
from PyQt6.QtTest import QSignalSpy

from grafla.splash import Splash
from grafla.workspace import ZoomBar


def populate(window, graph):
    window.document.reset(graph)
    window.canvas.fit_graph()


def test_horizontal_tool_modes_change_icons_and_remain_keyboard_accessible(window, qtbot):
    assert window.tools.orientation() == Qt.Orientation.Horizontal
    action = window.commands["tool_vertex"]
    inactive = action.icon().cacheKey()
    window.canvas.setFocus()
    qtbot.keyClick(window.canvas, Qt.Key.Key_N)
    assert action.isChecked()
    assert action.icon().cacheKey() != inactive
    assert not window.commands["tool_select"].isChecked()


def test_physics_control_fits_in_horizontal_strip_on_laptop_width(window, qtbot):
    window.resize(1280, 768)
    qtbot.wait(20)
    assert window.tools.widgetForAction(window.commands["physics"]).isVisible()


def test_zoom_slider_tracks_wheel_fit_and_buttons_without_feedback_loop(window, graph):
    populate(window, graph)
    controls = window.zoom_controls
    spy = QSignalSpy(controls.zoom_requested)
    controls.slider.setValue(600)
    assert window.canvas.transform().m11() == pytest.approx(ZoomBar.scale_at(600))
    assert len(spy) == 1
    window.canvas.zoom(1.2)
    assert len(spy) == 1
    assert ZoomBar.scale_at(controls.slider.value()) == pytest.approx(
        window.canvas.transform().m11(), rel=0.006
    )
    window.canvas.reset_view()
    assert controls.percent.text() == "100%"
    window.canvas.fit_graph()
    assert controls.percent.text() == f"{window.canvas.transform().m11() * 100:.0f}%"


def test_route_selection_links_cost_sequence_canvas_and_optional_report(window, graph, qtbot):
    graph.add_edge(1, 3, True, True, 8)
    populate(window, graph)
    window.tabs.setCurrentIndex(1)
    panel = window.analysis
    panel.algorithm.setCurrentIndex(panel.algorithm.findData("all"))
    panel.destination.setCurrentIndex(2)
    window.runner.run_analysis()
    qtbot.waitUntil(lambda: window.runner.result is not None, timeout=3000)
    browser = panel.browser
    assert browser.routes.count() == 2
    assert window.results_dock.isHidden()
    index = window.runner.result.paths.index([1, 3])
    item = browser.routes.item(index)
    qtbot.mouseClick(
        browser.routes.viewport(),
        Qt.MouseButton.LeftButton,
        pos=browser.routes.visualItemRect(item).center(),
    )
    assert window.canvas.highlight_vertices == {1, 3}
    assert window.canvas.highlight_edges == {3}
    assert "Custo 8" in browser.metric.text()
    assert browser.sequence.text() == "1 → 3"
    browser.report_requested.emit()
    assert not window.results_dock.isHidden()
    assert window.document.graph == graph


def test_lazy_step_table_and_scrubber_jump_to_exact_execution_state(window, graph, qtbot):
    populate(window, graph)
    window.tabs.setCurrentIndex(1)
    panel = window.analysis
    panel.algorithm.setCurrentIndex(panel.algorithm.findData("bfs"))
    window.runner.run_analysis()
    qtbot.waitUntil(lambda: window.runner.result is not None, timeout=3000)
    browser = panel.browser
    assert browser.steps.model().rowCount() == 3
    window.runner.toggle_playback()
    row = browser.steps.model().index(2, 0)
    qtbot.mouseClick(
        browser.steps.viewport(),
        Qt.MouseButton.LeftButton,
        pos=browser.steps.visualRect(row).center(),
    )
    assert window.runner.result_index == 2
    assert not window.runner.playback.isActive()
    assert window.canvas.current_vertex == 3
    assert window.canvas.highlight_edges == {1, 2}
    browser.scrub.setValue(1)
    assert window.canvas.current_vertex == 2
    assert window.canvas.highlight_vertices == {1, 2}
    assert browser.steps.selectionModel().currentIndex().row() == 1
    assert window.document.graph == graph


def test_changing_algorithm_or_endpoints_invalidates_query_results(window, graph, qtbot):
    populate(window, graph)
    window.runner.run_analysis()
    qtbot.waitUntil(lambda: window.runner.result is not None, timeout=3000)
    window.analysis.algorithm.setCurrentIndex(window.analysis.algorithm.findData("bfs"))
    assert window.runner.result is None
    assert not window.canvas.highlight_vertices
    window.runner.run_analysis()
    qtbot.waitUntil(lambda: window.runner.result is not None, timeout=3000)
    window.analysis.origin.setCurrentIndex(1)
    assert window.runner.result is None
    assert "Parâmetros" in window.analysis.status.text()


def test_generator_and_matrix_are_integrated_transactional_and_preserve_pending_cells(
    window, graph, qtbot
):
    populate(window, graph)
    window.generate()
    panel = window.building.generator
    panel.vertices.setValue(4)
    panel.edges.setValue(6)
    assert window.document.graph == graph
    qtbot.mouseClick(panel.apply, Qt.MouseButton.LeftButton)
    assert len(window.document.graph.vertices) == 4
    assert len(window.document.graph.edges) == 6
    window.document.undo()
    assert window.document.graph == graph
    window.matrix(True)
    matrix = window.building.matrix
    matrix.count.setValue(2)
    matrix.model.setData(matrix.model.index(0, 1), "1")
    matrix.weighted.setChecked(True)
    assert matrix.model.values == [[None, 1], [1, None]]
    matrix.directed.setChecked(True)
    matrix.model.setData(matrix.model.index(1, 0), "2")
    matrix.directed.setChecked(False)
    assert matrix.directed.isChecked()  # conflicting weights are kept, not discarded
    assert matrix.model.values[1][0] == 2
    assert "diferentes" in matrix.feedback.text()
    matrix.model.setData(matrix.model.index(1, 0), "1")
    matrix.directed.setChecked(False)
    qtbot.mouseClick(matrix.apply, Qt.MouseButton.LeftButton)
    assert len(window.document.graph.edges) == 1
    window.document.undo()
    assert window.document.graph == graph


def test_splash_minimum_is_nonblocking_and_not_added_to_work_duration(qapp, qtbot):
    splash = Splash(animate=False, minimum_ms=100)
    qtbot.addWidget(splash)
    splash.show()
    elapsed = QElapsedTimer()
    elapsed.start()
    events = []
    QTimer.singleShot(10, lambda: events.append(("event", elapsed.elapsed())))
    splash.finish_when_ready(lambda: events.append(("ready", elapsed.elapsed())))
    assert events == []
    qtbot.waitUntil(lambda: any(name == "ready" for name, _ in events), timeout=1000)
    assert [name for name, _ in events] == ["event", "ready"]
    assert events[-1][1] >= 100
    splash.close()
    slow = Splash(animate=False, minimum_ms=30)
    qtbot.addWidget(slow)
    slow.show()
    qtbot.wait(45)
    finished = []
    slow.finish_when_ready(lambda: finished.append(True))
    assert finished == [True]
    slow.close()


def test_zoom_grid_preferences_are_persisted_in_context(window):
    window.zoom_controls.grid.setChecked(False)
    window.zoom_controls.snap.setChecked(True)
    assert not window.canvas.show_grid
    assert window.canvas.snap
    assert not window.settings.value("grid", type=bool)
    assert window.settings.value("snap", type=bool)
