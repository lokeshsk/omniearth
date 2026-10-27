"""
Base Provider Interface for OmniEarth
=====================================
Defines the contract all data provider adapters must satisfy.
"""

import os
from abc import ABC, abstractmethod
from typing import List, Optional
import requests
from tqdm import tqdm

from omniearth.models import AOI, SearchResult, Category, FilterOptions
from omniearth.config import config


class BaseProvider(ABC):
    category: Category
    name: str

    @abstractmethod
    def search(
        self,
        aoi: AOI,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        filters: Optional[FilterOptions] = None
    ) -> List[SearchResult]:
        """Search upstream API for matching data products."""
        pass

    @abstractmethod
    def download(
        self,
        result: SearchResult,
        asset_key: Optional[str] = None,
        outdir: Optional[str] = None
    ) -> str:
        """Download asset to local disk and return absolute file path."""
        pass

    def _stream_download(
        self,
        url: str,
        outpath: str,
        auth: Optional[tuple] = None,
        headers: Optional[dict] = None,
        desc: str = "Downloading"
    ) -> str:
        """
        Streams a remote URL into a local file using atomic writes (.part staging)
        and an interactive tqdm progress bar.
        """
        os.makedirs(os.path.dirname(os.path.abspath(outpath)), exist_ok=True)
        part_path = f"{outpath}.part"

        # Check existing complete file
        req_headers = headers.copy() if headers else {}
        
        with requests.get(url, auth=auth, headers=req_headers, stream=True, timeout=config.timeout) as r:
            r.raise_for_status()
            total_size = int(r.headers.get("content-length", 0))

            # Resume or skip if already completed
            if os.path.exists(outpath) and os.path.getsize(outpath) == total_size and total_size > 0:
                print(f"✔ File already fully downloaded: {os.path.basename(outpath)}")
                return os.path.abspath(outpath)

            with open(part_path, "wb") as f, tqdm(
                desc=desc[:26].ljust(26),
                total=total_size,
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
                leave=False
            ) as pbar:
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))

        # Atomic rename
        os.replace(part_path, outpath)
        return os.path.abspath(outpath)
