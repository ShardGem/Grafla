from PyQt6.QtCore import QSettings, Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
)


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
        self.splash_duration = QDoubleSpinBox()
        self.splash_duration.setRange(0.5, 5.0)
        self.splash_duration.setDecimals(1)
        self.splash_duration.setSingleStep(0.2)
        self.splash_duration.setSuffix(" s")
        self.splash_duration.setValue(settings.value("splash_duration_ms", 1800, type=int) / 1000)
        for label, widget in (
            ("Aparência", self.theme),
            ("Canvas", self.grid),
            ("Snap", self.snap),
            ("Recuperação", self.autosave),
            ("Movimento", self.animations),
            ("Tempo mínimo da abertura", self.splash_duration),
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
            ("splash_duration_ms", round(self.splash_duration.value() * 1000)),
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
