"""
Tests for OmniEarth Client and Category Resolution
"""

import pytest
from omniearth import OmniEarth, Category, AOI


def test_client_initialization_and_categories():
    client = OmniEarth()
    categories = client.list_categories()
    assert "optical" in categories
    assert "hyperspectral" in categories
    assert "sar" in categories
    assert "weather" in categories
    assert "soil" in categories


def test_resolve_aoi():
    client = OmniEarth()
    
    # 1. Direct AOI
    aoi = AOI.from_bounds(10, 20, 11, 21)
    res = client._resolve_aoi(aoi, None, None)
    assert res.min_lon == 10

    # 2. Bbox
    res2 = client._resolve_aoi(None, [10, 20, 11, 21], None)
    assert res2.max_lat == 21

    # 3. Point
    res3 = client._resolve_aoi(None, None, (10.0, 20.0, 2.0))
    assert res3.min_lon < 10.0 < res3.max_lon

    # 4. Error when none provided
    with pytest.raises(ValueError):
        client._resolve_aoi(None, None, None)


def test_invalid_category():
    client = OmniEarth()
    with pytest.raises(ValueError):
        client.search(category="invalid_category", bbox=[10, 20, 11, 21])
