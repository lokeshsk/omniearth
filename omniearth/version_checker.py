"""
OmniEarth Version & Update Notification Engine
==============================================
Provides non-blocking, cached version checks against PyPI and npm registries
to inform users of new releases and upcoming features across SDK and CLI usage.
"""

from __future__ import annotations

import sys
import os
import time
import json
from pathlib import Path
from typing import Optional, Dict, Any

try:
    from packaging.version import parse as parse_version
except ImportError:  # pragma: no cover
    def parse_version(v: str):
        parts = []
        for x in v.strip().split("."):
            try:
                parts.append(int(x))
            except ValueError:
                parts.append(x)
        return tuple(parts)

DEFAULT_CACHE_DIR = Path.home() / ".cache" / "omniearth"
CACHE_FILE_NAME = "version_check.json"
PYPI_JSON_URL = "https://pypi.org/pypi/omniearth/json"
CHECK_INTERVAL_SECONDS = 86400.0  # 24 hours

# In-process guard so we only notify once per Python runtime session
_SESSION_NOTIFIED = False


def is_check_disabled(json_mode: bool = False, force_check: bool = False) -> bool:
    """Determine whether the version check should be suppressed."""
    if force_check:
        return False
    if json_mode:
        return True

    # Opt-out environment variable
    opt_out = os.environ.get("OMNIEARTH_NO_UPDATE_CHECK", "").strip().lower()
    if opt_out in ("1", "true", "yes", "on"):
        return True

    # CI environments (GitHub Actions, GitLab CI, etc.)
    if os.environ.get("CI", "").strip().lower() in ("1", "true", "yes"):
        return True

    # Non-interactive / headless terminals (e.g. cron, redirected output)
    if not hasattr(sys.stderr, "isatty") or not sys.stderr.isatty():
        return True

    return False


def get_cached_version(cache_file: Path, ttl: float = CHECK_INTERVAL_SECONDS) -> Optional[str]:
    """Retrieve the cached version if fresh."""
    try:
        if cache_file.is_file():
            data = json.loads(cache_file.read_text(encoding="utf-8"))
            last_checked = float(data.get("last_checked", 0))
            if (time.time() - last_checked) < ttl:
                return data.get("latest_version")
    except Exception:
        pass
    return None


def write_cached_version(cache_file: Path, latest_version: str) -> None:
    """Store the checked version in local cache."""
    try:
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "last_checked": time.time(),
            "latest_version": latest_version,
        }
        cache_file.write_text(json.dumps(data), encoding="utf-8")
    except Exception:
        pass


def fetch_latest_pypi_version(timeout: float = 1.5) -> Optional[str]:
    """Query PyPI JSON API for latest package version with short timeout."""
    import requests
    try:
        resp = requests.get(PYPI_JSON_URL, timeout=timeout)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("info", {}).get("version")
    except Exception:
        pass
    return None


def format_update_banner(current_version: str, latest_version: str, is_cli: bool = True) -> str:
    """Render a clean, non-intrusive terminal notification banner."""
    if is_cli:
        lines = [
            f"OmniEarth update available: {current_version} -> {latest_version}",
            "To view new features: run 'omniearth whatsnew'",
            "To upgrade: pip install --upgrade omniearth (or 'uv pip install -U omniearth')",
            "Release Notes: https://github.com/lokeshsk/omniearth/releases",
        ]
        max_len = max(len(l) for l in lines) + 2
        border_top = "┌" + "─" * max_len + "┐"
        border_bot = "└" + "─" * max_len + "┘"
        content = "\n".join(f"│  {l.ljust(max_len - 2)}│" for l in lines)
        return f"\n{border_top}\n{content}\n{border_bot}\n"
    else:
        return (
            f"[omniearth] A newer version v{latest_version} is available (installed: v{current_version}).\n"
            f"Run 'omniearth.whats_new()' or visit https://github.com/lokeshsk/omniearth/releases to view new features.\n"
        )


def check_for_updates(
    current_version: str,
    cache_dir: Optional[Path] = None,
    json_mode: bool = False,
    force_check: bool = False,
    is_cli: bool = True,
    timeout: float = 1.5,
) -> Optional[str]:
    """
    Perform a non-blocking check for omniearth updates on PyPI.
    Prints a notification banner to sys.stderr if a newer version is available.
    """
    global _SESSION_NOTIFIED

    if is_check_disabled(json_mode=json_mode, force_check=force_check):
        return None

    if _SESSION_NOTIFIED and not force_check:
        return None

    cache_path = (cache_dir or DEFAULT_CACHE_DIR) / CACHE_FILE_NAME
    latest_version = get_cached_version(cache_path)

    if not latest_version:
        latest_version = fetch_latest_pypi_version(timeout=timeout)
        if latest_version:
            write_cached_version(cache_path, latest_version)

    if latest_version:
        try:
            if parse_version(latest_version) > parse_version(current_version):
                banner = format_update_banner(current_version, latest_version, is_cli=is_cli)
                sys.stderr.write(banner)
                sys.stderr.flush()
                _SESSION_NOTIFIED = True
                return latest_version
        except Exception:
            pass

    return None


def get_whats_new() -> str:
    """
    Retrieve formatted release notes and new features summary from local or remote changelog.
    """
    search_paths = [
        Path(__file__).resolve().parent.parent / "RELEASE_NOTES.md",
        Path.cwd() / "RELEASE_NOTES.md",
        Path(__file__).resolve().parent.parent / "CHANGELOG.md",
    ]
    for sp in search_paths:
        if sp.is_file():
            try:
                content = sp.read_text(encoding="utf-8")
                # Normalize line breaks and split by top-level headers (# )
                if content.startswith("# "):
                    parts = ("\n" + content).split("\n# ")
                else:
                    parts = content.split("\n# ")
                
                for section in parts:
                    clean = section.strip()
                    if clean and any(term in clean.lower() for term in ["release notes", "highlights"]):
                        return "# " + clean.split("\n---")[0].strip()
                return content[:2000]
            except Exception:
                pass

    # Fallback standard highlights
    return (
        "# OmniEarth - What's New\n\n"
        "- Direct Hyperspectral Provider & Dataset Routing (NASA EMIT, DLR EnMAP)\n"
        "- Interchangeable Elevation Flags (Copernicus DEM, SRTM, ALOS)\n"
        "- Universal Semantic Asset Aliasing & Interactive Terminal Picker (-i)\n"
        "- Dedicated Scene Folder Packaging (--folder) & Direct ZIP Bundling (--zip)\n"
        "- Parallel Asset URL Deduplication\n\n"
        "Full Release Notes: https://github.com/lokeshsk/omniearth/releases\n"
        "Changelog: https://github.com/lokeshsk/omniearth/blob/main/CHANGELOG.md"
    )


def whats_new() -> None:
    """Print the latest OmniEarth release notes and feature highlights to stdout."""
    summary = get_whats_new()
    print("=" * 76)
    print(" OmniEarth - Latest Features & Release Highlights")
    print("=" * 76)
    print(summary)
    print("=" * 76)
    print("Subscribe to releases: https://github.com/lokeshsk/omniearth/releases")
    print("PyPI RSS: https://pypi.org/rss/project/omniearth/releases.xml")
    print("=" * 76)
