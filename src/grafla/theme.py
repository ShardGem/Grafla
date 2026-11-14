from dataclasses import dataclass
from pathlib import Path

from PyQt6.QtGui import QColor, QFontDatabase, QPalette
from PyQt6.QtWidgets import QApplication


@dataclass(frozen=True)
class Theme:
    background: str
    surface: str
    panel: str
    canvas: str
    border: str
    text: str
    muted: str
    accent: str
    hover: str
    grid: str
    danger: str
    visited: str = "#7ed8c5"

    @property
    def disabled(self) -> str:
        ink, background = QColor(self.muted), QColor(self.canvas)
        return QColor(
            (ink.red() + background.red()) // 2,
            (ink.green() + background.green()) // 2,
            (ink.blue() + background.blue()) // 2,
        ).name()


DARK = Theme(
    "#171c24",
    "#202733",
    "#252e3b",
    "#11161e",
    "#394455",
    "#edf2f8",
    "#aebacc",
    "#ffad78",
    "#303d4e",
    "#2d3847",
    "#ff929f",
)
LIGHT = Theme(
    "#edf1f7",
    "#ffffff",
    "#f4f6fa",
    "#fafbfd",
    "#bac6d5",
    "#202b3b",
    "#4d6078",
    "#a84617",
    "#e0e7f1",
    "#d6dfe9",
    "#b52842",
    "#17766d",
)


def resolve(mode: str) -> Theme:
    if mode == "system":
        hints = QApplication.styleHints()
        return DARK if hints.colorScheme().name == "Dark" else LIGHT
    return LIGHT if mode == "light" else DARK


def apply(app: QApplication, theme: Theme) -> None:
    app.setStyle("Fusion")
    palette = QPalette()
    for role, color in {
        QPalette.ColorRole.Window: theme.background,
        QPalette.ColorRole.WindowText: theme.text,
        QPalette.ColorRole.Base: theme.canvas,
        QPalette.ColorRole.AlternateBase: theme.panel,
        QPalette.ColorRole.Text: theme.text,
        QPalette.ColorRole.Button: theme.surface,
        QPalette.ColorRole.ButtonText: theme.text,
        QPalette.ColorRole.Highlight: theme.accent,
        QPalette.ColorRole.HighlightedText: theme.canvas,
        QPalette.ColorRole.ToolTipBase: theme.surface,
        QPalette.ColorRole.ToolTipText: theme.text,
        QPalette.ColorRole.PlaceholderText: theme.muted,
    }.items():
        palette.setColor(role, QColor(color))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(theme.muted))
    palette.setColor(
        QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(theme.muted)
    )
    app.setPalette(palette)
    font = QFontDatabase.systemFont(QFontDatabase.SystemFont.GeneralFont)
    font.setPointSizeF(10)
    app.setFont(font)
    accent = QColor(theme.accent)
    accent_wash = f"rgba({accent.red()}, {accent.green()}, {accent.blue()}, 24)"
    resources = Path(__file__).parent / "resources"
    up_arrow = (resources / "chevron-up.svg").as_posix()
    down_arrow = (resources / "chevron-down.svg").as_posix()
    app.setStyleSheet(f"""
        QMainWindow, QDialog {{ background: {theme.background}; }}
        QMenuBar {{ background: {theme.background}; padding: 3px; }}
        QMenuBar::item {{ padding: 5px 9px; background: transparent; }}
        QMenuBar::item:selected, QMenu::item:selected {{ background: {theme.hover}; }}
        QMenu {{ background: {theme.surface}; border: 1px solid {theme.border}; padding: 5px; }}
        QMenu::item {{ padding: 7px 24px 7px 12px; }}
        QToolBar {{ background: {theme.surface}; border: none; spacing: 5px; padding: 6px; }}
        QToolBar#DocumentBar {{ padding: 0; spacing: 0; border: none; }}
        QToolBar::separator {{ background: {theme.border}; width: 1px; height: 1px; margin: 6px; }}
        QToolButton {{ border: 1px solid transparent; border-radius: 7px; padding: 6px; }}
        QToolButton:hover, QPushButton:hover {{ background: {theme.hover}; }}
        QToolButton:checked {{ border: 1px solid {theme.accent}; background: {theme.hover}; }}
        QToolBar#ToolStrip {{ background: {theme.background}; padding: 6px 12px; border-bottom: 1px solid {theme.border}; }}
        QToolBar#ToolStrip QToolButton {{ padding: 7px 10px; }}
        QToolBar#ToolStrip QToolButton:checked {{ color: {theme.accent}; background: {accent_wash};
            border: 1px solid {theme.accent}; font-weight: 600; }}
        QToolButton:disabled {{ color: {theme.muted}; background: transparent; border-color: transparent; }}
        QToolButton:pressed, QPushButton:pressed {{ background: {theme.border}; }}
        QFrame#ModeContext {{ background: {theme.surface}; border-bottom: 1px solid {theme.border}; }}
        QFrame#ModeContext QLabel {{ font-size: 11px; }}
        QFrame#ModeContext QPushButton {{ padding: 2px 8px; font-size: 11px; }}
        QFrame#CanvasControls {{ background: {theme.surface}; border-top: 1px solid {theme.border}; }}
        QSlider::groove:horizontal {{ height: 3px; background: {theme.border}; border-radius: 1px; }}
        QSlider::sub-page:horizontal {{ background: {theme.accent}; }}
        QSlider::handle:horizontal {{ background: {theme.accent}; width: 12px; margin: -5px 0; border-radius: 6px; }}
        QListWidget#RouteList {{ background: {theme.canvas}; border: 1px solid {theme.border}; border-radius: 5px; }}
        QListWidget#RouteList::item {{ padding: 9px 8px; border-bottom: 1px solid {theme.border}; }}
        QListWidget#RouteList::item:selected {{ background: {theme.hover}; color: {theme.accent}; border-left: 3px solid {theme.accent}; }}
        QListWidget#RouteList::item:hover {{ background: {theme.panel}; }}
        QLabel#ResultMetric {{ font-size: 15px; font-weight: 600; }}
        QPushButton {{ background: {theme.panel}; border: 1px solid {theme.border};
                       border-radius: 7px; padding: 7px 12px; }}
        QPushButton[primary="true"] {{ color: {theme.canvas}; background: {theme.accent};
                                          border-color: {theme.accent}; font-weight: 600; }}
        QPushButton[danger="true"] {{ color: {theme.danger}; }}
        QPushButton:disabled {{ color: {theme.muted}; }}
        QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QPlainTextEdit {{
            background: {theme.canvas}; border: 1px solid {theme.border};
            border-radius: 4px; padding: 6px; selection-background-color: {theme.accent}; }}
        QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus,
        QPushButton:focus, QToolButton:focus {{ border: 1px solid {theme.accent}; }}
        QLineEdit:disabled, QDoubleSpinBox:disabled {{ color: {theme.muted}; background: {theme.panel}; }}
        QSpinBox::up-button, QDoubleSpinBox::up-button {{ subcontrol-origin: border;
            subcontrol-position: top right; width: 16px; border-left: 1px solid {theme.border};
            border-bottom: 1px solid {theme.border}; border-top-right-radius: 4px; }}
        QSpinBox::down-button, QDoubleSpinBox::down-button {{ subcontrol-origin: border;
            subcontrol-position: bottom right; width: 16px; border-left: 1px solid {theme.border};
            border-bottom-right-radius: 4px; }}
        QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{ image: url("{up_arrow}"); width: 8px; height: 5px; }}
        QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{ image: url("{down_arrow}"); width: 8px; height: 5px; }}
        QSpinBox::up-button:hover, QSpinBox::down-button:hover,
        QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {{ background: {theme.hover}; }}
        QCheckBox {{ spacing: 8px; padding: 4px 0; }}
        QDockWidget::title {{ background: {theme.panel}; padding: 8px; font-weight: 600; }}
        QTabWidget::pane {{ border: none; background: {theme.surface}; }}
        QTabBar::tab {{ padding: 10px 12px; background: {theme.background}; color: {theme.muted}; }}
        QTabBar::tab:selected {{ color: {theme.text}; background: {theme.surface};
                                border-bottom: 2px solid {theme.accent}; }}
        QGroupBox {{ border: 1px solid {theme.border}; border-radius: 5px;
                    margin-top: 14px; padding: 12px; font-weight: 600; }}
        QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 4px; }}
        QHeaderView::section {{ background: {theme.panel}; padding: 6px; border: none; }}
        QTableView {{ background: {theme.canvas}; gridline-color: {theme.border}; }}
        QStatusBar {{ background: {theme.surface}; border-top: 1px solid {theme.border}; }}
        QStatusBar::item {{ border: none; }}
        QLabel[muted="true"] {{ color: {theme.muted}; }}
        QLabel[eyebrow="true"] {{ color: {theme.muted}; font-size: 11px; font-weight: 600; }}
        QLabel#PhysicsState {{ color: {theme.accent}; font-size: 20px; font-weight: 600; }}
        QFrame#AdvancedControls {{ border: 1px solid {theme.border}; border-radius: 5px; }}
        QToolButton#BrandButton, QToolButton#BrandButton:focus {{ padding: 4px;
            border: 1px solid transparent; background: transparent; border-radius: 10px; }}
        QToolButton#BrandButton:hover, QToolButton#BrandButton:pressed {{
            border-color: {theme.accent}; background: {theme.hover}; }}
        QFrame#BrandCard {{ background: #18212d; border: 1px solid #303e50;
                            border-radius: 12px; }}
        QLabel#DocumentName {{ font-size: 14px; font-weight: 600; }}
        QFrame#Header {{ background: {theme.surface}; border-bottom: 1px solid {theme.border}; }}
        QScrollArea {{ border: none; background: {theme.surface}; }}
        QScrollBar:vertical {{ background: {theme.background}; width: 10px; margin: 0; }}
        QScrollBar::handle:vertical {{ background: {theme.border}; min-height: 28px; border-radius: 4px; }}
        QScrollBar::handle:vertical:hover {{ background: {theme.muted}; }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
        QSplitter::handle {{ background: {theme.border}; }}
        QToolTip {{ padding: 6px; border: 1px solid {theme.border}; }}
    """)
