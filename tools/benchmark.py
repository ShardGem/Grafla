"""Mede o canvas em grafos esparsos; os tempos não representam FPS."""

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
from grafla.physics_controller import PhysicsController


def sparse_graph(n):
    graph = Graph()
    for index in range(n):
        graph.add_vertex(100 + index % 50 * 80, 100 + index // 50 * 80)
    for key in range(1, n):
        graph.edges[key] = Edge(key, key, key + 1, directed=True)
    graph.next_edge = n
    graph.validate()
    return graph


def measure(n):
    graph = sparse_graph(n)
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


def measure_physics(n):
    """Mede o passo e a atualização do canvas separadamente da renderização."""
    doc = Document()
    physics = PhysicsController(doc)
    canvas = Canvas(doc)
    canvas.resize(960, 680)
    doc.reset(sparse_graph(n))
    canvas.show()
    canvas.fit_graph()
    QApplication.processEvents()
    physics.set_enabled(True)
    ticks, render = [], []
    for _ in range(12):
        start = time.perf_counter()
        physics.tick()
        ticks.append((time.perf_counter() - start) * 1000)
        image = QImage(960, 680, QImage.Format.Format_ARGB32_Premultiplied)
        painter = QPainter(image)
        start = time.perf_counter()
        canvas.render(painter)
        render.append((time.perf_counter() - start) * 1000)
        painter.end()
    start = time.perf_counter()
    physics.set_enabled(False)
    flush_ms = (time.perf_counter() - start) * 1000
    canvas.close()
    return {
        "vertices": n,
        "edges": n - 1,
        "physics_tick_median_ms": statistics.median(ticks),
        "viewport_render_median_ms": statistics.median(render),
        "history_flush_ms": flush_ms,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("sizes", nargs="*", type=int)
    parser.add_argument(
        "--physics", action="store_true", help="Medir física, canvas e consolidação"
    )
    args = parser.parse_args()
    app = QApplication([])
    app.setQuitOnLastWindowClosed(False)
    sizes = args.sizes or ([100, 500, 1000] if args.physics else [100, 500, 1000, 5000])
    for size in sizes:
        if not 2 <= size <= 10_000:
            parser.error("sizes must be between 2 and 10000")
        if args.physics and size > 1000:
            parser.error("physics sizes must be between 2 and 1000")
        sys.stdout.write(
            json.dumps(measure_physics(size) if args.physics else measure(size)) + "\n"
        )
        sys.stdout.flush()


if __name__ == "__main__":
    main()
