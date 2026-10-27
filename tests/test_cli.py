"""
Tests for OmniEarth CLI
"""

import subprocess
import sys


def test_cli_version():
    res = subprocess.run([sys.executable, "-m", "omniearth.cli", "--version"], capture_output=True, text=True)
    assert res.returncode == 0
    assert "omniearth 1.0.0" in res.stdout or "omniearth 1.0.0" in res.stderr


def test_cli_categories():
    res = subprocess.run([sys.executable, "-m", "omniearth.cli", "categories"], capture_output=True, text=True)
    assert res.returncode == 0
    assert "OPTICAL" in res.stdout
    assert "HYPERSPECTRAL" in res.stdout
    assert "WEATHER" in res.stdout


def test_cli_info():
    res = subprocess.run([sys.executable, "-m", "omniearth.cli", "info"], capture_output=True, text=True)
    assert res.returncode == 0
    assert "OmniEarth Engine" in res.stdout
    assert "Lokesh Kumar" in res.stdout
