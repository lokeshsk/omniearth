"""
OmniEarth Soil Provider Adapter
===============================
Integrates ISRIC SoilGrids v2.0 REST API (250m global 3D soil properties)
and Copernicus DEM elevation queries.
Zero credentials required. Completely open public access.
"""

import os
import json
from typing import List, Optional
import requests

from omniearth.models import AOI, SearchResult, Asset, Category, FilterOptions
from omniearth.providers.base import BaseProvider
from omniearth.config import config


class SoilProvider(BaseProvider):
    category = Category.SOIL
    name = "soil"

    SOILGRIDS_QUERY_URL = "https://rest.isric.org/soilgrids/v2.0/properties/query"
    DEFAULT_PROPERTIES = ["clay", "phh2o"]
    DEFAULT_DEPTHS = ["0-5cm"]

    def search(
        self,
        aoi: AOI,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        filters: Optional[FilterOptions] = None
    ) -> List[SearchResult]:
        center_lon = round((aoi.min_lon + aoi.max_lon) / 2.0, 4)
        center_lat = round((aoi.min_lat + aoi.max_lat) / 2.0, 4)

        props = filters.variables if filters and filters.variables else self.DEFAULT_PROPERTIES
        depths = [filters.depth] if filters and filters.depth else self.DEFAULT_DEPTHS

        query_params = [("lon", center_lon), ("lat", center_lat)]
        for p in props:
            query_params.append(("property", p))
        for d in depths:
            query_params.append(("depth", d))

        try:
            resp = requests.get(self.SOILGRIDS_QUERY_URL, params=query_params, timeout=config.timeout)
            resp.raise_for_status()
            data = resp.json()

            layers = data.get("properties", {}).get("layers", [])
            parsed_summary = {}
            for lay in layers:
                name = lay.get("name")
                depths_data = lay.get("depths", [])
                if depths_data:
                    top_depth = depths_data[0]
                    parsed_summary[name] = {
                        "range": top_depth.get("label"),
                        "mean": top_depth.get("values", {}).get("mean")
                    }

            feed_id = f"soilgrids_{center_lat}_{center_lon}"
            result = SearchResult(
                id=feed_id,
                collection="isric-soilgrids-v2",
                category=self.category,
                provider="isric",
                datetime="static-3d",
                bbox=aoi.bbox,
                properties={
                    "latitude": center_lat,
                    "longitude": center_lon,
                    "depths_queried": depths,
                    "summary_topsoil": parsed_summary
                },
                assets={
                    "data": Asset(
                        key="data",
                        href=resp.url,
                        title="3D Soil Properties Profile (JSON)",
                        media_type="application/json"
                    )
                }
            )
            result.properties["_raw_data"] = data
            return [result]
        except requests.exceptions.RequestException as e:
            print(f"❌ SoilGrids query error: {e}")
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
        os.makedirs(target_dir, exist_ok=True)
        filename = f"{result.id}.json"
        outpath = os.path.join(target_dir, filename)

        if "_raw_data" in result.properties:
            with open(outpath, "w") as f:
                json.dump(result.properties["_raw_data"], f, indent=2)
            print(f"✔ Saved SoilGrids profile to: {os.path.abspath(outpath)}")
            return os.path.abspath(outpath)

        target_asset = result.assets.get(asset_key or "data")
        return self._stream_download(
            url=target_asset.href,
            outpath=outpath,
            desc=f"{result.id[:20]}",
            resume=resume,
            multipart=multipart,
            max_workers=max_workers
        )
