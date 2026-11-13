"""Gera um GIF da física usando o controlador e a interface do Grafla."""

from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_SCALE_FACTOR", "1")

from PyQt6.QtCore import QPoint, QSettings, Qt
from PyQt6.QtGui import QImage
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

from grafla.main_window import MainWindow
from grafla.persistence import load, save
from grafla.theme import DARK, apply

RAIZ = Path(__file__).resolve().parents[1]


def preparar_grafo():
    grafo = load(RAIZ / "examples/galeria/fisica-em-grupos.grafla")
    grupos = [
        (1, (-260, -20), (135, 225, 65, 295)),
        (6, (0, 150), (45, 135, 225, 315)),
        (11, (260, -20), (45, 315, 115, 245)),
    ]
    for chave, (x, y), angulos in grupos:
        centro = grafo.vertices[chave]
        centro.x, centro.y, centro.radius = x, y, 36
        for folha, graus in zip(range(chave + 1, chave + 5), angulos, strict=True):
            vertice = grafo.vertices[folha]
            angulo = math.radians(graus)
            vertice.x = x + 90 * math.cos(angulo)
            vertice.y = y + 90 * math.sin(angulo)
            vertice.radius = 26
    grafo.validate()
    return grafo


def posicoes(janela):
    return {chave: (v.x, v.y) for chave, v in janela.document.graph.vertices.items()}


def pausar(janela):
    if janela.physics.timer.isActive():
        janela.physics_panel.pause.click()
    else:
        janela.physics.pause(suspend=True)


def gravar(app, temporario, ffmpeg, fps):
    settings = QSettings(str(temporario / "preferencias.ini"), QSettings.Format.IniFormat)
    settings.setValue("interface_animations", False)
    settings.setValue("autosave", False)
    apply(app, DARK)
    janela = MainWindow(temporario / "dados", settings)
    janela.autosave_timer.stop()
    janela.resize(1440, 900)
    janela.show()
    janela.show_physics()
    janela.resizeDocks([janela.workspace], [380], Qt.Orientation.Horizontal)
    for chave, valor in {
        "repulsion": 7000,
        "ideal_distance": 170,
        "damping": 0.28,
        "centering": 0.001,
        "speed": 1.0,
    }.items():
        janela.physics_panel.controls[chave].spin.setValue(valor)
    grafo = preparar_grafo()
    janela.document.reset(grafo)
    documento = temporario / "fisica-em-acao.grafla"
    janela.document.write(documento)
    save(RAIZ / "examples/fisica-em-acao.grafla", grafo)
    janela.canvas.reset_view()
    janela.canvas.zoom(0.95)
    janela.canvas.centerOn(0, 60)
    janela.canvas.setFocus()
    QTest.mouseMove(janela.canvas.viewport(), QPoint(14, 14))
    app.processEvents()
    QTest.qWait(30)

    # O roteiro controla o relógio para gerar a mesma animação em máquinas diferentes.
    # Cada passo continua passando pelo controlador real e pelo canvas do aplicativo.
    janela.physics.timer.blockSignals(True)
    amostra = janela.grab().toImage()
    largura, altura = amostra.width(), amostra.height()
    video = temporario / "gravacao.mkv"
    comando = [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-f",
        "rawvideo",
        "-pixel_format",
        "rgb24",
        "-video_size",
        f"{largura}x{altura}",
        "-framerate",
        str(fps),
        "-i",
        "pipe:0",
        "-an",
        "-c:v",
        "ffv1",
        "-threads",
        "2",
        str(video),
    ]
    encoder = subprocess.Popen(comando, stdin=subprocess.PIPE)
    fixados = {chave: (v.x, v.y) for chave, v in grafo.vertices.items() if v.pinned}
    roteiro = []
    acumulado = 0.0
    movimento = []
    pausas = []
    capa = None
    total = 12 * fps
    try:
        for indice in range(total):
            if indice == fps:
                janela.physics_panel.enable.click()
            elif indice == round(4.5 * fps):
                pausar(janela)
            elif indice == round(5.5 * fps):
                janela.physics_panel.controls["ideal_distance"].spin.setValue(220)
            elif indice == 6 * fps:
                janela.physics_panel.pause.click()
            elif indice == 10 * fps:
                pausar(janela)

            if janela.physics.timer.isActive():
                acumulado += 1 / fps
                while acumulado + 1e-9 >= 0.03 and janela.physics.timer.isActive():
                    janela.physics.tick()
                    acumulado -= 0.03
            else:
                acumulado = 0.0
            app.processEvents()
            atuais = posicoes(janela)
            if any(atuais[chave] != ponto for chave, ponto in fixados.items()):
                raise RuntimeError("Um centro fixado se moveu durante a gravação.")
            regiao = janela.canvas.mapToScene(janela.canvas.viewport().rect()).boundingRect()
            if any(
                not regiao.contains(item.sceneBoundingRect())
                for item in (*janela.canvas.vertices.values(), *janela.canvas.edges.values())
            ):
                raise RuntimeError(f"O grafo saiu do enquadramento no quadro {indice}.")
            roteiro.append(
                {
                    "quadro": indice,
                    "tempo": indice / fps,
                    "estado": janela.physics.state,
                    "posicoes": atuais,
                }
            )
            if fps <= indice < round(4.5 * fps) or 6 * fps <= indice < 10 * fps:
                movimento.append(atuais)
            if round(4.5 * fps) <= indice < 6 * fps:
                pausas.append(atuais)
            janela.statusBar().clearMessage()
            quadro = janela.grab().toImage().convertToFormat(QImage.Format.Format_RGB888)
            if quadro.width() != largura or quadro.height() != altura:
                raise RuntimeError("A janela mudou de tamanho durante a gravação.")
            if indice == 3 * fps:
                capa = quadro.copy()
            encoder.stdin.write(quadro.constBits().asstring(quadro.sizeInBytes()))
            if indice % (2 * fps) == 0:
                print(f"Quadro {indice + 1}/{total} · {janela.physics.state}", flush=True)
    finally:
        encoder.stdin.close()
        codigo = encoder.wait(timeout=60)
        janela.physics.set_enabled(False)
        janela.document.undo_stack.setClean()
        janela.close()
    if codigo != 0:
        raise RuntimeError("O FFmpeg não conseguiu gravar os quadros.")
    if not movimento or movimento[0] == movimento[-1]:
        raise RuntimeError("A gravação não apresentou movimento.")
    if not pausas or any(ponto != pausas[0] for ponto in pausas):
        raise RuntimeError("As posições não permaneceram paradas durante a pausa.")
    (temporario / "roteiro.json").write_text(json.dumps(roteiro, indent=2), encoding="utf-8")
    if capa is not None:
        capa.save(str(temporario / "capa.png"))
    return video


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, default=RAIZ / "docs/screenshots/fisica-em-acao.gif")
    parser.add_argument("--fps", type=int, choices=(10, 20, 25), default=20)
    args = parser.parse_args()
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        parser.error("Instale o FFmpeg para gerar o GIF.")
    trabalho = RAIZ / "work"
    trabalho.mkdir(exist_ok=True)
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    app = QApplication([])
    app.setQuitOnLastWindowClosed(False)
    with tempfile.TemporaryDirectory(prefix="gif-fisica-", dir=trabalho) as pasta:
        temporario = Path(pasta)
        video = gravar(app, temporario, ffmpeg, args.fps)
        filtro = (
            "[0:v]scale=1280:800:flags=lanczos,split[quadros][cores];"
            "[cores]palettegen=stats_mode=diff[paleta];"
            "[quadros][paleta]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle"
        )
        subprocess.run(
            [
                ffmpeg,
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-i",
                str(video),
                "-filter_complex",
                filtro,
                "-gifflags",
                "+offsetting+transdiff",
                "-loop",
                "0",
                "-threads",
                "2",
                str(args.saida),
            ],
            check=True,
        )
        for nome in ("roteiro.json", "capa.png"):
            shutil.copyfile(temporario / nome, trabalho / f"gif-fisica-{nome}")
    print(f"GIF salvo em {args.saida} · {args.saida.stat().st_size / 1024 / 1024:.2f} MB")


if __name__ == "__main__":
    main()
