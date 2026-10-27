"""
Tests for OmniEarth Configuration Manager
"""

import os
from omniearth.config import Config


def test_config_defaults():
    cfg = Config()
    assert cfg.timeout >= 10
    assert cfg.max_retries >= 1
    assert cfg.default_outdir is not None


def test_config_env_lookup(monkeypatch):
    monkeypatch.setenv("DLR_USERNAME", "test_dlr_user")
    monkeypatch.setenv("DLR_PASSWORD", "test_dlr_pass")
    
    cfg = Config()
    u, p = cfg.dlr_credentials
    assert u == "test_dlr_user"
    assert p == "test_dlr_pass"
    assert cfg.get("DLR_USERNAME") == "test_dlr_user"

