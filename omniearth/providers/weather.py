"""
OmniEarth Weather Provider Adapter
==================================
Integrates Open-Meteo API (ECMWF, NOAA GFS, ICON, and ERA5 Reanalysis).
Zero credentials required. Delivers hourly temperature, humidity, rainfall,
and multi-depth soil moisture.
"""

import os
import json
from typing import List, Optional
import requests

from omniearth.models import AOI, SearchResult, Asset, Category, FilterOptions
from omniearth.providers.base import BaseProvider
from omniearth.config import config


class WeatherProvider(BaseProvider):
    category = Category.WEATHER
    name = "weather"

    FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
    HISTORICAL_URL = "https://archive-api.open-meteo.com/v1/archive"

    DEFAULT_HOURLY_VARS = [
        "temperature_2m",
        "relative_humidity_2m",
        "dew_point_2m",
        "apparent_temperature",
        "precipitation",
        "surface_pressure",
        "wind_speed_10m",
        "wind_direction_10m",
        "shortwave_radiation_sum",
        "et0_fao_evapotranspiration",
        "vapour_pressure_deficit",
        "soil_temperature_0cm",
        "soil_moisture_0_to_1cm",
        "soil_moisture_1_to_3cm",
        "soil_moisture_3_to_9cm"
    ]

    def search(
        self,
        aoi: AOI,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        filters: Optional[FilterOptions] = None
    ) -> List[SearchResult]:
        # Compute center coordinate of AOI
        center_lon = round((aoi.min_lon + aoi.max_lon) / 2.0, 4)
        center_lat = round((aoi.min_lat + aoi.max_lat) / 2.0, 4)

        hourly_vars = (filters.variables if filters and filters.variables else self.DEFAULT_HOURLY_VARS)
        vars_param = ",".join(hourly_vars)

        # Decide whether to query forecast or historical archive
        is_historical = False
        if start_date and end_date:
            # If dates are in the past (e.g. before today), use historical archive
            api_url = self.HISTORICAL_URL if start_date < "2026-10-20" else self.FORECAST_URL
            is_historical = (api_url == self.HISTORICAL_URL)
        else:
            api_url = self.FORECAST_URL

        params = {
            "latitude": center_lat,
            "longitude": center_lon,
            "hourly": vars_param,
            "timezone": "auto"
        }

        if is_historical:
            params["start_date"] = start_date
            params["end_date"] = end_date
        elif start_date and end_date:
            params["start_date"] = start_date
            params["end_date"] = end_date

        try:
            resp = requests.get(api_url, params=params, timeout=config.timeout)
            resp.raise_for_status()
            data = resp.json()

            feed_id = f"openmeteo_{center_lat}_{center_lon}_{start_date or 'latest'}"
            direct_json_url = str(resp.url) if resp.url else ""

            assets_dict = {
                "data": Asset(
                    key="data",
                    href=direct_json_url,
                    title="Hourly Meteorological & Soil Feed",
                    media_type="application/json"
                )
            }

            result = SearchResult(
                id=feed_id,
                collection="open-meteo-weather",
                category=self.category,
                provider="open_meteo",
                datetime=start_date or "now",
                bbox=aoi.bbox,
                properties={
                    "latitude": center_lat,
                    "longitude": center_lon,
                    "elevation": data.get("elevation"),
                    "variables": hourly_vars,
                    "hourly_sample": {k: data.get("hourly", {}).get(k, [])[:3] for k in hourly_vars}
                },
                assets=assets_dict
            )
            # Cache the payload in object for instant download
            result.properties["_raw_data"] = data
            return [result]
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Weather API query error: {e}")
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

        # If already cached in search result
        if "_raw_data" in result.properties:
            with open(outpath, "w") as f:
                json.dump(result.properties["_raw_data"], f, indent=2)
            print(f"[OK] Saved weather data to: {os.path.abspath(outpath)}")
            return os.path.abspath(outpath)

        # Otherwise fetch from URL
        target_asset = result.assets.get(asset_key or "data")
        if not target_asset:
            raise ValueError("No download asset found for weather result.")

        return self._stream_download(
            url=target_asset.href,
            outpath=outpath,
            desc=f"{result.id[:20]}",
            resume=resume,
            multipart=multipart,
            max_workers=max_workers
        )
