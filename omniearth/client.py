"""
OmniEarth Main Client
=====================
The primary interface for searching and downloading multi-modal Earth data.
"""

import os
import concurrent.futures
from typing import List, Optional, Union, Dict, Any
from omniearth.models import AOI, SearchResult, SearchResults, Category, FilterOptions
from omniearth.config import config
from omniearth.providers.base import BaseProvider
from omniearth.providers.cdse import CDSEProvider, UUID_REGEX
from omniearth.providers.optical import OpticalProvider
from omniearth.providers.hyperspectral import HyperspectralProvider
from omniearth.providers.sar import SARProvider
from omniearth.providers.weather import WeatherProvider
from omniearth.providers.soil import SoilProvider
from omniearth.providers.elevation import ElevationProvider
from omniearth.providers.landcover import LandcoverProvider
from omniearth.providers.atmosphere import AtmosphereProvider
from omniearth.providers.fire import FireProvider
from omniearth.providers.ocean import OceanProvider
from omniearth.providers.altimetry import AltimetryProvider
from omniearth.providers.precipitation import PrecipitationProvider
from omniearth.providers.hydrology import HydrologyProvider
from omniearth.providers.nightlights import NightlightsProvider
from omniearth.indices import compute_spectral_index


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
            Category.LANDCOVER: LandcoverProvider(),
            Category.ATMOSPHERE: AtmosphereProvider(),
            Category.FIRE: FireProvider(),
            Category.OCEAN: OceanProvider(),
            Category.ALTIMETRY: AltimetryProvider(),
            Category.PRECIPITATION: PrecipitationProvider(),
            Category.HYDROLOGY: HydrologyProvider(),
            Category.NIGHTLIGHTS: NightlightsProvider()
        }
        self._cdse_provider = CDSEProvider()

        # Non-blocking version update check
        try:
            from omniearth.version_checker import check_for_updates
            import omniearth
            check_for_updates(current_version=omniearth.__version__, is_cli=False)
        except Exception:
            pass

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
        level: Optional[str] = "sr",
        limit: int = 10,
        provider: Optional[str] = None,
        format: Optional[str] = None
    ) -> SearchResults:
        """
        Universal search across any satellite, meteorological, soil, elevation, or land cover provider.
        """
        cat_enum = Category(category) if isinstance(category, str) else category
        resolved_aoi = self._resolve_aoi(aoi, bbox, point, geojson)

        effective_start = start_date
        effective_end = end_date
        if year and not effective_start and not effective_end:
            effective_start = f"{year}-01-01"
            effective_end = f"{year}-12-31"

        filters = FilterOptions(
            max_cloud_cover=max_cloud_cover,
            bands=bands,
            variables=variables,
            depth=depth,
            dataset=dataset,
            year=year,
            level=level,
            limit=limit,
            provider=provider,
            format=format
        )

        if provider == "cdse" or dataset == "cdse" or (format in ("safe", "raw") and cat_enum in (Category.OPTICAL, Category.SAR, Category.OCEAN, Category.ATMOSPHERE)):
            self._cdse_provider.category = cat_enum
            results = self._cdse_provider.search(
                aoi=resolved_aoi,
                start_date=effective_start,
                end_date=effective_end,
                filters=filters
            )
        else:
            base_prov = self._providers.get(cat_enum)
            if not base_prov:
                raise ValueError(f"Unsupported category '{cat_enum}'. Supported: {self.list_categories()}")
            results = base_prov.search(
                aoi=resolved_aoi,
                start_date=effective_start,
                end_date=effective_end,
                filters=filters
            )

        results.sort(key=lambda x: getattr(x, "datetime", None) or "", reverse=True)
        return SearchResults(results, client=self)

    def search_and_download(
        self,
        category: Union[Category, str],
        aoi: Optional[AOI] = None,
        bbox: Optional[List[float]] = None,
        point: Optional[tuple] = None,
        geojson: Optional[Union[str, dict, Any]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        max_cloud_cover: Optional[float] = None,
        bands: Optional[Union[str, List[str]]] = None,
        variables: Optional[List[str]] = None,
        depth: Optional[str] = None,
        dataset: Optional[str] = None,
        year: Optional[int] = None,
        level: Optional[str] = "sr",
        limit: int = 10,
        asset_key: Optional[str] = None,
        outdir: Optional[str] = None,
        resume: bool = True,
        multipart: bool = True,
        max_workers: int = 4,
        provider: Optional[str] = None,
        format: Optional[str] = None,
        verify_checksum: bool = False,
        composite: Optional[str] = None,
        **kwargs
    ) -> List[str]:
        """
        Searches for scenes and immediately downloads all matching results in parallel.
        Returns list of downloaded absolute file paths.
        """
        bands_list = [b.strip() for b in bands.split(",")] if isinstance(bands, str) else bands
        results = self.search(
            category=category,
            aoi=aoi,
            bbox=bbox,
            point=point,
            geojson=geojson,
            start_date=start_date,
            end_date=end_date,
            max_cloud_cover=max_cloud_cover,
            bands=bands_list,
            variables=variables,
            depth=depth,
            dataset=dataset,
            year=year,
            level=level,
            limit=limit,
            provider=provider,
            format=format
        )
        download_kwargs = {
            "asset_key": asset_key,
            "outdir": outdir,
            "max_workers": max_workers,
            "resume": resume,
            "multipart": multipart
        }
        if format is not None:
            download_kwargs["format"] = format
        if bands is not None:
            download_kwargs["bands"] = bands
        if verify_checksum:
            download_kwargs["verify_checksum"] = verify_checksum
        if composite is not None:
            download_kwargs["composite"] = composite
        download_kwargs.update(kwargs)
        return results.download_all(**download_kwargs)

    def get_item(
        self,
        category: Union[Category, str],
        item_id: str,
        provider: Optional[str] = None
    ) -> Optional[SearchResult]:
        """
        Directly retrieves a specific STAC item or CDSE product by ID without running a spatial search query.
        """
        cat_enum = Category(category) if isinstance(category, str) else category
        clean_id = item_id.strip()

        is_cdse_hint = bool(UUID_REGEX.match(clean_id)) or (
            clean_id.startswith(("S1", "S2", "S3", "S5P")) and any(x in clean_id for x in ("_MSIL", "_GRD", "_RAW", ".SAFE", "_OL_", "_SL_"))
        )

        if provider == "cdse" or (is_cdse_hint and cat_enum in (Category.OPTICAL, Category.SAR, Category.OCEAN, Category.ATMOSPHERE)):
            res = self._cdse_provider.get_item(clean_id)
            if res:
                return res

        base_prov = self._providers.get(cat_enum)
        if not base_prov:  # pragma: no cover
            raise ValueError(f"Unsupported category '{cat_enum}'. Supported: {self.list_categories()}")

        item = base_prov.get_item(clean_id)
        if not item and cat_enum in (Category.OPTICAL, Category.SAR, Category.OCEAN, Category.ATMOSPHERE):
            item = self._cdse_provider.get_item(clean_id)
        return item

    def download(
        self,
        result: SearchResult,
        asset_key: Optional[str] = None,
        outdir: Optional[str] = None,
        resume: bool = True,
        multipart: bool = True,
        max_workers: int = 4,
        format: Optional[str] = None,
        bands: Optional[Union[str, List[str]]] = None,
        verify_checksum: bool = False,
        composite: Optional[str] = None,
        folder: bool = False,
        zip: bool = False,
        **kwargs
    ) -> str:
        """
        Downloads a search result asset to local storage with multipart and resumable support.
        """
        base_outdir = outdir or config.default_outdir
        target_outdir = os.path.join(base_outdir, result.id) if (folder or zip) else base_outdir
        os.makedirs(target_outdir, exist_ok=True)

        resolved_key = result.resolve_asset_key(asset_key) if asset_key else None

        if (
            result.provider == "cdse"
            or format in ("safe", "raw", "node", "band")
            or (bands is not None and result.provider == "cdse")
        ):
            downloaded = self._cdse_provider.download(
                result=result,
                asset_key=resolved_key,
                outdir=target_outdir,
                resume=resume,
                multipart=multipart,
                max_workers=max_workers,
                format=format,
                bands=bands,
                verify_checksum=verify_checksum
            )
        else:
            provider = self._providers.get(result.category)
            if not provider:
                raise ValueError(f"No provider found for category '{result.category}'")

            downloaded = provider.download(
                result=result,
                asset_key=resolved_key,
                outdir=target_outdir,
                resume=resume,
                multipart=multipart,
                max_workers=max_workers
            )

        if composite:
            from omniearth.processors import create_composite_from_downloaded
            comp_path = create_composite_from_downloaded(
                directory_or_files=downloaded,
                composite_type=composite
            )
            if comp_path:
                return comp_path

        if zip and not (isinstance(downloaded, str) and downloaded.endswith(".zip")):
            if os.path.exists(target_outdir):
                import shutil
                zip_base = os.path.join(base_outdir, result.id)
                return shutil.make_archive(zip_base, "zip", target_outdir)

        return downloaded

    def download_all(
        self,
        result: SearchResult,
        asset_keys: Optional[List[str]] = None,
        outdir: Optional[str] = None,
        max_workers: int = 4,
        resume: bool = True,
        multipart: bool = True,
        format: Optional[str] = None,
        bands: Optional[Union[str, List[str]]] = None,
        verify_checksum: bool = False,
        composite: Optional[str] = None,
        folder: bool = True,
        zip: bool = False,
        **kwargs
    ) -> Dict[str, str]:
        """
        Downloads multiple or all assets of a search result concurrently.
        Returns a dictionary mapping asset_key -> downloaded absolute file path.
        """
        base_outdir = outdir or config.default_outdir
        target_outdir = os.path.join(base_outdir, result.id) if (folder or zip) else base_outdir
        os.makedirs(target_outdir, exist_ok=True)

        raw_keys = asset_keys
        if not raw_keys:
            raw_keys = [
                k for k, a in result.assets.items()
                if not k.startswith("s3_") and not (a.href or "").startswith("s3://")
            ]
        if not raw_keys and result.provider != "cdse" and not bands:
            raise ValueError(f"No assets found to download for result '{result.id}'")

        seen_hrefs = set()
        keys_to_download = []
        duplicate_key_map = {}

        for k in raw_keys:
            asset = result.assets.get(k)
            href = (asset.href.split("?")[0]) if (asset and asset.href) else None
            if href:
                if href in seen_hrefs:
                    for prev_k in keys_to_download:
                        prev_asset = result.assets.get(prev_k)
                        if prev_asset and (prev_asset.href or "").split("?")[0] == href:
                            duplicate_key_map[k] = prev_k
                            break
                    continue
                seen_hrefs.add(href)
            keys_to_download.append(k)

        if result.provider == "cdse" or format in ("safe", "raw", "node", "band") or bands:
            dl_path = self.download(
                result=result,
                outdir=target_outdir,
                resume=resume,
                multipart=multipart,
                max_workers=max_workers,
                format=format,
                bands=bands,
                verify_checksum=verify_checksum,
                composite=composite,
                folder=False,
                zip=False,
                **kwargs
            )
            res_dict = {"data": dl_path}
            if zip:
                if isinstance(dl_path, str) and dl_path.endswith(".zip"):
                    res_dict["zip"] = dl_path
                elif os.path.exists(target_outdir):
                    import shutil
                    zip_base = os.path.join(base_outdir, result.id)
                    res_dict["zip"] = shutil.make_archive(zip_base, "zip", target_outdir)
            return res_dict

        results_dict: Dict[str, str] = {}
        has_extra = bool(verify_checksum or kwargs)
        extra = {}
        if verify_checksum:
            extra["verify_checksum"] = verify_checksum
        extra.update(kwargs)

        if keys_to_download:
            with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, min(max_workers, len(keys_to_download)))) as executor:
                if has_extra:
                    future_to_key = {
                        executor.submit(
                            self.download,
                            result,
                            k,
                            target_outdir,
                            resume,
                            multipart,
                            1,
                            **extra
                        ): k
                        for k in keys_to_download
                    }
                else:
                    future_to_key = {
                        executor.submit(
                            self.download,
                            result,
                            k,
                            target_outdir,
                            resume,
                            multipart,
                            1
                        ): k
                        for k in keys_to_download
                    }
                for future in concurrent.futures.as_completed(future_to_key):
                    k = future_to_key[future]
                    results_dict[k] = future.result()

        for dup_k, canon_k in duplicate_key_map.items():
            if canon_k in results_dict:
                results_dict[dup_k] = results_dict[canon_k]

        if composite:
            from omniearth.processors import create_composite_from_downloaded
            comp_path = create_composite_from_downloaded(
                directory_or_files=list(results_dict.values()),
                composite_type=composite
            )
            if comp_path:
                results_dict["composite"] = comp_path

        if zip and os.path.exists(target_outdir):
            import shutil
            zip_base = os.path.join(base_outdir, result.id)
            zip_path = shutil.make_archive(zip_base, "zip", target_outdir)
            results_dict["zip"] = zip_path

        return results_dict

    def download_many(
        self,
        results: List[SearchResult],
        asset_key: Optional[str] = None,
        outdir: Optional[str] = None,
        max_workers: int = 4,
        resume: bool = True,
        multipart: bool = True,
        format: Optional[str] = None,
        bands: Optional[Union[str, List[str]]] = None,
        verify_checksum: bool = False,
        composite: Optional[str] = None,
        **kwargs
    ) -> List[str]:
        """
        Downloads assets for multiple search results concurrently across worker threads.
        Returns list of downloaded absolute file paths.
        """
        if not results:
            return []

        paths: List[Optional[str]] = [None] * len(results)
        has_extra = bool(format is not None or bands is not None or verify_checksum or composite is not None or kwargs)
        extra = {}
        if format is not None:
            extra["format"] = format
        if bands is not None:
            extra["bands"] = bands
        if verify_checksum:
            extra["verify_checksum"] = verify_checksum
        if composite is not None:
            extra["composite"] = composite
        extra.update(kwargs)

        with concurrent.futures.ThreadPoolExecutor(max_workers=min(max_workers, len(results))) as executor:
            if has_extra:
                future_to_idx = {
                    executor.submit(
                        self.download,
                        r,
                        asset_key,
                        outdir,
                        resume,
                        multipart,
                        1,
                        **extra
                    ): idx
                    for idx, r in enumerate(results)
                }
            else:
                future_to_idx = {
                    executor.submit(
                        self.download,
                        r,
                        asset_key,
                        outdir,
                        resume,
                        multipart,
                        1
                    ): idx
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

    def get_atmosphere(
        self,
        bbox: Optional[List[float]] = None,
        aoi: Optional[AOI] = None,
        point: Optional[tuple] = None,
        geojson: Optional[Union[str, dict, Any]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        variables: Optional[List[str]] = None
    ) -> Optional[SearchResult]:
        """Instant convenience shortcut to fetch atmospheric & air quality trace gases."""
        results = self.search(category=Category.ATMOSPHERE, bbox=bbox, aoi=aoi, point=point, geojson=geojson, start_date=start_date, end_date=end_date, variables=variables)
        return results[0] if results else None

    def get_fire(
        self,
        bbox: Optional[List[float]] = None,
        aoi: Optional[AOI] = None,
        point: Optional[tuple] = None,
        geojson: Optional[Union[str, dict, Any]] = None,
        start_date: Optional[str] = None
    ) -> Optional[SearchResult]:
        """Instant convenience shortcut to fetch active fire hotspots and thermal anomalies."""
        results = self.search(category=Category.FIRE, bbox=bbox, aoi=aoi, point=point, geojson=geojson, start_date=start_date)
        return results[0] if results else None

    def get_ocean(
        self,
        bbox: Optional[List[float]] = None,
        aoi: Optional[AOI] = None,
        point: Optional[tuple] = None,
        geojson: Optional[Union[str, dict, Any]] = None,
        start_date: Optional[str] = None
    ) -> Optional[SearchResult]:
        """Instant convenience shortcut to fetch Sentinel-3 ocean color & SST data."""
        results = self.search(category=Category.OCEAN, bbox=bbox, aoi=aoi, point=point, geojson=geojson, start_date=start_date)
        return results[0] if results else None

    def get_altimetry(
        self,
        bbox: Optional[List[float]] = None,
        aoi: Optional[AOI] = None,
        point: Optional[tuple] = None,
        geojson: Optional[Union[str, dict, Any]] = None,
        start_date: Optional[str] = None
    ) -> Optional[SearchResult]:
        """Instant convenience shortcut to fetch Sentinel-6 radar altimetry & wave height."""
        results = self.search(category=Category.ALTIMETRY, bbox=bbox, aoi=aoi, point=point, geojson=geojson, start_date=start_date)
        return results[0] if results else None

    def get_precipitation(
        self,
        bbox: Optional[List[float]] = None,
        aoi: Optional[AOI] = None,
        point: Optional[tuple] = None,
        geojson: Optional[Union[str, dict, Any]] = None,
        start_date: Optional[str] = None
    ) -> Optional[SearchResult]:
        """Instant convenience shortcut to fetch GPM & CHIRPS high-resolution rainfall."""
        results = self.search(category=Category.PRECIPITATION, bbox=bbox, aoi=aoi, point=point, geojson=geojson, start_date=start_date)
        return results[0] if results else None

    def get_hydrology(
        self,
        bbox: Optional[List[float]] = None,
        aoi: Optional[AOI] = None,
        point: Optional[tuple] = None,
        geojson: Optional[Union[str, dict, Any]] = None,
        start_date: Optional[str] = None
    ) -> Optional[SearchResult]:
        """Instant convenience shortcut to fetch SMAP root-zone soil moisture."""
        results = self.search(category=Category.HYDROLOGY, bbox=bbox, aoi=aoi, point=point, geojson=geojson, start_date=start_date)
        return results[0] if results else None

    def get_nightlights(
        self,
        bbox: Optional[List[float]] = None,
        aoi: Optional[AOI] = None,
        point: Optional[tuple] = None,
        geojson: Optional[Union[str, dict, Any]] = None,
        start_date: Optional[str] = None
    ) -> Optional[SearchResult]:
        """Instant convenience shortcut to fetch VIIRS Black Marble nocturnal lights."""
        results = self.search(category=Category.NIGHTLIGHTS, bbox=bbox, aoi=aoi, point=point, geojson=geojson, start_date=start_date)
        return results[0] if results else None

    def get_optical(
        self,
        bbox: Optional[List[float]] = None,
        aoi: Optional[AOI] = None,
        point: Optional[tuple] = None,
        geojson: Optional[Union[str, dict, Any]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        max_cloud_cover: float = 20.0,
        level: str = "sr"
    ) -> Optional[SearchResult]:
        """Convenience shortcut to fetch an Optical scene (Sentinel-2 L2A SR or L1C TOA)."""
        results = self.search(
            category=Category.OPTICAL,
            bbox=bbox,
            aoi=aoi,
            point=point,
            geojson=geojson,
            start_date=start_date,
            end_date=end_date,
            max_cloud_cover=max_cloud_cover,
            level=level,
            limit=1
        )
        return results[0] if results else None

    def get_sar(
        self,
        bbox: Optional[List[float]] = None,
        aoi: Optional[AOI] = None,
        point: Optional[tuple] = None,
        geojson: Optional[Union[str, dict, Any]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Optional[SearchResult]:
        """Convenience shortcut to fetch a Sentinel-1 SAR scene."""
        results = self.search(
            category=Category.SAR,
            bbox=bbox,
            aoi=aoi,
            point=point,
            geojson=geojson,
            start_date=start_date,
            end_date=end_date,
            limit=1
        )
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
        l_factor: float = 0.5,
        outpath: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Computes standard remote sensing radiometric & biophysical indices:
        - ndvi: (nir - red) / (nir + red)
        - ndwi: (green - nir) / (green + nir)
        - ndre: (nir - rededge) / (nir + rededge)
        - evi:  2.5 * (nir - red) / (nir + 6*red - 7.5*blue + 1)
        - nbr:  (nir - swir) / (nir + swir)
        - savi: (1 + L) * (nir - red) / (nir + red + L)
        - msavi: 0.5 * (2*nir + 1 - sqrt((2*nir + 1)^2 - 8*(nir - red)))
        - bsi:  ((swir + red) - (nir + blue)) / ((swir + red) + (nir + blue))
        - mndwi: (green - swir) / (green + swir)
        """
        return compute_spectral_index(
            index=index,
            nir=nir,
            red=red,
            green=green,
            blue=blue,
            rededge=rededge,
            swir=swir,
            l_factor=l_factor,
            outpath=outpath
        )

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

        if cat_enum in (Category.WEATHER, Category.ATMOSPHERE) and results:
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
