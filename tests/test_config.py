"""
Comprehensive Tests for OmniEarth Configuration Manager
"""

import os
from omniearth.config import Config


def test_config_defaults():
    cfg = Config()
    assert cfg.timeout >= 10
    assert cfg.max_retries >= 1
    assert cfg.default_outdir is not None


def test_config_all_credential_properties(monkeypatch, tmp_path):
    monkeypatch.setenv("DLR_USERNAME", "test_dlr_user")
    monkeypatch.setenv("DLR_PASSWORD", "test_dlr_pass")
    monkeypatch.setenv("PRISMA_USERNAME", "test_prisma_user")
    monkeypatch.setenv("PRISMA_PASSWORD", "test_prisma_pass")
    monkeypatch.setenv("EARTHDATA_USERNAME", "test_ed_user")
    monkeypatch.setenv("EARTHDATA_PASSWORD", "test_ed_pass")
    monkeypatch.setenv("CDSE_USERNAME", "test_cdse_user")
    monkeypatch.setenv("CDSE_PASSWORD", "test_cdse_pass")
    monkeypatch.setenv("ACCESS_KEY", "test_s3_key")
    monkeypatch.setenv("SECRET_KEY", "test_s3_secret")
    
    cfg = Config()
    assert cfg.dlr_credentials == ("test_dlr_user", "test_dlr_pass")
    assert cfg.prisma_credentials == ("test_prisma_user", "test_prisma_pass")
    assert cfg.earthdata_credentials == ("test_ed_user", "test_ed_pass")
    assert cfg.cdse_credentials == ("test_cdse_user", "test_cdse_pass")
    assert cfg.s3_credentials == ("test_s3_key", "test_s3_secret")
    assert cfg.get("DLR_USERNAME") == "test_dlr_user"
    assert cfg.get("NONEXISTENT", "default_val") == "default_val"


def test_config_custom_env_path(tmp_path):
    env_file = tmp_path / "custom.env"
    env_file.write_text("CUSTOM_VAR=custom_value\n")
    cfg = Config(env_path=str(env_file))
    assert cfg.get("CUSTOM_VAR") == "custom_value"
