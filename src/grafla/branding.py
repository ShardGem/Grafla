"""As marcas do Grafla, com as cores e proporções dos arquivos do autor."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QIcon, QImageReader, QPixmap

BrandVariant = Literal["symbol", "horizontal", "vertical"]
RESOURCES = Path(__file__).parent / "resources"
BRAND_FILES: dict[BrandVariant, str] = {
    "symbol": "grafla.png",
    "horizontal": "grafla-horizontal.png",
    "vertical": "grafla-vertical.png",
}


@lru_cache(maxsize=32)
def brand_pixmap(
    variant: BrandVariant, width: int, height: int, device_pixel_ratio: float = 1.0
) -> QPixmap:
    """Carrega só o tamanho necessário e reaproveita a imagem nas próximas pinturas."""
    reader = QImageReader(str(RESOURCES / BRAND_FILES[variant]))
    target = QSize(round(width * device_pixel_ratio), round(height * device_pixel_ratio))
    reader.setScaledSize(reader.size().scaled(target, Qt.AspectRatioMode.KeepAspectRatio))
    pixmap = QPixmap.fromImage(reader.read())
    pixmap.setDevicePixelRatio(device_pixel_ratio)
    return pixmap


@lru_cache(maxsize=1)
def application_icon() -> QIcon:
    """Mantém o símbolo nítido na janela, na barra de tarefas e nos diálogos."""
    icon = QIcon()
    source = brand_pixmap("symbol", 256, 256)
    for size in (16, 20, 24, 32, 40, 48, 64, 96, 128, 192, 256):
        icon.addPixmap(
            source.scaled(
                size,
                size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
    return icon
