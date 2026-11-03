from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QCheckBox,
    QLabel, QSpinBox, QPushButton, QWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPalette, QColor


class ArestaDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nova Aresta")
        self.setModal(True)
        self.setFixedSize(240, 160)  # Tamanho compacto

        # Aplicar tema escuro básico
        self.setStyleSheet("""
            QDialog {
                background-color: #2D2D2D;
                color: #FFFFFF;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLabel {
                color: #CCCCCC;
                font-size: 11px;
            }
            QCheckBox {
                color: #E0E0E0;
                font-size: 11px;
            }
            QSpinBox {
                background-color: #3A3A3A;
                color: #FFFFFF;
                border: 1px solid #5D5D60;
                border-radius: 3px;
                padding: 3px;
                min-width: 60px;
                font-size: 11px;
            }
            QPushButton {
                background-color: #3E3E42;
                color: #FFFFFF;
                border: 1px solid #5D5D60;
                border-radius: 3px;
                padding: 4px 10px;
                min-width: 70px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #4A4A4F;
            }
        """)

        self._build_ui()
        self._connect_signals()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Checkbox Direcionado
        self.cb_direcionado = QCheckBox("Direcionado?")
        layout.addWidget(self.cb_direcionado)

        # Checkbox Ponderado
        self.cb_ponderado = QCheckBox("Ponderado?")
        layout.addWidget(self.cb_ponderado)

        # Linha do peso
        peso_layout = QHBoxLayout()
        peso_layout.setContentsMargins(0, 0, 0, 0)
        peso_layout.setSpacing(8)

        lbl_peso = QLabel("Peso:")
        self.spin_peso = QSpinBox()
        self.spin_peso.setRange(1, 1000)
        self.spin_peso.setValue(1)
        self.spin_peso.setEnabled(False)

        peso_layout.addWidget(lbl_peso)
        peso_layout.addStretch()
        peso_layout.addWidget(self.spin_peso)

        layout.addLayout(peso_layout)

        # Espaçamento
        layout.addStretch(1)

        # Botões
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_cancel = QPushButton("Cancelar")
        self.btn_criar = QPushButton("Criar")

        # Garantir tamanho adequado
        self.btn_cancel.setMinimumWidth(75)
        self.btn_criar.setMinimumWidth(75)

        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_criar)

        layout.addLayout(btn_layout)

    def _connect_signals(self):
        self.cb_ponderado.toggled.connect(self.spin_peso.setEnabled)
        self.btn_criar.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)

    def get_values(self) -> tuple[bool, bool, int]:
        direc = self.cb_direcionado.isChecked()
        pond = self.cb_ponderado.isChecked()
        peso = self.spin_peso.value() if pond else 1
        return direc, pond, peso