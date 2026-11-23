"""
OmniEarth Hyperspectral Provider Adapter
========================================
Integrates German EnMAP (DLR EOC Geoservice STAC) and NASA EMIT
(224 to 285 contiguous hyperspectral bands).
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

    DLR_STAC_URL = "https://geoservice.dlr.de/eoc/ogc/stac/v1/collections/ENMAP_HSI_L2A/items"
    NASA_EMIT_STAC_URL = "https://cmr.earthdata.nasa.gov/stac/LPCLOUD/search"

    def search(
        self,
        aoi: AOI,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        filters: Optional[FilterOptions] = None
    ) -> List[SearchResult]:
        limit = filters.limit if filters else 10

        target = (filters.provider or filters.dataset or "").lower() if filters else ""
        if "enmap" in target:
            return self._search_enmap(aoi, start_date, end_date, filters, limit=limit)[:limit]
        if "emit" in target:
            return self._search_emit(aoi, start_date, end_date, limit=limit)[:limit]

        results = []

        # 1. Search EnMAP on DLR EOC STAC
        results.extend(self._search_enmap(aoi, start_date, end_date, filters, limit=limit))

        # 2. Search NASA EMIT on CMR STAC
        results.extend(self._search_emit(aoi, start_date, end_date, limit=limit))

        # Sort all aggregated hyperspectral scenes chronologically descending (newest first)
        results.sort(key=lambda x: x.datetime or "", reverse=True)
        return results[:limit]

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
            "limit": limit,
            "sortby": [{"field": "properties.datetime", "direction": "desc"}]
        }
        if start_date and end_date:
            payload["datetime"] = f"{start_date}T00:00:00Z/{end_date}T23:59:59Z"
        elif start_date:
            payload["datetime"] = f"{start_date}T00:00:00Z/.."
        elif end_date:
            payload["datetime"] = f"../{end_date}T23:59:59Z"

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

    def get_item(self, item_id: str) -> Optional[SearchResult]:
        """Directly retrieves a specific hyperspectral scene by STAC item ID."""
        # 1. EnMAP (DLR EOC STAC direct item endpoint)
        if item_id.startswith("ENMAP") or "ENMAP" in item_id:
            url = f"https://geoservice.dlr.de/eoc/ogc/stac/v1/collections/ENMAP_HSI_L2A/items/{item_id}"
            try:
                resp = requests.get(url, timeout=config.timeout)
                if resp.status_code == 200:
                    f = resp.json()
                    props = f.get("properties", {})
                    assets_dict = {}
                    for k, a in f.get("assets", {}).items():
                        assets_dict[k] = Asset(
                            key=k,
                            href=a.get("href"),
                            title=a.get("title", k),
                            media_type=a.get("type"),
                            roles=a.get("roles", [])
                        )
                    return SearchResult(
                        id=f.get("id", item_id),
                        collection="enmap-hsi-l2a",
                        category=self.category,
                        provider="dlr_enmap",
                        datetime=props.get("datetime"),
                        bbox=f.get("bbox"),
                        properties=props,
                        assets=assets_dict
                    )
            except requests.exceptions.RequestException:
                pass

        # 2. NASA EMIT (CMR STAC direct item endpoint)
        if item_id.startswith("EMIT") or "EMIT" in item_id:
            url = f"https://cmr.earthdata.nasa.gov/stac/LPCLOUD/collections/EMITL2ARFL_001/items/{item_id}"
            try:
                resp = requests.get(url, timeout=config.timeout)
                if resp.status_code == 200:
                    f = resp.json()
                    props = f.get("properties", {})
                    assets_dict = {}
                    for k, a in f.get("assets", {}).items():
                        assets_dict[k] = Asset(
                            key=k,
                            href=a.get("href"),
                            title=a.get("title", k),
                            media_type=a.get("type"),
                            roles=a.get("roles", [])
                        )
                    return SearchResult(
                        id=f.get("id", item_id),
                        collection="emit-l2a-rfl",
                        category=self.category,
                        provider="nasa_lpdaac",
                        datetime=props.get("datetime"),
                        bbox=f.get("bbox"),
                        properties=props,
                        assets=assets_dict
                    )
            except requests.exceptions.RequestException:
                pass

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
        provider_name = result.provider
        if provider_name == "hyperspectral":
            if "EMIT" in result.id.upper():
                provider_name = "nasa_lpdaac"
            else:
                provider_name = "dlr_enmap"

        if provider_name == "dlr_enmap":
            u, p = config.dlr_credentials
            if not u or not p:
                raise ValueError("DLR credentials (DLR_USERNAME, DLR_PASSWORD) required in .env for EnMAP downloads.")

            chosen_key = result.resolve_asset_key(asset_key)
            if not chosen_key or chosen_key not in result.assets:
                dl_url = f"https://geoservice.dlr.de/eoc/ogc/wcs/v1?SERVICE=WCS&VERSION=2.0.1&REQUEST=GetCoverage&COVERAGEID={result.id}"
                result.assets["image"] = Asset(key="image", href=dl_url, media_type="image/tiff")
                chosen_key = "image"

            target_asset = result.assets[chosen_key]
            url = target_asset.href
            ext = os.path.splitext(url)[1].split("?")[0] or ".tif"
            base_key = os.path.basename(chosen_key) or chosen_key.replace("/", "_")
            if not base_key.endswith(ext):
                base_key = f"{base_key}{ext}"
            filename = base_key if base_key.startswith(result.id) else f"{result.id}_{base_key}"
            outpath = os.path.join(target_dir, filename)

            return self._stream_download(
                url=url,
                outpath=outpath,
                auth=(u, p),
                desc=f"{result.id[:18]} [{chosen_key}]",
                resume=resume,
                multipart=multipart,
                max_workers=max_workers
            )

        elif provider_name == "nasa_lpdaac":
            chosen_key = result.resolve_asset_key(asset_key)
            if not chosen_key or chosen_key not in result.assets:
                dl_url = f"https://data.lpdaac.earthdatacloud.nasa.gov/lp-prod-protected/EMITL2ARFL.001/{result.id}/{result.id}.nc"
                result.assets["data"] = Asset(key="data", href=dl_url, media_type="application/x-netcdf")
                chosen_key = "data"

            target_asset = result.assets[chosen_key]
            url = target_asset.href
            ext = os.path.splitext(url)[1].split("?")[0] or ".nc"
            base_key = os.path.basename(chosen_key) or chosen_key.replace("/", "_")
            if not base_key.endswith(ext):
                base_key = f"{base_key}{ext}"
            filename = base_key if base_key.startswith(result.id) else f"{result.id}_{base_key}"
            outpath = os.path.join(target_dir, filename)

            auth = None
            if "protected" in url:
                u, p = config.earthdata_credentials
                if u and p:
                    auth = (u, p)
                else:
                    import sys
                    print(
                        "Notice: NASA Earthdata credentials (EARTHDATA_USERNAME, EARTHDATA_PASSWORD) not configured in .env. "
                        "Protected EMIT NetCDF cubes require an Earthdata login (free at urs.earthdata.nasa.gov). "
                        "If download fails with HTTP 401, provide credentials or pass '--asset browse' for public preview.",
                        file=sys.stderr
                    )

            return self._stream_download(
                url=url,
                outpath=outpath,
                auth=auth,
                desc=f"{result.id[:18]} [{os.path.basename(chosen_key)}]",
                resume=resume,
                multipart=multipart,
                max_workers=max_workers
            )

        raise ValueError(f"Unknown hyperspectral provider: {result.provider}")
