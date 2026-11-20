"""
OmniEarth Copernicus Data Space Ecosystem (CDSE) Provider Adapter
==================================================================
Provides direct access to official ESA Copernicus archives:
- Full raw .SAFE ZIP product archives (Sentinel-1, Sentinel-2, Sentinel-3, Sentinel-5P).
- Selective band streaming via CDSE OData /Nodes tree traversal (saves 90% bandwidth).
- Cryptographic MD5 and SHA-256 integrity validation.
- Thread-safe OAuth2 Bearer token management with auto-refresh.
"""

import logging
import os
import re
import threading
import time
from typing import Any, Dict, List, Optional, Tuple, Union
import requests

from omniearth.models import AOI, SearchResult, Asset, Category, FilterOptions
from omniearth.providers.base import BaseProvider
from omniearth.config import config

logger = logging.getLogger(__name__)

UUID_REGEX = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)

# Standard Band and Polarization Presets
S2_BAND_PRESETS = {
    "rgb": ["TCI", "B04", "B03", "B02"],
    "tci": ["TCI"],
    "vnir": ["B02", "B03", "B04", "B08"],
    "ndvi": ["B04", "B08"],
    "ndwi": ["B03", "B08"],
    "swir": ["B11", "B12", "B8A"],
    "scl": ["SCL"],
    "10m": ["B02", "B03", "B04", "B08", "TCI"],
    "20m": ["B05", "B06", "B07", "B8A", "B11", "B12", "SCL"],
    "all": [
        "B01", "B02", "B03", "B04", "B05", "B06", "B07", "B08",
        "B8A", "B09", "B11", "B12", "TCI", "SCL", "AOT", "WVP"
    ],
}

S1_POLARIZATION_PRESETS = {
    "vh": ["vh"],
    "vv": ["vv"],
    "dual": ["vh", "vv"],
    "hh": ["hh"],
    "hv": ["hv"],
    "all": ["vh", "vv", "hh", "hv"],
}


class CDSEAuthManager:
    """Manages thread-safe OAuth2 access tokens for CDSE API requests."""
    IDENTITY_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
    TOKEN_LIFETIME_SEC = 540  # 9 minutes

    def __init__(self, username: Optional[str] = None, password: Optional[str] = None):
        self._username = username
        self._password = password
        self._token: Optional[str] = None
        self._token_timestamp: float = 0
        self._lock = threading.Lock()

    def get_credentials(self) -> Tuple[Optional[str], Optional[str]]:
        u = self._username or config.cdse_credentials[0]
        p = self._password or config.cdse_credentials[1]
        return u, p

    def get_token(self, force_refresh: bool = False) -> str:
        """Retrieves a valid bearer token, refreshing automatically when expired."""
        u, p = self.get_credentials()
        if not u or not p:
            raise ValueError(
                "Missing CDSE credentials for official Copernicus download. "
                "Set CDSE_USERNAME and CDSE_PASSWORD (or SENTINEL_USER and SENTINEL_PASS) in .env "
                "or pass them to OmniEarth. Free registration: https://dataspace.copernicus.eu/"
            )

        with self._lock:
            now = time.time()
            if not force_refresh and self._token and (now - self._token_timestamp < self.TOKEN_LIFETIME_SEC):
                return self._token

            try:
                resp = requests.post(
                    self.IDENTITY_URL,
                    data={
                        "grant_type": "password",
                        "username": u,
                        "password": p,
                        "client_id": "cdse-public"
                    },
                    timeout=config.timeout
                )
                if resp.status_code in (400, 401):
                    raise ValueError(
                        f"CDSE authentication failed ({resp.status_code}): Invalid username or password. "
                        "Please verify your credentials at https://dataspace.copernicus.eu/"
                    )
                resp.raise_for_status()
                data = resp.json()
                self._token = data.get("access_token")
                self._token_timestamp = time.time()
                if not self._token:
                    raise ValueError("CDSE authentication response did not contain an access_token.")
                return self._token
            except requests.exceptions.RequestException as exc:
                raise RuntimeError(f"Network error connecting to CDSE authentication service: {exc}") from exc


class CDSEProvider(BaseProvider):
    """
    Copernicus Data Space Ecosystem (CDSE) Provider Adapter.
    Supports official Sentinel-1, Sentinel-2, Sentinel-3, and Sentinel-5P archives.
    """
    category = Category.OPTICAL
    name = "cdse"

    CATALOGUE_URL = "https://catalogue.dataspace.copernicus.eu/odata/v1"
    DOWNLOAD_URL = "https://download.dataspace.copernicus.eu/odata/v1"
    ZIPPER_URL = "https://zipper.dataspace.copernicus.eu/odata/v1"
    STAC_URL = "https://stac.dataspace.copernicus.eu/v1"

    def __init__(self, auth_manager: Optional[CDSEAuthManager] = None):
        self.auth = auth_manager or CDSEAuthManager()

    def _api_get(self, url: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Makes an authenticated GET request with the CDSE bearer token."""
        token = self.auth.get_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }
        resp = requests.get(url, headers=headers, params=params, timeout=config.timeout)
        if resp.status_code in (401, 403):
            # Token might have expired early; force refresh once
            token = self.auth.get_token(force_refresh=True)
            headers["Authorization"] = f"Bearer {token}"
            resp = requests.get(url, headers=headers, params=params, timeout=config.timeout)

        resp.raise_for_status()
        return resp.json()

    def _extract_values(self, json_data: Any) -> List[Dict[str, Any]]:
        """Normalizes OData responses into a list of items."""
        if isinstance(json_data, dict):
            if "value" in json_data:
                return json_data["value"]
            if "result" in json_data:
                return json_data["result"]
            return [json_data]
        if isinstance(json_data, list):
            return json_data
        return []

    def _resolve_collection(self, category: Category, requested: Optional[str] = None) -> str:
        """Resolves CDSE collection name from category or filter."""
        if requested:
            req_up = requested.upper()
            if req_up in ("SENTINEL-1", "S1"):
                return "SENTINEL-1"
            if req_up in ("SENTINEL-2", "S2"):
                return "SENTINEL-2"
            if req_up in ("SENTINEL-3", "S3"):
                return "SENTINEL-3"
            if req_up in ("SENTINEL-5P", "S5P"):
                return "SENTINEL-5P"
            return req_up

        if category == Category.SAR:
            return "SENTINEL-1"
        if category == Category.OCEAN:
            return "SENTINEL-3"
        if category == Category.ATMOSPHERE:
            return "SENTINEL-5P"
        return "SENTINEL-2"

    def search(
        self,
        aoi: AOI,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        filters: Optional[FilterOptions] = None
    ) -> List[SearchResult]:
        limit = filters.limit if filters else 10
        collection = self._resolve_collection(self.category, filters.dataset if filters else None)
        
        # Try STAC search first
        try:
            return self._search_stac(aoi, collection, start_date, end_date, filters, limit)
        except Exception as exc:
            logger.debug(f"CDSE STAC query fallback to OData: {exc}")
            return self._search_odata(aoi, collection, start_date, end_date, filters, limit)

    def _search_stac(
        self,
        aoi: AOI,
        collection: str,
        start_date: Optional[str],
        end_date: Optional[str],
        filters: Optional[FilterOptions],
        limit: int
    ) -> List[SearchResult]:
        search_url = f"{self.STAC_URL}/search"
        payload: Dict[str, Any] = {
            "collections": [collection],
            "limit": limit
        }
        if aoi and aoi.bbox:
            payload["bbox"] = aoi.bbox

        if start_date and end_date:
            s = start_date if "T" in start_date else f"{start_date}T00:00:00Z"
            e = end_date if "T" in end_date else f"{end_date}T23:59:59Z"
            payload["datetime"] = f"{s}/{e}"
        elif start_date:
            s = start_date if "T" in start_date else f"{start_date}T00:00:00Z"
            payload["datetime"] = f"{s}/.."
        elif end_date:
            e = end_date if "T" in end_date else f"{end_date}T23:59:59Z"
            payload["datetime"] = f"../{e}"

        if filters and filters.max_cloud_cover is not None:
            payload["query"] = {"eo:cloud_cover": {"lte": filters.max_cloud_cover}}

        # CDSE STAC search supports public queries or token queries
        token = None
        try:
            token = self.auth.get_token()
        except Exception:
            pass

        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        resp = requests.post(search_url, json=payload, headers=headers, timeout=config.timeout)
        resp.raise_for_status()
        features = resp.json().get("features", [])

        results: List[SearchResult] = []
        for feat in features:
            props = feat.get("properties", {})
            feat_id = feat.get("id", "")
            cdse_id = props.get("id") or feat_id
            product_name = props.get("title") or feat_id
            cloud = props.get("eo:cloud_cover")
            dt = props.get("datetime")
            bbox = feat.get("bbox") or (aoi.bbox if aoi else None)

            assets_dict: Dict[str, Asset] = {}
            for k, a in feat.get("assets", {}).items():
                assets_dict[k] = Asset(
                    key=k,
                    href=a.get("href", ""),
                    title=a.get("title", k),
                    media_type=a.get("type"),
                    roles=a.get("roles", [])
                )

            # Ensure 'full' raw .SAFE archive download asset is present
            if "full" not in assets_dict and "safe" not in assets_dict:
                assets_dict["full"] = Asset(
                    key="full",
                    href=f"{self.DOWNLOAD_URL}/Products({cdse_id})/$value",
                    title=f"{product_name}.zip",
                    media_type="application/zip",
                    roles=["archive", "safe"]
                )

            results.append(SearchResult(
                id=product_name,
                collection=collection,
                category=self.category,
                provider="cdse",
                datetime=dt,
                bbox=bbox,
                properties={
                    "cdse_id": cdse_id,
                    "title": product_name,
                    "cloud_cover": cloud,
                    "geometry": feat.get("geometry")
                },
                assets=assets_dict
            ))
        return results

    def _search_odata(
        self,
        aoi: AOI,
        collection: str,
        start_date: Optional[str],
        end_date: Optional[str],
        filters: Optional[FilterOptions],
        limit: int
    ) -> List[SearchResult]:
        filter_parts = [f"Collection/Name eq '{collection}'"]
        if start_date:
            s = start_date if "T" in start_date else f"{start_date}T00:00:00.000Z"
            filter_parts.append(f"ContentDate/Start ge {s}")
        if end_date:
            e = end_date if "T" in end_date else f"{end_date}T23:59:59.999Z"
            filter_parts.append(f"ContentDate/Start le {e}")

        if aoi and aoi.bbox:
            min_lon, min_lat, max_lon, max_lat = aoi.bbox
            poly_wkt = f"POLYGON(({min_lon} {min_lat}, {max_lon} {min_lat}, {max_lon} {max_lat}, {min_lon} {max_lat}, {min_lon} {min_lat}))"
            filter_parts.append(f"OData.CSC.Intersects(area=geography'SRID=4326;{poly_wkt}')")

        if filters and filters.max_cloud_cover is not None:
            filter_parts.append(
                f"Attributes/OData.CSC.DoubleAttribute/any(att:att/Name eq 'cloudCover' and att/OData.CSC.DoubleAttribute/Value le {filters.max_cloud_cover})"
            )

        params = {
            "$filter": " and ".join(filter_parts),
            "$top": limit,
            "$orderby": "ContentDate/Start desc",
            "$expand": "Attributes,Checksum"
        }
        url = f"{self.CATALOGUE_URL}/Products"
        data = self._api_get(url, params=params)
        items = self._extract_values(data)

        results: List[SearchResult] = []
        for it in items:
            results.append(self._build_search_result_from_odata(it, collection))
        return results

    def _build_search_result_from_odata(self, data: Dict[str, Any], collection: str) -> SearchResult:
        product_id = data.get("Id", "")
        product_name = data.get("Name", "")
        checksum_val = None
        checksum_algo = "MD5"
        chk_list = data.get("Checksum", [])
        if chk_list and isinstance(chk_list, list) and len(chk_list) > 0:
            checksum_val = chk_list[0].get("Value")
            checksum_algo = chk_list[0].get("Algorithm", "MD5")

        cloud = None
        for att in data.get("Attributes", []):
            if att.get("Name") == "cloudCover":
                cloud = float(att.get("Value", 0.0))
                break

        assets_dict = {
            "full": Asset(
                key="full",
                href=f"{self.DOWNLOAD_URL}/Products({product_id})/$value",
                title=f"{product_name}.zip",
                media_type="application/zip",
                size_bytes=data.get("ContentLength"),
                roles=["archive", "safe"],
                checksum=checksum_val,
                checksum_algorithm=checksum_algo
            )
        }

        content_date = data.get("ContentDate", {})
        dt = content_date.get("Start") or data.get("PublicationDate")

        return SearchResult(
            id=product_name,
            collection=collection,
            category=self.category,
            provider="cdse",
            datetime=dt,
            properties={
                "cdse_id": product_id,
                "title": product_name,
                "cloud_cover": cloud,
                "checksum": checksum_val,
                "checksum_algorithm": checksum_algo,
                "content_length": data.get("ContentLength"),
                "geometry": data.get("GeoFootprint")
            },
            assets=assets_dict
        )

    def get_item(self, item_id: str) -> Optional[SearchResult]:
        """Directly retrieves product metadata from CDSE by UUID or SAFE product name."""
        item_id = item_id.strip()
        try:
            if UUID_REGEX.match(item_id):
                url = f"{self.CATALOGUE_URL}/Products({item_id})"
                params = {"$expand": "Attributes,Checksum"}
                data = self._api_get(url, params=params)
                collection = data.get("Collection", {}).get("Name", "SENTINEL-2")
                return self._build_search_result_from_odata(data, collection)

            url = f"{self.CATALOGUE_URL}/Products"
            params = {"$filter": f"Name eq '{item_id}'", "$expand": "Attributes,Checksum"}
            data = self._api_get(url, params=params)
            items = self._extract_values(data)
            if items:
                collection = items[0].get("Collection", {}).get("Name", "SENTINEL-2")
                return self._build_search_result_from_odata(items[0], collection)
        except Exception as exc:
            logger.debug(f"CDSE get_item error for '{item_id}': {exc}")
        return None

    def _find_files_recursive(self, node: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Recursively traverses OData product node hierarchy to discover individual files."""
        files: List[Dict[str, Any]] = []
        nodes_uri = node.get("Nodes", {}).get("uri")

        if not nodes_uri:
            node_id = node.get("Id")
            download_url = f"{self.CATALOGUE_URL}/Nodes({node_id})/$value"
            files.append({
                "id": node.get("Id", ""),
                "name": node.get("Name", ""),
                "download_url": download_url,
                "size_bytes": node.get("ContentLength", 0)
            })
            return files

        child_response = self._api_get(nodes_uri)
        children = self._extract_values(child_response)

        for child in children:
            if child.get("ChildrenNumber", 0) == 0:
                child_uri = child.get("Nodes", {}).get("uri", "")
                download_url = child_uri.rstrip("/Nodes") + "/$value" if child_uri else f"{self.CATALOGUE_URL}/Nodes({child.get('Id')})/$value"
                files.append({
                    "id": child.get("Id", ""),
                    "name": child.get("Name", ""),
                    "download_url": download_url,
                    "size_bytes": child.get("ContentLength", 0)
                })
            else:
                files.extend(self._find_files_recursive(child))
        return files

    def list_product_files(self, product_id_or_name: str) -> List[Dict[str, Any]]:
        """Lists all individual asset files inside a .SAFE product package."""
        item = self.get_item(product_id_or_name)
        if not item:
            raise ValueError(f"Product '{product_id_or_name}' not found on CDSE.")
        cdse_id = item.properties.get("cdse_id") or item.id
        root_url = f"{self.CATALOGUE_URL}/Products({cdse_id})/Nodes"
        root_nodes = self._extract_values(self._api_get(root_url))
        files: List[Dict[str, Any]] = []
        for root_node in root_nodes:
            files.extend(self._find_files_recursive(root_node))
        return files

    def resolve_requested_bands(self, requested: Optional[str], mission: str = "sentinel2") -> List[str]:
        """Resolves band preset string or comma-separated list into normalized band identifiers."""
        if not requested:
            return S2_BAND_PRESETS["rgb"] if mission == "sentinel2" else S1_POLARIZATION_PRESETS["dual"]

        req_clean = requested.strip().lower()
        if mission == "sentinel2" and req_clean in S2_BAND_PRESETS:
            return S2_BAND_PRESETS[req_clean]
        if mission == "sentinel1" and req_clean in S1_POLARIZATION_PRESETS:
            return S1_POLARIZATION_PRESETS[req_clean]

        return [b.strip() for b in requested.split(",") if b.strip()]

    def find_files_for_bands(
        self,
        product_id_or_name: str,
        requested_bands: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Finds individual files matching requested bands within the product's remote file tree."""
        all_files = self.list_product_files(product_id_or_name)
        is_s1 = "S1" in product_id_or_name.upper()
        mission = "sentinel1" if is_s1 else "sentinel2"
        target_bands = self.resolve_requested_bands(requested_bands, mission=mission)
        target_bands_lower = [b.lower() for b in target_bands]

        matched: List[Dict[str, Any]] = []
        for pfile in all_files:
            fname = pfile["name"].lower()
            if not is_s1:
                # Sentinel-2 JP2 band files
                if fname.endswith(".jp2"):
                    for band in target_bands_lower:
                        if f"_{band}_" in fname or f"_{band}." in fname or fname.startswith(f"{band}_"):
                            if pfile not in matched:
                                matched.append(pfile)
            else:
                # Sentinel-1 GeoTIFF polarization files
                if fname.endswith(".tiff") or fname.endswith(".tif"):
                    for pol in target_bands_lower:
                        if f"-{pol}-" in fname or f"_{pol}_" in fname or f"{pol}" in fname:
                            if pfile not in matched:
                                matched.append(pfile)
        return matched

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
        verify_checksum: bool = False
    ) -> str:
        """
        Downloads either:
        1. Selective band rasters (.jp2 / .tif) via /Nodes node traversal (saving 90% bandwidth).
        2. Full official .SAFE ZIP archive with byte-range resume and cryptographic verification.
        """
        outdir_str = outdir or config.default_outdir
        os.makedirs(outdir_str, exist_ok=True)
        token = self.auth.get_token()
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Selective Node Band Extraction
        bands_str = ",".join(bands) if isinstance(bands, list) else bands
        if not bands_str and asset_key and asset_key.upper() in (
            "B01", "B02", "B03", "B04", "B05", "B06", "B07", "B08", "B8A", "B09", "B11", "B12", "VV", "VH", "HH", "HV"
        ):
            bands_str = asset_key.upper()

        if format in ("node", "band") or bands_str:
            cdse_id = result.properties.get("cdse_id") or result.id
            matched_files = self.find_files_for_bands(cdse_id, bands_str)
            if not matched_files:
                raise ValueError(
                    f"No matching band files found for '{bands_str}' in product '{result.id}'"
                )
            product_folder = os.path.join(outdir_str, result.id)
            os.makedirs(product_folder, exist_ok=True)

            downloaded_paths = []
            for f in matched_files:
                band_outpath = os.path.join(product_folder, f["name"])
                dl_path = self._stream_download(
                    url=f["download_url"],
                    outpath=band_outpath,
                    headers=headers,
                    desc=f["name"],
                    resume=resume,
                    multipart=multipart,
                    max_workers=max_workers
                )
                downloaded_paths.append(dl_path)
            return downloaded_paths[0] if len(downloaded_paths) == 1 else product_folder

        # 2. Full .SAFE ZIP Archive Download
        resolved_key = result.resolve_asset_key(asset_key)
        target_asset = (result.assets.get(resolved_key) if resolved_key else None) or result.assets.get("full") or result.assets.get("safe")
        if not target_asset or not target_asset.href:
            cdse_id = result.properties.get("cdse_id") or result.id
            dl_url = f"{self.DOWNLOAD_URL}/Products({cdse_id})/$value"
        else:
            dl_url = target_asset.href

        out_filename = f"{result.id}.zip" if not result.id.endswith(".zip") else result.id
        outpath = os.path.join(outdir_str, out_filename)

        expected_chk = result.checksum
        chk_algo = result.checksum_algorithm or "MD5"

        return self._stream_download(
            url=dl_url,
            outpath=outpath,
            headers=headers,
            desc=result.id[:20],
            resume=resume,
            multipart=multipart,
            max_workers=max_workers,
            expected_checksum=expected_chk,
            checksum_algorithm=chk_algo,
            verify_checksum=verify_checksum
        )

