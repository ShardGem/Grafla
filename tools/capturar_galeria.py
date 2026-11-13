"""Gera capturas reais do Grafla e salva os grafos usados em cada exemplo."""

from __future__ import annotations

import argparse
import math
import os
import tempfile
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_SCALE_FACTOR", "1.5")

from PyQt6.QtCore import QEvent, QPoint, QPointF, QRectF, QSettings, Qt
from PyQt6.QtGui import QColor, QFont, QImage, QMouseEvent, QPainter, QPainterPath, QPen
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QScrollArea

from grafla.domain import Graph
from grafla.main_window import MainWindow
from grafla.persistence import load
from grafla.theme import DARK, apply

RAIZ = Path(__file__).resolve().parents[1]
LARANJA = "#ffad78"
AZUL = "#82b6ff"
VERDE = "#7ed8c5"
ROXO = "#b7a4f5"
ROSA = "#efa4bb"
AMARELO = "#e6c47c"
CORES = (AZUL, VERDE, ROXO, ROSA, AMARELO)


def criar_grafo(vertices, arestas, *, direcionado=False, ponderado=False, raio=34):
    grafo = Graph()
    for rotulo, x, y, cor in vertices:
        vertice = grafo.add_vertex(x, y, rotulo)
        vertice.color, vertice.radius = cor, raio
    for origem, destino, peso, rotulo in arestas:
        aresta = grafo.add_edge(origem, destino, direcionado, ponderado, peso)
        aresta.label, aresta.color = rotulo, "#71869d"
    grafo.validate()
    return grafo


def ligacoes(valores):
    return [(a, b, peso, "") for a, b, peso in valores]


def rotas_entrega():
    return criar_grafo(
        [
            ("CD", -420, 0, LARANJA),
            ("Oeste", -200, -230, AZUL),
            ("Sul", -200, 230, VERDE),
            ("Norte", 40, -230, AZUL),
            ("Centro", 40, 0, ROXO),
            ("Bairro", 40, 230, VERDE),
            ("Aero", 280, -230, AZUL),
            ("Porto", 280, 230, VERDE),
            ("Leste", 280, 0, ROXO),
            ("Destino", 520, 0, LARANJA),
        ],
        ligacoes(
            [
                (1, 2, 3),
                (1, 3, 4),
                (1, 5, 8),
                (2, 4, 2),
                (2, 5, 3),
                (3, 6, 3),
                (3, 5, 4),
                (4, 7, 3),
                (4, 5, 1),
                (5, 7, 4),
                (5, 8, 5),
                (5, 9, 3),
                (6, 8, 2),
                (7, 9, 2),
                (7, 10, 7),
                (8, 9, 1),
                (8, 10, 4),
                (9, 10, 2),
            ]
        ),
        direcionado=True,
        ponderado=True,
    )


def rede_buscas():
    return criar_grafo(
        [
            ("Central", -400, 0, LARANJA),
            ("A", -150, -230, AZUL),
            ("B", -150, 0, VERDE),
            ("C", -150, 230, ROXO),
            ("A1", 110, -310, AZUL),
            ("A2", 110, -150, AZUL),
            ("B1", 110, 50, VERDE),
            ("C1", 110, 220, ROXO),
            ("C2", 110, 380, ROXO),
            ("R1", 380, -230, AZUL),
            ("R2", 380, 30, VERDE),
            ("R3", 380, 300, ROXO),
        ],
        ligacoes(
            [
                (1, 2, 1),
                (1, 3, 1),
                (1, 4, 1),
                (2, 5, 1),
                (2, 6, 1),
                (3, 7, 1),
                (4, 8, 1),
                (4, 9, 1),
                (5, 10, 1),
                (6, 10, 1),
                (7, 11, 1),
                (8, 12, 1),
                (9, 12, 1),
            ]
        ),
    )


def rede_fibra():
    nomes = ["Norte", "Campus", "Parque", "Oeste", "Centro", "Leste", "Hub", "Sul", "Porto"]
    vertices = [
        (nome, (i % 3 - 1) * 300, (i // 3 - 1) * 230, CORES[i % 3]) for i, nome in enumerate(nomes)
    ]
    return criar_grafo(
        vertices,
        ligacoes(
            [
                (1, 2, 4),
                (2, 3, 7),
                (4, 5, 3),
                (5, 6, 6),
                (7, 8, 4),
                (8, 9, 5),
                (1, 4, 8),
                (4, 7, 7),
                (2, 5, 2),
                (5, 8, 9),
                (3, 6, 3),
                (6, 9, 4),
                (1, 5, 6),
                (2, 6, 5),
                (4, 8, 8),
                (5, 9, 7),
            ]
        ),
        ponderado=True,
    )


def dependencias():
    return criar_grafo(
        [
            ("Plano", -430, 0, LARANJA),
            ("Dados", -200, -210, AZUL),
            ("API", 50, -210, AZUL),
            ("Web", 50, 180, VERDE),
            ("Login", 290, -210, ROXO),
            ("Testes", 290, 130, AMARELO),
            ("Docs", -200, 180, ROSA),
            ("Release", 540, 0, LARANJA),
        ],
        ligacoes(
            [
                (1, 2, 1),
                (1, 7, 1),
                (2, 3, 1),
                (7, 4, 1),
                (3, 5, 1),
                (4, 6, 1),
                (5, 6, 1),
                (5, 8, 1),
                (6, 8, 1),
                (7, 8, 1),
            ]
        ),
        direcionado=True,
        raio=36,
    )


def comunidades():
    return criar_grafo(
        [
            ("CD", -410, -140, AZUL),
            ("Loja 1", -250, -300, AZUL),
            ("Loja 2", -90, -140, AZUL),
            ("Loja 3", -250, 20, AZUL),
            ("Hub", 100, -70, VERDE),
            ("Ana", 280, -240, VERDE),
            ("Bia", 460, -70, VERDE),
            ("Caio", 280, 100, VERDE),
            ("Lab", -260, 260, ROXO),
            ("Ivo", -90, 150, ROXO),
            ("Lia", -90, 370, ROXO),
            ("Ilha", 350, 330, ROSA),
        ],
        ligacoes(
            [
                (1, 2, 1),
                (2, 3, 1),
                (3, 4, 1),
                (4, 1, 1),
                (1, 3, 1),
                (5, 6, 1),
                (6, 7, 1),
                (7, 8, 1),
                (8, 5, 1),
                (5, 7, 1),
                (9, 10, 1),
                (10, 11, 1),
                (11, 9, 1),
            ]
        ),
    )


def equipe():
    grafo = criar_grafo(
        [
            ("Oficina", 0, 0, LARANJA),
            ("Design", -300, -200, ROSA),
            ("Dados", 0, -310, AZUL),
            ("Web", 300, -200, VERDE),
            ("API", 340, 110, AZUL),
            ("App", 130, 310, VERDE),
            ("Infra", -160, 290, ROXO),
            ("Docs", -340, 70, AMARELO),
        ],
        ligacoes([(1, i, 1) for i in range(2, 9)] + [(2, 8, 1), (3, 5, 1)]),
        raio=36,
    )
    grafo.vertices[1].pinned = True
    return grafo


def fluxo_pedidos():
    return criar_grafo(
        [
            ("Novo", -380, 0, AZUL),
            ("Fila", -100, 0, ROXO),
            ("Exec", 190, 0, LARANJA),
            ("Erro", 480, 280, ROSA),
            ("Fim", 480, 0, VERDE),
        ],
        [
            (1, 2, 1, "enviar"),
            (2, 3, 1, "iniciar"),
            (3, 2, 1, "voltar"),
            (3, 3, 1, "aguardar"),
            (3, 4, 1, "falhar"),
            (4, 2, 1, "tentar"),
            (3, 5, 1, "concluir"),
            (4, 4, 1, "revisar"),
        ],
        direcionado=True,
        raio=38,
    )


def matriz_pesos():
    return criar_grafo(
        [
            (
                str(i + 1),
                300 * math.cos(math.pi * i / 3 - math.pi / 2),
                260 * math.sin(math.pi * i / 3 - math.pi / 2),
                CORES[i % 3],
            )
            for i in range(6)
        ],
        ligacoes(
            [(1, 2, 0), (2, 3, 4), (1, 6, 7), (6, 5, 2), (5, 4, 3), (2, 5, 6), (3, 4, 1), (4, 1, 9)]
        ),
        direcionado=True,
        ponderado=True,
    )


def fisica_clusters():
    vertices = []
    for centro, rotulos, cor, pontos in [
        (
            (-320, 0),
            ["Produto", "API", "Web 1", "Web 2", "App"],
            AZUL,
            [(-520, -160), (-420, 180), (-200, 180), (-150, -180)],
        ),
        (
            (0, 0),
            ["Dados", "BI", "ETL", "SQL", "Cache"],
            VERDE,
            [(-80, -250), (140, -180), (-80, 250), (140, 180)],
        ),
        (
            (400, 0),
            ["Infra", "Cloud", "Logs", "CI", "DNS"],
            ROXO,
            [(250, -250), (600, -160), (620, 160), (320, 250)],
        ),
    ]:
        vertices.append((rotulos[0], *centro, cor))
        vertices.extend((nome, x, y, cor) for nome, (x, y) in zip(rotulos[1:], pontos, strict=True))
    grafo = criar_grafo(
        vertices,
        ligacoes(
            [(hub, folha, 1) for hub in (1, 6, 11) for folha in range(hub + 1, hub + 5)]
            + [(1, 6, 1), (6, 11, 1)]
        ),
        raio=31,
    )
    for chave in (1, 6, 11):
        grafo.vertices[chave].pinned = True
        grafo.vertices[chave].radius = 38
    return grafo


def atribuicoes():
    return criar_grafo(
        [
            ("Ana", -320, -270, AZUL),
            ("Bia", -320, -90, AZUL),
            ("Caio", -320, 90, AZUL),
            ("Dani", -320, 270, AZUL),
            ("Web", 280, -220, VERDE),
            ("API", 280, 0, ROXO),
            ("App", 280, 220, ROSA),
        ],
        ligacoes([(1, 5, 1), (1, 6, 1), (2, 5, 1), (2, 7, 1), (3, 6, 1), (4, 6, 1), (4, 7, 1)]),
        raio=38,
    )


class Galeria:
    def __init__(self, app, destino, exemplos, temporario):
        self.app, self.destino, self.exemplos = app, destino, exemplos
        self.destino.mkdir(parents=True, exist_ok=True)
        self.exemplos.mkdir(parents=True, exist_ok=True)
        settings = QSettings(str(temporario / "preferencias.ini"), QSettings.Format.IniFormat)
        settings.setValue("interface_animations", False)
        settings.setValue("autosave", False)
        apply(app, DARK)
        self.window = MainWindow(temporario / "dados", settings)
        self.window.autosave_timer.stop()
        self.window.resize(1600, 1000)
        self.window.show()
        self.registros = []

    def preparar(self, grafo, arquivo, *, tema="dark", painel=0, largura=440):
        janela = self.window
        janela.runner.clear_analysis()
        janela.physics.set_enabled(False)
        janela.canvas.cancel_edge()
        janela.canvas.set_mode("select")
        janela.settings.setValue("theme", tema)
        janela.settings.setValue("chain_edges", False)
        janela.settings.setValue("create_directed", False)
        janela.settings.setValue("create_weighted", False)
        janela.settings.setValue("create_weight", 1)
        janela.resize(1600, 1000)
        janela.apply_preferences()
        janela.physics_panel.choose_preset("Equilibrada")
        janela.physics_panel.advanced.setChecked(False)
        janela.document.reset(grafo)
        janela.workspace.show()
        janela.results_dock.hide()
        janela.tabs.setCurrentIndex(painel)
        janela.resizeDocks([janela.workspace], [largura], Qt.Orientation.Horizontal)
        janela.set_grid(True)
        janela.set_snap(False)
        self.arquivo = self.exemplos / arquivo
        self.salvar()
        self.assentar()
        janela.canvas.fit_graph()
        self.assentar()

    def assentar(self):
        self.app.processEvents()
        QTest.qWait(50)

    def salvar(self):
        self.window.document.write(self.arquivo)
        if load(self.arquivo) != self.window.document.graph:
            raise RuntimeError(f"O exemplo não preservou os dados: {self.arquivo.name}")

    def analisar(self, algoritmo, origem=1, destino=None, etapa=0):
        janela, painel = self.window, self.window.analysis
        janela.tabs.setCurrentIndex(1)
        painel.algorithm.setCurrentIndex(painel.algorithm.findData(algoritmo))
        painel.origin.setCurrentIndex(painel.origin.findData(origem))
        if destino is not None:
            painel.destination.setCurrentIndex(painel.destination.findData(destino))
        painel.run.click()
        limite = time.monotonic() + 8
        while janela.runner.result is None:
            if time.monotonic() >= limite:
                raise RuntimeError(f"A análise {algoritmo} não terminou: {painel.status.text()}")
            QTest.qWait(20)
        resultado = janela.runner.result
        if not resultado.complete or resultado.cancelled:
            raise RuntimeError(f"A análise {algoritmo} ficou incompleta.")
        if etapa:
            janela.runner.select_result(etapa)
        self.assentar()
        return resultado

    def capturar(self, nome, titulo, descricao, *, mover_ponteiro=True):
        janela = self.window
        self.salvar()
        janela.canvas.fit_graph()
        janela.canvas.setFocus()
        if mover_ponteiro:
            QTest.mouseMove(janela.canvas.viewport(), QPoint(16, 16))
        janela.statusBar().clearMessage()
        self.assentar()
        if not mover_ponteiro and janela.canvas._preview.path().isEmpty():
            raise RuntimeError("A captura da conexão ficou sem a prévia da aresta.")
        regiao = janela.canvas.mapToScene(janela.canvas.viewport().rect()).boundingRect()
        for item in (*janela.canvas.vertices.values(), *janela.canvas.edges.values()):
            if not regiao.contains(item.sceneBoundingRect()):
                raise RuntimeError(f"Há um elemento fora do enquadramento: {nome}")
        imagem = janela.grab().toImage()
        if imagem.isNull() or imagem.width() < 1600 or imagem.height() < 1000:
            raise RuntimeError(f"A captura ficou vazia ou pequena: {nome}")
        caminho = self.destino / nome
        if not imagem.save(str(caminho), "PNG") or QImage(str(caminho)).isNull():
            raise RuntimeError(f"Não foi possível salvar a captura: {nome}")
        self.registros.append((nome, titulo, descricao, self.arquivo.name))
        print(
            f"{len(self.registros):02} · {titulo} · {imagem.width()}×{imagem.height()}", flush=True
        )

    def gerar(self):
        janela = self.window
        self.preparar(rotas_entrega(), "rotas-de-entrega.grafla")
        self.analisar("shortest", destino=10)
        self.capturar(
            "01-rotas-de-entrega.png",
            "Planejar uma entrega",
            "Dijkstra encontra o menor custo entre o centro de distribuição e o destino.",
        )
        resultado = self.analisar("all", destino=10)
        ordem = sorted(range(len(resultado.paths)), key=lambda i: (resultado.costs[i], i))
        janela.runner.select_result(ordem[min(5, len(ordem) - 1)])
        self.capturar(
            "02-comparar-caminhos.png",
            "Comparar alternativas",
            "A lista de rotas mostra custos e sequências; clicar em outra opção muda o destaque.",
        )

        self.preparar(rede_buscas(), "buscas-em-rede.grafla", largura=480)
        self.analisar("bfs", etapa=5)
        self.capturar(
            "03-busca-em-largura.png",
            "Busca em largura",
            "BFS percorre a rede por níveis. A tabela mostra a ordem das visitas e a fila.",
        )
        self.analisar("dfs", etapa=6)
        self.capturar(
            "04-busca-em-profundidade.png",
            "Busca em profundidade",
            "A mesma rede percorrida em profundidade, com a pilha e o passo atual visíveis.",
        )

        self.preparar(rede_fibra(), "rede-de-fibra.grafla")
        self.analisar("mst")
        self.capturar(
            "05-arvore-geradora-minima.png",
            "Conectar com menor custo",
            "Uma rede de fibra com nove pontos. A árvore mínima destaca as conexões escolhidas.",
        )
        self.preparar(dependencias(), "dependencias-do-projeto.grafla")
        self.analisar("topological", etapa=5)
        self.capturar(
            "06-dependencias.png",
            "Organizar dependências",
            "Um projeto da primeira tarefa à publicação, com a ordenação topológica em etapas.",
        )
        self.preparar(comunidades(), "comunidades.grafla", largura=500)
        self.analisar("components", etapa=1)
        self.capturar(
            "07-componentes.png",
            "Encontrar grupos separados",
            "Quatro componentes, incluindo um vértice isolado. Um dos grupos está em destaque.",
        )

        self.preparar(equipe(), "equipe-do-projeto.grafla")
        janela.canvas.vertices[1].setSelected(True)
        self.capturar(
            "08-propriedades.png",
            "Cuidar dos detalhes",
            "Rótulo, posição, raio, cor e fixação do vértice central no inspector.",
        )
        janela.inspector.create_directed.setChecked(True)
        janela.inspector.create_weighted.setChecked(True)
        janela.inspector.create_weight.setValue(2.5)
        janela.inspector.chain_edges.setChecked(True)
        janela.commands["tool_edge"].trigger()
        origem = janela.canvas.mapFromScene(janela.canvas.vertices[4].pos())
        QTest.mouseClick(janela.canvas.viewport(), Qt.MouseButton.LeftButton, pos=origem)
        alvo = janela.canvas.mapFromScene(QPointF(155, 220))
        viewport = janela.canvas.viewport()
        movimento = QMouseEvent(
            QEvent.Type.MouseMove,
            QPointF(alvo),
            QPointF(viewport.mapToGlobal(alvo)),
            Qt.MouseButton.NoButton,
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier,
        )
        self.app.sendEvent(viewport, movimento)
        self.capturar(
            "09-criar-conexoes.png",
            "Construir novas conexões",
            "Origem marcada, prévia da aresta e novas conexões direcionadas, com peso e sequência.",
            mover_ponteiro=False,
        )

        self.preparar(fluxo_pedidos(), "fluxo-de-pedidos.grafla")
        janela.canvas.edges[3].setSelected(True)
        self.capturar(
            "10-lacos-e-opostas.png",
            "Desenhar um fluxo de estados",
            "Um pedido pode aguardar, avançar, voltar ou falhar. Laços e arestas opostas coexistem.",
        )

        self.preparar(matriz_pesos(), "matriz-de-pesos.grafla", painel=2, largura=480)
        janela.matrix(False)
        janela.building.matrix.weighted.setChecked(True)
        self.assentar()
        tabela = janela.building.matrix.table
        tabela.setCurrentIndex(tabela.model().index(0, 1))
        self.capturar(
            "11-grafo-para-matriz.png",
            "Ler o grafo como matriz",
            "Arestas e pesos na tabela. O zero é uma conexão real; o ponto marca uma ausência.",
        )

        self.preparar(Graph(), "grafo-da-matriz.grafla", painel=2, largura=480)
        janela.matrix(True)
        matriz = janela.building.matrix
        matriz.count.setValue(6)
        matriz.weighted.setChecked(True)
        for a, b, peso in [
            (1, 2, 3),
            (2, 3, 4),
            (1, 4, 2),
            (2, 5, 5),
            (3, 6, 2),
            (4, 5, 0),
            (5, 6, 6),
            (2, 4, 4),
        ]:
            if not matriz.model.setData(matriz.model.index(a - 1, b - 1), str(peso)):
                raise RuntimeError("A matriz do exemplo recusou um peso válido.")
        matriz.apply.click()
        janela.canvas.move_vertices(
            {i + 1: ((i % 3 - 1) * 300, (i // 3 - 0.5) * 350) for i in range(6)},
            "Espaçar os vértices",
        )
        self.capturar(
            "12-matriz-para-grafo.png",
            "Construir a partir de uma tabela",
            "A matriz vira um grafo editável, organizado para leitura. O peso zero também é preservado.",
        )

        self.preparar(Graph(), "rede-gerada.grafla", painel=2)
        janela.generate()
        gerador = janela.building.generator
        gerador.vertices.setValue(18)
        gerador.edges.setValue(24)
        gerador.seed.setValue(57)
        gerador.apply.click()

        def colorir(grafo):
            for chave, vertice in grafo.vertices.items():
                vertice.color = CORES[(chave - 1) % 3]
                vertice.radius = 26

        janela.document.edit("Colorir o exemplo", colorir)
        self.capturar(
            "13-gerador.png",
            "Começar com uma rede pronta",
            "O gerador criou 18 vértices e 24 arestas. A seed permite repetir o mesmo exemplo.",
        )
        gerado = janela.document.graph.clone()

        self.preparar(fisica_clusters(), "fisica-em-grupos.grafla", painel=3)
        janela.physics_panel.choose_preset("Suave")
        janela.physics.set_enabled(True)
        for _ in range(220):
            janela.physics.tick()
        janela.physics.pause(suspend=True)
        janela.canvas.fit_graph()
        self.capturar(
            "14-fisica.png",
            "Organizar sem perder as âncoras",
            "Três centros fixados mantêm a estrutura; os demais vértices foram organizados pela física.",
        )
        janela.physics_panel.advanced.setChecked(True)
        janela.physics_panel.controls["gravity"].spin.setValue(0.18)
        janela.physics_panel.controls["centering"].spin.setValue(0.003)
        janela.physics.resume()
        for _ in range(80):
            janela.physics.tick()
        janela.physics.pause(suspend=True)
        self.arquivo = self.exemplos / "fisica-com-gravidade.grafla"
        janela.resize(1600, 1320)
        self.assentar()
        painel_fisica = janela.tabs.widget(3)
        if isinstance(painel_fisica, QScrollArea):
            painel_fisica.verticalScrollBar().setValue(0)
        janela.canvas.fit_graph()
        self.capturar(
            "15-fisica-avancada.png",
            "Ajustar as forças em tempo real",
            "Gravidade, direção, rigidez, centralização e limites de movimento nos ajustes avançados.",
        )

        self.preparar(rotas_entrega(), "rotas-de-entrega.grafla", tema="light")
        self.analisar("shortest", destino=10)
        self.capturar(
            "16-tema-claro.png",
            "O mesmo trabalho no tema claro",
            "A rota de menor custo no tema claro, preservando os destaques e o contraste dos controles.",
        )
        self.preparar(atribuicoes(), "pessoas-e-projetos.grafla")
        for chave in (1, 2, 5):
            janela.canvas.vertices[chave].setSelected(True)
        self.capturar(
            "17-selecao-em-grupo.png",
            "Editar uma seleção inteira",
            "Pessoas e projetos numa rede bipartida, com três elementos selecionados para edição em grupo.",
        )
        self.preparar(gerado, "rede-circular.grafla", painel=2)
        janela.building.setCurrentIndex(2)
        janela.commands["layout_circular"].trigger()
        self.capturar(
            "18-layout-circular.png",
            "Trocar o enquadramento da rede",
            "A rede do gerador reorganizada em círculo pelo painel de layouts, sem mudar as conexões.",
        )
        self.criar_indice()
        self.criar_pagina()
        janela.physics.set_enabled(False)
        janela.document.undo_stack.setClean()
        janela.close()

    def criar_indice(self):
        colunas, largura, altura = 4, 600, 375
        margem, topo, passo = 24, 130, 445
        linhas = math.ceil(len(self.registros) / colunas)
        imagem = QImage(
            colunas * largura + (colunas + 1) * margem,
            topo + linhas * passo + 35,
            QImage.Format.Format_RGB32,
        )
        imagem.fill(QColor("#11161e"))
        painter = QPainter(imagem)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QColor(LARANJA))
        painter.setFont(QFont("Noto Sans", 25, QFont.Weight.DemiBold))
        painter.drawText(margem + 2, 55, f"Grafla · {len(self.registros)} casos de uso")
        painter.setPen(QColor("#aebacc"))
        painter.setFont(QFont("Noto Sans", 12))
        painter.drawText(
            margem + 2, 94, "Capturas reais do aplicativo · exemplos para abrir e explorar"
        )
        for indice, (nome, titulo, _, _) in enumerate(self.registros):
            linha, coluna = divmod(indice, colunas)
            restantes = len(self.registros) - linha * colunas
            deslocamento = (
                (colunas - restantes) * (largura + margem) / 2 if restantes < colunas else 0
            )
            x = margem + coluna * (largura + margem) + deslocamento
            y = topo + linha * passo
            foto = QImage(str(self.destino / nome)).scaled(
                largura,
                altura,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            quadro = QRectF(x, y, largura, altura)
            painter.save()
            clip = QPainterPath()
            clip.addRoundedRect(quadro, 8, 8)
            painter.setClipPath(clip)
            painter.fillRect(quadro, QColor("#202733"))
            painter.drawImage(
                QRectF(
                    x + (largura - foto.width()) / 2,
                    y + (altura - foto.height()) / 2,
                    foto.width(),
                    foto.height(),
                ),
                foto,
            )
            painter.restore()
            painter.setPen(QPen(QColor("#394455"), 1))
            painter.drawRoundedRect(quadro, 8, 8)
            painter.setPen(QColor("#edf2f8"))
            painter.setFont(QFont("Noto Sans", 11, QFont.Weight.Medium))
            painter.drawText(
                QRectF(x, y + altura + 10, largura, 36),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                f"{indice + 1:02}  {titulo}",
            )
        painter.end()
        if not imagem.save(str(self.destino / "00-visao-geral.png"), "PNG"):
            raise RuntimeError("Não foi possível salvar o índice visual.")

    def criar_pagina(self):
        pagina = [
            "# Grafla em uso",
            "",
            "Rotas, redes, buscas, matrizes e edição: 18 capturas do aplicativo em funcionamento. "
            "Os grafos são exemplos fictícios, feitos para explorar as ferramentas.",
            "",
            "As imagens foram capturadas no Qt em Linux offscreen, com uma janela de 1600×1000 "
            "e escala de 150%. A captura dos ajustes avançados usa uma janela mais alta para "
            "mostrar o painel inteiro. A interface e os resultados são os do aplicativo, sem retoques. "
            "Clique em qualquer imagem para ver o tamanho completo.",
            "",
            "![Índice visual dos 18 casos de uso](screenshots/galeria/00-visao-geral.png)",
            "",
            "## Escolha um exemplo",
            "",
            "| Captura | O que mostra |",
            "| --- | --- |",
        ]
        for indice, (_, titulo, descricao, _) in enumerate(self.registros, 1):
            pagina.append(f"| [{indice:02} · {titulo}](#caso-{indice:02}) | {descricao} |")
        pagina.extend(["", "## Capturas", ""])
        for indice, (nome, titulo, descricao, arquivo) in enumerate(self.registros, 1):
            pagina.extend(
                [
                    f'<a id="caso-{indice:02}"></a>',
                    "",
                    f"### {indice:02} · {titulo}",
                    "",
                    descricao,
                    "",
                    f"[Abrir o grafo de exemplo](../examples/galeria/{arquivo}) · "
                    f"[Ver a imagem completa](screenshots/galeria/{nome})",
                    "",
                    f"![{titulo}](screenshots/galeria/{nome})",
                    "",
                ]
            )
        pagina.extend(
            [
                "## Reproduzir as capturas",
                "",
                "Os arquivos `.grafla` ficam em [`examples/galeria/`](../examples/galeria/). "
                "Abra pelo menu Arquivo ou passe o caminho ao iniciar:",
                "",
                "```bash",
                "uv run grafla examples/galeria/rotas-de-entrega.grafla",
                "```",
                "",
                "Para gerar as capturas novamente:",
                "",
                "```bash",
                "QT_QPA_PLATFORM=offscreen QT_SCALE_FACTOR=1.5 uv run python tools/capturar_galeria.py",
                "```",
                "",
                "A geração usa preferências temporárias e não altera os dados pessoais do editor.",
                "",
            ]
        )
        (self.destino.parent.parent / "galeria.md").write_text("\n".join(pagina), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destino", type=Path, default=RAIZ / "docs/screenshots/galeria")
    parser.add_argument("--exemplos", type=Path, default=RAIZ / "examples/galeria")
    args = parser.parse_args()
    app = QApplication([])
    app.setQuitOnLastWindowClosed(False)
    trabalho = RAIZ / "work"
    trabalho.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="galeria-", dir=trabalho) as temporario:
        galeria = Galeria(app, args.destino, args.exemplos, Path(temporario))
        try:
            galeria.gerar()
        finally:
            galeria.window.runner.cancel_analysis()
            galeria.window.physics.set_enabled(False)
            galeria.window.document.undo_stack.setClean()
            galeria.window.close()


if __name__ == "__main__":
    main()
