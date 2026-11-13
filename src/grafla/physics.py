"""Simulação de forças sem dependência de Qt ou do histórico."""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, fields
from typing import ClassVar

from grafla.domain import Graph


@dataclass(frozen=True)
class PhysicsParameters:
    repulsion: float = 4200.0
    repulsion_distance: float = 240.0
    attraction: float = 1.0
    stiffness: float = 0.025
    ideal_distance: float = 150.0
    damping: float = 0.22
    centering: float = 0.002
    gravity: float = 0.0
    gravity_angle: float = 90.0
    speed: float = 1.0
    max_speed: float = 7.0
    stability: float = 0.07

    LIMITS: ClassVar[dict[str, tuple[float, float]]] = {
        "repulsion": (0, 20000),
        "repulsion_distance": (40, 600),
        "attraction": (0, 3),
        "stiffness": (0.001, 0.12),
        "ideal_distance": (40, 400),
        "damping": (0.05, 0.95),
        "centering": (0, 0.02),
        "gravity": (0, 2),
        "gravity_angle": (0, 360),
        "speed": (0.25, 2),
        "max_speed": (1, 14),
        "stability": (0.01, 0.5),
    }

    def __post_init__(self) -> None:
        for name, (low, high) in self.LIMITS.items():
            value = getattr(self, name)
            if not math.isfinite(value) or not low <= value <= high:
                raise ValueError(f"Parâmetro físico inválido: {name}")

    @classmethod
    def from_mapping(cls, values: dict[str, object]) -> PhysicsParameters:
        """Aproveita os valores válidos e usa o padrão para os demais."""
        valid = {}
        for field in fields(cls):
            try:
                value = float(str(values[field.name]))
                low, high = cls.LIMITS[field.name]
                if math.isfinite(value) and low <= value <= high:
                    valid[field.name] = value
            except (KeyError, ValueError, TypeError):
                continue
        return cls(**valid)


def _forces(
    graph: Graph,
    positions: dict[int, tuple[float, float]],
    parameters: PhysicsParameters,
    center: tuple[float, float],
) -> dict[int, list[float]]:
    radius = parameters.repulsion_distance
    cells: dict[tuple[int, int], list[int]] = defaultdict(list)
    for key, (x, y) in positions.items():
        cells[(math.floor(x / radius), math.floor(y / radius))].append(key)
    angle = math.radians(parameters.gravity_angle)
    gx, gy = parameters.gravity * math.cos(angle), parameters.gravity * math.sin(angle)
    forces = {
        key: [
            (center[0] - x) * parameters.centering + gx,
            (center[1] - y) * parameters.centering + gy,
        ]
        for key, (x, y) in positions.items()
    }
    radius_squared = radius * radius
    fade_start, fade_scale = radius * 0.8, 5 / radius
    repulsion = parameters.repulsion
    pinned = {v.id for v in graph.vertices.values() if v.pinned}
    if repulsion:
        for vertex in graph.vertices.values():
            x, y = positions[vertex.id]
            cx, cy = math.floor(x / radius), math.floor(y / radius)
            own_force = forces[vertex.id]
            inspected = 0
            for bx in range(cx - 1, cx + 2):
                for by in range(cy - 1, cy + 2):
                    for key in cells.get((bx, by), ()):
                        # Calcula cada par uma vez e aplica forças opostas aos dois vértices.
                        if key <= vertex.id or (vertex.pinned and key in pinned):
                            continue
                        inspected += 1
                        if inspected > 160:
                            break
                        ox, oy = positions[key]
                        dx, dy = x - ox, y - oy
                        squared = dx * dx + dy * dy
                        if squared >= radius_squared:
                            continue
                        if squared < 0.0001:
                            angle = math.radians((vertex.id * 137 + key * 53) % 360)
                            dx, dy = -math.cos(angle), -math.sin(angle)
                            squared = 1.0
                        distance = math.sqrt(squared)
                        strength = min(12.0, repulsion / max(1.0, squared)) / distance
                        if distance > fade_start:
                            strength *= (radius - distance) * fade_scale
                        fx, fy = strength * dx, strength * dy
                        own_force[0] += fx
                        own_force[1] += fy
                        other_force = forces[key]
                        other_force[0] -= fx
                        other_force[1] -= fy
                    if inspected > 160:
                        break
                if inspected > 160:
                    break
    for edge in graph.edges.values():
        if edge.source == edge.target:
            continue
        ax, ay = positions[edge.source]
        target_x, target_y = positions[edge.target]
        dx, dy = target_x - ax, target_y - ay
        distance = max(1.0, math.hypot(dx, dy))
        force = max(
            -12.0,
            min(
                12.0,
                (distance - parameters.ideal_distance)
                * parameters.stiffness
                * parameters.attraction,
            ),
        )
        for key, sign in ((edge.source, 1), (edge.target, -1)):
            forces[key][0] += sign * force * dx / distance
            forces[key][1] += sign * force * dy / distance
    return forces


def step(
    graph: Graph,
    velocities: dict[int, tuple[float, float]],
    parameters: PhysicsParameters | None = None,
    center: tuple[float, float] = (0.0, 0.0),
) -> tuple[dict[int, tuple[float, float]], float]:
    parameters = parameters if parameters is not None else PhysicsParameters()
    positions = {key: (v.x, v.y) for key, v in graph.vertices.items()}
    for key in velocities.keys() - graph.vertices.keys():
        del velocities[key]
    # Aumenta o ritmo com subpassos, mantendo o tamanho de cada passo limitado.
    substeps = math.ceil(parameters.speed)
    dt = parameters.speed / substeps
    decay = (1 - parameters.damping) ** dt
    for _ in range(substeps):
        forces = _forces(graph, positions, parameters, center)
        for vertex in graph.vertices.values():
            if vertex.pinned:
                velocities[vertex.id] = (0.0, 0.0)
                continue
            vx, vy = velocities.get(vertex.id, (0.0, 0.0))
            fx, fy = forces[vertex.id]
            vx, vy = (vx + fx * dt) * decay, (vy + fy * dt) * decay
            speed = math.hypot(vx, vy)
            if speed > parameters.max_speed:
                vx, vy = vx * parameters.max_speed / speed, vy * parameters.max_speed / speed
            velocities[vertex.id] = (vx, vy)
            x, y = positions[vertex.id]
            positions[vertex.id] = (
                max(-1e7, min(1e7, x + vx * dt)),
                max(-1e7, min(1e7, y + vy * dt)),
            )
    moved = {
        key: position
        for key, position in positions.items()
        if not graph.vertices[key].pinned
        and math.hypot(position[0] - graph.vertices[key].x, position[1] - graph.vertices[key].y)
        > 0.001
    }
    max_speed = max((math.hypot(vx, vy) for vx, vy in velocities.values()), default=0.0)
    return moved, max_speed
