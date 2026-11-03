import csv
import io

from PyQt6.QtCore import QSettings, Qt
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableView,
    QVBoxLayout,
)

from grafla.domain import GraphError, generate_graph
from grafla.matrices import MatrixModel, from_matrix, to_matrix


def buttons(dialog, label="Aplicar"):
    box = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
    )
    box.button(QDialogButtonBox.StandardButton.Ok).setText(label)
    box.button(QDialogButtonBox.StandardButton.Ok).setProperty("primary", True)
    box.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
    box.accepted.connect(dialog.accept)
    box.rejected.connect(dialog.reject)
    return box


class GenerateDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gerar grafo")
        self.graph = None
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Um grafo reproduzível. A geração inteira pode ser desfeita."))
        form = QFormLayout()
        self.vertices = QSpinBox()
        self.vertices.setRange(1, 500)
        self.vertices.setValue(12)
        self.edges = QSpinBox()
        self.edges.setRange(0, 5000)
        self.edges.setValue(18)
        self.directed = QCheckBox("Arestas direcionadas")
        self.weighted = QCheckBox("Arestas ponderadas")
        self.minimum, self.maximum = QDoubleSpinBox(), QDoubleSpinBox()
        for spin in (self.minimum, self.maximum):
            spin.setRange(0, 1e6)
            spin.setDecimals(2)
            spin.setEnabled(False)
        self.minimum.setValue(1)
        self.maximum.setValue(10)
        self.weighted.toggled.connect(self.minimum.setEnabled)
        self.weighted.toggled.connect(self.maximum.setEnabled)
        self.seed = QSpinBox()
        self.seed.setRange(0, 2**31 - 1)
        self.seed.setValue(42)
        for label, widget in (
            ("Vértices", self.vertices),
            ("Arestas", self.edges),
            ("Tipo", self.directed),
            ("Pesos", self.weighted),
            ("Peso mínimo", self.minimum),
            ("Peso máximo", self.maximum),
            ("Seed", self.seed),
        ):
            form.addRow(label, widget)
        layout.addLayout(form)
        self.capacity = QLabel()
        self.capacity.setProperty("muted", True)
        layout.addWidget(self.capacity)
        self.vertices.valueChanged.connect(self.update_capacity)
        self.directed.toggled.connect(self.update_capacity)
        self.update_capacity()
        layout.addWidget(buttons(self, "Gerar e substituir"))

    def update_capacity(self):
        n = self.vertices.value()
        maximum = min(5000, n * (n - 1) // (1 if self.directed.isChecked() else 2))
        self.edges.setMaximum(maximum)
        self.capacity.setText(
            f"Até {maximum} arestas, sem laços ou duplicatas. O grafo atual será substituído."
        )
        self.capacity.setWordWrap(True)

    def accept(self):
        try:
            self.graph = generate_graph(
                self.vertices.value(),
                self.edges.value(),
                self.directed.isChecked(),
                self.weighted.isChecked(),
                self.minimum.value(),
                self.maximum.value(),
                self.seed.value(),
            )
        except GraphError as error:
            QMessageBox.warning(self, "Parâmetros inválidos", str(error))
            return
        super().accept()


class MatrixDialog(QDialog):
    def __init__(self, graph, importing=False, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Matriz → grafo" if importing else "Representação matricial")
        self.resize(640, 520)
        self.graph, self.importing, self.result_graph = graph, importing, None
        layout = QVBoxLayout(self)
        controls = QHBoxLayout()
        self.count = QSpinBox()
        self.count.setRange(1, 100)
        self.count.setValue(5)
        self.weighted = QCheckBox("Matriz de pesos")
        self.directed = QCheckBox("Direcionada")
        if importing:
            controls.addWidget(QLabel("Vértices"))
            controls.addWidget(self.count)
            controls.addWidget(self.directed)
        controls.addWidget(self.weighted)
        layout.addLayout(controls)
        note = QLabel(
            "Edite com duplo clique. Pesos: · significa ausência; 0 é uma aresta de custo zero.\n"
            "Conversão substitui o grafo e pode ser desfeita."
            if importing
            else "Cabeçalhos são IDs. Adjacência binária e pesos são representações diferentes.\n"
            "Matrizes não preservam estilo, posições ou o tipo de cada aresta de um grafo misto."
        )
        note.setWordWrap(True)
        note.setProperty("muted", True)
        layout.addWidget(note)
        self.table = QTableView()
        self.table.horizontalHeader().setDefaultSectionSize(64)
        self.table.verticalHeader().setDefaultSectionSize(32)
        layout.addWidget(self.table)
        self.count.valueChanged.connect(self.rebuild)
        self.weighted.toggled.connect(self.rebuild)
        self.directed.toggled.connect(self.rebuild)
        self.rebuild()
        copy = QPushButton("Copiar CSV")
        copy.clicked.connect(self.copy_csv)
        layout.addWidget(copy)
        if importing:
            layout.addWidget(buttons(self, "Criar grafo"))
        else:
            close = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
            close.rejected.connect(self.reject)
            layout.addWidget(close)

    def rebuild(self):
        if self.importing:
            n = self.count.value()
            values = [
                [None if self.weighted.isChecked() else 0 for _ in range(n)] for _ in range(n)
            ]
            ids = list(range(1, n + 1))
        else:
            ids, values = to_matrix(self.graph, self.weighted.isChecked())
        self.model = MatrixModel(
            values, ids, self.importing, self.directed.isChecked(), self.weighted.isChecked(), self
        )
        old = self.table.model()
        self.table.setModel(self.model)
        if old is not None:
            old.deleteLater()

    def copy_csv(self):
        stream = io.StringIO()
        writer = csv.writer(stream)
        writer.writerows(
            [["." if v is None else f"{v:g}" for v in row] for row in self.model.values]
        )
        QApplication.clipboard().setText(stream.getvalue())

    def accept(self):
        try:
            self.result_graph = from_matrix(
                self.model.values, self.directed.isChecked(), self.weighted.isChecked()
            )
        except GraphError as error:
            QMessageBox.warning(self, "Matriz inválida", str(error))
            return
        super().accept()


class PreferencesDialog(QDialog):
    def __init__(self, settings: QSettings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Preferências")
        self.settings = settings
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.theme = QComboBox()
        for label, key in (("Escuro", "dark"), ("Claro", "light"), ("Sistema", "system")):
            self.theme.addItem(label, key)
        self.theme.setCurrentIndex(max(0, self.theme.findData(settings.value("theme", "dark"))))
        self.grid = QCheckBox("Exibir grade")
        self.grid.setChecked(settings.value("grid", True, type=bool))
        self.snap = QCheckBox("Alinhar movimento à grade")
        self.snap.setChecked(settings.value("snap", False, type=bool))
        self.autosave = QCheckBox("Manter cópia de recuperação a cada minuto")
        self.autosave.setChecked(settings.value("autosave", True, type=bool))
        self.animations = QCheckBox("Animar a abertura")
        self.animations.setChecked(settings.value("animations", True, type=bool))
        for label, widget in (
            ("Aparência", self.theme),
            ("Canvas", self.grid),
            ("Snap", self.snap),
            ("Recuperação", self.autosave),
            ("Movimento", self.animations),
        ):
            form.addRow(label, widget)
        layout.addLayout(form)
        note = QLabel(
            "A física tem controle próprio na barra superior. Em repouso ela não consome ciclos.\n"
            "Documentos e recuperação ficam separados das preferências."
        )
        note.setWordWrap(True)
        note.setProperty("muted", True)
        layout.addWidget(note)
        layout.addWidget(buttons(self, "Salvar preferências"))

    def accept(self):
        for key, value in (
            ("theme", self.theme.currentData()),
            ("grid", self.grid.isChecked()),
            ("snap", self.snap.isChecked()),
            ("autosave", self.autosave.isChecked()),
            ("animations", self.animations.isChecked()),
        ):
            self.settings.setValue(key, value)
        self.settings.sync()
        super().accept()


class SearchDialog(QDialog):
    def __init__(self, actions, vertices, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Buscar comandos e vértices")
        self.resize(550, 430)
        self.chosen = None
        layout = QVBoxLayout(self)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Digite um comando, rótulo ou ID…")
        layout.addWidget(self.search)
        self.list = QListWidget()
        layout.addWidget(self.list)
        self.entries = [
            (f"Comando · {a.text().replace('&', '')}  {a.shortcut().toString()}", a)
            for a in actions
            if a.isEnabled()
        ]
        self.entries += [(f"Vértice #{v.id} · {v.label or v.id}", v.id) for v in vertices]
        self.search.textChanged.connect(self.filter)
        self.list.itemActivated.connect(self.choose)
        self.search.returnPressed.connect(self.choose_current)
        self.filter("")

    def filter(self, text):
        self.list.clear()
        for label, value in self.entries:
            if text.casefold() in label.casefold():
                item = QListWidgetItem(label)
                item.setData(Qt.ItemDataRole.UserRole, value)
                self.list.addItem(item)
        if self.list.count():
            self.list.setCurrentRow(0)

    def choose_current(self):
        if self.list.currentItem():
            self.choose(self.list.currentItem())

    def choose(self, item):
        self.chosen = item.data(Qt.ItemDataRole.UserRole)
        self.accept()
