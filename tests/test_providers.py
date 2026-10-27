"""
Comprehensive Unit Tests for All Provider Adapters
"""

import os
from unittest.mock import patch, MagicMock
from omniearth.models import AOI, FilterOptions, Category, SearchResult, Asset
from omniearth.providers.optical import OpticalProvider
from omniearth.providers.hyperspectral import HyperspectralProvider
from omniearth.providers.weather import WeatherProvider
from omniearth.providers.sar import SARProvider
from omniearth.providers.soil import SoilProvider
from omniearth.providers.base import BaseProvider


def test_optical_provider_search():
    provider = OpticalProvider()
    aoi = AOI.from_bounds(78.5, 20.65, 78.6, 20.72)

    mock_resp = MagicMock()
    mock_resp.status_code = 200
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
        results = provider.search(aoi=aoi, filters=FilterOptions(limit=1, max_cloud_cover=10.0))
        assert len(results) == 1
        assert results[0].id == "S2_MOCK_01"
        assert results[0].cloud_cover == 1.2
        assert "visual" in results[0].assets


def test_sar_provider_search():
    provider = SARProvider()
    aoi = AOI.from_bounds(78.5, 20.65, 78.6, 20.72)

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "features": [
            {
                "id": "S1_MOCK_GRD",
                "collection": "sentinel-1-grd",
                "properties": {"datetime": "2026-10-21T00:30:00Z", "platform": "sentinel-1a"},
                "bbox": [78.5, 20.65, 78.6, 20.72],
                "assets": {
                    "vv": {"href": "https://s3.amazonaws.com/s1/vv.tif", "type": "image/tiff"},
                    "vh": {"href": "https://s3.amazonaws.com/s1/vh.tif", "type": "image/tiff"}
                }
            }
        ]
    }

    with patch("requests.post", return_value=mock_resp):
        results = provider.search(aoi=aoi, start_date="2026-10-01", end_date="2026-10-22")
        assert len(results) == 1
        assert results[0].id == "S1_MOCK_GRD"
        assert results[0].category == Category.SAR


def test_weather_provider_search_and_download(tmp_path):
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
        results = provider.search(aoi=aoi, start_date="2026-10-01", end_date="2026-10-10")
        assert len(results) == 1
        assert results[0].category == Category.WEATHER
        assert results[0].properties["elevation"] == 250

        # Test download
        dl_path = provider.download(results[0], outdir=str(tmp_path))
        assert os.path.exists(dl_path)


def test_soil_provider_search_and_download(tmp_path):
    provider = SoilProvider()
    aoi = AOI.from_bounds(78.5, 20.65, 78.6, 20.72)

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.url = "https://rest.isric.org/soilgrids/v2.0/properties/query"
    mock_resp.json.return_value = {
        "properties": {
            "layers": [
                {
                    "name": "clay",
                    "depths": [{"label": "0-5cm", "values": {"mean": 410}}]
                }
            ]
        }
    }

    with patch("requests.get", return_value=mock_resp):
        results = provider.search(aoi=aoi, filters=FilterOptions(depth="0-5cm"))
        assert len(results) == 1
        assert results[0].category == Category.SOIL
        assert "clay" in results[0].properties["summary_topsoil"]

        dl_path = provider.download(results[0], outdir=str(tmp_path))
        assert os.path.exists(dl_path)


def test_hyperspectral_enmap_and_emit(tmp_path):
    provider = HyperspectralProvider()
    aoi = AOI.from_bounds(78.5, 20.65, 78.6, 20.72)

    # 1. EnMAP returns 0, falls through to EMIT CMR via requests.post
    enmap_resp = MagicMock()
    enmap_resp.status_code = 200
    enmap_resp.json.return_value = {"features": []}

    emit_resp = MagicMock()
    emit_resp.status_code = 200
    emit_resp.json.return_value = {
        "features": [
            {
                "id": "EMIT_L2A_MOCK",
                "collection": "EMITL2ARFL.v001",
                "properties": {"datetime": "2026-09-15T10:00:00Z"},
                "bbox": [78.5, 20.65, 78.6, 20.72],
                "assets": {
                    "data": {"href": "https://data.lpdaac.earthdatacloud.nasa.gov/emit.nc", "type": "application/x-netcdf"}
                }
            }
        ]
    }

    with patch("requests.get", return_value=enmap_resp), patch("requests.post", return_value=emit_resp):
        results = provider.search(aoi=aoi, filters=FilterOptions(limit=2))
        assert len(results) >= 1
        assert results[0].id == "EMIT_L2A_MOCK"


def test_base_provider_download_stream(tmp_path):
    provider = OpticalProvider()
    res = SearchResult(
        id="test_scene",
        collection="test-col",
        category=Category.OPTICAL,
        provider="test-prov",
        assets={"visual": Asset(key="visual", href="https://example.com/image.tif")}
    )

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {"content-length": "100"}
    mock_resp.__enter__.return_value = mock_resp
    mock_resp.iter_content.return_value = [b"mock_tif_bytes_12345"]

    with patch("requests.get", return_value=mock_resp):
        out_file = provider.download(res, asset_key="visual", outdir=str(tmp_path))
        assert os.path.exists(out_file)
        with open(out_file, "rb") as f:
            assert f.read() == b"mock_tif_bytes_12345"

        # Test cache hit / file already exists branch
        cached_file = provider.download(res, asset_key="visual", outdir=str(tmp_path))
        assert cached_file == out_file


def test_hyperspectral_downloads_all_sources(tmp_path):
    import pytest
    provider = HyperspectralProvider()

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {"content-length": "10"}
    mock_resp.__enter__.return_value = mock_resp
    mock_resp.iter_content.return_value = [b"mock_bytes"]

    # 1. DLR EnMAP download without credentials raises ValueError
    dlr_res = SearchResult(
        id="ENMAP_001",
        collection="enmap",
        category=Category.HYPERSPECTRAL,
        provider="dlr_enmap",
        assets={"image": Asset(key="image", href="https://dlr.de/enmap.tif")}
    )
    with patch.dict(os.environ, {"DLR_USERNAME": "", "DLR_PASSWORD": "", "EOWEB_USERNAME": "", "EOWEB_PASSWORD": "", "DLR_USER": "", "DLR_PASS": ""}), pytest.raises(ValueError, match="DLR credentials"):
        provider.download(dlr_res, outdir=str(tmp_path))

    # DLR EnMAP download with credentials
    with patch.dict(os.environ, {"DLR_USERNAME": "test_dlr_user", "DLR_PASSWORD": "test_dlr_pass"}), patch("requests.get", return_value=mock_resp):
        out = provider.download(dlr_res, outdir=str(tmp_path))
        assert os.path.exists(out)

    # 2. NASA EMIT download
    emit_res = SearchResult(
        id="EMIT_001",
        collection="emit",
        category=Category.HYPERSPECTRAL,
        provider="nasa_lpdaac",
        assets={"browse": Asset(key="browse", href="https://data.lpdaac.nasa.gov/emit.png")}
    )
    with patch("requests.get", return_value=mock_resp):
        out = provider.download(emit_res, outdir=str(tmp_path))
        assert os.path.exists(out)

    # 3. ASI PRISMA download
    prisma_res = SearchResult(
        id="PRISMA_001",
        collection="prisma",
        category=Category.HYPERSPECTRAL,
        provider="asi_prisma",
        assets={"he5": Asset(key="he5", href="https://prisma.asi.it/data.he5")}
    )
    with patch("requests.get", return_value=mock_resp):
        out = provider.download(prisma_res, outdir=str(tmp_path))
        assert os.path.exists(out)

    # 4. Unknown hyperspectral provider
    bad_res = SearchResult(
        id="BAD_001", collection="c", category=Category.HYPERSPECTRAL, provider="unknown_sensor"
    )
    with pytest.raises(ValueError, match="Unknown hyperspectral provider"):
        provider.download(bad_res, outdir=str(tmp_path))


def test_sar_download(tmp_path):
    sar_prov = SARProvider()
    res = SearchResult(
        id="S1_SCENE_001",
        collection="sentinel-1-grd",
        category=Category.SAR,
        provider="element84_earth_search",
        assets={"vv": Asset(key="vv", href="https://sentinel-s1.s3.amazonaws.com/vv.tif")}
    )
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {"content-length": "10"}
    mock_resp.__enter__.return_value = mock_resp
    mock_resp.iter_content.return_value = [b"mock_sar_data"]

    with patch("requests.get", return_value=mock_resp):
        out = sar_prov.download(res, asset_key="vv", outdir=str(tmp_path))
        assert os.path.exists(out)
