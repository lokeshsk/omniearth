"""
Tests for OmniEarth Core Data Models
"""

import pytest
from omniearth.models import AOI, Asset, SearchResult, SearchResults, Category, FilterOptions


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


def test_aoi_contains_and_polygon_masking():
    from omniearth.models import _point_in_polygon

    # 1. Test _point_in_polygon edge cases
    assert _point_in_polygon(0.0, 0.0, [[0.0, 0.0], [1.0, 1.0]]) is False  # < 3 points

    # Triangle
    tri = [[0.0, 0.0], [4.0, 0.0], [2.0, 4.0], [0.0, 0.0]]
    assert _point_in_polygon(2.0, 2.0, tri) is True
    assert _point_in_polygon(5.0, 5.0, tri) is False

    # 2. AOI.contains without geometry (bbox only)
    aoi_box = AOI.from_bounds(0.0, 0.0, 10.0, 10.0)
    assert aoi_box.contains(5.0, 5.0) is True
    assert aoi_box.contains(15.0, 5.0) is False

    # Triangle inside bbox
    tri_geom = {
        "type": "Polygon",
        "coordinates": [
            [[2.0, 2.0], [8.0, 2.0], [5.0, 8.0], [2.0, 2.0]]
        ]
    }
    aoi_tri = AOI.from_bounds(0.0, 0.0, 10.0, 10.0, geometry=tri_geom)
    assert aoi_tri.contains(5.0, 4.0) is True  # inside triangle
    assert aoi_tri.contains(1.0, 1.0) is False  # inside bbox [0,10], outside triangle

    # 3. AOI.contains with Polygon geometry and hole
    # Square [0, 0] to [10, 10] with central hole [4, 4] to [6, 6]
    poly_geom = {
        "type": "Polygon",
        "coordinates": [
            [[0.0, 0.0], [10.0, 0.0], [10.0, 10.0], [0.0, 10.0], [0.0, 0.0]],
            [[4.0, 4.0], [6.0, 4.0], [6.0, 6.0], [4.0, 6.0], [4.0, 4.0]]
        ]
    }
    aoi_poly = AOI.from_bounds(0.0, 0.0, 10.0, 10.0, geometry=poly_geom)
    assert aoi_poly.contains(2.0, 2.0) is True  # inside outer ring, outside hole
    assert aoi_poly.contains(5.0, 5.0) is False  # inside hole -> False
    assert aoi_poly.contains(15.0, 5.0) is False  # outside bbox

    # Polygon with no coords
    aoi_empty_poly = AOI.from_bounds(0.0, 0.0, 10.0, 10.0, geometry={"type": "Polygon", "coordinates": []})
    assert aoi_empty_poly.contains(5.0, 5.0) is True

    # 4. AOI.contains with MultiPolygon geometry
    multipoly_geom = {
        "type": "MultiPolygon",
        "coordinates": [
            # Polygon 1: [0, 0] to [2, 2]
            [[[0.0, 0.0], [2.0, 0.0], [2.0, 2.0], [0.0, 2.0], [0.0, 0.0]]],
            # Polygon 2: [8, 8] to [10, 10] with a hole [8.8, 8.8] to [9.2, 9.2]
            [
                [[8.0, 8.0], [10.0, 8.0], [10.0, 10.0], [8.0, 10.0], [8.0, 8.0]],
                [[8.8, 8.8], [9.2, 8.8], [9.2, 9.2], [8.8, 9.2], [8.8, 8.8]]
            ]
        ]
    }
    aoi_multi = AOI.from_bounds(0.0, 0.0, 10.0, 10.0, geometry=multipoly_geom)
    assert aoi_multi.contains(1.0, 1.0) is True  # inside poly 1
    assert aoi_multi.contains(8.2, 8.2) is True  # inside poly 2 outside hole
    assert aoi_multi.contains(9.0, 9.0) is False  # inside hole in poly 2
    assert aoi_multi.contains(5.0, 5.0) is False  # between poly 1 and poly 2

    # Point geometry in AOI geometry (falls back to bbox containment)
    aoi_pt = AOI.from_bounds(0.0, 0.0, 10.0, 10.0, geometry={"type": "Point", "coordinates": [5.0, 5.0]})
    assert aoi_pt.contains(5.0, 5.0) is True


def test_search_results_fluent_and_direct_downloads(monkeypatch):
    from unittest.mock import MagicMock
    from omniearth.models import SearchResults

    mock_client = MagicMock()
    mock_client.download.return_value = "/tmp/downloaded.tif"
    mock_client.download_all.return_value = {"visual": "/tmp/visual.tif"}
    mock_client.download_many.return_value = ["/tmp/item1.tif", "/tmp/item2.tif"]

    item1 = SearchResult(
        id="item1",
        collection="sentinel-2-l2a",
        category=Category.OPTICAL,
        provider="aws",
        properties={"cloud_cover": 5.0},
        assets={"visual": Asset(key="visual", href="https://example.com/item1.tif")}
    )
    item2 = SearchResult(
        id="item2",
        collection="sentinel-2-l2a",
        category=Category.OPTICAL,
        provider="aws",
        properties={"cloud_cover": 25.0},
        assets={"visual": Asset(key="visual", href="https://example.com/item2.tif")}
    )
    item3 = SearchResult(
        id="item3",
        collection="landsat-8",
        category=Category.OPTICAL,
        provider="usgs",
        properties={"cloud_cover": 15.0},
        assets={"visual": Asset(key="visual", href="https://example.com/item3.tif")}
    )

    results = SearchResults([item1, item2, item3], client=mock_client)
    assert len(results) == 3
    assert results.first() == item1
    assert item1._client == mock_client

    empty_results = SearchResults([], client=mock_client)
    assert empty_results.first() is None

    # Filter
    filtered_provider = results.filter(provider="aws")
    assert len(filtered_provider) == 2

    filtered_collection = results.filter(collection="landsat-8")
    assert len(filtered_collection) == 1

    filtered_clouds = results.filter(max_cloud_cover=10.0)
    assert len(filtered_clouds) == 1
    assert filtered_clouds[0].id == "item1"

    # SearchResults.download_all
    paths = results.download_all(outdir="/tmp")
    assert paths == ["/tmp/item1.tif", "/tmp/item2.tif"]
    mock_client.download_many.assert_called_with(
        results=[item1, item2, item3],
        asset_key=None,
        outdir="/tmp",
        max_workers=4,
        resume=True,
        multipart=True
    )

    # SearchResults.download_indices
    indices_paths = results.download_indices([0, 2], outdir="/tmp")
    assert indices_paths == ["/tmp/item1.tif", "/tmp/item2.tif"]

    # SearchResult.download and download_all with bound _client
    d_path = item1.download()
    assert d_path == "/tmp/downloaded.tif"
    d_all = item1.download_all()
    assert d_all == {"visual": "/tmp/visual.tif"}

    # SearchResult and SearchResults fallback to default OmniEarth() when client is None
    item_standalone = SearchResult(
        id="standalone",
        collection="col",
        category=Category.OPTICAL,
        provider="aws"
    )
    with monkeypatch.context() as m:
        mock_omni_cls = MagicMock()
        mock_inst = MagicMock()
        mock_inst.download.return_value = "/tmp/fallback_download.tif"
        mock_inst.download_all.return_value = {"visual": "/tmp/fallback_visual.tif"}
        mock_inst.download_many.return_value = ["/tmp/fallback_many.tif"]
        mock_omni_cls.return_value = mock_inst
        m.setattr("omniearth.client.OmniEarth", mock_omni_cls)

        assert item_standalone.download() == "/tmp/fallback_download.tif"
        assert item_standalone.download_all() == {"visual": "/tmp/fallback_visual.tif"}

        results_standalone = SearchResults([item_standalone])
        assert results_standalone.download_all() == ["/tmp/fallback_many.tif"]
        assert results_standalone.download_indices([0]) == ["/tmp/fallback_many.tif"]


def test_search_result_checksum_and_footprint(tmp_path):
    from omniearth.models import SearchResults

    # 1. Properties with digest and explicit geometry
    res1 = SearchResult(
        id="res1",
        collection="col",
        category=Category.OPTICAL,
        provider="cdse",
        properties={
            "digest": "abc123md5",
            "checksum_algorithm": "SHA256",
            "geometry": {"type": "Point", "coordinates": [10.0, 20.0]},
            "cloud_cover": 1.2
        }
    )
    assert res1.checksum == "abc123md5"
    assert res1.checksum_algorithm == "SHA256"
    assert res1.footprint == {"type": "Point", "coordinates": [10.0, 20.0]}

    # 2. Checksum fallback to "checksum", default algorithm "MD5", footprint from bbox
    res2 = SearchResult(
        id="res2",
        collection="col",
        category=Category.OPTICAL,
        provider="aws",
        bbox=[10.0, 20.0, 30.0, 40.0],
        properties={"checksum": "def456"}
    )
    assert res2.checksum == "def456"
    assert res2.checksum_algorithm == "MD5"
    fp = res2.footprint
    assert fp["type"] == "Polygon"
    assert fp["coordinates"] == [[[10.0, 20.0], [30.0, 20.0], [30.0, 40.0], [10.0, 40.0], [10.0, 20.0]]]

    # 3. No bbox and no geometry
    res3 = SearchResult(
        id="res3",
        collection="col",
        category=Category.OPTICAL,
        provider="aws",
        properties={}
    )
    assert res3.checksum is None
    assert res3.checksum_algorithm == "MD5"
    assert res3.footprint is None

    # Export tests
    results = SearchResults([res1, res2, res3])

    # Export GeoJSON
    geo_out = results.export_geojson(tmp_path / "export.geojson")
    assert geo_out.endswith("export.geojson")
    import json
    with open(geo_out, "r") as f:
        geo_data = json.load(f)
    assert geo_data["type"] == "FeatureCollection"
    assert len(geo_data["features"]) == 3
    assert geo_data["features"][0]["id"] == "res1"

    # Export CSV
    csv_out = results.export_csv(tmp_path / "export.csv")
    assert csv_out.endswith("export.csv")
    import csv
    with open(csv_out, "r") as f:
        reader = list(csv.DictReader(f))
    assert len(reader) == 3
    assert reader[0]["id"] == "res1"
    assert reader[0]["cloud_cover"] == "1.2"

    # Export auto dispatcher (.csv vs .geojson)
    auto_csv = results.export(tmp_path / "auto.csv")
    assert auto_csv.endswith(".csv")
    auto_geo = results.export(tmp_path / "auto.geojson")
    assert auto_geo.endswith(".geojson")

    # Point footprint from identical min/max coords
    res_pt = SearchResult(
        id="pt1",
        collection="col",
        category=Category.WEATHER,
        provider="open_meteo",
        bbox=[78.5, 20.5, 78.5, 20.5],
        properties={"latitude": 20.5, "longitude": 78.5}
    )
    assert res_pt.footprint["type"] == "Point"
    assert res_pt.footprint["coordinates"] == [78.5, 20.5]

    # Point footprint from properties when bbox is None
    res_prop_pt = SearchResult(
        id="pt2",
        collection="col",
        category=Category.SOIL,
        provider="isric",
        bbox=None,
        properties={"center_lat": 20.6, "center_lon": 78.6}
    )
    assert res_prop_pt.footprint["type"] == "Point"
    assert res_prop_pt.footprint["coordinates"] == [78.6, 20.6]


def test_all_14_modalities_footprint_export_geojson_and_csv(tmp_path):
    """
    Verifies that all 14 modalities produce valid footprints and export cleanly
    to GeoJSON FeatureCollections and CSV spreadsheets for QGIS / ArcGIS.
    """
    import os
    import json
    import csv

    all_modalities = [
        Category.OPTICAL,
        Category.SAR,
        Category.HYPERSPECTRAL,
        Category.WEATHER,
        Category.SOIL,
        Category.ELEVATION,
        Category.LANDCOVER,
        Category.ATMOSPHERE,
        Category.FIRE,
        Category.OCEAN,
        Category.ALTIMETRY,
        Category.PRECIPITATION,
        Category.HYDROLOGY,
        Category.NIGHTLIGHTS,
    ]

    items = []
    for i, cat in enumerate(all_modalities, 1):
        items.append(SearchResult(
            id=f"scene_{cat.value}_{i}",
            collection=f"{cat.value}-collection",
            category=cat,
            provider=f"provider_{cat.value}",
            datetime="2026-11-19T00:00:00Z",
            bbox=[78.0 + (i * 0.01), 20.0 + (i * 0.01), 78.1 + (i * 0.01), 20.1 + (i * 0.01)],
            properties={
                "modality": cat.value,
                "cloud_cover": 5.0,
                "latitude": 20.05 + (i * 0.01),
                "longitude": 78.05 + (i * 0.01),
            },
            assets={
                "data": Asset(key="data", href=f"https://example.com/{cat.value}.tif")
            }
        ))

    results = SearchResults(items)
    assert len(results) == 14

    # Export all 14 modalities to GeoJSON
    geojson_path = tmp_path / "all_14_footprints.geojson"
    out_geo = results.export_geojson(geojson_path)
    assert os.path.exists(out_geo)

    with open(out_geo, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) == 14
    for feat, cat in zip(data["features"], all_modalities):
        assert feat["properties"]["category"] == cat.value
        assert feat["geometry"]["type"] in ("Polygon", "Point")
        assert feat["properties"]["download_url"].startswith("https://example.com/")

    # Export all 14 modalities to CSV
    csv_path = tmp_path / "all_14_footprints.csv"
    out_csv = results.export_csv(csv_path)
    assert os.path.exists(out_csv)

    with open(out_csv, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))

    assert len(reader) == 14
    for row, cat in zip(reader, all_modalities):
        assert row["category"] == cat.value
        assert float(row["latitude"]) > 0
        assert float(row["longitude"]) > 0
        assert row["download_url"].startswith("https://example.com/")
        assert row["assets"] == "data"


def test_search_result_resolve_asset_key():
    res_empty = SearchResult(
        id="empty", collection="c", category=Category.HYPERSPECTRAL, provider="p", properties={}, assets={}
    )
    assert res_empty.resolve_asset_key("data") is None
    assert res_empty.resolve_asset_key(None) is None

    emit_res = SearchResult(
        id="EMIT_001",
        collection="emit-l2a-rfl",
        category=Category.HYPERSPECTRAL,
        provider="nasa_lpdaac",
        properties={},
        assets={
            "browse": Asset(key="browse", href="https://example.com/browse.png"),
            "thumbnail_0": Asset(key="thumbnail_0", href="https://example.com/thumb.png"),
            "001/EMIT/EMIT_RFL": Asset(key="001/EMIT/EMIT_RFL", href="https://example.com/rfl.nc"),
            "001/EMIT/EMIT_RFLUNCERT": Asset(key="001/EMIT/EMIT_RFLUNCERT", href="https://example.com/uncert.nc"),
            "001/EMIT/EMIT_MASK": Asset(key="001/EMIT/EMIT_MASK", href="https://example.com/mask.nc"),
            "s3_001/EMIT/EMIT_RFL": Asset(key="s3_001/EMIT/EMIT_RFL", href="s3://bucket/rfl.nc"),
            "metadata": Asset(key="metadata", href="https://example.com/meta.xml"),
        }
    )
    assert emit_res.resolve_asset_key(None) == "001/EMIT/EMIT_RFL"
    assert emit_res.resolve_asset_key("") == "001/EMIT/EMIT_RFL"
    assert emit_res.resolve_asset_key("browse") == "browse"
    assert emit_res.resolve_asset_key("BROWSE") == "browse"
    assert emit_res.resolve_asset_key("data") == "001/EMIT/EMIT_RFL"
    assert emit_res.resolve_asset_key("rfl") == "001/EMIT/EMIT_RFL"
    assert emit_res.resolve_asset_key("cube") == "001/EMIT/EMIT_RFL"
    assert emit_res.resolve_asset_key("uncert") == "001/EMIT/EMIT_RFLUNCERT"
    assert emit_res.resolve_asset_key("mask") == "001/EMIT/EMIT_MASK"
    assert emit_res.resolve_asset_key("metadata") == "metadata"
    assert emit_res.resolve_asset_key("xml") == "metadata"
    assert emit_res.resolve_asset_key("RFLUNCERT") == "001/EMIT/EMIT_RFLUNCERT"
    assert emit_res.resolve_asset_key("s3_001") == "s3_001/EMIT/EMIT_RFL"
    assert emit_res.resolve_asset_key("nonexistent_anything") is None

    # Test aliases not matching exact key
    assert emit_res.resolve_asset_key("preview") == "browse"
    assert emit_res.resolve_asset_key("science") == "001/EMIT/EMIT_RFL"
    assert emit_res.resolve_asset_key("qa") == "001/EMIT/EMIT_MASK"
    assert emit_res.resolve_asset_key("uncertainty") == "001/EMIT/EMIT_RFLUNCERT"
    assert emit_res.resolve_asset_key("info") == "metadata"

    # Test visual/data primary key exact branch
    opt_res = SearchResult(
        id="opt", collection="c", category=Category.OPTICAL, provider="p", properties={},
        assets={"visual": Asset(key="visual", href="https://example.com/vis.tif")}
    )
    assert opt_res.resolve_asset_key(None) == "visual"

    # Test rfl in key without standard extension
    rfl_no_ext = SearchResult(
        id="rfl_ne", collection="c", category=Category.HYPERSPECTRAL, provider="p", properties={},
        assets={"my_rfl_cube": Asset(key="my_rfl_cube", href="https://example.com/cube")}
    )
    assert rfl_no_ext.resolve_asset_key(None) == "my_rfl_cube"

    fallback_res = SearchResult(
        id="fb", collection="c", category=Category.OPTICAL, provider="p", properties={},
        assets={"some_misc_key": Asset(key="some_misc_key", href="https://example.com/misc.bin")}
    )
    assert fallback_res.resolve_asset_key(None) == "some_misc_key"

    s3_only_res = SearchResult(
        id="s3_only", collection="c", category=Category.OPTICAL, provider="p", properties={},
        assets={"s3_data": Asset(key="s3_data", href="s3://bucket/data")}
    )
    assert s3_only_res.resolve_asset_key(None) == "s3_data"

    s3_first_res = SearchResult(
        id="s3_f", collection="c", category=Category.HYPERSPECTRAL, provider="p", properties={},
        assets={
            "s3_data": Asset(key="s3_data", href="s3://bucket/data.nc"),
            "data_http": Asset(key="data_http", href="https://example.com/data.nc")
        }
    )
    assert s3_first_res.resolve_asset_key("science") == "data_http"





