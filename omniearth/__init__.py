"""
OmniEarth
=========
Universal Multi-Modal Open Earth Observation, Hyperspectral, and Weather Data Engine.

Author: Lokesh S. K. (https://lokeshsk.github.io)
Repository: https://github.com/lokeshsk/omniearth
"""

__version__ = "1.3.2"
__author__ = "Lokesh Kumar"

from omniearth.client import OmniEarth
from omniearth.models import AOI, SearchResult, Asset, Category, FilterOptions
from omniearth.indices import (
    compute_spectral_index,
    calculate_ndvi,
    calculate_ndwi,
    calculate_ndre,
    calculate_evi,
    calculate_nbr,
    calculate_savi,
    calculate_msavi,
    calculate_bsi,
    calculate_mndwi,
)

__all__ = [
    "OmniEarth",
    "AOI",
    "SearchResult",
    "Asset",
    "Category",
    "FilterOptions",
    "compute_spectral_index",
    "calculate_ndvi",
    "calculate_ndwi",
    "calculate_ndre",
    "calculate_evi",
    "calculate_nbr",
    "calculate_savi",
    "calculate_msavi",
    "calculate_bsi",
    "calculate_mndwi",
]
