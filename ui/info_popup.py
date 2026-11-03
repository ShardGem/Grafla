from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLabel, QLineEdit, QCheckBox,
    QDoubleSpinBox, QPushButton, QHBoxLayout
)
from PyQt6.QtCore import Qt


class InfoPopup(QWidget):
    def __init__(self, parent=None, titulo="Propriedades"):
        super().__init__(parent, Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setObjectName("infoPopup")

        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(6)

        # Widget container para o conteúdo (isso ajuda com o fundo)
        container = QWidget()
        container.setObjectName("container")
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(12, 12, 12, 12)

        # Título
        lbl_titulo = QLabel(f"<b>{titulo}</b>")
        lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(lbl_titulo)

        # Campos de formulário
        form = QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(4)

        # Rótulo (para caso queira exibir rótulo)
        self.input_rotulo = QLineEdit()
        self.label_rotulo = QLabel("Rótulo:")  # Guarda referência separa
        form.addRow(self.label_rotulo, self.input_rotulo)

        # Checkbox “Direcionado”
        self.chk_direcionado = QCheckBox("Direcionado")
        form.addRow(self.chk_direcionado)

        # Peso
        self.label_peso = QLabel("Peso:")
        self.spn_peso = QDoubleSpinBox()
        self.spn_peso.setRange(1, 1e6)
        self.spn_peso.setSingleStep(1)
        self.spn_peso.setDecimals(0)

        form.addRow(self.label_peso, self.spn_peso)

        container_layout.addLayout(form)

        # Botões na parte de baixo: Salvar | Remover
        botoes_layout = QHBoxLayout()
        botoes_layout.setSpacing(8)

        self.btn_salvar = QPushButton("Salvar")
        self.btn_salvar.setStyleSheet("""
            QPushButton {
                background-color: #2E8B57;
                color: white;
                border: none;
                padding: 4px 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #4CAF50;
            }
        """)
        botoes_layout.addWidget(self.btn_salvar)

        self.btn_remover = QPushButton("Remover")
        self.btn_remover.setStyleSheet("""
            QPushButton {
                background-color: #B22222;
                color: white;
                border: none;
                padding: 4px 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #C04040;
            }
        """)
        botoes_layout.addWidget(self.btn_remover)

        container_layout.addLayout(botoes_layout)

        main_layout.addWidget(container)

        # Estilo geral do popup
        self.setStyleSheet("""
            QWidget#infoPopup {
                background-color: transparent;
            }
            QWidget#container {
                background-color: rgba(30, 30, 30, 220);
                color: white;
                border: 1px solid #444;
                border-radius: 6px;
                padding: 8px;
            }
            QLineEdit, QDoubleSpinBox {
                background-color: white;
                color: black;
            }
            QCheckBox {
                spacing: 4px;
            }
        """)
        self.adjustSize()