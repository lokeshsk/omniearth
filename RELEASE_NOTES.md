# OmniEarth v1.5.2 Release Notes

**Release Date:** November 20, 2026  
**DOI:** [10.5281/zenodo.24359617](https://doi.org/10.5281/zenodo.24359617)  
**PyPI:** [omniearth 1.5.2](https://pypi.org/project/omniearth/)  
**npm:** [omniearth 1.5.2](https://www.npmjs.com/package/omniearth)  

OmniEarth v1.5.2 is a maintenance and feature patch release introducing a **Non-Blocking Version & Update Notification Engine** across Python and Node.js SDKs/CLIs, **Automated GitHub Release Notes Generation**, and streamlined **Hyperspectral Provider Routing** focused on NASA EMIT and DLR EnMAP.

---

## Key Highlights in v1.5.2

### 1. Non-Blocking Version & Update Notification Engine
Users are now automatically alerted when newer OmniEarth releases are published on PyPI or npm:
- **24-Hour Cache**: Checked against local cache (`~/.cache/omniearth/version_check.json` / `npm_version_check.json`) with an aggressive 1.5s timeout. Queries remote registries only once daily.
- **Non-Intrusive Stderr Banner**: Clean box banner sent to `sys.stderr`, preventing corruption of piped CLI JSON outputs or automated scripts.
- **Opt-Out Controls**: Respects `OMNIEARTH_NO_UPDATE_CHECK=1`, `CI=true`, `--json`, and non-interactive TTY environments.
- **Inspect New Releases**:
  - CLI: `omniearth whatsnew` displays formatted highlights and changelog links.
  - Python SDK: `omniearth.whats_new()`
  - Node.js / TypeScript SDK: `whatsNew()`

### 2. Automated GitHub Release Notes & Provenance
- `publish.yml` integrates `softprops/action-gh-release@v2` with `generate_release_notes: true`, automatically compiling pull requests, commit highlights, and distributing signed wheel/sdist/npm artifacts upon tag push.
- Full compliance with Keep a Changelog documented in `CHANGELOG.md`.

### 3. Streamlined Hyperspectral Architecture
- Decoupled ASI PRISMA routing from OmniEarth core while automated programmatic download protocol is finalized in a dedicated external pilot project (`prisma_pilot`).
- Hyperspectral searches and downloads remain fully supported and focused on **NASA EMIT** (285 bands, 381-2493 nm) and **DLR EnMAP** (224 bands, 420-2450 nm).

---

# OmniEarth v1.5.1 Release Notes

**Release Date:** November 20, 2026  
**DOI:** [10.5281/zenodo.24359617](https://doi.org/10.5281/zenodo.24359617)  
**PyPI:** [omniearth 1.5.1](https://pypi.org/project/omniearth/)  
**npm:** [omniearth 1.5.1](https://www.npmjs.com/package/omniearth)  

OmniEarth v1.5.1 is a targeted patch release introducing **Direct Provider and Dataset Targeting** for hyperspectral missions (NASA EMIT, DLR EnMAP) and elevation models (Copernicus DEM, SRTM, ALOS World 3D-30m) across both the Python and TypeScript SDKs.

---

## Key Highlights in v1.5.1

### 1. Direct Hyperspectral Provider and Dataset Routing
Users can now query specific hyperspectral constellations directly from the CLI and SDK via `--provider` or `--dataset` (`emit`, `enmap`) without triggering the default multi-sensor cascade:
- `--provider emit` / `--dataset emit`: Queries the NASA LP DAAC STAC endpoint for EMIT L2A reflectance products.
- `--provider enmap` / `--dataset enmap`: Queries DLR EOC WCS for EnMAP hyperspectral L2A data.
- Example:
  ```bash
  omniearth search --category hyperspectral --provider emit --aoi 12.4 41.8 12.6 42.0 --year 2026
  ```

### 2. Interchangeable Elevation Provider and Dataset Flags
Standardized CLI and client parameter handling for digital elevation models, accepting `--provider` and `--dataset` interchangeably:
- `--provider copernicus` / `--dataset copernicus`: Copernicus DEM GLO-30 (30m global DSM).
- `--provider srtm` / `--dataset srtm`: NASA SRTM v3 (30m elevation).
- `--provider alos` / `--dataset alos`: JAXA ALOS World 3D-30m (AW3D30).
- Example:
  ```bash
  omniearth search --category elevation --provider copernicus --aoi 78.0 20.0 78.5 20.5
  ```

---

# OmniEarth v1.5.0 Release Notes

**Release Date:** November 20, 2026  
**DOI:** [10.5281/zenodo.24359617](https://doi.org/10.5281/zenodo.24359617)  
**PyPI:** [omniearth 1.5.0](https://pypi.org/project/omniearth/)  
**npm:** [omniearth 1.5.0](https://www.npmjs.com/package/omniearth)  

OmniEarth v1.5.0 introduces **Universal Semantic Asset Selection**, an **Interactive Terminal Asset Selector (`-i` / `--interactive`)**, dedicated **Scene Folder Packaging (`--folder` / `folder=True`)**, direct **ZIP Archive Packaging (`--zip` / `zip=True`)**, and **URL-Level Parallel Asset Deduplication** across all 14 Earth Observation and environmental modalities in both the Python SDK and Node.js / TypeScript SDK.

---

## Key Highlights in v1.5.0

### 1. Universal Semantic Asset Aliasing (`resolve_asset_key` / `resolveAssetKey`)
Standardizes asset resolution across all 14 modalities and providers. Users no longer need to know provider-specific internal STAC dictionary keys (such as `001/EMIT_L2A_RFL_.../EMIT_L2A_RFL_...` or `B04`):
- **Hyperspectral (NASA EMIT & DLR EnMAP)**: `cube`, `rfl`, `reflectance`, `uncert`, `mask`, `browse`, `thumbnail`, `xml`, `metadata`
- **Optical (Sentinel-2 & Landsat-8/9)**: `visual`, `rgb`, `tci`, `red`, `green`, `blue`, `nir`, `swir16`, `swir22`, `b02`, `b03`, `b04`, `b08`, `b11`, `b12`, `safe`
- **SAR (Sentinel-1)**: `sar`, `vv`, `vh`, `hh`, `hv`, `amplitude`, `intensity`, `measurement`, `safe`
- **Elevation (Copernicus DEM & NASADEM)**: `dem`, `elevation`, `height`, `terrain`, `cog`
- **Land Cover (ESA WorldCover & Dynamic World)**: `map`, `landcover`, `classification`, `lc`, `cog`
- **Atmosphere (Sentinel-5P & CAMS)**: `no2`, `co`, `o3`, `so2`, `ch4`, `aer_ai`, `hcho`, `atmosphere`, `netcdf`
- **Weather (Open-Meteo & ERA5)**: `weather`, `meteo`, `forecast`, `temperature`, `data`
- **Soil (ISRIC SoilGrids)**: `soil`, `profile`, `clay`, `sand`, `ph`, `soc`, `bulk_density`, `cec`
- **Fire (FIRMS VIIRS/MODIS)**: `fire`, `hotspot`, `thermal`, `csv`, `geojson`
- **Ocean (Sentinel-3 OLCI/SLSTR & Copernicus Marine)**: `ocean`, `sst`, `chlorophyll`, `salinity`, `temperature`
- **Altimetry (Sentinel-6 & Jason-3)**: `altimetry`, `sla`, `adt`, `ssh`, `sea_surface_height`
- **Precipitation (GPM IMERG & CHIRPS)**: `precipitation`, `precip`, `rain`, `rainfall`, `imerg`
- **Hydrology (GLDAS & NASA SMAP)**: `hydrology`, `hydro`, `soil_moisture`, `runoff`, `evapotranspiration`
- **Nightlights (VIIRS DNB & Black Marble)**: `nightlights`, `dnb`, `radiance`, `lights`

### 2. Interactive Terminal Asset Picker (`-i` / `--interactive`)
Adds an interactive selection mode when downloading scenes from the CLI:
- Automatically queries available assets for the specified scene ID.
- Displays an interactive menu displaying each asset key, format (MIME type), and human-readable file size.
- Prompts the user to pick a specific asset number or download all scene assets concurrently.
- Syntax:
  ```bash
  omniearth download --category hyperspectral --id EMIT_L2A_RFL_001_20260819T071612_2623105_035 -i
  ```

### 3. Dedicated Scene Folder Packaging (`--folder` / `folder=True`)
Prevents output directory clutter when downloading complex scenes containing dozens of band files and metadata:
- Automatically creates an isolated scene subdirectory at `<outdir>/<scene_id>/...`.
- Supported across `download()`, `download_all()`, and CLI `omniearth download`.

### 4. Direct ZIP Archive Packaging (`--zip` / `zip=True`)
Bundles downloaded scene assets directly into a clean, portable `.zip` archive:
- In Python: Leverages standard library `shutil.make_archive` for lossless compression.
- In TypeScript / Node.js: Implements cross-platform native archive generation (`zip -r -q` on Unix/macOS, `Compress-Archive` on Windows PowerShell).
- Automatically sets the archive path at `<outdir>/<scene_id>.zip`.
- Syntax:
  ```bash
  omniearth download --category elevation --id Copernicus_DSM_COG_10_N20_00_E078_00_DEM --zip
  ```

### 5. Parallel Asset URL Deduplication
STAC catalogs frequently map multiple metadata keys (e.g. `data` and `dem`) to the exact same remote GeoTIFF URL:
- OmniEarth now deduplicates candidate asset keys by underlying URL (`href`) before launching concurrent worker threads.
- Eliminates redundant network egress, duplicate disk writes, and concurrent `.part` staging file lock collisions.
- Returns all mapped keys pointing to the single resolved local file in the returned download dictionary.

---

# OmniEarth v1.4.0 Release Notes

**Release Date:** November 19, 2026  
**DOI:** [10.5281/zenodo.23689449](https://doi.org/10.5281/zenodo.23689449)  
**PyPI:** [omniearth 1.4.0](https://pypi.org/project/omniearth/)  
**npm:** [omniearth 1.4.0](https://www.npmjs.com/package/omniearth)  

OmniEarth v1.4.0 delivers a major architectural unification of **Search** and **Download** pipelines across the Python SDK, TypeScript SDK, and CLI, while integrating full Smart Sentinel Data Downloader capabilities: the official **Copernicus Data Space Ecosystem (CDSE)** adapter, full raw `.SAFE.zip` downloads, selective band extraction via OData `/Nodes` tree traversal, space-agency cryptographic checksum verification, GIS footprint exports (`.geojson` / `.csv`), and on-the-fly GeoTIFF compositing (RGB, CIR, NDVI).

---

## Key Highlights in v1.4.0

### 1. Official Copernicus Data Space Ecosystem (CDSE) Adapter & Raw SAFE Support
OmniEarth now natively supports direct querying and streaming from the official Copernicus Data Space Ecosystem (CDSE) for Sentinel-1, Sentinel-2, Sentinel-3, and Sentinel-5P:
- **Full Raw Product Downloads**: Download raw `.SAFE.zip`, `.SEN3`, and `.nc` archives directly from CDSE OData endpoints with byte-range HTTP resume and concurrent multi-threading.
- **Automated OIDC Authentication**: Integrated `CDSEAuthManager` handling Keycloak token negotiation, 9-minute thread-safe token caching, and automated token refresh using `CDSE_USERNAME` / `CDSE_PASSWORD` (or `SENTINEL_USER` / `SENTINEL_PASS`).
- **Zero-Config Priority Retained**: Free public Cloud-Optimized GeoTIFFs (COGs) via AWS Open Data STAC remain the default zero-config experience. CDSE is seamlessly engaged when specifying `--provider cdse`, `--format safe`, passing CDSE UUIDs, or requesting raw `.SAFE` product titles.

### 2. Selective Band Extraction via OData `/Nodes` Traversal
Say goodbye to downloading 1.1 GB `.SAFE.zip` archives just to access a single 10m band:
- **Virtual Product Tree Traversal**: Recursively navigates CDSE `/Nodes` OData hierarchy (`GRANULE/.../IMG_DATA/R10m/...`) to locate and stream individual band files (`.jp2`, `.tif`, `.nc`) directly without downloading the parent archive.
- **Band & Polarization Presets**:
  - **Sentinel-2**: `rgb` (B02, B03, B04), `ndvi` (B04, B08), `tci` (True Color Image), `vnir` (B02-B08A), `10m` (B02, B03, B04, B08), `20m` (B05, B06, B07, B8A, B11, B12), `swir` (B11, B12), and `all`.
  - **Sentinel-1**: `vh`, `vv`, `dual` (VV + VH), and `all`.
- **CLI & SDK Syntax**:
  ```bash
  # Download only RGB bands for a Sentinel-2 scene from CDSE
  omniearth download --category optical --id "<CDSE_UUID>" --provider cdse --bands rgb
  ```

### 3. Cryptographic Checksum Verification (`--verify-checksum`)
- **Space Agency Integrity Verification**: Automatically fetches official MD5 and SHA-256 hashes published in STAC/OData provider manifests.
- **Atomic Staging Verification**: Streams data into `.part` files, computes block-wise cryptographic digests, validates against expected hashes, and atomically renames to the target destination only upon verified match. Mismatched downloads raise `ValueError` and purge corrupted partial files.

### 4. GIS Footprint Export (`.geojson` / `.csv`)
- **Direct GeoJSON Export**: Export search results directly to RFC 7946 GeoJSON `FeatureCollection` files containing bounding polygons, cloud cover, acquisition dates, scene IDs, and direct download links.
- **Tabular CSV Export**: Export search results to tabular CSV formats compatible with pandas, QGIS, ArcGIS, and Excel.
- **CLI & SDK Integration**:
  ```bash
  # CLI export flag
  omniearth search --category optical --point 78.96 20.59 --export footprints.geojson
  ```
  ```python
  # Python SDK export methods
  results = client.search(category="optical", bbox=[78.0, 20.0, 78.5, 20.5])
  results.export_geojson("results.geojson")
  results.export_csv("results.csv")
  ```

### 5. Automated On-the-Fly GeoTIFF Compositing
- **Instant Optical Compositing**: Automatically blends downloaded single bands into calibrated multiband GeoTIFFs:
  - `rgb`: 3-band True Color composite (Red B04, Green B03, Blue B02).
  - `cir`: Color Infrared vegetation false color (NIR B08, Red B04, Green B03).
  - `ndvi`: Calibrated float32 Normalized Difference Vegetation Index raster (`(NIR - Red) / (NIR + Red)`).
- **Engine Architecture**: Fast native raster generation accelerated by `rasterio` when installed, with seamless fallback to pure `numpy` and standard spatial formats.
- **CLI & SDK Flag**: `--composite rgb` / `composite="rgb"`.

### 6. Unified Search-to-Download Pipeline & Fluent Chaining
Previously, searching and downloading required disconnected two-step commands. OmniEarth v1.4.0 unifies them into a single, cohesive workflow:
- **Fluent SDK Chaining (`SearchResults`)**:
  - `client.search(...)` now returns a specialized `SearchResults` collection (subclassing `list` in Python and `Array` in TypeScript).
  - Chain downloads immediately:
    ```python
    # Python
    results = client.search(category="optical", bbox=[78.0, 20.0, 78.5, 20.5], max_cloud_cover=10)
    downloaded_paths = results.download_all(outdir="./scenes")
    first_scene = results.first().download(asset_key="visual")
    selected_paths = results.download_indices([0, 2], outdir="./selected")
    ```
    ```typescript
    // TypeScript / Node.js
    const results = await client.search({ category: Category.OPTICAL, bbox: [78.0, 20.0, 78.5, 20.5] });
    const downloadedPaths = await results.downloadAll("visual", "./scenes");
    const topScene = results.first();
    ```
- **High-Level Helper**:
  - `client.search_and_download(...)` / `client.searchAndDownload(...)` executes search and concurrent download in one unified call.
- **CLI Search-to-Download Action Flags**:
  - `--download-all`: Downloads all matching search results concurrently.
  - `--download-top <N>`: Downloads top N matching results.
  - `--select <indices>`: Downloads specified scenes by 1-based index (e.g. `--select 1,3` or `--select 1-3`).
  - `-i, --interactive`: Launches an interactive selection prompt immediately following search output table display.
- **CLI Download Multi-Scene Dispatch**:
  - Comma-separated scene IDs: `omniearth download --category hyperspectral --id "ID1,ID2"`.
  - AOI multi-scene batching: `omniearth download --category optical --bbox ... --all-scenes --limit 5`.

### 7. Direct STAC Item Resolution (`get_item`) & Hyperspectral Fix
- **Direct Scene Resolution**: Added `get_item(category, item_id)` to `OmniEarth` and concrete provider classes (`OpticalProvider`, `SARProvider`, `HyperspectralProvider`, `ElevationProvider`, `LandcoverProvider`, `CDSEProvider`).
- **EnMAP & EMIT Direct Resolution**: Resolves exact STAC metadata and 13+ asset URLs directly from DLR EOC STAC (`ENMAP_HSI_L2A`) and NASA LP DAAC CMR STAC (`EMITL2ARFL_001`) in $< 200\text{ms}$ without requiring an AOI query.
- **Provider Auto-Detection**: Auto-detects provider backend (`dlr_enmap`, `nasa_lpdaac`, `cdse`) from scene ID prefixes, completely eliminating fallback `Unknown hyperspectral provider` exceptions.

### 8. Category-Wide Hardening Across All 14 Modalities
- **Optical & SAR**: Direct STAC item querying via AWS Earth Search `{"ids": [item_id]}` in O(1) time. Added empty asset guards preventing unhandled `StopIteration`.
- **Elevation & Land Cover**: Deterministic tile coordinate parsing in `get_item` for Copernicus DEM GLO-30, SRTM GL1, ALOS AW3D30, and ESA WorldCover (2020 v100 and 2021 v200).
- **SoilGrids**: Added asset existence guards preventing `AttributeError: 'NoneType' object has no attribute 'href'`.

### 9. Dual SDK Parity & Strict 100.00% Coverage Gate
- **Dual SDK Parity**: All new fluent methods, CDSE provider capabilities, export formats, and CLI flags exist identically across Python and TypeScript SDKs.
- **Strict Coverage Policy**: 100.00% test coverage maintained across Python codebase (`2,487/2,487` statements, `fail_under = 100`).
- **Test Suites**: 81 Python unit & integration tests and 22 TypeScript tests passing with zero failures.

---

# OmniEarth v1.3.2 Release Notes

**Release Date:** November 5, 2026  
**DOI:** [10.5281/zenodo.23689449](https://doi.org/10.5281/zenodo.23689449)  
**PyPI:** [omniearth 1.3.2](https://pypi.org/project/omniearth/)  
**npm:** [omniearth 1.3.2](https://www.npmjs.com/package/omniearth)  

OmniEarth v1.3.2 enforces pure OpenID Connect (OIDC) Trusted Publishing for PyPI via the official Python Packaging Authority (`pypa/gh-action-pypi-publish`) workflow, activating Sigstore PEP 740 Digital Attestations and verifiable build provenance. It also implements Grouped Version Updates in Dependabot to streamline dependency management into unified pull requests.

---

## What's New in v1.3.2

### 1. PyPA Official Action for PyPI PEP 740 Digital Attestations
- Upgraded `.github/workflows/publish.yml` to utilize `pypa/gh-action-pypi-publish@release/v1` with GitHub Environment `pypi`.
- Completely transitioned away from legacy static API tokens in favor of pure OIDC cryptographic exchange, guaranteeing verifiable build provenance ("Signed by GitHub Actions") on PyPI.

### 2. Grouped Dependabot Updates
- Configured `groups` in `.github/dependabot.yml` for `python-dependencies`, `node-dependencies`, and `actions-dependencies`.
- Reduced open pull requests limit to 1 per ecosystem, eliminating separate single-dependency PR clutter while maintaining continuous automated security scanning.

---

# OmniEarth v1.3.1 Release Notes

**Release Date:** November 5, 2026  
**DOI:** [10.5281/zenodo.23689449](https://doi.org/10.5281/zenodo.23689449)  
**PyPI:** [omniearth 1.3.1](https://pypi.org/project/omniearth/)  
**npm:** [omniearth 1.3.1](https://www.npmjs.com/package/omniearth)  

OmniEarth v1.3.1 is a dedicated **Security, Provenance & Supply-Chain Integrity** patch release. This release equips OmniEarth with cryptographically verifiable build provenance (PyPI PEP 740 & npm Sigstore), automated Static Application Security Testing (CodeQL SAST), continuous dependency vulnerability auditing (Dependabot), an official Vulnerability Disclosure Policy (`SECURITY.md`), and PEP 639 SPDX license metadata modernization.

---

## Key Security & Integrity Enhancements

### 1. Cryptographic Build Provenance (PEP 740 & Sigstore SLSA)
- **PyPI Trusted Publishing & PEP 740 Attestations**:
  - Upgraded publishing workflow (`.github/workflows/publish.yml`) to authenticate via GitHub Actions OpenID Connect (OIDC) identities.
  - Generates verifiable Sigstore digital attestations published directly to PyPI, resolving the *"No provenance found"* warning and establishing cryptographic proof of build origin.
- **npm Build Provenance (`--provenance`)**:
  - Published using `npm publish --provenance --access public` backed by `permissions: id-token: write`.
  - Publishes in-toto SLSA Level 2+ provenance records logged to the public Rekor transparency log, granting the verified publisher badge on npm.
- **GitHub Build Attestation Action**:
  - Integrated `actions/attest-build-provenance@v2` across all Python distribution artifacts (`.whl`, `.tar.gz`) and npm distribution tarballs (`.tgz`).

### 2. Automated Static Application Security Testing (CodeQL SAST)
- Integrated GitHub Advanced Security CodeQL workflow (`.github/workflows/codeql.yml`).
- Scans both Python and JavaScript/TypeScript codebases on every `push` to `main`, every `pull_request`, and on a weekly automated schedule.
- Actively guards against common CWEs, injection, and improper input handling.

### 3. Automated Dependency Vulnerability Monitoring (Dependabot)
- Added `.github/dependabot.yml` configured for weekly security scans across:
  - `pip` (monitoring `pyproject.toml` dependencies).
  - `npm` (monitoring `package.json` dependencies).
  - `github-actions` (keeping CI/CD action versions pinned and up-to-date).
- **Audit Verification**:
  - `pip-audit`: **0 known vulnerabilities found**.
  - `pnpm audit`: **0 known vulnerabilities found**.

### 4. Official Vulnerability Disclosure Policy & Threat Model (`SECURITY.md`)
- Created `SECURITY.md` in repository root and bundled it into npm and Python release packages:
  - Establishes private vulnerability disclosure channels via GitHub Private Vulnerability Reporting and direct security email (`lokesh.skshukla@gmail.com`).
  - Commits to a **24 to 48 hour SLA** for initial report response and triage.
  - Documents our privacy-first threat model: **zero telemetry**, zero usage tracking, and local-only execution with credentials strictly kept on client machines.

### 5. PEP 639 & SPDX License Modernization
- Converted license metadata in `pyproject.toml` to PEP 639 standard (`license = "LicenseRef-OmniEarth-Attribution-1.0"`, `license-files = ["LICENSE"]`).
- Converted `package.json` license string to `"LicenseRef-OmniEarth-Attribution-1.0"`.
- Eliminates setuptools build deprecation warnings and resolves Socket.dev "Ambiguous / Unrecognized License" flags.

### 6. Supply-Chain Rules Enforcement (`socket.yml`)
- Added `socket.yml` in repository root declaring strict supply-chain policies:
  - Enforces zero install scripts (`preinstall`/`postinstall`).
  - Flags unvetted network access during install phases.
  - Signals active security management to Socket.dev crawlers.

---

# OmniEarth v1.3.0 Release Notes

**Release Date:** November 4, 2026  
**DOI:** [10.5281/zenodo.23689449](https://doi.org/10.5281/zenodo.23689449)  
**PyPI:** [omniearth 1.3.0](https://pypi.org/project/omniearth/)  
**npm:** [omniearth 1.3.0](https://www.npmjs.com/package/omniearth)  

OmniEarth v1.3.0 is a feature and accuracy milestone introducing dual-level optical processing (Surface Reflectance vs Top-of-Atmosphere), universal chronological descending search ordering across all 14 data modalities, an expanded 9-index biophysical remote sensing calculation engine, pure Python/TypeScript zero-dependency polygon ray-casting containment, and a dedicated interactive documentation manual (`docs/guide.html`).

---

## 1. Key Additions & Architectural Enhancements

### 1. Dual Optical Processing Levels: Surface Reflectance (SR) vs Top-of-Atmosphere (TOA)
OmniEarth now provides explicit control over optical reflectance calibration via the `--level` CLI flag and `level` parameter in Python/Node.js SDKs:
- **Surface Reflectance (`level="sr"`, Default)**:
  - Maps to Sentinel-2 Level-2A (`sentinel-2-l2a`) via AWS Earth Search STAC.
  - Atmosphere scattering and aerosols corrected via ESA Sen2Cor.
  - Standard for terrestrial vegetation monitoring, agriculture, soil spectroscopy, and land cover classification.
- **Top-of-Atmosphere (`level="toa"`)**:
  - Maps to Sentinel-2 Level-1C (`sentinel-2-l1c`) via AWS Earth Search STAC.
  - Preserves **Band 10 (1375 nm Cirrus band)**, which is omitted in L2A products because water vapor completely attenuates ground signals.
  - Critical for:
    - High-altitude thin cirrus cloud detection and cloud masking algorithms.
    - Aquatic remote sensing, coastal bathymetry, and lake limnology (where standard atmospheric correction over-subtracts water leaving reflectance).
    - Foundation model GeoAI pre-training (e.g. NASA/IBM Prithvi, Clay, DOFA) where raw radiometry is required without sen2cor bias.
- **Convenience Shortcuts**:
  - Python: `client.get_optical(bbox=..., level="toa")` and `client.get_optical(bbox=..., level="sr")`
  - Node.js: `client.getOptical({ bbox, level: "toa" })`

### 2. Universal Chronological Descending Ordering Across All Modalities & Providers
- **STAC Query Sortby**: All upstream STAC queries (Element84 Earth Search for Sentinel-1/2, NASA CMR STAC for EMIT, NSIDC, PODAAC, LPCLOUD) now explicitly pass `"sortby": [{"field": "properties.datetime", "direction": "desc"}]`.
- **NASA CMR STAC Fix**: Resolved an issue where NASA CMR STAC defaulted to chronological ascending order, causing multi-provider searches to return oldest (2023) scenes first.
- **Unified Multi-Provider Descending Sort**: In multi-satellite modalities (such as Hyperspectral merging German DLR EnMAP and NASA EMIT), OmniEarth queries each archive, aggregates results, and enforces global chronological descending ordering (`reverse=True`).
- **Newest Acquisitions Always First**: All search outputs in CLI, Python SDK, Node.js SDK, and REST calls now guarantee that the freshest acquisitions rank at index 0.

### 3. Expanded 9-Index Biophysical & Spectral Calculation Engine
The remote sensing computation engine (`omniearth.indices` / `src/indices.ts`) has been expanded from simple NDVI to a comprehensive sensor-agnostic suite of 9 radiometric indices:
1. **NDVI** (Normalized Difference Vegetation Index): `(nir - red) / (nir + red)`
2. **NDWI** (Normalized Difference Water Index - McFeeters): `(green - nir) / (green + nir)`
3. **NDRE** (Normalized Difference Red Edge Index): `(nir - rededge) / (nir + rededge)` - Sensitive to high biomass chlorophyll and nitrogen status.
4. **EVI** (Enhanced Vegetation Index): `2.5 * (nir - red) / (nir + 6*red - 7.5*blue + 1)`
5. **NBR** (Normalized Burn Ratio): `(nir - swir) / (nir + swir)` - Wildfire severity and burn scar delineation.
6. **SAVI** (Soil-Adjusted Vegetation Index): `(1 + L) * (nir - red) / (nir + red + L)` with configurable soil adjustment factor `l_factor` (default `0.5`).
7. **MSAVI** (Modified Soil-Adjusted Vegetation Index): `0.5 * (2*nir + 1 - sqrt((2*nir + 1)^2 - 8*(nir - red)))`
8. **BSI** (Bare Soil Index): `((swir + red) - (nir + blue)) / ((swir + red) + (nir + blue))`
9. **MNDWI** (Modified NDWI - Xu): `(green - swir) / (green + swir)` - Open surface water enhancement in urban/built-up environments.

- **CLI Support**:
  `omniearth compute --index savi --nir 0.80 --red 0.20 --l-factor 0.5`
- **Re-exported SDK Helpers**:
  `calculate_ndvi()`, `calculate_ndwi()`, `calculate_ndre()`, `calculate_evi()`, `calculate_nbr()`, `calculate_savi()`, `calculate_msavi()`, `calculate_bsi()`, `calculate_mndwi()`.

### 4. Pure Python/TypeScript Ray-Casting Polygon Containment (`AOI.contains`)
- Retains original GeoJSON geometry when parsing AOIs via `AOI.from_geojson(...)`.
- Implements an optimized point-in-polygon ray-casting algorithm checking outer polygon boundaries and subtracting interior hole rings (e.g. water bodies or non-farm exclusions).
- **Zero C/C++ Dependencies**: Runs cleanly in pure Python and TypeScript without requiring GDAL, GEOS, or Shapely.
- Python: `aoi.contains(lon, lat)` -> `bool`
- TypeScript: `aoi.contains(lon, lat)` -> `boolean`

### 5. Strict Temporal Bounds for Single-Year Queries
- Passing `year=YYYY` or `--year YYYY` without explicit start and end dates now automatically binds queries to `YYYY-01-01T00:00:00Z` through `YYYY-12-31T23:59:59Z`, eliminating accidental leakage into older or newer data years.

### 6. Interactive Documentation Manual (`docs/guide.html`)
- Launched a complete interactive documentation portal and user manual with sticky sidebar navigation, search, and responsive layout.
- Novice geospatial concepts guide explaining Longitude/Latitude ordering, continuous polar vs on-demand tasked orbits, and physical differences between SR and TOA.
- Complete reference tables covering every parameter for `search`, `download`, `compute`, and `timeseries`.
- Worked code examples for all 14 modalities in CLI, Python, and TypeScript.

---

## 2. Test Suite & Coverage Verification
- **Python**: 63/63 tests passing with **100.00% statement coverage** (`1645 / 1645 statements`).
- **Node.js**: 18/18 tests passing; TypeScript (`tsc`) compiling with zero warnings and zero errors.
- Strict test gate enforced via `fail_under = 100` in `pyproject.toml`.

---

# OmniEarth v1.2.0 Release Notes

**Release Date:** October 31, 2026  
**DOI:** [10.5281/zenodo.23689449](https://doi.org/10.5281/zenodo.23689449)  
**PyPI:** [omniearth 1.2.0](https://pypi.org/project/omniearth/)  
**npm:** [omniearth 1.2.0](https://www.npmjs.com/package/omniearth)  

OmniEarth v1.2.0 is a milestone release expanding the engine from 7 to **14 universal Earth Observation and environmental data modalities**. This release broadens the platform from surface imaging and topography into atmospheric trace gases, active fire thermal hotspots, ocean color and biology, radar altimetry, high-resolution precipitation climatology, root-zone hydrology, and nocturnal human activity.

---

## 1. New Modalities & Capabilities

### 1. Atmospheric Composition & Air Quality (`Category.ATMOSPHERE`)
- **Sensors:** Copernicus Sentinel-5P TROPOMI & CAMS ECMWF.
- **Parameters:** Tropospheric NO2, CO, CH4 (methane), SO2, Ozone (O3), Aerosol Optical Depth (AOD), UV Index, PM2.5, PM10.
- **Backend:** Copernicus Data Space STAC / Open-Meteo Air Quality.
- **Auth:** Zero-Config public API / COGs.
- **Convenience Shortcut:** `client.get_atmosphere(...)` / `client.getAtmosphere(...)`.

### 2. Active Fire & Thermal Anomalies (`Category.FIRE`)
- **Sensors:** NASA FIRMS VIIRS (375m) and MODIS (1km).
- **Parameters:** Active fire hotspots, Fire Radiative Power (FRP in MW), brightness temperature, confidence levels, day/night flag.
- **Backend:** NASA FIRMS REST API.
- **Auth:** Zero-Config public API.
- **Convenience Shortcut:** `client.get_fire(...)` / `client.getFire(...)`.

### 3. Ocean Color, Marine Biology & SST (`Category.OCEAN`)
- **Sensors:** Copernicus Sentinel-3 OLCI (21 spectral bands) and SLSTR.
- **Parameters:** Chlorophyll-a concentration (mg/m3), Total Suspended Matter (TSM / turbidity), Sea Surface Temperature (SST).
- **Backend:** Copernicus Data Space STAC / EUMETSAT Data Store.
- **Auth:** Zero-Config public open data.
- **Convenience Shortcut:** `client.get_ocean(...)` / `client.getOcean(...)`.

### 4. Radar Altimetry & Water Surface Levels (`Category.ALTIMETRY`)
- **Sensors:** Copernicus Sentinel-6 Michael Freilich (Poseidon-4 SAR Altimeter) & Jason-3.
- **Parameters:** Significant Wave Height (SWH, meters), Sea Surface Height Anomaly (SSHA, meters), ocean wind speed, inland lake and reservoir surface heights.
- **Backend:** PO.DAAC CMR STAC / Copernicus Marine.
- **Auth:** Zero-Config public open data.
- **Convenience Shortcut:** `client.get_altimetry(...)` / `client.getAltimetry(...)`.

### 5. High-Resolution Precipitation Climatology (`Category.PRECIPITATION`)
- **Sensors / Programs:** NASA GPM IMERG (0.1 deg half-hourly/daily global calibrated precipitation) & CHIRPS v2.0 (0.05 deg daily rainfall 1981-present).
- **Parameters:** Daily rainfall accumulation (mm), half-hourly precipitation rate (mm/hr), historical climatological anomalies.
- **Backend:** NASA GES DISC CMR STAC / UCSB CHIRPS AWS Open Data S3.
- **Auth:** Zero-Config public open data.
- **Convenience Shortcut:** `client.get_precipitation(...)` / `client.getPrecipitation(...)`.

### 6. Hydrology & Root-Zone Soil Moisture (`Category.HYDROLOGY`)
- **Sensors:** NASA SMAP (L-band Radiometer 9km/3km) & Copernicus Global Land Service Soil Water Index.
- **Parameters:** Surface soil moisture (0-5cm), root-zone soil moisture (0-100cm), freeze/thaw status.
- **Backend:** NSIDC DAAC CMR STAC.
- **Auth:** Zero-Config public open data.
- **Convenience Shortcut:** `client.get_hydrology(...)` / `client.getHydrology(...)`.

### 7. Nighttime Lights & Nocturnal Radiance (`Category.NIGHTLIGHTS`)
- **Sensors:** Suomi-NPP / NOAA-20/21 VIIRS Day/Night Band (DNB 750m) & NASA Black Marble (VNP46A1/A2/A3).
- **Parameters:** Calibrated nocturnal radiance (nW/cm2/sr), stable lights, blackout anomalies.
- **Backend:** NASA LPCLOUD CMR STAC.
- **Auth:** Zero-Config public open data.
- **Convenience Shortcut:** `client.get_nightlights(...)` / `client.getNightlights(...)`.

---

## 2. Enriched Weather & Agronomic Analytics

The `weather` provider has been expanded with crucial agronomic and energy balance variables:
- `et0_fao_evapotranspiration`: Reference evapotranspiration according to FAO-56 Penman-Monteith (vital for irrigation management).
- `vapour_pressure_deficit` (VPD): Determines plant transpiration stress and stomatal conductance.
- `dew_point_2m`, `apparent_temperature`, `surface_pressure`.
- `wind_speed_10m`, `wind_direction_10m`, `wind_gusts_10m`.
- `shortwave_radiation_sum`, `uv_index`.

---

## 3. Complete Upstream Data Attribution & Compliance

OmniEarth is a decentralized aggregation engine. Every upstream provider is formally credited, and users are notified of individual data usage policies:
- **ESA / Copernicus**: Open access under the [EU Copernicus Legal Notice](https://sentinels.copernicus.eu/web/sentinel/terms-conditions) (Sentinel-1, 2, 3, 5P, 6, Copernicus DEM, ESA WorldCover).
- **NASA Earth Science**: Public domain and open access under [NASA Data and Information Policy](https://www.earthdata.nasa.gov/engage/open-data-services-and-software/data-and-information-policy) (Landsat 8/9, NASA EMIT, NASA FIRMS, NASA GPM IMERG, NASA SMAP, Suomi-NPP / NOAA VIIRS Nighttime Lights).
- **German Aerospace Center (DLR)**: Governed by the [DLR EnMAP Data Policy and User License](https://www.enmap.org/data/policy/).
- **Open-Meteo & ECMWF**: Open access under [CC BY 4.0](https://open-meteo.com/en/terms).
- **ISRIC SoilGrids**: Open access under [CC BY 4.0](https://www.isric.org/about/data-policy).
- **JAXA ALOS**: Open access under [JAXA Earth Observation Data Policy](https://earth.jaxa.jp/en/data/policy/).
- **UC Santa Barbara CHIRPS**: Open access under [Climate Hazards Center Data Policy](https://www.chc.ucsb.edu/data/chirps).

> **Disclaimer of Liability**: OmniEarth is an open-source tool. The authors and maintainers assume no liability and are **not responsible for any misuse**, unintended interpretation, or violation of third-party data licenses by end-users. Users must independently ensure compliance with each upstream provider's terms.

---

## 4. Test Suite and Coverage Verification

- **Python**: 60/60 unit and integration tests passing in 0.93s with **100.00% statement coverage** (`1512 / 1512 statements`).
- **Node.js**: 18/18 unit tests passing in 0.32s; clean TypeScript compilation (`tsc`) with zero errors.
- Cross-platform CI matrix verified across Ubuntu Linux, macOS, and Windows.
