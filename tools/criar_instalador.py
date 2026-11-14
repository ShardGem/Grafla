"""Gera o pacote do Grafla e o instalador para Windows de 64 bits."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import sysconfig
import tempfile
from pathlib import Path

from grafla import __version__

RAIZ = Path(__file__).resolve().parents[1]


def localizar_compilador(caminho: Path | None = None) -> Path:
    if caminho is not None:
        if caminho.is_file():
            return caminho.resolve()
        raise FileNotFoundError(f"Compilador não encontrado: {caminho}")
    encontrado = shutil.which("ISCC.exe") or shutil.which("ISCC")
    if encontrado:
        return Path(encontrado)
    for pasta in (os.environ.get("ProgramFiles(x86)"), os.environ.get("ProgramFiles")):
        if pasta:
            candidato = Path(pasta) / "Inno Setup 6" / "ISCC.exe"
            if candidato.is_file():
                return candidato
    local = os.environ.get("LOCALAPPDATA")
    if local:
        candidato = Path(local) / "Programs" / "Inno Setup 6" / "ISCC.exe"
        if candidato.is_file():
            return candidato
    raise FileNotFoundError(
        "Instale o Inno Setup 6 em https://jrsoftware.org/isdl.php e execute novamente. "
        "Se estiver em outra pasta, use --iscc com o caminho do ISCC.exe."
    )


def validar_pacote(pasta: Path) -> None:
    for relativo in (
        "Grafla.exe",
        "_internal/grafla/resources/grafla.ico",
        "_internal/PyQt6/Qt6/plugins/platforms/qwindows.dll",
    ):
        arquivo = pasta / relativo
        if not arquivo.is_file() or arquivo.stat().st_size == 0:
            raise FileNotFoundError(f"O pacote está incompleto: falta {arquivo}")


def testar_aplicativo(executavel: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="grafla-teste-") as temporario:
        resultado = subprocess.run(
            [str(executavel), "--smoke-test", "--no-splash", "--data-dir", temporario],
            timeout=30,
            check=False,
        )
        evidencias = Path(temporario)
        if resultado.returncode or not (evidencias / "smoke-icon.png").is_file():
            log = evidencias / "grafla.log"
            detalhes = log.read_text(encoding="utf-8")[-4000:] if log.exists() else "Sem log."
            raise RuntimeError(f"O aplicativo gerado não passou no teste de abertura.\n{detalhes}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iscc", type=Path, help="Caminho do compilador ISCC.exe")
    parser.add_argument(
        "--sem-compilar-app", action="store_true", help="Usar o pacote que já está em dist/Grafla"
    )
    args = parser.parse_args()
    if sys.platform != "win32" or sysconfig.get_platform() != "win-amd64":
        parser.error("Gere o instalador no Windows, usando Python de 64 bits (x64).")
    try:
        compilador = localizar_compilador(args.iscc)
        if not args.sem_compilar_app:
            subprocess.run(
                [sys.executable, "-m", "PyInstaller", "--noconfirm", "packaging/grafla.spec"],
                cwd=RAIZ,
                check=True,
            )
        pacote = RAIZ / "dist" / "Grafla"
        validar_pacote(pacote)
        testar_aplicativo(pacote / "Grafla.exe")
        subprocess.run(
            [str(compilador), f"/DAppVersion={__version__}", str(RAIZ / "packaging/grafla.iss")],
            cwd=RAIZ,
            check=True,
        )
        instalador = RAIZ / "dist" / "installer" / f"Grafla-{__version__}-Windows-x64-Setup.exe"
        if not instalador.is_file() or instalador.stat().st_size == 0:
            raise FileNotFoundError("O compilador não gerou o instalador esperado.")
        print(f"\nInstalador pronto: {instalador}")
        return 0
    except (OSError, RuntimeError, subprocess.SubprocessError) as erro:
        print(f"Não foi possível gerar o instalador: {erro}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
