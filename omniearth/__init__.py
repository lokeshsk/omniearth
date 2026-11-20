"""
OmniEarth
=========
Universal Multi-Modal Open Earth Observation, Hyperspectral, and Weather Data Engine.

Author: Lokesh S. K. (https://lokeshsk.github.io)
Repository: https://github.com/lokeshsk/omniearth
"""

__version__ = "1.5.1"
__author__ = "Lokesh Kumar"

from omniearth.client import OmniEarth
from omniearth.models import AOI, SearchResult, SearchResults, Asset, Category, FilterOptions
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

from omniearth.version_checker import check_for_updates, whats_new

__all__ = [
    "OmniEarth",
    "AOI",
    "SearchResult",
    "SearchResults",
    "Asset",
    "Category",
    "FilterOptions",
    "check_for_updates",
    "whats_new",
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
