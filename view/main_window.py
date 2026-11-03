from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QPushButton, QHBoxLayout, QVBoxLayout,
    QLabel, QLineEdit, QCheckBox, QSpinBox, QTableWidget, QTableWidgetItem,
    QScrollArea, QMessageBox, QToolBar, QToolButton, QSizePolicy,
    QFrame, QDialog, QHeaderView, QDockWidget
)
from PyQt6.QtGui import (
    QPainter, QPen, QColor, QPalette, QIcon, QPixmap,
    QRegion, QPainterPath,
)
from PyQt6.QtCore import (
    Qt, QPoint, QSize, QEvent, QRect, QPointF, QObject, QTimer
)

from core.controlador import GrafoControlador
from core.modelos.grafo_modelo import Grafo
from core.utilitarios.algoritmos.algoritmos import PainelAlgoritmos
from core.utilitarios.utilitarios import resource_path
from ui.menu import Menu
from ui.zoom import ZoomControls
from ui.barra_ferramentas import criar_barra_de_ferramentas, BOTOES_COM_GATILHO

class CustomTitleBar(QWidget):
    def __init__(self, parent):
        super().__init__(parent)

        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#1c1c1c"))
        self.setPalette(palette)
        self.setAutoFillBackground(True)

        self.setFixedHeight(38)

        self.pos_inicial = None

        titlebar_layout = QHBoxLayout(self)
        titlebar_layout.setContentsMargins(0, 0, 0, 10)
        titlebar_layout.setSpacing(0)

        # Ícone
        icone_label = QLabel()
        pixmap = QPixmap(resource_path('assets/Icone-Grafla.png'))
        icone_label.setPixmap(pixmap)
        icone_label.setScaledContents(True)
        icone_label.setFixedSize(24, 24)
        icon_layout = QVBoxLayout()
        icon_layout.setContentsMargins(7, 7, 10, 0)
        icon_layout.addWidget(icone_label)
        titlebar_layout.addLayout(icon_layout)

        # Título
        self.title = QLabel(parent.windowTitle(), self)
        self.title.setStyleSheet("""
            color: white; 
            font-family: "Assistant", sans-serif;
            font-size: 16px; 
            font-weight: 400;
        """)
        self.title.setFixedHeight(38)

        self.title.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        titlebar_layout.addWidget(self.title)

        titlebar_layout.addStretch()

        self.btn_style = ("""
            QWidget#TitleBar {
                background-color: #1e1e2f;
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
            }
            
            QToolButton {
                background-color: transparent;
                padding: 6px;
                border-radius: none;
            }

            QToolButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }

            QToolButton#BotaoFechar:hover {
                background-color: rgba(255, 0, 0, 0.75);
            }
        """)

        def criar_botao(imagem, tooltip):
            botao = QToolButton(self)
            botao.setIcon(QIcon(imagem))
            botao.setIconSize(QSize(10, 10))
            botao.setToolTip(tooltip)
            botao.setStyleSheet(self.btn_style)
            botao.setFixedSize(QSize(46, 40))
            botao.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            return botao

        self.botao_minimizar = criar_botao(resource_path('assets/TitleBar/minimize-icon.png'), 'Minimizar')
        self.botao_minimizar.clicked.connect(self.window().showMinimized)

        self.botao_maximizar = criar_botao(resource_path('assets/TitleBar/maximize-icon.png'), 'Maximizar')
        self.botao_maximizar.clicked.connect(self.toggle_max_restore)

        self.botao_restaurar = criar_botao(resource_path('assets/TitleBar/maximize-size-icon.png'), 'Restaurar')
        self.botao_restaurar.clicked.connect(self.toggle_max_restore)
        self.botao_restaurar.setVisible(False)

        self.botao_fechar = criar_botao(resource_path('assets/TitleBar/close-icon.png'), 'Fechar')
        self.botao_fechar.clicked.connect(self.window().close)
        self.botao_fechar.setObjectName('BotaoFechar')

        for btn in [self.botao_minimizar, self.botao_maximizar, self.botao_restaurar, self.botao_fechar]:
            titlebar_layout.addWidget(btn)

    def toggle_max_restore(self):
        win = self.window()
        if win.isMaximized():
            win.showNormal()
            self.botao_maximizar.setVisible(True)
            self.botao_restaurar.setVisible(False)
        else:
            win.showMaximized()
            self.botao_maximizar.setVisible(False)
            self.botao_restaurar.setVisible(True)

    def window_state_changed(self, state):
        self.botao_restaurar.setVisible(state == Qt.WindowState.WindowMaximized)
        self.botao_maximizar.setVisible(state != Qt.WindowState.WindowMaximized)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle_max_restore()

class HoverEventFilter(QObject):
    def __init__(self, btn, icon_hover, icon_normal):
        super().__init__()
        self.btn = btn
        self.icon_hover = icon_hover
        self.icon_normal = icon_normal

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Enter:
            self.btn.setIcon(QIcon(self.icon_hover))
        elif event.type() == QEvent.Type.Leave:
            self.btn.setIcon(QIcon(self.icon_normal))
        return False  # continua propagando o evento

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Grafla')
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)  # Remover as bordas da janela
        self.resize(1280, 720)

        self.grafo = Grafo()

        self.menu_popup = Menu(self)
        self.grafo_controlador = GrafoControlador(self)

        # Declare aqui, antes de usar:
        self.menu_toolbar_container = None
        self.menu_personalizado = None
        self.menu_button = None
        self.menu_toolbar = None
        self.zoom_controls = None
        self.modo_atual = 'nenhum'

        self.menu_aberto = False
        self.toggle_travado = False
        self.configurar_menu()

        self.algo_panel = PainelAlgoritmos(self.grafo_controlador)
        dock = QDockWidget("Algoritmos / Caminhos", self)
        dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea)
        dock.setWidget(self.algo_panel)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)

        container = QWidget(self)
        self.setCentralWidget(container)

        self.layout_principal = QVBoxLayout(container)
        self.layout_principal.setContentsMargins(0, 0, 0, 0)
        self.layout_principal.setSpacing(0)

        self.title_bar = CustomTitleBar(self)
        self.title_bar.window_state_changed(self.windowState())
        self.layout_principal.addWidget(self.title_bar)

        self.layout_principal.addWidget(self.grafo_controlador)

        # Conectar o sinal de modo atualizado
        self.grafo_controlador.modo_atualizado.connect(self.atualizar_botoes_modo)

        self.toolbar_container, self.botoes_gatilho = criar_barra_de_ferramentas(
            self.grafo_controlador,
            self,
            self.handle_btn_enter,
            self.handle_btn_leave,
            self.handle_btn_press,
            self.handle_btn_release,
            self.atualizar_botoes_modo
        )

    # ====== BOTÃO DE MENU ======
    def configurar_menu(self):
        icone_normal = QIcon(resource_path('assets/Menu/Icone-Menu.png'))
        icone_hover = QIcon(resource_path('assets/Menu/Icone-Menu-Hover.png'))
        icone_clique = QIcon(resource_path('assets/Menu/Icone-Menu-Clique.png'))

        self.menu_button = QToolButton()
        self.menu_button.setIcon(icone_normal)
        self.menu_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.menu_button.setStyleSheet("QToolButton { background: transparent; border: none; }")
        self.menu_button.setIconSize(QSize(60, 60))
        self.menu_button.setAutoRaise(True)

        self.menu_button.clicked.connect(self.toggle_menu)

        # Ícones dinâmicos
        self.menu_button.pressed.connect(lambda: self.menu_button.setIcon(icone_clique))
        self.menu_button.released.connect(lambda: self.menu_button.setIcon(icone_normal))
        self.menu_button.enterEvent = lambda e: self.menu_button.setIcon(icone_hover)
        self.menu_button.leaveEvent = lambda e: self.menu_button.setIcon(icone_normal)

        self.menu_toolbar = QToolBar()
        self.menu_toolbar.setMovable(False)
        self.menu_toolbar.addWidget(self.menu_button)
        self.menu_toolbar.setStyleSheet("""
        QToolBar { 
            background: transparent; 
            border: none;
            outline: none; 
        }
        QToolButton { 
            padding: 0px;
            border: none;
        }
        QToolButton:pressed {
            padding: 0px;
        }
    """)

        self.menu_toolbar.setIconSize(QSize(60, 60))

        self.menu_toolbar_container = QWidget(self.grafo_controlador)
        layout = QHBoxLayout(self.menu_toolbar_container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.menu_toolbar)
        self.menu_toolbar_container.setFixedHeight(60)
        self.menu_toolbar_container.raise_()

    def toggle_menu(self):
        if self.toggle_travado:
            print("Toggle travado, ignorando clique")
            return
        self.toggle_travado = True
        QTimer.singleShot(200, self.destravar_toggle)  # trava por 200ms para evitar cliques múltiplos

        if self.menu_aberto:
            print("Fechando menu")
            self.menu_popup.hide()
            self.menu_aberto = False
        else:
            print("Abrindo menu")

            self.menu_popup.mostrar_abaixo_do(self.menu_button)
            self.menu_aberto = True

    def destravar_toggle(self):
        self.toggle_travado = False

    def centralizar_barra_ferramentas(self):
        if hasattr(self, 'toolbar_container'):
            centro_x = (self.width() - self.toolbar_container.width()) // 2
            self.toolbar_container.move(centro_x, 10)

        # Outros controles
        if self.zoom_controls is None:
            self.zoom_controls = ZoomControls(self.grafo_controlador)

        self.on_resize()

        # Conectar evento de redimensionamento
        self.grafo_controlador.resizeEvent = lambda event: self.on_resize()
        self.aplicar_cantos_arredondados()

        # Atualizar botões inicialmente
        self.atualizar_botoes_modo()

        self.grafo_controlador.modo_atualizado.connect(self.atualizar_botoes_modo)

    # ===== MÉTODOS DA MAINWINDOW PARA MANIPULAR BOTÕES =====
    def handle_btn_enter(self, btn):
        """Manipula evento de mouse entrando no botão"""
        if btn.isChecked():
            btn.setIcon(QIcon(btn._selected_icon))
        else:
            btn.setIcon(QIcon(btn._hover_icon))

    def handle_btn_leave(self, btn):
        """Manipula evento de mouse saindo do botão"""
        if btn.isChecked():
            btn.setIcon(QIcon(btn._selected_icon))
        else:
            btn.setIcon(QIcon(btn._normal_icon))

    def handle_btn_press(self, btn):
        """Manipula evento de pressionar botão"""
        btn.setIcon(QIcon(btn._press_icon))

    def handle_btn_release(self, btn):
        """Manipula evento de soltar botão"""
        if btn.isChecked():
            btn.setIcon(QIcon(btn._selected_icon))
        else:
            btn.setIcon(QIcon(btn._hover_icon))

    def handle_btn_click(self, btn):
        """Manipula clique no botão"""
        # Chama a função callback associada ao botão
        btn._funcao()

    def atualizar_botoes_modo(self):
        for btn, acao in zip(self.botoes_gatilho, BOTOES_COM_GATILHO):
            _, _, _, _, _, _, verif_estado = acao
            esta_ativo = verif_estado(self.grafo_controlador)

            btn.setChecked(esta_ativo)
            if esta_ativo:
                btn.setIcon(QIcon(btn._selected_icon))
            else:
                btn.setIcon(QIcon(btn._normal_icon))

    def criar_callback_gatilho(self, botao, acao):
        nome, _, _, _, _, funcao, _ = acao

        def callback():
            self.desmarcar_outros_botoes(botao)
            funcao(self.grafo_controlador)
            self.grafo_controlador.modo_atualizado.emit()  # Atualiza ícones e estados

        return callback

    def desmarcar_outros_botoes(self, botao_clicado):
        for botao in self.botoes_gatilho:
            if botao != botao_clicado:
                botao.setChecked(False)
                botao.setIcon(QIcon(botao._normal_icon))

    def aplicar_cantos_arredondados(self, raio=8):
        retangulo = QRect(0, 0, self.width(), self.height())
        regiao = QRegion(retangulo, QRegion.RegionType.Rectangle)
        mascara = QRegion(self.rect(), QRegion.RegionType.Rectangle)

        # Região com cantos arredondados
        mascara = QRegion(self.rect(), QRegion.RegionType.Ellipse).intersected(regiao)

        path = QRegion(0, 0, self.width(), self.height(), QRegion.RegionType.Rectangle)
        rounded = QRegion(self.rect(), QRegion.RegionType.Rectangle)
        rounded = QRegion(QRect(0, 0, self.width(), self.height()), QRegion.RegionType.Rectangle)

        if self.isMaximized():
            self.setMask(QRegion())  # Remove a máscara se maximizada
        else:
            path = QPainterPath()
            path.addRoundedRect(0, 0, self.width(), self.height(), raio, raio)
            region = QRegion(path.toFillPolygon().toPolygon())
            self.setMask(region)

    def changeEvent(self, event):
        if event.type() == QEvent.Type.WindowStateChange:
            self.title_bar.window_state_changed(self.windowState())
            print("Janela mudou de estado:", self.windowState())
        super().changeEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.title_bar.pos_inicial = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.window().isMaximized():
            return

        if self.title_bar.pos_inicial is not None:
            delta = event.position().toPoint() - self.title_bar.pos_inicial
            self.move(self.x() + delta.x(), self.y() + delta.y())
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.title_bar.pos_inicial = None
        super().mouseReleaseEvent(event)

    def resizeEvent(self, event):
        if not self.isMaximized():
            self._normal_geometry = self.geometry()

        self.aplicar_cantos_arredondados()
        self.centralizar_barra_ferramentas()
        super().resizeEvent(event)

    def on_resize(self):
        margem_x = 20
        margem_y = 30


        # Posiciona a barra de menu no canto superior esquerdo.
        self.menu_toolbar_container.move(10, 10)

    def comecar_aresta(self):
        if self.grafo_controlador.vertice_selecionado:
            self.grafo_controlador.comeco_aresta = self.grafo_controlador.vertice_selecionado

    def converter_dict_para_matriz(self, adj_dict):
        vertices = sorted(adj_dict.keys())
        n = len(vertices)
        index_map = {v: i for i, v in enumerate(vertices)}
        matriz = [[0]*n for _ in range(n)]

        for origem in adj_dict:
            for destino in adj_dict[origem]:
                i = index_map[origem]
                j = index_map[destino]
                matriz[i][j] = 1
        return matriz