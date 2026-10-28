"""
OmniEarth SAR Provider Adapter
==============================
Handles search and streaming downloads for Sentinel-1 Synthetic Aperture Radar (SAR)
GRD and RTC products via AWS Open Data STAC.
All-weather, day-and-night cloud penetration.
"""

import os
from typing import List, Optional
import requests

from omniearth.models import AOI, SearchResult, Asset, Category, FilterOptions
from omniearth.providers.base import BaseProvider
from omniearth.config import config


class SARProvider(BaseProvider):
    category = Category.SAR
    name = "sar"

    STAC_SEARCH_URL = "https://earth-search.aws.element84.com/v1/search"
    DEFAULT_COLLECTION = "sentinel-1-grd"

    def search(
        self,
        aoi: AOI,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        filters: Optional[FilterOptions] = None
    ) -> List[SearchResult]:
        limit = filters.limit if filters else 10
        payload = {
            "collections": [self.DEFAULT_COLLECTION],
            "bbox": aoi.bbox,
            "limit": limit
        }

        if start_date and end_date:
            payload["datetime"] = f"{start_date}T00:00:00Z/{end_date}T23:59:59Z"
        elif start_date:
            payload["datetime"] = f"{start_date}T00:00:00Z/.."
        elif end_date:
            payload["datetime"] = f"../{end_date}T23:59:59Z"

        try:
            resp = requests.post(self.STAC_SEARCH_URL, json=payload, timeout=config.timeout)
            resp.raise_for_status()
            data = resp.json()

            results = []
            for feat in data.get("features", []):
                feat_id = feat.get("id")
                props = feat.get("properties", {})
                assets_dict = {}

                for k, a in feat.get("assets", {}).items():
                    assets_dict[k] = Asset(
                        key=k,
                        href=a.get("href"),
                        title=a.get("title", k),
                        media_type=a.get("type"),
                        roles=a.get("roles", [])
                    )

                results.append(SearchResult(
                    id=feat_id,
                    collection=feat.get("collection", self.DEFAULT_COLLECTION),
                    category=self.category,
                    provider="aws_earth_search_s1",
                    datetime=props.get("datetime"),
                    bbox=feat.get("bbox"),
                    properties=props,
                    assets=assets_dict
                ))
            return results
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] SAR STAC search error: {e}")
            return []

    def download(
        self,
        result: SearchResult,
        asset_key: Optional[str] = None,
        outdir: Optional[str] = None,
        resume: bool = True,
        multipart: bool = True,
        max_workers: int = 4
    ) -> str:
        target_dir = outdir or config.default_outdir
        chosen_key = asset_key or ("vv" if "vv" in result.assets else "vh" if "vh" in result.assets else next(iter(result.assets.keys())))
        target_asset = result.assets[chosen_key]
        url = target_asset.href
        ext = os.path.splitext(url)[1].split("?")[0] or ".tif"
        filename = f"{result.id}_{chosen_key}{ext}"
        outpath = os.path.join(target_dir, filename)

        return self._stream_download(
            url=url,
            outpath=outpath,
            desc=f"{result.id[:18]} [{chosen_key}]",
            resume=resume,
            multipart=multipart,
            max_workers=max_workers
        )
