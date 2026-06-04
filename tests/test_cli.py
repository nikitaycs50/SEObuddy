import subprocess
import sys

import pytest
from typer.testing import CliRunner

from seobuddy.cli import app, run

runner = CliRunner()


def test_help_shows_branding():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Created by NikitaY.com" in result.output
    assert "https://nikitay.com/" in result.output


def test_missing_url_shows_branding():
    result = subprocess.run(
        [sys.executable, "-m", "seobuddy"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    combined = result.stdout + result.stderr
    assert "Created by NikitaY.com" in combined
    assert "Missing argument 'URL'" in combined


def test_run_adds_branding_on_usage_error(monkeypatch):
    import seobuddy.cli as cli_mod

    branding: list[bool] = []
    monkeypatch.setattr(
        cli_mod,
        "show_branding",
        lambda *args, **kwargs: branding.append(True),
    )
    monkeypatch.setattr(cli_mod, "app", lambda: (_ for _ in ()).throw(SystemExit(2)))

    with pytest.raises(SystemExit) as exc:
        run()
    assert exc.value.code == 2
    assert branding


def test_about_shows_details():
    result = runner.invoke(app, ["--about"])
    assert result.exit_code == 0
    assert "About SEObuddy" in result.output
    assert "How it works" in result.output
    assert "Audit categories" in result.output
    assert "https://github.com/nikitaycs50/SEObuddy" in result.output
    assert "Copyright © 2026 NikitaY.com" in result.output
    assert "Created by NikitaY.com" in result.output


def test_about_does_not_require_url():
    result = runner.invoke(app, ["--about"])
    assert result.exit_code == 0
    assert "Missing argument" not in result.output
