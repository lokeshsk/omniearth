"""
Unit tests for Provider Adapters with Mocking
"""

from unittest.mock import patch, MagicMock
from omniearth.models import AOI, FilterOptions, Category
from omniearth.providers.optical import OpticalProvider
from omniearth.providers.hyperspectral import HyperspectralProvider
from omniearth.providers.weather import WeatherProvider
from omniearth.providers.sar import SARProvider
from omniearth.providers.soil import SoilProvider


def test_optical_provider_mock():
    provider = OpticalProvider()
    aoi = AOI.from_bounds(78.5, 20.65, 78.6, 20.72)

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.url = "https://api.open-meteo.com/v1/forecast"
    mock_resp.json.return_value = {
        "features": [
            {
                "id": "S2_MOCK_01",
                "collection": "sentinel-2-l2a",
                "properties": {"datetime": "2026-10-22T05:30:00Z", "eo:cloud_cover": 1.2, "platform": "sentinel-2b"},
                "bbox": [78.5, 20.65, 78.6, 20.72],
                "assets": {
                    "visual": {"href": "https://s3.amazonaws.com/s2/visual.tif", "type": "image/tiff"},
                    "red": {"href": "https://s3.amazonaws.com/s2/B04.tif", "type": "image/tiff"}
                }
            }
        ]
    }

    with patch("requests.post", return_value=mock_resp):
        results = provider.search(aoi=aoi, filters=FilterOptions(limit=1))
        assert len(results) == 1
        assert results[0].id == "S2_MOCK_01"
        assert results[0].cloud_cover == 1.2
        assert "visual" in results[0].assets


def test_weather_provider_mock():
    provider = WeatherProvider()
    aoi = AOI.from_bounds(78.5, 20.65, 78.6, 20.72)

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.url = "https://api.open-meteo.com/v1/forecast"
    mock_resp.json.return_value = {
        "latitude": 20.68,
        "longitude": 78.55,
        "elevation": 250,
        "hourly": {
            "time": ["2026-10-27T00:00"],
            "temperature_2m": [26.5],
            "relative_humidity_2m": [60]
        }
    }

    with patch("requests.get", return_value=mock_resp):
        results = provider.search(aoi=aoi)
        assert len(results) == 1
        assert results[0].category == Category.WEATHER
        assert results[0].properties["elevation"] == 250


def test_hyperspectral_enmap_mock():
    provider = HyperspectralProvider()
    aoi = AOI.from_bounds(78.5, 20.65, 78.6, 20.72)

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.url = "https://api.open-meteo.com/v1/forecast"
    mock_resp.json.return_value = {
        "features": [
            {
                "id": "ENMAP01_MOCK",
                "collection": "ENMAP_HSI_L2A",
                "properties": {"datetime": "2026-10-06T05:57:00Z", "platform": "enmap"},
                "bbox": [78.5, 20.65, 78.6, 20.72],
                "assets": {
                    "SPECTRAL_IMAGE_COG": {"href": "https://download.geoservice.dlr.de/file.tif", "type": "image/tiff"}
                }
            }
        ]
    }

    with patch("requests.get", return_value=mock_resp):
        results = provider.search(aoi=aoi, filters=FilterOptions(limit=1))
        assert len(results) >= 1
        assert results[0].id == "ENMAP01_MOCK"
        assert results[0].category == Category.HYPERSPECTRAL
