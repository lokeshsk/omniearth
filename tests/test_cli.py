"""
Comprehensive Tests for OmniEarth CLI Commands and Formatting
"""

import os
import sys
import subprocess
from unittest.mock import patch, MagicMock
import omniearth
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
    assert "ATMOSPHERE" in captured.out
    assert "FIRE" in captured.out
    assert "OCEAN" in captured.out
    assert "ALTIMETRY" in captured.out
    assert "PRECIPITATION" in captured.out
    assert "HYDROLOGY" in captured.out
    assert "NIGHTLIGHTS" in captured.out


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
    assert f"omniearth {omniearth.__version__}" in res.stdout or f"omniearth {omniearth.__version__}" in res.stderr


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

    with patch.object(client, "get_item", return_value=None), \
         patch.object(client, "search", return_value=[]), \
         patch.object(client, "download", return_value=str(tmp_path / "fallback.tif")):
        cmd_download(args_fallback, client)
        captured = capsys.readouterr()
        assert "attempting direct provider resolution" in captured.out

    # 1b-ii. Category fallbacks for Hyperspectral, Elevation, Landcover
    for cat, prefix in [
        ("hyperspectral", "ENMAP_TEST"),
        ("hyperspectral", "EMIT_TEST"),
        ("hyperspectral", "PRS_TEST"),
        ("hyperspectral", "GENERIC_HSI"),
        ("elevation", "Copernicus_DSM_COG_10_N20_00_E078_00_DEM"),
        ("landcover", "ESA_WorldCover_10m_2021_v200_N18E075_Map"),
    ]:
        args_hs = MagicMock()
        args_hs.category = cat
        args_hs.id = prefix
        args_hs.bbox = None
        args_hs.asset = None
        args_hs.outdir = str(tmp_path)
        with patch.object(client, "get_item", return_value=None), \
             patch.object(client, "search", return_value=[]), \
             patch.object(client, "download", return_value=str(tmp_path / "item.tif")):
            cmd_download(args_hs, client)

    # 1b-iii. Direct get_item hit
    args_direct = MagicMock()
    args_direct.category = "hyperspectral"
    args_direct.id = "ENMAP_DIRECT"
    args_direct.bbox = None
    args_direct.asset = None
    args_direct.outdir = str(tmp_path)
    with patch.object(client, "get_item", return_value=mock_res), \
         patch.object(client, "download", return_value=str(tmp_path / "direct.tif")):
        cmd_download(args_direct, client)

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

    # test compute dispatch
    with patch("sys.argv", ["omniearth", "compute", "--index", "ndvi", "--nir", "0.8", "--red", "0.2"]):
        with patch("omniearth.cli.cmd_compute") as mock_c:
            main()
            mock_c.assert_called_once()

    # test timeseries dispatch
    with patch("sys.argv", ["omniearth", "timeseries", "--category", "weather", "--bbox", "78.5", "20.6", "78.6", "20.7"]):
        with patch("omniearth.cli.cmd_timeseries") as mock_ts:
            main()
            mock_ts.assert_called_once()


def test_cmd_compute(capsys, tmp_path):
    import pytest
    from omniearth.cli import cmd_compute

    client = OmniEarth()

    # 1. Scalar compute
    args_scalar = MagicMock()
    args_scalar.index = "ndvi"
    args_scalar.nir = "0.8"
    args_scalar.red = "0.2"
    args_scalar.green = None
    args_scalar.blue = None
    args_scalar.rededge = None
    args_scalar.swir = None
    args_scalar.outpath = None

    cmd_compute(args_scalar, client)
    captured = capsys.readouterr()
    assert "Radiometric Index Calculation [NDVI]" in captured.out
    assert "Mean:  0.6000" in captured.out

    # 2. Array compute with outpath
    outp = str(tmp_path / "idx_cli.json")
    args_arr = MagicMock()
    args_arr.index = "ndvi"
    args_arr.nir = "[0.8, 0.9]"
    args_arr.red = "[0.2, 0.1]"
    args_arr.green = None
    args_arr.blue = None
    args_arr.rededge = None
    args_arr.swir = None
    args_arr.outpath = outp

    cmd_compute(args_arr, client)
    captured_arr = capsys.readouterr()
    assert "Saved:" in captured_arr.out
    assert os.path.exists(outp)

    # 2b. SAVI with l_factor
    args_savi = MagicMock(index="savi", nir="0.8", red="0.2", green=None, blue=None, rededge=None, swir=None, l_factor="0.5", outpath=None)
    cmd_compute(args_savi, client)
    captured_savi = capsys.readouterr()
    assert "SAVI" in captured_savi.out

    # 3. Error compute -> sys.exit(1)
    args_err = MagicMock()
    args_err.index = "ndvi"
    args_err.nir = "0.8"
    args_err.red = None
    args_err.green = None
    args_err.blue = None
    args_err.rededge = None
    args_err.swir = None
    args_err.outpath = None

    with pytest.raises(SystemExit):
        cmd_compute(args_err, client)


def test_cmd_timeseries(capsys):
    import pytest
    from omniearth.cli import cmd_timeseries

    client = OmniEarth()

    # 1. Missing bbox and geojson -> sys.exit(1)
    args_missing = MagicMock(bbox=None, geojson=None)
    with pytest.raises(SystemExit):
        cmd_timeseries(args_missing, client)

    # 2. Valid timeseries with > 15 items
    mock_records = [{"datetime": f"2026-10-{i:02d}T00:00", "temp": 20 + i} for i in range(1, 20)]
    args_valid = MagicMock()
    args_valid.category = "weather"
    args_valid.bbox = [78.0, 20.0, 78.5, 20.5]
    args_valid.geojson = None
    args_valid.variables = "temp"
    args_valid.start = None
    args_valid.end = None
    args_valid.limit = 20
    args_valid.json = False

    with patch.object(client, "get_time_series", return_value=mock_records):
        cmd_timeseries(args_valid, client)
        captured = capsys.readouterr()
        assert "Time-Series [WEATHER] - 19 record(s)" in captured.out
        assert "more records" in captured.out

    # 3. JSON mode
    args_valid.json = True
    with patch.object(client, "get_time_series", return_value=mock_records):
        cmd_timeseries(args_valid, client)
        captured_json = capsys.readouterr()
        assert "2026-10-01T00:00" in captured_json.out

    # 4. Error during get_time_series -> sys.exit(1)
    with patch.object(client, "get_time_series", side_effect=RuntimeError("API error")), pytest.raises(SystemExit):
        cmd_timeseries(args_valid, client)


    # test no args -> exits with help
    with patch("sys.argv", ["omniearth"]), pytest.raises(SystemExit):
        main()


def test_cmd_search_download_actions(capsys, tmp_path):
    import builtins
    client = OmniEarth()
    item1 = SearchResult(
        id="SEARCH_ITEM_1", collection="s2", category=Category.OPTICAL, provider="aws",
        assets={"visual": Asset(key="visual", href="https://example.com/item1.tif")}
    )
    item2 = SearchResult(
        id="SEARCH_ITEM_2", collection="s2", category=Category.OPTICAL, provider="aws",
        assets={"visual": Asset(key="visual", href="https://example.com/item2.tif")}
    )
    from omniearth.models import SearchResults
    results = SearchResults([item1, item2], client=client)

    # 1. --download-all
    args_all = MagicMock()
    args_all.category = "optical"
    args_all.bbox = [78.0, 20.0, 78.5, 20.5]
    args_all.point = None
    args_all.geojson = None
    args_all.variables = None
    args_all.dataset = None
    args_all.year = None
    args_all.level = "sr"
    args_all.limit = 2
    args_all.json = False
    args_all.download_all = True
    args_all.download_top = None
    args_all.select = None
    args_all.interactive = False
    args_all.outdir = str(tmp_path)
    args_all.no_resume = False
    args_all.no_multipart = False
    args_all.threads = 2
    args_all.asset = "visual"

    with patch.object(client, "search", return_value=results), \
         patch.object(client, "download_many", return_value=[str(tmp_path / "1.tif"), str(tmp_path / "2.tif")]) as mock_dm:
        cmd_search(args_all, client)
        captured = capsys.readouterr()
        assert "Dispatching concurrent download for 2 scene(s)" in captured.out
        assert "Successfully downloaded 2 scene(s)" in captured.out
        mock_dm.assert_called_once()

    # 2. --download-top
    args_top = MagicMock()
    args_top.category = "optical"
    args_top.bbox = [78.0, 20.0, 78.5, 20.5]
    args_top.point = None
    args_top.geojson = None
    args_top.variables = None
    args_top.dataset = None
    args_top.year = None
    args_top.level = "sr"
    args_top.limit = 2
    args_top.json = False
    args_top.download_all = False
    args_top.download_top = 1
    args_top.select = None
    args_top.interactive = False
    args_top.outdir = str(tmp_path)
    args_top.no_resume = False
    args_top.no_multipart = False
    args_top.threads = 2
    args_top.asset = None

    with patch.object(client, "search", return_value=results), \
         patch.object(client, "download_many", return_value=[str(tmp_path / "1.tif")]):
        cmd_search(args_top, client)
        captured = capsys.readouterr()
        assert "Dispatching concurrent download for 1 scene(s)" in captured.out

    # 3. --select with single index and range '1-2'
    args_select = MagicMock()
    args_select.category = "optical"
    args_select.bbox = [78.0, 20.0, 78.5, 20.5]
    args_select.point = None
    args_select.geojson = None
    args_select.variables = None
    args_select.dataset = None
    args_select.year = None
    args_select.level = "sr"
    args_select.limit = 2
    args_select.json = False
    args_select.download_all = False
    args_select.download_top = None
    args_select.select = "1, 2-2"
    args_select.interactive = False
    args_select.outdir = str(tmp_path)
    args_select.no_resume = False
    args_select.no_multipart = False
    args_select.threads = 2
    args_select.asset = None

    with patch.object(client, "search", return_value=results), \
         patch.object(client, "download_many", return_value=[str(tmp_path / "1.tif"), str(tmp_path / "2.tif")]):
        cmd_search(args_select, client)
        captured = capsys.readouterr()
        assert "Dispatching concurrent download for 2 scene(s)" in captured.out

    # 4. --interactive with various inputs
    args_interactive = MagicMock()
    args_interactive.category = "optical"
    args_interactive.bbox = [78.0, 20.0, 78.5, 20.5]
    args_interactive.point = None
    args_interactive.geojson = None
    args_interactive.variables = None
    args_interactive.dataset = None
    args_interactive.year = None
    args_interactive.level = "sr"
    args_interactive.limit = 2
    args_interactive.json = False
    args_interactive.download_all = False
    args_interactive.download_top = None
    args_interactive.select = None
    args_interactive.interactive = True
    args_interactive.outdir = str(tmp_path)
    args_interactive.no_resume = False
    args_interactive.no_multipart = False
    args_interactive.threads = 2
    args_interactive.asset = None

    # 4a. input 'all'
    with patch.object(client, "search", return_value=results), \
         patch.object(builtins, "input", return_value="all"), \
         patch.object(client, "download_many", return_value=[str(tmp_path / "1.tif"), str(tmp_path / "2.tif")]):
        cmd_search(args_interactive, client)
        captured = capsys.readouterr()
        assert "Dispatching concurrent download for 2 scene(s)" in captured.out

    # 4b. input '1,2' (comma separated)
    with patch.object(client, "search", return_value=results), \
         patch.object(builtins, "input", return_value="1, 2"), \
         patch.object(client, "download_many", return_value=[str(tmp_path / "1.tif"), str(tmp_path / "2.tif")]):
        cmd_search(args_interactive, client)
        captured = capsys.readouterr()
        assert "Dispatching concurrent download for 2 scene(s)" in captured.out

    # 4b-ii. input '1-2' (range)
    with patch.object(client, "search", return_value=results), \
         patch.object(builtins, "input", return_value="1-2"), \
         patch.object(client, "download_many", return_value=[str(tmp_path / "1.tif"), str(tmp_path / "2.tif")]):
        cmd_search(args_interactive, client)
        captured = capsys.readouterr()
        assert "Dispatching concurrent download for 2 scene(s)" in captured.out

    # 4c. input 'q'
    with patch.object(client, "search", return_value=results), \
         patch.object(builtins, "input", return_value="q"):
        cmd_search(args_interactive, client)
        captured = capsys.readouterr()
        assert "Dispatching concurrent download" not in captured.out

    # 4c-ii. input empty string ''
    with patch.object(client, "search", return_value=results), \
         patch.object(builtins, "input", return_value=""):
        cmd_search(args_interactive, client)
        captured = capsys.readouterr()
        assert "Dispatching concurrent download" not in captured.out

    # 4d. input KeyboardInterrupt/EOFError
    with patch.object(client, "search", return_value=results), \
         patch.object(builtins, "input", side_effect=EOFError):
        cmd_search(args_interactive, client)
        captured = capsys.readouterr()
        assert "Dispatching concurrent download" not in captured.out


def test_cmd_download_multi_id_and_all_scenes(capsys, tmp_path):
    client = OmniEarth()
    item1 = SearchResult(
        id="MULTI_1", collection="s2", category=Category.OPTICAL, provider="aws",
        assets={"visual": Asset(key="visual", href="https://example.com/1.tif")}
    )
    item2 = SearchResult(
        id="MULTI_2", collection="s2", category=Category.OPTICAL, provider="aws",
        assets={"visual": Asset(key="visual", href="https://example.com/2.tif")}
    )

    # 1. Comma-separated IDs: --id "MULTI_1, MULTI_2"
    args_multi_id = MagicMock()
    args_multi_id.category = "optical"
    args_multi_id.id = "MULTI_1, MULTI_2"
    args_multi_id.bbox = None
    args_multi_id.geojson = None
    args_multi_id.dataset = None
    args_multi_id.year = None
    args_multi_id.outdir = str(tmp_path)
    args_multi_id.no_resume = False
    args_multi_id.no_multipart = False
    args_multi_id.threads = 2
    args_multi_id.asset = None
    args_multi_id.all = False

    with patch.object(client, "get_item", side_effect=[item1, item2]), \
         patch.object(client, "download_many", return_value=[str(tmp_path / "1.tif"), str(tmp_path / "2.tif")]) as mock_dm:
        cmd_download(args_multi_id, client)
        captured = capsys.readouterr()
        assert "Target(s):  2 item(s)" in captured.out
        assert "Successfully downloaded 2 scene(s)" in captured.out
        mock_dm.assert_called_once()

    # 2. AOI with --all-scenes
    args_aoi_all = MagicMock()
    args_aoi_all.category = "optical"
    args_aoi_all.id = None
    args_aoi_all.bbox = [78.0, 20.0, 78.5, 20.5]
    args_aoi_all.geojson = None
    args_aoi_all.start = None
    args_aoi_all.end = None
    args_aoi_all.max_cloud = None
    args_aoi_all.dataset = None
    args_aoi_all.year = None
    args_aoi_all.level = "sr"
    args_aoi_all.limit = 5
    args_aoi_all.all_scenes = True
    args_aoi_all.outdir = str(tmp_path)
    args_aoi_all.no_resume = False
    args_aoi_all.no_multipart = False
    args_aoi_all.threads = 2
    args_aoi_all.asset = None
    args_aoi_all.all = False

    with patch.object(client, "search", return_value=[item1, item2]), \
         patch.object(client, "download_many", return_value=[str(tmp_path / "1.tif"), str(tmp_path / "2.tif")]):
        cmd_download(args_aoi_all, client)
        captured = capsys.readouterr()
        assert "Found 2 scene(s) matching criteria." in captured.out
        assert "Successfully downloaded 2 scene(s)" in captured.out

    # 3. AOI with GeoJSON
    args_geojson = MagicMock()
    args_geojson.category = "optical"
    args_geojson.id = None
    args_geojson.bbox = None
    args_geojson.geojson = '{"type": "Point", "coordinates": [78.0, 20.0]}'
    args_geojson.start = None
    args_geojson.end = None
    args_geojson.max_cloud = None
    args_geojson.dataset = None
    args_geojson.year = None
    args_geojson.level = "sr"
    args_geojson.limit = 1
    args_geojson.all_scenes = False
    args_geojson.outdir = str(tmp_path)
    args_geojson.no_resume = False
    args_geojson.no_multipart = False
    args_geojson.threads = 2
    args_geojson.asset = None
    args_geojson.all = False

    with patch.object(client, "search", return_value=[item1]), \
         patch.object(client, "download", return_value=str(tmp_path / "1.tif")):
        cmd_download(args_geojson, client)
        captured = capsys.readouterr()
        assert "Searching for matching scenes in geojson" in captured.out
        assert "Selected latest scene: MULTI_1" in captured.out


def test_cmd_search_export_and_cdse_flags(capsys, tmp_path):
    client = OmniEarth()
    mock_res = SearchResult(
        id="S2_SEARCH_EXPORT_1",
        collection="SENTINEL-2",
        category=Category.OPTICAL,
        provider="cdse",
        assets={"B04": Asset(key="B04", href="https://example.com/b4.jp2")}
    )
    from omniearth.models import SearchResults
    results = SearchResults([mock_res], client=client)

    args = MagicMock()
    args.category = "optical"
    args.bbox = [78.0, 20.0, 78.5, 20.5]
    args.point = None
    args.geojson = None
    args.start = "2026-11-01"
    args.end = "2026-11-19"
    args.max_cloud = 15.0
    args.variables = None
    args.depth = None
    args.dataset = "cdse"
    args.year = 2026
    args.level = "sr"
    args.limit = 5
    args.provider = "cdse"
    args.format = "safe"
    args.bands = "B04,B03"
    args.export = str(tmp_path / "results.geojson")
    args.download_all = True
    args.download_top = None
    args.select = None
    args.interactive = False
    args.json = False
    args.outdir = str(tmp_path)
    args.no_resume = False
    args.no_multipart = False
    args.threads = 4
    args.asset = None
    args.verify_checksum = True
    args.composite = "rgb"

    with patch.object(client, "search", return_value=results) as mock_search, \
         patch.object(client, "download_many", return_value=[str(tmp_path / "b4.jp2")]) as mock_dm:
        cmd_search(args, client)
        captured = capsys.readouterr()
        assert "Exported 1 search result(s)" in captured.out
        assert "Dispatching concurrent download for 1 scene(s)" in captured.out
        mock_search.assert_called_once()
        assert mock_search.call_args.kwargs["provider"] == "cdse"
        assert mock_search.call_args.kwargs["format"] == "safe"
        assert mock_search.call_args.kwargs["bands"] == ["B04", "B03"]
        mock_dm.assert_called_once()
        assert mock_dm.call_args.kwargs["format"] == "safe"
        assert mock_dm.call_args.kwargs["bands"] == "B04,B03"
        assert mock_dm.call_args.kwargs["verify_checksum"] is True
        assert mock_dm.call_args.kwargs["composite"] == "rgb"


def test_cmd_download_cdse_flags_and_fallbacks(capsys, tmp_path):
    client = OmniEarth()

    # 1. CDSE fallback resolution for S2 SAFE item not found in catalog
    args_s2_fallback = MagicMock()
    args_s2_fallback.category = "optical"
    args_s2_fallback.id = "S2A_MSIL2A_20261119T0530_TEST"
    args_s2_fallback.bbox = None
    args_s2_fallback.geojson = None
    args_s2_fallback.provider = "cdse"
    args_s2_fallback.format = "safe"
    args_s2_fallback.bands = "rgb"
    args_s2_fallback.verify_checksum = True
    args_s2_fallback.composite = "rgb"
    args_s2_fallback.outdir = str(tmp_path)
    args_s2_fallback.all = False
    args_s2_fallback.no_resume = False
    args_s2_fallback.no_multipart = False
    args_s2_fallback.threads = 4
    args_s2_fallback.asset = None

    with patch.object(client, "get_item", return_value=None), \
         patch.object(client, "search", return_value=[]), \
         patch.object(client, "download", return_value=str(tmp_path / "s2.zip")) as mock_dl:
        cmd_download(args_s2_fallback, client)
        captured = capsys.readouterr()
        assert "attempting direct provider resolution" in captured.out
        assert "Successfully downloaded" in captured.out
        mock_dl.assert_called_once()
        assert mock_dl.call_args.kwargs["format"] == "safe"
        assert mock_dl.call_args.kwargs["bands"] == "rgb"
        assert mock_dl.call_args.kwargs["verify_checksum"] is True
        assert mock_dl.call_args.kwargs["composite"] == "rgb"

    # 2. AOI search download with provider and format
    args_aoi_cdse = MagicMock()
    args_aoi_cdse.category = "optical"
    args_aoi_cdse.id = None
    args_aoi_cdse.bbox = [78.0, 20.0, 78.5, 20.5]
    args_aoi_cdse.geojson = None
    args_aoi_cdse.start = None
    args_aoi_cdse.end = None
    args_aoi_cdse.max_cloud = None
    args_aoi_cdse.dataset = None
    args_aoi_cdse.year = None
    args_aoi_cdse.level = "sr"
    args_aoi_cdse.limit = 1
    args_aoi_cdse.all_scenes = False
    args_aoi_cdse.outdir = str(tmp_path)
    args_aoi_cdse.provider = "cdse"
    args_aoi_cdse.format = "safe"
    args_aoi_cdse.bands = None
    args_aoi_cdse.verify_checksum = False
    args_aoi_cdse.composite = None
    args_aoi_cdse.no_resume = False
    args_aoi_cdse.no_multipart = False
    args_aoi_cdse.threads = 4
    args_aoi_cdse.asset = None
    args_aoi_cdse.all = False

    mock_matched = SearchResult(
        id="S2A_MATCH", collection="SENTINEL-2", category=Category.OPTICAL, provider="cdse", assets={}
    )
    with patch.object(client, "search", return_value=[mock_matched]) as mock_search, \
         patch.object(client, "download", return_value=str(tmp_path / "matched.zip")):
        cmd_download(args_aoi_cdse, client)
        mock_search.assert_called_once()
        assert mock_search.call_args.kwargs["provider"] == "cdse"
        assert mock_search.call_args.kwargs["format"] == "safe"



