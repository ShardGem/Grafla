from functools import partial

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QWidget, QSizePolicy, QVBoxLayout, QGroupBox, QLabel, QComboBox, QHBoxLayout, QPushButton, \
    QSpacerItem, QScrollArea
import heapq

from core.controlador import GrafoControlador

def encontrar_rotas_possiveis(inicio, fim, adj):
    todas_rotas = []
    rotas_set = set()

    def dfs(v_atual, caminho_atual, visitados):
        if v_atual == fim:
            rota_tupla = tuple(caminho_atual)
            if rota_tupla not in rotas_set:
                rotas_set.add(rota_tupla)
                todas_rotas.append(caminho_atual.copy())
            return
        for (viz_id, _) in adj[v_atual]:
            if viz_id in visitados:
                continue
            visitados.add(viz_id)
            caminho_atual.append(viz_id)
            dfs(viz_id, caminho_atual, visitados)
            caminho_atual.pop()
            visitados.remove(viz_id)

    dfs(inicio, [inicio], {inicio})
    return todas_rotas


def encontrar_menor_rota(inicio, fim, adj):
    dist = {v: float('inf') for v in adj}
    prev = {v: None for v in adj}
    dist[inicio] = 0
    pq = [(0, inicio)]
    while pq:
        d_v, v_id = heapq.heappop(pq)
        if d_v > dist[v_id]:
            continue
        if v_id == fim:
            break
        for (viz_id, peso) in adj[v_id]:
            alt = d_v + peso
            if alt < dist[viz_id]:
                dist[viz_id] = alt
                prev[viz_id] = v_id
                heapq.heappush(pq, (alt, viz_id))
    if dist[fim] == float('inf'):
        return []
    caminho = []
    u = fim
    while u is not None:
        caminho.append(u)
        u = prev[u]
    caminho.reverse()
    return caminho


def encontrar_maior_rota(inicio, fim, adj):
    melhor_rota = []
    melhor_peso = float('-inf')

    def dfs(v_atual, acumulado, caminho_atual, visitados):
        nonlocal melhor_peso, melhor_rota
        if v_atual == fim:
            if acumulado > melhor_peso:
                melhor_peso = acumulado
                melhor_rota = caminho_atual.copy()
            return
        for (viz_id, peso_aresta) in adj[v_atual]:
            if viz_id in visitados:
                continue
            visitados.add(viz_id)
            caminho_atual.append(viz_id)
            dfs(viz_id, acumulado + peso_aresta, caminho_atual, visitados)
            caminho_atual.pop()
            visitados.remove(viz_id)

    dfs(inicio, 0.0, [inicio], {inicio})
    return melhor_rota if melhor_peso != float('-inf') else []


class PainelAlgoritmos(QWidget):
    def __init__(self, controlador: GrafoControlador):
        super().__init__()
        self.ctrl = controlador

        self.rotas_multiplas = []
        self.rota_atual = 0

        self.ctrl.grafo_atualizado.connect(self.atualizar_lista_vertices)
        self._criar_ui()

        self.conectar_sinais_vertices()
        self.atualizar_lista_vertices()


    def _criar_ui(self):
        self.setMinimumWidth(320)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        grp_info = QGroupBox("Informações do Grafo")
        vinfo = QVBoxLayout(grp_info)
        self.lbl_n_vertices = QLabel()
        self.lbl_n_arestas = QLabel()
        self.lbl_direcionado = QLabel()
        self.lbl_ponderado = QLabel()
        vinfo.addWidget(self.lbl_n_vertices)
        vinfo.addWidget(self.lbl_n_arestas)
        vinfo.addWidget(self.lbl_direcionado)
        vinfo.addWidget(self.lbl_ponderado)
        layout.addWidget(grp_info)

        grp_alg = QGroupBox("Algoritmos / Caminhos")
        valg = QVBoxLayout(grp_alg)
        valg.setSpacing(10)

        lbl_algo = QLabel("Selecionar Algoritmo:")
        self.cmb_algo = QComboBox()
        self.cmb_algo.addItem("Menor Rota")
        self.cmb_algo.addItem("Maior Rota")
        self.cmb_algo.addItem("Todas Rotas")
        valg.addWidget(lbl_algo)
        valg.addWidget(self.cmb_algo)

        lbl_origem = QLabel("Origem (ID ou Rótulo):")
        self.cmb_origem = QComboBox()
        valg.addWidget(lbl_origem)
        valg.addWidget(self.cmb_origem)

        lbl_destino = QLabel("Destino (ID ou Rótulo):")
        self.cmb_destino = QComboBox()
        valg.addWidget(lbl_destino)
        valg.addWidget(self.cmb_destino)

        hbtn = QHBoxLayout()
        self.btn_run = QPushButton("Rodar")
        self.btn_clear = QPushButton("Limpar")
        hbtn.addWidget(self.btn_run)
        hbtn.addWidget(self.btn_clear)
        valg.addLayout(hbtn)

        self.navegacao_widget = QWidget()
        nav_layout = QHBoxLayout(self.navegacao_widget)
        self.btn_anterior = QPushButton("◀  Anterior")
        self.lbl_rota_status = QLabel("Rota 0 de 0")
        self.btn_proxima = QPushButton("Próxima ▶")
        nav_layout.addWidget(self.btn_anterior)
        nav_layout.addWidget(self.lbl_rota_status)
        nav_layout.addWidget(self.btn_proxima)
        self.navegacao_widget.setVisible(False)

        self.lbl_titulo_rotas = QLabel("Caminhos encontrados:")
        self.lbl_titulo_rotas.setStyleSheet("font-weight: bold; font-size: 12px;")
        self.lbl_titulo_rotas.setVisible(False)

        self.lbl_lista_rotas = QLabel()
        self.lbl_lista_rotas.setWordWrap(True)
        # Agora definimos RichText para poder usar <b> … </b>
        self.lbl_lista_rotas.setTextFormat(Qt.TextFormat.RichText)
        self.lbl_lista_rotas.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.lbl_lista_rotas.setStyleSheet("""
                   QLabel {
                       font-size: 11px;
                       color: #CCCCCC;
                   }
               """)

        self.scroll_lista_rotas = QScrollArea()
        self.scroll_lista_rotas.setWidgetResizable(True)
        self.scroll_lista_rotas.setWidget(self.lbl_lista_rotas)
        self.scroll_lista_rotas.setFixedHeight(250)
        self.scroll_lista_rotas.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.scroll_lista_rotas.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.scroll_lista_rotas.setVisible(False)

        layout.addWidget(grp_alg)
        layout.addWidget(self.navegacao_widget)
        layout.addWidget(self.lbl_titulo_rotas)
        layout.addWidget(self.scroll_lista_rotas)
        layout.addItem(
            QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        self.btn_run.clicked.connect(self.on_btn_run)
        self.btn_clear.clicked.connect(self.on_btn_clear)
        self.btn_anterior.clicked.connect(self.rota_anterior)
        self.btn_proxima.clicked.connect(self.rota_proxima)

    def atualizar_lista_vertices(self):
        self.cmb_origem.blockSignals(True)
        self.cmb_destino.blockSignals(True)

        self.cmb_origem.clear()
        self.cmb_destino.clear()

        ids = sorted(self.ctrl.grafo.vertices.keys())
        for vid in ids:
            rotulo = self.ctrl.grafo.vertices[vid].rotulo or str(vid)
            self.cmb_origem.addItem(rotulo, userData=vid)
            self.cmb_destino.addItem(rotulo, userData=vid)

        self.lbl_n_vertices.setText(f"Vértices: {len(ids)}")
        self.lbl_n_arestas.setText(f"Arestas: {len(self.ctrl.grafo.arestas)}")

        if self.ctrl.grafo.arestas:
            eh_direcionado = any(aresta.direcionado for aresta in self.ctrl.grafo.arestas)
            eh_ponderado = any(aresta.ponderado or aresta.peso > 1
                               for aresta in self.ctrl.grafo.arestas)
        else:
            eh_direcionado = False
            eh_ponderado = False

        self.lbl_direcionado.setText(
            f"Direcionado: {'✅' if eh_direcionado else '❌'}"
        )
        self.lbl_ponderado.setText(
            f"Ponderado: {'✅' if eh_ponderado else '❌'}"
        )

        self.cmb_origem.blockSignals(False)
        self.cmb_destino.blockSignals(False)

    def conectar_sinais_vertices(self):
        for vertice in self.ctrl.grafo.vertices.values():
            vertice.rotulo_alterado.connect(self.slot_rotulo_alterado)

    def slot_rotulo_alterado(self, vid_str, rotulo):
        self.atualizar_lista_vertices()

    def on_btn_run(self):
        self.rotas_multiplas = []
        self.rota_atual = 0
        self.scroll_lista_rotas.setVisible(False)
        self.navegacao_widget.setVisible(False)

        if self.cmb_origem.count() == 0 or self.cmb_destino.count() == 0:
            return

        origem_id = self.cmb_origem.currentData()
        destino_id = self.cmb_destino.currentData()

        algo_text = self.cmb_algo.currentText()

        adj = self.ctrl.grafo.criar_dicionario_adjacencia()

        if algo_text == "Menor Rota":
            caminho = encontrar_menor_rota(origem_id, destino_id, adj) or []
            self.rotas_multiplas = [caminho]

        elif algo_text == "Maior Rota":
            caminho = encontrar_maior_rota(origem_id, destino_id, adj) or []
            self.rotas_multiplas = [caminho]

        else:  # "Todas Rotas"
            rotas = encontrar_rotas_possiveis(inicio=origem_id, fim=destino_id, adj=adj) or []
            if not rotas:
                self.ctrl.resetar_cores()
                self.navegacao_widget.setVisible(False)
                self.lbl_lista_rotas.setVisible(False)
                return
            self.rotas_multiplas = rotas

        self.rota_atual = 0
        self._exibir_rota_atual()
        self._exibir_lista_de_rotas()

    def on_btn_clear(self):
        self.ctrl.modo_destaque = False
        self.ctrl.vertice_hover = None
        self.ctrl.resetar_cores()
        self.ctrl.atualizar_cores()
        self.ctrl.scene.update()
        self.rotas_multiplas = []
        self.rota_atual = 0
        self.navegacao_widget.setVisible(False)
        self.scroll_lista_rotas.setVisible(False)
        self.lbl_lista_rotas.clear()

    def _calcular_peso_rota(self, rota: list[int], adj: dict[int, list[tuple[int, float]]]) -> float:
        """
        Soma apenas os pesos maiores que 1. Arestas com peso == 1 são considerada como não ponderadas
        não alteram o total.
        """
        peso_total = 0.0
        for i in range(len(rota) - 1):
            v1, v2 = rota[i], rota[i + 1]
            for (viz_id, peso) in adj[v1]:
                if viz_id == v2:
                    if peso > 1:
                        peso_total += peso
                    break
        return peso_total

    def _destacar_caminho(self, lista_ids: list[int]):
        self.ctrl.modo_destaque = True
        if not lista_ids:
            self.ctrl.resetar_cores()
            return

        self.ctrl.resetar_cores()
        ids_no_caminho = set(lista_ids)

        cor_vertice = QColor(255, 165, 0)
        for vid, vertice in self.ctrl.grafo.vertices.items():
            vertice.cor_atual = cor_vertice if vid in ids_no_caminho else self.ctrl.COR_DESSATURADO
            vertice.update()

        cor_aresta = QColor(255, 165, 0)
        for aresta in self.ctrl.grafo.arestas:
            v1 = aresta.vertice1.vertice_id
            v2 = aresta.vertice2.vertice_id
            if aresta.direcionado:
                existe = any(lista_ids[i] == v1 and lista_ids[i + 1] == v2
                             for i in range(len(lista_ids) - 1))
                aresta.cor_atual = cor_aresta if existe else self.ctrl.COR_DESSATURADO
            else:
                existe = any((lista_ids[i] == v1 and lista_ids[i + 1] == v2) or
                             (lista_ids[i] == v2 and lista_ids[i + 1] == v1)
                             for i in range(len(lista_ids) - 1))
                aresta.cor_atual = cor_aresta if existe else self.ctrl.COR_DESSATURADO
            aresta.atualizar_cor()

        self.ctrl.scene.update()

    def _exibir_rota_atual(self):
        if not self.rotas_multiplas:
            return
        rota = self.rotas_multiplas[self.rota_atual]
        self._destacar_caminho(rota)
        total = len(self.rotas_multiplas)
        self.lbl_rota_status.setText(f"Rota {self.rota_atual + 1} de {total}")
        self.navegacao_widget.setVisible(True)

    def _ids_para_rotulos(self, rota: list[int]) -> list[str]:
        return [
            self.ctrl.grafo.vertices[vid].rotulo or str(vid)
            for vid in rota
        ]

    def _exibir_lista_de_rotas(self):
        """
        Exibe cada rota como HTML, com a rota atual em negrito.
        Usa <br> para quebrar linha e RichText para negrito.
        """
        if not self.rotas_multiplas:
            self.scroll_lista_rotas.setVisible(False)
            return

        adj = self.ctrl.grafo.criar_dicionario_adjacencia()
        linhas = []
        for idx, rota in enumerate(self.rotas_multiplas, start=1):
            nomes = self._ids_para_rotulos(rota)
            texto_rota = " → ".join(nomes)
            peso_total = self._calcular_peso_rota(rota, adj)
            linha = f"{idx}. {texto_rota}  (Peso: {peso_total:.0f})"
            if idx - 1 == self.rota_atual:
                linha = f"<b>{linha}</b>"
            linhas.append(linha)

        html = "<br>".join(linhas)
        self.lbl_lista_rotas.setText(html)

        self.lbl_titulo_rotas.setVisible(True)
        self.scroll_lista_rotas.setVisible(True)

    def rota_anterior(self):
        if not self.rotas_multiplas:
            return
        self.rota_atual = (self.rota_atual - 1) % len(self.rotas_multiplas)
        self._exibir_rota_atual()
        self._exibir_lista_de_rotas()

    def rota_proxima(self):
        if not self.rotas_multiplas:
            return
        self.rota_atual = (self.rota_atual + 1) % len(self.rotas_multiplas)
        self._exibir_rota_atual()
        self._exibir_lista_de_rotas()
