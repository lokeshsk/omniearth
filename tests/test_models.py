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
    # min_lon > max_lon
    with pytest.raises(ValueError, match="min_lon"):
        AOI(bbox=[78.60, 20.65, 78.50, 20.72])
    # min_lat > max_lat
    with pytest.raises(ValueError, match="min_lat"):
        AOI(bbox=[78.50, 20.75, 78.60, 20.65])
    # length != 4
    with pytest.raises(ValueError, match="must contain exactly 4 coordinates"):
        AOI(bbox=[78.50, 20.65, 78.60])


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

    # Fallback to image
    res_image = SearchResult(
        id="s2", collection="c", category=Category.OPTICAL, provider="p",
        assets={"image": Asset(key="image", href="https://example.com/image.png")}
    )
    assert res_image.get_download_url("missing") == "https://example.com/image.png"

    # Fallback to next(iter(assets))
    res_other = SearchResult(
        id="s3", collection="c", category=Category.OPTICAL, provider="p",
        assets={"arbitrary_key": Asset(key="arbitrary_key", href="https://example.com/custom.bin")}
    )
    assert res_other.get_download_url("missing") == "https://example.com/custom.bin"
    assert "arbitrary_key" in res_other.to_dict()["assets"]

    # Empty assets
    res_empty = SearchResult(id="s4", collection="c", category=Category.OPTICAL, provider="p")
    assert res_empty.get_download_url("missing") is None


def test_filter_options():
    filters = FilterOptions(max_cloud_cover=20.0, limit=5, depth="0-5cm")
    assert filters.max_cloud_cover == 20.0
    assert filters.limit == 5
    assert filters.depth == "0-5cm"


def test_aoi_from_geojson(tmp_path):
    import json

    # 1. FeatureCollection dict
    geo_fc = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [[78.0, 20.0], [78.5, 20.0], [78.5, 20.5], [78.0, 20.5], [78.0, 20.0]]
                    ]
                }
            }
        ]
    }
    aoi_fc = AOI.from_geojson(geo_fc)
    assert aoi_fc.bbox == [78.0, 20.0, 78.5, 20.5]

    # 2. String JSON
    aoi_str = AOI.from_geojson(json.dumps(geo_fc))
    assert aoi_str.bbox == [78.0, 20.0, 78.5, 20.5]

    # 3. File path
    file_p = tmp_path / "test.geojson"
    file_p.write_text(json.dumps(geo_fc))
    aoi_file = AOI.from_geojson(str(file_p))
    assert aoi_file.bbox == [78.0, 20.0, 78.5, 20.5]

    # 4. GeometryCollection
    geo_gc = {
        "type": "GeometryCollection",
        "geometries": [
            {"type": "Point", "coordinates": [10.0, 15.0]},
            {"type": "Point", "coordinates": [12.0, 18.0]}
        ]
    }
    aoi_gc = AOI.from_geojson(geo_gc)
    assert aoi_gc.bbox == [10.0, 15.0, 12.0, 18.0]

    # 5. Direct Geometry dict
    geo_poly = {
        "type": "Polygon",
        "coordinates": [[[0.0, 0.0], [1.0, 1.0]]]
    }
    aoi_poly = AOI.from_geojson(geo_poly)
    assert aoi_poly.bbox == [0.0, 0.0, 1.0, 1.0]

    # 5b. Single Feature dict
    geo_feat = {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [5.0, 6.0]
        }
    }
    aoi_feat = AOI.from_geojson(geo_feat)
    assert aoi_feat.bbox == [5.0, 6.0, 5.0, 6.0]

    # 6. No coordinates found
    with pytest.raises(ValueError, match="No valid coordinates found"):
        AOI.from_geojson({"type": "FeatureCollection", "features": []})

    # 7. Invalid type
    with pytest.raises(ValueError, match="Invalid GeoJSON source"):
        AOI.from_geojson(12345)


