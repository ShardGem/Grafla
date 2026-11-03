import math

import pytest

from grafla.domain import Graph, GraphError, generate_graph, layout_positions
from grafla.matrices import from_matrix, to_matrix


def test_mixed_direction_loop_and_zero_cost():
    graph = Graph()
    graph.add_vertex(0, 0)
    graph.add_vertex(100, 0)
    graph.add_edge(1, 2)
    graph.add_edge(1, 1, True, True, 0)
    graph.validate()
    assert graph.kind == "Misto"
    assert graph.adjacency() == {1: [(2, 1.0, 1), (1, 0, 2)], 2: [(1, 1.0, 1)]}


def test_duplicate_policy_preserves_opposite_directed_edges(graph):
    graph.add_edge(2, 1, True)
    with pytest.raises(GraphError):
        graph.add_edge(2, 1, True)
    with pytest.raises(GraphError):
        graph.add_edge(2, 1, False)
    graph.validate()


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -1])
def test_invalid_weights_rejected(graph, value):
    graph.edges[1].weight = value
    with pytest.raises(GraphError):
        graph.validate()


def test_remove_cascades_incident_edges(graph):
    graph.remove({2}, set())
    assert set(graph.vertices) == {1, 3}
    assert not graph.edges
    graph.validate()


@pytest.mark.parametrize("directed", [False, True])
@pytest.mark.parametrize("n", [1, 2, 4, 12])
def test_generator_respects_exact_capacity_and_seed(n, directed):
    count = n * (n - 1) // (1 if directed else 2)
    graph = generate_graph(n, count, directed, True, seed=9)
    assert len(graph.edges) == count
    assert graph == generate_graph(n, count, directed, True, seed=9)
    assert all(e.source != e.target for e in graph.edges.values())
    graph.validate()


def test_generator_invalid_request_does_not_partially_return():
    with pytest.raises(GraphError):
        generate_graph(1, 1, False, False)


def test_undirected_matrix_creates_one_edge():
    graph = from_matrix([[0, 1], [1, 0]], False, False)
    assert len(graph.edges) == 1
    assert to_matrix(graph)[1] == [[0, 1], [1, 0]]


def test_weight_matrix_distinguishes_zero_and_absence():
    values = [[None, 0], [None, None]]
    graph = from_matrix(values, True, True)
    assert len(graph.edges) == 1
    assert graph.edges[1].cost == 0
    assert to_matrix(graph, True)[1] == values


def test_matrix_rejects_asymmetry_and_bad_values():
    with pytest.raises(GraphError):
        from_matrix([[0, 1], [0, 0]], False, False)
    with pytest.raises(GraphError):
        from_matrix([[2]], False, False)


@pytest.mark.parametrize("kind", ["grid", "circular", "random"])
def test_layout_is_finite_and_respects_pinned(graph, kind):
    graph.vertices[1].pinned = True
    positions = layout_positions(graph, kind)
    assert set(positions) == {2, 3}
    assert all(math.isfinite(value) for pair in positions.values() for value in pair)
