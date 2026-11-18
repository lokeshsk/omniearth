"""
OmniEarth Optical Provider Adapter
==================================
Handles search and streaming downloads for Sentinel-2 L2A and Landsat 8/9
via AWS Registry of Open Data (Element84 Earth Search STAC API).
Zero-cost, cloud-optimized GeoTIFFs (COGs).
"""

import os
from typing import List, Optional
import requests

from omniearth.models import AOI, SearchResult, Asset, Category, FilterOptions
from omniearth.providers.base import BaseProvider
from omniearth.config import config


class OpticalProvider(BaseProvider):
    category = Category.OPTICAL
    name = "optical"

    STAC_SEARCH_URL = "https://earth-search.aws.element84.com/v1/search"
    DEFAULT_COLLECTION = "sentinel-2-l2a"
    TOA_COLLECTION = "sentinel-2-l1c"

    def search(
        self,
        aoi: AOI,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        filters: Optional[FilterOptions] = None
    ) -> List[SearchResult]:
        limit = filters.limit if filters else 10
        level = (filters.level or "sr").lower() if filters and filters.level else "sr"
        target_collection = self.TOA_COLLECTION if level == "toa" else self.DEFAULT_COLLECTION
        collections = [target_collection]
        
        payload = {
            "collections": collections,
            "bbox": aoi.bbox,
            "limit": limit,
            "sortby": [{"field": "properties.datetime", "direction": "desc"}]
        }

        # Date range
        if start_date and end_date:
            payload["datetime"] = f"{start_date}T00:00:00Z/{end_date}T23:59:59Z"
        elif start_date:
            payload["datetime"] = f"{start_date}T00:00:00Z/.."
        elif end_date:
            payload["datetime"] = f"../{end_date}T23:59:59Z"

        # Cloud cover query
        if filters and filters.max_cloud_cover is not None:
            payload["query"] = {
                "eo:cloud_cover": {"lte": filters.max_cloud_cover}
            }

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
                    collection=feat.get("collection", target_collection),
                    category=self.category,
                    provider="aws_earth_search",
                    datetime=props.get("datetime"),
                    bbox=feat.get("bbox"),
                    properties=props,
                    assets=assets_dict
                ))
            results.sort(key=lambda x: x.datetime or "", reverse=True)
            return results[:limit]
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Optical STAC search error: {e}")
            return []

    def get_item(self, item_id: str) -> Optional[SearchResult]:
        """Directly retrieves a specific Sentinel-2 or Landsat STAC item by ID."""
        payload = {"ids": [item_id]}
        try:
            resp = requests.post(self.STAC_SEARCH_URL, json=payload, timeout=config.timeout)
            if resp.status_code != 200:
                return None
            data = resp.json()
            features = data.get("features", [])
            if not features:
                return None
            f = features[0]
            props = f.get("properties", {})
            assets_dict = {
                k: Asset(
                    key=k,
                    href=a.get("href"),
                    title=a.get("title", k),
                    media_type=a.get("type"),
                    roles=a.get("roles", [])
                )
                for k, a in f.get("assets", {}).items()
            }
            return SearchResult(
                id=f.get("id"),
                collection=f.get("collection", "sentinel-2-l2a"),
                category=self.category,
                provider="aws_earth_search",
                datetime=props.get("datetime"),
                bbox=f.get("bbox"),
                cloud_cover=props.get("eo:cloud_cover"),
                properties=props,
                assets=assets_dict
            )
        except requests.exceptions.RequestException:
            return None

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
        
        if not result.assets:
            raise ValueError(f"No downloadable assets found for optical scene '{result.id}'.")

        # Determine asset to download
        # For optical: prefer visual RGB or red band or requested band
        chosen_key = asset_key or ("visual" if "visual" in result.assets else "red")
        if chosen_key not in result.assets:
            chosen_key = next(iter(result.assets.keys()))

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
