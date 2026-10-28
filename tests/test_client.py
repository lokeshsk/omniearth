"""
Comprehensive Tests for OmniEarth Client and Category Resolution
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from omniearth import OmniEarth, Category, AOI, SearchResult, Asset


def test_client_initialization_and_categories():
    client = OmniEarth()
    categories = client.list_categories()
    assert "optical" in categories
    assert "hyperspectral" in categories
    assert "sar" in categories
    assert "weather" in categories
    assert "soil" in categories


def test_resolve_aoi():
    client = OmniEarth()
    
    # 1. Direct AOI
    aoi = AOI.from_bounds(10, 20, 11, 21)
    res = client._resolve_aoi(aoi, None, None)
    assert res.min_lon == 10

    # 2. Bbox
    res2 = client._resolve_aoi(None, [10, 20, 11, 21], None)
    assert res2.max_lat == 21

    # 3. Point
    res3 = client._resolve_aoi(None, None, (10.0, 20.0, 2.0))
    assert res3.min_lon < 10.0 < res3.max_lon

    # 4. Error when none provided
    with pytest.raises(ValueError):
        client._resolve_aoi(None, None, None)


def test_invalid_category():
    client = OmniEarth()
    with pytest.raises(ValueError):
        client.search(category="invalid_category", bbox=[10, 20, 11, 21])


def test_client_get_weather_and_soil_shortcuts():
    client = OmniEarth()
    mock_item = SearchResult(
        id="mock_item_01",
        collection="test",
        category=Category.WEATHER,
        provider="test",
        properties={"elevation": 100}
    )
    with patch.object(client, "search", return_value=[mock_item]):
        wx = client.get_weather(bbox=[78.5, 20.65, 78.6, 20.72])
        assert wx.id == "mock_item_01"
        assert wx.properties["elevation"] == 100

        soil = client.get_soil(bbox=[78.5, 20.65, 78.6, 20.72])
        assert soil.id == "mock_item_01"


def test_client_download():
    client = OmniEarth()
    mock_res = SearchResult(
        id="mock_item_01",
        collection="test",
        category=Category.WEATHER,
        provider="test",
        assets={"data": Asset(key="data", href="https://example.com/data.json")}
    )
    with patch.object(client._providers[Category.WEATHER], "download", return_value="/tmp/test.json"):
        path = client.download(mock_res)
        assert path == "/tmp/test.json"


def test_client_env_path_and_empty_shortcuts(tmp_path):
    # Test env_path loading
    env_file = tmp_path / ".env.test"
    env_file.write_text("OMNIEARTH_CACHE_DIR=/tmp/test_cache\n")
    client = OmniEarth(env_path=str(env_file))
    assert client is not None

    # Test get_weather and get_soil when no results returned
    with patch.object(client, "search", return_value=[]):
        assert client.get_weather([10, 20, 11, 21]) is None
        assert client.get_soil([10, 20, 11, 21]) is None


def test_client_search_success_and_unsupported_provider():
    client = OmniEarth()
    mock_res = SearchResult(
        id="s2_item", collection="c", category=Category.OPTICAL, provider="p"
    )
    with patch.object(client._providers[Category.OPTICAL], "search", return_value=[mock_res]) as mock_s:
        res = client.search(
            category="optical",
            bbox=[10, 20, 11, 21],
            start_date="2026-01-01",
            end_date="2026-01-02",
            max_cloud_cover=10.0,
            limit=2
        )
        assert len(res) == 1
        assert res[0].id == "s2_item"
        mock_s.assert_called_once()

    # Unsupported provider in client._providers map
    client._providers = {}
    with pytest.raises(ValueError, match="Unsupported category"):
        client.search(category=Category.OPTICAL, bbox=[10, 20, 11, 21])


def test_client_download_invalid_provider():
    client = OmniEarth()
    mock_res = SearchResult(
        id="mock_unsupported",
        collection="test",
        category=Category.OPTICAL,
        provider="test",
        assets={"data": Asset(key="data", href="https://example.com/data.json")}
    )
    # Remove provider
    client._providers = {}
    with pytest.raises(ValueError, match="No provider found for category"):
        client.download(mock_res)


def test_client_download_all_and_many(tmp_path):
    client = OmniEarth()
    mock_res1 = SearchResult(
        id="res_multi_1",
        collection="sentinel-2-l2a",
        category=Category.OPTICAL,
        provider="aws",
        assets={
            "visual": Asset(key="visual", href="https://example.com/visual.tif"),
            "data": Asset(key="data", href="https://example.com/data.tif"),
        }
    )
    mock_res2 = SearchResult(
        id="res_multi_2",
        collection="sentinel-2-l2a",
        category=Category.OPTICAL,
        provider="aws",
        assets={
            "visual": Asset(key="visual", href="https://example.com/visual2.tif"),
        }
    )

    # 1. download_all with default assets (all)
    with patch.object(client, "download", side_effect=lambda r, k, outdir, resume, multipart, max_workers: f"/tmp/{r.id}_{k}.tif"):
        paths = client.download_all(mock_res1, outdir=str(tmp_path), max_workers=2)
        assert len(paths) == 2
        assert "visual" in paths
        assert "data" in paths
        assert paths["visual"] == "/tmp/res_multi_1_visual.tif"
        assert paths["data"] == "/tmp/res_multi_1_data.tif"

        # download_all with specific asset_keys
        sub_paths = client.download_all(mock_res1, asset_keys=["visual"], outdir=str(tmp_path))
        assert len(sub_paths) == 1
        assert "visual" in sub_paths

    # 2. download_all on empty assets raises ValueError
    mock_res_empty = SearchResult(
        id="empty_assets",
        collection="c",
        category=Category.OPTICAL,
        provider="p",
        assets={}
    )
    with pytest.raises(ValueError, match="No assets found to download"):
        client.download_all(mock_res_empty)

    # 3. download_many with empty list
    assert client.download_many([]) == []

    # 4. download_many with items
    with patch.object(client, "download", side_effect=lambda r, k, outdir, resume, multipart, max_workers: f"/tmp/{r.id}.tif"):
        many_paths = client.download_many([mock_res1, mock_res2], outdir=str(tmp_path), max_workers=2)
        assert len(many_paths) == 2
        assert many_paths == ["/tmp/res_multi_1.tif", "/tmp/res_multi_2.tif"]


def test_client_geojson_resolution():
    client = OmniEarth()
    geo = {
        "type": "Polygon",
        "coordinates": [[[78.0, 20.0], [78.5, 20.5]]]
    }
    with patch.object(client._providers[Category.ELEVATION], "search", return_value=["mock_dem"]) as mock_s:
        res = client.search(category="elevation", geojson=geo)
        assert res == ["mock_dem"]
        assert mock_s.called


def test_client_elevation_and_landcover_shortcuts():
    client = OmniEarth()
    mock_elev = SearchResult(id="dem_01", collection="c", category=Category.ELEVATION, provider="p")
    mock_lc = SearchResult(id="lc_01", collection="c", category=Category.LANDCOVER, provider="p")

    with patch.object(client, "search", return_value=[mock_elev]):
        assert client.get_elevation(bbox=[78.0, 20.0, 78.5, 20.5]) == mock_elev
    with patch.object(client, "search", return_value=[]):
        assert client.get_elevation(bbox=[78.0, 20.0, 78.5, 20.5]) is None

    with patch.object(client, "search", return_value=[mock_lc]):
        assert client.get_landcover(bbox=[78.0, 20.0, 78.5, 20.5]) == mock_lc
    with patch.object(client, "search", return_value=[]):
        assert client.get_landcover(bbox=[78.0, 20.0, 78.5, 20.5]) is None


def test_client_compute_index(tmp_path):
    client = OmniEarth()

    # 1. NDVI scalar & list
    ndvi = client.compute_index("ndvi", nir=0.8, red=0.2)
    assert round(ndvi["mean"], 2) == 0.60
    assert "data" in ndvi

    list_n = [0.8, 0.9]
    list_r = [0.2, 0.1]
    ndvi_list = client.compute_index("ndvi", nir=list_n, red=list_r)
    assert len(ndvi_list["data"]) == 2

    # 2. NDWI
    ndwi = client.compute_index("ndwi", nir=0.8, green=0.3)
    assert ndwi["index"] == "ndwi"

    # 3. NDRE
    ndre = client.compute_index("ndre", nir=0.8, rededge=0.4)
    assert ndre["index"] == "ndre"

    # 4. EVI
    evi = client.compute_index("evi", nir=0.8, red=0.2, blue=0.1)
    assert evi["index"] == "evi"

    # 5. NBR
    nbr = client.compute_index("nbr", nir=0.8, swir=0.3)
    assert nbr["index"] == "nbr"

    # Error branches
    with pytest.raises(ValueError, match="Red band required"):
        client.compute_index("ndvi", nir=0.8)
    with pytest.raises(ValueError, match="Green band required"):
        client.compute_index("ndwi", nir=0.8)
    with pytest.raises(ValueError, match="RedEdge band required"):
        client.compute_index("ndre", nir=0.8)
    with pytest.raises(ValueError, match="Red and Blue bands required"):
        client.compute_index("evi", nir=0.8, red=0.2)
    with pytest.raises(ValueError, match="SWIR band required"):
        client.compute_index("nbr", nir=0.8)
    with pytest.raises(ValueError, match="Unsupported index"):
        client.compute_index("fake_index", nir=0.8)

    # Save output
    json_path = str(tmp_path / "idx.json")
    client.compute_index("ndvi", nir=0.8, red=0.2, outpath=json_path)
    assert os.path.exists(json_path)


def test_client_get_time_series():
    client = OmniEarth()

    # 1. Weather time series
    mock_weather_res = SearchResult(
        id="wx_feed", collection="wx", category=Category.WEATHER, provider="open_meteo",
        properties={
            "_raw_data": {
                "hourly": {
                    "time": ["2026-10-20T00:00", "2026-10-20T01:00"],
                    "temperature_2m": [22.0, 23.5]
                }
            }
        }
    )
    with patch.object(client, "search", return_value=[mock_weather_res]):
        ts = client.get_time_series(category="weather", bbox=[78.0, 20.0, 78.5, 20.5])
        assert len(ts) == 2
        assert ts[0]["datetime"] == "2026-10-20T00:00"
        assert ts[0]["temperature_2m"] == 22.0

    # 2. Satellite time series
    s1 = SearchResult(id="s1", collection="c", category=Category.OPTICAL, provider="p", datetime="2026-10-02T00:00:00Z", properties={"eo:cloud_cover": 5.0})
    s2 = SearchResult(id="s2", collection="c", category=Category.OPTICAL, provider="p", datetime="2026-10-01T00:00:00Z", properties={"eo:cloud_cover": 10.0})

    with patch.object(client, "search", return_value=[s1, s2]):
        sat_ts = client.get_time_series(category="optical", bbox=[78.0, 20.0, 78.5, 20.5])
        assert len(sat_ts) == 2
        # sorted chronologically
        assert sat_ts[0]["id"] == "s2"
        assert sat_ts[1]["id"] == "s1"

