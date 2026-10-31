"""
OmniEarth Data Models
=====================
Standardized representations for areas of interest, search results, and assets.
"""

import os
from enum import Enum
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, model_validator


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


class AOI(BaseModel):
    """Area of Interest representation (WGS84 [min_lon, min_lat, max_lon, max_lat])."""
    bbox: List[float] = Field(..., description="[min_lon, min_lat, max_lon, max_lat]")

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
    def from_bounds(cls, min_lon: float, min_lat: float, max_lon: float, max_lat: float) -> "AOI":
        return cls(bbox=[min_lon, min_lat, max_lon, max_lat])

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
        Recursively scans coordinates to find [min_lon, min_lat, max_lon, max_lat].
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
        return cls.from_bounds(min_lon, min_lat, max_lon, max_lat)

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

    @property
    def cloud_cover(self) -> Optional[float]:
        return self.properties.get("eo:cloud_cover") or self.properties.get("cloud_cover")

    def get_download_url(self, preferred_key: str = "data") -> Optional[str]:
        """Returns the primary asset download URL."""
        if preferred_key in self.assets:
            return self.assets[preferred_key].href
        if "data" in self.assets:
            return self.assets["data"].href
        if "image" in self.assets:
            return self.assets["image"].href
        if self.assets:
            return next(iter(self.assets.values())).href
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serializable dictionary representation."""
        return self.model_dump(mode="json")


class FilterOptions(BaseModel):
    """Universal filter options for search queries."""
    max_cloud_cover: Optional[float] = None
    bands: Optional[List[str]] = None
    variables: Optional[List[str]] = None
    depth: Optional[str] = None
    dataset: Optional[str] = None
    year: Optional[int] = None
    limit: int = 10
