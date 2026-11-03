from PyQt6.QtWidgets import (
    QGraphicsPathItem, QGraphicsTextItem, QGraphicsProxyWidget
)
from PyQt6.QtGui import QPen, QColor, QPainterPath, QTransform, QPainterPathStroker
from PyQt6.QtCore import QPointF, Qt, QLineF

from core.modelos import GrafoVertice
from ui.info_popup import InfoPopup

class GrafoAresta(QGraphicsPathItem):
    def __init__(
        self,
        vertice1: GrafoVertice,
        vertice2: GrafoVertice,
        cor = QColor(128, 128, 128),
        ponderado = False,
        direcionado = False,
        peso = 1
    ):
        super().__init__()

        self.vertice1 = vertice1
        self.vertice2 = vertice2
        self.peso = peso
        self.ponderado = ponderado
        self.direcionado = direcionado

        self.cor_atual = cor
        self.cor_alvo = cor

        pen = QPen(self.cor_atual)
        pen.setWidth(2)
        self.setPen(pen)

        self.hover = False

        self.setZValue(-1)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAcceptHoverEvents(True)

        # Proxy do popup (inicialmente None; vai conter o InfoPopup)
        self.info_proxy = None

        # Texto do peso (apenas se ponderado e peso > 1)
        self.texto_peso = None
        if self.ponderado and self.peso > 1:
            self.texto_peso = QGraphicsTextItem(str(self.peso), self)
            self.texto_peso.setDefaultTextColor(Qt.GlobalColor.white)

        # Path da seta (será desenhado em paint())
        self.path_seta = QPainterPath()

        # Itens gráficos da seta (preenchimento e contorno)
        self.seta = QGraphicsPathItem(self)
        self.seta.setPen(QPen(Qt.GlobalColor.transparent, 1))
        self.seta.setBrush(self.cor_atual)

        self.contorno_seta = QGraphicsPathItem(self)
        self.contorno_seta.setPen(QPen(QColor("white"), 4))
        self.contorno_seta.setBrush(Qt.GlobalColor.transparent)
        self.contorno_seta.setZValue(self.seta.zValue() - 1)

        # Monta posição inicial
        self.atualizar_posicao()

        # Assim que a aresta for adicionada à cena, você deve chamar:
        #    aresta.abrir_popup_inicial()
        # para exibir o popup automaticamente.

    def atualizar_posicao(self):
        p1 = self.vertice1.pos()
        p2 = self.vertice2.pos()
        path = QPainterPath()

        # Laço
        if self.vertice1.vertice_id == self.vertice2.vertice_id:
            raio = self.vertice1.raio + 10
            path.moveTo(p1)
            path.arcTo(p1.x() - 2 * raio, p1.y() - raio, 2 * raio, 2 * raio, 0, 360)

            if self.texto_peso:
                centro_laco = QPointF(p1.x() - raio, p1.y())
                desloc_x = -raio * 1.7
                desloc_y = -raio * 0.5
                self.texto_peso.setPos(centro_laco + QPointF(desloc_x, desloc_y))

            # Sem seta para loop
            self.path_seta = QPainterPath()
        else:
            dx = p2.x() - p1.x()
            dy = p2.y() - p1.y()
            dist = (dx * dx + dy * dy) ** 0.5
            if dist == 0:
                return

            nx = dx / dist
            ny = dy / dist

            raio_origem = self.vertice1.raio
            raio_destino = self.vertice2.raio

            # Para evitar sobreposição, verificamos se existe a aresta oposta
            # para deslocar o caminho e fazer curva
            existe_oposta = False
            cena = self.scene()
            if cena:
                for item in cena.items():
                    if isinstance(item, GrafoAresta):
                        if item.vertice1 == self.vertice2 and item.vertice2 == self.vertice1:
                            existe_oposta = True
                            break

            p1_recuado = QPointF(
                p1.x() + nx * raio_origem,
                p1.y() + ny * raio_origem
            )

            p2_recuado = QPointF(
                p2.x() - nx * raio_destino,
                p2.y() - ny * raio_destino
            )

            if existe_oposta:
                # Criar caminho curvo usando Bezier
                path.moveTo(p1_recuado)

                # Vetor perpendicular para curvatura lateral
                perp_x = -ny
                perp_y = nx
                curva_desloc = 38  # valor do deslocamento da curva (ajuste aqui)

                ctrl1 = QPointF(
                    (p1_recuado.x() + p2_recuado.x()) / 2 + perp_x * curva_desloc,
                    (p1_recuado.y() + p2_recuado.y()) / 2 + perp_y * curva_desloc
                )

                path.quadTo(ctrl1, p2_recuado)

                # Para setas direcionadas, calcular ponto final e base seta no final da curva
                if self.direcionado:
                    # Aproximar o ponto final da curva para a ponta da seta
                    # Usando fórmula do Bezier quadrático
                    t = 0.9
                    p0 = p1_recuado
                    p1_ctrl = ctrl1
                    p2_end = p2_recuado
                    x = (1 - t) ** 2 * p0.x() + 2 * (1 - t) * t * p1_ctrl.x() + t ** 2 * p2_end.x()
                    y = (1 - t) ** 2 * p0.y() + 2 * (1 - t) * t * p1_ctrl.y() + t ** 2 * p2_end.y()
                    ponta_seta = QPointF(x, y)

                    dx_seta = ponta_seta.x() - p2.x()
                    dy_seta = ponta_seta.y() - p2.y()
                    dist_seta_destino = (dx_seta * dx_seta + dy_seta * dy_seta) ** 0.5
                    if dist_seta_destino != 0:
                        nx_seta_corrigido = dx_seta / dist_seta_destino
                        ny_seta_corrigido = dy_seta / dist_seta_destino

                        margem_extra = -40
                        ponta_seta = QPointF(
                            p2.x() - nx_seta_corrigido * (self.vertice2.raio + margem_extra),
                            p2.y() - ny_seta_corrigido * (self.vertice2.raio + margem_extra)
                        )

                    # Calcular direção da tangente no ponto t para a seta
                    dx_dt = 2 * (1 - t) * (p1_ctrl.x() - p0.x()) + 2 * t * (p2_end.x() - p1_ctrl.x())
                    dy_dt = 2 * (1 - t) * (p1_ctrl.y() - p0.y()) + 2 * t * (p2_end.y() - p1_ctrl.y())
                    ang_seta = (dx_dt ** 2 + dy_dt ** 2) ** 0.5
                    if ang_seta != 0:
                        nx_seta = dx_dt / ang_seta
                        ny_seta = dy_dt / ang_seta
                    else:
                        nx_seta, ny_seta = 0, 0

                    tamanho_seta = 12
                    p2_base_seta = QPointF(
                        ponta_seta.x() - nx_seta * tamanho_seta,
                        ponta_seta.y() - ny_seta * tamanho_seta
                    )

                    # Redesenha o caminho incluindo a linha para base da seta
                    path = QPainterPath()
                    path.moveTo(p1_recuado)
                    path.quadTo(ctrl1, ponta_seta)
                    self._gerar_path_seta(p2_base_seta, ponta_seta, tamanho_seta)

                else:
                    self.path_seta = QPainterPath()

            else:
                # Sem aresta oposta: linha reta
                if self.direcionado:
                    ponta_seta = QPointF(
                        p2.x() - nx * raio_destino,
                        p2.y() - ny * raio_destino
                    )
                    p2_base_seta = QPointF(
                        ponta_seta.x() - nx * 12,
                        ponta_seta.y() - ny * 12
                    )
                    path.moveTo(p1_recuado)
                    path.lineTo(p2_base_seta)
                    self._gerar_path_seta(p2_base_seta, ponta_seta, 12)
                else:
                    path.moveTo(p1_recuado)
                    path.lineTo(p2_recuado)
                    self.path_seta = QPainterPath()

            if self.texto_peso:
                # Posicionar o texto no ponto médio da curva (aproximado)
                if existe_oposta:
                    meio = ctrl1
                else:
                    meio = QPointF((p1.x() + p2.x()) / 2, (p1.y() + p2.y()) / 2)
                self.texto_peso.setPos(meio)

        self.setPath(path)
        self.atualizar_cor()

        if self.info_proxy:
            meio_x = (p1.x() + p2.x()) / 2
            meio_y = (p1.y() + p2.y()) / 2
            self.info_proxy.setPos(self.mapFromScene(QPointF(meio_x, meio_y)))

    def _gerar_path_seta(self, base: QPointF, ponta: QPointF, tamanho: float):
        linha = QLineF(base, ponta)
        angulo = linha.angle()
        meio_asa = tamanho / 2.0

        transform = QTransform()
        transform.translate(ponta.x(), ponta.y())
        transform.rotate(-angulo)

        p_asa1 = transform.map(QPointF(-tamanho, -meio_asa))
        p_asa2 = transform.map(QPointF(-tamanho, meio_asa))

        seta_path = QPainterPath()
        seta_path.moveTo(ponta)
        seta_path.lineTo(p_asa1)
        seta_path.lineTo(p_asa2)
        seta_path.closeSubpath()

        self.path_seta = seta_path

    def atualizar_cor(self):
        pen = self.pen()
        pen.setColor(self.cor_atual)
        self.setPen(pen)

        # não desenhamos os itens filhos da seta aqui, desenhamos em paint()
        self.update()

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(painter.RenderHint.Antialiasing)

        # 1) Contorno branco da própria linha
        if self.hover:
            pen_hover = QPen(QColor("white"), 5)
            painter.setPen(pen_hover)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(self.path())

        # 2) Desenha a linha normal
        painter.setPen(self.pen())
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(self.path())

        # 3) Desenha a seta (se direcionado)
        if self.direcionado and not self.path_seta.isEmpty():
            if self.hover:
                # contorno branco da seta
                painter.setPen(QPen(QColor("white"), 3))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawPath(self.path_seta)

                # preenchimento selecionado
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(self.cor_atual)
                painter.drawPath(self.path_seta)
            else:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(self.cor_atual)
                painter.drawPath(self.path_seta)

    def mouseDoubleClickEvent(self, event):
        # Abre o popup para editar aresta ao dar double-click (mantido)
        self.abrir_popup()  # reaproveita o mesmo método
        super().mouseDoubleClickEvent(event)

    def abrir_popup(self):
        """
        Abre o InfoPopup **logo após a criação** e também quando for double-click.
        Cria um QGraphicsProxyWidget para inserir o InfoPopup na cena e posicioná-lo.
        """
        # Se já existir um popup aberto, não abre outro
        if self.info_proxy:
            return

        popup = InfoPopup(titulo="Propriedades da Aresta")
        # Esconde o campo “Rótulo” (opcional; se não quiser usar rótulo em arestas)
        popup.input_rotulo.setVisible(False)
        popup.label_rotulo.setVisible(False)

        # Preenche com os valores atuais
        popup.chk_direcionado.setChecked(self.direcionado)
        popup.spn_peso.setValue(self.peso)

        # Atualiza direção ao marcar checkbox
        def atualizar_direcionamento(val):
            self.direcionado = val
            self.atualizar_posicao()
            self.update()

        popup.chk_direcionado.toggled.connect(atualizar_direcionamento)

        # Atualiza peso dinamicamente
        def atualizar_peso(val):
            self.peso = val
            self.ponderado = True
            if self.texto_peso is None:
                self.texto_peso = QGraphicsTextItem(str(self.peso), self)
                self.texto_peso.setDefaultTextColor(Qt.GlobalColor.white)
            else:
                self.texto_peso.setPlainText(str(self.peso))
            self.atualizar_posicao()
            self.update()

        popup.spn_peso.valueChanged.connect(atualizar_peso)

        # Função para remover a aresta
        def on_remover():
            cena = self.scene()
            if cena:
                cena.removeItem(self)
            # Se for chamado via criação inicial, também remover do modelo
            view = None
            try:
                views = self.scene().views()
                if views:
                    view = views[0]
            except Exception:
                pass

            if view and hasattr(view, '_remover_aresta'):
                try:
                    view._remover_aresta(self)
                except Exception as e:
                    print(f"[ERRO ao chamar _remover_aresta]: {e}")

            if view and hasattr(view, 'limpar_estado_aresta'):
                try:
                    view.limpar_estado_aresta()
                except Exception as e:
                    print(f"[ERRO ao chamar limpar_estado_aresta]: {e}")

            # Fecha o popup e limpa referência
            popup.close()
            self.info_proxy = None

        popup.btn_salvar.clicked.connect(lambda: (popup.close(), setattr(self, 'info_proxy', None)))
        popup.btn_remover.clicked.connect(on_remover)

        proxy = QGraphicsProxyWidget(self)
        proxy.setWidget(popup)

        # Posiciona no meio da aresta (mesmo cálculo de atualizar_posicao)
        p1 = self.vertice1.pos()
        p2 = self.vertice2.pos()
        meio = QPointF((p1.x() + p2.x()) / 2, (p1.y() + p2.y()) / 2)
        proxy.setPos(self.mapFromScene(meio))
        self.info_proxy = proxy

    def hoverEnterEvent(self, event):
        self.hover = True
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.hover = False
        self.update()
        super().hoverLeaveEvent(event)

    def shape(self):
        stroker = QPainterPathStroker()
        stroker.setWidth(15)
        return stroker.createStroke(self.path())

    def get_vertices(self):
        return [self.vertice1.vertice_id, self.vertice2.vertice_id]