"""Gera capturas reais do Grafla e salva os grafos usados em cada exemplo."""

from __future__ import annotations

import argparse
import math
import os
import shutil
import tempfile
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_SCALE_FACTOR", "2")

from PyQt6.QtCore import QEvent, QPoint, QPointF, QRectF, QSettings, Qt
from PyQt6.QtGui import QColor, QFont, QImage, QMouseEvent, QPainter, QPainterPath, QPen
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QScrollArea

from grafla.branding import brand_pixmap
from grafla.dialogs import AboutDialog, PreferencesDialog, SearchDialog
from grafla.domain import Graph
from grafla.main_window import MainWindow
from grafla.persistence import load
from grafla.splash import Splash
from grafla.theme import DARK, apply

RAIZ = Path(__file__).resolve().parents[1]
LARANJA = "#ffad78"
AZUL = "#82b6ff"
VERDE = "#7ed8c5"
ROXO = "#b7a4f5"
ROSA = "#efa4bb"
AMARELO = "#e6c47c"
CORES = (AZUL, VERDE, ROXO, ROSA, AMARELO)
JANELA = (1680, 1050)


def paleta_clara(grafo):
    """Usa cores mais escuras nos exemplos destinados ao fundo claro."""
    grafo = grafo.clone()
    cores = {
        LARANJA: "#b45220",
        AZUL: "#386faa",
        VERDE: "#218674",
        ROXO: "#8061b5",
        ROSA: "#b34d77",
        AMARELO: "#967022",
        "#71869d": "#65788f",
    }
    for elemento in (*grafo.vertices.values(), *grafo.edges.values()):
        elemento.color = cores.get(elemento.color, elemento.color)
    return grafo


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


def rede_metro():
    grafo = criar_grafo(
        [
            ("Oeste", -650, 40, AZUL),
            ("Vila", -430, 40, AZUL),
            ("Centro", -210, 40, LARANJA),
            ("Luz", 10, 40, LARANJA),
            ("Museu", 230, 40, AZUL),
            ("Leste", 450, 40, AZUL),
            ("Terminal", 670, 40, AZUL),
            ("Parque", -210, -200, VERDE),
            ("Campus", -430, -420, VERDE),
            ("Sul", -210, 280, VERDE),
            ("Jardim", 10, 500, VERDE),
            ("Teatro", 230, -180, LARANJA),
            ("Aero", 450, -400, LARANJA),
            ("Praça", 230, 260, LARANJA),
            ("Porto", 450, 480, LARANJA),
            ("Mercado", -650, -200, VERDE),
            ("Estádio", -650, 300, VERDE),
        ],
        [],
        raio=44,
    )
    for cor, trechos in (
        (AZUL, [(1, 2, 3), (2, 3, 2), (3, 4, 2), (4, 5, 3), (5, 6, 2), (6, 7, 4)]),
        (
            VERDE,
            [
                (3, 8, 3),
                (8, 9, 4),
                (3, 10, 3),
                (10, 11, 4),
                (1, 16, 3),
                (16, 9, 4),
                (1, 17, 3),
                (17, 10, 5),
            ],
        ),
        (LARANJA, [(4, 12, 3), (12, 13, 4), (4, 14, 3), (14, 15, 4)]),
    ):
        for origem, destino, minutos in trechos:
            aresta = grafo.add_edge(origem, destino, weighted=True, weight=minutos)
            aresta.color = cor
    for vertice in grafo.vertices.values():
        vertice.y *= 0.72
    grafo.validate()
    return grafo


def pre_requisitos():
    nomes = [
        "Álgebra",
        "Lógica",
        "Prog 1",
        "Cálculo",
        "Discreta",
        "Prog 2",
        "Modelos",
        "Grafos",
        "Dados",
        "Otimizar",
        "Projeto",
        "Sistemas",
    ]
    return criar_grafo(
        [
            (nome, (i // 3 - 1.5) * 330, (i % 3 - 1) * 250, CORES[i % 3])
            for i, nome in enumerate(nomes)
        ],
        ligacoes(
            [
                (1, 4, 1),
                (1, 5, 1),
                (2, 5, 1),
                (3, 6, 1),
                (4, 7, 1),
                (5, 8, 1),
                (6, 9, 1),
                (7, 10, 1),
                (8, 10, 1),
                (8, 11, 1),
                (9, 11, 1),
                (9, 12, 1),
                (10, 11, 1),
            ]
        ),
        direcionado=True,
        raio=44,
    )


def arvore_binaria():
    vertices = []
    for i, valor in enumerate((50, 25, 75, 12, 37, 62, 87, 6, 18, 31, 43, 56, 68, 81, 93)):
        nivel = (i + 1).bit_length() - 1
        posicao = i - (2**nivel - 1)
        x = (posicao - (2**nivel - 1) / 2) * 1140 / 2**nivel
        cor = LARANJA if nivel == 0 else (AZUL if (i + 1) >> (nivel - 1) == 2 else VERDE)
        vertices.append((str(valor), x, nivel * 230 - 345, cor))
    grafo = criar_grafo(
        vertices, ligacoes([(i // 2, i, 1) for i in range(2, 16)]), direcionado=True, raio=32
    )
    grafo.vertices[1].radius = 42
    return grafo


def arquitetura_servicos():
    grafo = criar_grafo(
        [
            ("App", -600, -180, AZUL),
            ("Web", -600, 180, AZUL),
            ("Gateway", -320, 0, LARANJA),
            ("Login", -40, -300, ROXO),
            ("Busca", -40, -100, VERDE),
            ("Pedidos", -40, 150, ROSA),
            ("Cache", 260, -250, VERDE),
            ("Banco", 260, -30, AZUL),
            ("Fila", 260, 250, AMARELO),
            ("Worker", 540, 250, AMARELO),
            ("Logs", 540, -250, ROXO),
            ("Storage", 540, -30, AZUL),
        ],
        [
            (1, 3, 1, "HTTPS"),
            (2, 3, 1, "HTTPS"),
            (3, 4, 1, "JWT"),
            (3, 5, 1, "GET"),
            (3, 6, 1, "POST"),
            (4, 7, 1, "sessão"),
            (5, 7, 1, "leitura"),
            (5, 8, 1, "consulta"),
            (6, 8, 1, "gravar"),
            (6, 9, 1, "evento"),
            (9, 10, 1, "consumir"),
            (10, 12, 1, "salvar"),
            (7, 11, 1, "métricas"),
            (8, 12, 1, "réplica"),
        ],
        direcionado=True,
        raio=44,
    )
    for aresta in grafo.edges.values():
        aresta.color = grafo.vertices[aresta.target].color
    return grafo


def mapa_estudos():
    vertices = [("Grafos", 0, 0, LARANJA)]
    arestas = []
    for i, (assunto, folhas) in enumerate(
        [
            ("Buscas", ("BFS", "DFS")),
            ("Caminhos", ("Dijkstra", "Rotas")),
            ("Árvores", ("Mínima", "Geradora")),
            ("Matrizes", ("Binária", "Pesos")),
            ("Física", ("Fixados", "Forças")),
            ("Modelos", ("Direção", "Laços")),
        ]
    ):
        angulo = math.radians(i * 60 - 90)
        cor = (*CORES, LARANJA)[i]
        ramo = len(vertices) + 1
        vertices.append((assunto, 340 * math.cos(angulo), 210 * math.sin(angulo), cor))
        arestas.append((1, ramo, 1))
        for nome, deslocamento in zip(folhas, (-12, 12), strict=True):
            ponta = angulo + math.radians(deslocamento)
            folha = len(vertices) + 1
            vertices.append((nome, 660 * math.cos(ponta), 400 * math.sin(ponta), cor))
            arestas.append((ramo, folha, 1))
    grafo = criar_grafo(vertices, ligacoes(arestas), raio=44)
    grafo.vertices[1].radius = 62
    for aresta in grafo.edges.values():
        aresta.color = grafo.vertices[aresta.target].color
    return grafo


def malha_rede():
    return criar_grafo(
        [
            (f"{chr(65 + linha)}{coluna + 1}", (coluna - 2) * 210, (linha - 2) * 180, CORES[coluna])
            for linha in range(5)
            for coluna in range(5)
        ],
        ligacoes(
            [
                (linha * 5 + coluna + 1, linha * 5 + coluna + 2, 1)
                for linha in range(5)
                for coluna in range(4)
            ]
            + [
                (linha * 5 + coluna + 1, (linha + 1) * 5 + coluna + 1, 1)
                for linha in range(4)
                for coluna in range(5)
            ]
        ),
        raio=31,
    )


def grafo_completo():
    return criar_grafo(
        [
            (
                str(i + 1),
                420 * math.cos(math.tau * i / 8 - math.pi / 2),
                310 * math.sin(math.tau * i / 8 - math.pi / 2),
                CORES[i % 5],
            )
            for i in range(8)
        ],
        ligacoes([(a, b, 1) for a in range(1, 9) for b in range(a + 1, 9)]),
        raio=38,
    )


def circuito_cultural():
    return criar_grafo(
        [
            ("Casa", -530, 0, LARANJA),
            ("Praça", -280, -240, AZUL),
            ("Museu", 20, -240, AZUL),
            ("Feira", 320, -240, VERDE),
            ("Café", 570, 0, LARANJA),
            ("Teatro", 320, 240, ROXO),
            ("Parque", 20, 240, VERDE),
            ("Lago", -280, 240, ROXO),
        ],
        [
            (1, 2, 0, "livre"),
            (2, 3, 1.5, ""),
            (3, 4, 2.75, ""),
            (4, 5, 1.25, ""),
            (5, 6, 2, ""),
            (6, 7, 1, ""),
            (7, 8, 2.5, ""),
            (8, 1, 1.5, ""),
            (2, 8, 0.5, ""),
            (3, 7, 1.75, ""),
            (4, 6, 0.75, ""),
            (3, 6, 3, ""),
        ],
        ponderado=True,
        raio=42,
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
        self.window.resize(*JANELA)
        self.window.show()
        self.registros = []

    def preparar(self, grafo, arquivo, *, tema="dark", painel=0, largura=440):
        janela = self.window
        janela.runner.clear_analysis()
        janela.physics.set_enabled(False)
        janela.canvas.cancel_edge()
        janela.canvas.set_mode("select")
        if tema == "light":
            grafo = paleta_clara(grafo)
        janela.settings.setValue("theme", tema)
        janela.settings.setValue("chain_edges", False)
        janela.settings.setValue("create_directed", False)
        janela.settings.setValue("create_weighted", False)
        janela.settings.setValue("create_weight", 1)
        janela.settings.setValue("grid", True)
        janela.settings.setValue("snap", False)
        janela.resize(*JANELA)
        janela.apply_preferences()
        janela.physics_panel.choose_preset("Equilibrada")
        janela.physics_panel.advanced.setChecked(False)
        janela.document.reset(grafo)
        janela.workspace.show()
        janela.results_dock.hide()
        janela.tabs.setCurrentIndex(painel)
        janela.resizeDocks([janela.workspace], [largura], Qt.Orientation.Horizontal)
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
        self.assentar()
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
        if imagem.isNull() or imagem.width() < JANELA[0] or imagem.height() < JANELA[1]:
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

        self.preparar(rede_fibra(), "rede-de-fibra.grafla", tema="light")
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

        self.preparar(equipe(), "equipe-do-projeto.grafla", tema="light")
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

        self.preparar(matriz_pesos(), "matriz-de-pesos.grafla", tema="light", painel=2, largura=480)
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
        janela.resize(JANELA[0], 1350)
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

        self.preparar(rotas_entrega(), "rotas-tema-claro.grafla", tema="light")
        self.analisar("shortest", destino=10)
        self.capturar(
            "16-tema-claro.png",
            "O mesmo trabalho no tema claro",
            "A rota de menor custo no tema claro, preservando os destaques e o contraste dos controles.",
        )
        self.preparar(atribuicoes(), "pessoas-e-projetos.grafla", tema="light")
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
        self.gerar_variacoes()
        self.criar_indice()
        self.criar_destaques()
        self.capturar_identidade()
        self.criar_pagina()
        janela.physics.set_enabled(False)
        janela.document.undo_stack.setClean()
        janela.close()

    def gerar_variacoes(self):
        janela = self.window
        self.preparar(rede_metro(), "metro-urbano.grafla")
        janela.workspace.hide()
        janela.zoom_controls.grid.setChecked(False)
        self.capturar(
            "19-rede-de-metro.png",
            "Uma rede de metrô no canvas inteiro",
            "Dezessete estações e três linhas coloridas, com tempos por trecho. "
            "Painéis recolhidos e grade desligada deixam o mapa em primeiro plano.",
        )
        self.preparar(rede_metro(), "metro-tema-claro.grafla", tema="light", largura=460)
        self.analisar("shortest", origem=9, destino=15)
        self.capturar(
            "20-metro-tema-claro.png",
            "Do campus ao porto",
            "Dijkstra encontra a viagem de menor custo entre Campus e Porto. "
            "O mesmo metrô aparece no tema claro, com as cores ajustadas para esse fundo.",
        )
        self.preparar(pre_requisitos(), "pre-requisitos.grafla", largura=470)
        self.analisar("topological", etapa=7)
        self.capturar(
            "21-pre-requisitos.png",
            "Planejar uma trilha de estudos",
            "Doze disciplinas e seus pré-requisitos. A ordenação topológica mostra "
            "uma sequência possível, com a etapa atual em destaque.",
        )
        self.preparar(arvore_binaria(), "arvore-binaria.grafla", tema="light", largura=460)
        self.analisar("bfs", etapa=8)
        self.capturar(
            "22-arvore-binaria.png",
            "Percorrer uma árvore por níveis",
            "Uma árvore binária com quinze valores. A busca em largura mostra "
            "as visitas, o vértice atual e a fila ao lado do desenho.",
        )
        self.preparar(arquitetura_servicos(), "arquitetura-de-servicos.grafla")
        janela.canvas.edges[10].setSelected(True)
        self.capturar(
            "23-arquitetura-de-servicos.png",
            "Desenhar as conexões de um sistema",
            "Clientes, gateway, serviços, banco e fila. Os rótulos descrevem as "
            "chamadas; uma conexão está selecionada para edição no inspector.",
        )
        self.preparar(arquitetura_servicos(), "servicos-tema-claro.grafla", tema="light")
        janela.workspace.hide()
        janela.zoom_controls.grid.setChecked(False)
        self.capturar(
            "24-servicos-tema-claro.png",
            "Revisar um diagrama sem os painéis",
            "A arquitetura no tema claro, com mais espaço no canvas. Direções, "
            "protocolos e cores ajudam a acompanhar o fluxo entre os serviços.",
        )
        self.preparar(mapa_estudos(), "mapa-de-estudos.grafla")
        janela.workspace.hide()
        janela.zoom_controls.grid.setChecked(False)
        self.capturar(
            "25-mapa-de-estudos.png",
            "Organizar os assuntos de uma aula",
            "Um mapa com dezenove vértices e seis assuntos. Cores e tamanhos "
            "foram editados no grafo para separar os ramos do estudo.",
        )
        self.preparar(mapa_estudos(), "mapa-tema-claro.grafla", tema="light")
        for chave in (5, 6, 7):
            janela.canvas.vertices[chave].setSelected(True)
        self.capturar(
            "26-selecao-no-mapa.png",
            "Editar um ramo em conjunto",
            "Três vértices do ramo Caminhos selecionados no tema claro. "
            "O inspector apresenta as propriedades da seleção em grupo.",
        )
        self.preparar(rede_metro(), "metro-urbano.grafla", largura=460)
        self.analisar("all", origem=9, destino=15)
        janela.analysis.browser.report_requested.emit()
        janela.resizeDocks([janela.results_dock], [230], Qt.Orientation.Vertical)
        self.capturar(
            "27-relatorio-de-rotas.png",
            "Consultar e copiar as rotas",
            "Caminhos alternativos no metrô, com o relatório textual aberto "
            "abaixo do canvas e a lista navegável de rotas ao lado.",
        )
        self.preparar(malha_rede(), "malha-de-rede.grafla", tema="light", painel=2)
        janela.building.setCurrentIndex(2)
        janela.commands["layout_grid"].trigger()
        janela.zoom_controls.snap.setChecked(True)
        self.capturar(
            "28-layout-em-grade.png",
            "Organizar uma malha em grade",
            "Vinte e cinco vértices e quarenta conexões, organizados pelo layout "
            "em grade. O snap está ligado para os próximos movimentos.",
        )
        self.preparar(grafo_completo(), "grafo-completo-k8.grafla", painel=2)
        janela.building.setCurrentIndex(2)
        janela.commands["layout_circular"].trigger()
        self.capturar(
            "29-grafo-completo.png",
            "Explorar um grafo completo",
            "K8 tem oito vértices e vinte e oito arestas. O layout circular "
            "separa os vértices e evidencia todas as conexões entre eles.",
        )
        self.preparar(circuito_cultural(), "circuito-cultural.grafla", tema="light", largura=460)
        self.analisar("shortest", origem=1, destino=5)
        self.capturar(
            "30-pesos-decimais.png",
            "Combinar custos decimais e custo zero",
            "Um circuito cultural com pesos fracionários e uma conexão de custo "
            "zero. A rota até o Café mantém esses valores no cálculo de Dijkstra.",
        )

    def capturar_identidade(self):
        destino = self.destino.parent
        for nome, captura in {
            "editor.png": "19-rede-de-metro.png",
            "light.png": "24-servicos-tema-claro.png",
            "physics.png": "14-fisica.png",
            "steps.png": "22-arvore-binaria.png",
        }.items():
            shutil.copyfile(self.destino / captura, destino / nome)
        for tema in ("dark", "light"):
            self.window.settings.setValue("theme", tema)
            self.window.apply_preferences()
            sobre = AboutDialog(self.window)
            try:
                sobre.show()
                self.assentar()
                if not sobre.grab().save(str(destino / f"sobre-{tema}.png"), "PNG"):
                    raise RuntimeError(f"Não foi possível capturar o Sobre no tema {tema}.")
            finally:
                sobre.close()
            preferencias = PreferencesDialog(self.window.settings, self.window)
            try:
                preferencias.resize(700, preferencias.sizeHint().height())
                preferencias.show()
                self.assentar()
                if not preferencias.grab().save(str(destino / f"preferencias-{tema}.png"), "PNG"):
                    raise RuntimeError(f"Não foi possível capturar as preferências no tema {tema}.")
            finally:
                preferencias.close()
        self.window.settings.setValue("theme", "dark")
        self.window.apply_preferences()
        busca = SearchDialog(
            list(self.window.commands.values()),
            self.window.document.graph.vertices.values(),
            self.window,
        )
        try:
            busca.search.setText("Física")
            busca.show()
            self.assentar()
            if not busca.grab().save(str(destino / "busca-de-comandos.png"), "PNG"):
                raise RuntimeError("Não foi possível capturar a busca de comandos.")
        finally:
            busca.close()
        splash = Splash(animate=False, minimum_ms=0)
        try:
            splash.show()
            for nome, status, progresso in [
                ("splash-carregando.png", "Carregando preferências e recursos…", 0.2),
                ("splash.png", "Preparando editor, documentos e algoritmos…", 0.55),
                ("splash-pronta.png", "Pronto para explorar.", 1),
            ]:
                splash.report(status, progresso)
                self.assentar()
                if not splash.grab().save(str(destino / nome), "PNG"):
                    raise RuntimeError("Não foi possível capturar a abertura.")
        finally:
            splash.close()

    def criar_indice(self):
        self.montar_painel(
            "00-visao-geral.png",
            self.registros,
            f"Grafla · {len(self.registros)} capturas",
            "Grafos, temas e ferramentas · capturas reais do aplicativo",
        )

    def criar_destaques(self):
        destaques = [self.registros[i - 1] for i in (19, 24, 25, 22, 14, 29)]
        self.montar_painel(
            "00-destaques.png",
            destaques,
            "Grafla · construir, explorar e compreender",
            "Redes urbanas, sistemas, mapas de estudo e algoritmos · temas claro e escuro",
            colunas=2,
            largura=1000,
        )

    def montar_painel(self, nome, registros, titulo, subtitulo, *, colunas=4, largura=600):
        altura = round(largura * JANELA[1] / JANELA[0])
        margem, topo, passo = 28, 130, altura + 70
        linhas = math.ceil(len(registros) / colunas)
        imagem = QImage(
            colunas * largura + (colunas + 1) * margem,
            topo + linhas * passo + 35,
            QImage.Format.Format_RGB32,
        )
        imagem.fill(QColor("#11161e"))
        painter = QPainter(imagem)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.drawPixmap(margem, 22, brand_pixmap("symbol", 64, 64))
        painter.setPen(QColor(LARANJA))
        painter.setFont(QFont("Noto Sans", 25, QFont.Weight.DemiBold))
        painter.drawText(margem + 84, 55, titulo)
        painter.setPen(QColor("#aebacc"))
        painter.setFont(QFont("Noto Sans", 12))
        painter.drawText(margem + 84, 94, subtitulo)
        for indice, (captura, legenda, _, _) in enumerate(registros):
            linha, coluna = divmod(indice, colunas)
            restantes = len(registros) - linha * colunas
            deslocamento = (
                (colunas - restantes) * (largura + margem) / 2 if restantes < colunas else 0
            )
            x = margem + coluna * (largura + margem) + deslocamento
            y = topo + linha * passo
            foto = QImage(str(self.destino / captura))
            if foto.isNull():
                raise RuntimeError(f"A imagem do painel está vazia: {captura}")
            foto = foto.scaled(
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
                f"{captura.split('-')[0]}  {legenda}",
            )
        painter.end()
        if not imagem.save(str(self.destino / nome), "PNG"):
            raise RuntimeError("Não foi possível salvar o índice visual.")

    def criar_pagina(self):
        quantidade = len(self.registros)
        foto = QImage(str(self.destino / self.registros[0][0]))
        escala = self.window.devicePixelRatioF() * 100
        pagina = [
            "# Grafla em uso",
            "",
            f"{quantidade} capturas do aplicativo, com variações de tema, enquadramento e ferramentas. "
            "Metrô, arquitetura de serviços, estudos, árvores, matrizes e física: "
            "os exemplos são fictícios e podem ser abertos no editor.",
            "",
            f"As imagens foram capturadas no Qt em Linux offscreen, com uma janela de "
            f"{JANELA[0]}×{JANELA[1]}, escala de {escala:.0f}% e PNGs de "
            f"{foto.width()}×{foto.height()}. A captura dos ajustes avançados usa uma janela mais alta para "
            "mostrar o painel inteiro. A interface e os resultados são os do aplicativo, sem retoques. "
            "Clique em qualquer imagem para ver o tamanho completo.",
            "",
            "![Seis maneiras de usar o Grafla](screenshots/galeria/00-destaques.png)",
            "",
            f"[Ver as {quantidade} capturas em um painel](screenshots/galeria/00-visao-geral.png) · "
            "[Tema escuro](#caso-19) · [Tema claro](#caso-24) · "
            "[Canvas inteiro](#caso-25) · [Algoritmos](#caso-22) · [Layouts](#caso-28)",
            "",
            "## Marca do Grafla",
            "",
            "O símbolo aparece no canto superior esquerdo do editor e abre a tela Sobre. "
            "A abertura usa a marca horizontal enviada pelo autor, com o progresso das etapas "
            "de inicialização. As versões com o nome branco ficam sobre um fundo escuro "
            "nos dois temas, preservando as cores e o contraste.",
            "",
            "![Abertura do Grafla com a nova marca](screenshots/splash.png)",
            "",
            "[Carregando preferências](screenshots/splash-carregando.png) · "
            "[Editor pronto](screenshots/splash-pronta.png) · "
            "[Sobre no tema escuro](screenshots/sobre-dark.png) · "
            "[Sobre no tema claro](screenshots/sobre-light.png)",
            "",
            "## Busca e preferências",
            "",
            "A busca reúne comandos e vértices por nome ou ID. As preferências "
            "controlam tema, grade, snap, interação, recuperação e abertura.",
            "",
            "[Busca de comandos](screenshots/busca-de-comandos.png) · "
            "[Preferências no tema escuro](screenshots/preferencias-dark.png) · "
            "[Preferências no tema claro](screenshots/preferencias-light.png)",
            "",
            "## Física em movimento",
            "",
            "![Acomodação dos vértices, pausa e retomada da física](screenshots/fisica-em-acao.gif)",
            "",
            "Os três centros permanecem fixos. A simulação acomoda os demais vértices, é pausada\n"
            "e retoma com outra distância ideal. O GIF se repete a cada 12 segundos.",
            "",
            "[Abrir o GIF](screenshots/fisica-em-acao.gif) ·\n"
            "[Abrir o grafo inicial](../examples/fisica-em-acao.grafla)",
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
                "QT_QPA_PLATFORM=offscreen QT_SCALE_FACTOR=2 uv run python tools/capturar_galeria.py",
                "```",
                "",
                "A geração usa preferências temporárias e não altera os dados pessoais do editor.",
                "",
                "Para gerar o GIF da física, tenha o FFmpeg instalado e execute:",
                "",
                "```bash",
                "QT_QPA_PLATFORM=offscreen QT_SCALE_FACTOR=1 uv run python tools/animar_fisica.py",
                "```",
                "",
                "O roteiro usa o controlador do aplicativo em passos de 30 ms e captura a interface\n"
                "do Qt a 20 quadros por segundo. A câmera fica parada durante toda a animação.",
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
