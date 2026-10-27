"""
OmniEarth Configuration & Credentials Manager
=============================================
Automatically reads configuration from .env files and environment variables.
"""

import os
from pathlib import Path
from typing import Optional, Tuple
from dotenv import load_dotenv


class Config:
    def __init__(self, env_path: Optional[str] = None):
        self._load_environment(env_path)

    def _load_environment(self, custom_path: Optional[str] = None):
        """Attempts to load .env from custom path, current dir, parent dirs, or home."""
        candidates = []
        if custom_path:
            candidates.append(Path(custom_path))
        
        # Current working dir
        candidates.append(Path.cwd() / ".env")
        # Parent directory
        candidates.append(Path.cwd().parent / ".env")
        # System specific agri dir if running in workspace
        candidates.append(Path("/home/ubuntu/Documents/agri/.env"))
        # User home config
        candidates.append(Path.home() / ".omniearth" / ".env")

        for p in candidates:
            if p.exists() and p.is_file():
                load_dotenv(p)
                break

    @property
    def dlr_credentials(self) -> Tuple[Optional[str], Optional[str]]:
        u = os.getenv("DLR_USERNAME") or os.getenv("EOWEB_USERNAME") or os.getenv("DLR_USER")
        p = os.getenv("DLR_PASSWORD") or os.getenv("EOWEB_PASSWORD") or os.getenv("DLR_PASS")
        return u, p

    @property
    def prisma_credentials(self) -> Tuple[Optional[str], Optional[str]]:
        u = os.getenv("PRISMA_USERNAME") or os.getenv("ASI_USERNAME")
        p = os.getenv("PRISMA_PASSWORD") or os.getenv("ASI_PASSWORD")
        return u, p

    @property
    def earthdata_credentials(self) -> Tuple[Optional[str], Optional[str]]:
        u = os.getenv("EARTHDATA_USERNAME") or os.getenv("NASA_USERNAME")
        p = os.getenv("EARTHDATA_PASSWORD") or os.getenv("NASA_PASSWORD")
        return u, p

    @property
    def cdse_credentials(self) -> Tuple[Optional[str], Optional[str]]:
        u = os.getenv("CDSE_USERNAME") or os.getenv("COPERNICUS_USERNAME")
        p = os.getenv("CDSE_PASSWORD") or os.getenv("COPERNICUS_PASSWORD")
        return u, p

    @property
    def s3_credentials(self) -> Tuple[Optional[str], Optional[str]]:
        ak = os.getenv("ACCESS_KEY") or os.getenv("EODATA_ACCESS_KEY") or os.getenv("AWS_ACCESS_KEY_ID")
        sk = os.getenv("SECRET_KEY") or os.getenv("EODATA_SECRET_KEY") or os.getenv("AWS_SECRET_ACCESS_KEY")
        return ak, sk

    @property
    def default_outdir(self) -> str:
        return os.getenv("OMNIEARTH_DEFAULT_OUTDIR", "./downloads")

    @property
    def timeout(self) -> int:
        return int(os.getenv("OMNIEARTH_TIMEOUT_SEC", "30"))

    @property
    def max_retries(self) -> int:
        return int(os.getenv("OMNIEARTH_MAX_RETRIES", "3"))

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get an environment variable value or fallback default."""
        return os.getenv(key, default)


# Global default configuration instance
config = Config()
