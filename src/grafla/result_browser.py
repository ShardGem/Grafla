"""Views of analysis data: selectable routes and a lazy table of algorithm steps."""

from PyQt6.QtCore import QAbstractTableModel, QModelIndex, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSlider,
    QStackedWidget,
    QTableView,
    QVBoxLayout,
)

ROOT = QModelIndex()


def vertex_name(graph, key, limit=24):
    label = graph.vertices[key].label or str(key)
    return label if len(label) <= limit else label[: limit - 1] + "…"


class StepModel(QAbstractTableModel):
    def __init__(self, graph, result, parent=None):
        super().__init__(parent)
        self.graph, self.result = graph, result

    def rowCount(self, parent=ROOT):
        return 0 if parent.isValid() else len(self.result.steps)

    def columnCount(self, parent=ROOT):
        return 0 if parent.isValid() else 3

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return ("Passo", "Visita / grupo", "Fila / pilha")[section]
        return None

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        if role not in {Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.ToolTipRole}:
            return None
        row, col = index.row(), index.column()
        if col == 0:
            return str(row + 1)
        if col == 1:
            group = self.result.steps[row]
            names = [vertex_name(self.graph, key) for key in group[:5]]
            return ", ".join(names) + (f" … ({len(group)})" if len(group) > 5 else "")
        if self.result.frontier:
            return (
                ", ".join(vertex_name(self.graph, key, 12) for key in self.result.frontier[row])
                or "—"
            )
        return "—"


class ResultBrowser(QFrame):
    index_selected = pyqtSignal(int)
    report_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ResultBrowser")
        self.graph, self.result = None, None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        row = QHBoxLayout()
        title = QLabel("RESULTADO")
        title.setProperty("muted", True)
        row.addWidget(title, 1)
        report = QPushButton("Relatório ↗")
        report.clicked.connect(self.report_requested.emit)
        row.addWidget(report)
        layout.addLayout(row)
        self.metric = QLabel("Pronto para explorar")
        self.metric.setObjectName("ResultMetric")
        self.metric.setTextFormat(Qt.TextFormat.PlainText)
        layout.addWidget(self.metric)
        self.sequence = QLabel("Execute uma análise para ligar os resultados ao canvas.")
        self.sequence.setWordWrap(True)
        self.sequence.setTextFormat(Qt.TextFormat.PlainText)
        self.sequence.setProperty("muted", True)
        layout.addWidget(self.sequence)
        self.filter = QLineEdit()
        self.filter.setPlaceholderText("Filtrar rotas por vértice ou custo…")
        self.filter.textChanged.connect(self.filter_routes)
        self.filter.hide()
        layout.addWidget(self.filter)
        self.stack = QStackedWidget()
        self.empty = QLabel(
            "O grafo permanece livre para edição.\nSelecione uma rota ou etapa para ver seu destaque."
        )
        self.empty.setWordWrap(True)
        self.empty.setProperty("muted", True)
        self.stack.addWidget(self.empty)
        self.routes = QListWidget()
        self.routes.setObjectName("RouteList")
        self.routes.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.routes.setAccessibleName("Rotas encontradas")
        self.routes.currentRowChanged.connect(self.choose_route)
        self.stack.addWidget(self.routes)
        self.steps = QTableView()
        self.steps.setAccessibleName("Etapas do algoritmo")
        self.steps.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.steps.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.steps.verticalHeader().hide()
        self.steps.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.stack.addWidget(self.steps)
        layout.addWidget(self.stack, 1)
        self.scrub = QSlider(Qt.Orientation.Horizontal)
        self.scrub.setAccessibleName("Etapa da execução")
        self.scrub.valueChanged.connect(self.index_selected.emit)
        self.scrub.hide()
        layout.addWidget(self.scrub)
        self.stack.setMinimumHeight(125)

    def clear(self):
        self.result, self.graph = None, None
        self.routes.blockSignals(True)
        self.routes.clear()
        self.routes.blockSignals(False)
        old = self.steps.model()
        old_selection = self.steps.selectionModel()
        self.steps.setModel(None)
        if old_selection is not None:
            old_selection.deleteLater()
        if old is not None:
            old.deleteLater()
        self.stack.setCurrentIndex(0)
        self.filter.clear()
        self.filter.hide()
        self.scrub.hide()
        self.metric.setText("Pronto para explorar")
        self.sequence.setText("Execute uma análise para ligar os resultados ao canvas.")

    def set_result(self, graph, result):
        self.clear()
        self.graph, self.result = graph, result
        state = "completo" if result.complete else "parcial"
        if result.paths:
            self.routes.blockSignals(True)
            for index, path in enumerate(result.paths):
                names = [vertex_name(graph, key, 18) for key in path[:6]]
                sequence = " → ".join(names) + (" → …" if len(path) > 6 else "")
                kind = "Aresta" if result.algorithm == "mst" else "Rota"
                item = QListWidgetItem(
                    f"{kind} {index + 1}   ·   Custo {result.costs[index]:g}\n{sequence}"
                )
                item.setData(Qt.ItemDataRole.UserRole, index)
                self.routes.addItem(item)
            self.routes.blockSignals(False)
            self.stack.setCurrentIndex(1)
            self.filter.setVisible(len(result.paths) > 1)
            self.metric.setText(
                f"{len(result.paths)} {'arestas' if result.algorithm == 'mst' else 'rotas'} · {state}"
            )
        elif result.steps:
            model = StepModel(graph, result, self)
            self.steps.setModel(model)
            self.steps.selectionModel().currentRowChanged.connect(self.choose_step)
            self.stack.setCurrentIndex(2)
            self.scrub.blockSignals(True)
            self.scrub.setRange(0, len(result.steps) - 1)
            self.scrub.setValue(0)
            self.scrub.blockSignals(False)
            self.scrub.show()
            self.metric.setText(f"{len(result.steps)} etapas · {state}")
        else:
            self.metric.setText("Nenhum caminho encontrado" if result.complete else "Busca parcial")
        self.sequence.setText(result.message)

    def filter_routes(self, text):
        for row in range(self.routes.count()):
            item = self.routes.item(row)
            item.setHidden(text.casefold() not in item.text().casefold())

    def choose_route(self, row):
        if self.result is not None and row >= 0:
            self.index_selected.emit(row)

    def choose_step(self, current, previous):
        if self.result is not None and current.isValid():
            self.index_selected.emit(current.row())

    def set_index(self, index):
        if self.result is None:
            return
        result = self.result
        self.scrub.blockSignals(True)
        self.scrub.setValue(index)
        self.scrub.blockSignals(False)
        if result.paths:
            self.routes.blockSignals(True)
            self.routes.setCurrentRow(index)
            self.routes.blockSignals(False)
            path = result.paths[index]
            names = [vertex_name(self.graph, key) for key in path[:12]]
            self.sequence.setText(" → ".join(names) + (" → …" if len(path) > 12 else ""))
            self.metric.setText(f"Custo {result.costs[index]:g}  ·  {len(path)} vértices")
        else:
            model = self.steps.model()
            selection = self.steps.selectionModel()
            selection.blockSignals(True)
            self.steps.selectRow(index)
            selection.blockSignals(False)
            self.steps.scrollTo(model.index(index, 0))
            group = result.steps[index]
            self.sequence.setText(
                "Atual: "
                + ", ".join(vertex_name(self.graph, key) for key in group[:8])
                + (" …" if len(group) > 8 else "")
            )
            self.metric.setText(f"Etapa {index + 1} de {len(result.steps)}")
