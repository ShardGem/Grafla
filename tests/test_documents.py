import json

import pytest

from grafla.document import Document
from grafla.domain import GraphError
from grafla.persistence import DocumentError, decode, encode, load


def test_roundtrip_all_graph_properties(graph):
    graph.vertices[1].label = "Origem <A> & São Paulo"
    graph.vertices[1].color = "#ff1234"
    graph.vertices[1].radius = 32
    graph.vertices[1].pinned = True
    graph.edges[1].label = "Rota útil"
    graph.edges[1].weight = 0
    assert decode(encode(graph)) == graph


@pytest.mark.parametrize("change", ["future", "duplicate", "missing_endpoint", "nan", "bad_color"])
def test_invalid_document_is_rejected(graph, change):
    data = json.loads(encode(graph))
    if change == "future":
        data["schema_version"] = 999
    elif change == "duplicate":
        data["graph"]["vertices"].append(data["graph"]["vertices"][0])
    elif change == "missing_endpoint":
        data["graph"]["edges"][0]["target"] = 777
    elif change == "nan":
        data["graph"]["vertices"][0]["x"] = float("nan")
    else:
        data["graph"]["vertices"][0]["color"] = "invalid"
    with pytest.raises(DocumentError):
        decode(json.dumps(data).encode())


def test_delete_undo_redo_restores_incident_edges_and_attributes(qapp, graph):
    document = Document()
    document.reset(graph)
    document.edit("Excluir", lambda g: g.remove({2}, set()))
    assert set(document.graph.vertices) == {1, 3}
    assert not document.graph.edges
    assert document.dirty
    document.undo()
    assert document.graph == graph
    assert not document.dirty
    document.redo()
    assert not document.graph.edges


def test_save_clean_state_and_atomic_failure(qapp, graph, tmp_path):
    document = Document()
    document.replace("Criar", graph)
    document.write(tmp_path / "document.grafla")
    assert load(document.path) == graph
    assert not document.dirty
    document.edit("Rótulo", lambda g: setattr(g.vertices[1], "label", "Novo"))
    with pytest.raises(OSError):
        document.write(tmp_path / "missing" / "bad.grafla")
    assert document.dirty
    assert load(tmp_path / "document.grafla") == graph
    document.undo()
    assert not document.dirty


def test_failed_edit_is_transactional(qapp, graph):
    document = Document()
    document.reset(graph)
    with pytest.raises(GraphError):
        document.edit("Inválida", lambda g: setattr(g.edges[1], "weight", -9))
    assert document.graph == graph
    assert not document.dirty
    assert document.undo_stack.count() == 0


def test_branch_after_undo_cannot_restore_old_saved_state(qapp, graph, tmp_path):
    document = Document()
    document.replace("Criar", graph)
    document.write(tmp_path / "saved.grafla")
    document.undo()
    document.edit("Outro grafo", lambda g: g.add_vertex(50, 50))
    assert document.dirty
    assert not document.undo_stack.canRedo()
