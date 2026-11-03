from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QDialogButtonBox, QLabel, QHBoxLayout, QCheckBox
)
from PyQt6.QtCore import Qt

# INUTILIZADO!!!
class MatrizDialog(QDialog):
    """
    Dialog para criar uma matriz de adjacência (com pesos) para grafo.
    Suporta opção de direcionado e ponderado.
    """
    def __init__(self, tamanho, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Montar Matriz de Adjacência")
        self.setMinimumSize(400, 400)
        self.tamanho = tamanho

        # Matriz default (0 = sem aresta)
        self.matriz = [[0 for _ in range(tamanho)] for _ in range(tamanho)]

        self._construir_ui()

    def _construir_ui(self):
        layout = QVBoxLayout(self)

        # --- Opções: direcionado / ponderado
        opcoes_layout = QHBoxLayout()
        self.cb_direcionado = QCheckBox("Grafo Direcionado?")
        self.cb_ponderado = QCheckBox("Grafo Ponderado?")
        self.cb_ponderado.setChecked(True)
        opcoes_layout.addWidget(self.cb_direcionado)
        opcoes_layout.addWidget(self.cb_ponderado)
        layout.addLayout(opcoes_layout)

        # --- Tabela de pesos
        self.tabela = QTableWidget(self.tamanho, self.tamanho)
        self.tabela.setHorizontalHeaderLabels([str(i) for i in range(self.tamanho)])
        self.tabela.setVerticalHeaderLabels([str(i) for i in range(self.tamanho)])

        for i in range(self.tamanho):
            for j in range(self.tamanho):
                item = QTableWidgetItem("0")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabela.setItem(i, j, item)

        layout.addWidget(self.tabela)

        # --- Botões
        botoes = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        botoes.accepted.connect(self.accept)
        botoes.rejected.connect(self.reject)
        layout.addWidget(botoes)

        # --- Sinais
        self.cb_direcionado.toggled.connect(self._atualizar_simetria)

    def _atualizar_simetria(self, direcionado):
        """
        Se grafo NÃO direcionado, espelha automaticamente i→j = j→i
        """
        if not direcionado:
            for i in range(self.tamanho):
                for j in range(i + 1, self.tamanho):
                    valor = self.tabela.item(i, j).text()
                    self.tabela.item(j, i).setText(valor)

    def obter_matriz_completa(self):
        """
        Retorna:
            {
                'matriz': [[int]],  # matriz de pesos
                'direcionado': bool,
                'ponderado': bool
            }
        """
        for i in range(self.tamanho):
            for j in range(self.tamanho):
                try:
                    val = int(self.tabela.item(i, j).text())
                    self.matriz[i][j] = max(0, val)
                except:
                    self.matriz[i][j] = 0

        return {
            'matriz': self.matriz,
            'direcionado': self.cb_direcionado.isChecked(),
            'ponderado': self.cb_ponderado.isChecked()
        }
