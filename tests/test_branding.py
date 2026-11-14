import pytest
from PyQt6.QtCore import QPoint, Qt, QTimer
from PyQt6.QtGui import QImageReader
from PyQt6.QtWidgets import QDialogButtonBox

from grafla.branding import BRAND_FILES, RESOURCES, application_icon, brand_pixmap
from grafla.dialogs import AboutDialog
from grafla.splash import Splash


@pytest.mark.parametrize("variant", ["symbol", "horizontal", "vertical"])
@pytest.mark.parametrize("ratio", [1.0, 1.5, 2.0])
def test_supplied_brand_keeps_proportions_and_transparency_at_each_scale(qapp, variant, ratio):
    source = QImageReader(str(RESOURCES / BRAND_FILES[variant])).size()
    image = brand_pixmap(variant, 180, 120, ratio)
    assert not image.isNull()
    assert image.hasAlphaChannel()
    assert image.devicePixelRatioF() == ratio
    logical = image.deviceIndependentSize()
    assert logical.width() <= 180 and logical.height() <= 120
    assert image.width() / image.height() == pytest.approx(
        source.width() / source.height(), rel=0.015
    )
    assert not application_icon().pixmap(32, 32).isNull()


@pytest.mark.parametrize(("width", "theme"), [(1024, "dark"), (1280, "light")])
def test_brand_stays_at_upper_left_and_opens_about_without_editing(
    window, graph, qtbot, qapp, width, theme
):
    window.document.reset(graph)
    window.settings.setValue("theme", theme)
    window.apply_preferences()
    font = window.font()
    font.setPointSize(12)
    window.setFont(font)
    window.resize(width, 768)
    for visible in (False, True):
        window.workspace.setVisible(visible)
        qtbot.wait(20)
        top_left = window.brand_button.mapTo(window, QPoint())
        assert 0 <= top_left.x() <= 30
        assert top_left.y() < 110
        assert window.brand_button.isVisible()
        brand_right = window.brand_button.mapTo(window, window.brand_button.rect().topRight())
        document_left = window.document_name.mapTo(window, QPoint())
        assert brand_right.x() < document_left.x()
    assert not window.windowIcon().isNull()
    opened = []

    def close_about():
        dialog = qapp.activeModalWidget()
        try:
            assert isinstance(dialog, AboutDialog)
            assert not dialog.brand.pixmap().isNull()
            opened.append(dialog.windowTitle())
            box = dialog.findChild(QDialogButtonBox)
            qtbot.mouseClick(
                box.button(QDialogButtonBox.StandardButton.Close), Qt.MouseButton.LeftButton
            )
        finally:
            if isinstance(dialog, AboutDialog):
                dialog.reject()

    QTimer.singleShot(0, close_about)
    qtbot.mouseClick(window.brand_button, Qt.MouseButton.LeftButton)
    assert opened == ["Sobre o Grafla"]
    assert window.document.graph == graph
    assert window.document.undo_stack.count() == 0


def test_closing_splash_cancels_the_pending_startup_callback(qapp, qtbot):
    splash = Splash(animate=False, minimum_ms=5000)
    qtbot.addWidget(splash)
    splash.show()
    ready = []
    splash.finish_when_ready(lambda: ready.append(True))
    splash.close()
    qtbot.wait(120)
    assert ready == []
    assert not splash.hold.isActive()
