from __future__ import annotations

import argparse
import logging
import multiprocessing
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from PyQt6.QtCore import QCoreApplication, QSettings, QStandardPaths, QTimer
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QMessageBox

from grafla import __version__
from grafla.splash import Splash


def configure_logging(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(
        directory / "grafla.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8"
    )
    handlers = [handler]
    if sys.stderr is not None:
        handlers.append(logging.StreamHandler())
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=handlers,
    )


def main() -> int:
    multiprocessing.freeze_support()
    parser = argparse.ArgumentParser(description="Grafla — editor desktop de grafos")
    parser.add_argument("file", nargs="?", type=Path, help="Documento .grafla para abrir")
    parser.add_argument(
        "--data-dir", type=Path, help="Diretório de preferências, recuperação e logs"
    )
    parser.add_argument("--no-splash", action="store_true")
    parser.add_argument(
        "--smoke-test", action="store_true", help="Validar bootstrap e encerrar automaticamente"
    )
    parser.add_argument("--version", action="version", version=__version__)
    args = parser.parse_args()
    if args.smoke_test and args.data_dir is None:
        parser.error("--smoke-test exige --data-dir apontando para um diretório de testes")
    QCoreApplication.setOrganizationName("Grafla")
    QCoreApplication.setApplicationName("Grafla")
    QCoreApplication.setApplicationVersion(__version__)
    app = QApplication(sys.argv[:1])
    app.setWindowIcon(QIcon(str(Path(__file__).parent / "resources" / "grafla.png")))
    data_dir = args.data_dir or Path(
        QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation)
    )
    configure_logging(data_dir)
    if args.smoke_test and (data_dir / "recovery.grafla").exists():
        logging.getLogger("grafla.app").error(
            "Smoke test recusado: há recuperação nesse diretório. Use outro --data-dir."
        )
        return 1
    settings = QSettings(str(data_dir / "preferences.ini"), QSettings.Format.IniFormat)
    splash = (
        None
        if args.no_splash
        else Splash(
            settings.value("animations", True, type=bool),
            settings.value("splash_duration_ms", 1800, type=int),
        )
    )
    if splash:
        splash.show()
    state = {}

    def exception_hook(kind, value, traceback):
        logging.getLogger("grafla.app").critical(
            "Unhandled application failure", exc_info=(kind, value, traceback)
        )
        if args.smoke_test:
            app.exit(1)
        else:
            QMessageBox.critical(
                None,
                "Erro no Grafla",
                "Ocorreu um erro interno. Os detalhes foram registrados em grafla.log. Preserve seu trabalho e reinicie a aplicação.",
            )

    sys.excepthook = exception_hook

    def bootstrap():
        if splash:
            splash.report("Carregando preferências e recursos…", 0.2)
        from grafla.theme import apply, resolve

        apply(app, resolve(settings.value("theme", "dark")))
        QTimer.singleShot(0, create_window)

    def create_window():
        if splash:
            splash.report("Preparando editor, documentos e algoritmos…", 0.55)
        from grafla.main_window import MainWindow

        window = MainWindow(data_dir, settings)
        screen = app.primaryScreen()
        if screen is not None and not settings.contains("geometry"):
            available = screen.availableGeometry()
            window.resize(
                min(1366, int(available.width() * 0.94)), min(820, int(available.height() * 0.9))
            )
        state["window"] = window
        if splash:
            splash.finish_when_ready(present)
        else:
            QTimer.singleShot(0, present)

    def present():
        window = state["window"]
        if splash:
            splash.report("Editor pronto.", 1.0)
        window.show()
        if splash:
            if splash.animation:
                splash.animation.stop()
            splash.close()
        logging.getLogger("grafla.app").info("Grafla %s initialized", __version__)
        if args.smoke_test:
            if args.file and not window.files.open(args.file):
                raise RuntimeError("Não foi possível abrir o arquivo do smoke test")
            QTimer.singleShot(150, smoke_finish)
        else:
            QTimer.singleShot(0, open_workspace)

    def open_workspace():
        window = state["window"]
        # Recovery must be offered before a command-line file can clear it.
        window.files.offer_recovery()
        if args.file:
            window.files.open(args.file)

    def smoke_finish():
        window = state["window"]
        if not window.isVisible() or window.canvas.scene() is None:
            app.exit(1)
            return
        from grafla.algorithms import analyze
        from grafla.domain import generate_graph
        from grafla.exporting import export_graph
        from grafla.persistence import load

        window.physics.set_enabled(False)
        if not window.document.graph.vertices:
            window.document.replace("Smoke", generate_graph(6, 8, True, True))
        graph = window.document.graph.clone()
        window.document.write(data_dir / "smoke.grafla")
        if load(data_dir / "smoke.grafla") != graph:
            raise RuntimeError("Packaged document roundtrip failed")
        result = analyze(graph, "bfs", next(iter(graph.vertices)), None)
        if not result.steps:
            raise RuntimeError("Packaged graph backend failed")
        if len(graph.vertices) <= 1000 and len(graph.edges) <= 5000:
            window.physics.set_enabled(True)
            window.physics.tick()
            window.physics.set_enabled(False)
        for suffix in ("png", "jpg", "svg", "pdf"):
            export_graph(window.canvas, data_dir / f"smoke-graph.{suffix}", 800)
        window.canvas.fit_graph()
        window.grab().save(str(data_dir / "smoke-window.png"))
        window.document.undo_stack.setClean()
        window.close()
        app.quit()

    QTimer.singleShot(0, bootstrap)
    return app.exec()
