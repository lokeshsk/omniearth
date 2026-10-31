"""
OmniEarth
=========
Universal Multi-Modal Open Earth Observation, Hyperspectral, and Weather Data Engine.

Author: Lokesh S. K. (https://lokeshsk.github.io)
Repository: https://github.com/lokeshsk/omniearth
"""

__version__ = "1.2.0"
__author__ = "Lokesh Kumar"

from omniearth.client import OmniEarth
from omniearth.models import AOI, SearchResult, Asset, Category, FilterOptions

__all__ = [
    "OmniEarth",
    "AOI",
    "SearchResult",
    "Asset",
    "Category",
    "FilterOptions",
]
