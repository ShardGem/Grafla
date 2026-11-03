"""Algorithms consume a snapshot, not widgets; expensive searches are bounded."""

from __future__ import annotations

import threading
import time
from collections import deque
from collections.abc import Iterator
from dataclasses import dataclass, field
from itertools import islice

import networkx as nx

from grafla.domain import Graph, GraphError

ALGORITHMS = {
    "shortest": "Menor caminho · Dijkstra",
    "longest": "Maior caminho simples · limitado",
    "all": "Caminhos simples · limitados",
    "bfs": "Busca em largura · BFS",
    "dfs": "Busca em profundidade · DFS",
    "components": "Componentes conexos / fracos",
    "mst": "Árvore geradora mínima",
    "topological": "Ordenação topológica",
}


@dataclass
class Analysis:
    algorithm: str
    paths: list[list[int]] = field(default_factory=list)
    costs: list[float] = field(default_factory=list)
    steps: list[list[int]] = field(default_factory=list)
    frontier: list[list[int]] = field(default_factory=list)
    step_edges: list[list[int]] = field(default_factory=list)
    message: str = ""
    complete: bool = True
    cancelled: bool = False
    elapsed: float = 0


def backend(graph: Graph) -> nx.DiGraph:
    result = nx.DiGraph()
    result.add_nodes_from(graph.vertices)
    for edge in graph.edges.values():
        result.add_edge(edge.source, edge.target, weight=edge.cost, edge_id=edge.id)
        if not edge.directed:
            result.add_edge(edge.target, edge.source, weight=edge.cost, edge_id=edge.id)
    return result


def analyze(
    graph: Graph,
    algorithm: str,
    start: int | None,
    end: int | None,
    cancel: threading.Event | None = None,
    limit: int = 300,
    seconds: float = 1.5,
) -> Analysis:
    graph.validate()
    began = time.monotonic()
    cancel = cancel if cancel is not None else threading.Event()
    if not 1 <= limit <= 1000 or not 0 < seconds <= 10:
        raise GraphError("Orçamento de busca inválido.")
    if algorithm not in ALGORITHMS:
        raise GraphError("Algoritmo desconhecido.")
    result = Analysis(algorithm)
    if algorithm in {"shortest", "longest", "all", "bfs", "dfs"} and start not in graph.vertices:
        raise GraphError("Escolha um vértice de origem.")
    if algorithm in {"shortest", "longest", "all"} and end not in graph.vertices:
        raise GraphError("Escolha um vértice de destino.")
    network = backend(graph)
    if algorithm == "shortest":
        try:
            result.paths = [nx.dijkstra_path(network, start, end, weight="weight")]
        except nx.NetworkXNoPath:
            result.message = "Não existe caminho entre os vértices escolhidos."
    elif algorithm in {"longest", "all"}:
        assert start is not None and end is not None
        deadline = began + seconds
        path = [start]
        visited = {start}
        stack = [iter(sorted(network.neighbors(start)))]
        if start == end:
            result.paths = [[start]]
            stack.clear()
        examined = 0
        best_cost = float("-inf")
        while stack:
            if cancel.is_set() or time.monotonic() >= deadline:
                result.complete = False
                result.cancelled = cancel.is_set()
                break
            neighbor = next(stack[-1], None)
            if neighbor is None:
                stack.pop()
                visited.remove(path.pop())
                continue
            if neighbor in visited:
                continue
            candidate = [*path, neighbor]
            if neighbor == end:
                examined += 1
                if algorithm == "all":
                    result.paths.append(candidate)
                else:
                    cost = nx.path_weight(network, candidate, "weight")
                    if cost > best_cost:
                        result.paths = [candidate]
                        best_cost = cost
                if examined >= limit:
                    result.complete = False
                    break
            else:
                visited.add(neighbor)
                path.append(neighbor)
                stack.append(iter(sorted(network.neighbors(neighbor))))
        result.message = (
            "Busca concluída."
            if result.complete
            else f"Busca interrompida no orçamento ({limit} caminhos / {seconds:g} s). "
            "Resultados parciais; o maior caminho pode não ser ótimo."
        )
        if not result.paths and result.complete:
            result.message = "Não existe caminho entre os vértices escolhidos."
    elif algorithm in {"bfs", "dfs"}:
        assert start is not None
        discovered = {start}
        order: list[int] = []
        # Keep playback memory linear: one visited ID and bounded frontier per step.
        if algorithm == "bfs":
            frontier = deque([start])
            parents: dict[int, int | None] = {start: None}
            while frontier:
                if cancel.is_set():
                    result.complete, result.cancelled = False, True
                    break
                node = frontier.popleft()
                order.append(node)
                for neighbor in sorted(network.neighbors(node)):
                    if neighbor not in discovered:
                        discovered.add(neighbor)
                        parents[neighbor] = network[node][neighbor]["edge_id"]
                        frontier.append(neighbor)
                result.steps.append([node])
                parent_edge = parents[node]
                result.step_edges.append([] if parent_edge is None else [parent_edge])
                result.frontier.append(list(islice(frontier, 30)))
        else:
            # A call-stack iterator is necessary: pre-marking all pushed siblings
            # would produce a wrong DFS discovery tree on graphs with cross edges.
            dfs_stack: list[tuple[int, Iterator[int]]] = [
                (start, iter(sorted(network.neighbors(start))))
            ]
            order.append(start)
            result.steps.append([start])
            result.step_edges.append([])
            result.frontier.append([start])
            while dfs_stack:
                if cancel.is_set():
                    result.complete, result.cancelled = False, True
                    break
                neighbor = next(dfs_stack[-1][1], None)
                if neighbor is None:
                    dfs_stack.pop()
                    continue
                if neighbor in discovered:
                    continue
                parent = dfs_stack[-1][0]
                discovered.add(neighbor)
                dfs_stack.append((neighbor, iter(sorted(network.neighbors(neighbor)))))
                order.append(neighbor)
                result.steps.append([neighbor])
                result.step_edges.append([network[parent][neighbor]["edge_id"]])
                result.frontier.append([frame[0] for frame in dfs_stack[-30:]])
        result.message = f"{len(order)} vértice(s) visitado(s)."
    elif algorithm == "components":
        parts = sorted(nx.weakly_connected_components(network), key=lambda p: (-len(p), min(p)))
        result.steps = [sorted(part) for part in parts]
        result.message = f"{len(parts)} componente(s). Direção ignorada para conectividade fraca."
    elif algorithm == "mst":
        if any(edge.directed for edge in graph.edges.values()):
            raise GraphError("Árvore geradora mínima exige um grafo não direcionado.")
        forest = nx.minimum_spanning_tree(network.to_undirected(), weight="weight")
        result.paths = [[a, b] for a, b in forest.edges]
        result.message = (
            f"Floresta geradora mínima · {nx.number_connected_components(forest)} componente(s)."
        )
    elif algorithm == "topological":
        if any(not edge.directed for edge in graph.edges.values()):
            raise GraphError("Ordenação topológica exige todas as arestas direcionadas.")
        try:
            order = list(nx.topological_sort(network))
        except nx.NetworkXUnfeasible as error:
            raise GraphError("O grafo contém ciclo; não há ordenação topológica.") from error
        result.steps = [[key] for key in order]
        result.message = f"Ordenação de {len(order)} vértices."
    result.costs = [float(nx.path_weight(network, path, "weight")) for path in result.paths]
    result.cancelled |= cancel.is_set()
    if result.cancelled:
        result.complete = False
    result.elapsed = time.monotonic() - began
    return result


def format_result(graph: Graph, result: Analysis) -> str:
    """Bound display work as well as search work; the underlying result stays intact."""
    lines = [
        ALGORITHMS[result.algorithm],
        f"Tempo: {result.elapsed * 1000:.2f} ms",
        "Concluído" if result.complete else "Resultado parcial",
        result.message,
    ]
    if result.algorithm == "mst":
        lines.append(f"Custo total: {sum(result.costs):g}")
    if result.algorithm in {"bfs", "dfs", "topological"}:
        lines.append("Ordem: " + " → ".join(str(key) for step in result.steps for key in step))
    remaining = 100_000 - sum(len(line) + 1 for line in lines)
    groups = (
        result.paths if result.paths else (result.steps if result.algorithm == "components" else [])
    )
    for index, path in enumerate(groups):
        labels = [graph.vertices[key].label or str(key) for key in path[:100]]
        line = f"{index + 1}. " + " → ".join(labels)
        if len(path) > 100:
            line += f" … [mais {len(path) - 100} vértices; caminho abreviado]"
        if result.paths:
            line += f"  |  Custo: {result.costs[index]:g}"
        if len(line) > remaining:
            lines.append("Exibição limitada a 100.000 caracteres; use a navegação visual.")
            break
        lines.append(line)
        remaining -= len(line) + 1
    return "\n".join(lines)
