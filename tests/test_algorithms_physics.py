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


def test_physics_force_controls_have_distinct_effects():
    from dataclasses import replace

    from grafla.domain import Graph
    from grafla.physics import PhysicsParameters

    graph = Graph()
    graph.add_vertex(-40, 0)
    graph.add_vertex(40, 0)
    graph.add_edge(1, 2)
    neutral = PhysicsParameters(repulsion=0, attraction=0, centering=0)
    assert step(graph, {}, neutral)[0] == {}
    repel, _ = step(graph, {}, replace(neutral, repulsion=4200))
    assert repel[1][0] < -40 and repel[2][0] > 40
    outside_range, _ = step(graph, {}, replace(neutral, repulsion=4200, repulsion_distance=40))
    assert outside_range == {}
    attract, _ = step(graph, {}, replace(neutral, attraction=1, ideal_distance=40))
    assert attract[1][0] > -40 and attract[2][0] < 40
    elastic, _ = step(graph, {}, replace(neutral, attraction=1, ideal_distance=40, stiffness=0.1))
    assert elastic[1][0] > attract[1][0]
    equilibrium, _ = step(graph, {}, replace(neutral, attraction=1, ideal_distance=80))
    assert equilibrium == {}
    centered, _ = step(graph, {}, replace(neutral, centering=0.01))
    assert centered[1][0] > -40 and centered[2][0] < 40


@pytest.mark.parametrize("angle,axis,sign", [(0, 0, 1), (90, 1, 1), (180, 0, -1), (270, 1, -1)])
def test_gravity_direction_is_explicit(angle, axis, sign):
    from grafla.domain import Graph
    from grafla.physics import PhysicsParameters

    graph = Graph()
    graph.add_vertex(0, 0)
    parameters = PhysicsParameters(gravity=1, gravity_angle=angle, centering=0)
    moved, _ = step(graph, {}, parameters)
    assert moved[1][axis] * sign > 0.5
    assert abs(moved[1][1 - axis]) < 1e-10


def test_damping_speed_and_velocity_limit_are_effective_without_mutating_graph(graph):
    from dataclasses import replace

    from grafla.physics import PhysicsParameters

    neutral = PhysicsParameters(repulsion=0, attraction=0, centering=0)
    original = graph.clone()
    _, slow = step(graph, {1: (5, 0)}, replace(neutral, damping=0.8))
    _, fast = step(graph, {1: (5, 0)}, replace(neutral, damping=0.1))
    assert slow < fast
    short, _ = step(graph, {}, replace(neutral, gravity=1, speed=0.25))
    long, _ = step(graph, {}, replace(neutral, gravity=1, speed=2))
    assert long[1][1] > short[1][1]
    _, capped = step(graph, {1: (100, 0), 999: (1000, 0)}, replace(neutral, max_speed=2))
    assert capped <= 2
    assert graph == original


@pytest.mark.parametrize(
    "values",
    [{"damping": 0}, {"speed": 20}, {"gravity": float("nan")}, {"ideal_distance": float("inf")}],
)
def test_invalid_physics_parameters_are_rejected(values):
    from grafla.physics import PhysicsParameters

    with pytest.raises(ValueError):
        PhysicsParameters(**values)


def test_aggressive_physics_remains_bounded_with_coincident_and_pinned_nodes():
    from grafla.domain import Graph
    from grafla.physics import PhysicsParameters

    graph = Graph()
    for index in range(40):
        graph.add_vertex(0 if index < 20 else 1e7, 0)
    graph.vertices[1].pinned = True
    for key in range(1, 40):
        graph.add_edge(key, key + 1)
    parameters = PhysicsParameters(
        repulsion=20000,
        attraction=3,
        stiffness=0.12,
        damping=0.05,
        gravity=2,
        speed=2,
        max_speed=14,
    )
    velocities = {}
    for _ in range(50):
        moved, speed = step(graph, velocities, parameters)
        assert math.isfinite(speed) and speed <= 14.000001
        for key, (x, y) in moved.items():
            assert math.isfinite(x) and math.isfinite(y)
            assert -1e7 <= x <= 1e7 and -1e7 <= y <= 1e7
            graph.vertices[key].x, graph.vertices[key].y = x, y
    assert (graph.vertices[1].x, graph.vertices[1].y) == (0, 0)
    assert velocities[1] == (0, 0)
    graph.validate()
