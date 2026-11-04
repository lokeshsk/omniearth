"""
OmniEarth Spectral and Biophysical Index Engine
==============================================
Sensor-agnostic radiometric and biophysical indices calculation across
satellite modalities (Sentinel-2, Landsat, EnMAP, PRISMA).
Supported indices:
- NDVI:  Normalized Difference Vegetation Index
- NDWI:  Normalized Difference Water Index (McFeeters 1996)
- NDRE:  Normalized Difference Red Edge (Gitelson & Merzlyak 1994)
- EVI:   Enhanced Vegetation Index (Huete et al. 2002)
- NBR:   Normalized Burn Ratio (Key & Benson 2006)
- SAVI:  Soil-Adjusted Vegetation Index (Huete 1988)
- MSAVI: Modified Soil-Adjusted Vegetation Index (Qi et al. 1994)
- BSI:   Bare Soil Index (Rikimaru et al. 2002)
- MNDWI: Modified Normalized Difference Water Index (Xu 2006)
"""

import json
from typing import Any, Dict, List, Optional, Union

SUPPORTED_INDICES = ["ndvi", "ndwi", "ndre", "evi", "nbr", "savi", "msavi", "bsi", "mndwi"]
EPSILON = 1e-8


def _calc_scalar_or_array(
    index_name: str,
    n: float,
    r: Optional[float] = None,
    g: Optional[float] = None,
    b: Optional[float] = None,
    re: Optional[float] = None,
    s: Optional[float] = None,
    l: float = 0.5
) -> float:
    """Internal formula evaluator for a single pixel or scalar values."""
    idx = index_name.lower()
    if idx == "ndvi":
        if r is None:
            raise ValueError("Red band required to compute NDVI")
        return (float(n) - float(r)) / (float(n) + float(r) + EPSILON)
    elif idx == "ndwi":
        if g is None:
            raise ValueError("Green band required to compute NDWI")
        return (float(g) - float(n)) / (float(g) + float(n) + EPSILON)
    elif idx == "ndre":
        if re is None:
            raise ValueError("RedEdge band required to compute NDRE")
        return (float(n) - float(re)) / (float(n) + float(re) + EPSILON)
    elif idx == "evi":
        if r is None or b is None:
            raise ValueError("Red and Blue bands required to compute EVI")
        return 2.5 * ((float(n) - float(r)) / (float(n) + 6.0 * float(r) - 7.5 * float(b) + 1.0 + EPSILON))
    elif idx == "nbr":
        if s is None:
            raise ValueError("SWIR band required to compute NBR")
        return (float(n) - float(s)) / (float(n) + float(s) + EPSILON)
    elif idx == "savi":
        if r is None:
            raise ValueError("Red band required to compute SAVI")
        return (1.0 + l) * (float(n) - float(r)) / (float(n) + float(r) + l + EPSILON)
    elif idx == "msavi":
        if r is None:
            raise ValueError("Red band required to compute MSAVI")
        term = (2.0 * float(n) + 1.0) ** 2 - 8.0 * (float(n) - float(r))
        safe_term = max(0.0, term)
        return (2.0 * float(n) + 1.0 - (safe_term ** 0.5)) / 2.0
    elif idx == "bsi":
        if r is None or b is None or s is None:
            raise ValueError("Red, Blue, and SWIR bands required to compute BSI")
        num = (float(s) + float(r)) - (float(n) + float(b))
        denom = (float(s) + float(r)) + (float(n) + float(b)) + EPSILON
        return num / denom
    elif idx == "mndwi":
        if g is None or s is None:
            raise ValueError("Green and SWIR bands required to compute MNDWI")
        return (float(g) - float(s)) / (float(g) + float(s) + EPSILON)
    else:
        raise ValueError(f"Unsupported index '{index_name}'. Supported indices: {', '.join(SUPPORTED_INDICES)}")


def compute_spectral_index(
    index: str,
    nir: Any,
    red: Optional[Any] = None,
    green: Optional[Any] = None,
    blue: Optional[Any] = None,
    rededge: Optional[Any] = None,
    swir: Optional[Any] = None,
    l_factor: float = 0.5,
    outpath: Optional[str] = None
) -> Dict[str, Any]:
    """
    Computes a remote sensing spectral index over scalars or lists/arrays.
    Returns a dictionary with summary statistics (mean, min, max, std) and data.
    """
    idx = index.lower()

    if isinstance(nir, (list, tuple)):
        r_list = red if isinstance(red, (list, tuple)) else [red] * len(nir)
        g_list = green if isinstance(green, (list, tuple)) else [green] * len(nir)
        b_list = blue if isinstance(blue, (list, tuple)) else [blue] * len(nir)
        re_list = rededge if isinstance(rededge, (list, tuple)) else [rededge] * len(nir)
        s_list = swir if isinstance(swir, (list, tuple)) else [swir] * len(nir)

        data = [
            _calc_scalar_or_array(idx, nir[i], r_list[i], g_list[i], b_list[i], re_list[i], s_list[i], l=l_factor)
            for i in range(len(nir))
        ]
        mean_val = sum(data) / len(data) if data else 0.0
        min_val = min(data) if data else 0.0
        max_val = max(data) if data else 0.0
        variance = sum((x - mean_val) ** 2 for x in data) / len(data) if data else 0.0
        std_val = variance ** 0.5
    else:
        val = _calc_scalar_or_array(idx, nir, red, green, blue, rededge, swir, l=l_factor)
        data = val
        mean_val = float(val)
        min_val = float(val)
        max_val = float(val)
        std_val = 0.0

    stats = {
        "index": idx,
        "mean": mean_val,
        "min": min_val,
        "max": max_val,
        "std": std_val,
        "data": data
    }

    if outpath:
        with open(outpath, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2)

    return stats


def calculate_ndvi(nir: Any, red: Any) -> Dict[str, Any]:
    """Convenience function for NDVI."""
    return compute_spectral_index("ndvi", nir=nir, red=red)


def calculate_ndwi(green: Any, nir: Any) -> Dict[str, Any]:
    """Convenience function for NDWI (McFeeters)."""
    return compute_spectral_index("ndwi", nir=nir, green=green)


def calculate_ndre(nir: Any, rededge: Any) -> Dict[str, Any]:
    """Convenience function for NDRE."""
    return compute_spectral_index("ndre", nir=nir, rededge=rededge)


def calculate_evi(nir: Any, red: Any, blue: Any) -> Dict[str, Any]:
    """Convenience function for EVI."""
    return compute_spectral_index("evi", nir=nir, red=red, blue=blue)


def calculate_nbr(nir: Any, swir: Any) -> Dict[str, Any]:
    """Convenience function for NBR."""
    return compute_spectral_index("nbr", nir=nir, swir=swir)


def calculate_savi(nir: Any, red: Any, l_factor: float = 0.5) -> Dict[str, Any]:
    """Convenience function for SAVI."""
    return compute_spectral_index("savi", nir=nir, red=red, l_factor=l_factor)


def calculate_msavi(nir: Any, red: Any) -> Dict[str, Any]:
    """Convenience function for MSAVI."""
    return compute_spectral_index("msavi", nir=nir, red=red)


def calculate_bsi(nir: Any, red: Any, blue: Any, swir: Any) -> Dict[str, Any]:
    """Convenience function for Bare Soil Index (BSI)."""
    return compute_spectral_index("bsi", nir=nir, red=red, blue=blue, swir=swir)


def calculate_mndwi(green: Any, swir: Any) -> Dict[str, Any]:
    """Convenience function for Modified NDWI (MNDWI)."""
    return compute_spectral_index("mndwi", nir=0.0, green=green, swir=swir)

