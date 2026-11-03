from dataclasses import dataclass

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
    app.setStyleSheet(f"""
        QMainWindow, QDialog {{ background: {theme.background}; }}
        QMenuBar {{ background: {theme.background}; padding: 3px; }}
        QMenuBar::item {{ padding: 5px 9px; background: transparent; }}
        QMenuBar::item:selected, QMenu::item:selected {{ background: {theme.hover}; }}
        QMenu {{ background: {theme.surface}; border: 1px solid {theme.border}; padding: 5px; }}
        QMenu::item {{ padding: 7px 24px 7px 12px; }}
        QToolBar {{ background: {theme.surface}; border: none; spacing: 5px; padding: 6px; }}
        QToolBar::separator {{ background: {theme.border}; width: 1px; height: 1px; margin: 6px; }}
        QToolButton {{ border: 1px solid transparent; border-radius: 5px; padding: 6px; }}
        QToolButton:hover, QPushButton:hover {{ background: {theme.hover}; }}
        QToolButton:checked {{ border: 1px solid {theme.accent}; background: {theme.hover}; }}
        QPushButton {{ background: {theme.panel}; border: 1px solid {theme.border};
                       border-radius: 5px; padding: 7px 12px; }}
        QPushButton[primary="true"] {{ color: {theme.canvas}; background: {theme.accent};
                                          border-color: {theme.accent}; font-weight: 600; }}
        QPushButton[danger="true"] {{ color: {theme.danger}; }}
        QPushButton:disabled {{ color: {theme.muted}; }}
        QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QPlainTextEdit {{
            background: {theme.canvas}; border: 1px solid {theme.border};
            border-radius: 4px; padding: 6px; selection-background-color: {theme.accent}; }}
        QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus,
        QPushButton:focus, QToolButton:focus {{ border: 1px solid {theme.accent}; }}
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
        QLabel#Brand {{ font-size: 19px; font-weight: 700; color: {theme.accent}; }}
        QLabel#DocumentName {{ font-size: 14px; font-weight: 600; }}
        QFrame#Header {{ background: {theme.surface}; border-bottom: 1px solid {theme.border}; }}
        QScrollArea {{ border: none; background: {theme.surface}; }}
        QSplitter::handle {{ background: {theme.border}; }}
        QToolTip {{ padding: 6px; border: 1px solid {theme.border}; }}
    """)
