"""
OmniEarth Main Client
=====================
The primary interface for searching and downloading multi-modal Earth data.
"""

import concurrent.futures
from typing import List, Optional, Union, Dict, Any
from omniearth.models import AOI, SearchResult, Category, FilterOptions
from omniearth.config import config
from omniearth.providers.base import BaseProvider
from omniearth.providers.optical import OpticalProvider
from omniearth.providers.hyperspectral import HyperspectralProvider
from omniearth.providers.sar import SARProvider
from omniearth.providers.weather import WeatherProvider
from omniearth.providers.soil import SoilProvider
from omniearth.providers.elevation import ElevationProvider
from omniearth.providers.landcover import LandcoverProvider


class OmniEarth:
    """
    Universal Multi-Modal Earth Observation and Environmental Data Client.

    Example:
        import omniearth as oe

        client = oe.OmniEarth()
        results = client.search(
            category="hyperspectral",
            bbox=[78.50, 20.65, 78.60, 20.72],
            max_cloud_cover=20
        )
        client.download(results[0], outdir="./data")
    """

    def __init__(self, env_path: Optional[str] = None):
        if env_path:
            config._load_environment(env_path)

        # Register core provider adapters
        self._providers: Dict[Category, BaseProvider] = {
            Category.OPTICAL: OpticalProvider(),
            Category.HYPERSPECTRAL: HyperspectralProvider(),
            Category.SAR: SARProvider(),
            Category.WEATHER: WeatherProvider(),
            Category.SOIL: SoilProvider(),
            Category.ELEVATION: ElevationProvider(),
            Category.LANDCOVER: LandcoverProvider()
        }

    def list_categories(self) -> List[str]:
        """Returns all supported data categories."""
        return [c.value for c in Category]

    def _resolve_aoi(
        self,
        aoi: Optional[AOI] = None,
        bbox: Optional[List[float]] = None,
        point: Optional[tuple] = None,
        geojson: Optional[Union[str, dict, Any]] = None
    ) -> AOI:
        if aoi:
            return aoi
        if geojson:
            return AOI.from_geojson(geojson)
        if bbox:
            return AOI.from_bounds(bbox[0], bbox[1], bbox[2], bbox[3])
        if point:
            lon, lat = point[:2]
            rad = point[2] if len(point) > 2 else 5.0
            return AOI.from_point(lon, lat, radius_km=rad)
        raise ValueError("Must specify an AOI using 'aoi', 'bbox' ([min_lon, min_lat, max_lon, max_lat]), 'point' (lon, lat), or 'geojson'.")

    def search(
        self,
        category: Union[Category, str],
        aoi: Optional[AOI] = None,
        bbox: Optional[List[float]] = None,
        point: Optional[tuple] = None,
        geojson: Optional[Union[str, dict, Any]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        max_cloud_cover: Optional[float] = None,
        bands: Optional[List[str]] = None,
        variables: Optional[List[str]] = None,
        depth: Optional[str] = None,
        dataset: Optional[str] = None,
        year: Optional[int] = None,
        limit: int = 10
    ) -> List[SearchResult]:
        """
        Universal search across any satellite, meteorological, soil, elevation, or land cover provider.
        """
        cat_enum = Category(category) if isinstance(category, str) else category
        resolved_aoi = self._resolve_aoi(aoi, bbox, point, geojson)

        filters = FilterOptions(
            max_cloud_cover=max_cloud_cover,
            bands=bands,
            variables=variables,
            depth=depth,
            dataset=dataset,
            year=year,
            limit=limit
        )

        provider = self._providers.get(cat_enum)
        if not provider:
            raise ValueError(f"Unsupported category '{cat_enum}'. Supported: {self.list_categories()}")

        return provider.search(
            aoi=resolved_aoi,
            start_date=start_date,
            end_date=end_date,
            filters=filters
        )

    def download(
        self,
        result: SearchResult,
        asset_key: Optional[str] = None,
        outdir: Optional[str] = None,
        resume: bool = True,
        multipart: bool = True,
        max_workers: int = 4
    ) -> str:
        """
        Downloads a search result asset to local storage with multipart and resumable support.
        """
        provider = self._providers.get(result.category)
        if not provider:
            raise ValueError(f"No provider found for category '{result.category}'")

        return provider.download(
            result=result,
            asset_key=asset_key,
            outdir=outdir,
            resume=resume,
            multipart=multipart,
            max_workers=max_workers
        )

    def download_all(
        self,
        result: SearchResult,
        asset_keys: Optional[List[str]] = None,
        outdir: Optional[str] = None,
        max_workers: int = 4,
        resume: bool = True,
        multipart: bool = True
    ) -> Dict[str, str]:
        """
        Downloads multiple or all assets of a search result concurrently.
        Returns a dictionary mapping asset_key -> downloaded absolute file path.
        """
        keys_to_download = asset_keys or list(result.assets.keys())
        if not keys_to_download:
            raise ValueError(f"No assets found to download for result '{result.id}'")

        results_dict: Dict[str, str] = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(max_workers, len(keys_to_download))) as executor:
            future_to_key = {
                executor.submit(self.download, result, k, outdir, resume, multipart, 1): k
                for k in keys_to_download
            }
            for future in concurrent.futures.as_completed(future_to_key):
                k = future_to_key[future]
                results_dict[k] = future.result()
        return results_dict

    def download_many(
        self,
        results: List[SearchResult],
        asset_key: Optional[str] = None,
        outdir: Optional[str] = None,
        max_workers: int = 4,
        resume: bool = True,
        multipart: bool = True
    ) -> List[str]:
        """
        Downloads assets for multiple search results concurrently across worker threads.
        Returns list of downloaded absolute file paths.
        """
        if not results:
            return []

        paths: List[Optional[str]] = [None] * len(results)
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(max_workers, len(results))) as executor:
            future_to_idx = {
                executor.submit(self.download, r, asset_key, outdir, resume, multipart, 1): idx
                for idx, r in enumerate(results)
            }
            for future in concurrent.futures.as_completed(future_to_idx):
                idx = future_to_idx[future]
                paths[idx] = future.result()
        return [p for p in paths if p is not None]

    # Convenience shortcuts
    def get_weather(self, bbox: List[float], start_date: Optional[str] = None, end_date: Optional[str] = None, variables: Optional[List[str]] = None) -> Optional[SearchResult]:
        """Instant convenience shortcut to fetch weather for a bbox."""
        results = self.search(category=Category.WEATHER, bbox=bbox, start_date=start_date, end_date=end_date, variables=variables)
        return results[0] if results else None

    def get_soil(self, bbox: List[float], depth: Optional[str] = "0-5cm", variables: Optional[List[str]] = None) -> Optional[SearchResult]:
        """Instant convenience shortcut to fetch SoilGrids 3D profile for a bbox."""
        results = self.search(category=Category.SOIL, bbox=bbox, depth=depth, variables=variables)
        return results[0] if results else None

    def get_elevation(
        self,
        bbox: Optional[List[float]] = None,
        aoi: Optional[AOI] = None,
        point: Optional[tuple] = None,
        geojson: Optional[Union[str, dict, Any]] = None,
        dataset: str = "copernicus"
    ) -> Optional[SearchResult]:
        """Instant convenience shortcut to fetch DEM tile for an AOI."""
        results = self.search(category=Category.ELEVATION, bbox=bbox, aoi=aoi, point=point, geojson=geojson, dataset=dataset)
        return results[0] if results else None

    def get_landcover(
        self,
        bbox: Optional[List[float]] = None,
        aoi: Optional[AOI] = None,
        point: Optional[tuple] = None,
        geojson: Optional[Union[str, dict, Any]] = None,
        year: int = 2021
    ) -> Optional[SearchResult]:
        """Instant convenience shortcut to fetch ESA WorldCover map tile for an AOI."""
        results = self.search(category=Category.LANDCOVER, bbox=bbox, aoi=aoi, point=point, geojson=geojson, year=year)
        return results[0] if results else None

    def compute_index(
        self,
        index: str,
        nir: Any,
        red: Optional[Any] = None,
        green: Optional[Any] = None,
        blue: Optional[Any] = None,
        rededge: Optional[Any] = None,
        swir: Optional[Any] = None,
        outpath: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Computes standard remote sensing indices on arrays or scalars:
        - ndvi: (nir - red) / (nir + red)
        - ndwi: (green - nir) / (green + nir)
        - ndre: (nir - rededge) / (nir + rededge)
        - evi: 2.5 * (nir - red) / (nir + 6*red - 7.5*blue + 1)
        - nbr: (nir - swir) / (nir + swir)
        """
        import json

        idx = index.lower()
        eps = 1e-8

        def calc(n, r=None, g=None, b=None, re=None, s=None):
            if idx == "ndvi":
                if r is None:
                    raise ValueError("Red band required to compute NDVI")
                return (float(n) - float(r)) / (float(n) + float(r) + eps)
            elif idx == "ndwi":
                if g is None:
                    raise ValueError("Green band required to compute NDWI")
                return (float(g) - float(n)) / (float(g) + float(n) + eps)
            elif idx == "ndre":
                if re is None:
                    raise ValueError("RedEdge band required to compute NDRE")
                return (float(n) - float(re)) / (float(n) + float(re) + eps)
            elif idx == "evi":
                if r is None or b is None:
                    raise ValueError("Red and Blue bands required to compute EVI")
                return 2.5 * ((float(n) - float(r)) / (float(n) + 6.0 * float(r) - 7.5 * float(b) + 1.0 + eps))
            elif idx == "nbr":
                if s is None:
                    raise ValueError("SWIR band required to compute NBR")
                return (float(n) - float(s)) / (float(n) + float(s) + eps)
            else:
                raise ValueError(f"Unsupported index '{index}'. Supported: ndvi, ndwi, ndre, evi, nbr")

        if isinstance(nir, (list, tuple)):
            r_list = red if isinstance(red, (list, tuple)) else [red] * len(nir)
            g_list = green if isinstance(green, (list, tuple)) else [green] * len(nir)
            b_list = blue if isinstance(blue, (list, tuple)) else [blue] * len(nir)
            re_list = rededge if isinstance(rededge, (list, tuple)) else [rededge] * len(nir)
            s_list = swir if isinstance(swir, (list, tuple)) else [swir] * len(nir)

            data = [calc(nir[i], r_list[i], g_list[i], b_list[i], re_list[i], s_list[i]) for i in range(len(nir))]
            mean_val = sum(data) / len(data) if data else 0.0
            min_val = min(data) if data else 0.0
            max_val = max(data) if data else 0.0
            variance = sum((x - mean_val) ** 2 for x in data) / len(data) if data else 0.0
            std_val = variance ** 0.5
        else:
            val = calc(nir, red, green, blue, rededge, swir)
            data = val
            mean_val = float(val)
            min_val = float(val)
            max_val = float(val)
            std_val = 0.0

        stats = {
            "index": idx,
            "mean": mean_val,
            "min": min_val,
            "max": max_val,
            "std": std_val,
            "data": data
        }

        if outpath:
            with open(outpath, "w", encoding="utf-8") as f:
                json.dump(stats, f, indent=2)

        return stats

    def get_time_series(
        self,
        category: Union[Category, str],
        aoi: Optional[AOI] = None,
        bbox: Optional[List[float]] = None,
        point: Optional[tuple] = None,
        geojson: Optional[Union[str, dict, Any]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        variables: Optional[List[str]] = None,
        max_cloud_cover: Optional[float] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Extracts a chronological time-series of observations across the given AOI and date range.
        """
        cat_enum = Category(category) if isinstance(category, str) else category
        results = self.search(
            category=cat_enum,
            aoi=aoi,
            bbox=bbox,
            point=point,
            geojson=geojson,
            start_date=start_date,
            end_date=end_date,
            variables=variables,
            max_cloud_cover=max_cloud_cover,
            limit=limit
        )

        if cat_enum == Category.WEATHER and results:
            raw = results[0].properties.get("_raw_data", {})
            hourly = raw.get("hourly", {})
            times = hourly.get("time", [])
            series = []
            for idx, t in enumerate(times):
                record = {"datetime": t}
                for k, v in hourly.items():
                    if k != "time" and isinstance(v, list) and idx < len(v):
                        record[k] = v[idx]
                series.append(record)
            return series

        sorted_results = sorted(results, key=lambda r: r.datetime or "")
        return [
            {
                "id": r.id,
                "datetime": r.datetime,
                "category": r.category.value,
                "collection": r.collection,
                "cloud_cover": r.properties.get("eo:cloud_cover"),
                "assets": list(r.assets.keys())
            }
            for r in sorted_results
        ]
