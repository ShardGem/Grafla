import os
import subprocess
import sys

from grafla.splash import Splash


def test_splash_renders_actual_stage_without_timing_delay(qapp, qtbot, tmp_path):
    splash = Splash(animate=False)
    qtbot.addWidget(splash)
    splash.show()
    splash.report("Preparando editor…", 0.55)
    qapp.processEvents()
    assert splash.status == "Preparando editor…"
    assert splash.progress == 0.55
    assert splash.grab().save(str(tmp_path / "splash.png"))
    splash.close()


def test_actual_entrypoint_starts_and_exits_cleanly(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "grafla", "--smoke-test", "--data-dir", str(tmp_path)],
        env={**os.environ, "QT_QPA_PLATFORM": "offscreen"},
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0, result.stderr
    assert "initialized" in result.stderr
    assert (tmp_path / "smoke-window.png").is_file()
    assert "Traceback" not in result.stderr


def test_smoke_mode_never_erases_an_existing_recovery(tmp_path):
    recovery = tmp_path / "recovery.grafla"
    recovery.write_bytes(b"existing recovery")
    result = subprocess.run(
        [sys.executable, "-m", "grafla", "--smoke-test", "--data-dir", str(tmp_path)],
        env={**os.environ, "QT_QPA_PLATFORM": "offscreen"},
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 1
    assert recovery.read_bytes() == b"existing recovery"
