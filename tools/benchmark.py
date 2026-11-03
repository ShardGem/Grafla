"""Run a reproducible sparse-graph canvas baseline; timings are not FPS."""

import argparse
import json
import statistics
import sys
import time

from PyQt6.QtCore import QEventLoop, QTimer
from PyQt6.QtGui import QImage, QPainter
from PyQt6.QtTest import QSignalSpy
from PyQt6.QtWidgets import QApplication

from grafla.canvas import Canvas
from grafla.document import Document
from grafla.domain import Edge, Graph


def measure(n):
    graph = Graph()
    for index in range(n):
        graph.add_vertex(100 + index % 50 * 80, 100 + index // 50 * 80)
    for key in range(1, n):
        graph.edges[key] = Edge(key, key, key + 1, directed=True)
    graph.next_edge = n
    graph.validate()
    doc = Document()
    canvas = Canvas(doc)
    canvas.resize(960, 680)
    start = time.perf_counter()
    doc.reset(graph)
    build_ms = (time.perf_counter() - start) * 1000
    canvas.show()
    QApplication.processEvents()
    spy = QSignalSpy(canvas.graph_scene.changed)
    loop = QEventLoop()
    QTimer.singleShot(100, loop.quit)
    loop.exec()
    idle_changes = len(spy)
    node = canvas.vertices[max(1, n // 2)]
    live, commit, render = [], [], []
    for _ in range(3):
        start = time.perf_counter()
        node.setPos(node.pos().x() + 1, node.pos().y())
        live.append((time.perf_counter() - start) * 1000)
        start = time.perf_counter()
        canvas.move_vertices({node.vertex.id: (node.pos().x(), node.pos().y())})
        commit.append((time.perf_counter() - start) * 1000)
        image = QImage(960, 680, QImage.Format.Format_ARGB32_Premultiplied)
        painter = QPainter(image)
        start = time.perf_counter()
        canvas.render(painter)
        render.append((time.perf_counter() - start) * 1000)
        painter.end()
    canvas.close()
    return {
        "vertices": n,
        "edges": n - 1,
        "scene_build_ms": build_ms,
        "idle_scene_changes_100ms": idle_changes,
        "live_move_median_ms": statistics.median(live),
        "commit_undo_median_ms": statistics.median(commit),
        "viewport_render_median_ms": statistics.median(render),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("sizes", nargs="*", type=int, default=[100, 500, 1000, 5000])
    args = parser.parse_args()
    app = QApplication([])
    app.setQuitOnLastWindowClosed(False)
    for size in args.sizes:
        if not 2 <= size <= 10_000:
            parser.error("sizes must be between 2 and 10000")
        sys.stdout.write(json.dumps(measure(size)) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
