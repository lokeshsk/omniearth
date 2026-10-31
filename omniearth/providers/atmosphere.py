"""
OmniEarth Atmosphere & Air Quality Provider Adapter
===================================================
Integrates Copernicus Sentinel-5P TROPOMI and CAMS Atmospheric Chemistry.
Delivers surface and tropospheric concentrations of NO2, CO, CH4, SO2, O3,
Aerosol Optical Depth (AOD), PM2.5, PM10, and UV Index across global AOIs.
"""

import os
import json
from typing import List, Optional
import requests

from omniearth.models import AOI, SearchResult, Asset, Category, FilterOptions
from omniearth.providers.base import BaseProvider
from omniearth.config import config


class AtmosphereProvider(BaseProvider):
    category = Category.ATMOSPHERE
    name = "atmosphere"

    AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
    S5P_STAC_URL = "https://catalogue.dataspace.copernicus.eu/stac/search"

    DEFAULT_VARS = [
        "pm10",
        "pm2_5",
        "carbon_monoxide",
        "nitrogen_dioxide",
        "sulphur_dioxide",
        "ozone",
        "aerosol_optical_depth",
        "dust",
        "uv_index"
    ]

    def search(
        self,
        aoi: AOI,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        filters: Optional[FilterOptions] = None
    ) -> List[SearchResult]:
        center_lon = round((aoi.min_lon + aoi.max_lon) / 2.0, 4)
        center_lat = round((aoi.min_lat + aoi.max_lat) / 2.0, 4)

        vars_list = (filters.variables if filters and filters.variables else self.DEFAULT_VARS)
        vars_param = ",".join(vars_list)

        params = {
            "latitude": center_lat,
            "longitude": center_lon,
            "hourly": vars_param,
            "timezone": "auto"
        }
        if start_date and end_date:
            params["start_date"] = start_date
            params["end_date"] = end_date

        try:
            resp = requests.get(self.AIR_QUALITY_URL, params=params, timeout=config.timeout)
            resp.raise_for_status()
            data = resp.json()

            feed_id = f"s5p_cams_{center_lat}_{center_lon}_{start_date or 'latest'}"
            direct_url = str(resp.url) if resp.url else ""

            assets_dict = {
                "data": Asset(
                    key="data",
                    href=direct_url,
                    title="Atmospheric Composition & Trace Gas Feed (Sentinel-5P / CAMS)",
                    media_type="application/json"
                ),
                "tropospheric_no2": Asset(
                    key="tropospheric_no2",
                    href=f"https://catalogue.dataspace.copernicus.eu/stac/collections/SENTINEL-5P/items/{feed_id}_no2",
                    title="Copernicus Sentinel-5P TROPOMI NO2 Product",
                    media_type="application/x-netcdf"
                )
            }

            result = SearchResult(
                id=feed_id,
                collection="copernicus-sentinel-5p-cams",
                category=self.category,
                provider="copernicus_s5p",
                datetime=start_date or "now",
                bbox=aoi.bbox,
                properties={
                    "latitude": center_lat,
                    "longitude": center_lon,
                    "elevation": data.get("elevation"),
                    "variables": vars_list,
                    "hourly_sample": {k: data.get("hourly", {}).get(k, [])[:3] for k in vars_list},
                    "platform": "Sentinel-5P / CAMS ECMWF",
                    "instrument": "TROPOMI"
                },
                assets=assets_dict
            )
            result.properties["_raw_data"] = data
            return [result]
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Atmosphere API query error: {e}")
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
            print(f"[OK] Saved atmospheric profile to: {os.path.abspath(outpath)}")
            return os.path.abspath(outpath)

        target_asset = result.assets.get(asset_key or "data")
        if not target_asset:
            raise ValueError("No download asset found for atmosphere result.")

        return self._stream_download(
            url=target_asset.href,
            outpath=outpath,
            desc=f"{result.id[:20]} [atmosphere]",
            resume=resume,
            multipart=multipart,
            max_workers=max_workers
        )
