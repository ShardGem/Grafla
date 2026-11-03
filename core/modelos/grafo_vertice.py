from PyQt6.QtWidgets import QGraphicsItem, QGraphicsEllipseItem, QGraphicsTextItem, QGraphicsProxyWidget
from PyQt6.QtGui import QBrush, QPen, QColor, QPainter
from PyQt6.QtCore import Qt, QTimer

from ui.info_popup import InfoPopup

'''
CLASSE DE VÉRTICES

Essa classe herda de 'QGraphicsEllipseItem', um componente que desenha círculos
com propriedades que podem ser modificadas de qualquer forma. Cada vértice tem as 
seguintes propriedades:
- Um ID.
- raio.
- Posição atual.
- Cor da borda e fundo.
- Um 'QGraphicsTextItem' filho, que exibe seu ID no centro do vértice.
'''

class GrafoVertice(QGraphicsEllipseItem):
    def __init__(
        self,
        vertice_id,
        x,
        y,
        raio = 20,
        cor = QColor(128, 128, 128)
    ):
        super().__init__(-raio, -raio, 2 * raio, 2 * raio) # (posição x, posição y, largura, altura)

        self.vertice_id = vertice_id
        self.rotulo = ''
        self.setPos(x, y)
        self.raio = raio

        self.cor_atual = cor
        self.cor_alvo = cor
        self.contorno_atual = QPen(QColor(0, 0, 0))

        self.escala_rotulo = 1.0
        self.escala_rotulo_alvo = 1.0 # Muda dinamicamente

        # Variáveis para física
        self.vx = 0.0
        self.vy = 0.0
        self.fixo = False

        # Timer
        self.timer_interpolacao = QTimer()
        self.timer_interpolacao.setInterval(16)  # ~60fps
        self.timer_interpolacao.timeout.connect(self.atualizar_escala_rotulo)
        self.timer_interpolacao.start()

        # Menu de propriedades
        self.info_proxy = None

        # Ajustes
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable) # Flags que permitem que os vértices sejam selecionados e movidos.
        self.setAcceptHoverEvents(True)
        self.setZValue(1)  # Deixar os vértices em cima das arestas
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # ID do vértice
        self.texto_id = QGraphicsTextItem(str(self.vertice_id), self)
        self.texto_id.setDefaultTextColor(Qt.GlobalColor.white)
        limite = self.texto_id.boundingRect()
        self.texto_id.setPos(-limite.width()/2, -limite.height()/2)

        # # Rótulo do vértice
        # self.texto_rotulo = QGraphicsTextItem('', self)
        # self.texto_rotulo.setDefaultTextColor(Qt.GlobalColor.white)
        # limite = self.texto_rotulo.boundingRect()
        # self.texto_rotulo.setPos(-limite.width() / 2, -limite.height() * -0.75)

    ''' -------------------------------------
             RENDERIZAÇÃO DO VÉRTICE
    ------------------------------------- '''
    def paint(self, painter: QPainter, opcao, widget = None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing) # Suavização dos cantos
        painter.setPen(self.contorno_atual) # Cor dos cantos do vértice
        painter.setBrush(QBrush(self.cor_atual)) # Cor de fundo do vértice
        painter.drawEllipse(self.rect()) # Desenhar o vértice

    # def alterar_rotulo(self, novo_rotulo):
    #     self.rotulo = novo_rotulo
    #     self.texto_rotulo.setPlainText(str(self.rotulo))
    #     limite = self.texto_rotulo.boundingRect()
    #     self.texto_rotulo.setPos(-limite.width() / 2, -limite.height() * -0.75)

    def alterar_rotulo(self, novo_rotulo):
        if self.rotulo != novo_rotulo:
            self.rotulo = novo_rotulo
            self.texto_id.setPlainText(str(self.rotulo))
            limite = self.texto_id.boundingRect()
            self.texto_id.setPos(-limite.width() / 2, -limite.height() / 2)

    def definir_contorno(self, cor: QColor = QColor(255, 0, 0), espessura: int = 3):
        self.contorno_atual = QPen(cor, espessura)
        self.update()

    def resetar_contorno(self):
        self.contorno_atual = QPen(QColor(0, 0, 0))
        self.update()

    ''' -------------------------------------
                MUDAR ESCALA DO TEXTO
    ------------------------------------- '''
    def hoverEnterEvent(self, event):
        self.escala_rotulo_alvo = 1.25  # Aumenta o tamanho do texto em 25% quanndo o mouse passa por cima do vértice
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.escala_rotulo_alvo = 1.0  # Volta ao tamanho original
        super().hoverLeaveEvent(event)

    def atualizar_escala_rotulo(self):
        # Interpola suavemente a escala do rótulo
        fator_de_escala = 0.15
        if abs(self.escala_rotulo - self.escala_rotulo_alvo) > 0.01:
            self.escala_rotulo += (self.escala_rotulo_alvo - self.escala_rotulo) * fator_de_escala
            self.texto_id.setScale(self.escala_rotulo)
            limite = self.texto_id.boundingRect()
            self.texto_id.setTransformOriginPoint(limite.width() / 2, limite.height() / 2)
        else:
            self.escala_rotulo = self.escala_rotulo_alvo

    ''' -------------------------------------
                EVENTOS DO MOUSE
    ------------------------------------- '''
    def mouseDoubleClickEvent(self, event):
        # força modo nenhum ao abrir
        views = self.scene().views()
        if views and hasattr(views[0], 'alternar_modo'):
            views[0].alternar_modo('nenhum')

        # fecha popup antigo
        if self.info_proxy:
            self.scene().removeItem(self.info_proxy)
            self.info_proxy = None

        popup = InfoPopup(titulo=f"Vértice #{self.vertice_id}")
        popup.input_rotulo.setText(self.rotulo)
        popup.chk_direcionado.setVisible(False)
        popup.spn_peso.setVisible(False)
        popup.label_peso.setVisible(False)

        # conexões
        popup.btn_salvar.clicked.connect(lambda: self._on_salvar(popup))
        popup.btn_remover.clicked.connect(lambda: self._on_remover(popup))

        proxy = QGraphicsProxyWidget(self)
        proxy.setWidget(popup)
        proxy.setPos(self.raio + 5, -popup.height() / 2)
        proxy.setZValue(self.zValue() + 1)

        self.info_proxy = proxy

        super().mouseDoubleClickEvent(event)

    def _on_salvar(self, popup: InfoPopup):
        novo = popup.input_rotulo.text()
        self.alterar_rotulo(novo)

        # volta ao modo nenhum
        views = self.scene().views()
        if views and hasattr(views[0], 'alternar_modo'):
            views[0].alternar_modo('nenhum')

        # fecha popup
        if self.info_proxy:
            self.scene().removeItem(self.info_proxy)
            self.info_proxy = None

        # avisa painel
        view = views[0]
        if hasattr(view, 'grafo_atualizado'):
            view.grafo_atualizado.emit()

    def _on_remover(self, popup: InfoPopup):
        # fecha popup
        if self.info_proxy:
            self.scene().removeItem(self.info_proxy)
            self.info_proxy = None

        # delega ao controlador (a View que exibe este vértice)
        views = self.scene().views()
        if not views:
            return
        view = views[0]
        # supondo que seu GrafoControlador tem um método handle_remover_vertice
        if hasattr(view, 'handle_remover_vertice'):
            view.handle_remover_vertice(self)

        # após remoção, garante atualização do painel
        if hasattr(view, 'grafo_atualizado'):
            view.grafo_atualizado.emit()