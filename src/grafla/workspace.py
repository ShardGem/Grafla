"""Integrated canvas controls and construction panels; no nested modal workflow."""

import csv
import io
import math

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QSpinBox,
    QTableView,
    QTabWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from grafla.domain import GraphError, generate_graph
from grafla.matrices import MatrixModel, from_matrix, to_matrix


class ZoomBar(QFrame):
    zoom_requested = pyqtSignal(float)
    fit_requested = pyqtSignal()
    reset_requested = pyqtSignal()
    grid_changed = pyqtSignal(bool)
    snap_changed = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("CanvasControls")
        row = QHBoxLayout(self)
        row.setContentsMargins(12, 7, 12, 7)
        row.setSpacing(8)
        self.minus, self.plus = QToolButton(), QToolButton()
        self.minus.setText("−")
        self.plus.setText("+")
        self.minus.setToolTip("Afastar")
        self.plus.setToolTip("Aproximar")
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 1000)
        self.slider.setMinimumWidth(100)
        self.slider.setMaximumWidth(220)
        self.slider.setAccessibleName("Zoom do canvas")
        self.slider.setToolTip("Escala de zoom · Ctrl+roda também aproxima no cursor")
        self.percent = QToolButton()
        self.percent.setToolTip("Redefinir para 100%")
        fit = QPushButton("Ajustar grafo")
        fit.clicked.connect(self.fit_requested.emit)
        for widget in (self.minus, self.slider, self.plus, self.percent, fit):
            row.addWidget(widget)
        row.addStretch()
        self.grid, self.snap = QCheckBox("Grade"), QCheckBox("Snap")
        self.grid.toggled.connect(self.grid_changed.emit)
        self.snap.toggled.connect(self.snap_changed.emit)
        row.addWidget(self.grid)
        row.addWidget(self.snap)
        self.percent.clicked.connect(self.reset_requested.emit)
        self.slider.valueChanged.connect(self.request_zoom)
        self.minus.clicked.connect(lambda: self.slider.setValue(self.slider.value() - 35))
        self.plus.clicked.connect(lambda: self.slider.setValue(self.slider.value() + 35))
        self.set_scale(1.0)

    @staticmethod
    def scale_at(value):
        return 0.02 * (4 / 0.02) ** (value / 1000)

    def request_zoom(self, value):
        self.zoom_requested.emit(self.scale_at(value))

    def set_scale(self, scale):
        value = round(1000 * math.log(max(0.02, min(4, scale)) / 0.02) / math.log(200))
        self.slider.blockSignals(True)
        self.slider.setValue(value)
        self.slider.blockSignals(False)
        self.percent.setText(f"{scale * 100:.0f}%")


class GeneratorPanel(QWidget):
    graph_ready = pyqtSignal(str, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        intro = QLabel("GERAR UM GRAFO")
        intro.setProperty("muted", True)
        layout.addWidget(intro)
        form = QFormLayout()
        self.vertices, self.edges, self.seed = QSpinBox(), QSpinBox(), QSpinBox()
        self.vertices.setRange(1, 500)
        self.vertices.setValue(12)
        self.edges.setRange(0, 5000)
        self.edges.setValue(18)
        self.seed.setRange(0, 2**31 - 1)
        self.seed.setValue(42)
        self.directed = QCheckBox("Direcionadas")
        self.weighted = QCheckBox("Ponderadas")
        self.minimum, self.maximum = QDoubleSpinBox(), QDoubleSpinBox()
        for spin in (self.minimum, self.maximum):
            spin.setRange(0, 1e6)
            spin.setEnabled(False)
        self.minimum.setValue(1)
        self.maximum.setValue(10)
        self.weighted.toggled.connect(self.minimum.setEnabled)
        self.weighted.toggled.connect(self.maximum.setEnabled)
        for title, widget in (
            ("Vértices", self.vertices),
            ("Arestas", self.edges),
            ("Conexões", self.directed),
            ("Pesos", self.weighted),
            ("Peso mínimo", self.minimum),
            ("Peso máximo", self.maximum),
            ("Seed", self.seed),
        ):
            form.addRow(title, widget)
        layout.addLayout(form)
        self.capacity, self.feedback = QLabel(), QLabel()
        for label in (self.capacity, self.feedback):
            label.setWordWrap(True)
            label.setProperty("muted", True)
            layout.addWidget(label)
        self.apply = QPushButton("Gerar grafo")
        self.apply.setProperty("primary", True)
        self.apply.clicked.connect(self.submit)
        layout.addWidget(self.apply)
        note = QLabel(
            "Substitui o grafo atual em uma única operação. Ctrl+Z desfaz.\nA seed permite repetir o mesmo exemplo."
        )
        note.setWordWrap(True)
        note.setProperty("muted", True)
        layout.addWidget(note)
        layout.addStretch()
        self.vertices.valueChanged.connect(self.update_capacity)
        self.directed.toggled.connect(self.update_capacity)
        self.update_capacity()

    def update_capacity(self):
        n = self.vertices.value()
        capacity = min(5000, n * (n - 1) // (1 if self.directed.isChecked() else 2))
        self.edges.setMaximum(capacity)
        self.capacity.setText(f"Capacidade: {capacity} conexões únicas, sem laços.")

    def submit(self):
        try:
            graph = generate_graph(
                self.vertices.value(),
                self.edges.value(),
                self.directed.isChecked(),
                self.weighted.isChecked(),
                self.minimum.value(),
                self.maximum.value(),
                self.seed.value(),
            )
        except GraphError as error:
            self.feedback.setText(str(error))
            return
        self.graph_ready.emit("Gerar grafo", graph)
        self.feedback.setText("Grafo aplicado. Você pode continuar ajustando os parâmetros.")


class MatrixPanel(QWidget):
    graph_ready = pyqtSignal(str, object)

    def __init__(self, graph, parent=None):
        super().__init__(parent)
        self.graph = graph
        self.model = None
        layout = QVBoxLayout(self)
        self.mode = QComboBox()
        self.mode.addItems(["Representar o grafo atual", "Criar grafo de uma matriz"])
        layout.addWidget(self.mode)
        self.count = QSpinBox()
        self.count.setRange(1, 100)
        self.count.setValue(5)
        self.directed, self.weighted = QCheckBox("Direcionada"), QCheckBox("Pesos")
        row = QHBoxLayout()
        self.count_label = QLabel("Vértices")
        for widget in (self.count_label, self.count, self.directed, self.weighted):
            row.addWidget(widget)
        layout.addLayout(row)
        self.note = QLabel()
        self.note.setWordWrap(True)
        self.note.setProperty("muted", True)
        layout.addWidget(self.note)
        self.table = QTableView()
        self.table.horizontalHeader().setDefaultSectionSize(54)
        self.table.verticalHeader().setDefaultSectionSize(30)
        self.table.setMinimumHeight(180)
        layout.addWidget(self.table, 1)
        self.feedback = QLabel()
        self.feedback.setWordWrap(True)
        layout.addWidget(self.feedback)
        row = QHBoxLayout()
        self.copy = QPushButton("Copiar CSV")
        self.copy.clicked.connect(self.copy_csv)
        self.apply = QPushButton("Aplicar ao grafo")
        self.apply.setProperty("primary", True)
        self.apply.clicked.connect(self.submit)
        row.addWidget(self.copy)
        row.addWidget(self.apply)
        layout.addLayout(row)
        self.mode.currentIndexChanged.connect(self.mode_changed)
        self.count.valueChanged.connect(self.rebuild)
        self.directed.toggled.connect(self.rebuild)
        self.weighted.toggled.connect(self.rebuild)
        self.mode_changed()

    @property
    def importing(self):
        return self.mode.currentIndex() == 1

    def showEvent(self, event):
        if not self.importing:
            self.rebuild()
        super().showEvent(event)

    def set_graph(self, graph):
        self.graph = graph
        if not self.importing and self.isVisible():
            self.rebuild()

    def mode_changed(self):
        for widget in (self.count, self.count_label, self.directed, self.apply):
            widget.setVisible(self.importing)
        self.note.setText(
            "Edite com duplo clique. · é ausência; peso 0 é uma conexão real.\nAplicar substitui o grafo e pode ser desfeito."
            if self.importing
            else "IDs nas linhas e colunas. Matriz não preserva rótulos, posições ou a direção de cada aresta de um grafo misto."
        )
        self.rebuild(reset=True)

    def rebuild(self, *args, reset=False):
        self.feedback.clear()
        weighted, directed = self.weighted.isChecked(), self.directed.isChecked()
        if not self.importing:
            try:
                ids, values = to_matrix(self.graph, weighted)
            except GraphError as error:
                ids, values = [], []
                self.feedback.setText(str(error))
        else:
            n = self.count.value()
            ids = list(range(1, n + 1))
            absent = None if weighted else 0
            values = [[absent for _ in range(n)] for _ in range(n)]
            old = self.model
            if not reset and old is not None and old.editable:
                for i in range(min(n, len(old.values))):
                    for j in range(min(n, len(old.values))):
                        value = old.values[i][j]
                        if weighted != old.weighted:
                            value = (
                                (None if value == 0 else value)
                                if weighted
                                else (0 if value is None else 1)
                            )
                        values[i][j] = value
                if not directed:
                    for i in range(n):
                        for j in range(i):
                            a, b = values[i][j], values[j][i]
                            if a != absent and b != absent and a != b:
                                self.directed.blockSignals(True)
                                self.directed.setChecked(True)
                                self.directed.blockSignals(False)
                                self.feedback.setText(
                                    "Há pesos diferentes nos dois sentidos. Iguale-os antes de remover a direção."
                                )
                                return
                            values[i][j] = values[j][i] = b if b != absent else a
        old = self.model
        self.model = MatrixModel(values, ids, self.importing, directed, weighted, self)
        self.table.setModel(self.model)
        if old is not None:
            old.deleteLater()
        self.copy.setEnabled(bool(values))

    def copy_csv(self):
        stream = io.StringIO()
        csv.writer(stream).writerows(
            [["." if v is None else f"{v:g}" for v in row] for row in self.model.values]
        )
        QApplication.clipboard().setText(stream.getvalue())
        self.feedback.setText("Matriz copiada em CSV.")

    def submit(self):
        try:
            graph = from_matrix(
                self.model.values, self.directed.isChecked(), self.weighted.isChecked()
            )
        except GraphError as error:
            self.feedback.setText(str(error))
            return
        self.graph_ready.emit("Aplicar matriz", graph)
        self.feedback.setText("Matriz aplicada. Ctrl+Z recupera o grafo anterior.")


class BuildPanel(QTabWidget):
    graph_ready = pyqtSignal(str, object)

    def __init__(self, graph, commands, parent=None):
        super().__init__(parent)
        self.generator = GeneratorPanel()
        self.matrix = MatrixPanel(graph)
        self.addTab(self.generator, "Gerar")
        self.addTab(self.matrix, "Matriz")
        layouts = QWidget()
        layout = QVBoxLayout(layouts)
        label = QLabel("ORGANIZAR O GRAFO")
        label.setProperty("muted", True)
        layout.addWidget(label)
        for key, label in (("circular", "Circular"), ("grid", "Grade"), ("random", "Aleatório")):
            button = QPushButton(label)
            button.clicked.connect(commands[f"layout_{key}"].trigger)
            layout.addWidget(button)
        note = QLabel("Layouts respeitam vértices fixados e são uma única operação de undo.")
        note.setWordWrap(True)
        note.setProperty("muted", True)
        layout.addWidget(note)
        physics = QToolButton()
        physics.setDefaultAction(commands["physics"])
        physics.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        layout.addWidget(physics)
        layout.addStretch()
        self.addTab(layouts, "Layouts")
        self.generator.graph_ready.connect(self.graph_ready.emit)
        self.matrix.graph_ready.connect(self.graph_ready.emit)
