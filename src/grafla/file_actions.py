import logging
from pathlib import Path

from PyQt6.QtCore import QObject
from PyQt6.QtWidgets import QFileDialog, QMessageBox

from grafla.persistence import DocumentError, load, save

logger = logging.getLogger(__name__)


class FileActions(QObject):
    def __init__(self, window, data_dir: Path):
        super().__init__(window)
        self.window = window
        self.document = window.document
        self.settings = window.settings
        self.recovery = data_dir / "recovery.grafla"

    def maybe_save(self) -> bool:
        self.window.physics.pause()
        if not self.document.dirty:
            return True
        choice = QMessageBox.question(
            self.window,
            "Alterações não salvas",
            "Salvar as alterações do documento antes de continuar?",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save,
        )
        if choice == QMessageBox.StandardButton.Save:
            return self.save()
        return choice == QMessageBox.StandardButton.Discard

    def new(self):
        if self.maybe_save():
            self.document.reset()
            self.clear_recovery()
            self.window.canvas.reset_view()

    def open(self, path: Path | None = None) -> bool:
        if path is None:
            filename, _ = QFileDialog.getOpenFileName(
                self.window, "Abrir grafo", "", "Grafla (*.grafla);;JSON (*.json)"
            )
            if not filename:
                return False
            path = Path(filename)
        try:
            graph = load(path)
        except (OSError, DocumentError) as error:
            self.window.notify(f"Não foi possível abrir: {error}", error=True)
            logger.warning("Open failed: %s", error)
            return False
        if not self.maybe_save():
            return False
        self.document.reset(graph, path.resolve())
        self.clear_recovery()
        self.add_recent(path)
        self.window.canvas.fit_graph()
        self.window.notify("Documento aberto.")
        return True

    def save(self, save_as: bool = False) -> bool:
        path = None if save_as else self.document.path
        if path is None:
            filename, _ = QFileDialog.getSaveFileName(
                self.window,
                "Salvar grafo",
                str(self.document.path or "Sem título.grafla"),
                "Grafla (*.grafla)",
            )
            if not filename:
                return False
            path = Path(filename)
            if not path.suffix:
                path = path.with_suffix(".grafla")
        try:
            self.document.write(path.resolve())
        except (OSError, ValueError) as error:
            self.window.notify(f"Não foi possível salvar: {error}", error=True)
            logger.exception("Save failed")
            return False
        self.clear_recovery()
        self.add_recent(path)
        self.window.notify("Arquivo salvo.")
        return True

    def add_recent(self, path):
        values = self.recent_paths()
        name = str(path.resolve())
        values = [name] + [value for value in values if value != name]
        self.settings.setValue("recent", values[:10])

    def recent_paths(self):
        values = self.settings.value("recent", [])
        return [values] if isinstance(values, str) else list(values or [])

    def autosave(self):
        if not self.settings.value("autosave", True, type=bool):
            return
        if self.document.dirty or self.window.physics.timer.isActive():
            try:
                save(self.recovery, self.document.graph)
            except (OSError, ValueError) as error:
                logger.warning("Recovery copy failed: %s", error)
                self.window.notify("Não foi possível atualizar a cópia de recuperação.", error=True)

    def clear_recovery(self):
        try:
            self.recovery.unlink(missing_ok=True)
        except OSError:
            logger.warning("Could not remove recovery file", exc_info=True)

    def offer_recovery(self):
        if not self.recovery.exists():
            return
        try:
            graph = load(self.recovery)
        except (OSError, DocumentError):
            logger.warning("Invalid recovery file", exc_info=True)
            self.window.notify("Há uma cópia de recuperação inválida. Consulte o log.", error=True)
            return
        answer = QMessageBox.question(
            self.window,
            "Recuperar trabalho",
            "Foi encontrada uma sessão não salva. Recuperar em um novo documento?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.document.reset(graph)
            self.document.undo_stack.resetClean()
            self.window.canvas.fit_graph()
            self.window.notify("Sessão recuperada. Use Salvar como para preservar o trabalho.")
        else:
            self.clear_recovery()
