"""
Base Provider Interface for OmniEarth
=====================================
Defines the contract all data provider adapters must satisfy.
"""

import os
import threading
import concurrent.futures
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple
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
        pass  # pragma: no cover

    @abstractmethod
    def download(
        self,
        result: SearchResult,
        asset_key: Optional[str] = None,
        outdir: Optional[str] = None,
        resume: bool = True,
        multipart: bool = True,
        max_workers: int = 4
    ) -> str:
        """Download asset to local disk and return absolute file path."""
        pass  # pragma: no cover

    def _multipart_download(
        self,
        url: str,
        part_path: str,
        total_size: int,
        auth: Optional[tuple] = None,
        headers: Optional[dict] = None,
        max_workers: int = 4,
        desc: str = "Downloading"
    ) -> None:
        """
        Downloads a large file in parallel byte chunks across multiple worker threads.
        """
        # Pre-allocate part_path to total_size
        with open(part_path, "wb") as f:
            f.seek(total_size - 1)
            f.write(b"\0")

        chunk_size = (total_size + max_workers - 1) // max_workers
        ranges = []
        for i in range(max_workers):
            start = i * chunk_size
            end = min(total_size - 1, (i + 1) * chunk_size - 1)
            if start <= end:
                ranges.append((start, end))

        write_lock = threading.Lock()
        pbar_lock = threading.Lock()

        with open(part_path, "r+b") as file_obj:
            with tqdm(
                desc=desc[:26].ljust(26),
                total=total_size,
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
                leave=True
            ) as pbar:
                def download_range(start: int, end: int):
                    req_headers = headers.copy() if headers else {}
                    req_headers["Range"] = f"bytes={start}-{end}"
                    with requests.get(url, auth=auth, headers=req_headers, stream=True, timeout=config.timeout) as resp:
                        resp.raise_for_status()
                        curr = start
                        for chunk in resp.iter_content(chunk_size=64 * 1024):
                            if chunk:
                                with write_lock:
                                    file_obj.seek(curr)
                                    file_obj.write(chunk)
                                curr += len(chunk)
                                with pbar_lock:
                                    pbar.update(len(chunk))

                with concurrent.futures.ThreadPoolExecutor(max_workers=len(ranges)) as executor:
                    futures = [executor.submit(download_range, s, e) for s, e in ranges]
                    for future in concurrent.futures.as_completed(futures):
                        future.result()

    def _write_stream_response(
        self,
        resp: requests.Response,
        part_path: str,
        outpath: str,
        desc: str,
        total_size: int,
        is_resume: bool,
        initial_bytes: int = 0
    ) -> str:
        mode = "ab" if is_resume else "wb"
        with open(part_path, mode) as f, tqdm(
            desc=desc[:26].ljust(26),
            total=total_size,
            initial=initial_bytes,
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
            leave=True
        ) as pbar:
            for chunk in resp.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))

        os.replace(part_path, outpath)
        return os.path.abspath(outpath)

    def _stream_download(
        self,
        url: str,
        outpath: str,
        auth: Optional[tuple] = None,
        headers: Optional[dict] = None,
        desc: str = "Downloading",
        resume: bool = True,
        multipart: bool = True,
        max_workers: int = 4,
        min_multipart_size: int = 10 * 1024 * 1024
    ) -> str:
        """
        Streams a remote URL into a local file with:
        1. Instant skip if the complete file already exists.
        2. Parallel multipart range chunk downloading for large files.
        3. Automatic byte-range resumption for interrupted downloads (.part staging).
        4. Atomic file replacement upon verification.
        """
        os.makedirs(os.path.dirname(os.path.abspath(outpath)), exist_ok=True)
        part_path = f"{outpath}.part"
        req_headers = headers.copy() if headers else {}

        # 1. Probe remote file length and range support via HEAD
        total_size = 0
        supports_ranges = False
        try:
            head_resp = requests.head(url, auth=auth, headers=req_headers, timeout=config.timeout, allow_redirects=True)
            if head_resp.status_code == 200:
                total_size = int(head_resp.headers.get("content-length", 0))
                accept_ranges = head_resp.headers.get("accept-ranges", "").lower()
                supports_ranges = ("bytes" in accept_ranges) or (total_size > 0)
        except Exception:
            pass

        # 2. Check existing complete file
        if os.path.exists(outpath):
            existing_complete = os.path.getsize(outpath)
            if (total_size > 0 and existing_complete == total_size) or (total_size == 0 and existing_complete > 0):
                print(f"File already fully downloaded: {os.path.basename(outpath)}")
                return os.path.abspath(outpath)

        # 3. Check partial download for resumption
        existing_part = os.path.getsize(part_path) if (os.path.exists(part_path) and resume) else 0

        # 4. Check if parallel multipart is applicable
        if (
            multipart
            and max_workers > 1
            and supports_ranges
            and total_size >= min_multipart_size
            and existing_part == 0
        ):
            try:
                self._multipart_download(
                    url=url,
                    part_path=part_path,
                    total_size=total_size,
                    auth=auth,
                    headers=req_headers,
                    max_workers=max_workers,
                    desc=desc
                )
                os.replace(part_path, outpath)
                return os.path.abspath(outpath)
            except Exception:
                if os.path.exists(part_path):
                    try:
                        os.remove(part_path)
                    except OSError:
                        pass
                existing_part = 0

        # 5. Single-stream resumable download
        is_resume = False
        if existing_part > 0 and resume:
            req_headers["Range"] = f"bytes={existing_part}-"

        with requests.get(url, auth=auth, headers=req_headers, stream=True, timeout=config.timeout) as r:
            if r.status_code == 416:
                existing_part = 0
                req_headers.pop("Range", None)
                with requests.get(url, auth=auth, headers=req_headers, stream=True, timeout=config.timeout) as r_fresh:
                    r_fresh.raise_for_status()
                    fresh_total = int(r_fresh.headers.get("content-length", 0))
                    return self._write_stream_response(r_fresh, part_path, outpath, desc, fresh_total, False, 0)

            r.raise_for_status()
            if r.status_code == 206:
                is_resume = True
                stream_total = existing_part + int(r.headers.get("content-length", 0))
            else:
                existing_part = 0
                stream_total = int(r.headers.get("content-length", 0)) or total_size

            return self._write_stream_response(r, part_path, outpath, desc, stream_total, is_resume, existing_part)
