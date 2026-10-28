"""
Comprehensive Tests for OmniEarth Client and Category Resolution
"""

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
