import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("XDG_CACHE_HOME", "/tmp/grafla-test-cache")

import pytest
from PyQt6.QtCore import QSettings

from grafla.domain import Graph
from grafla.main_window import MainWindow


@pytest.fixture
def graph():
    graph = Graph()
    for x in (0, 180, 360):
        graph.add_vertex(x, 0)
    graph.add_edge(1, 2, directed=True, weighted=True, weight=1)
    graph.add_edge(2, 3, directed=True, weighted=True, weight=2)
    return graph


@pytest.fixture
def window(qtbot, tmp_path):
    settings = QSettings(str(tmp_path / "test.ini"), QSettings.Format.IniFormat)
    window = MainWindow(tmp_path, settings)

    def cleanup(widget):
        widget.runner.cancel_analysis()
        widget.physics.set_enabled(False)
        widget.document.undo_stack.setClean()

    qtbot.addWidget(window, before_close_func=cleanup)
    window.show()
    qtbot.waitExposed(window)
    yield window
    cleanup(window)
    window.close()
