"""
OmniEarth Land Cover Provider Adapter
====================================
Unified interface for global 10m Land Use / Land Cover (LULC) data:
- ESA WorldCover 10m (2020 v100 and 2021 v200) from AWS Open Data (S3)
Zero-cost, cloud-optimized GeoTIFFs (COGs).
"""

import math
import os
from typing import List, Optional

from omniearth.models import AOI, SearchResult, Asset, Category, FilterOptions
from omniearth.providers.base import BaseProvider
from omniearth.config import config

ESA_WORLDCOVER_BASE = "https://esa-worldcover.s3.eu-central-1.amazonaws.com"

# ESA WorldCover 10m Legend
WORLDCOVER_CLASSES = {
    10: "Tree cover",
    20: "Shrubland",
    30: "Grassland",
    40: "Cropland",
    50: "Built-up",
    60: "Bare / sparse vegetation",
    70: "Snow and ice",
    80: "Permanent water bodies",
    90: "Herbaceous wetland",
    95: "Mangroves",
    100: "Moss and lichen"
}


class LandcoverProvider(BaseProvider):
    """Provider for global 10m land cover classification maps."""
    category = Category.LANDCOVER
    name = "landcover"

    def _generate_worldcover_tile(self, lat: int, lon: int, year: int = 2021) -> SearchResult:
        # ESA WorldCover tiles are 3x3 degrees, named by bottom-left grid corner
        grid_lat = (lat // 3) * 3
        grid_lon = (lon // 3) * 3

        lat_p = f"N{grid_lat:02d}" if grid_lat >= 0 else f"S{abs(grid_lat):02d}"
        lon_p = f"E{grid_lon:03d}" if grid_lon >= 0 else f"W{abs(grid_lon):03d}"
        version = "v200" if year >= 2021 else "v100"
        actual_year = 2021 if year >= 2021 else 2020

        tile_id = f"ESA_WorldCover_10m_{actual_year}_{version}_{lat_p}{lon_p}_Map"
        filename = f"{tile_id}.tif"
        url = f"{ESA_WORLDCOVER_BASE}/{version}/{actual_year}/map/{filename}"

        return SearchResult(
            id=tile_id,
            collection=f"esa-worldcover-{actual_year}",
            category=Category.LANDCOVER,
            provider="esa_worldcover_aws",
            datetime=f"{actual_year}-01-01T00:00:00Z",
            bbox=[float(grid_lon), float(grid_lat), float(grid_lon + 3), float(grid_lat + 3)],
            properties={
                "title": f"ESA WorldCover 10m ({actual_year}, {lat_p}{lon_p})",
                "dataset": "esa-worldcover",
                "resolution": "10m",
                "year": actual_year,
                "version": version,
                "classes": WORLDCOVER_CLASSES,
                "grid_lat": grid_lat,
                "grid_lon": grid_lon
            },
            assets={
                "map": Asset(
                    key="map",
                    href=url,
                    media_type="image/tiff; application=geotiff; profile=cloud-optimized",
                    title="ESA WorldCover 10m COG Map"
                ),
                "data": Asset(
                    key="data",
                    href=url,
                    media_type="image/tiff",
                    title="ESA WorldCover 10m Raster"
                )
            }
        )

    def search(
        self,
        aoi: AOI,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        filters: Optional[FilterOptions] = None
    ) -> List[SearchResult]:
        """
        Searches and generates intersecting ESA WorldCover 10m tiles for the AOI.
        """
        year = 2021
        if filters and filters.year:
            year = filters.year
        elif end_date and len(end_date) >= 4 and end_date[:4].isdigit():
            year = int(end_date[:4])
        elif start_date and len(start_date) >= 4 and start_date[:4].isdigit():
            year = int(start_date[:4])

        limit = filters.limit if filters and filters.limit else 10

        minx, miny, maxx, maxy = aoi.bbox
        lon_start = (math.floor(minx) // 3) * 3
        lon_end = (math.ceil(maxx) // 3) * 3
        lat_start = (math.floor(miny) // 3) * 3
        lat_end = (math.ceil(maxy) // 3) * 3

        if lon_start == lon_end:
            lon_end += 3
        if lat_start == lat_end:
            lat_end += 3

        seen = set()
        results: List[SearchResult] = []

        for lat in range(lat_start, lat_end, 3):
            for lon in range(lon_start, lon_end, 3):
                tile = self._generate_worldcover_tile(lat, lon, year=year)
                if tile.id not in seen:
                    seen.add(tile.id)
                    results.append(tile)
                if len(results) >= limit:
                    return results

        return results

    def download(
        self,
        result: SearchResult,
        asset_key: Optional[str] = None,
        outdir: Optional[str] = None,
        resume: bool = True,
        multipart: bool = True,
        max_workers: int = 4
    ) -> str:
        """Download Land Cover raster tile with resumable, multipart streaming."""
        target_asset = None
        if asset_key and asset_key in result.assets:
            target_asset = result.assets[asset_key]
        elif "map" in result.assets:
            target_asset = result.assets["map"]
        elif "data" in result.assets:
            target_asset = result.assets["data"]
        elif result.assets:
            target_asset = next(iter(result.assets.values()))

        if not target_asset or not target_asset.href:
            raise ValueError(f"No valid Landcover asset found to download for '{result.id}'")

        filename = os.path.basename(target_asset.href.split("?")[0])
        if not filename.endswith(".tif") and not filename.endswith(".tiff"):
            filename = f"{result.id}.tif"

        target_dir = outdir or config.default_outdir
        os.makedirs(target_dir, exist_ok=True)
        outpath = os.path.join(target_dir, filename)

        return self._stream_download(
            url=target_asset.href,
            outpath=outpath,
            desc=f"Downloading {filename}",
            resume=resume,
            multipart=multipart,
            max_workers=max_workers
        )
