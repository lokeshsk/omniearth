"""
OmniEarth Data Models
=====================
Standardized representations for areas of interest, search results, and assets.
"""

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


class FilterOptions(BaseModel):
    """Universal filter options for search queries."""
    max_cloud_cover: Optional[float] = None
    bands: Optional[List[str]] = None
    variables: Optional[List[str]] = None
    depth: Optional[str] = None
    limit: int = 10
