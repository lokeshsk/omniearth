"""
Comprehensive Tests for OmniEarth CLI Commands and Formatting
"""

import sys
import subprocess
from unittest.mock import patch, MagicMock
from omniearth.cli import format_size, cmd_categories, cmd_info, cmd_search, cmd_download, main
from omniearth import OmniEarth, Category, SearchResult, Asset


def test_format_size():
    assert format_size(0) == "Unknown size"
    assert format_size(-10) == "Unknown size"
    assert format_size(500) == "500.0 B"
    assert format_size(1024 * 512) == "512.0 KB"
    assert format_size(1024 * 1024 * 10) == "10.0 MB"
    assert format_size(1024 * 1024 * 1024 * 2) == "2.0 GB"
    assert format_size(1024 ** 5 * 3) == "3.0 PB"


def test_cmd_categories(capsys):
    client = OmniEarth()
    cmd_categories(None, client)
    captured = capsys.readouterr()
    assert "OPTICAL" in captured.out
    assert "HYPERSPECTRAL" in captured.out
    assert "WEATHER" in captured.out


def test_cmd_info(capsys):
    client = OmniEarth()
    cmd_info(None, client)
    captured = capsys.readouterr()
    assert "OmniEarth Engine" in captured.out
    assert "Lokesh Kumar" in captured.out


def test_cmd_search_direct(capsys):
    client = OmniEarth()
    args = MagicMock()
    args.category = "weather"
    args.bbox = [78.5, 20.65, 78.6, 20.72]
    args.point = None
    args.start = None
    args.end = None
    args.max_cloud = None
    args.variables = None
    args.depth = None
    args.limit = 1
    args.json = False

    mock_res = SearchResult(
        id="test_weather_item",
        collection="weather-col",
        category=Category.WEATHER,
        provider="open_meteo",
        assets={"data": Asset(key="data", href="https://example.com/weather.json")}
    )

    with patch.object(client, "search", return_value=[mock_res]):
        cmd_search(args, client)
        captured = capsys.readouterr()
        assert "test_weather_item" in captured.out


def test_cmd_download_direct(capsys, tmp_path):
    client = OmniEarth()
    args = MagicMock()
    args.category = "weather"
    args.id = None
    args.bbox = [78.5, 20.65, 78.6, 20.72]
    args.start = None
    args.end = None
    args.max_cloud = None
    args.asset = None
    args.outdir = str(tmp_path)

    mock_res = SearchResult(
        id="test_dl_item",
        collection="weather-col",
        category=Category.WEATHER,
        provider="open_meteo",
        assets={"data": Asset(key="data", href="https://example.com/weather.json")}
    )

    with patch.object(client, "search", return_value=[mock_res]):
        with patch.object(client, "download", return_value=str(tmp_path / "downloaded.json")):
            cmd_download(args, client)
            captured = capsys.readouterr()
            assert "Successfully downloaded" in captured.out


def test_cli_subprocess_version():
    res = subprocess.run([sys.executable, "-m", "omniearth.cli", "--version"], capture_output=True, text=True)
    assert res.returncode == 0
    assert "omniearth 1.0.0" in res.stdout or "omniearth 1.0.0" in res.stderr


def test_cmd_search_json_and_point(capsys):
    client = OmniEarth()
    args = MagicMock()
    args.category = "soil"
    args.bbox = None
    args.point = [78.55, 20.68, 10.0]
    args.start = None
    args.end = None
    args.max_cloud = None
    args.variables = "clay,sand"
    args.depth = "0-5cm"
    args.limit = 2
    args.json = True

    mock_res = SearchResult(
        id="soil_point_res",
        collection="soilgrids",
        category=Category.SOIL,
        provider="isric",
        assets={"data": Asset(key="data", href="https://example.com/soil.json")}
    )

    with patch.object(client, "search", return_value=[mock_res]):
        cmd_search(args, client)
        captured = capsys.readouterr()
        assert "soil_point_res" in captured.out
        assert '"category": "soil"' in captured.out


def test_cmd_search_no_results(capsys):
    client = OmniEarth()
    args = MagicMock()
    args.category = "optical"
    args.bbox = [78.5, 20.65, 78.6, 20.72]
    args.point = None
    args.start = None
    args.end = None
    args.max_cloud = None
    args.variables = None
    args.depth = None
    args.limit = 5
    args.json = False

    with patch.object(client, "search", return_value=[]):
        cmd_search(args, client)
        captured = capsys.readouterr()
        assert "No items found matching the specified criteria." in captured.out


def test_cmd_search_validation_errors():
    import pytest
    client = OmniEarth()
    
    # 1. Invalid bbox length
    args_bad_bbox = MagicMock(bbox=[78.5, 20.65], point=None)
    with pytest.raises(SystemExit):
        cmd_search(args_bad_bbox, client)

    # 2. Invalid point length
    args_bad_point = MagicMock(bbox=None, point=[78.5])
    with pytest.raises(SystemExit):
        cmd_search(args_bad_point, client)

    # 3. Neither bbox nor point
    args_no_geo = MagicMock(bbox=None, point=None)
    with pytest.raises(SystemExit):
        cmd_search(args_no_geo, client)


def test_cmd_download_by_id_and_fallbacks(capsys, tmp_path):
    import pytest
    client = OmniEarth()

    mock_res = SearchResult(
        id="SPECIFIC_SCENE_123",
        collection="s2",
        category=Category.OPTICAL,
        provider="aws",
        assets={"visual": Asset(key="visual", href="https://example.com/vis.tif")}
    )

    # 1. ID found
    args_found = MagicMock()
    args_found.category = "optical"
    args_found.id = "SPECIFIC_SCENE_123"
    args_found.bbox = None
    args_found.asset = "visual"
    args_found.outdir = str(tmp_path)

    with patch.object(client, "search", return_value=[mock_res]), \
         patch.object(client, "download", return_value=str(tmp_path / "vis.tif")):
        cmd_download(args_found, client)
        captured = capsys.readouterr()
        assert "Successfully downloaded" in captured.out

    # 1b. ID not found in catalog -> fallback direct synthetic result
    args_fallback = MagicMock()
    args_fallback.category = "optical"
    args_fallback.id = "MISSING_ID_999"
    args_fallback.bbox = None
    args_fallback.asset = None
    args_fallback.outdir = str(tmp_path)

    with patch.object(client, "search", return_value=[]), \
         patch.object(client, "download", return_value=str(tmp_path / "fallback.tif")):
        cmd_download(args_fallback, client)
        captured = capsys.readouterr()
        assert "attempting direct provider resolution" in captured.out

    # 1c. Bbox search with no scenes found -> exits 1
    args_bbox_empty = MagicMock()
    args_bbox_empty.category = "optical"
    args_bbox_empty.id = None
    args_bbox_empty.bbox = [10.0, 20.0, 11.0, 21.0]
    args_bbox_empty.start = None
    args_bbox_empty.end = None
    args_bbox_empty.max_cloud = None
    with patch.object(client, "search", return_value=[]), pytest.raises(SystemExit):
        cmd_download(args_bbox_empty, client)

    # 2. Neither ID nor bbox -> exits
    args_empty = MagicMock(id=None, bbox=None)
    with pytest.raises(SystemExit):
        cmd_download(args_empty, client)

    # 3. Download exception
    with patch.object(client, "search", return_value=[mock_res]), \
         patch.object(client, "download", side_effect=RuntimeError("Network Error")), \
         pytest.raises(SystemExit):
        cmd_download(args_found, client)


def test_cmd_download_all_and_flags(capsys, tmp_path):
    client = OmniEarth()
    mock_res = SearchResult(
        id="SCENE_ALL_TEST",
        collection="s2",
        category=Category.OPTICAL,
        provider="aws",
        assets={
            "visual": Asset(key="visual", href="https://example.com/vis.tif"),
            "data": Asset(key="data", href="https://example.com/data.tif"),
        }
    )

    args = MagicMock()
    args.category = "optical"
    args.id = "SCENE_ALL_TEST"
    args.bbox = None
    args.asset = None
    args.outdir = str(tmp_path)
    args.all = True
    args.threads = 4
    args.no_resume = True
    args.no_multipart = True

    with patch.object(client, "search", return_value=[mock_res]), \
         patch.object(client, "download_all", return_value={"visual": str(tmp_path / "vis.tif"), "data": str(tmp_path / "data.tif")}) as mock_dl_all:
        cmd_download(args, client)
        captured = capsys.readouterr()
        assert "Downloading all assets" in captured.out
        assert "Successfully downloaded 2 asset(s)" in captured.out
        assert "visual:" in captured.out
        mock_dl_all.assert_called_once_with(mock_res, outdir=str(tmp_path), max_workers=4, resume=False, multipart=False)


def test_cmd_search_error_and_cloud_formatting(capsys):
    import pytest
    client = OmniEarth()
    args = MagicMock()
    args.category = "optical"
    args.bbox = [78.5, 20.65, 78.6, 20.72]
    args.point = None
    args.start = None
    args.end = None
    args.max_cloud = None
    args.variables = None
    args.depth = None
    args.limit = 1
    args.json = False

    # 1. Search throws exception -> sys.exit(1)
    with patch.object(client, "search", side_effect=RuntimeError("STAC Timeout")), pytest.raises(SystemExit):
        cmd_search(args, client)

    # 2. Search result with cloud cover and size_bytes
    mock_item = SearchResult(
        id="s2_cloud_test",
        collection="s2",
        category=Category.OPTICAL,
        provider="aws",
        properties={"eo:cloud_cover": 15.6},
        assets={"visual": Asset(key="visual", href="https://example.com/vis.tif", size_bytes=2048, media_type="image/tiff")}
    )
    with patch.object(client, "search", return_value=[mock_item]):
        cmd_search(args, client)
        captured = capsys.readouterr()
        assert "Cloud:      15.6%" in captured.out
        assert "2.0 KB" in captured.out


def test_main_cli_dispatch(capsys):
    import pytest
    # test categories
    with patch("sys.argv", ["omniearth", "categories"]):
        main()
        captured = capsys.readouterr()
        assert "OPTICAL" in captured.out

    # test info
    with patch("sys.argv", ["omniearth", "info"]):
        main()
        captured = capsys.readouterr()
        assert "OmniEarth Engine" in captured.out

    # test search dispatch
    with patch("sys.argv", ["omniearth", "search", "--category", "weather", "--bbox", "78.5", "20.6", "78.6", "20.7", "--limit", "1"]):
        with patch("omniearth.cli.cmd_search") as mock_s:
            main()
            mock_s.assert_called_once()

    # test download dispatch
    with patch("sys.argv", ["omniearth", "download", "--category", "weather", "--bbox", "78.5", "20.6", "78.6", "20.7"]):
        with patch("omniearth.cli.cmd_download") as mock_d:
            main()
            mock_d.assert_called_once()

    # test no args -> exits with help
    with patch("sys.argv", ["omniearth"]), pytest.raises(SystemExit):
        main()
