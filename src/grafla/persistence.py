"""Versioned documents. Decode fully before touching an open editor."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QIODevice, QSaveFile

from grafla.domain import Edge, Graph, GraphError, Vertex

FORMAT_VERSION = 1
MAX_FILE_BYTES = 32 * 1024 * 1024


class DocumentError(ValueError):
    pass


def encode(graph: Graph) -> bytes:
    graph.validate()
    data = {
        "format": "grafla",
        "schema_version": FORMAT_VERSION,
        "graph": {
            "vertices": [asdict(v) for v in graph.vertices.values()],
            "edges": [asdict(e) for e in graph.edges.values()],
            "next_vertex": graph.next_vertex,
            "next_edge": graph.next_edge,
        },
    }
    return json.dumps(data, ensure_ascii=False, allow_nan=False, indent=2).encode("utf-8")


def decode(raw: bytes) -> Graph:
    if len(raw) > MAX_FILE_BYTES:
        raise DocumentError("Arquivo maior que o limite de 32 MB.")
    try:
        data: Any = json.loads(raw)
        if not isinstance(data, dict) or data.get("format") != "grafla":
            raise DocumentError("Este arquivo não é um documento Grafla.")
        if type(data.get("schema_version")) is not int or data["schema_version"] != FORMAT_VERSION:
            raise DocumentError("Versão de documento incompatível com este Grafla.")
        payload = data["graph"]
        vertices = [Vertex(**v) for v in payload["vertices"]]
        edges = [Edge(**e) for e in payload["edges"]]
        graph = Graph(
            {v.id: v for v in vertices},
            {e.id: e for e in edges},
            payload["next_vertex"],
            payload["next_edge"],
        )
        if len(vertices) != len(graph.vertices) or len(edges) != len(graph.edges):
            raise DocumentError("O arquivo contém IDs duplicados.")
        graph.validate()
        return graph
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
        TypeError,
        KeyError,
        GraphError,
        RecursionError,
        OverflowError,
    ) as error:
        raise DocumentError(f"Documento inválido: {error}") from error


def load(path: Path) -> Graph:
    with path.open("rb") as source:
        return decode(source.read(MAX_FILE_BYTES + 1))


def save(path: Path, graph: Graph) -> None:
    raw = encode(graph)
    target = QSaveFile(str(path))
    if not target.open(QIODevice.OpenModeFlag.WriteOnly):
        raise OSError(target.errorString())
    if target.write(raw) != len(raw):
        target.cancelWriting()
        raise OSError(target.errorString())
    if not target.commit():
        raise OSError(target.errorString())
