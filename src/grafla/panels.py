from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSlider,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from grafla.algorithms import ALGORITHMS


def number(minimum=-1e7, maximum=1e7, decimals=2):
    spin = QDoubleSpinBox()
    spin.setRange(minimum, maximum)
    spin.setDecimals(decimals)
    spin.setKeyboardTracking(False)
    return spin


class Inspector(QScrollArea):
    apply_requested = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        content = QWidget()
        self.setWidget(content)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        self.heading = QLabel("DOCUMENTO")
        self.heading.setProperty("muted", True)
        layout.addWidget(self.heading)
        self.stack = QStackedWidget()
        layout.addWidget(self.stack)
        self.summary = QLabel()
        self.summary.setWordWrap(True)
        empty = QWidget()
        empty_layout = QVBoxLayout(empty)
        empty_layout.setContentsMargins(0, 0, 0, 0)
        empty_layout.addWidget(self.summary)
        hint = QLabel(
            "Selecione um elemento para editar.\nCtrl+clique adiciona à seleção.\n\nDuplo clique abre as propriedades."
        )
        hint.setWordWrap(True)
        hint.setProperty("muted", True)
        empty_layout.addWidget(hint)
        empty_layout.addStretch()
        self.stack.addWidget(empty)
        vertex_page = QWidget()
        form = QFormLayout(vertex_page)
        form.setContentsMargins(0, 0, 0, 0)
        self.vertex_label = QLineEdit()
        self.vertex_label.setMaxLength(200)
        self.vertex_x, self.vertex_y = number(), number()
        self.vertex_radius = number(12, 100, 0)
        self.vertex_color = QLineEdit()
        self.vertex_color.setPlaceholderText("#RRGGBB")
        self.vertex_pinned = QCheckBox("Fixar durante a física e layouts")
        for label, widget in (
            ("Rótulo", self.vertex_label),
            ("X", self.vertex_x),
            ("Y", self.vertex_y),
            ("Raio", self.vertex_radius),
            ("Cor", self.vertex_color),
            ("Posição", self.vertex_pinned),
        ):
            form.addRow(label, widget)
        self.stack.addWidget(vertex_page)
        edge_page = QWidget()
        form = QFormLayout(edge_page)
        form.setContentsMargins(0, 0, 0, 0)
        self.edge_endpoints = QLabel()
        self.edge_label = QLineEdit()
        self.edge_label.setMaxLength(200)
        self.edge_directed = QCheckBox("Direcionada")
        self.edge_weighted = QCheckBox("Ponderada")
        self.edge_weight = number(0, 1e9)
        self.edge_color = QLineEdit()
        self.edge_weighted.toggled.connect(self.edge_weight.setEnabled)
        for label, widget in (
            ("Extremos", self.edge_endpoints),
            ("Rótulo", self.edge_label),
            ("Tipo", self.edge_directed),
            ("Peso", self.edge_weighted),
            ("Valor", self.edge_weight),
            ("Cor", self.edge_color),
        ):
            form.addRow(label, widget)
        self.stack.addWidget(edge_page)
        multi_page = QWidget()
        form = QFormLayout(multi_page)
        form.setContentsMargins(0, 0, 0, 0)
        self.multi_color = QLineEdit("#ffad78")
        form.addRow("Cor comum", self.multi_color)
        self.stack.addWidget(multi_page)
        self.apply_button = QPushButton("Aplicar propriedades")
        self.apply_button.setProperty("primary", True)
        self.apply_button.clicked.connect(self.submit)
        layout.addWidget(self.apply_button)
        defaults = QGroupBox("Novas conexões")
        form = QFormLayout(defaults)
        self.create_directed = QCheckBox("Direcionadas")
        self.create_weighted = QCheckBox("Ponderadas")
        self.create_weight = number(0, 1e9)
        self.create_weight.setValue(1)
        self.create_weight.setEnabled(False)
        self.create_weighted.toggled.connect(self.create_weight.setEnabled)
        form.addRow(self.create_directed)
        form.addRow(self.create_weighted)
        form.addRow("Peso padrão", self.create_weight)
        layout.addWidget(defaults)
        tips = QLabel(
            "E · clique na origem e no destino\nEsc · cancelar conexão\nEspaço + arrastar · navegar"
        )
        tips.setProperty("muted", True)
        tips.setWordWrap(True)
        layout.addWidget(tips)
        layout.addStretch()
        self.refresh(None, (set(), set()))

    def refresh(self, graph, selection):
        vertices, edges = selection
        self.apply_button.setVisible(bool(vertices or edges))
        if not vertices and not edges:
            self.heading.setText("DOCUMENTO")
            self.stack.setCurrentIndex(0)
            if graph is not None:
                self.summary.setText(
                    f"{len(graph.vertices)} vértices · {len(graph.edges)} arestas\n{graph.kind}\n\nEdição livre, análise e aprendizado de grafos."
                )
        elif len(vertices) == 1 and not edges:
            v = graph.vertices[next(iter(vertices))]
            self.heading.setText(f"VÉRTICE #{v.id}")
            self.stack.setCurrentIndex(1)
            self.vertex_label.setText(v.label)
            self.vertex_x.setValue(v.x)
            self.vertex_y.setValue(v.y)
            self.vertex_radius.setValue(v.radius)
            self.vertex_color.setText(v.color)
            self.vertex_pinned.setChecked(v.pinned)
        elif len(edges) == 1 and not vertices:
            edge = graph.edges[next(iter(edges))]
            self.heading.setText(f"ARESTA #{edge.id}")
            self.stack.setCurrentIndex(2)
            self.edge_endpoints.setText(f"{edge.source} → {edge.target}")
            self.edge_label.setText(edge.label)
            self.edge_directed.setChecked(edge.directed)
            self.edge_weighted.setChecked(edge.weighted)
            self.edge_weight.setEnabled(edge.weighted)
            self.edge_weight.setValue(edge.weight)
            self.edge_color.setText(edge.color)
        else:
            self.heading.setText(f"SELEÇÃO · {len(vertices) + len(edges)} ELEMENTOS")
            self.stack.setCurrentIndex(3)
        self._displayed_values = self.values()

    def values(self):
        if self.stack.currentIndex() == 1:
            values = {
                "label": self.vertex_label.text(),
                "x": self.vertex_x.value(),
                "y": self.vertex_y.value(),
                "radius": self.vertex_radius.value(),
                "color": self.vertex_color.text(),
                "pinned": self.vertex_pinned.isChecked(),
            }
        elif self.stack.currentIndex() == 2:
            values = {
                "label": self.edge_label.text(),
                "directed": self.edge_directed.isChecked(),
                "weighted": self.edge_weighted.isChecked(),
                "weight": self.edge_weight.value(),
                "color": self.edge_color.text(),
            }
        else:
            values = {"color": self.multi_color.text()}
        return values

    def submit(self):
        values = self.values()
        if self.stack.currentIndex() in (1, 2):
            # Don't round untouched persisted coordinates/weights through spinboxes.
            values = {
                key: value
                for key, value in values.items()
                if value != self._displayed_values.get(key)
            }
        if values:
            self.apply_requested.emit(values)


class AnalysisPanel(QWidget):
    run_requested = pyqtSignal()
    cancel_requested = pyqtSignal()
    clear_requested = pyqtSignal()
    next_requested = pyqtSignal(int)
    play_requested = pyqtSignal()
    restart_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        from grafla.result_browser import ResultBrowser

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(9)
        self.algorithm = QComboBox()
        self.algorithm.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
        self.algorithm.setMinimumContentsLength(14)
        for key, label in ALGORITHMS.items():
            self.algorithm.addItem(label, key)
        layout.addWidget(QLabel("Algoritmo"))
        layout.addWidget(self.algorithm)
        endpoints = QHBoxLayout()
        self.origin, self.destination = QComboBox(), QComboBox()
        for combo in (self.origin, self.destination):
            combo.setMinimumContentsLength(4)
            combo.setSizeAdjustPolicy(
                QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
            )
        endpoints.addWidget(QLabel("De"))
        endpoints.addWidget(self.origin, 1)
        endpoints.addWidget(QLabel("Para"))
        endpoints.addWidget(self.destination, 1)
        layout.addLayout(endpoints)
        self.note = QLabel()
        self.note.setWordWrap(True)
        self.note.setProperty("muted", True)
        layout.addWidget(self.note)
        row = QHBoxLayout()
        self.run = QPushButton("Executar análise")
        self.run.setProperty("primary", True)
        self.cancel = QPushButton("Parar")
        self.cancel.setEnabled(False)
        row.addWidget(self.run, 1)
        row.addWidget(self.cancel)
        layout.addLayout(row)
        self.status = QLabel("Escolha um algoritmo e os vértices de referência.")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.browser = ResultBrowser()
        layout.addWidget(self.browser, 1)
        row = QHBoxLayout()
        self.previous, self.play, self.next = (
            QPushButton("←"),
            QPushButton("Reproduzir"),
            QPushButton("→"),
        )
        self.previous.setToolTip("Passo ou rota anterior")
        self.next.setToolTip("Próximo passo ou rota")
        row.addWidget(self.previous)
        row.addWidget(self.play, 1)
        row.addWidget(self.next)
        layout.addLayout(row)
        self.position = QLabel("Sem execução")
        self.position.setWordWrap(True)
        self.position.setProperty("muted", True)
        layout.addWidget(self.position)
        row = QHBoxLayout()
        row.addWidget(QLabel("Velocidade"))
        self.speed = QSlider(Qt.Orientation.Horizontal)
        self.speed.setRange(1, 10)
        self.speed.setValue(4)
        self.speed.setAccessibleName("Velocidade da visualização")
        row.addWidget(self.speed, 1)
        layout.addLayout(row)
        row = QHBoxLayout()
        self.restart = QPushButton("↺ Reiniciar")
        self.restart.clicked.connect(self.restart_requested.emit)
        clear = QPushButton("Limpar")
        clear.clicked.connect(self.clear_requested.emit)
        row.addWidget(self.restart)
        row.addWidget(clear)
        layout.addLayout(row)
        self.run.clicked.connect(self.run_requested.emit)
        self.cancel.clicked.connect(self.cancel_requested.emit)
        self.previous.clicked.connect(lambda: self.next_requested.emit(-1))
        self.next.clicked.connect(lambda: self.next_requested.emit(1))
        self.play.clicked.connect(self.play_requested.emit)
        self.algorithm.currentIndexChanged.connect(self.inputs)
        self.inputs()
        self.set_playback(False)

    def inputs(self):
        name = self.algorithm.currentData()
        self.origin.setEnabled(name in {"shortest", "longest", "all", "bfs", "dfs"})
        self.destination.setEnabled(name in {"shortest", "longest", "all"})
        notes = {
            "shortest": "Menor custo total. Arestas sem peso custam 1.",
            "longest": "Busca parcial: até 300 caminhos / 1,5 s. Não garante o ótimo se interrompida.",
            "all": "Até 300 caminhos / 1,5 s. Clique numa rota para destacá-la.",
            "bfs": "Explore por níveis. A tabela mostra visitas, arestas e fila.",
            "dfs": "Explore em profundidade. A pilha mostra o caminho da busca.",
            "mst": "Grafo não direcionado. O resultado destaca a floresta inteira.",
            "components": "Conectividade fraca. Selecione um grupo para isolá-lo visualmente.",
            "topological": "Exige grafo dirigido sem ciclos.",
        }
        self.note.setText(notes[name])

    def refresh_vertices(self, graph):
        origin, destination = self.origin.currentData(), self.destination.currentData()
        for combo in (self.origin, self.destination):
            combo.blockSignals(True)
            combo.clear()
        try:
            for key in sorted(graph.vertices):
                vertex = graph.vertices[key]
                label = f"{key} · {vertex.label}" if vertex.label else str(key)
                self.origin.addItem(label, key)
                self.destination.addItem(label, key)
            for combo, previous in ((self.origin, origin), (self.destination, destination)):
                index = combo.findData(previous)
                if index >= 0:
                    combo.setCurrentIndex(index)
                elif combo is self.destination and combo.count() > 1:
                    combo.setCurrentIndex(combo.count() - 1)
        finally:
            for combo in (self.origin, self.destination):
                combo.blockSignals(False)
        self.run.setEnabled(bool(graph.vertices))

    def set_playback(self, enabled):
        for widget in (self.play, self.previous, self.next, self.restart):
            widget.setEnabled(enabled)
