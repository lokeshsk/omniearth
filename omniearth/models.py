"""
OmniEarth Data Models
=====================
Standardized representations for areas of interest, search results, and assets.
"""

import os
from pathlib import Path
from enum import Enum
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, PrivateAttr, model_validator


class Category(str, Enum):
    OPTICAL = "optical"
    SAR = "sar"
    HYPERSPECTRAL = "hyperspectral"
    WEATHER = "weather"
    SOIL = "soil"
    ELEVATION = "elevation"
    LANDCOVER = "landcover"
    ATMOSPHERE = "atmosphere"
    FIRE = "fire"
    OCEAN = "ocean"
    ALTIMETRY = "altimetry"
    PRECIPITATION = "precipitation"
    HYDROLOGY = "hydrology"
    NIGHTLIGHTS = "nightlights"


def _point_in_polygon(x: float, y: float, polygon_ring: List[List[float]]) -> bool:
    """Ray casting algorithm to determine if point (x, y) is inside a polygon ring."""
    inside = False
    n = len(polygon_ring)
    if n < 3:
        return False
    p1x, p1y = polygon_ring[0]
    for i in range(1, n + 1):
        p2x, p2y = polygon_ring[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside


class AOI(BaseModel):
    """Area of Interest representation (WGS84 [min_lon, min_lat, max_lon, max_lat])."""
    bbox: List[float] = Field(..., description="[min_lon, min_lat, max_lon, max_lat]")
    geometry: Optional[Dict[str, Any]] = Field(default=None, description="Optional GeoJSON geometry dictionary")

    @model_validator(mode="after")
    def validate_bbox(self) -> "AOI":
        if len(self.bbox) != 4:
            raise ValueError("AOI bbox must contain exactly 4 coordinates: [min_lon, min_lat, max_lon, max_lat]")
        min_lon, min_lat, max_lon, max_lat = self.bbox
        if min_lon > max_lon:
            raise ValueError(f"min_lon ({min_lon}) cannot be greater than max_lon ({max_lon})")
        if min_lat > max_lat:
            raise ValueError(f"min_lat ({min_lat}) cannot be greater than max_lat ({max_lat})")
        return self

    @classmethod
    def from_bounds(cls, min_lon: float, min_lat: float, max_lon: float, max_lat: float, geometry: Optional[Dict[str, Any]] = None) -> "AOI":
        return cls(bbox=[min_lon, min_lat, max_lon, max_lat], geometry=geometry)

    @classmethod
    def from_point(cls, lon: float, lat: float, radius_km: float = 5.0) -> "AOI":
        """Approximates a bounding box around a lat/lon center point."""
        deg_lat = radius_km / 111.0
        deg_lon = radius_km / (111.0 * max(0.1, abs(1.0 - (lat / 90.0))))
        return cls(bbox=[
            round(lon - deg_lon, 5),
            round(lat - deg_lat, 5),
            round(lon + deg_lon, 5),
            round(lat + deg_lat, 5)
        ])

    @classmethod
    def from_geojson(cls, geojson_source: Union[str, dict, Any]) -> "AOI":
        """
        Derives an AOI from a GeoJSON file path, JSON string, or dict structure.
        Recursively scans coordinates to find [min_lon, min_lat, max_lon, max_lat]
        and captures the primary geometry.
        """
        import json
        from pathlib import Path

        data = None
        if isinstance(geojson_source, (str, Path)) and os.path.exists(str(geojson_source)):
            with open(str(geojson_source), "r", encoding="utf-8") as f:
                data = json.load(f)
        elif isinstance(geojson_source, str):
            data = json.loads(geojson_source)
        elif isinstance(geojson_source, dict):
            data = geojson_source
        else:
            raise ValueError(f"Invalid GeoJSON source: {type(geojson_source)}")

        coords: List[List[float]] = []
        primary_geom: Optional[Dict[str, Any]] = None

        if isinstance(data, dict):
            if "type" in data and data["type"] in ("Polygon", "MultiPolygon", "Point", "LineString"):
                primary_geom = data
            elif "geometry" in data and isinstance(data["geometry"], dict):
                primary_geom = data["geometry"]
            elif "features" in data and isinstance(data["features"], list) and len(data["features"]) > 0:
                feat = data["features"][0]
                if isinstance(feat, dict) and "geometry" in feat:
                    primary_geom = feat["geometry"]

        def extract_coords(obj):
            if isinstance(obj, dict):
                if "coordinates" in obj:
                    extract_coords(obj["coordinates"])
                elif "features" in obj:
                    for feat in obj["features"]:
                        extract_coords(feat.get("geometry", {}))
                elif "geometry" in obj:
                    extract_coords(obj["geometry"])
                elif "geometries" in obj:
                    for g in obj["geometries"]:
                        extract_coords(g)
            elif isinstance(obj, (list, tuple)):
                if len(obj) >= 2 and isinstance(obj[0], (int, float)) and isinstance(obj[1], (int, float)):
                    coords.append([float(obj[0]), float(obj[1])])
                else:
                    for item in obj:
                        extract_coords(item)

        extract_coords(data)
        if not coords:
            raise ValueError("No valid coordinates found in GeoJSON structure")

        min_lon = min(c[0] for c in coords)
        max_lon = max(c[0] for c in coords)
        min_lat = min(c[1] for c in coords)
        max_lat = max(c[1] for c in coords)
        return cls(bbox=[min_lon, min_lat, max_lon, max_lat], geometry=primary_geom)

    def contains(self, lon: float, lat: float) -> bool:
        """
        Tests whether the geographic point (lon, lat) falls within this AOI.
        If a Polygon or MultiPolygon geometry is attached, performs point-in-polygon ray casting.
        Otherwise, tests bounding box containment.
        """
        in_bbox = (self.min_lon <= lon <= self.max_lon) and (self.min_lat <= lat <= self.max_lat)
        if not in_bbox or not self.geometry:
            return in_bbox

        gtype = self.geometry.get("type")
        coords = self.geometry.get("coordinates")
        if not coords:
            return in_bbox

        if gtype == "Polygon":
            # Exterior ring is coords[0]
            if not _point_in_polygon(lon, lat, coords[0]):
                return False
            # Check interior holes: if in any hole, not inside
            for hole in coords[1:]:
                if _point_in_polygon(lon, lat, hole):
                    return False
            return True
        elif gtype == "MultiPolygon":
            for poly in coords:
                if _point_in_polygon(lon, lat, poly[0]):
                    # Check holes in this polygon
                    in_hole = False
                    for hole in poly[1:]:
                        if _point_in_polygon(lon, lat, hole):
                            in_hole = True
                            break
                    if not in_hole:
                        return True
            return False
        return in_bbox

    @property
    def min_lon(self) -> float:
        return self.bbox[0]

    @property
    def min_lat(self) -> float:
        return self.bbox[1]

    @property
    def max_lon(self) -> float:
        return self.bbox[2]

    @property
    def max_lat(self) -> float:
        return self.bbox[3]

    def to_bbox_string(self) -> str:
        return f"{self.min_lon},{self.min_lat},{self.max_lon},{self.max_lat}"


class Asset(BaseModel):
    """Represents a downloadable file or data stream."""
    key: str
    href: str
    title: Optional[str] = None
    media_type: Optional[str] = None
    size_bytes: Optional[int] = None
    roles: List[str] = Field(default_factory=list)
    checksum: Optional[str] = None
    checksum_algorithm: Optional[str] = "MD5"


class SearchResult(BaseModel):
    """Universal search result item returned across any category or provider."""
    id: str
    collection: str
    category: Category
    provider: str
    datetime: Optional[str] = None
    bbox: Optional[List[float]] = None
    properties: Dict[str, Any] = Field(default_factory=dict)
    assets: Dict[str, Asset] = Field(default_factory=dict)
    _client: Optional[Any] = PrivateAttr(default=None)

    @property
    def cloud_cover(self) -> Optional[float]:
        return self.properties.get("eo:cloud_cover") or self.properties.get("cloud_cover")

    @property
    def checksum(self) -> Optional[str]:
        return self.properties.get("checksum") or self.properties.get("digest")

    @property
    def checksum_algorithm(self) -> str:
        return self.properties.get("checksum_algorithm") or "MD5"

    @property
    def footprint(self) -> Optional[Dict[str, Any]]:
        if "geometry" in self.properties and self.properties["geometry"]:
            return self.properties["geometry"]
        if self.bbox and len(self.bbox) == 4:
            min_lon, min_lat, max_lon, max_lat = self.bbox
            if min_lon == max_lon and min_lat == max_lat:
                return {
                    "type": "Point",
                    "coordinates": [min_lon, min_lat]
                }
            return {
                "type": "Polygon",
                "coordinates": [[
                    [min_lon, min_lat],
                    [max_lon, min_lat],
                    [max_lon, max_lat],
                    [min_lon, max_lat],
                    [min_lon, min_lat]
                ]]
            }
        lat = self.properties.get("latitude") or self.properties.get("center_lat") or self.properties.get("lat")
        lon = self.properties.get("longitude") or self.properties.get("center_lon") or self.properties.get("lon")
        if lat is not None and lon is not None:
            return {
                "type": "Point",
                "coordinates": [float(lon), float(lat)]
            }
        return None

    def resolve_asset_key(self, query: Optional[str] = None) -> Optional[str]:
        """
        Resolves friendly asset names/aliases or selects the primary science asset.
        Supports aliases: 'data', 'rfl', 'cube', 'nc', 'image', 'visual', 'uncert',
        'mask', 'browse', 'preview', 'metadata', or partial/case-insensitive key matching.
        """
        if not self.assets:
            return None

        if not query or not str(query).strip():
            for k in ("data", "image", "visual", "SPECTRAL_IMAGE_COG", "dem", "map"):
                if k in self.assets:
                    return k
            for k, a in self.assets.items():
                if k.startswith("s3_") or "s3://" in (a.href or ""):
                    continue
                k_lower = k.lower()
                href_lower = (a.href or "").lower()
                if any(skip in k_lower for skip in ("browse", "thumbnail", "uncert", "mask", "metadata", "xml")):
                    continue
                if any(ext in href_lower for ext in (".nc", ".he5", ".tif", ".tiff", ".zip", ".tar", ".safe")):
                    return k
                if "rfl" in k_lower or "reflectance" in k_lower or "cube" in k_lower:
                    return k
            for k, a in self.assets.items():
                if not k.startswith("s3_") and "s3://" not in (a.href or ""):
                    return k
            return next(iter(self.assets.keys()))

        q = str(query).strip().lower()
        if query in self.assets:
            return query
        for k in self.assets:
            if k.lower() == q:
                return k

        if q in ("data", "cube", "science", "rfl", "reflectance", "nc", "image"):
            for k, a in self.assets.items():
                if k.startswith("s3_") or "s3://" in (a.href or ""):
                    continue
                k_lower = k.lower()
                href_lower = (a.href or "").lower()
                if any(skip in k_lower for skip in ("browse", "thumbnail", "uncert", "mask", "metadata")):
                    continue
                if any(ext in href_lower for ext in (".nc", ".he5", ".tif", ".tiff")) or "rfl" in k_lower:
                    return k
        elif q in ("uncert", "uncertainty"):
            for k in self.assets:
                if "uncert" in k.lower() and not k.startswith("s3_"):
                    return k
        elif q in ("mask", "cloud_mask", "qa"):
            for k in self.assets:
                if "mask" in k.lower() and not k.startswith("s3_"):
                    return k
        elif q in ("browse", "preview", "thumbnail", "thumb", "png", "jpg", "jpeg"):
            for k in self.assets:
                if any(w in k.lower() for w in ("browse", "thumbnail", "preview")) and not k.startswith("s3_"):
                    return k
        elif q in ("metadata", "meta", "xml", "info"):
            for k in self.assets:
                if any(w in k.lower() for w in ("metadata", "meta", "xml")):
                    return k

        for k in self.assets:
            if not k.startswith("s3_") and q in k.lower():
                return k

        for k in self.assets:
            if q in k.lower():
                return k

        return None

    def get_download_url(self, preferred_key: str = "data") -> Optional[str]:
        """Returns the primary asset download URL."""
        resolved = self.resolve_asset_key(preferred_key)
        if resolved and resolved in self.assets:
            return self.assets[resolved].href
        if "data" in self.assets:
            return self.assets["data"].href
        if "image" in self.assets:
            return self.assets["image"].href
        if self.assets:
            return next(iter(self.assets.values())).href
        return None

    def download(
        self,
        asset_key: Optional[str] = None,
        outdir: Optional[str] = None,
        resume: bool = True,
        multipart: bool = True,
        max_workers: int = 4,
        client: Optional[Any] = None,
        **kwargs
    ) -> str:
        """Download this result directly to local storage."""
        active_client = client or self._client
        if not active_client:
            from omniearth.client import OmniEarth
            active_client = OmniEarth()
        return active_client.download(
            result=self,
            asset_key=asset_key,
            outdir=outdir,
            resume=resume,
            multipart=multipart,
            max_workers=max_workers,
            **kwargs
        )

    def download_all(
        self,
        asset_keys: Optional[List[str]] = None,
        outdir: Optional[str] = None,
        max_workers: int = 4,
        resume: bool = True,
        multipart: bool = True,
        client: Optional[Any] = None,
        **kwargs
    ) -> Dict[str, str]:
        """Download all or selected assets of this result concurrently."""
        active_client = client or self._client
        if not active_client:
            from omniearth.client import OmniEarth
            active_client = OmniEarth()
        return active_client.download_all(
            result=self,
            asset_keys=asset_keys,
            outdir=outdir,
            max_workers=max_workers,
            resume=resume,
            multipart=multipart,
            **kwargs
        )

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serializable dictionary representation."""
        return self.model_dump(mode="json")


class SearchResults(list):
    """
    List-compatible collection of SearchResult items with fluent batch download
    and filtering methods.
    """
    def __init__(self, iterable=None, client: Optional[Any] = None):
        super().__init__(iterable or [])
        self._client = client
        if self._client:
            for item in self:
                if isinstance(item, SearchResult):
                    item._client = self._client

    def first(self) -> Optional[SearchResult]:
        """Returns the first search result in the collection, or None if empty."""
        return self[0] if len(self) > 0 else None

    def filter(
        self,
        provider: Optional[str] = None,
        collection: Optional[str] = None,
        max_cloud_cover: Optional[float] = None
    ) -> "SearchResults":
        """Filter results in-memory by provider, collection, or cloud cover."""
        filtered = []
        for r in self:
            if provider and r.provider != provider:
                continue
            if collection and r.collection != collection:
                continue
            if max_cloud_cover is not None and r.cloud_cover is not None and r.cloud_cover > max_cloud_cover:
                continue
            filtered.append(r)
        return SearchResults(filtered, client=self._client)

    def download_all(
        self,
        asset_key: Optional[str] = None,
        outdir: Optional[str] = None,
        max_workers: int = 4,
        resume: bool = True,
        multipart: bool = True,
        client: Optional[Any] = None,
        **kwargs
    ) -> List[str]:
        """
        Downloads all search results in the collection concurrently.
        Returns list of downloaded absolute file paths.
        """
        active_client = client or self._client
        if not active_client:
            from omniearth.client import OmniEarth
            active_client = OmniEarth()
        return active_client.download_many(
            results=list(self),
            asset_key=asset_key,
            outdir=outdir,
            max_workers=max_workers,
            resume=resume,
            multipart=multipart,
            **kwargs
        )

    def download_indices(
        self,
        indices: List[int],
        asset_key: Optional[str] = None,
        outdir: Optional[str] = None,
        max_workers: int = 4,
        resume: bool = True,
        multipart: bool = True,
        client: Optional[Any] = None,
        **kwargs
    ) -> List[str]:
        """
        Downloads specific search results by their integer index in the collection.
        """
        selected = [self[i] for i in indices if 0 <= i < len(self)]
        active_client = client or self._client
        if not active_client:
            from omniearth.client import OmniEarth
            active_client = OmniEarth()
        return active_client.download_many(
            results=selected,
            asset_key=asset_key,
            outdir=outdir,
            max_workers=max_workers,
            resume=resume,
            multipart=multipart,
            **kwargs
        )

    def export_geojson(self, output_path: Union[str, Path]) -> str:
        """Export all search result footprints into a standard GeoJSON FeatureCollection."""
        import json
        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        features = []
        for r in self:
            feat = {
                "type": "Feature",
                "id": r.id,
                "geometry": r.footprint,
                "properties": {
                    "id": r.id,
                    "collection": r.collection,
                    "category": r.category.value,
                    "provider": r.provider,
                    "datetime": r.datetime,
                    "cloud_cover": r.cloud_cover,
                    "download_url": r.get_download_url() or "",
                    "assets": list(r.assets.keys()),
                    **{k: v for k, v in r.properties.items() if not k.startswith("_")}
                }
            }
            features.append(feat)
        fc = {"type": "FeatureCollection", "features": features}
        with open(p, "w", encoding="utf-8") as f:
            json.dump(fc, f, indent=2, default=str)
        return str(p.resolve())

    def export_csv(self, output_path: Union[str, Path]) -> str:
        """Export tabular summary of search results to CSV spreadsheet for QGIS/ArcGIS/Excel."""
        import csv
        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        headers = [
            "id",
            "collection",
            "category",
            "provider",
            "datetime",
            "cloud_cover",
            "latitude",
            "longitude",
            "bbox",
            "download_url",
            "assets"
        ]
        with open(p, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            for r in self:
                lat_val = r.properties.get("latitude") or r.properties.get("center_lat") or r.properties.get("lat")
                lon_val = r.properties.get("longitude") or r.properties.get("center_lon") or r.properties.get("lon")
                if (lat_val is None or lon_val is None) and r.bbox and len(r.bbox) == 4:
                    lon_val = round((r.bbox[0] + r.bbox[2]) / 2.0, 6)
                    lat_val = round((r.bbox[1] + r.bbox[3]) / 2.0, 6)

                bbox_str = ",".join(str(x) for x in r.bbox) if r.bbox else ""
                writer.writerow({
                    "id": r.id,
                    "collection": r.collection,
                    "category": r.category.value,
                    "provider": r.provider,
                    "datetime": r.datetime or "",
                    "cloud_cover": r.cloud_cover if r.cloud_cover is not None else "",
                    "latitude": lat_val if lat_val is not None else "",
                    "longitude": lon_val if lon_val is not None else "",
                    "bbox": bbox_str,
                    "download_url": r.get_download_url() or "",
                    "assets": ";".join(r.assets.keys())
                })
        return str(p.resolve())

    def export(self, output_path: Union[str, Path]) -> str:
        """Automatically export to .geojson or .csv based on filename extension."""
        p = Path(output_path)
        if p.suffix.lower() == ".csv":
            return self.export_csv(p)
        return self.export_geojson(p)


class FilterOptions(BaseModel):
    """Universal filter options for search queries."""
    max_cloud_cover: Optional[float] = None
    bands: Optional[List[str]] = None
    variables: Optional[List[str]] = None
    depth: Optional[str] = None
    dataset: Optional[str] = None
    year: Optional[int] = None
    level: Optional[str] = "sr"
    provider: Optional[str] = None
    format: Optional[str] = None
    limit: int = 10
