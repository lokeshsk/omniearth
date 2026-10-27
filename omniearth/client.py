"""
OmniEarth Main Client
=====================
The primary interface for searching and downloading multi-modal Earth data.
"""

from typing import List, Optional, Union, Dict, Any
from omniearth.models import AOI, SearchResult, Category, FilterOptions
from omniearth.config import config
from omniearth.providers.base import BaseProvider
from omniearth.providers.optical import OpticalProvider
from omniearth.providers.hyperspectral import HyperspectralProvider
from omniearth.providers.sar import SARProvider
from omniearth.providers.weather import WeatherProvider
from omniearth.providers.soil import SoilProvider


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
            Category.SOIL: SoilProvider()
        }

    def list_categories(self) -> List[str]:
        """Returns all supported data categories."""
        return [c.value for c in Category]

    def _resolve_aoi(self, aoi: Optional[AOI], bbox: Optional[List[float]], point: Optional[tuple]) -> AOI:
        if aoi:
            return aoi
        if bbox:
            return AOI.from_bounds(bbox[0], bbox[1], bbox[2], bbox[3])
        if point:
            lon, lat = point[:2]
            rad = point[2] if len(point) > 2 else 5.0
            return AOI.from_point(lon, lat, radius_km=rad)
        raise ValueError("Must specify an AOI using 'aoi', 'bbox' ([min_lon, min_lat, max_lon, max_lat]), or 'point' (lon, lat).")

    def search(
        self,
        category: Union[Category, str],
        aoi: Optional[AOI] = None,
        bbox: Optional[List[float]] = None,
        point: Optional[tuple] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        max_cloud_cover: Optional[float] = None,
        bands: Optional[List[str]] = None,
        variables: Optional[List[str]] = None,
        depth: Optional[str] = None,
        limit: int = 10
    ) -> List[SearchResult]:
        """
        Universal search across any satellite, meteorological, or soil provider.
        """
        cat_enum = Category(category) if isinstance(category, str) else category
        resolved_aoi = self._resolve_aoi(aoi, bbox, point)

        filters = FilterOptions(
            max_cloud_cover=max_cloud_cover,
            bands=bands,
            variables=variables,
            depth=depth,
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
        outdir: Optional[str] = None
    ) -> str:
        """
        Downloads a search result asset to local storage.
        """
        provider = self._providers.get(result.category)
        if not provider:
            raise ValueError(f"No provider found for category '{result.category}'")

        return provider.download(
            result=result,
            asset_key=asset_key,
            outdir=outdir
        )

    # Convenience shortcuts
    def get_weather(self, bbox: List[float], start_date: Optional[str] = None, end_date: Optional[str] = None, variables: Optional[List[str]] = None) -> SearchResult:
        """Instant convenience shortcut to fetch weather for a bbox."""
        results = self.search(category=Category.WEATHER, bbox=bbox, start_date=start_date, end_date=end_date, variables=variables)
        return results[0] if results else None

    def get_soil(self, bbox: List[float], depth: Optional[str] = "0-5cm", variables: Optional[List[str]] = None) -> SearchResult:
        """Instant convenience shortcut to fetch SoilGrids 3D profile for a bbox."""
        results = self.search(category=Category.SOIL, bbox=bbox, depth=depth, variables=variables)
        return results[0] if results else None
