"""Controles da física. O estado da simulação fica no controlador."""

from dataclasses import asdict, replace

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from grafla.physics import PhysicsParameters

PRESETS = {
    "Equilibrada": PhysicsParameters(),
    "Suave": replace(PhysicsParameters(), damping=0.4, max_speed=4, speed=0.75),
    "Elástica": replace(PhysicsParameters(), stiffness=0.045, damping=0.15, centering=0.001),
}


class ParameterControl(QWidget):
    changed = pyqtSignal()

    def __init__(self, key, label, decimals, step, suffix, description):
        super().__init__()
        self.key = key
        self.title = label
        low, high = PhysicsParameters.LIMITS[key]
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(10)
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 200)
        self.slider.setMinimumWidth(48)
        self.slider.setAccessibleName(label)
        self.spin = QDoubleSpinBox()
        self.spin.setRange(low, high)
        self.spin.setDecimals(decimals)
        self.spin.setSingleStep(step)
        self.spin.setSuffix(suffix)
        self.spin.setKeyboardTracking(False)
        self.spin.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.spin.setMinimumWidth(100)
        self.spin.setAccessibleName(label + " · valor")
        self.setToolTip(description)
        row.addWidget(self.slider, 1)
        row.addWidget(self.spin)
        self.slider.valueChanged.connect(self.from_slider)
        self.spin.valueChanged.connect(self.from_spin)

    def from_slider(self, value):
        low, high = PhysicsParameters.LIMITS[self.key]
        self.spin.setValue(low + (high - low) * value / 200)

    def from_spin(self, value):
        low, high = PhysicsParameters.LIMITS[self.key]
        self.slider.blockSignals(True)
        self.slider.setValue(round((value - low) / (high - low) * 200))
        self.slider.blockSignals(False)
        self.changed.emit()

    def set_value(self, value):
        self.spin.blockSignals(True)
        self.spin.setValue(value)
        self.spin.blockSignals(False)
        self.slider.blockSignals(True)
        low, high = PhysicsParameters.LIMITS[self.key]
        self.slider.setValue(round((value - low) / (high - low) * 200))
        self.slider.blockSignals(False)


class PhysicsPanel(QWidget):
    parameters_changed = pyqtSignal(object)
    enable_requested = pyqtSignal(bool)
    pause_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)
        title = QLabel("MOVIMENTO DO GRAFO")
        title.setProperty("eyebrow", True)
        layout.addWidget(title)
        self.status = QLabel()
        self.status.setObjectName("PhysicsState")
        layout.addWidget(self.status)
        self.feedback = QLabel()
        self.feedback.setWordWrap(True)
        self.feedback.setProperty("muted", True)
        layout.addWidget(self.feedback)
        actions = QHBoxLayout()
        self.enable = QPushButton("Ativar física")
        self.enable.setCheckable(True)
        self.enable.setProperty("primary", True)
        self.enable.toggled.connect(self.enable_requested)
        self.pause = QPushButton("Retomar")
        self.pause.clicked.connect(self.pause_requested)
        actions.addWidget(self.enable, 1)
        actions.addWidget(self.pause, 1)
        layout.addLayout(actions)
        self.preset = QComboBox()
        self.preset.setAccessibleName("Perfil de simulação")
        self.preset.addItems([*PRESETS, "Personalizada"])
        self.preset.textActivated.connect(self.choose_preset)
        preset_form = QFormLayout()
        preset_form.addRow("Perfil", self.preset)
        layout.addLayout(preset_form)
        self.controls = {}
        basic = QGroupBox("Ajustes essenciais")
        basic_form = QFormLayout(basic)
        basic_form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        advanced = QFrame()
        advanced.setObjectName("AdvancedControls")
        advanced_layout = QVBoxLayout(advanced)
        self.advanced = QToolButton()
        self.advanced.setText("Ajustes avançados")
        self.advanced.setCheckable(True)
        self.advanced.setArrowType(Qt.ArrowType.RightArrow)
        self.advanced.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.advanced.setAccessibleName("Mostrar ajustes avançados da física")
        advanced_layout.addWidget(self.advanced)
        self.advanced_content = QWidget()
        advanced_form = QFormLayout(self.advanced_content)
        advanced_form.setContentsMargins(0, 0, 0, 0)
        advanced_form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        advanced_layout.addWidget(self.advanced_content)
        self.advanced_content.hide()
        self.advanced.toggled.connect(self.advanced_content.setVisible)
        self.advanced.toggled.connect(
            lambda checked: self.advanced.setArrowType(
                Qt.ArrowType.DownArrow if checked else Qt.ArrowType.RightArrow
            )
        )
        specs = [
            ("repulsion", "Repulsão", 0, 250, "", "Força que afasta vértices próximos."),
            ("ideal_distance", "Distância ideal", 0, 10, " u", "Comprimento desejado das arestas."),
            ("damping", "Amortecimento", 2, 0.05, "", "Valores maiores reduzem as oscilações."),
            ("speed", "Velocidade", 2, 0.25, "×", "Ritmo da simulação, com passos limitados."),
            (
                "repulsion_distance",
                "Alcance da repulsão",
                0,
                20,
                " u",
                "Distância máxima de interação entre vértices próximos.",
            ),
            ("attraction", "Atração das arestas", 2, 0.1, "×", "Multiplica a força das conexões."),
            (
                "stiffness",
                "Rigidez das conexões",
                3,
                0.005,
                "",
                "Elasticidade ao redor da distância ideal.",
            ),
            ("centering", "Centralização", 4, 0.001, "", "Mantém o grafo perto do centro inicial."),
            ("gravity", "Gravidade", 2, 0.1, "", "Força uniforme. Zero desativa a gravidade."),
            (
                "gravity_angle",
                "Direção da gravidade",
                0,
                15,
                "°",
                "0° direita · 90° baixo · 180° esquerda · 270° cima.",
            ),
            ("max_speed", "Limite de movimento", 1, 0.5, "", "Limita a velocidade e evita saltos."),
            (
                "stability",
                "Limiar de repouso",
                2,
                0.01,
                "",
                "A simulação repousa após 12 passos abaixo deste limite.",
            ),
        ]
        for index, spec in enumerate(specs):
            key, label, *_ = spec
            control = ParameterControl(*spec)
            self.controls[key] = control
            (basic_form if index < 4 else advanced_form).addRow(label, control)
            control.changed.connect(self.submit)
        layout.addWidget(basic)
        layout.addWidget(advanced)
        reset = QPushButton("Restaurar parâmetros padrão")
        reset.clicked.connect(lambda: self.choose_preset("Equilibrada"))
        layout.addWidget(reset)
        note = QLabel(
            "Os ajustes são salvos automaticamente. Vértices fixados permanecem no lugar. "
            "Desfazer ou refazer pausa o movimento; use Retomar para continuar."
        )
        note.setWordWrap(True)
        note.setProperty("muted", True)
        layout.addWidget(note)
        layout.addStretch()
        self.set_parameters(PhysicsParameters())

    def choose_preset(self, label):
        if label in PRESETS:
            parameters = PRESETS[label]
            self.set_parameters(parameters)
            self.parameters_changed.emit(parameters)

    def set_parameters(self, parameters):
        for key, value in asdict(parameters).items():
            self.controls[key].set_value(value)
        self.preset.setCurrentText(
            next((key for key, value in PRESETS.items() if value == parameters), "Personalizada")
        )

    def submit(self):
        parameters = PhysicsParameters(**{k: c.spin.value() for k, c in self.controls.items()})
        self.set_parameters(parameters)
        self.parameters_changed.emit(parameters)

    def refresh(self, controller):
        self.enable.blockSignals(True)
        self.enable.setChecked(controller.enabled)
        self.enable.blockSignals(False)
        self.enable.setText("Desativar física" if controller.enabled else "Ativar física")
        moving = controller.timer.isActive()
        self.status.setText("●  " + controller.state)
        self.pause.setEnabled(controller.enabled and bool(controller.document.graph.vertices))
        self.pause.setText("Pausar" if moving else "Retomar")
        self.feedback.setText(
            "Ajuste os controles durante o movimento."
            if moving
            else (
                "Posições preservadas. Retome quando quiser."
                if controller.paused
                else "Ative a física para organizar as conexões."
                if not controller.enabled
                else "Grafo em repouso. Uma edição pode reativar o movimento."
            )
        )
