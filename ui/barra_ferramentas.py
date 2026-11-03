from PyQt6.QtWidgets import QToolBar, QToolButton, QWidget, QHBoxLayout
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon

from core.utilitarios.utilitarios import resource_path

# Listas de constantes de cada botão
BOTOES_COM_GATILHO = [
    (
        'Mão (Rolagem)',
        resource_path('assets/Mão/icone-Mao.png'),
        resource_path('assets/Mão/icone-Mao-Hover.png'),
        resource_path('assets/Mão/icone-Mao-Clique.png'),
        resource_path('assets/Mão/icone-Mao-Selecionado.png'),
        lambda f: f.alternar_modo_mao(),
        lambda f: f.modo_atual == 'mao'
    ),
    (
        'Adicionar Vértice',
        resource_path('assets/Vértice/icone-Vertice.png'),
        resource_path('assets/Vértice/icone-Vertice-Hover.png'),
        resource_path('assets/Vértice/icone-Vertice-Clique.png'),
        resource_path('assets/Vértice/icone-Vertice-Selecionado.png'),
        lambda f: f.alternar_adicionar_vertice(),
        lambda f: f.modo_atual == 'vertice'
    ),
    (
        'Adicionar Aresta',
        resource_path('assets/Aresta/icone-Aresta.png'),
        resource_path('assets/Aresta/icone-Aresta-Hover.png'),
        resource_path('assets/Aresta/icone-Aresta-Clique.png'),
        resource_path('assets/Aresta/icone-Aresta-Selecionado.png'),
        lambda f: f.alternar_adicionar_aresta(),
        lambda f: f.modo_atual == 'aresta'
    ),
    (
        'Apagar Objetos',
        resource_path('assets/Borracha/icone-Borracha.png'),
        resource_path('assets/Borracha/icone-Borracha-Hover.png'),
        resource_path('assets/Borracha/icone-Borracha-Clique.png'),
        resource_path('assets/Borracha/icone-Borracha-Selecionado.png'),
        lambda f: f.alternar_modo_borracha(),
        lambda f: f.modo_atual == 'borracha'
    ),
]

BOTOES_SEM_GATILHO = [
    (
        'Gerar Grafo',
        resource_path('assets/NovoGrafo/Icone-NovoGrafo.png'),
        resource_path('assets/NovoGrafo/Icone-NovoGrafo-Hover.png'),
        resource_path('assets/NovoGrafo/Icone-NovoGrafo-Clique.png'),
        lambda f: f.abrir_dialogo_gerar_grafo
    ),
    (
        'Grafo para Matriz',
        resource_path('assets/GrafoParaMatriz/Icone-GrafoMatriz.png'),
        resource_path('assets/GrafoParaMatriz/Icone-GrafoMatriz-Hover.png'),
        resource_path('assets/GrafoParaMatriz/Icone-GrafoMatriz-Clique.png'),
        lambda f: f.grafo_para_matriz
    ),
    (
        'Matriz para Grafo',
        resource_path('assets/MatrizParaGrafo/Icone-MatrizGrafo.png'),
        resource_path('assets/MatrizParaGrafo/Icone-MatrizGrafo-Hover.png'),
        resource_path('assets/MatrizParaGrafo/Icone-MatrizGrafo-Clique.png'),
        lambda f: f.matriz_para_grafo
    ),
    (
        'Limpar Tela',
        resource_path('assets/Limpar/Icone-Limpar.png'),
        resource_path('assets/Limpar/Icone-Limpar-Hover.png'),
        resource_path('assets/Limpar/Icone-Limpar-Clique.png'),
        lambda f: f.resetar_grafo
    )
]

""" -------------------------------------
          BARRA DE FERRAMENTAS
------------------------------------- """
def criar_barra_de_ferramentas(
    controlador,
    janela,  # <--- agora a MainWindow é passada aqui
    handle_btn_enter,
    handle_btn_leave,
    handle_btn_press,
    handle_btn_release,
    atualizar_botoes_modo
):
    main_toolbar = QToolBar()
    main_toolbar.setIconSize(QSize(60, 60))
    main_toolbar.setMovable(False)
    main_toolbar.setStyleSheet("""
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

    botoes_gatilho = []

    # Conectar o sinal de modo atualizado
    controlador.modo_atualizado.connect(atualizar_botoes_modo)

    for acao in BOTOES_COM_GATILHO:
        nome, ico_normal, ico_hover, ico_clique, ico_selecionado, funcao, verif_estado = acao
        btn = QToolButton()
        btn.setIcon(QIcon(ico_normal))
        btn.setIconSize(QSize(60, 60))
        btn.setCheckable(True)
        btn.setToolTip(nome)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet("QToolButton { background: transparent; border: none; }")
        btn.setAutoRaise(True)

        # Armazena os ícones como atributos do botão
        btn._normal_icon = ico_normal
        btn._hover_icon = ico_hover
        btn._press_icon = ico_clique
        btn._selected_icon = ico_selecionado
        btn._funcao = lambda f=controlador: funcao(f)

        # Conecta os eventos usando métodos da classe
        btn.enterEvent = lambda event, b=btn: handle_btn_enter(b)
        btn.leaveEvent = lambda event, b=btn: handle_btn_leave(b)
        btn.pressed.connect(lambda b=btn: handle_btn_press(b))
        btn.released.connect(lambda b=btn: handle_btn_release(b))
        callback = janela.criar_callback_gatilho(btn, acao)
        btn.clicked.connect(callback)

        main_toolbar.addWidget(btn)
        botoes_gatilho.append(btn)

    # Lista de ações sem estado de toggle


    for acao in BOTOES_SEM_GATILHO:
        nome, ico_normal, ico_hover, ico_clique, funcao = acao
        btn = QToolButton()
        btn.setIcon(QIcon(ico_normal))
        btn.setIconSize(QSize(60, 60))
        btn.setToolTip(nome)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet("QToolButton { background: transparent; border: none; }")
        btn.setAutoRaise(True)


        # Eventos visuais com ícones fixados na closure
        def make_enter_event(button, icon_path):
            return lambda event: button.setIcon(QIcon(icon_path))

        def make_leave_event(button, icon_path):
            return lambda event: button.setIcon(QIcon(icon_path))

        def make_press_event(button, icon_path):
            return lambda: button.setIcon(QIcon(icon_path))

        def make_release_event(button, icon_path):
            return lambda: button.setIcon(QIcon(icon_path))

        # Conecta eventos corretamente com ícones individuais
        btn.enterEvent = make_enter_event(btn, ico_hover)
        btn.leaveEvent = make_leave_event(btn, ico_normal)
        btn.pressed.connect(make_press_event(btn, ico_clique))
        btn.released.connect(make_release_event(btn, ico_hover))
        btn.clicked.connect(funcao(controlador))

        main_toolbar.addWidget(btn)

    # Container para a barra de ferramentas
    toolbar_container = QWidget(controlador)
    toolbar_container.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
    toolbar_container.setFixedHeight(60)
    toolbar_container.setFixedWidth(1000)

    layout_toolbar = QHBoxLayout(toolbar_container)
    layout_toolbar.setContentsMargins(0, 0, 0, 0)
    layout_toolbar.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
    layout_toolbar.addWidget(main_toolbar)

    main_toolbar.layout().setSpacing(6)  # Separação entre cada botão

    return toolbar_container, botoes_gatilho