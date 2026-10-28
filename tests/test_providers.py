"""
Comprehensive Unit Tests for All Provider Adapters
"""

import os
import requests
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


def test_optical_provider_date_filters_and_errors(tmp_path):
    provider = OpticalProvider()
    aoi = AOI.from_bounds(78.5, 20.65, 78.6, 20.72)

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"features": []}

    # 1. start_date and end_date
    with patch("requests.post", return_value=mock_resp) as mock_p:
        provider.search(aoi=aoi, start_date="2026-01-01", end_date="2026-01-10")
        assert "2026-01-01T00:00:00Z/2026-01-10T23:59:59Z" in mock_p.call_args[1]["json"]["datetime"]

    # 2. start_date only
    with patch("requests.post", return_value=mock_resp) as mock_p:
        provider.search(aoi=aoi, start_date="2026-01-01")
        assert "2026-01-01T00:00:00Z/.." in mock_p.call_args[1]["json"]["datetime"]

    # 3. end_date only
    with patch("requests.post", return_value=mock_resp) as mock_p:
        provider.search(aoi=aoi, end_date="2026-01-10")
        assert "../2026-01-10T23:59:59Z" in mock_p.call_args[1]["json"]["datetime"]

    # 4. RequestException error branch
    with patch("requests.post", side_effect=requests.exceptions.ConnectionError("Network Down")):
        res = provider.search(aoi=aoi)
        assert res == []

    # 5. Download fallback when neither 'visual' nor 'red' is in assets
    res_other = SearchResult(
        id="s2_b08",
        collection="sentinel-2-l2a",
        category=Category.OPTICAL,
        provider="aws_earth_search",
        assets={"nir": Asset(key="nir", href="https://example.com/b08.tif")}
    )
    mock_dl = MagicMock(status_code=200, headers={"content-length": "4"})
    mock_dl.__enter__.return_value = mock_dl
    mock_dl.iter_content.return_value = [b"data"]
    with patch("requests.head", return_value=mock_dl), patch("requests.get", return_value=mock_dl):
        out = provider.download(res_other, outdir=str(tmp_path))
        assert os.path.exists(out)


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

    # 1. start_date only
    with patch("requests.post", return_value=mock_resp) as mock_p:
        provider.search(aoi=aoi, start_date="2026-10-01")
        assert "2026-10-01T00:00:00Z/.." in mock_p.call_args[1]["json"]["datetime"]

    # 2. end_date only
    with patch("requests.post", return_value=mock_resp) as mock_p:
        provider.search(aoi=aoi, end_date="2026-10-22")
        assert "../2026-10-22T23:59:59Z" in mock_p.call_args[1]["json"]["datetime"]

    # 3. RequestException
    with patch("requests.post", side_effect=requests.exceptions.Timeout("SAR STAC Timeout")):
        res = provider.search(aoi=aoi)
        assert res == []


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

        # Test download with _raw_data cached
        dl_path = provider.download(results[0], outdir=str(tmp_path))
        assert os.path.exists(dl_path)

        # 1. Search without dates (line 57: FORECAST_URL)
        res_nodates = provider.search(aoi=aoi)
        assert len(res_nodates) == 1

        # 2. Search with recent dates (lines 69-71: FORECAST_URL with dates)
        res_recent = provider.search(aoi=aoi, start_date="2026-10-25", end_date="2026-10-28")
        assert len(res_recent) == 1

    # 3. RequestException error branch
    with patch("requests.get", side_effect=requests.exceptions.HTTPError("OpenMeteo Error")):
        assert provider.search(aoi=aoi) == []

    # 4. Download without _raw_data (remote streaming)
    res_uncached = SearchResult(
        id="weather_uncached",
        collection="open-meteo-weather",
        category=Category.WEATHER,
        provider="open_meteo",
        assets={"data": Asset(key="data", href="https://example.com/weather.json")}
    )
    mock_dl = MagicMock(status_code=200, headers={"content-length": "4"})
    mock_dl.__enter__.return_value = mock_dl
    mock_dl.iter_content.return_value = [b"json"]
    with patch("requests.head", return_value=mock_dl), patch("requests.get", return_value=mock_dl):
        dl_uncached = provider.download(res_uncached, outdir=str(tmp_path))
        assert os.path.exists(dl_uncached)

    # 5. Download without target_asset -> ValueError
    import pytest
    res_empty_asset = SearchResult(
        id="weather_no_asset",
        collection="open-meteo-weather",
        category=Category.WEATHER,
        provider="open_meteo",
        assets={}
    )
    with pytest.raises(ValueError, match="No download asset found"):
        provider.download(res_empty_asset, outdir=str(tmp_path))


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

    # 1. RequestException error branch
    with patch("requests.get", side_effect=requests.exceptions.ConnectionError("SoilGrids Down")):
        assert provider.search(aoi=aoi) == []

    # 2. Download without _raw_data (remote streaming)
    res_uncached = SearchResult(
        id="soil_uncached",
        collection="isric-soilgrids-v2",
        category=Category.SOIL,
        provider="isric",
        assets={"data": Asset(key="data", href="https://rest.isric.org/soil.json")}
    )
    mock_dl = MagicMock(status_code=200, headers={"content-length": "4"})
    mock_dl.__enter__.return_value = mock_dl
    mock_dl.iter_content.return_value = [b"json"]
    with patch("requests.head", return_value=mock_dl), patch("requests.get", return_value=mock_dl):
        dl_uncached = provider.download(res_uncached, outdir=str(tmp_path))
        assert os.path.exists(dl_uncached)


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
        results = provider.search(aoi=aoi, start_date="2026-09-01", end_date="2026-09-20", filters=FilterOptions(limit=2))
        assert len(results) >= 1
        assert results[0].id == "EMIT_L2A_MOCK"


def test_hyperspectral_search_all_branches_and_filters():
    provider = HyperspectralProvider()
    aoi = AOI.from_bounds(78.5, 20.65, 78.6, 20.72)

    # 1. DLR EnMAP date branches & cloud filter
    mock_dlr = MagicMock()
    mock_dlr.status_code = 200
    mock_dlr.json.return_value = {
        "features": [
            {
                "id": "ENMAP_HIGH_CLOUD",
                "properties": {"eo:cloud_cover": 85.0, "datetime": "2026-05-01T10:00:00Z"},
                "assets": {"image": {"href": "https://dlr.de/img.tif"}}
            },
            {
                "id": "ENMAP_LOW_CLOUD",
                "properties": {"eo:cloud_cover": 5.0, "datetime": "2026-05-02T10:00:00Z"},
                "assets": {"image": {"href": "https://dlr.de/img2.tif"}}
            }
        ]
    }

    # Test cloud filter
    with patch("requests.get", return_value=mock_dlr):
        res = provider._search_enmap(aoi, "2026-05-01", "2026-05-10", filters=FilterOptions(max_cloud_cover=20.0), limit=5)
        assert len(res) == 1
        assert res[0].id == "ENMAP_LOW_CLOUD"

    # Test DLR start_date only
    with patch("requests.get", return_value=mock_dlr) as mock_g:
        provider._search_enmap(aoi, "2026-05-01", None, filters=None, limit=5)
        assert "2026-05-01T00:00:00Z/.." in mock_g.call_args[1]["params"]["datetime"]

    # Test DLR end_date only
    with patch("requests.get", return_value=mock_dlr) as mock_g:
        provider._search_enmap(aoi, None, "2026-05-10", filters=None, limit=5)
        assert "../2026-05-10T23:59:59Z" in mock_g.call_args[1]["params"]["datetime"]

    # Test DLR status != 200 and RequestException
    mock_bad = MagicMock(status_code=500)
    with patch("requests.get", return_value=mock_bad):
        assert provider._search_enmap(aoi, None, None, filters=None, limit=5) == []

    with patch("requests.get", side_effect=requests.exceptions.ConnectionError):
        assert provider._search_enmap(aoi, None, None, filters=None, limit=5) == []

    # 2. NASA EMIT error branches
    mock_emit_bad = MagicMock(status_code=404)
    with patch("requests.post", return_value=mock_emit_bad):
        assert provider._search_emit(aoi, None, None, limit=5) == []

    with patch("requests.post", side_effect=requests.exceptions.Timeout):
        assert provider._search_emit(aoi, None, None, limit=5) == []

    # 3. ASI PRISMA search branches
    mock_prisma = MagicMock()
    mock_prisma.status_code = 200
    mock_prisma.json.return_value = {
        "features": [
            {
                "id": "PRISMA_L2D_01",
                "properties": {"datetime": "2026-04-12T08:00:00Z"},
                "assets": {"he5": {"href": "https://prisma.asi.it/p1.he5"}}
            }
        ]
    }
    with patch("requests.get", return_value=mock_prisma) as mock_p:
        res_prisma = provider._search_prisma(aoi, "2026-04-01", "2026-04-30", limit=2)
        assert len(res_prisma) == 1
        assert res_prisma[0].id == "PRISMA_L2D_01"
        assert mock_p.call_args[1]["params"]["start"] == "2026-04-01"
        assert mock_p.call_args[1]["params"]["end"] == "2026-04-30"

    mock_prisma_bad = MagicMock(status_code=503)
    with patch("requests.get", return_value=mock_prisma_bad):
        assert provider._search_prisma(aoi, None, None, limit=2) == []

    with patch("requests.get", side_effect=requests.exceptions.HTTPError):
        assert provider._search_prisma(aoi, None, None, limit=2) == []


def test_base_provider_download_stream(tmp_path):
    provider = OpticalProvider()
    res = SearchResult(
        id="test_scene",
        collection="test-col",
        category=Category.OPTICAL,
        provider="test-prov",
        assets={"visual": Asset(key="visual", href="https://example.com/image.tif")}
    )

    data_bytes = b"mock_tif_bytes_12345"
    mock_head = MagicMock(status_code=200, headers={"content-length": str(len(data_bytes)), "accept-ranges": "bytes"})
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {"content-length": str(len(data_bytes))}
    mock_resp.__enter__.return_value = mock_resp
    mock_resp.iter_content.return_value = [data_bytes]

    with patch("requests.head", return_value=mock_head), patch("requests.get", return_value=mock_resp):
        out_file = provider.download(res, asset_key="visual", outdir=str(tmp_path))
        assert os.path.exists(out_file)
        with open(out_file, "rb") as f:
            assert f.read() == data_bytes

        # Test cache hit / file already exists branch
        cached_file = provider.download(res, asset_key="visual", outdir=str(tmp_path))
        assert cached_file == out_file


def test_base_provider_multipart_download(tmp_path):
    provider = OpticalProvider()
    part_path = str(tmp_path / "multipart_test.tif.part")
    outpath = str(tmp_path / "multipart_test.tif")
    total_size = 120

    # Mock chunk ranges response
    def fake_get_range(url, **kwargs):
        range_header = kwargs.get("headers", {}).get("Range", "")
        # format bytes=start-end
        start, end = range_header.replace("bytes=", "").split("-")
        s, e = int(start), int(end)
        length = e - s + 1
        chunk_data = b"X" * length
        m = MagicMock()
        m.status_code = 206
        m.__enter__.return_value = m
        m.iter_content.return_value = [chunk_data]
        return m

    with patch("requests.get", side_effect=fake_get_range):
        provider._multipart_download(
            url="https://example.com/multipart_test.tif",
            part_path=part_path,
            total_size=total_size,
            max_workers=3,
            desc="Testing Multipart"
        )
        assert os.path.exists(part_path)
        assert os.path.getsize(part_path) == total_size
        with open(part_path, "rb") as f:
            assert f.read() == b"X" * total_size

    # Test full download_stream triggering multipart
    outpath_stream_mp = str(tmp_path / "stream_big_mp.tif")
    mock_head = MagicMock(
        status_code=200,
        headers={"content-length": "20000000", "accept-ranges": "bytes"}
    )
    def fake_mp(*args, **kwargs):
        part = kwargs.get("part_path")
        with open(part, "wb") as f:
            f.write(b"M" * 20000000)

    with patch("requests.head", return_value=mock_head), \
         patch.object(provider, "_multipart_download", side_effect=fake_mp):
        res_file = provider._stream_download(
            url="https://example.com/big_mp.tif",
            outpath=outpath_stream_mp,
            multipart=True,
            max_workers=4
        )
        assert os.path.exists(res_file)
        assert os.path.getsize(res_file) == 20000000

    # Test requests.head raising exception (lines 165-166)
    outpath_no_head = str(tmp_path / "stream_no_head.tif")
    single_mock_head_fail = MagicMock(status_code=200, headers={"content-length": "5"})
    single_mock_head_fail.__enter__.return_value = single_mock_head_fail
    single_mock_head_fail.iter_content.return_value = [b"nohead"]
    with patch("requests.head", side_effect=requests.exceptions.ConnectionError("HEAD failed")), \
         patch("requests.get", return_value=single_mock_head_fail):
        res_nh = provider._stream_download(
            url="https://example.com/no_head.tif",
            outpath=outpath_no_head,
            multipart=True
        )
        assert os.path.exists(res_nh)

    # Test multipart exception fallback to single-stream
    outpath_fallback = str(tmp_path / "mp_fallback.tif")
    single_mock = MagicMock(status_code=200, headers={"content-length": "5"})
    single_mock.__enter__.return_value = single_mock
    single_mock.iter_content.return_value = [b"hello"]

    def fail_after_part_created(*args, **kwargs):
        part = kwargs.get("part_path")
        with open(part, "wb") as f:
            f.write(b"part_garbage")
        raise RuntimeError("Worker error")

    with patch("requests.head", return_value=mock_head), \
         patch.object(provider, "_multipart_download", side_effect=fail_after_part_created), \
         patch("requests.get", return_value=single_mock):
        res_fallback = provider._stream_download(
            url="https://example.com/fail_mp.tif",
            outpath=outpath_fallback,
            multipart=True,
            max_workers=2
        )
        assert os.path.exists(res_fallback)
        with open(res_fallback, "rb") as f:
            assert f.read() == b"hello"

    # Test multipart exception when os.remove raises OSError
    outpath_oserr = str(tmp_path / "mp_oserr.tif")
    with patch("requests.head", return_value=mock_head), \
         patch.object(provider, "_multipart_download", side_effect=fail_after_part_created), \
         patch("os.remove", side_effect=OSError("Permission denied")), \
         patch("requests.get", return_value=single_mock):
        res_oserr = provider._stream_download(
            url="https://example.com/oserr_mp.tif",
            outpath=outpath_oserr,
            multipart=True,
            max_workers=2
        )
        assert os.path.exists(res_oserr)


def test_base_provider_resumable_and_416(tmp_path):
    provider = OpticalProvider()
    outpath = str(tmp_path / "resume_test.tif")
    part_path = f"{outpath}.part"

    # 1. Existing partial file -> HTTP 206 resume
    with open(part_path, "wb") as f:
        f.write(b"initial_bytes_")  # 14 bytes

    mock_head = MagicMock(status_code=200, headers={"content-length": "24", "accept-ranges": "bytes"})
    mock_206 = MagicMock(status_code=206, headers={"content-length": "10"})
    mock_206.__enter__.return_value = mock_206
    mock_206.iter_content.return_value = [b"appended10"]

    with patch("requests.head", return_value=mock_head), patch("requests.get", return_value=mock_206) as mock_g:
        res = provider._stream_download("https://example.com/resumable.tif", outpath, resume=True, multipart=False)
        assert os.path.exists(res)
        with open(res, "rb") as f:
            assert f.read() == b"initial_bytes_appended10"
        assert mock_g.call_args[1]["headers"]["Range"] == "bytes=14-"

    # 2. HTTP 416 Range Not Satisfiable -> fresh download from scratch
    outpath_416 = str(tmp_path / "err_416.tif")
    part_path_416 = f"{outpath_416}.part"
    with open(part_path_416, "wb") as f:
        f.write(b"corrupted_stale_bytes")

    mock_416 = MagicMock(status_code=416)
    mock_416.__enter__.return_value = mock_416
    mock_fresh = MagicMock(status_code=200, headers={"content-length": "7"})
    mock_fresh.__enter__.return_value = mock_fresh
    mock_fresh.iter_content.return_value = [b"freshOK"]

    with patch("requests.head", return_value=mock_head), patch("requests.get", side_effect=[mock_416, mock_fresh]):
        res_416 = provider._stream_download("https://example.com/416.tif", outpath_416, resume=True, multipart=False)
        assert os.path.exists(res_416)
        with open(res_416, "rb") as f:
            assert f.read() == b"freshOK"

    # 3. Server does not support ranges (returns 200 instead of 206) -> overwrites cleanly
    outpath_200 = str(tmp_path / "server_200.tif")
    part_path_200 = f"{outpath_200}.part"
    with open(part_path_200, "wb") as f:
        f.write(b"old_data")

    mock_200 = MagicMock(status_code=200, headers={"content-length": "8"})
    mock_200.__enter__.return_value = mock_200
    mock_200.iter_content.return_value = [b"full_200"]

    with patch("requests.head", return_value=mock_head), patch("requests.get", return_value=mock_200):
        res_200 = provider._stream_download("https://example.com/no_range.tif", outpath_200, resume=True, multipart=False)
        assert os.path.exists(res_200)
        with open(res_200, "rb") as f:
            assert f.read() == b"full_200"


def test_hyperspectral_downloads_all_sources(tmp_path):
    import pytest
    provider = HyperspectralProvider()

    mock_head = MagicMock(status_code=200, headers={"content-length": "10", "accept-ranges": "bytes"})
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
    with patch.dict(os.environ, {"DLR_USERNAME": "test_dlr_user", "DLR_PASSWORD": "test_dlr_pass"}), patch("requests.head", return_value=mock_head), patch("requests.get", return_value=mock_resp):
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
    with patch("requests.head", return_value=mock_head), patch("requests.get", return_value=mock_resp):
        out = provider.download(emit_res, outdir=str(tmp_path))
        assert os.path.exists(out)

    # 2b. NASA EMIT protected URL download with credentials
    emit_prot_res = SearchResult(
        id="EMIT_PROT_002",
        collection="emit",
        category=Category.HYPERSPECTRAL,
        provider="nasa_lpdaac",
        assets={"data": Asset(key="data", href="https://data.lpdaac.nasa.gov/protected/emit.nc")}
    )
    with patch.dict(os.environ, {"EARTHDATA_USERNAME": "test_nasa_user", "EARTHDATA_PASSWORD": "test_nasa_pass"}), patch("requests.head", return_value=mock_head), patch("requests.get", return_value=mock_resp) as mock_get_prot:
        out_prot = provider.download(emit_prot_res, outdir=str(tmp_path))
        assert os.path.exists(out_prot)
        assert mock_get_prot.call_args[1]["auth"] == ("test_nasa_user", "test_nasa_pass")

    # 3. ASI PRISMA download
    prisma_res = SearchResult(
        id="PRISMA_001",
        collection="prisma",
        category=Category.HYPERSPECTRAL,
        provider="asi_prisma",
        assets={"he5": Asset(key="he5", href="https://prisma.asi.it/data.he5")}
    )
    with patch("requests.head", return_value=mock_head), patch("requests.get", return_value=mock_resp):
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
    mock_head = MagicMock(status_code=200, headers={"content-length": "10", "accept-ranges": "bytes"})
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {"content-length": "10"}
    mock_resp.__enter__.return_value = mock_resp
    mock_resp.iter_content.return_value = [b"mock_sar_data"]

    with patch("requests.head", return_value=mock_head), patch("requests.get", return_value=mock_resp):
        out = sar_prov.download(res, asset_key="vv", outdir=str(tmp_path))
        assert os.path.exists(out)

        # Test VH fallback when VV is missing
        res_vh = SearchResult(
            id="S1_VH_ONLY",
            collection="sentinel-1-grd",
            category=Category.SAR,
            provider="element84_earth_search",
            assets={"vh": Asset(key="vh", href="https://sentinel-s1.s3.amazonaws.com/vh.tif")}
        )
        out_vh = sar_prov.download(res_vh, outdir=str(tmp_path))
        assert os.path.exists(out_vh)

        # Test arbitrary fallback when neither VV nor VH is in assets
        res_other = SearchResult(
            id="S1_DATA_ONLY",
            collection="sentinel-1-grd",
            category=Category.SAR,
            provider="element84_earth_search",
            assets={"data": Asset(key="data", href="https://sentinel-s1.s3.amazonaws.com/data.tif")}
        )
        out_other = sar_prov.download(res_other, outdir=str(tmp_path))
        assert os.path.exists(out_other)


def test_elevation_provider_search_and_download(tmp_path):
    from omniearth.providers.elevation import ElevationProvider
    import pytest

    provider = ElevationProvider()
    aoi = AOI.from_bounds(78.2, 20.1, 79.5, 21.2)

    # 1. Search Copernicus
    res_cop = provider.search(aoi, filters=FilterOptions(dataset="copernicus", limit=10))
    assert len(res_cop) >= 1
    assert res_cop[0].category == Category.ELEVATION
    assert "Copernicus_DSM_COG" in res_cop[0].id
    assert "dem" in res_cop[0].assets

    # 2. Search SRTM
    res_srtm = provider.search(aoi, filters=FilterOptions(dataset="srtm", limit=1))
    assert len(res_srtm) == 1
    assert "SRTM_GL1" in res_srtm[0].id

    # 3. Search ALOS
    res_alos = provider.search(aoi, filters=FilterOptions(dataset="alos", limit=1))
    assert len(res_alos) == 1
    assert "ALPSMLC30" in res_alos[0].id

    # 4. Search fallback and negative coordinates + narrow bbox
    aoi_narrow = AOI.from_bounds(10.0, 20.0, 10.0, 20.0)
    res_narrow = provider.search(aoi_narrow, filters=FilterOptions(dataset="copernicus", limit=5))
    assert len(res_narrow) >= 1

    aoi_neg = AOI.from_bounds(-10.5, -20.5, -9.5, -19.5)
    res_neg = provider.search(aoi_neg, filters=FilterOptions(dataset="unknown_dem", limit=2))
    assert len(res_neg) >= 1
    assert "S21" in res_neg[0].id or "S20" in res_neg[0].id

    # 5. Download test
    mock_head = MagicMock(status_code=200, headers={"content-length": "10", "accept-ranges": "bytes"})
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {"content-length": "10"}
    mock_resp.__enter__.return_value = mock_resp
    mock_resp.iter_content.return_value = [b"mock_dem_data"]

    with patch("requests.head", return_value=mock_head), patch("requests.get", return_value=mock_resp):
        # dem key via default without passing asset_key
        out1 = provider.download(res_cop[0], outdir=str(tmp_path))
        assert os.path.exists(out1)

        # explicit custom asset_key
        res_custom_key = SearchResult(
            id="DEM_CUSTOM", collection="c", category=Category.ELEVATION, provider="p",
            assets={"custom_dem": Asset(key="custom_dem", href="https://example.com/c.tif")}
        )
        out_custom = provider.download(res_custom_key, asset_key="custom_dem", outdir=str(tmp_path))
        assert os.path.exists(out_custom)

        # data key fallback
        res_data_only = SearchResult(
            id="DEM_DATA_ONLY",
            collection="c",
            category=Category.ELEVATION,
            provider="p",
            assets={"data": Asset(key="data", href="https://example.com/tile.tif")}
        )
        out2 = provider.download(res_data_only, outdir=str(tmp_path))
        assert os.path.exists(out2)

        # non-tif extension fallback naming
        res_nontif = SearchResult(
            id="DEM_RAW",
            collection="c",
            category=Category.ELEVATION,
            provider="p",
            assets={"other": Asset(key="other", href="https://example.com/tile.bin")}
        )
        out3 = provider.download(res_nontif, outdir=str(tmp_path))
        assert out3.endswith("DEM_RAW.tif")
        assert os.path.exists(out3)

        # missing asset error
        empty_res = SearchResult(id="E", collection="c", category=Category.ELEVATION, provider="p", assets={})
        with pytest.raises(ValueError, match="No valid DEM asset found"):
            provider.download(empty_res)


def test_landcover_provider_search_and_download(tmp_path):
    from omniearth.providers.landcover import LandcoverProvider
    import pytest

    provider = LandcoverProvider()
    aoi = AOI.from_bounds(78.2, 20.1, 80.5, 22.2)

    # 1. Search 2021 (v200)
    res_2021 = provider.search(aoi, filters=FilterOptions(year=2021, limit=5))
    assert len(res_2021) >= 1
    assert res_2021[0].category == Category.LANDCOVER
    assert "2021_v200" in res_2021[0].id
    assert "map" in res_2021[0].assets

    # 2. Search 2020 (v100) via start_date
    res_2020 = provider.search(aoi, start_date="2020-05-01", filters=FilterOptions(limit=1))
    assert len(res_2020) == 1
    assert "2020_v100" in res_2020[0].id

    # 3. Search via end_date and negative coordinates + narrow bbox
    aoi_narrow = AOI.from_bounds(12.0, 21.0, 12.0, 21.0)
    res_narrow = provider.search(aoi_narrow, filters=FilterOptions(limit=5))
    assert len(res_narrow) >= 1

    aoi_neg = AOI.from_bounds(-15.0, -12.0, -14.0, -11.0)
    res_neg = provider.search(aoi_neg, end_date="2020-12-31", filters=FilterOptions(limit=1))
    assert len(res_neg) == 1
    assert "S12W015" in res_neg[0].id

    # 4. Download test
    mock_head = MagicMock(status_code=200, headers={"content-length": "10", "accept-ranges": "bytes"})
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {"content-length": "10"}
    mock_resp.__enter__.return_value = mock_resp
    mock_resp.iter_content.return_value = [b"mock_landcover_data"]

    with patch("requests.head", return_value=mock_head), patch("requests.get", return_value=mock_resp):
        # map key via default without passing asset_key
        out1 = provider.download(res_2021[0], outdir=str(tmp_path))
        assert os.path.exists(out1)

        # explicit custom asset_key
        res_custom_key = SearchResult(
            id="LC_CUSTOM", collection="c", category=Category.LANDCOVER, provider="p",
            assets={"custom_map": Asset(key="custom_map", href="https://example.com/c_map.tif")}
        )
        out_custom = provider.download(res_custom_key, asset_key="custom_map", outdir=str(tmp_path))
        assert os.path.exists(out_custom)

        # data key fallback
        res_data_only = SearchResult(
            id="LC_DATA_ONLY",
            collection="c",
            category=Category.LANDCOVER,
            provider="p",
            assets={"data": Asset(key="data", href="https://example.com/lc_map.tif")}
        )
        out2 = provider.download(res_data_only, outdir=str(tmp_path))
        assert os.path.exists(out2)

        # non-tif extension naming
        res_nontif = SearchResult(
            id="LC_RAW",
            collection="c",
            category=Category.LANDCOVER,
            provider="p",
            assets={"other": Asset(key="other", href="https://example.com/raw.bin")}
        )
        out3 = provider.download(res_nontif, outdir=str(tmp_path))
        assert out3.endswith("LC_RAW.tif")
        assert os.path.exists(out3)

        # missing asset error
        empty_res = SearchResult(id="E", collection="c", category=Category.LANDCOVER, provider="p", assets={})
        with pytest.raises(ValueError, match="No valid Landcover asset found"):
            provider.download(empty_res)

