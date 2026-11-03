from PyQt6.QtCore import QObject, QThreadPool, QTimer

from grafla.algorithms import format_result
from grafla.tasks import AnalysisTask


class AnalysisController(QObject):
    def __init__(self, window):
        super().__init__(window)
        self.document, self.physics, self.canvas = window.document, window.physics, window.canvas
        self.analysis, self.results = window.analysis, window.results
        self.results_dock = window.results_dock
        self.notify = window.notify
        self.task = None
        self.task_token = 0
        self.result = None
        self.result_index = 0
        self.tree_focus = False
        self.pool = QThreadPool(self)
        self.pool.setMaxThreadCount(2)
        self.playback = QTimer(self)
        self.playback.timeout.connect(self.advance_playback)

    def run_analysis(self):
        self.physics.pause()
        self.clear_analysis()
        self.task_token += 1
        self.task_revision = self.document.revision
        self.task = AnalysisTask(
            self.task_token,
            self.document.graph.clone(),
            self.analysis.algorithm.currentData(),
            self.analysis.origin.currentData(),
            self.analysis.destination.currentData(),
        )
        self.task.signals.finished.connect(self.analysis_finished)
        self.task.signals.failed.connect(self.analysis_failed)
        self.analysis.status.setText("Executando análise…")
        self.analysis.cancel.setEnabled(True)
        self.analysis.run.setEnabled(False)
        self.analysis.run.setText("Analisando…")
        self.pool.start(self.task)

    def cancel_analysis(self):
        if self.task:
            self.task.cancel.set()
            self.analysis.status.setText("Cancelamento solicitado…")
        self.playback.stop()
        self.analysis.play.setText("Reproduzir")

    def stop_execution(self):
        self.cancel_analysis()
        if self.result is not None:
            self.result_index = 0
            self.canvas.highlight(set(), set())
            self.analysis.position.setText(
                "Visualização parada. Use Reiniciar para voltar ao início."
            )

    def restart(self):
        self.playback.stop()
        self.analysis.play.setText("Reproduzir")
        self.result_index = 0
        self.tree_focus = False
        self.render_result()

    def clear_analysis(self, stale=False):
        had_result = self.result is not None or self.task is not None
        self.cancel_analysis()
        self.task_token += 1
        self.task = None
        self.result = None
        self.result_index = 0
        self.tree_focus = False
        self.canvas.highlight(set(), set())
        self.analysis.set_playback(False)
        self.analysis.position.setText("Sem execução")
        self.analysis.cancel.setEnabled(False)
        self.analysis.run.setEnabled(bool(self.document.graph.vertices))
        self.analysis.run.setText("Executar análise")
        self.analysis.browser.clear()
        self.results.clear()
        self.analysis.status.setText(
            "O grafo mudou. Execute novamente."
            if stale and had_result
            else "Escolha um algoritmo e execute."
        )

    def analysis_finished(self, token, result):
        if token != self.task_token or self.task_revision != self.document.revision:
            return
        self.task = None
        self.result = result
        self.analysis.cancel.setEnabled(False)
        self.analysis.run.setEnabled(True)
        self.analysis.run.setText("Executar análise")
        self.analysis.status.setText(("Cancelado. " if result.cancelled else "") + result.message)
        self.results.setPlainText(format_result(self.document.graph, result))
        self.analysis.browser.set_result(self.document.graph, result)
        playback = bool(result.paths or result.steps) and result.algorithm != "mst"
        self.analysis.set_playback(playback)
        self.analysis.cancel.setEnabled(playback)
        self.render_result()

    def analysis_failed(self, token, message):
        if token == self.task_token:
            self.task = None
            self.analysis.cancel.setEnabled(False)
            self.analysis.run.setEnabled(True)
            self.analysis.run.setText("Executar análise")
            self.notify(message, error=True)

    def render_result(self):
        if self.result is None:
            return
        result = self.result
        if result.algorithm == "mst":
            if self.tree_focus and result.paths:
                self.canvas.highlight_path(result.paths[self.result_index])
                self.analysis.browser.set_index(self.result_index)
                self.analysis.position.setText(
                    f"Aresta {self.result_index + 1} da floresta · custo {result.costs[self.result_index]:g}"
                )
                return
            edges = set()
            for a, b in result.paths:
                key = self.canvas.pairs.get((a, b), self.canvas.pairs.get((b, a)))
                if key is not None:
                    edges.add(key)
            self.canvas.highlight(set(self.document.graph.vertices), edges)
            self.analysis.position.setText(
                f"Floresta · {len(edges)} arestas · custo {sum(result.costs):g}"
            )
            self.analysis.browser.metric.setText(
                f"Custo {sum(result.costs):g} · {len(edges)} arestas"
            )
            return
        count = len(result.paths or result.steps)
        if not count:
            self.canvas.highlight(set(), set())
            return
        self.result_index = max(0, min(count - 1, self.result_index))
        index = self.result_index
        self.analysis.browser.set_index(index)
        if result.paths:
            self.canvas.highlight_path(result.paths[index])
            self.analysis.position.setText(
                f"Caminho {index + 1} de {count} · custo {result.costs[index]:g}"
            )
        else:
            nodes = (
                set(result.steps[index])
                if result.algorithm == "components"
                else {key for step in result.steps[: index + 1] for key in step}
            )
            edges = {key for step in result.step_edges[: index + 1] for key in step}
            self.canvas.highlight(
                nodes, edges, current=result.steps[index][0] if result.steps[index] else None
            )
            frontier = result.frontier[index] if result.frontier else []
            self.analysis.position.setText(
                f"Passo {index + 1} de {count} · atual {result.steps[index][:8]}"
                + (" …" if len(result.steps[index]) > 8 else "")
                + "\n"
                + (f"Fila/pilha (até 30): {frontier}" if result.frontier else "")
            )

    def navigate_result(self, delta):
        self.playback.stop()
        self.analysis.play.setText("Reproduzir")
        self.result_index += delta
        self.render_result()

    def select_result(self, index):
        if self.result is None:
            return
        count = len(self.result.paths or self.result.steps)
        if not count:
            return
        self.playback.stop()
        self.analysis.play.setText("Reproduzir")
        self.result_index = max(0, min(count - 1, index))
        self.tree_focus = self.result.algorithm == "mst"
        self.render_result()

    def parameters_changed(self, *args):
        had_result = self.result is not None or self.task is not None
        self.clear_analysis()
        if had_result:
            self.analysis.status.setText(
                "Parâmetros alterados. Execute novamente para atualizar o resultado."
            )

    def update_speed(self, *args):
        self.playback.setInterval(1100 - self.analysis.speed.value() * 100)

    def toggle_playback(self):
        if self.playback.isActive():
            self.playback.stop()
            self.analysis.play.setText("Reproduzir")
        elif self.result:
            if self.result_index >= len(self.result.paths or self.result.steps) - 1:
                self.result_index = 0
            self.render_result()
            self.update_speed()
            self.playback.start()
            self.analysis.play.setText("Pausar")

    def advance_playback(self):
        if not self.result or self.result_index + 1 >= len(self.result.paths or self.result.steps):
            self.playback.stop()
            self.analysis.play.setText("Reproduzir")
            return
        self.result_index += 1
        self.render_result()
