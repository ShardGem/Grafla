from PyQt6.QtWidgets import (
    QWidget, QToolButton, QHBoxLayout, QLabel, QSizePolicy
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt, QSize

from core.utilitarios.utilitarios import resource_path


class ZoomControls(QWidget):
    def __init__(self, parent_view):
        super().__init__(parent_view)
        self.view = parent_view

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        base = "assets/Escala/"
        specs = [
            ("Icone-Menos", self.diminuir_zoom),
            ("Icone-Escala", self.resetar_zoom),
            ("Icone-Mais", self.aumentar_zoom),
        ]

        self.btns = []
        for nome, callback in specs:
            btn = QToolButton()
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setIconSize(QSize(36, 36))
            btn.setFixedSize(36, 36)
            btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

            if nome == "Icone-Escala":
                btn.setToolTip("Redefinir Zoom")
                btn.setIconSize(QSize(54, 36))  # Largura 1.5x maior
                btn.setFixedSize(54, 36)
                btn.setText("")  # Remove texto do botão

                # Label sobreposto para o texto
                self.center_label = QLabel(btn)
                self.center_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.center_label.setStyleSheet("""
                    background: transparent;
                    color: white;
                    font-weight: 600;
                    font-size: 12px;
                    qproperty-alignment: 'AlignCenter | AlignVCenter';
                """)
                self.center_label.setText("100%")
                self.center_label.setGeometry(0, 1, 55, 36)

            btn.setStyleSheet("""
                QToolButton {
                    background: transparent;
                    background-color: transparent;
                    padding: 0px;
                    margin: 0px;
                    border: none;
                }

            """)
            btn.setContentsMargins(0, 0, 0, 0)

            # monta QIcon com estados
            ico = QIcon()
            ico.addFile(resource_path(f"{base}{nome}.png"), mode=QIcon.Mode.Normal, state=QIcon.State.Off)
            ico.addFile(resource_path(f"{base}{nome}-Hover.png"), mode=QIcon.Mode.Active, state=QIcon.State.Off)
            ico.addFile(resource_path(f"{base}{nome}-Clique.png"), mode=QIcon.Mode.Selected, state=QIcon.State.Off)
            # não usamos checked, logo state On fica igual ao Normal
            btn.setIcon(ico)

            # closures para manter o nome fixo
            def make_press(b=btn, n=nome):
                return lambda: b.setIcon(QIcon(f"{base}{n}-Clique.png"))

            def make_release(b=btn, n=nome):
                return lambda: b.setIcon(QIcon(f"{base}{n}-Hover.png"))

            def make_enter(b=btn, n=nome):
                return lambda e: b.setIcon(QIcon(f"{base}{n}-Hover.png"))

            def make_leave(b=btn, n=nome):
                return lambda e: b.setIcon(QIcon(f"{base}{n}.png"))

            btn.pressed.connect(make_press())
            btn.released.connect(make_release())
            btn.enterEvent = make_enter(btn, nome)
            btn.leaveEvent = make_leave(btn, nome)
            btn.clicked.connect(callback)

            layout.addWidget(btn)
            self.btns.append(btn)

        # posiciona no canto inferior esquerdo
        self.setFixedHeight(36)

        def reposicionar():
            geom = parent_view.viewport().geometry()
            x = geom.left() + 10
            y = geom.bottom() - self.height() - 100
            self.move(x, y)

        reposicionar()
        parent_view.resizeEvent = lambda e: reposicionar()

        # Atualiza posição quando a janela for redimensionada
        self.raise_()

        # atualiza texto do meio via sinal
        self.view.escala_alterada.connect(self._update_center)

    def _update_center(self, escala):
        txt = f"{int(escala * 100)}%"
        self.center_label.setText(txt)  # Atualiza o label

    def definir_escala(self, nova):
        nova = max(0.5, min(3.0, nova))
        atual = self.view.transform().m11()
        if round(nova, 2) == round(atual, 2): return
        centro = self.view.mapToScene(self.view.viewport().rect().center())
        fator = nova / atual
        self.view.scale(fator, fator)
        self.view.centerOn(centro)
        self.view.escala_alterada.emit(self.view.transform().m11())

    def aumentar_zoom(self):
        atual = round(self.view.transform().m11(), 2)
        self.definir_escala(atual + 0.1)

    def diminuir_zoom(self):
        atual = round(self.view.transform().m11(), 2)
        self.definir_escala(atual - 0.1)

    def resetar_zoom(self):
        self.definir_escala(1.0)