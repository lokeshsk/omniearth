"""
OmniEarth Elevation & Topography Provider
==========================================
Unified interface for 30m global Digital Elevation Models (DEM/DSM/DTM):
- Copernicus DEM GLO-30 (30m, DSM) from AWS Open Data
- SRTM GL1 1 Arc-Second (30m, DSM) from OpenTopography S3
- ALOS World 3D - 30m (AW3D30, DSM) by JAXA from OpenTopography S3
- FABDEM v1-2 (30m, DTM bare-earth) from University of Bristol
"""

import math
import os
from typing import List, Optional

from omniearth.models import AOI, SearchResult, Asset, Category, FilterOptions
from omniearth.providers.base import BaseProvider

S3_COP30_BASE = "https://copernicus-dem-30m.s3.amazonaws.com"
OPENTOPOGRAPHY_SRTM_BASE = "https://opentopography.s3.sdsc.edu/raster/SRTM_GL1/SRTM_GL1_srtm"
OPENTOPOGRAPHY_ALOS_BASE = "https://opentopography.s3.sdsc.edu/raster/AW3D30/AW3D30_global"
BRISTOL_FABDEM_BASE = "https://data.bris.ac.uk/datasets/s5hqmjcdj8yo2ibzi9b4ew3sn"


class ElevationProvider(BaseProvider):
    """Provider for global elevation models (DEM / DSM / DTM)."""
    category = Category.ELEVATION
    name = "elevation"

    def _generate_copernicus_tile(self, lat: int, lon: int) -> SearchResult:
        lat_p = f"N{lat:02d}" if lat >= 0 else f"S{abs(lat):02d}"
        lon_p = f"E{lon:03d}" if lon >= 0 else f"W{abs(lon):03d}"
        tile_id = f"Copernicus_DSM_COG_10_{lat_p}_00_{lon_p}_00_DEM"
        filename = f"{tile_id}.tif"
        url = f"{S3_COP30_BASE}/{tile_id}/{filename}"

        return SearchResult(
            id=tile_id,
            collection="copernicus-dem-glo-30",
            category=Category.ELEVATION,
            provider="aws_copernicus_dem",
            datetime="2026-01-01T00:00:00Z",
            bbox=[float(lon), float(lat), float(lon + 1), float(lat + 1)],
            properties={
                "title": f"Copernicus DEM 30m ({lat_p}, {lon_p})",
                "dataset": "copernicus",
                "resolution": "30m",
                "sensor_type": "DSM",
                "grid_lat": lat,
                "grid_lon": lon
            },
            assets={
                "dem": Asset(key="dem", href=url, media_type="image/tiff; application=geotiff; profile=cloud-optimized", title="DEM Raster COG"),
                "data": Asset(key="data", href=url, media_type="image/tiff", title="DEM Raster")
            }
        )

    def _generate_srtm_tile(self, lat: int, lon: int) -> SearchResult:
        lat_p = f"N{lat:02d}" if lat >= 0 else f"S{abs(lat):02d}"
        lon_p = f"E{lon:03d}" if lon >= 0 else f"W{abs(lon):03d}"
        tile_id = f"{lat_p}{lon_p}"
        filename = f"{tile_id}.tif"
        url = f"{OPENTOPOGRAPHY_SRTM_BASE}/{filename}"

        return SearchResult(
            id=f"SRTM_GL1_{tile_id}",
            collection="srtm-gl1-30m",
            category=Category.ELEVATION,
            provider="opentopography_srtm",
            datetime="2026-01-01T00:00:00Z",
            bbox=[float(lon), float(lat), float(lon + 1), float(lat + 1)],
            properties={
                "title": f"SRTM GL1 30m ({lat_p}, {lon_p})",
                "dataset": "srtm",
                "resolution": "30m",
                "sensor_type": "DSM",
                "grid_lat": lat,
                "grid_lon": lon
            },
            assets={
                "dem": Asset(key="dem", href=url, media_type="image/tiff", title="SRTM GeoTIFF"),
                "data": Asset(key="data", href=url, media_type="image/tiff", title="SRTM GeoTIFF")
            }
        )

    def _generate_alos_tile(self, lat: int, lon: int) -> SearchResult:
        lat_p = f"N{lat:03d}" if lat >= 0 else f"S{abs(lat):03d}"
        lon_p = f"E{lon:03d}" if lon >= 0 else f"W{abs(lon):03d}"
        tile_id = f"ALPSMLC30_{lat_p}{lon_p}_DSM"
        filename = f"{tile_id}.tif"
        url = f"{OPENTOPOGRAPHY_ALOS_BASE}/{filename}"

        return SearchResult(
            id=tile_id,
            collection="alos-aw3d30-30m",
            category=Category.ELEVATION,
            provider="opentopography_alos",
            datetime="2026-01-01T00:00:00Z",
            bbox=[float(lon), float(lat), float(lon + 1), float(lat + 1)],
            properties={
                "title": f"ALOS World 3D 30m ({lat_p}, {lon_p})",
                "dataset": "alos",
                "resolution": "30m",
                "sensor_type": "DSM",
                "grid_lat": lat,
                "grid_lon": lon
            },
            assets={
                "dem": Asset(key="dem", href=url, media_type="image/tiff", title="ALOS AW3D30 GeoTIFF"),
                "data": Asset(key="data", href=url, media_type="image/tiff", title="ALOS AW3D30 GeoTIFF")
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
        Searches and generates intersecting DEM tiles for the specified AOI.
        Supports datasets: 'copernicus' (default), 'srtm', 'alos'/'aw3d30'.
        """
        dataset = (filters.dataset.lower() if filters and filters.dataset else "copernicus")
        limit = filters.limit if filters and filters.limit else 10

        minx, miny, maxx, maxy = aoi.bbox
        lon_start = math.floor(minx)
        lon_end = math.ceil(maxx)
        lat_start = math.floor(miny)
        lat_end = math.ceil(maxy)

        if lon_start == lon_end:
            lon_end += 1
        if lat_start == lat_end:
            lat_end += 1

        results: List[SearchResult] = []
        for lat in range(lat_start, lat_end):
            for lon in range(lon_start, lon_end):
                if len(results) >= limit:
                    return results

                if dataset in ("copernicus", "cop30", "glo-30"):
                    results.append(self._generate_copernicus_tile(lat, lon))
                elif dataset in ("srtm", "srtm30", "gl1"):
                    results.append(self._generate_srtm_tile(lat, lon))
                elif dataset in ("alos", "aw3d30"):
                    results.append(self._generate_alos_tile(lat, lon))
                else:
                    # Default fallback to Copernicus DEM GLO-30
                    results.append(self._generate_copernicus_tile(lat, lon))

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
        """Download DEM raster tile with resumable, multipart streaming."""
        target_asset = None
        if asset_key and asset_key in result.assets:
            target_asset = result.assets[asset_key]
        elif "dem" in result.assets:
            target_asset = result.assets["dem"]
        elif "data" in result.assets:
            target_asset = result.assets["data"]
        elif result.assets:
            target_asset = next(iter(result.assets.values()))

        if not target_asset or not target_asset.href:
            raise ValueError(f"No valid DEM asset found to download for '{result.id}'")

        filename = os.path.basename(target_asset.href.split("?")[0])
        if not filename.endswith(".tif") and not filename.endswith(".tiff"):
            filename = f"{result.id}.tif"

        target_dir = outdir or "./omniearth_downloads"
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
