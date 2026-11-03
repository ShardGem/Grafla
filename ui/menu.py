# menu_popup.py
from PyQt6.QtWidgets import QMenu, QWidget, QVBoxLayout, QPushButton, QFrame, QHBoxLayout, QLabel
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import QSize, Qt, QPoint, QTimer

from core.utilitarios.utilitarios import resource_path


class Menu(QMenu):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("""
                    QWidget#MenuContainer {
                        background-color: #232329;
                        border-radius: 10px;
                    }
                    QPushButton {
                        color: white;
                        font-size: 13px;
                        background-color: transparent;
                        border: none;
                        border-radius: 7px;
                        padding: 8px 8px;
                        text-align: left;
                    }
                    QPushButton:hover {
                        background-color: #2c2c3b;
                    }
                """)

        self.setFixedWidth(200)

        self.container = QWidget(self)
        self.container.setObjectName("MenuContainer")
        layout_externo = QVBoxLayout(self)
        layout_externo.setContentsMargins(0, 0, 0, 0)
        layout_externo.addWidget(self.container)

        self.layout = QVBoxLayout(self.container)
        self.layout.setContentsMargins(8, 8, 8, 8)
        self.layout.setSpacing(4)

        # Adiciona botões com ícones e texto
        self.botoes = []
        self.adicionar_item(resource_path("assets/Menu/Botoes/Icone-Teste.svg"), "Abrir", lambda: print("Abrir clicado"))
        self.adicionar_item(resource_path("assets/Menu/Botoes/Icone-Teste.svg"), "Salvar", lambda: print("Abrir clicado"))
        self.adicionar_item(resource_path("assets/Menu/Botoes/Icone-Exportar.svg"), "Salvar como...", lambda: print("Salvar clicado"))
        self.adicionar_item(resource_path("assets/Menu/Botoes/Icone-Imagem.svg"), "Exportar imagem...", lambda: print("Exportar clicado"))
        self.adicionar_item(resource_path("assets/Menu/Botoes/Icone-Ajuda.svg"), "Ajuda", lambda: print("Ajuda clicado"))
        self.adicionar_item(resource_path("assets/Menu/Botoes/Icone-Limpar.svg"), "Limpar o canvas", lambda: print("Limpar clicado"))
        self.adicionar_item(resource_path("assets/Menu/Botoes/Icone-Sair.svg"), "Sair", lambda: print("Limpar clicado"))

    def adicionar_item(self, icone_path, texto, acao):
        botao = QPushButton(texto)
        botao.setIcon(QIcon(icone_path))
        botao.setIconSize(QSize(16, 16))
        botao.clicked.connect(lambda: (acao(), self.close()))
        self.layout.addWidget(botao)
        self.botoes.append(botao)

    def mostrar_abaixo_do(self, widget_origem):
        margem_x = 0  # ajuste lateral, se quiser
        margem_y = 8  # distância vertical entre botão e menu

        global_pos = widget_origem.mapToGlobal(QPoint(margem_x, widget_origem.height() + margem_y))
        self.move(global_pos)
        self.show()

    def esconder(self):
        self.hide()
