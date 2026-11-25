---
title: 'OmniEarth: A Unified Multi-Modal Earth Observation and Environmental Data Engine for Python, Node.js, and the CLI'
tags:
  - Python
  - TypeScript
  - Earth Observation
  - Remote Sensing
  - STAC
  - Hyperspectral
  - Geospatial
authors:
  - name: Lokesh Kumar
    affiliation: 1
affiliations:
  - name: Independent Researcher, India
    index: 1
date: 25 November 2026
bibliography: paper.bib
---

# Summary

Modern environmental science, precision agriculture, climate modeling, and GeoAI workflows routinely require fusing heterogeneous Earth Observation (EO) modalities: optical multispectral reflectance, synthetic aperture radar (SAR), spaceborne imaging spectroscopy (hyperspectral cubes), digital elevation models (DEM), land use/land cover (LULC), meteorological reanalysis, 3D soil profiles, atmospheric trace gases, active fire anomalies, ocean color, radar altimetry, precipitation, hydrology, and nighttime lights.

**OmniEarth** is an open-source, Apache-2.0 licensed data discovery, aggregation, and streaming engine providing feature-equivalent **Python** (`pip install omniearth`) and **Node.js / TypeScript** (`npm install omniearth`) SDKs, a unified **CLI** (`omniearth`), and a zero-dependency **Model Context Protocol (MCP)** server (`omniearth-mcp`). It unifies 14 geospatial and environmental modalities behind a single spatial query interface (`bbox`, `point`, or `GeoJSON`), enabling 12 of the 14 modalities to run with zero authentication setup while preserving optional authenticated access to Copernicus Data Space Ecosystem (CDSE), NASA Earthdata, and DLR EnMAP archives.

# Statement of Need

While open Earth Observation archives have expanded rapidly through AWS Open Data, STAC catalogs [@stac_spec], NASA Earthdata CMR, Copernicus Data Space Ecosystem, Open-Meteo, and ISRIC SoilGrids [@poggio2021soilgrids], practitioners still face severe integration friction:

1. **Fragmented APIs and Protocols:** Scientists must combine STAC JSON APIs (`Element84 Earth Search`, `DLR EOC STAC`, `NASA CMR STAC`), OData product endpoints (`CDSE`), custom REST JSON services (`Open-Meteo`, `SoilGrids`, `NASA FIRMS`), and direct Cloud-Optimized GeoTIFF (COG) tiling grids (`Copernicus DEM GLO-30`, `ESA WorldCover` [@zanaga2021worldcover]).
2. **Inconsistent Spatial/Temporal Semantics:** Existing libraries are frequently tied to a single ecosystem (e.g., Python-only STAC clients or platform-specific cloud sandboxes) and rarely unify raster satellite catalogs with tabular weather, evapotranspiration, or multi-depth soil profiles under a consistent spatial footprint and chronological ordering.
3. **Resilience and Observability Gaps:** Upstream archives experience maintenance windows, rate limits (HTTP 429), and transient HTTP 5xx outages. Silent empty results lead researchers to misinterpret server outages as missing satellite coverage.

OmniEarth resolves these barriers by abstracting protocol heterogeneity, coordinate-tile resolution, semantic asset aliasing, parallel resumable HTTP Range downloads, and upstream health diagnostics into one lightweight, cross-language toolkit.

# Architecture and Capabilities

OmniEarth exposes a symmetric object model across Python and TypeScript anchored around `OmniEarth`, `SearchResult`, and `SearchResults`:

- **Unified Multi-Modal Discovery:** Supports 14 categories (`optical`, `hyperspectral`, `sar`, `elevation`, `landcover`, `weather`, `soil`, `atmosphere`, `fire`, `ocean`, `altimetry`, `precipitation`, `hydrology`, and `nightlights`) with chronological descending ordering and in-memory filtering.
- **Zero-Config & Optional Auth Routing:** Public COGs and open environmental feeds work out of the box without credentials, while `.env` credential detection seamlessly unlocks raw Copernicus `.SAFE` archives, NASA EMIT [@green2020emit] / CMR granules, and DLR EnMAP [@guanter2015enmap] hyperspectral scenes.
- **Ecosystem Exports & Analytics:** Provides fluent GeoJSON (`to_geojson_dict()`, `export_geojson()`), tabular CSV (`export_csv()`), `geopandas.GeoDataFrame` (`to_geodataframe()`), and `xarray`/`rioxarray` (`to_xarray()`) integration alongside built-in radiometric index computation (`NDVI`, `NDWI`, `NDRE`, `EVI`, `NBR`, `SAVI`, `MSAVI`, `BSI`, `MNDWI`) and GeoTIFF compositing.
- **High-Throughput Streaming & Resilience:** Implements concurrent multipart HTTP Range downloads, HTTP 206 resumable transfer recovery, SHA256/MD5 checksum verification, and structured `stderr` upstream provider health notifications (`warn_upstream_issue`).
- **AI Agent Interoperability:** Ships a pure-Python stdio MCP server (`omniearth-mcp`) so AI assistants and automated geospatial pipelines can query live satellite availability, weather, soil, and spectral indices directly.

# Quality Assurance and Reproducibility

OmniEarth maintains strict parity between its Python and TypeScript implementations, backed by cross-platform CI matrices (Linux, macOS, Windows), 100% statement test coverage in Python (`pytest-cov`), automated TypeScript unit tests, static security analysis (`CodeQL`), and cryptographically signed SLSA build provenance for both PyPI and npm releases.

# References
