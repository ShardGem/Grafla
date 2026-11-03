"""Composition of the desktop workspace; mathematical state lives elsewhere."""

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtWidgets import (
    QDockWidget,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTabWidget,
    QToolBar,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from grafla.panels import AnalysisPanel, Inspector
from grafla.workspace import BuildPanel, ZoomBar


class ToolStrip(QToolBar):
    """Keep commands accessible when font metrics leave less horizontal space."""

    def __init__(self):
        super().__init__("Ferramentas")
        self.mode_actions = []

    def resizeEvent(self, event):
        super().resizeEvent(event)
        buttons = [self.widgetForAction(action) for action in self.mode_actions]
        for button in buttons:
            button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        compact = self.layout().sizeHint().width() > self.width()
        if compact:
            for button in buttons:
                button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)


def build_shell(window):
    commands = window.commands
    for title, keys in (
        ("Arquivo", ["new", "open", "save", "save_as", "export", "quit"]),
        (
            "Editar",
            [
                "undo",
                "redo",
                "copy",
                "paste",
                "select_all",
                "delete_selection",
                "clear",
                "preferences",
            ],
        ),
        ("Exibir", ["fit", "fit_selection", "reset_view", "zoom_in", "zoom_out", "search"]),
        (
            "Grafo",
            [
                "generate",
                "to_matrix",
                "from_matrix",
                "physics",
                "layout_circular",
                "layout_grid",
                "layout_random",
            ],
        ),
        ("Ajuda", ["about"]),
    ):
        menu = window.menuBar().addMenu(title)
        for key in keys:
            menu.addAction(commands[key])
        if title == "Arquivo":
            window.recent_menu = menu.addMenu("Arquivos recentes")
            window.recent_menu.aboutToShow.connect(window.populate_recent)
    central = QWidget()
    layout = QVBoxLayout(central)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)
    header = QFrame()
    header.setObjectName("Header")
    row = QHBoxLayout(header)
    row.setContentsMargins(16, 10, 12, 10)
    row.setSpacing(10)
    brand = QLabel("GRAFLA")
    brand.setObjectName("Brand")
    row.addWidget(brand)
    row.addSpacing(6)
    window.document_name = QLabel()
    window.document_name.setObjectName("DocumentName")
    window.document_name.setTextFormat(Qt.TextFormat.PlainText)
    window.document_name.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
    row.addWidget(window.document_name, 1)
    window.saved_state = QLabel()
    window.saved_state.setProperty("muted", True)
    row.addWidget(window.saved_state)
    for key in ("undo", "redo", "save"):
        button = QToolButton()
        button.setDefaultAction(commands[key])
        button.setIconSize(QSize(18, 18))
        if key == "save":
            button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        row.addWidget(button)
    search = QPushButton("Buscar  Ctrl+K")
    search.clicked.connect(window.search)
    row.addWidget(search)
    window.panel_button = QToolButton()
    row.addWidget(window.panel_button)
    layout.addWidget(header)

    window.tools = ToolStrip()
    window.tools.setObjectName("ToolStrip")
    window.tools.setMovable(False)
    window.tools.setIconSize(QSize(21, 21))
    window.tools.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
    for key in ("select", "hand", "vertex", "edge", "delete"):
        action = commands[f"tool_{key}"]
        window.tools.addAction(action)
        window.tools.mode_actions.append(action)
        if key == "hand":
            window.tools.addSeparator()
    window.tools.addSeparator()
    from PyQt6.QtWidgets import QMenu

    build = QToolButton()
    build.setText("Construir")
    build.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
    build_menu = QMenu(build)
    for key in ("generate", "from_matrix", "to_matrix"):
        build_menu.addAction(commands[key])
    build.setMenu(build_menu)
    window.tools.addWidget(build)
    layouts = QToolButton()
    layouts.setText("Organizar")
    layouts.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
    menu = QMenu(layouts)
    for key in ("layout_circular", "layout_grid", "layout_random", "fit"):
        menu.addAction(commands[key])
    layouts.setMenu(menu)
    window.tools.addWidget(layouts)
    window.tools.addSeparator()
    window.tools.addAction(commands["physics"])
    window.physics_label = QLabel()
    window.physics_label.setProperty("muted", True)
    window.tools.addWidget(window.physics_label)
    layout.addWidget(window.tools)
    layout.addWidget(window.canvas, 1)
    window.zoom_controls = ZoomBar()
    window.zoom_controls.zoom_requested.connect(
        lambda scale: window.canvas.zoom(scale / window.canvas.transform().m11())
    )
    window.zoom_controls.fit_requested.connect(window.canvas.fit_graph)
    window.zoom_controls.reset_requested.connect(window.canvas.reset_view)
    window.zoom_controls.grid_changed.connect(window.set_grid)
    window.zoom_controls.snap_changed.connect(window.set_snap)
    layout.addWidget(window.zoom_controls)
    window.setCentralWidget(central)

    window.inspector, window.analysis = Inspector(), AnalysisPanel()
    window.building = BuildPanel(window.document.graph, commands)
    window.building.graph_ready.connect(window.replace_graph)
    window.tabs = QTabWidget()
    window.tabs.setObjectName("WorkspaceTabs")
    window.tabs.addTab(window.inspector, "Elemento")
    for widget, title in ((window.analysis, "Análise"), (window.building, "Construir")):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(widget)
        window.tabs.addTab(scroll, title)
    window.workspace = QDockWidget("Explorar o grafo", window)
    window.workspace.setObjectName("workspace")
    window.workspace.setFeatures(
        QDockWidget.DockWidgetFeature.DockWidgetClosable
        | QDockWidget.DockWidgetFeature.DockWidgetMovable
    )
    window.workspace.setWidget(window.tabs)
    window.workspace.setMinimumWidth(330)
    window.workspace.setAllowedAreas(
        Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea
    )
    window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, window.workspace)
    window.resizeDocks([window.workspace], [365], Qt.Orientation.Horizontal)
    window.workspace.toggleViewAction().setText("Painéis")
    window.panel_button.setDefaultAction(window.workspace.toggleViewAction())
    window.results = QPlainTextEdit()
    window.results.setReadOnly(True)
    window.results.setAccessibleName("Relatório completo da análise")
    window.results_dock = QDockWidget("Relatório de análise · texto para copiar", window)
    window.results_dock.setObjectName("results")
    window.results_dock.setWidget(window.results)
    window.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, window.results_dock)
    window.results_dock.hide()
    window.analysis.browser.report_requested.connect(window.results_dock.show)
    view_menu = window.menuBar().actions()[2].menu()
    view_menu.addAction(window.workspace.toggleViewAction())
    view_menu.addAction(window.results_dock.toggleViewAction())
    window.graph_status = QLabel()
    window.statusBar().addPermanentWidget(window.graph_status, 1)
    hint = QLabel("Espaço + arrastar · navegar    Ctrl+roda · zoom")
    hint.setProperty("muted", True)
    window.statusBar().addPermanentWidget(hint)
