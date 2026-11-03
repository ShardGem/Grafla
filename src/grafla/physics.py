"""Bounded force layout on plain graph data, with spatially local repulsion."""

from __future__ import annotations

import math
from collections import defaultdict

from grafla.domain import Graph


def step(
    graph: Graph,
    velocities: dict[int, tuple[float, float]],
) -> tuple[dict[int, tuple[float, float]], float]:
    cells: dict[tuple[int, int], list[int]] = defaultdict(list)
    for vertex in graph.vertices.values():
        cells[(math.floor(vertex.x / 170), math.floor(vertex.y / 170))].append(vertex.id)
    forces = {key: [0.0, 0.0] for key in graph.vertices}
    for vertex in graph.vertices.values():
        if vertex.pinned:
            continue
        cx, cy = math.floor(vertex.x / 170), math.floor(vertex.y / 170)
        inspected = 0
        for bx in range(cx - 1, cx + 2):
            for by in range(cy - 1, cy + 2):
                for key in cells.get((bx, by), []):
                    if key == vertex.id:
                        continue
                    inspected += 1
                    if inspected > 160:
                        break
                    other = graph.vertices[key]
                    dx, dy = vertex.x - other.x, vertex.y - other.y
                    if abs(dx) + abs(dy) < 0.01:
                        dx = 1.0 if vertex.id > key else -1.0
                        dy = dx * 0.3
                    distance = max(1.0, math.hypot(dx, dy))
                    if distance < 240:
                        force = min(12.0, 4200 / (distance * distance))
                        forces[vertex.id][0] += force * dx / distance
                        forces[vertex.id][1] += force * dy / distance
    for edge in graph.edges.values():
        if edge.source == edge.target:
            continue
        a, b = graph.vertices[edge.source], graph.vertices[edge.target]
        dx, dy = b.x - a.x, b.y - a.y
        distance = max(1.0, math.hypot(dx, dy))
        force = max(-8.0, min(8.0, (distance - 150) * 0.025))
        for key, sign in ((a.id, 1), (b.id, -1)):
            forces[key][0] += sign * force * dx / distance
            forces[key][1] += sign * force * dy / distance
    moved = {}
    max_speed = 0.0
    for vertex in graph.vertices.values():
        if vertex.pinned:
            velocities[vertex.id] = (0.0, 0.0)
            continue
        vx, vy = velocities.get(vertex.id, (0.0, 0.0))
        fx, fy = forces[vertex.id]
        vx, vy = (vx + fx) * 0.78, (vy + fy) * 0.78
        speed = math.hypot(vx, vy)
        if speed > 7:
            vx, vy = vx * 7 / speed, vy * 7 / speed
            speed = 7
        velocities[vertex.id] = (vx, vy)
        max_speed = max(max_speed, speed)
        if speed > 0.015:
            moved[vertex.id] = (
                max(-1e7, min(1e7, vertex.x + vx)),
                max(-1e7, min(1e7, vertex.y + vy)),
            )
    return moved, max_speed
