from PyQt6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QInputDialog, QMenu, QFrame, QMessageBox, QPushButton, \
    QLabel, QHBoxLayout, QDialog, QVBoxLayout, QSpinBox, QCheckBox, QTableWidget, QHeaderView, QScrollArea, QSizePolicy, \
    QTableWidgetItem
)
from PyQt6.QtGui import QColor, QPainter, QPen, QMouseEvent, QIcon
from PyQt6.QtCore import QRectF, QTimer, Qt, pyqtSignal, QEvent, QPointF
import random

from core.modelos import GrafoAresta
from core.utilitarios import *
from core.modelos.grafo_modelo import Grafo
from core.modelos import GrafoVertice
from core.utilitarios.utilitarios import resource_path
from ui.matriz_dialog import MatrizDialog
from ui.aresta_dialog import ArestaDialog
from ui.grafo_dialog import GerarGrafoDialog

"""
CONTROLE DO GRAFO

Essa classe herda de QGraphicsView e integra a cena (QGraphicsScene) onde os vértices e as arestas são adicionados. Ela gerencia:
- Criação dos vértices e arestas com funções.
- Física.
- Eventos do mouse para permitir seleção e movimento dos vértices.
- Atualização da cena, garantido que os vértices e arestas sejam reposicionados e atualizados em uma taxa constante de tempo.
"""
class GrafoControlador(QGraphicsView):
    grafo_atualizado = pyqtSignal() # Sinal que avisa a view que o grafo foi alterado, serve pra re-gerar a tabela de adjacencia
    modo_atualizado = pyqtSignal()
    escala_alterada = pyqtSignal(float) # Sinal que avisa que a escala da tela foi alterada, sincronizando o texto do botão com a escala atual.

    # Constantes da cena
    CENA_LARGURA = 1920
    CENA_ALTURA = 1080
    FPS_DELAY = 10 # (~100fps)
    FADE_ALPHA = 0.15

    # Cores e estilização
    COR_PADRAO = QColor(170, 170, 170)
    COR_SELECIONADO = QColor(138, 92, 236)
    COR_DESSATURADO = QColor(35, 35, 35)

    # Propriedades da grade de fundo
    GRADE_TAMANHO = 40
    GRADE_COR = QColor(60, 60, 60)

    def __init__(self, parent=None):
        super().__init__(parent)

        # ==================== INICIALIZAÇÃO DA CENA ====================
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setSceneRect(QRectF(0, 0, self.CENA_LARGURA, self.CENA_ALTURA)) # Tamanho da tela dos grafos

        self.setBackgroundBrush(QColor("#121212"))  # Cor de fundo
        self.setRenderHint(QPainter.RenderHint.Antialiasing) # Suavização de cantos
        self.setRenderHint(QPainter.RenderHint.TextAntialiasing) # Suavização do texto
        self.setStyleSheet("border: none;")  # Remover a borda branca

        # Desabilitar o scroll da janela
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse) # Deixa o Zoom-in e out "fixado" na posição do mouse
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.scene.setItemIndexMethod(QGraphicsScene.ItemIndexMethod.NoIndex)

        # Centraliza a cena
        self.centerOn(self.CENA_LARGURA / 2, self.CENA_ALTURA / 2)

        # Modelo do grafo
        self.grafo = Grafo()

        # ==================== ESTADOS DE INTERAÇÃO ====================
        self.modo_atual = 'nenhum' # 'mao', 'vertice', 'aresta', 'borracha'
        
        self.ultimo_vertice_clicado = None
        self.proximo_vertice_id = 1

        self.vertice_selecionado = None
        self.comeco_aresta = None
        self.vertice_hover = None

        self.modo_destaque = False # Quando True, ignora hover e física na cor

        # Timer de update
        self.timer = QTimer()
        self.timer.timeout.connect(self.atualizar_grafo) # Atualiza o grafo quando o timer acaba (a cada 10ms)
        self.timer.start(self.FPS_DELAY) # Inicia o timer com 10ms, resetando toda a vez que acaba
        self.setMouseTracking(True)

    """ -------------------------------------
                  DESENHO DA GRADE
       ------------------------------------- """
    def drawBackground(self, painter: QPainter, rect: QRectF):
        super().drawBackground(painter, rect)

        left = int(rect.left()) - (int(rect.left()) % self.GRADE_TAMANHO)
        top = int(rect.top()) - (int(rect.top()) % self.GRADE_TAMANHO)
        right = int(rect.right())
        bottom = int(rect.bottom())

        painter.setPen(QPen(self.GRADE_COR, 1))
        painter.setOpacity(0.7)  # Transparência da grade

        x = left
        while x < right:
            painter.drawLine(x, top, x, bottom)
            x += self.GRADE_TAMANHO
        y = top
        while y < bottom:
            painter.drawLine(left, y, right, y)
            y += self.GRADE_TAMANHO

    """ -------------------------------------
                      ZOOM
    ------------------------------------- """
    def wheelEvent(self, event):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            escala_atual = round(self.transform().m11(), 2)
            if event.angleDelta().y() > 0:
                nova_escala = escala_atual + 0.2
            else:
                nova_escala = escala_atual - 0.2
            nova_escala = max(0.5, min(3.0, nova_escala))
            fator = nova_escala / escala_atual
            self.scale(fator, fator)
        else:
            super().wheelEvent(event)

        self.escala_alterada.emit(self.transform().m11())

        rect = self.scene.sceneRect()
        print(f"Tamanho atual da cena: {rect.width()} x {rect.height()}")
        print(f"Posição: ({rect.x()}, {rect.y()})")

        viewport_tam = self.viewport().size()
        print(f"Tamanho do viewport: {viewport_tam.width()} x {viewport_tam.height()}")

        if self.modo_atual == 'mao':
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

    """ -------------------------------------
               MÉTODOS AUXILIARES
    ------------------------------------- """
    def handle_adicionar_vertice(self, x=None, y=None):
        try:
            if x is None or y is None:
                if not self.modo_atual == 'vertice':
                    return None
                centro_viewport = self.viewport().rect().center()
                scene_pt = self.mapToScene(centro_viewport)
                x, y = scene_pt.x(), scene_pt.y()

            # Verificação de proximidade
            raio_tolerancia = 20
            area = QRectF(x - raio_tolerancia, y - raio_tolerancia, raio_tolerancia * 2, raio_tolerancia * 2)

            itens_proximos = [item for item in self.scene.items(area) if isinstance(item, GrafoVertice)]

            if itens_proximos:
                print("Já existe um vértice próximo — impedindo criação.")
                # return None # Ta causando muito problema

            # Criação do vértice
            novo_vertice = self.grafo.adicionar_vertice(
                self.proximo_vertice_id,
                self.COR_PADRAO,
                x, y
            )
            self.proximo_vertice_id += 1
            self.scene.addItem(novo_vertice)
            self.grafo_atualizado.emit()
            return novo_vertice

        except Exception as e:
            print("Erro ao adicionar vértice:", e)
            return None

    def handle_adicionar_aresta(self, vertice1, vertice2,
                                cor,
                                ponderado=False,
                                direcionado=True,
                                peso=1):
        """
        Chama o metodo do modelo Grafo.adicionar_aresta() passando
        ponderado, direcionado e peso. Em seguida, adiciona a aresta na cena.
        """
        aresta = self.grafo.adicionar_aresta(
            vertice1=vertice1,
            vertice2=vertice2,
            cor=cor,
            ponderado=ponderado,
            direcionado=direcionado,
            peso=peso,
        )

        if aresta:
            self.scene.addItem(aresta)
            self.grafo_atualizado.emit()

    def handle_remover_vertice(self, vertice):
        # Remove todas as arestas conectadas
        for aresta in self.grafo.arestas[:]:
            if vertice.vertice_id in aresta.get_vertices():
                self.scene.removeItem(aresta)
                self.grafo.arestas.remove(aresta)

        # Limpa referências se este vértice estava selecionado
        if self.ultimo_vertice_clicado == vertice:
            self.ultimo_vertice_clicado = None

        # Remove o vértice
        self.grafo.remover_vertice(vertice)
        self.scene.removeItem(vertice)
        self.grafo_atualizado.emit()
        self.scene.update()

    def handle_remover_arestas(self, vertice):
        aresta = self.grafo.remover_arestas(vertice)
        self.scene.removeItem(aresta)
        self.grafo_atualizado.emit()

    """ -------------------------------------
                MODOS DE INTERAÇÃO
    ------------------------------------- """

    def alternar_modo(self, modo: str):
        """
        Muda o modo de interação:
        - 'mao': Arrastar a cena
        - 'vertice': Criar vértices
        - 'aresta': Criar arestas
        - 'borracha': Apagar objetos
        - Qualquer outro: voltar para seleção normal
        """
        # Se clicou no modo já ativo, desativa
        if self.modo_atual == modo:
            novo_modo = 'nenhum'
        else:
            novo_modo = modo

        self.modo_atual = novo_modo

        # Resetar contorno do último vértice clicado
        if self.ultimo_vertice_clicado:
            self.ultimo_vertice_clicado.resetar_contorno()
            self.ultimo_vertice_clicado = None

        # 💡 Também pode haver um vértice "selecionado" que precisa ser resetado
        if self.vertice_selecionado:
            self.vertice_selecionado.resetar_contorno()
            self.vertice_selecionado = None

        # Ajusta cursor e dragMode baseado no modo atual
        if self.modo_atual == 'mao':
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        else:
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            self.setCursor(Qt.CursorShape.ArrowCursor)

        if self.modo_atual == 'borracha':
            self.setCursor(Qt.CursorShape.ForbiddenCursor)  # ou um QCursor com ícone customizado
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)

        # Notifica que o modo mudou
        self.modo_atualizado.emit()

        print(f'Modo Atual: {self.modo_atual}')
        print(f"DragMode: {self.dragMode()}")
        print(f"Cursor: {self.cursor().shape()}")

    def alternar_modo_mao(self):
        self.alternar_modo('mao')

    def alternar_adicionar_vertice(self):
        self.alternar_modo('vertice')

    def alternar_adicionar_aresta(self):
        self.alternar_modo('aresta')

    def alternar_modo_borracha(self):
        self.alternar_modo('borracha')

    """ -------------------------------------
                  MONTAR MATRIZ
    ------------------------------------- """
    def montar_matriz(self):
        num_vertices, ok = QInputDialog.getInt(self, "Quantidade de Vértices", "Quantos vértices deseja criar?", min=1,
                                               max=100)
        if not ok:
            return

        dialogo = MatrizDialog(num_vertices, self)
        if dialogo.exec():
            resultado = dialogo.obter_matriz_completa()
            matriz = resultado['matriz']
            direcionado = resultado['direcionado']
            ponderado = resultado['ponderado']

            self.resetar_grafo()

            # Adiciona os vértices
            for _ in range(num_vertices):
                self.handle_adicionar_vertice()

            # Arestas a partir da matriz
            for i in range(num_vertices):
                for j in range(num_vertices):
                    peso = matriz[i][j]
                    if peso > 0:
                        v1 = self.grafo.vertices[i]
                        v2 = self.grafo.vertices[j]

                        # Se grafo não direcionado, só cria (i,j) se i < j
                        if not direcionado and j < i:
                            continue

                        self.handle_adicionar_aresta(
                            v1, v2,
                            cor=self.COR_PADRAO,
                            ponderado=ponderado,
                            direcionado=direcionado,
                            peso=(peso if ponderado else 1)
                        )

            self.grafo_atualizado.emit()

    """ -------------------------------------
               LIMPAR GRAFO ATUAL
    ------------------------------------- """
    def resetar_grafo(self):
        if self.proximo_vertice_id != 1:
            dlg = QDialog(self)
            dlg.setWindowTitle("Confirmar Limpeza")

            dlg.setWindowIcon(QIcon(resource_path('assets/Icone-Grafla.png')))  # Se quiser manter o ícone padrão da aplicação

            vlay = QVBoxLayout(dlg)
            lbl = QLabel("Tem certeza que deseja limpar o grafo atual?")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            vlay.setContentsMargins(20, 20, 20, 20)
            vlay.setSpacing(15)
            lbl.setWordWrap(True)
            vlay.addWidget(lbl)

            btns = QHBoxLayout()
            btn_cancel = QPushButton("Cancelar")
            btn_cancel.setStyleSheet("""
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

            btn_ok = QPushButton("Limpar Grafo")
            btn_ok.setStyleSheet("""
                QPushButton {
                    background-color: rgba(20, 20, 20, 240);
                    color: white;
                    border: none;
                    padding: 4px 12px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #4CAF50;
                }
            """)

            btns.addWidget(btn_cancel)
            btns.addWidget(btn_ok)
            vlay.addLayout(btns)

            btn_cancel.clicked.connect(dlg.reject)
            btn_ok.clicked.connect(dlg.accept)

            if dlg.exec():
                for vertice in list(self.grafo.vertices.values()):
                    self.scene.removeItem(vertice) # Remove cada vértice da tela.
                for aresta in self.grafo.arestas:
                    self.scene.removeItem(aresta) # Remove cada aresta da tela.
                self.grafo.vertices.clear() # Apaga todos os valores do dicionário de vértices.
                self.grafo.arestas.clear() # Apaga todos os valores da lista de arestas.
                self.proximo_vertice_id = 1 # Reseta o índice atual dos vértices.
                self.grafo_atualizado.emit()
        else:
            print('Sem grafo para limpar!')

    def resetar_escala(self):
        self.resetTransform()
        self.centerOn(self.CENA_LARGURA / 2, self.CENA_ALTURA / 2)
        self.escala_alterada.emit(self.transform().m11())

    """ -------------------------------------
                ATUALIZAR GRAFO
    ------------------------------------- """
    def atualizar_grafo(self):
        # aplicar_fisica(self) # Inicia a física do grafo
        self.atualizar_cores()

        for aresta in self.grafo.arestas:
            aresta.atualizar_posicao()

        self.scene.update() # Força a cena a atualizar (Evita nós cortados quando se mexem muito rápido)

    def atualizar_cores(self):
        if self.modo_destaque:
            return  # Modo de destaque ativo = não altera cores

        # Atualiza as cores dos vértices
        for vertice in self.grafo.vertices.values():
            alvo = self.COR_PADRAO
            if self.vertice_hover is not None: # Verifica se o vértice com o cursor por cima está conectado com os outros
                if (vertice == self.vertice_hover or
                        self.grafo.esta_diretamente_conectado(self.vertice_hover, vertice)):
                    alvo = self.COR_SELECIONADO
                else:
                    alvo = self.COR_DESSATURADO

            vertice.cor_atual = interpolar_cor(vertice.cor_atual, alvo, self.FADE_ALPHA) # Mudar cor de forma suave

            vertice.update()

        # Atualiza as cores das arestas
        for aresta in self.grafo.arestas:
            if aresta.hover:
                alvo = self.COR_SELECIONADO  # ou outra cor ao passar o mouse
            elif self.vertice_hover is not None:
                if (aresta.vertice1 == self.vertice_hover or
                        aresta.vertice2 == self.vertice_hover):
                    alvo = self.COR_SELECIONADO
                else:
                    alvo = self.COR_DESSATURADO
            else:
                alvo = self.COR_PADRAO

            aresta.cor_atual = interpolar_cor(aresta.cor_atual, alvo, self.FADE_ALPHA)
            aresta.atualizar_cor()

    def resetar_cores(self):
        """
        Restaura a cor padrão de todos os vértices e arestas do grafo.
        """
        # Resetar vértices
        for vertice in self.grafo.vertices.values():
            vertice.cor_atual = self.COR_PADRAO
            vertice.update()

        # Resetar arestas
        for aresta in self.grafo.arestas:
            aresta.cor_atual = self.COR_PADRAO
            aresta.atualizar_cor()

    """ -------------------------------------
                EVENTOS DO MOUSE
    ------------------------------------- """
    def mousePressEvent(self, event):
        cena_pos = self.mapToScene(event.pos())
        itens = self.scene.items(cena_pos)

        # 1) Se estivermos no modo “mao” (arrastar), simplesmente delegamos
        if self.modo_atual == 'mao':
            super().mousePressEvent(event)
            return

        # 2) Se estivermos no modo “borracha”, remover vértice/aresta
        if self.modo_atual == 'borracha' and event.button() == Qt.MouseButton.LeftButton:
            item = self.scene.itemAt(self.mapToScene(event.position().toPoint()), self.transform())
            # Sobe ao item raiz relevante
            while item is not None and not isinstance(item, (GrafoVertice, GrafoAresta)):
                item = item.parentItem()

            if isinstance(item, GrafoAresta):
                self._remover_aresta(item)
                return
            elif isinstance(item, GrafoVertice):
                self._remover_vertice(item)
                return

            return  # clique em vazio ignora

        # 3) Se estivermos no modo “vertice”, criamos novo vértice se clicou em fundo
        if event.button() == Qt.MouseButton.LeftButton and self.modo_atual == 'vertice':
            # Se não clicou sobre nenhum GrafoVertice, cria
            if not any(isinstance(i, GrafoVertice) for i in itens):
                novo_vertice = self.handle_adicionar_vertice(x=cena_pos.x(), y=cena_pos.y())
                if novo_vertice:
                    self.vertice_selecionado = novo_vertice
                return  # não chamamos super() aqui, pois criamos o vértice e não queremos arrastar

        # 4) Agora vamos permitir que o QGraphicsView inicie o arraste (se for o caso)
        super().mousePressEvent(event)

        # 5) Se estivermos no modo “aresta”, verificamos se clicamos num vértice
        if self.modo_atual == 'aresta' and event.button() == Qt.MouseButton.LeftButton:
            for item in itens:
                if isinstance(item, GrafoVertice):
                    # --- Primeiro clique: armazenamos v1 e pintamos contorno
                    if self.ultimo_vertice_clicado is None:
                        self.ultimo_vertice_clicado = item
                        item.definir_contorno(QColor(255, 255, 255), 3)
                        return

                    # --- Segundo clique: criar aresta entre v1 e v2
                    v1 = self.ultimo_vertice_clicado
                    v1.resetar_contorno()
                    v2 = item

                    # Se um deles foi removido em interim, só limpamos e saímos
                    if v1.vertice_id not in self.grafo.vertices or v2.vertice_id not in self.grafo.vertices:
                        self.ultimo_vertice_clicado = None
                        return

                    # Checa duplicata
                    # aresta_existe = any(
                    #     set(a.get_vertices()) == {v1.vertice_id, v2.vertice_id}
                    #     for a in self.grafo.arestas
                    # )
                    # if aresta_existe:
                    #     print(f"Aresta entre {v1.vertice_id} e {v2.vertice_id} já existe!")
                    #     self.ultimo_vertice_clicado = None
                    #     return

                    # Checa duplicata em grafos direcionados
                    if self.grafo.eh_direcionado:
                        aresta_existe = any(
                            a.vertice1.vertice_id == v1.vertice_id and
                            a.vertice2.vertice_id == v2.vertice_id
                            for a in self.grafo.arestas
                        )
                    else:
                        # No caso não direcionado, checa nos dois sentidos
                        aresta_existe = any(
                            {a.vertice1.vertice_id, a.vertice2.vertice_id} == {v1.vertice_id, v2.vertice_id}
                            for a in self.grafo.arestas
                        )

                    if aresta_existe:
                        print(f"Aresta entre {v1.vertice_id} e {v2.vertice_id} já existe!")
                        self.ultimo_vertice_clicado = None
                        return

                    # Abre diálogo de configuração (direcionado, ponderado, peso)
                    dialog = ArestaDialog(parent=self)
                    resultado = dialog.exec()
                    if resultado == QDialog.DialogCode.Accepted:
                        direcionado, ponderado, peso = dialog.get_values()
                        self.handle_adicionar_aresta(
                            v1,
                            v2,
                            self.COR_PADRAO,
                            ponderado=ponderado,
                            direcionado=direcionado,
                            peso=(peso if ponderado else 1)
                        )

                    # Limpa state
                    self.ultimo_vertice_clicado = None

                    # 6) Agora precisamos simular “mouse release” para garantir que o vértice
                    #    não fique grudado, mesmo que o usuário não tenha arrastado.
                    release_evt = QMouseEvent(
                        QEvent.Type.MouseButtonRelease,
                        event.position(),
                        event.globalPosition(),
                        Qt.MouseButton.LeftButton,
                        Qt.MouseButton.NoButton,
                        Qt.KeyboardModifier.NoModifier
                    )
                    super().mouseReleaseEvent(release_evt)
                    return

        if event.button() == Qt.MouseButton.MiddleButton:
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

            # Simula clique esquerdo para ativar scroll com botão do meio
            simular_evento = QMouseEvent(
                QEvent.Type.MouseButtonPress,
                event.position(),
                event.globalPosition(),
                Qt.MouseButton.LeftButton,
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier
            )
            super().mousePressEvent(simular_evento)
            return

    def mouseMoveEvent(self, event):
        pos = self.mapToScene(event.pos())
        itens = self.scene.items(pos)
        self.vertice_hover = None

        # Atualiza vértice sob o cursor
        for item in itens:
            if isinstance(item, GrafoVertice):
                self.vertice_hover = item
                break

        # Se estiver arrastando um vértice fixo manualmente
        if self.vertice_selecionado and self.vertice_selecionado.fixo:
            self.vertice_selecionado.setPos(pos)
            return  # ← não propaga o evento, pois já manipulamos manualmente

        # Caso contrário, comportamento padrão do Qt (para ItemIsMovable funcionar)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            self.setDragMode(QGraphicsView.DragMode.NoDrag)

            # Simula soltar botão esquerdo
            simular_evento = QMouseEvent(
                QEvent.Type.MouseButtonRelease,
                event.position(),
                event.globalPosition(),
                Qt.MouseButton.LeftButton,
                Qt.MouseButton.NoButton,
                Qt.KeyboardModifier.NoModifier
            )
            super().mouseReleaseEvent(simular_evento)
            return

        super().mouseReleaseEvent(event)

        if self.vertice_selecionado:
            self.vertice_selecionado.fixo = False

        super().mouseReleaseEvent(event)

    def menu_contexto_vertice(self, vertice, pos):
        menu_contexto_vertice = QMenu()
        acao_adicionar_aresta = menu_contexto_vertice.addAction("Adicionar Aresta")
        acao_remover_arestas = menu_contexto_vertice.addAction("Remover Arestas")
        acao_renomear_vertice = menu_contexto_vertice.addAction("Renomear Vértice")
        acao_remover_vertice = menu_contexto_vertice.addAction("Remover Vértice")

        acao_renomear_vertice.triggered.connect(lambda: self.menu_alterar_rotulo(vertice))
        acao_adicionar_aresta.triggered.connect(lambda: self.menu_adicionar_aresta(vertice))
        acao_remover_arestas.triggered.connect(lambda: self.menu_remover_arestas(vertice))
        acao_remover_vertice.triggered.connect(lambda: (
            self.limpar_estado_aresta(),
            self.handle_remover_vertice(vertice)
        ))

        menu_contexto_vertice.exec(pos)

    def limpar_estado_aresta(self):
        if self.ultimo_vertice_clicado:
            if self.ultimo_vertice_clicado in self.scene.items():
                self.ultimo_vertice_clicado.resetar_contorno()
        self.ultimo_vertice_clicado = None
        self.comeco_aresta = None

    def menu_alterar_rotulo(self, vertice):
        novo_rotulo, ok = QInputDialog.getText(self, "Renomear Nó", "Digite o novo rótulo:")
        if ok and novo_rotulo:
            vertice.alterar_rotulo(novo_rotulo)
            vertice.update()

    def menu_remover_vertice(self, vertice):
        print(vertice.vertice_id)
        # pega a key usando o value
        index_vertice = list(self.grafo.vertices.keys())[list(self.grafo.vertices.values()).index(vertice)] # nao sei eu tambem nao sei
        self.grafo.vertices.pop(index_vertice)
        self.scene.removeItem(vertice)
        print("self arestas: ", self.grafo.arestas)
        self.menu_remover_arestas(vertice)
        self.grafo_atualizado.emit()

    def menu_remover_arestas(self, vertice):
        for aresta in self.grafo.arestas.copy(): # precisa ser numa copia se nao so apaga a primeira aparicao do vertice
            print(aresta.get_vertices())
            if vertice.vertice_id in aresta.get_vertices():
                self.grafo.arestas.remove(aresta)
                self.scene.removeItem(aresta)
        self.grafo_atualizado.emit()

    def menu_adicionar_aresta(self, vertice):
        print(f"Vértice inicial selecionado: {vertice.vertice_id}")
        self.comeco_aresta = vertice  # Armazena o vértice inicial para a aresta, e espera o proximo clique

    def menu_contexto_padrao(self, pos):
        """Exibe o menu de contexto padrão."""
        menu = QMenu()
        acao_inserir = menu.addAction("Inserir nó")
        acao_resetar = menu.addAction("Limpar grafo")
        acao_gerar = menu.addAction("Gerar novo grafo")

        # Conecta as ações
        acao_inserir.triggered.connect(lambda: self.handle_adicionar_vertice(self.mapToScene(self.mapFromGlobal(pos)).x(), self.mapToScene(self.mapFromGlobal(pos)).y())) # passa a posição atual do mouse como parametro pra criar o vertice
        acao_resetar.triggered.connect(self.resetar_grafo)
        acao_gerar.triggered.connect(self.gerar_grafo)

        menu.exec(pos)

    def _remover_vertice(self, vertice: GrafoVertice):
        """
        Remove o vértice da cena e do dicionário de vértices,
        além de varrer e apagar todas as arestas que se conectam a ele.
        """
        try:
            # 1. Para cada aresta que contenha este vértice, remova-a
            # Usamos cópia para não modificar a lista enquanto iteramos
            for aresta in self.grafo.arestas.copy():
                if vertice.vertice_id in aresta.get_vertices():
                    # Reaproveita _remover_aresta para manter consistência
                    self._remover_aresta(aresta)

            # 2. Remover o vértice do dicionário do modelo
            # Encontrar a chave correspondente ao objeto
            index_vertice = None
            for chave, obj_v in self.grafo.vertices.items():
                if obj_v is vertice:
                    index_vertice = chave
                    break
            if index_vertice is not None:
                self.grafo.vertices.pop(index_vertice)

            # 3. Remover o item gráfico da cena
            self.scene.removeItem(vertice)

        except Exception as e:
            print(f"Erro ao remover vértice: {e}")

        # 4. Emitir sinal para atualizar UI/matriz/qualquer painel lateral
        self.grafo_atualizado.emit()

    def _remover_aresta(self, aresta: GrafoAresta):
        """
        Remove a aresta da cena e da lista do grafo, depois emite sinal de atualização.
        """
        try:
            # 1. Remover da lista de arestas do modelo
            if aresta in self.grafo.arestas:
                self.grafo.arestas.remove(aresta)

            # 2. Remover da QGraphicsScene
            self.scene.removeItem(aresta)

        except Exception as e:
            print(f"Erro ao remover aresta: {e}")

        # 3. Emitir sinal para atualizar UI/matriz/qualquer painel lateral
        self.grafo_atualizado.emit()

    """ -------------------------------------
           GERAÇÃO DE GRAFO ALEATÓRIO
    ------------------------------------- """
    def abrir_dialogo_gerar_grafo(self):
        dialog = GerarGrafoDialog(self)
        if dialog.exec():
            ponderado = dialog.ponderado_checkbox.isChecked()
            direcionado = dialog.direcionado_checkbox.isChecked()
            min_v = dialog.min_vertices_spin.value()
            max_v = dialog.max_vertices_spin.value()
            min_a = dialog.min_arestas_spin.value()
            max_a = dialog.max_arestas_spin.value()
            min_p = dialog.min_peso_spin.value() if ponderado else 1
            max_p = dialog.max_peso_spin.value() if ponderado else 1

            # Chama o método principal de geração com os parâmetros
            self.gerar_grafo(
                ponderado=ponderado,
                direcionado=direcionado,
                min_vertices=min_v,
                max_vertices=max_v,
                min_arestas=min_a,
                max_arestas=max_a,
                min_peso=min_p,
                max_peso=max_p,
            )

    def gerar_grafo(
            self,
            ponderado=True,
            direcionado=True,
            min_vertices=10,
            max_vertices=20,
            min_arestas=5,
            max_arestas=15,
            min_peso=1,
            max_peso=10
    ):
        if self.proximo_vertice_id == 1:
            tela_visivel = self.mapToScene(self.viewport().rect()).boundingRect()
            margem = 100
            num_vertices = random.randint(min_vertices, max_vertices)

            for _ in range(num_vertices):
                x = random.uniform(tela_visivel.left() + margem, tela_visivel.right() - margem)
                y = random.uniform(tela_visivel.top() + margem, tela_visivel.bottom() - margem)
                self.handle_adicionar_vertice(x, y)

            vertices = list(self.grafo.vertices.values())
            total_arestas = random.randint(min_arestas, max_arestas)

            tentativas = 0
            while total_arestas > 0 and tentativas < total_arestas * 5:
                tentativas += 1
                v1, v2 = random.sample(vertices, 2)

                if self.grafo.esta_diretamente_conectado(v1, v2):
                    continue

                peso = random.randint(min_peso, max_peso) if ponderado else 0
                self.handle_adicionar_aresta(
                    v1, v2, self.COR_PADRAO,
                    ponderado=ponderado,
                    direcionado=direcionado,
                    peso=peso
                )
                total_arestas -= 1

            self.grafo_atualizado.emit()
        else:
            self.resetar_grafo()
            self.gerar_grafo(
                ponderado, direcionado,
                min_vertices, max_vertices,
                min_arestas, max_arestas,
                min_peso, max_peso
            )

    """ -------------------------------------
              CONVERTER MATRIZ/GRAFO
    ------------------------------------- """
    def grafo_para_matriz(self):
        vertices = sorted(self.grafo.vertices.values(), key=lambda v: v.vertice_id)
        n = len(vertices)
        if n == 0:
            print("Grafo vazio")
            return

        # Mapear vertice_id → índice da matriz
        id_para_indice = {v.vertice_id: i for i, v in enumerate(vertices)}

        # --- Passo 2: montar matriz n×n com zeros e preencher com arestas ---
        matriz = [[0] * n for _ in range(n)]
        for aresta in self.grafo.arestas:
            i = id_para_indice[aresta.vertice1.vertice_id]
            j = id_para_indice[aresta.vertice2.vertice_id]
            matriz[i][j] = 1
            # Se não for direcionado, espelhar
            if not aresta.direcionado:
                matriz[j][i] = 1

        # --- Passo 3: criar QDialog para exibir a matriz ---
        dlg = QDialog(self)  # usa o controlador como parent
        dlg.setWindowTitle("Matriz de Adjacência do Grafo")
        dlg.setWindowIcon(QIcon(resource_path('assets/Icone-Grafla.png')))

        main_layout = QVBoxLayout(dlg)
        main_layout.setContentsMargins(8, 8, 8, 8)

        lbl = QLabel("Matriz de Adjacência")
        main_layout.addWidget(lbl)

        # Criar tabela fixa n×n
        tabela = QTableWidget()
        tabela.setStyleSheet("""
            QTableCornerButton {
                background-color: #1E1E1E;
            }
            QTableWidget::item {
                border-radius: 4px;
                padding: 0px;
            }
            QTableWidget::item:hover {
                background-color: #4C4C4C;
                border: 1px solid #4C4C4;
            }
            QHeaderView::section {
                padding: 0px;
                margin: 0px;
                font-weight: bold;
                border: 1px solid #353535;
            }
        """)
        tabela.setRowCount(n)
        tabela.setColumnCount(n)
        labels = [str(v.vertice_id) for v in vertices]
        tabela.setHorizontalHeaderLabels(labels)
        tabela.setVerticalHeaderLabels(labels)

        # Estilização de cabeçalhos
        h_header = tabela.horizontalHeader()
        v_header = tabela.verticalHeader()
        h_header.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        v_header.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        h_header.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        v_header.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)

        cell_size = 40
        h_header.setDefaultSectionSize(cell_size)
        v_header.setDefaultSectionSize(cell_size)
        h_header.setFixedHeight(cell_size)
        v_header.setFixedWidth(cell_size)

        # Preencher células
        for i in range(n):
            for j in range(n):
                item = QTableWidgetItem(str(matriz[i][j]))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                tabela.setItem(i, j, item)

        tabela.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        # Se a tabela for muito grande, colocar em QScrollArea
        scroll_area = QScrollArea()
        scroll_area.setWidget(tabela)
        scroll_area.setWidgetResizable(False)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)

        # Fixar tamanho máximo razoável (ou remova se quiser que cresça livremente)
        largura_total = n * cell_size + v_header.width() + 2
        altura_total = n * cell_size + h_header.height() + 2
        tabela.setFixedSize(largura_total, altura_total)

        main_layout.addWidget(scroll_area)

        # --- Passo 4: posicionar diálogo no canto inferior direito da janela principal ---
        dlg.resize(min(400, largura_total + 20), min(400, altura_total + 40))
        # Recupera a geometria da janela principal (ou do widget pai)
        parent_geom = self.window().geometry()
        pos_x = parent_geom.right() - dlg.width() - 20
        pos_y = parent_geom.bottom() - dlg.height() - 40
        dlg.move(pos_x, pos_y)

        dlg.exec()

    def matriz_para_grafo(self):
        # --- Passo 1: escolher tamanho ---
        dlg_n = QDialog(self)
        dlg_n.setWindowTitle("Escolher número de vértices")
        dlg_n.setWindowIcon(QIcon('assets/Icone-Grafla.png'))
        vlay = QVBoxLayout(dlg_n)
        vlay.addWidget(QLabel("Número de vértices:"))
        spin = QSpinBox()
        spin.setRange(1, 100) # Mínimo de 1 vértice, máximo de 100.
        spin.setValue(5) # Valor padrão.
        vlay.addWidget(spin)

        check_ponderado = QCheckBox("Ponderado")
        check_direcionado = QCheckBox("Direcionado")
        vlay.addWidget(check_ponderado)
        vlay.addWidget(check_direcionado)

        btn_ok = QPushButton("OK")

        btn_ok.setStyleSheet("""
            QPushButton {
                background-color: rgba(20, 20, 20, 240);
                color: white;
                border: none;
                padding: 4px 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #4CAF50;
            }
        """)

        btn_ok.clicked.connect(dlg_n.accept)
        vlay.addWidget(btn_ok)
        if not dlg_n.exec():
            return
        n = spin.value()

        # --- Passo 2: editar matriz n×n ---
        dlg_m = QDialog(self)
        dlg_m.setWindowTitle("Editar Matriz de Adjacência")
        dlg_m.setWindowIcon(QIcon('assets/Icone-Grafla.png'))

        # Criação da tabela fixa
        tabela = QTableWidget()
        tabela.setRowCount(n)
        tabela.setColumnCount(n)

        labels = [str(i + 1) for i in range(n)]
        tabela.setHorizontalHeaderLabels(labels)
        tabela.setVerticalHeaderLabels(labels)

        cell_size = 40
        h_header = tabela.horizontalHeader()
        v_header = tabela.verticalHeader()

        h_header.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        v_header.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        h_header.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        v_header.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        h_header.setDefaultSectionSize(cell_size)
        v_header.setDefaultSectionSize(cell_size)
        h_header.setFixedHeight(cell_size)
        v_header.setFixedWidth(cell_size)

        tabela.setStyleSheet("""
            QTableCornerButton {
                background-color: #1E1E1E;
            }
            QTableWidget::item {
                border-radius: 4px;
                padding: 0px;
            }
            QTableWidget::item:hover {
                background-color: #4C4C4C;
                border: 1px solid #4C4C4;
            }
            QHeaderView::section {
                padding: 0px;
                margin: 0px;
                font-weight: bold;
                border: 1px solid #353535;
            }
        """)

        # Cálculo do tamanho real da tabela
        largura_total = n * cell_size + v_header.width() + 2
        altura_total = n * cell_size + h_header.height() + 2

        # Definir tamanho fixo da tabela
        tabela.setFixedSize(largura_total, altura_total)

        tabela.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        tabela.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        tabela.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        # Área de rolagem sem redimensionamento automático
        scroll_area = QScrollArea()
        scroll_area.setWidget(tabela)
        scroll_area.setWidgetResizable(False)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)

        btns = QHBoxLayout()
        btn_cancel = QPushButton('Cancelar')
        btn_gerar = QPushButton('Gerar Grafo')

        btn_cancel.setStyleSheet("""
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

        btn_gerar.setStyleSheet("""
            QPushButton {
                background-color: rgba(20, 20, 20, 240);
                color: white;
                border: none;
                padding: 4px 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #4CAF50;
            }
        """)

        btns.addWidget(btn_cancel)
        btns.addWidget(btn_gerar)

        # Layout principal
        main_layout = QVBoxLayout()
        main_layout.addWidget(scroll_area)
        main_layout.addLayout(btns)
        dlg_m.setLayout(main_layout)

        # Preencher tabela com 0
        for i in range(n):
            for j in range(n):
                item = QTableWidgetItem("0")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                tabela.setItem(i, j, item)

        # Troca valores ao clicar
        def on_cell_clicked(r, c):
            atual = tabela.item(r, c).text()

            if check_ponderado.isChecked():
                # Se já tiver peso, mostra como valor atual
                peso_atual = int(atual) if atual.isdigit() else 1
                peso, ok = QInputDialog.getInt(
                    dlg_m, "Peso da Aresta",
                    f"Digite o peso da aresta de {r + 1} → {c + 1}:",
                    value=peso_atual, min=1, max=1000
                )
                if ok:
                    tabela.item(r, c).setText(str(peso))
                    if not check_direcionado.isChecked():
                        tabela.item(c, r).setText(str(peso))
            else:
                novo_valor = "1" if atual == "0" else "0"
                tabela.item(r, c).setText(novo_valor)
                if not check_direcionado.isChecked():
                    tabela.item(c, r).setText(novo_valor)

        tabela.cellClicked.connect(on_cell_clicked)

        # Ajuste inteligente da janela inicial:
        dlg_largura = min(largura_total + 40, 540)
        dlg_altura = min(altura_total + 40, 540)
        dlg_m.resize(dlg_largura, dlg_altura)
        dlg_m.setMinimumSize(300, 300)  # Opcional, limite mínimo confortável

        btn_cancel.clicked.connect(dlg_m.reject)
        btn_gerar.clicked.connect(dlg_m.accept)

        if not dlg_m.exec():
            return

        # --- Passo 3: gerar grafo a partir da matriz ---
        # limpa grafo existente
        self.resetar_grafo()

        # configurações de posicionamento
        raio_vertice = 20
        dist_min = raio_vertice * 2.5
        tela_visivel = self.mapToScene(
            self.viewport().rect()
        ).boundingRect()
        margem = 100

        # gera posições sem colisão
        posicoes = []
        tentativas_max = 200
        for _ in range(n):
            for _t in range(tentativas_max):
                x = random.uniform(
                    tela_visivel.left() + margem,
                    tela_visivel.right() - margem
                )
                y = random.uniform(
                    tela_visivel.top() + margem,
                    tela_visivel.bottom() - margem
                )
                pt = QPointF(x, y)
                if all((pt - p).manhattanLength() >= dist_min for p in posicoes):
                    posicoes.append(pt)
                    break
            else:
                QMessageBox.warning(
                    self, "Aviso",
                    f"Não foi possível posicionar o vértice {_ + 1} sem colisão.\n"
                    "Tente reduzir o número de vértices ou aumentar a área."
                )
                return

        # cria vértices
        vertices = []
        for pt in posicoes:
            v = self.handle_adicionar_vertice(x=pt.x(), y=pt.y())
            vertices.append(v)

        # cria arestas e laços conforme “1” na tabela
        # cria arestas e laços conforme valores na tabela
        for i in range(n):
            for j in range(n):
                try:
                    peso = int(tabela.item(i, j).text())
                except (ValueError, AttributeError):
                    peso = 0

                if peso > 0:
                    self.handle_adicionar_aresta(
                        vertices[i], vertices[j],
                        cor=self.COR_PADRAO,
                        ponderado=check_ponderado.isChecked(),
                        direcionado=check_direcionado.isChecked(),
                        peso=peso
                    )

        # atualiza a cena
        self.grafo_atualizado.emit()