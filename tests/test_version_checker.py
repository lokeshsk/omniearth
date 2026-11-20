"""
Unit Tests for OmniEarth Version & Update Notification Engine
"""

import sys
import os
import json
import time
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from omniearth.version_checker import (
    is_check_disabled,
    get_cached_version,
    write_cached_version,
    fetch_latest_pypi_version,
    format_update_banner,
    check_for_updates,
    get_whats_new,
    whats_new,
)
import omniearth.version_checker as vc


def test_is_check_disabled_flags():
    # force_check overrides everything
    assert is_check_disabled(json_mode=True, force_check=True) is False
    assert is_check_disabled(force_check=True) is False

    # json_mode suppresses check
    assert is_check_disabled(json_mode=True) is True


def test_is_check_disabled_env_vars(monkeypatch):
    # Opt-out environment variable
    for val in ("1", "true", "yes", "on"):
        monkeypatch.setenv("OMNIEARTH_NO_UPDATE_CHECK", val)
        assert is_check_disabled() is True

    monkeypatch.delenv("OMNIEARTH_NO_UPDATE_CHECK", raising=False)

    # CI environment
    for val in ("1", "true", "yes"):
        monkeypatch.setenv("CI", val)
        assert is_check_disabled() is True

    monkeypatch.delenv("CI", raising=False)


def test_is_check_disabled_tty(monkeypatch):
    monkeypatch.delenv("OMNIEARTH_NO_UPDATE_CHECK", raising=False)
    monkeypatch.delenv("CI", raising=False)

    # When stderr is not a tty
    mock_stderr = MagicMock()
    mock_stderr.isatty.return_value = False
    monkeypatch.setattr(sys, "stderr", mock_stderr)
    assert is_check_disabled() is True

    # When stderr has no isatty attr
    class NoIsatty:
        pass
    monkeypatch.setattr(sys, "stderr", NoIsatty())
    assert is_check_disabled() is True

    # When stderr is a tty
    mock_tty = MagicMock()
    mock_tty.isatty.return_value = True
    monkeypatch.setattr(sys, "stderr", mock_tty)
    assert is_check_disabled() is False


def test_cached_version(tmp_path):
    cache_file = tmp_path / "cache" / "version_check.json"

    # Non-existent file
    assert get_cached_version(cache_file) is None

    # Write cache
    write_cached_version(cache_file, "1.6.0")
    assert cache_file.is_file()

    # Read back fresh cache
    assert get_cached_version(cache_file, ttl=3600) == "1.6.0"

    # Expired cache
    expired_data = {
        "last_checked": time.time() - 7200,
        "latest_version": "1.6.0"
    }
    cache_file.write_text(json.dumps(expired_data), encoding="utf-8")
    assert get_cached_version(cache_file, ttl=3600) is None

    # Corrupt cache file
    cache_file.write_text("NOT_JSON", encoding="utf-8")
    assert get_cached_version(cache_file) is None

    # Write exception handling (e.g. read-only dir)
    with patch.object(Path, "write_text", side_effect=PermissionError("read-only")):
        write_cached_version(cache_file, "1.7.0")  # Should not raise


def test_fetch_latest_pypi_version():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"info": {"version": "2.0.0"}}

    with patch("requests.get", return_value=mock_resp):
        assert fetch_latest_pypi_version() == "2.0.0"

    # 404 response
    mock_resp.status_code = 404
    with patch("requests.get", return_value=mock_resp):
        assert fetch_latest_pypi_version() is None

    # Network error
    with patch("requests.get", side_effect=Exception("network error")):
        assert fetch_latest_pypi_version() is None


def test_format_update_banner():
    cli_banner = format_update_banner("1.5.0", "1.6.0", is_cli=True)
    assert "OmniEarth update available" in cli_banner
    assert "omniearth whatsnew" in cli_banner
    assert "┌" in cli_banner

    sdk_banner = format_update_banner("1.5.0", "1.6.0", is_cli=False)
    assert "[omniearth] A newer version v1.6.0 is available" in sdk_banner
    assert "omniearth.whats_new()" in sdk_banner


def test_check_for_updates(tmp_path, monkeypatch):
    cache_dir = tmp_path / "cache"

    # 1. Disabled check
    with patch("omniearth.version_checker.is_check_disabled", return_value=True):
        assert check_for_updates("1.5.0", cache_dir=cache_dir) is None

    # 2. Force check with newer version (uncached -> PyPI fetch)
    vc._SESSION_NOTIFIED = False
    with patch("omniearth.version_checker.is_check_disabled", return_value=False), \
         patch("omniearth.version_checker.fetch_latest_pypi_version", return_value="1.6.0"), \
         patch("sys.stderr.write") as mock_stderr_write:
        ver = check_for_updates("1.5.0", cache_dir=cache_dir, force_check=True, is_cli=True)
        assert ver == "1.6.0"
        mock_stderr_write.assert_called_once()
        assert vc._SESSION_NOTIFIED is True

    # 3. Already notified guard (without force_check)
    with patch("omniearth.version_checker.is_check_disabled", return_value=False):
        assert check_for_updates("1.5.0", cache_dir=cache_dir, force_check=False) is None

    # Reset guard
    vc._SESSION_NOTIFIED = False

    # 4. Version is older or same (no banner)
    with patch("omniearth.version_checker.is_check_disabled", return_value=False), \
         patch("sys.stderr.write") as mock_stderr_write:
        ver = check_for_updates("2.0.0", cache_dir=cache_dir, force_check=True)
        assert ver is None
        mock_stderr_write.assert_not_called()

    # 5. PyPI fetch fails and not cached
    empty_dir = tmp_path / "empty_cache"
    with patch("omniearth.version_checker.is_check_disabled", return_value=False), \
         patch("omniearth.version_checker.fetch_latest_pypi_version", return_value=None):
        ver = check_for_updates("1.5.0", cache_dir=empty_dir, force_check=True)
        assert ver is None

    # 6. Parse version exception handling
    with patch("omniearth.version_checker.is_check_disabled", return_value=False), \
         patch("omniearth.version_checker.parse_version", side_effect=Exception("parse error")):
        ver = check_for_updates("1.5.0", cache_dir=cache_dir, force_check=True)
        assert ver is None


def test_get_whats_new_from_file(tmp_path, monkeypatch):
    # Test reading valid release notes section
    notes_file = tmp_path / "RELEASE_NOTES.md"
    notes_file.write_text(
        "# OmniEarth Release Notes\n\n### Version 1.6.0\n- Feature A\n- Feature B\n\n---\n# Archive\n",
        encoding="utf-8"
    )

    with patch("omniearth.version_checker.Path.resolve") as mock_resolve:
        mock_resolve.return_value.parent.parent = tmp_path
        with patch.object(Path, "cwd", return_value=tmp_path):
            result = get_whats_new()
            assert "Version 1.6.0" in result
            assert "Feature A" in result

    # Test reading file with no explicit headers (arbitrary text truncation)
    notes_file.write_text("Arbitrary documentation text without keywords.", encoding="utf-8")
    with patch("omniearth.version_checker.Path.resolve") as mock_resolve:
        mock_resolve.return_value.parent.parent = tmp_path
        with patch.object(Path, "cwd", return_value=tmp_path):
            result = get_whats_new()
            assert "Arbitrary documentation text" in result

    # Test file read error fallback
    with patch("omniearth.version_checker.Path.resolve") as mock_resolve:
        mock_resolve.return_value.parent.parent = tmp_path
        with patch.object(Path, "cwd", return_value=tmp_path):
            with patch.object(Path, "read_text", side_effect=IOError("read failed")):
                result = get_whats_new()
                assert "OmniEarth - What's New" in result


def test_get_whats_new_fallback(tmp_path):
    empty_dir = tmp_path / "no_notes"
    empty_dir.mkdir()
    with patch("omniearth.version_checker.Path.resolve") as mock_resolve:
        mock_resolve.return_value.parent.parent = empty_dir
        with patch.object(Path, "cwd", return_value=empty_dir):
            result = get_whats_new()
            assert "OmniEarth - What's New" in result
            assert "NASA EMIT" in result


def test_whats_new_print(capsys):
    whats_new()
    captured = capsys.readouterr()
    assert "OmniEarth - Latest Features & Release Highlights" in captured.out
    assert "Subscribe to releases" in captured.out
