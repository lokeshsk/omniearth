"""
Tests for OmniEarth Geospatial Processors (omniearth.processors)
"""

import os
from pathlib import Path
import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

import omniearth.processors as processors
from omniearth.processors import (
    check_rasterio_available,
    create_rgb_composite,
    calculate_ndvi,
    create_composite_from_downloaded,
)


def _write_dummy_geotiff(path: Path, data: np.ndarray) -> str:
    transform = from_origin(78.0, 20.0, 0.001, 0.001)
    profile = {
        "driver": "GTiff",
        "height": data.shape[0],
        "width": data.shape[1],
        "count": 1,
        "dtype": data.dtype,
        "crs": "EPSG:4326",
        "transform": transform,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(data, 1)
    return str(path.resolve())


def test_check_rasterio_available(monkeypatch):
    # Success branch
    check_rasterio_available()

    # Failure branch
    monkeypatch.setattr(processors, "HAS_RASTERIO", False)
    with pytest.raises(ImportError, match="Geospatial raster processing requires 'rasterio'"):
        check_rasterio_available()


def test_create_rgb_composite(tmp_path):
    r_data = np.full((10, 10), 100, dtype=np.uint16)
    g_data = np.full((10, 10), 150, dtype=np.uint16)
    b_data = np.full((10, 10), 200, dtype=np.uint16)

    r_path = tmp_path / "red.tif"
    g_path = tmp_path / "green.tif"
    b_path = tmp_path / "blue.tif"
    out_path = tmp_path / "composite_rgb.tif"

    _write_dummy_geotiff(r_path, r_data)
    _write_dummy_geotiff(g_path, g_data)
    _write_dummy_geotiff(b_path, b_data)

    res = create_rgb_composite(r_path, g_path, b_path, out_path)
    assert Path(res).exists()

    with rasterio.open(out_path) as ds:
        assert ds.count == 3
        assert np.array_equal(ds.read(1), r_data)
        assert np.array_equal(ds.read(2), g_data)
        assert np.array_equal(ds.read(3), b_data)


def test_calculate_ndvi(tmp_path):
    # Array with some zeros to test denominator == 0 branch
    red_data = np.array([[100, 0], [200, 300]], dtype=np.float32)
    nir_data = np.array([[300, 0], [400, 300]], dtype=np.float32)

    r_path = tmp_path / "red.tif"
    n_path = tmp_path / "nir.tif"
    out_path = tmp_path / "ndvi.tif"

    _write_dummy_geotiff(r_path, red_data)
    _write_dummy_geotiff(n_path, nir_data)

    res = calculate_ndvi(r_path, n_path, out_path)
    assert Path(res).exists()

    with rasterio.open(out_path) as ds:
        assert ds.count == 1
        ndvi = ds.read(1)
        # (300 - 100) / (300 + 100) = 0.5
        assert np.isclose(ndvi[0, 0], 0.5)
        # Denominator == 0 -> 0.0
        assert np.isclose(ndvi[0, 1], 0.0)


def test_create_composite_from_downloaded_all_types(tmp_path):
    data = np.full((5, 5), 50, dtype=np.uint16)

    b02 = tmp_path / "T32TMT_20261119_B02_10m.jp2"
    b03 = tmp_path / "T32TMT_20261119_B03_10m.jp2"
    b04 = tmp_path / "T32TMT_20261119_B04_10m.jp2"
    b08 = tmp_path / "T32TMT_20261119_B08_10m.jp2"
    b8a = tmp_path / "T32TMT_20261119_B8A_20m.jp2"
    b12 = tmp_path / "T32TMT_20261119_B12_20m.jp2"

    for p in (b02, b03, b04, b08, b8a, b12):
        _write_dummy_geotiff(p, data)

    # 1. 'rgb' composite from directory path
    out_rgb = create_composite_from_downloaded(tmp_path, composite_type="rgb")
    assert out_rgb is not None
    assert Path(out_rgb).exists()
    assert "RGB" in out_rgb

    # 2. 'false-color' composite from list of file paths with custom output_path
    custom_fc = tmp_path / "custom_fc.tif"
    out_fc = create_composite_from_downloaded(
        [b02, b03, b04, b08, b8a, b12],
        composite_type="false-color",
        output_path=custom_fc
    )
    assert out_fc == str(custom_fc.resolve())
    assert custom_fc.exists()

    # 3. 'swir' composite
    out_swir = create_composite_from_downloaded(tmp_path, composite_type="swir")
    assert out_swir is not None
    assert "SWIR" in out_swir


def test_create_composite_from_downloaded_errors(tmp_path):
    data = np.full((5, 5), 50, dtype=np.uint16)
    b04 = tmp_path / "T32TMT_20261119_B04_10m.jp2"
    _write_dummy_geotiff(b04, data)

    # Unsupported composite type
    with pytest.raises(ValueError, match="Unsupported composite type"):
        create_composite_from_downloaded(tmp_path, composite_type="radar")

    # Missing band files error
    with pytest.raises(FileNotFoundError, match="missing band file"):
        create_composite_from_downloaded(tmp_path, composite_type="rgb")

    # Missing green only
    b02 = tmp_path / "T32TMT-b02-10m.jp2"
    _write_dummy_geotiff(b02, data)
    with pytest.raises(FileNotFoundError, match="Green/Red band"):
        create_composite_from_downloaded([b04, b02], composite_type="rgb")

    # Missing red only
    b03 = tmp_path / "T32TMT-b03-10m.jp2"
    _write_dummy_geotiff(b03, data)
    with pytest.raises(FileNotFoundError, match="Red/NIR band"):
        create_composite_from_downloaded([b03, b02], composite_type="rgb")
