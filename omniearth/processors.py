"""
OmniEarth Geospatial Processors
================================
Provides on-the-fly raster compositing (True Color RGB, False Color Infrared),
spectral index raster generation (NDVI), and format conversion using rasterio.
"""

import logging
from pathlib import Path
from typing import List, Optional, Union

logger = logging.getLogger(__name__)

try:
    import rasterio
    HAS_RASTERIO = True
except ImportError:  # pragma: no cover
    HAS_RASTERIO = False


def check_rasterio_available() -> None:
    """Verifies that rasterio is installed before running geospatial conversions."""
    if not HAS_RASTERIO:
        raise ImportError(
            "Geospatial raster processing requires 'rasterio'.\n"
            "Install optional geospatial dependencies using:\n"
            "  pip install 'omniearth[geo]'\n"
            "or with uv:\n"
            "  uv add rasterio"
        )


def create_rgb_composite(
    red_path: Union[str, Path],
    green_path: Union[str, Path],
    blue_path: Union[str, Path],
    output_path: Union[str, Path],
    compress: str = "deflate"
) -> str:
    """
    Combines Red, Green, and Blue single-band raster files into a 3-band GeoTIFF composite.
    Preserves spatial CRS, resolution, and georeferencing metadata.
    """
    check_rasterio_available()
    r_p = Path(red_path)
    g_p = Path(green_path)
    b_p = Path(blue_path)
    out_p = Path(output_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.open(r_p) as src_r:
        profile = src_r.profile.copy()
        profile.update(
            driver="GTiff",
            count=3,
            compress=compress,
            tiled=True,
            blockxsize=256,
            blockysize=256
        )

        with rasterio.open(g_p) as src_g, rasterio.open(b_p) as src_b:
            r_data = src_r.read(1)
            g_data = src_g.read(1)
            b_data = src_b.read(1)

            with rasterio.open(out_p, "w", **profile) as dst:
                dst.write(r_data, 1)
                dst.write(g_data, 2)
                dst.write(b_data, 3)
                try:
                    from rasterio.enums import ColorInterp
                    dst.colorinterp = (ColorInterp.red, ColorInterp.green, ColorInterp.blue)
                except Exception:  # pragma: no cover
                    pass

    return str(out_p.resolve())


def calculate_ndvi(
    red_path: Union[str, Path],
    nir_path: Union[str, Path],
    output_path: Union[str, Path]
) -> str:
    """
    Computes Normalized Difference Vegetation Index (NDVI) from Red and NIR bands:
    NDVI = (NIR - Red) / (NIR + Red)
    """
    check_rasterio_available()
    import numpy as np

    r_p = Path(red_path)
    n_p = Path(nir_path)
    out_p = Path(output_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.open(r_p) as red_ds, rasterio.open(n_p) as nir_ds:
        red = red_ds.read(1).astype("float32")
        nir = nir_ds.read(1).astype("float32")

        denominator = nir + red
        ndvi = np.zeros_like(nir, dtype="float32")
        valid = denominator != 0
        np.divide(nir - red, denominator, out=ndvi, where=valid)

        profile = red_ds.profile.copy()
        profile.update(
            dtype="float32",
            count=1,
            driver="GTiff",
            nodata=0,
            compress="deflate"
        )

        with rasterio.open(out_p, "w", **profile) as dst:
            dst.write(ndvi, 1)

    return str(out_p.resolve())


def create_composite_from_downloaded(
    directory_or_files: Union[str, Path, List[Union[str, Path]]],
    composite_type: str = "rgb",
    output_path: Optional[Union[str, Path]] = None
) -> Optional[str]:
    """
    Finds matching band files in a directory or list of file paths and merges them
    into a 3-band GeoTIFF composite.
    Supported types:
      - 'rgb' or 'true-color': Red=B04/red, Green=B03/green, Blue=B02/blue
      - 'false-color' or 'cir': NIR=B08/nir, Red=B04/red, Green=B03/green
      - 'swir': SWIR=B12/swir, Narrow NIR=B8A, Red=B04/red
    """
    check_rasterio_available()

    if isinstance(directory_or_files, (list, tuple)):
        files = [Path(f) for f in directory_or_files]
        directory = files[0].parent if files else Path(".")
    else:
        directory = Path(directory_or_files)
        files = list(directory.glob("*.*"))

    def _find_band(band_code: str, alt_names: List[str]) -> Optional[Path]:
        candidates = [band_code.lower()] + [a.lower() for a in alt_names]
        for f in files:
            fname = f.name.lower()
            if f.suffix.lower() in (".jp2", ".tif", ".tiff"):
                for c in candidates:
                    if f"_{c}_" in fname or f"_{c}." in fname or fname.startswith(f"{c}_") or fname.startswith(f"{c}."):
                        return f
                    # S2 style: B04, B03, B02
                    if f"-{c}-" in fname or f"-{c}." in fname:
                        return f
        return None

    c_type = composite_type.lower()
    if c_type in ("rgb", "true-color"):
        b_r = _find_band("b04", ["red", "b4"])
        b_g = _find_band("b03", ["green", "b3"])
        b_b = _find_band("b02", ["blue", "b2"])
        suffix = "RGB"
    elif c_type in ("false-color", "cir"):
        b_r = _find_band("b08", ["nir", "b8"])
        b_g = _find_band("b04", ["red", "b4"])
        b_b = _find_band("b03", ["green", "b3"])
        suffix = "FalseColor"
    elif c_type in ("swir", "geology"):
        b_r = _find_band("b12", ["swir2", "b12"])
        b_g = _find_band("b8a", ["narrow_nir", "nir08"])
        b_b = _find_band("b04", ["red", "b4"])
        suffix = "SWIR"
    else:
        raise ValueError(f"Unsupported composite type: '{composite_type}'. Supported: 'rgb', 'false-color', 'swir'")

    if not b_r or not b_g or not b_b:
        missing = []
        if not b_r:
            missing.append("Red/NIR band")
        if not b_g:
            missing.append("Green/Red band")
        if not b_b:
            missing.append("Blue/Green band")
        raise FileNotFoundError(
            f"Cannot create {composite_type} composite: missing band file(s): {', '.join(missing)}"
        )

    out = Path(output_path) if output_path else (directory / f"{directory.name}_{suffix}.tif")
    return create_rgb_composite(b_r, b_g, b_b, out)
