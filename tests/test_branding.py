import ctypes
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from PyQt6.QtCore import QPoint, Qt, QTimer
from PyQt6.QtGui import QImageReader, QPixmap
from PyQt6.QtWidgets import QDialogButtonBox

from grafla import branding
from grafla.branding import BRAND_FILES, RESOURCES, application_icon, brand_pixmap
from grafla.dialogs import AboutDialog
from grafla.splash import Splash


def test_window_uses_ico_and_header_keeps_the_png(window):
    expected = QPixmap(str(RESOURCES / "grafla.ico")).toImage()
    assert not expected.isNull()
    assert window.windowIcon().pixmap(256, 256).toImage() == expected
    assert (
        window.brand_button.icon().pixmap(256, 256).toImage()
        == brand_pixmap("symbol", 256, 256).toImage()
    )


@pytest.mark.parametrize(("result", "success"), [(0, True), (-2147467259, False)])
def test_windows_taskbar_identity_uses_the_grafla_id(monkeypatch, result, success):
    setter = Mock(return_value=result)
    loader = Mock(return_value=SimpleNamespace(SetCurrentProcessExplicitAppUserModelID=setter))
    monkeypatch.setattr(branding.sys, "platform", "win32")
    monkeypatch.setattr(ctypes, "WinDLL", loader, raising=False)
    assert branding.register_taskbar_identity() is success
    loader.assert_called_once_with("shell32")
    setter.assert_called_once_with("ShardGem.Grafla")
    assert setter.argtypes == [ctypes.c_wchar_p]
    assert setter.restype == ctypes.c_long


def test_missing_windows_shell_does_not_prevent_startup(monkeypatch):
    monkeypatch.setattr(branding.sys, "platform", "win32")
    monkeypatch.setattr(ctypes, "WinDLL", Mock(side_effect=OSError("Indisponível")), raising=False)
    assert not branding.register_taskbar_identity()


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
