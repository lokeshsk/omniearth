"""
OmniEarth Hyperspectral Provider Adapter
========================================
Integrates German EnMAP (DLR EOC Geoservice STAC), Italian PRISMA (ASI),
and NASA EMIT (224 to 285 contiguous hyperspectral bands).
"""

import os
from typing import List, Optional
import requests

from omniearth.models import AOI, SearchResult, Asset, Category, FilterOptions
from omniearth.providers.base import BaseProvider
from omniearth.config import config


class HyperspectralProvider(BaseProvider):
    category = Category.HYPERSPECTRAL
    name = "hyperspectral"

    DLR_STAC_URL = "https://geoservice.dlr.de/eoc/ogc/stac/collections/ENMAP_HSI_L2A/items"
    NASA_EMIT_STAC_URL = "https://cmr.earthdata.nasa.gov/stac/LPCLOUD/search"
    PRISMA_CATALOG_URL = "https://prisma.asi.it/api/v1/search"

    def search(
        self,
        aoi: AOI,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        filters: Optional[FilterOptions] = None
    ) -> List[SearchResult]:
        limit = filters.limit if filters else 10
        results = []

        # 1. Search EnMAP on DLR EOC STAC
        results.extend(self._search_enmap(aoi, start_date, end_date, filters, limit=limit))

        # 2. If limit not reached, also search NASA EMIT on CMR STAC
        if len(results) < limit:
            remaining = limit - len(results)
            results.extend(self._search_emit(aoi, start_date, end_date, remaining))

        # 3. If limit still not reached, search ASI PRISMA
        if len(results) < limit:
            remaining = limit - len(results)
            results.extend(self._search_prisma(aoi, start_date, end_date, remaining))

        return results

    def _search_enmap(
        self,
        aoi: AOI,
        start_date: Optional[str],
        end_date: Optional[str],
        filters: Optional[FilterOptions],
        limit: int
    ) -> List[SearchResult]:
        params = {
            "bbox": aoi.to_bbox_string(),
            "limit": limit
        }
        if start_date and end_date:
            params["datetime"] = f"{start_date}T00:00:00Z/{end_date}T23:59:59Z"
        elif start_date:
            params["datetime"] = f"{start_date}T00:00:00Z/.."
        elif end_date:
            params["datetime"] = f"../{end_date}T23:59:59Z"

        try:
            resp = requests.get(self.DLR_STAC_URL, params=params, timeout=config.timeout)
            if resp.status_code != 200:
                return []
            data = resp.json()
            features = data.get("features", [])

            items = []
            for f in features:
                props = f.get("properties", {})
                cloud = props.get("eo:cloud_cover", 0)
                if filters and filters.max_cloud_cover is not None and cloud > filters.max_cloud_cover:
                    continue

                assets_dict = {}
                for k, a in f.get("assets", {}).items():
                    assets_dict[k] = Asset(
                        key=k,
                        href=a.get("href"),
                        title=a.get("title", k),
                        media_type=a.get("type"),
                        roles=a.get("roles", [])
                    )

                items.append(SearchResult(
                    id=f.get("id"),
                    collection="enmap-hsi-l2a",
                    category=self.category,
                    provider="dlr_enmap",
                    datetime=props.get("datetime"),
                    bbox=f.get("bbox"),
                    properties=props,
                    assets=assets_dict
                ))
            return items
        except requests.exceptions.RequestException:
            return []

    def _search_emit(
        self,
        aoi: AOI,
        start_date: Optional[str],
        end_date: Optional[str],
        limit: int
    ) -> List[SearchResult]:
        payload = {
            "collections": ["EMITL2ARFL_001"],
            "bbox": aoi.bbox,
            "limit": limit
        }
        if start_date and end_date:
            payload["datetime"] = f"{start_date}T00:00:00Z/{end_date}T23:59:59Z"

        try:
            resp = requests.post(self.NASA_EMIT_STAC_URL, json=payload, timeout=config.timeout)
            if resp.status_code != 200:
                return []
            data = resp.json()
            features = data.get("features", [])

            items = []
            for f in features:
                props = f.get("properties", {})
                assets_dict = {}
                for k, a in f.get("assets", {}).items():
                    assets_dict[k] = Asset(
                        key=k,
                        href=a.get("href"),
                        title=a.get("title", k),
                        media_type=a.get("type")
                    )

                items.append(SearchResult(
                    id=f.get("id"),
                    collection="nasa-emit-l2a",
                    category=self.category,
                    provider="nasa_lpdaac",
                    datetime=props.get("datetime"),
                    bbox=f.get("bbox"),
                    properties=props,
                    assets=assets_dict
                ))
            return items
        except requests.exceptions.RequestException:
            return []

    def _search_prisma(
        self,
        aoi: AOI,
        start_date: Optional[str],
        end_date: Optional[str],
        limit: int
    ) -> List[SearchResult]:
        """Queries Italian Space Agency (ASI) PRISMA Hyperspectral archive."""
        params = {
            "bbox": aoi.to_bbox_string(),
            "limit": limit
        }
        if start_date:
            params["start"] = start_date
        if end_date:
            params["end"] = end_date

        try:
            resp = requests.get(self.PRISMA_CATALOG_URL, params=params, timeout=config.timeout)
            if resp.status_code != 200:
                return []
            data = resp.json()
            features = data.get("features", [])

            items = []
            for f in features:
                props = f.get("properties", {})
                assets_dict = {}
                for k, a in f.get("assets", {}).items():
                    assets_dict[k] = Asset(
                        key=k,
                        href=a.get("href", ""),
                        title=a.get("title", k),
                        media_type=a.get("type")
                    )

                items.append(SearchResult(
                    id=f.get("id"),
                    collection="asi-prisma-l2d",
                    category=self.category,
                    provider="asi_prisma",
                    datetime=props.get("datetime"),
                    bbox=f.get("bbox"),
                    properties=props,
                    assets=assets_dict
                ))
            return items
        except requests.exceptions.RequestException:
            return []

    def download(
        self,
        result: SearchResult,
        asset_key: Optional[str] = None,
        outdir: Optional[str] = None
    ) -> str:
        target_dir = outdir or config.default_outdir

        if result.provider == "dlr_enmap":
            u, p = config.dlr_credentials
            if not u or not p:
                raise ValueError("DLR credentials (DLR_USERNAME, DLR_PASSWORD) required in .env for EnMAP downloads.")

            chosen_key = asset_key or ("image" if "image" in result.assets else "thumbnail")
            target_asset = result.assets[chosen_key]
            url = target_asset.href
            ext = os.path.splitext(url)[1].split("?")[0] or ".tif"
            filename = f"{result.id}_{chosen_key}{ext}"
            outpath = os.path.join(target_dir, filename)

            return self._stream_download(
                url=url,
                outpath=outpath,
                auth=(u, p),
                desc=f"{result.id[:18]} [{chosen_key}]"
            )

        elif result.provider == "asi_prisma":
            u, p = config.prisma_credentials
            auth = (u, p) if (u and p) else None
            chosen_key = asset_key or next(iter(result.assets.keys()))
            target_asset = result.assets[chosen_key]
            url = target_asset.href
            ext = os.path.splitext(url)[1].split("?")[0] or ".he5"
            filename = f"{result.id}_{chosen_key}{ext}"
            outpath = os.path.join(target_dir, filename)

            return self._stream_download(
                url=url,
                outpath=outpath,
                auth=auth,
                desc=f"PRISMA {result.id[:16]}"
            )

        elif result.provider == "nasa_lpdaac":
            chosen_key = asset_key or ("browse" if "browse" in result.assets else next(iter(result.assets.keys())))
            target_asset = result.assets[chosen_key]
            url = target_asset.href
            ext = os.path.splitext(url)[1].split("?")[0] or ".nc"
            filename = f"{result.id}_{chosen_key}{ext}"
            outpath = os.path.join(target_dir, filename)

            auth = None
            if "protected" in url:
                u, p = config.earthdata_credentials
                if u and p:
                    auth = (u, p)

            return self._stream_download(
                url=url,
                outpath=outpath,
                auth=auth,
                desc=f"{result.id[:18]} [{chosen_key}]"
            )

        raise ValueError(f"Unknown hyperspectral provider: {result.provider}")
