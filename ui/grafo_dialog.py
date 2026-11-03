from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QSpinBox, QCheckBox, QFormLayout, QDialog, QDialogButtonBox, QPushButton, QHBoxLayout

from core.utilitarios.utilitarios import resource_path


class GerarGrafoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Parâmetros do Grafo")
        self.setWindowIcon(QIcon(resource_path('assets/icone-Grafla.png')))

        layout = QFormLayout(self)

        self.ponderado_checkbox = QCheckBox("Ponderado")
        self.direcionado_checkbox = QCheckBox("Direcionado")
        self.min_vertices_spin = QSpinBox()
        self.min_vertices_spin.setRange(1, 100)
        self.max_vertices_spin = QSpinBox()
        self.max_vertices_spin.setRange(1, 100)
        self.min_arestas_spin = QSpinBox()
        self.min_arestas_spin.setRange(0, 1000)
        self.max_arestas_spin = QSpinBox()
        self.max_arestas_spin.setRange(0, 1000)
        self.min_peso_spin = QSpinBox()
        self.min_peso_spin.setRange(1, 100)
        self.max_peso_spin = QSpinBox()
        self.max_peso_spin.setRange(1, 100)

        # Desabilitar campos de peso inicialmente
        self.min_peso_spin.setEnabled(False)
        self.max_peso_spin.setEnabled(False)
        self.ponderado_checkbox.toggled.connect(self.min_peso_spin.setEnabled)
        self.ponderado_checkbox.toggled.connect(self.max_peso_spin.setEnabled)

        # Conectar spinboxes para sincronizar limites
        self.min_vertices_spin.valueChanged.connect(
            lambda value: self.max_vertices_spin.setMinimum(value)
        )
        self.max_vertices_spin.valueChanged.connect(
            lambda value: self.min_vertices_spin.setMaximum(value)
        )

        self.min_arestas_spin.valueChanged.connect(
            lambda value: self.max_arestas_spin.setMinimum(value)
        )
        self.max_arestas_spin.valueChanged.connect(
            lambda value: self.min_arestas_spin.setMaximum(value)
        )

        self.min_peso_spin.valueChanged.connect(
            lambda value: self.max_peso_spin.setMinimum(value)
        )
        self.max_peso_spin.valueChanged.connect(
            lambda value: self.min_peso_spin.setMaximum(value)
        )

        layout.addRow("Grafo ponderado?", self.ponderado_checkbox)
        layout.addRow("Grafo direcionado?", self.direcionado_checkbox)
        layout.addRow("Vértices (min):", self.min_vertices_spin)
        layout.addRow("Vértices (max):", self.max_vertices_spin)
        layout.addRow("Arestas (min):", self.min_arestas_spin)
        layout.addRow("Arestas (max):", self.max_arestas_spin)
        layout.addRow("Peso (min):", self.min_peso_spin)
        layout.addRow("Peso (max):", self.max_peso_spin)

        buttons = QDialogButtonBox()

        btn_ok = QPushButton("Criar")
        btn_ok.setStyleSheet("""
                   QPushButton {
                       background-color: #4CAF50;
                       color: white;
                       border: none;
                       padding: 6px 14px;
                       border-radius: 6px;
                       font-weight: bold;
                   }
                   QPushButton:hover {
                       background-color: #45A049;
                   }
               """)

        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setStyleSheet("""
                   QPushButton {
                       background-color: #B22222;
                       color: white;
                       border: none;
                       padding: 6px 14px;
                       border-radius: 6px;
                       font-weight: bold;
                   }
                   QPushButton:hover {
                       background-color: #C04040;
                   }
               """)

        buttons.addButton(btn_ok, QDialogButtonBox.ButtonRole.AcceptRole)
        buttons.addButton(btn_cancel, QDialogButtonBox.ButtonRole.RejectRole)

        btn_ok.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(buttons)
        btn_layout.addStretch()

        layout.addRow(btn_layout)
