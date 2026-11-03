import math
import threading

import pytest

from grafla.algorithms import analyze
from grafla.domain import GraphError, generate_graph
from grafla.physics import step


def test_shortest_cost_includes_weight_one(graph):
    result = analyze(graph, "shortest", 1, 3)
    assert result.paths == [[1, 2, 3]]
    assert result.costs == [3]


def test_no_path_is_not_an_empty_route_with_zero_cost(graph):
    result = analyze(graph, "shortest", 3, 1)
    assert result.paths == []
    assert "Não existe" in result.message


def test_zero_weight_and_origin_equals_destination(graph):
    graph.edges[1].weight = 0
    assert analyze(graph, "shortest", 1, 2).costs == [0]
    assert analyze(graph, "shortest", 1, 1).paths == [[1]]


def test_exhaustive_routes_are_correct_on_small_graph(graph):
    graph.add_edge(1, 3, True, True, 8)
    result = analyze(graph, "all", 1, 3)
    assert result.complete
    assert {tuple(path) for path in result.paths} == {(1, 2, 3), (1, 3)}
    assert analyze(graph, "longest", 1, 3).paths == [[1, 3]]


def test_exhaustive_search_budget_is_explicit():
    graph = generate_graph(9, 72, True, False)
    result = analyze(graph, "all", 1, 9, limit=5)
    assert len(result.paths) == 5
    assert not result.complete
    assert "parciais" in result.message
    cancel = threading.Event()
    cancel.set()
    result = analyze(graph, "longest", 1, 9, cancel)
    assert result.cancelled and not result.complete


def test_search_times_out_even_when_no_path_is_ever_yielded():
    graph = generate_graph(10, 90, True, False)
    graph.add_vertex(0, 0)
    result = analyze(graph, "all", 1, 11, seconds=0.01)
    assert not result.complete
    assert result.paths == []


@pytest.mark.parametrize("kind", ["bfs", "dfs"])
def test_traversal_steps_have_frontier_and_no_ui_objects(graph, kind):
    result = analyze(graph, kind, 1, None)
    assert result.steps == [[1], [2], [3]]
    assert result.frontier == ([[2], [3], []] if kind == "bfs" else [[1], [1, 2], [1, 2, 3]])


def test_dfs_discovery_tree_does_not_preclaim_siblings(graph):
    graph.add_edge(1, 3, True)
    graph.add_vertex(200, 100)
    graph.add_edge(2, 4, True)
    result = analyze(graph, "dfs", 1, None)
    assert result.steps == [[1], [2], [3], [4]]
    assert result.step_edges == [[], [1], [2], [4]]


def test_mst_and_topological_preconditions(graph):
    with pytest.raises(GraphError):
        analyze(graph, "mst", None, None)
    assert analyze(graph, "topological", None, None).steps == [[1], [2], [3]]
    graph.add_edge(3, 1, True)
    with pytest.raises(GraphError):
        analyze(graph, "topological", None, None)


def test_undirected_mst_total_and_components(graph):
    for edge in graph.edges.values():
        edge.directed = False
    result = analyze(graph, "mst", None, None)
    assert sum(result.costs) == 3
    assert analyze(graph, "components", None, None).steps == [[1, 2, 3]]


def test_physics_moves_mobile_nodes_but_keeps_pinned_and_finite(graph):
    graph.vertices[1].pinned = True
    origin = (graph.vertices[1].x, graph.vertices[1].y)
    before = graph.vertices[3].x
    velocities = {}
    for _ in range(80):
        moved, speed = step(graph, velocities)
        assert math.isfinite(speed)
        for key, (x, y) in moved.items():
            graph.vertices[key].x, graph.vertices[key].y = x, y
    assert (graph.vertices[1].x, graph.vertices[1].y) == origin
    assert graph.vertices[3].x != before
    graph.validate()


def test_coincident_nodes_separate_even_with_pinned_neighbor(graph):
    graph.vertices[1].pinned = True
    graph.vertices[2].x = graph.vertices[1].x
    moved, _ = step(graph, {})
    assert 1 not in moved
    assert moved[2] != (graph.vertices[2].x, graph.vertices[2].y)
