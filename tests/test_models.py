"""
Tests for OmniEarth Core Data Models
"""

import pytest
from omniearth.models import AOI, Asset, SearchResult, Category, FilterOptions


def test_aoi_from_bounds():
    aoi = AOI.from_bounds(78.50, 20.65, 78.60, 20.72)
    assert aoi.min_lon == 78.50
    assert aoi.min_lat == 20.65
    assert aoi.max_lon == 78.60
    assert aoi.max_lat == 20.72
    assert aoi.to_bbox_string() == "78.5,20.65,78.6,20.72"


def test_aoi_from_point():
    aoi = AOI.from_point(78.55, 20.68, radius_km=5.0)
    assert aoi.min_lon < 78.55 < aoi.max_lon
    assert aoi.min_lat < 20.68 < aoi.max_lat


def test_aoi_validation_failure():
    with pytest.raises(ValueError):
        AOI(bbox=[78.60, 20.72, 78.50, 20.65])  # min > max


def test_asset_creation():
    asset = Asset(
        key="visual",
        href="https://example.com/visual.tif",
        media_type="image/tiff",
        size_bytes=1048576,
        roles=["visual"]
    )
    assert asset.key == "visual"
    assert asset.size_bytes == 1048576


def test_search_result_properties_and_download_url():
    result = SearchResult(
        id="test_scene_001",
        collection="sentinel-2-l2a",
        category=Category.OPTICAL,
        provider="aws_earth_search",
        datetime="2026-10-22T05:33:15Z",
        bbox=[78.5, 20.65, 78.6, 20.72],
        properties={"eo:cloud_cover": 2.5, "platform": "sentinel-2b"},
        assets={
            "visual": Asset(key="visual", href="https://example.com/visual.tif"),
            "data": Asset(key="data", href="https://example.com/data.tif")
        }
    )
    assert result.cloud_cover == 2.5
    assert result.get_download_url("visual") == "https://example.com/visual.tif"
    assert result.get_download_url("nonexistent") == "https://example.com/data.tif"


def test_filter_options():
    filters = FilterOptions(max_cloud_cover=20.0, limit=5, depth="0-5cm")
    assert filters.max_cloud_cover == 20.0
    assert filters.limit == 5
    assert filters.depth == "0-5cm"
