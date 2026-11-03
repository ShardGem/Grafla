"""Graph data and transformations. This module deliberately has no Qt dependency."""

from __future__ import annotations

import copy
import math
import random
import re
from bisect import bisect_right
from dataclasses import dataclass, field

MAX_VERTICES = 10_000
MAX_EDGES = 50_000


class GraphError(ValueError):
    """An expected validation error suitable for a user-facing explanation."""


@dataclass
class Vertex:
    id: int
    x: float
    y: float
    label: str = ""
    color: str = "#899bb2"
    radius: float = 24
    pinned: bool = False


@dataclass
class Edge:
    id: int
    source: int
    target: int
    directed: bool = False
    weighted: bool = False
    weight: float = 1
    label: str = ""
    color: str = "#899bb2"

    @property
    def cost(self) -> float:
        return self.weight if self.weighted else 1.0


@dataclass
class Graph:
    vertices: dict[int, Vertex] = field(default_factory=dict)
    edges: dict[int, Edge] = field(default_factory=dict)
    next_vertex: int = 1
    next_edge: int = 1

    def clone(self) -> Graph:
        return copy.deepcopy(self)

    def add_vertex(self, x: float, y: float, label: str = "") -> Vertex:
        if len(self.vertices) >= MAX_VERTICES:
            raise GraphError(f"Limite de {MAX_VERTICES:,} vértices por documento.")
        vertex = Vertex(self.next_vertex, x, y, label)
        self.vertices[vertex.id] = vertex
        self.next_vertex += 1
        return vertex

    def add_edge(
        self,
        source: int,
        target: int,
        directed: bool = False,
        weighted: bool = False,
        weight: float = 1,
    ) -> Edge:
        if source not in self.vertices or target not in self.vertices:
            raise GraphError("Os dois extremos da aresta precisam existir.")
        if len(self.edges) >= MAX_EDGES:
            raise GraphError(f"Limite de {MAX_EDGES:,} arestas por documento.")
        for edge in self.edges.values():
            if (edge.source, edge.target) == (source, target) or (
                (not edge.directed or not directed)
                and (edge.source, edge.target) == (target, source)
            ):
                raise GraphError("Essa conexão já existe. Edite suas propriedades no inspector.")
        edge = Edge(self.next_edge, source, target, directed, weighted, weight)
        self.edges[edge.id] = edge
        self.next_edge += 1
        return edge

    def remove(self, vertices: set[int], edges: set[int]) -> None:
        for key in list(self.edges):
            edge = self.edges[key]
            if key in edges or edge.source in vertices or edge.target in vertices:
                del self.edges[key]
        for key in vertices:
            self.vertices.pop(key, None)

    def adjacency(self) -> dict[int, list[tuple[int, float, int]]]:
        result: dict[int, list[tuple[int, float, int]]] = {key: [] for key in self.vertices}
        for edge in self.edges.values():
            result[edge.source].append((edge.target, edge.cost, edge.id))
            if not edge.directed and edge.source != edge.target:
                result[edge.target].append((edge.source, edge.cost, edge.id))
        return result

    @property
    def kind(self) -> str:
        directions = {edge.directed for edge in self.edges.values()}
        if len(directions) > 1:
            return "Misto"
        return "Direcionado" if True in directions else "Não direcionado"

    def validate(self) -> None:
        if len(self.vertices) > MAX_VERTICES or len(self.edges) > MAX_EDGES:
            raise GraphError("O grafo excede o limite de elementos desta versão.")
        for key, vertex in self.vertices.items():
            if type(key) is not int or key < 1 or vertex.id != key:
                raise GraphError("ID de vértice inválido ou duplicado.")
            if not all(valid_number(x) for x in (vertex.x, vertex.y, vertex.radius)):
                raise GraphError("Coordenadas e tamanhos precisam ser números finitos.")
            if abs(vertex.x) > 1e7 or abs(vertex.y) > 1e7 or not 12 <= vertex.radius <= 100:
                raise GraphError("Posição ou tamanho fora dos limites do editor.")
            validate_text(vertex.label)
            validate_color(vertex.color)
            if type(vertex.pinned) is not bool:
                raise GraphError("Estado de fixação inválido.")
        seen: dict[tuple[int, int], bool] = {}
        for key, edge in self.edges.items():
            if type(key) is not int or key < 1 or edge.id != key:
                raise GraphError("ID de aresta inválido ou duplicado.")
            if edge.source not in self.vertices or edge.target not in self.vertices:
                raise GraphError("Aresta aponta para um vértice inexistente.")
            if type(edge.source) is not int or type(edge.target) is not int:
                raise GraphError("Extremos de aresta inválidos.")
            if type(edge.directed) is not bool or type(edge.weighted) is not bool:
                raise GraphError("Tipo de aresta inválido.")
            if not valid_number(edge.weight) or not 0 <= edge.weight <= 1e9:
                raise GraphError("Pesos precisam ser finitos, entre 0 e 1.000.000.000.")
            pair = (edge.source, edge.target)
            reverse = (edge.target, edge.source)
            if pair in seen or (reverse in seen and (not edge.directed or not seen[reverse])):
                raise GraphError("Arestas duplicadas não são permitidas.")
            seen[pair] = edge.directed
            validate_text(edge.label)
            validate_color(edge.color)
        if type(self.next_vertex) is not int or self.next_vertex <= max(self.vertices, default=0):
            raise GraphError("Sequência de IDs de vértices inválida.")
        if type(self.next_edge) is not int or self.next_edge <= max(self.edges, default=0):
            raise GraphError("Sequência de IDs de arestas inválida.")


def valid_number(value: object) -> bool:
    return type(value) in (int, float) and math.isfinite(value)  # type: ignore[arg-type]


def validate_text(value: str) -> None:
    if not isinstance(value, str) or len(value) > 200:
        raise GraphError("Rótulos devem ter até 200 caracteres.")


def validate_color(value: str) -> None:
    if not isinstance(value, str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", value):
        raise GraphError("Cor inválida: use #RRGGBB.")


def generate_graph(
    vertices: int,
    edges: int,
    directed: bool,
    weighted: bool,
    min_weight: float = 1,
    max_weight: float = 10,
    seed: int = 42,
) -> Graph:
    if not 1 <= vertices <= MAX_VERTICES:
        raise GraphError("Quantidade de vértices inválida.")
    capacity = vertices * (vertices - 1) // (1 if directed else 2)
    if not 0 <= edges <= min(capacity, MAX_EDGES):
        raise GraphError(
            f"Esse grafo comporta no máximo {min(capacity, MAX_EDGES)} arestas sem laços."
        )
    if not (0 <= min_weight <= max_weight <= 1e9):
        raise GraphError("Intervalo de pesos inválido.")
    rng = random.Random(seed)
    graph = Graph()
    columns = math.ceil(math.sqrt(vertices))
    for i in range(vertices):
        graph.add_vertex(
            (i % columns) * 130 + rng.uniform(-20, 20), (i // columns) * 130 + rng.uniform(-20, 20)
        )
    starts = [i * (2 * vertices - i - 1) // 2 for i in range(vertices)]
    for index in rng.sample(range(capacity), edges):
        if directed:
            source, target = divmod(index, vertices - 1)
            if target >= source:
                target += 1
        else:
            source = bisect_right(starts, index) - 1
            target = source + 1 + index - starts[source]
        # Samples are unique, so avoid repeated O(E) duplicate scans here.
        edge = Edge(
            graph.next_edge,
            source + 1,
            target + 1,
            directed,
            weighted,
            round(rng.uniform(min_weight, max_weight), 2) if weighted else 1,
        )
        graph.edges[edge.id] = edge
        graph.next_edge += 1
    graph.validate()
    return graph


def layout_positions(graph: Graph, kind: str, seed: int = 42) -> dict[int, tuple[float, float]]:
    ids = sorted(graph.vertices)
    rng = random.Random(seed)
    columns = max(1, math.ceil(math.sqrt(len(ids))))
    result = {}
    for index, key in enumerate(ids):
        if kind == "circular":
            angle = 2 * math.pi * index / max(1, len(ids)) - math.pi / 2
            radius = max(180, len(ids) * 13)
            xy = (math.cos(angle) * radius, math.sin(angle) * radius)
        elif kind == "random":
            extent = columns * 130
            xy = (rng.uniform(0, extent), rng.uniform(0, extent))
        else:
            xy = (float(index % columns * 130), float(index // columns * 130))
        if not graph.vertices[key].pinned:
            result[key] = xy
    return result
