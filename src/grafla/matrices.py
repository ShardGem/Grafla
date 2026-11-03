from __future__ import annotations

import math

from PyQt6.QtCore import QAbstractTableModel, QModelIndex, Qt

from grafla.domain import Edge, Graph, GraphError

ROOT_INDEX = QModelIndex()


def to_matrix(graph: Graph, weighted: bool = False) -> tuple[list[int], list[list[float | None]]]:
    ids = sorted(graph.vertices)
    if len(ids) > 500:
        raise GraphError("A visualização matricial está limitada a 500 vértices (250.000 células).")
    indices = {key: i for i, key in enumerate(ids)}
    matrix: list[list[float | None]] = [[None if weighted else 0 for _ in ids] for _ in ids]
    for edge in graph.edges.values():
        i, j = indices[edge.source], indices[edge.target]
        matrix[i][j] = edge.cost if weighted else 1
        if not edge.directed:
            matrix[j][i] = matrix[i][j]
    return ids, matrix


def from_matrix(matrix: list[list[float | None]], directed: bool, weighted: bool) -> Graph:
    n = len(matrix)
    if not 1 <= n <= 500 or any(len(row) != n for row in matrix):
        raise GraphError("A matriz deve ser quadrada, entre 1 e 500 vértices.")
    if not directed and any(matrix[i][j] != matrix[j][i] for i in range(n) for j in range(i)):
        raise GraphError("Uma matriz não direcionada precisa ser simétrica.")
    graph = Graph()
    columns = math.ceil(math.sqrt(n))
    for index in range(n):
        graph.add_vertex(index % columns * 130, index // columns * 130)
    for i, row in enumerate(matrix):
        for j, value in enumerate(row):
            if not directed and j < i:
                continue
            if value is None or (not weighted and value == 0):
                continue
            if not weighted and value != 1:
                raise GraphError("Adjacência binária aceita apenas 0 e 1.")
            edge = Edge(graph.next_edge, i + 1, j + 1, directed, weighted, value)
            graph.edges[edge.id] = edge
            graph.next_edge += 1
    graph.validate()
    return graph


class MatrixModel(QAbstractTableModel):
    def __init__(self, values, ids, editable=False, directed=False, weighted=False, parent=None):
        super().__init__(parent)
        self.values, self.ids = values, ids
        self.editable, self.directed, self.weighted = editable, directed, weighted

    def rowCount(self, parent=ROOT_INDEX):
        return 0 if parent.isValid() else len(self.values)

    def columnCount(self, parent=ROOT_INDEX):
        return 0 if parent.isValid() else len(self.values)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            value = self.values[index.row()][index.column()]
            return "·" if value is None else f"{value:g}"
        if role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignmentFlag.AlignCenter
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        return str(self.ids[section]) if role == Qt.ItemDataRole.DisplayRole else None

    def flags(self, index):
        flags = super().flags(index)
        return flags | Qt.ItemFlag.ItemIsEditable if self.editable else flags

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if not self.editable or not index.isValid() or role != Qt.ItemDataRole.EditRole:
            return False
        try:
            number = (
                None
                if str(value).strip() in {"", ".", "·"}
                else float(str(value).replace(",", "."))
            )
            if number is not None and (not math.isfinite(number) or not 0 <= number <= 1e9):
                return False
            if not self.weighted and number not in (None, 0, 1):
                return False
        except ValueError:
            return False
        if number is None and not self.weighted:
            number = 0
        r, c = index.row(), index.column()
        self.values[r][c] = number
        self.dataChanged.emit(index, index)
        if not self.directed:
            self.values[c][r] = number
            opposite = self.index(c, r)
            self.dataChanged.emit(opposite, opposite)
        return True
