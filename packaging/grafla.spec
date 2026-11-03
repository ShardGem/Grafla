# Build on the target OS: uv run pyinstaller --noconfirm packaging/grafla.spec
from pathlib import Path
import sys
from PyInstaller.utils.hooks import collect_data_files, copy_metadata

root = Path(SPECPATH).parent
sys.path.insert(0, str(root / "src"))
from grafla import __version__

version_resource = None
if sys.platform == "win32":
    from PyInstaller.utils.win32.versioninfo import (
        FixedFileInfo, StringFileInfo, StringStruct, StringTable,
        VarFileInfo, VarStruct, VSVersionInfo,
    )
    version = tuple(int(part) for part in __version__.split(".")) + (0,)
    version_resource = VSVersionInfo(
        ffi=FixedFileInfo(filevers=version, prodvers=version, mask=0x3f, flags=0,
                          OS=0x40004, fileType=0x1, subtype=0, date=(0, 0)),
        kids=[StringFileInfo([StringTable("040904B0", [
            StringStruct("ProductName", "Grafla"),
            StringStruct("FileDescription", "Grafla — editor de grafos"),
            StringStruct("FileVersion", __version__),
            StringStruct("ProductVersion", __version__),
            StringStruct("OriginalFilename", "Grafla.exe"),
        ])]), VarFileInfo([VarStruct("Translation", [1033, 1200])])],
    )

a = Analysis([str(root / "main.py")], pathex=[str(root / "src")],
             datas=collect_data_files("grafla") + copy_metadata("PyQt6", recursive=True)
                   + copy_metadata("networkx") + copy_metadata("grafla"), binaries=[], hiddenimports=[],
             excludes=["PySide6", "PyQt5", "tkinter", "matplotlib", "scipy"],
             noarchive=False, optimize=1)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="Grafla", console=False,
          upx=False, debug=False, version=version_resource,
          icon=str(root / "src/grafla/resources/grafla.ico") if sys.platform == "win32" else None)
bundle = COLLECT(exe, a.binaries, a.datas, name="Grafla", upx=False)
