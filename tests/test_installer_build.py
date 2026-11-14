import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

from grafla import __version__

spec = importlib.util.spec_from_file_location(
    "criar_instalador", Path(__file__).resolve().parents[1] / "tools" / "criar_instalador.py"
)
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


def bundle_at(root):
    bundle = root / "dist" / "Grafla"
    for relative in (
        "Grafla.exe",
        "_internal/grafla/resources/grafla.ico",
        "_internal/PyQt6/Qt6/plugins/platforms/qwindows.dll",
    ):
        path = bundle / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"arquivo do pacote")
    return bundle


def test_incomplete_bundle_is_rejected_before_creating_an_installer(tmp_path):
    bundle = bundle_at(tmp_path)
    (bundle / "_internal/PyQt6/Qt6/plugins/platforms/qwindows.dll").unlink()
    with pytest.raises(FileNotFoundError, match="qwindows.dll"):
        builder.validar_pacote(bundle)


@pytest.mark.parametrize(
    ("variable", "relative"),
    [("ProgramFiles(x86)", "Inno Setup 6"), ("LOCALAPPDATA", "Programs/Inno Setup 6")],
)
def test_compiler_can_be_found_in_a_path_with_spaces_and_accents(
    tmp_path, monkeypatch, variable, relative
):
    folder = tmp_path / "Árthur" / "Arquivos de Programas"
    compiler = folder / relative / "ISCC.exe"
    compiler.parent.mkdir(parents=True)
    compiler.touch()
    monkeypatch.setattr(builder.shutil, "which", lambda _: None)
    for name in ("ProgramFiles(x86)", "ProgramFiles", "LOCALAPPDATA"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv(variable, str(folder))
    assert builder.localizar_compilador() == compiler


@pytest.mark.parametrize("app_works", [True, False])
def test_installer_compiles_only_after_a_successful_app_test(tmp_path, monkeypatch, app_works):
    root = tmp_path / "Árthur" / "Grafla build"
    root.mkdir(parents=True)
    compiler = root / "Inno Setup 6" / "ISCC.exe"
    commands = []
    output = root / "dist" / "installer" / f"Grafla-{__version__}-Windows-x64-Setup.exe"

    def run(command, **kwargs):
        assert kwargs["cwd"] == root
        commands.append(command)
        if "PyInstaller" in command:
            bundle_at(root)
        else:
            assert command == [
                str(compiler),
                f"/DAppVersion={__version__}",
                str(root / "packaging/grafla.iss"),
            ]
            assert tested
            output.parent.mkdir(parents=True)
            output.write_bytes(b"instalador compilado")
        return SimpleNamespace(returncode=0)

    tested = []

    def smoke(executable):
        assert executable == root / "dist" / "Grafla" / "Grafla.exe"
        tested.append(executable)
        if not app_works:
            raise RuntimeError("O aplicativo não abriu")

    monkeypatch.setattr(builder, "RAIZ", root)
    monkeypatch.setattr(builder.sys, "platform", "win32")
    monkeypatch.setattr(builder.sys, "argv", ["criar_instalador.py"])
    monkeypatch.setattr(builder.sysconfig, "get_platform", lambda: "win-amd64")
    monkeypatch.setattr(builder, "localizar_compilador", lambda _: compiler)
    monkeypatch.setattr(builder, "testar_aplicativo", smoke)
    monkeypatch.setattr(builder.subprocess, "run", run)
    assert builder.main() == (0 if app_works else 1)
    assert len(commands) == (2 if app_works else 1)
    assert output.exists() is app_works
