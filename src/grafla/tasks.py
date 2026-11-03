import logging
import threading

from PyQt6.QtCore import QObject, QRunnable, pyqtSignal

from grafla.algorithms import Analysis, analyze
from grafla.domain import Graph, GraphError

logger = logging.getLogger(__name__)


class TaskSignals(QObject):
    finished = pyqtSignal(int, object)
    failed = pyqtSignal(int, str)


class AnalysisTask(QRunnable):
    def __init__(self, token: int, graph: Graph, name: str, start: int | None, end: int | None):
        super().__init__()
        self.token, self.graph, self.name = token, graph, name
        self.start, self.end = start, end
        self.cancel = threading.Event()
        self.signals = TaskSignals()

    def run(self):
        try:
            result: Analysis = analyze(self.graph, self.name, self.start, self.end, self.cancel)
        except GraphError as error:
            self.signals.failed.emit(self.token, str(error))
        except Exception:
            # Boundary of an asynchronous job: report and retain the traceback.
            logger.exception("Unexpected failure in graph analysis")
            self.signals.failed.emit(
                self.token, "Falha interna na análise. Consulte o log do Grafla."
            )
        else:
            self.signals.finished.emit(self.token, result)
