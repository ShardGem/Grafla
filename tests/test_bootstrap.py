import os
import subprocess
import sys

from grafla.splash import Splash


def test_splash_default_is_three_seconds_and_preferences_keep_custom_durations(qapp, tmp_path):
    from PyQt6.QtCore import QSettings

    from grafla.dialogs import PreferencesDialog
    from grafla.splash import splash_duration

    settings = QSettings(str(tmp_path / "splash.ini"), QSettings.Format.IniFormat)
    splash = Splash(animate=False)
    assert splash.minimum_ms == 3000
    splash.close()
    assert splash_duration(settings) == 3000
    dialog = PreferencesDialog(settings)
    assert dialog.splash_duration.value() == 3
    dialog.close()
    legacy = QSettings(str(tmp_path / "legacy.ini"), QSettings.Format.IniFormat)
    legacy.setValue("splash_duration_ms", 1800)
    assert splash_duration(legacy) == 3000
    legacy.setValue("splash_duration_ms", 1800)
    assert splash_duration(legacy) == 1800
    custom = QSettings(str(tmp_path / "custom.ini"), QSettings.Format.IniFormat)
    custom.setValue("splash_duration_ms", 4200)
    assert splash_duration(custom) == 4200


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
    assert (tmp_path / "smoke-icon.png").is_file()
    assert "Traceback" not in result.stderr


def test_installed_version_matches_the_bootstrap_metadata():
    from importlib.metadata import version

    from grafla import __version__

    assert version("grafla") == __version__


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
