# OmniEarth

[![CI/CD](https://github.com/lokeshsk/omniearth/actions/workflows/ci.yml/badge.svg)](https://github.com/lokeshsk/omniearth/actions)
[![PyPI version](https://img.shields.io/pypi/v/omniearth.svg?color=blue)](https://pypi.org/project/omniearth/)
[![npm version](https://img.shields.io/npm/v/omniearth.svg?color=green)](https://www.npmjs.com/package/omniearth)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23689449.svg)](https://doi.org/10.5281/zenodo.23689449)
[![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen.svg)](https://github.com/lokeshsk/omniearth)
[![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20macOS%20%7C%20Windows-blue.svg)](https://github.com/lokeshsk/omniearth)
[![Python uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![pnpm](https://img.shields.io/badge/maintained%20with-pnpm-cc00ff.svg)](https://pnpm.io/)
[![License](https://img.shields.io/badge/License-OmniEarth_Attribution_1.0-orange.svg)](LICENSE)

**OmniEarth** is an open-source, universal multi-modal Earth Observation (EO), hyperspectral cube, topography, and environmental data aggregation engine. It provides a unified **Python SDK**, **Node.js / TypeScript SDK**, and **Universal CLI** to discover, query, filter, and stream open earth observation data across all modalities:

- **Optical Multispectral**: Sentinel-2 (L2A 10m COGs), Landsat-8/9 (30m) via AWS Open Data STAC.
- **Hyperspectral Cubes**: DLR EnMAP (224 spectral bands), NASA EMIT (285 bands), and ASI PRISMA (240 bands).
- **Synthetic Aperture Radar (SAR)**: Sentinel-1 (GRD / RTC VV/VH 10m COGs).
- **Digital Elevation Models (DEM / DSM / DTM)**: Copernicus DEM GLO-30 (30m DSM), SRTM GL1 (30m), ALOS World 3D (AW3D30 30m).
- **Land Use / Land Cover (LULC)**: ESA WorldCover 10m (2020 v100 and 2021 v200 global maps).
- **Weather & Climate Profiles**: Open-Meteo zero-config global forecasts, hourly soil moisture (0-9cm), FAO-56 reference evapotranspiration (ET0), vapour pressure deficit (VPD), and ERA5 historical reanalysis.
- **Soil & 3D Profiles**: ISRIC SoilGrids v2.0 (250m global physical and chemical soil profiles across 0-200cm).
- **Atmospheric Composition & Air Quality**: Copernicus Sentinel-5P TROPOMI (NO2, CO, CH4, SO2, O3, Aerosol Index) and CAMS ECMWF.
- **Active Fire & Thermal Anomalies**: NASA FIRMS VIIRS (375m) and MODIS (1km) near-real-time active fire hotspots and Fire Radiative Power (FRP).
- **Ocean Color, Marine Biology & SST**: Copernicus Sentinel-3 OLCI (21 spectral bands chlorophyll-a and turbidity) and SLSTR sea surface temperature (SST).
- **Radar Altimetry & Water Surface Levels**: Copernicus Sentinel-6 Michael Freilich / Jason-3 Poseidon-4 SAR altimeter (Significant Wave Height, Sea Surface Height Anomaly, lake levels).
- **High-Resolution Precipitation**: NASA GPM IMERG (0.1 deg half-hourly/daily global calibrated precipitation) and CHIRPS v2.0 (0.05 deg daily rainfall 1981-present).
- **Hydrology & Root-Zone Soil Moisture**: NASA SMAP (L-band 9km/3km radiometer surface 0-5cm and root-zone 0-100cm soil water content).
- **Nighttime Lights & Nocturnal Radiance**: Suomi-NPP / NOAA-20 VIIRS Day/Night Band (DNB 750m) and NASA Black Marble (calibrated nocturnal radiance and stable lights).

---

## Table of Contents
1. [Supported Modalities and Provider Matrix](#supported-modalities-and-provider-matrix)
2. [Installation and Setup](#installation-and-setup)
3. [Sequential CLI User Guide](#sequential-cli-user-guide)
4. [Sequential Python SDK Guide](#sequential-python-sdk-guide)
5. [Sequential Node.js / TypeScript SDK Guide](#sequential-nodejs--typescript-sdk-guide)
6. [Direct Underlying REST and STAC API Calls (cURL)](#direct-underlying-rest-and-stac-api-calls-curl)
7. [High-Performance Engine Features](#high-performance-engine-features)
8. [Authentication and Environment Configuration](#authentication-and-environment-configuration)
9. [License and Mandatory Attribution](#license-and-mandatory-attribution)
10. [Citation](#citation)
11. [Author and Maintainer](#author-and-maintainer)

---

## Supported Modalities and Provider Matrix

| Modality | Sensor / Dataset | Spatial / Spectral | Backend Architecture | Authentication |
| :--- | :--- | :--- | :--- | :--- |
| **Optical** | Sentinel-2 L2A, Landsat-8/9 | 10m-30m, 12 bands | AWS Earth Search STAC | **Zero-Config** (Free public COGs) |
| **SAR** | Sentinel-1 GRD / RTC | 10m, VV / VH dual-pol | AWS Earth Search STAC | **Zero-Config** (Free public COGs) |
| **Elevation** | Copernicus DEM GLO-30, SRTM GL1, ALOS | 30m, DSM / DTM | AWS Open Data / OpenTopography S3 | **Zero-Config** (Free direct COGs) |
| **Land Cover** | ESA WorldCover 10m (2020, 2021) | 10m global classification | AWS Open Data S3 | **Zero-Config** (Free direct COGs) |
| **Hyperspectral** | DLR EnMAP | 30m, 224 bands (420-2450 nm) | DLR EOC STAC + Geoservice | Free DLR Account (Optional) |
| **Hyperspectral** | NASA EMIT | 60m, 285 bands (381-2493 nm) | NASA CMR STAC | Free Earthdata Login (Optional) |
| **Hyperspectral** | ASI PRISMA | 30m, 240 bands | ASI PRISMA Portal | Free ASI Account (Optional) |
| **Weather** | Open-Meteo, ERA5, FAO-56 ET0, VPD | Global 1-11km, hourly | Open-Meteo REST API | **Zero-Config** (Public open API) |
| **Soil & 3D** | ISRIC SoilGrids v2.0 | 250m 3D profiles (0-200cm) | ISRIC REST API | **Zero-Config** (Public open API) |
| **Atmosphere** | Sentinel-5P TROPOMI, CAMS | NO2, CO, CH4, SO2, O3, AOD | Copernicus STAC / Open-Meteo | **Zero-Config** (Public open API) |
| **Fire** | NASA FIRMS (VIIRS 375m, MODIS 1km) | 375m-1km active hotspots, FRP | NASA FIRMS REST API | **Zero-Config** (Public open API) |
| **Ocean** | Sentinel-3 OLCI (21 bands) & SLSTR | 300m-1km Chlorophyll, SST | Copernicus Data Space STAC | **Zero-Config** (Public open data) |
| **Altimetry** | Sentinel-6 Poseidon-4, Jason-3 | SWH (m), SSHA (m), lake heights | PO.DAAC CMR STAC / Copernicus | **Zero-Config** (Public open data) |
| **Precipitation** | NASA GPM IMERG, CHIRPS v2.0 | 0.05-0.1 deg daily/hourly rain | NASA GES DISC / UCSB S3 | **Zero-Config** (Public open data) |
| **Hydrology** | NASA SMAP (L-band), CGLS SWI | 9km/1km Root-zone soil moisture | NSIDC DAAC CMR STAC | **Zero-Config** (Public open data) |
| **Nightlights** | VIIRS Day/Night Band, Black Marble | 750m nocturnal radiance | NASA LPCLOUD CMR STAC | **Zero-Config** (Public open data) |

> **Note**: 12 of the 14 modalities require **zero credentials** and work out of the box with zero setup! Free accounts are optionally supported for direct raw hyperspectral mission downloads (DLR EnMAP and NASA EMIT).

---

## Installation and Setup

OmniEarth is maintained using modern package workflows: **Astral `uv`** for Python and **`pnpm`** for Node.js.

### Python Package & CLI
```bash
# Using Astral uv (recommended):
uv add omniearth
# or via uv pip:
uv pip install omniearth

# Using standard pip:
pip install omniearth
```

### Node.js / TypeScript Package & CLI
```bash
# Using pnpm (recommended):
pnpm add omniearth
# or install CLI globally:
pnpm add -g omniearth

# Using npm:
npm install omniearth
# or install CLI globally:
npm install -g omniearth
```

---

## Sequential CLI User Guide

OmniEarth provides an identical, cross-platform CLI in both Python and Node.js environments.

### Step 1: Healthcheck and System Diagnostics
Verify your environment, detected credentials, and cache directory:
```bash
omniearth info
```

### Step 2: Explore Supported Categories and Modalities
List all available sensor modalities, spectral resolutions, and backend STAC endpoints:
```bash
omniearth categories
```

### Step 3: Spatial Search using Bounding Box, Point, or GeoJSON
Search for scenes intersecting an area of interest (AOI):
```bash
# Search using bounding box: min_lon min_lat max_lon max_lat
omniearth search --category optical --bbox 78.50 20.65 78.60 20.72 --limit 3

# Search using point with radius: lon lat [radius_km]
omniearth search --category sar --point 78.55 20.68 5.0 --limit 3

# Search using GeoJSON boundary file
omniearth search --category elevation --geojson ./field_boundary.geojson

# Search 10m ESA WorldCover
omniearth search --category landcover --bbox 78.50 20.65 78.60 20.72 --year 2021
```

### Step 4: Apply Temporal and Cloud Cover Filters
Narrow your search to specific acquisition windows or cloud thresholds:
```bash
omniearth search --category optical \
  --bbox 78.50 20.65 78.60 20.72 \
  --start 2026-01-01 \
  --end 2026-03-31 \
  --max-cloud 15 \
  --limit 5
```

### Step 5: Output Raw JSON for Automation and Scripting
Pipe search results directly to `jq` or downstream pipelines:
```bash
omniearth search --category weather --point 78.55 20.68 --json | jq .
```

### Step 6: Single-Asset Resumable Download
Download a specific asset (e.g. `visual`, `red`, `dem`, `map`, `SPECTRAL_IMAGE_COG`, or `vv`):
```bash
omniearth download --category elevation \
  --bbox 78.50 20.65 78.60 20.72 \
  --dataset copernicus \
  --outdir ./downloads
```

### Step 7: High-Speed Multi-Threaded All-Asset Download
Download all assets associated with a scene concurrently using worker threads:
```bash
omniearth download --category optical \
  --id S2A_32TPT_20260315_0_L2A \
  --all \
  --threads 8 \
  --outdir ./downloads
```

### Step 8: Network Interruption Resumption
If a connection drops during a large download, re-run the same command. OmniEarth detects the `<file>.part` staging file, queries byte ranges via `HTTP 206 Partial Content`, and automatically resumes without restarting from byte 0.

### Step 9: On-the-Fly Radiometric Indices (NDVI, NDWI, NDRE, EVI, NBR)
Compute standard remote sensing vegetation, water, and burn ratio indices directly from CLI:
```bash
# Compute NDVI from scalar band reflectances
omniearth compute --index ndvi --nir 0.82 --red 0.18

# Compute EVI from band values
omniearth compute --index evi --nir 0.75 --red 0.15 --blue 0.08

# Compute from JSON array and save output
omniearth compute --index ndvi --nir "[0.8, 0.7, 0.85]" --red "[0.2, 0.15, 0.22]" --outpath ./ndvi_stats.json
```

### Step 10: Historical Time-Series Extraction
Extract chronological time-series profiles across satellite passes or hourly weather observations:
```bash
# Hourly meteorological time-series
omniearth timeseries --category weather --bbox 78.50 20.65 78.60 20.72 --limit 24

# Chronological satellite observation pass timeline
omniearth timeseries --category optical --bbox 78.50 20.65 78.60 20.72 --start 2026-01-01 --end 2026-03-31
```

---

## Sequential Python SDK Guide

The Python SDK exposes a clean, synchronous interface with full type hints, thread pools, and zero-config shortcuts.

### Step 1: Import and Initialize Client
```python
import omniearth as oe

# Default initialization (auto-detects .env and environment variables)
client = oe.OmniEarth()

# Optional: specify custom .env file path
# client = oe.OmniEarth(env_path="/path/to/custom.env")
```

### Step 2: Define Spatial Area of Interest (AOI)
```python
# Bounding box AOI: [min_lon, min_lat, max_lon, max_lat]
bbox = [78.50, 20.65, 78.60, 20.72]

# Point AOI: (lon, lat, radius_km)
point = (78.55, 20.68, 5.0)

# GeoJSON AOI: from file or GeoJSON dict
aoi = oe.AOI.from_geojson("./field_boundary.geojson")
```

### Step 3: Search Multi-Modal Catalog
```python
# 1. Optical (Sentinel-2 L2A 10m COGs)
optical_scenes = client.search(
    category="optical",
    bbox=bbox,
    start_date="2026-01-01",
    end_date="2026-03-31",
    max_cloud_cover=20,
    limit=3
)

# 2. Elevation DEM (Copernicus DEM GLO-30, SRTM, or ALOS)
elevation_tiles = client.search(
    category="elevation",
    bbox=bbox,
    dataset="copernicus"
)

# 3. Land Cover (ESA WorldCover 10m)
landcover_tiles = client.search(
    category="landcover",
    bbox=bbox,
    year=2021
)

# 4. Hyperspectral (DLR EnMAP 224 spectral bands)
hsi_scenes = client.search(
    category="hyperspectral",
    bbox=bbox,
    limit=2
)

# 5. SAR (Sentinel-1 GRD Radar passes)
sar_scenes = client.search(
    category="sar",
    point=point,
    limit=2
)
```

### Step 4: Inspect Search Results and STAC Assets
```python
for scene in optical_scenes:
    print(f"ID: {scene.id}")
    print(f"Acquired: {scene.datetime}")
    print(f"Cloud Cover: {scene.cloud_cover}%")
    print("Available Assets:")
    for key, asset in scene.assets.items():
        print(f"  - {key}: {asset.href} ({asset.media_type})")
```

### Step 5: Download Single Asset (Resumable and Parallel Multipart)
```python
# Downloads the visual RGB Cloud-Optimized GeoTIFF with automatic resumption
if optical_scenes:
    scene = optical_scenes[0]
    file_path = client.download(
        result=scene,
        asset_key="visual",
        outdir="./downloads",
        resume=True,       # Auto-resume partial .part downloads
        multipart=True,    # Parallel chunked ranges for files >= 10MB
        max_workers=4      # Parallel chunk threads
    )
    print(f"Downloaded to: {file_path}")
```

### Step 6: Concurrent Multi-Asset Download (download_all)
```python
# Concurrently download all assets (B02, B03, B04, B08, visual) for a scene:
downloaded_map = client.download_all(
    result=scene,
    outdir="./downloads",
    max_workers=4
)
for asset_key, path in downloaded_map.items():
    print(f"Asset '{asset_key}' saved to: {path}")
```

### Step 7: Bulk Downloading Across Multiple Scenes (download_many)
```python
# Concurrently download assets across an entire list of search results:
all_paths = client.download_many(
    results=optical_scenes,
    asset_key="visual",
    outdir="./downloads",
    max_workers=4
)
print(f"Successfully downloaded {len(all_paths)} scenes in parallel.")
```

### Step 8: Zero-Config Convenience Shortcuts
```python
# 1. Digital Elevation Model (Copernicus DEM 30m)
dem = client.get_elevation(bbox=bbox, dataset="copernicus")

# 2. ESA WorldCover 10m LULC map
lc = client.get_landcover(bbox=bbox, year=2021)

# 3. Instant Weather & Soil Moisture Profile
weather = client.get_weather(bbox=bbox)
print(f"Elevation: {weather.properties['elevation']}m")
print(f"Hourly Temp: {weather.properties['_raw_data']['hourly']['temperature_2m'][:5]}")

# 4. ISRIC SoilGrids 3D Soil Chemistry & Texture Profile
soil = client.get_soil(bbox=bbox, depth="0-5cm")
print("Topsoil Summary:", soil.properties["summary_topsoil"])
```

### Step 9: On-the-Fly Index Computation
```python
# Compute NDVI
ndvi = client.compute_index("ndvi", nir=0.82, red=0.18)
print("NDVI Mean:", ndvi["mean"])

# Compute NDRE (RedEdge)
ndre = client.compute_index("ndre", nir=0.78, rededge=0.35)

# Compute EVI
evi = client.compute_index("evi", nir=0.80, red=0.15, blue=0.08)
```

### Step 10: Time-Series Extraction
```python
# Historical hourly meteorological records
series = client.get_time_series(
    category="weather",
    bbox=bbox,
    start_date="2026-10-01",
    end_date="2026-10-10"
)
for record in series[:5]:
    print(record["datetime"], record.get("temperature_2m"))
```

---

## Sequential Node.js / TypeScript SDK Guide

The Node.js SDK provides a native ESM / TypeScript interface built on `fetch`, `ReadableStream`, and `node:fs`.

### Step 1: Import and Instantiate
```typescript
import { OmniEarth, Category } from "omniearth";

const client = new OmniEarth();
```

### Step 2: Search with Full Type Safety
```typescript
const results = await client.search({
  category: Category.OPTICAL,
  bbox: [78.50, 20.65, 78.60, 20.72],
  startDate: "2026-01-01",
  endDate: "2026-03-31",
  maxCloudCover: 15,
  limit: 5
});

for (const scene of results) {
  console.log(`Scene: ${scene.id} | Date: ${scene.datetime}`);
  console.log(`Assets: ${Object.keys(scene.assets).join(", ")}`);
}
```

### Step 3: Resumable and Parallel Multipart Download
```typescript
if (results.length > 0) {
  const filePath = await client.download(results[0], "visual", "./downloads", {
    resume: true,
    multipart: true,
    concurrency: 4
  });
  console.log(`Downloaded: ${filePath}`);
}
```

### Step 4: Concurrent Multi-Asset Download (downloadAll)
```typescript
// Download all assets for a given scene in concurrent batches:
const assetMap = await client.downloadAll(results[0], undefined, "./downloads", {
  concurrency: 4
});
console.log("Downloaded assets:", assetMap);
```

### Step 5: Bulk Downloads Across Scenes (downloadMany)
```typescript
const allPaths = await client.downloadMany(results, "visual", "./downloads", {
  concurrency: 4
});
console.log(`Batch downloaded ${allPaths.length} visual rasters.`);
```

### Step 6: Zero-Config Convenience Shortcuts
```typescript
// Elevation DEM
const dem = await client.getElevation([78.50, 20.65, 78.60, 20.72], "copernicus");

// Land Cover 10m
const lc = await client.getLandcover([78.50, 20.65, 78.60, 20.72], 2021);

// Weather Feed
const wx = await client.getWeather([78.50, 20.65, 78.60, 20.72]);
console.log("Weather elevation:", wx?.properties.elevation);

// SoilGrids 3D Profile
const soil = await client.getSoil([78.50, 20.65, 78.60, 20.72], "0-5cm");
console.log("Topsoil profile:", soil?.properties.summary_topsoil);
```

### Step 7: Index Computation & Time-Series
```typescript
// Radiometric Index calculation
const ndvi = client.computeIndex("ndvi", { nir: 0.82, red: 0.18 });
console.log("Computed NDVI:", ndvi);

// Time-series extraction
const timeSeries = await client.getTimeSeries({
  category: Category.WEATHER,
  bbox: [78.50, 20.65, 78.60, 20.72]
});
console.log("Time-steps extracted:", timeSeries.length);
```

---

## Direct Underlying REST and STAC API Calls (cURL)

OmniEarth orchestrates open standard STAC and REST APIs under the hood. You can query these exact backends directly using raw `curl` or any HTTP client:

### 1. Optical Multispectral (AWS Earth Search STAC)
Queries Sentinel-2 L2A Cloud-Optimized GeoTIFFs (zero-config, free public egress):
```bash
curl -s -X POST "https://earth-search.aws.element84.com/v1/search" \
  -H "Content-Type: application/json" \
  -d '{
    "collections": ["sentinel-2-l2a"],
    "bbox": [78.50, 20.65, 78.60, 20.72],
    "datetime": "2026-01-01T00:00:00Z/2026-03-31T23:59:59Z",
    "query": { "eo:cloud_cover": { "lte": 20 } },
    "limit": 3
  }' | jq '.features[] | {id: .id, visual: .assets.visual.href}'
```

### 2. Synthetic Aperture Radar (Sentinel-1 GRD STAC)
Queries Sentinel-1 dual-polarization (VV/VH) radar backscatter:
```bash
curl -s -X POST "https://earth-search.aws.element84.com/v1/search" \
  -H "Content-Type: application/json" \
  -d '{
    "collections": ["sentinel-1-grd"],
    "bbox": [78.50, 20.65, 78.60, 20.72],
    "limit": 2
  }' | jq '.features[] | {id: .id, vv: .assets.vv.href, vh: .assets.vh.href}'
```

### 3. Digital Elevation Model (Copernicus DEM 30m S3)
Direct zero-config COG download from AWS Open Data:
```bash
curl -s -I "https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_N20_00_E078_00_DEM/Copernicus_DSM_COG_10_N20_00_E078_00_DEM.tif"
```

### 4. Land Cover (ESA WorldCover 10m S3)
Direct zero-config 10m classification map COG download from AWS Open Data:
```bash
curl -s -I "https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_N18E075_Map.tif"
```

### 5. Weather & Climate Profile (Open-Meteo REST API)
Fetches hourly temperature, relative humidity, solar radiation, and soil moisture:
```bash
curl -s "https://api.open-meteo.com/v1/forecast?latitude=20.68&longitude=78.55&hourly=temperature_2m,relative_humidity_2m,soil_moisture_0_to_1cm,surface_solar_radiation" \
  | jq '{elevation: .elevation, current_temp: .hourly.temperature_2m[0]}'
```

### 6. Soil Chemistry & 3D Texture (ISRIC SoilGrids REST API)
Fetches clay, sand, silt, soil organic carbon (SOC), pH, and bulk density across standard depths:
```bash
curl -s "https://rest.isric.org/soilgrids/v2.0/properties/query?lon=78.55&lat=20.68&property=clay&property=sand&property=soc&property=phh2o&depth=0-5cm" \
  | jq '.properties.layers[] | {name: .name, mean_value: .depths[0].values.mean}'
```

### 7. Hyperspectral Data Cubes (DLR EOC STAC API)
Queries DLR EnMAP 224-band hyperspectral cubes:
```bash
curl -s "https://geoservice.dlr.de/eoc/ogc/stac/v1/search?collections=ENMAP_L2A&bbox=78.50,20.65,78.60,20.72&limit=2" \
  | jq '.features[] | {id: .id, datetime: .properties.datetime, assets: .assets | keys}'
```

---

## High-Performance Engine Features

### 1. Parallel Chunked Multipart Downloading
For files >= 10MB, OmniEarth probes the server with `HEAD`, determines range support (`Accept-Ranges: bytes`), pre-allocates the local file, and distributes byte intervals across worker threads. Chunk downloads are written via thread-safe seek-write operations, maximizing network saturation.

### 2. Resumable Downloads via .part Staging
Downloads stream to `<destination>.part`. If interrupted, OmniEarth queries the file size of the existing partial file and issues a `Range: bytes=<existing_size>-` request. Upon receiving `HTTP 206 Partial Content`, it appends remaining bytes. If the server returns `HTTP 416 Range Not Satisfiable` (e.g. file changed upstream), OmniEarth automatically restarts cleanly from byte 0.

### 3. Multi-Platform Homogeneity
- **Windows File Locking Protection**: Implements a shared handle with synchronized locking, preventing Windows `PermissionError` during concurrent multi-threaded writes.
- **Line Ending Homogeneity**: Enforces LF line endings via `.gitattributes` to prevent checkout corruptions on Windows systems.

---

## Authentication and Environment Configuration

OmniEarth automatically discovers credentials from local `.env` files, parent directories, or system environment variables:

```bash
cp .env.example .env
```

```env
# DLR Geoservice (Required for downloading raw EnMAP 224-band hyperspectral cubes)
# Register free: https://eoweb.dlr.de/egp/
DLR_USERNAME=your_dlr_username
DLR_PASSWORD=your_dlr_password

# NASA Earthdata (Optional: for direct NASA EMIT cube downloads)
# Register free: https://urs.earthdata.nasa.gov/
EARTHDATA_USERNAME=your_earthdata_username
EARTHDATA_PASSWORD=your_earthdata_password

# ASI PRISMA (Optional: for PRISMA hyperspectral missions)
# Register free: https://prisma.asi.it/
PRISMA_USERNAME=your_prisma_username
PRISMA_PASSWORD=your_prisma_password
```

*(Optical Sentinel-2, Sentinel-1 SAR, Copernicus DEM, ESA WorldCover, Open-Meteo Weather, and ISRIC SoilGrids require zero credentials!)*

---

## License and Mandatory Attribution

OmniEarth is distributed under the **OmniEarth Open Source License with Mandatory Attribution & Academic Citation**. See [LICENSE](LICENSE) for the full legal text.

1. **Academic Citation**: Any research, preprint, paper, or published benchmark utilizing OmniEarth must cite the software using Zenodo DOI or the citation below.
2. **Corporate & Commercial Attribution**: Any commercial SaaS platform, internal corporate dashboard, website, or data pipeline utilizing OmniEarth must display prominent attribution:  
   *`"Powered by OmniEarth (https://github.com/lokeshsk/omniearth)"`* in user interfaces and technical documentation.
3. **Upstream Data Provider Liability and Usage Policies**: OmniEarth is an orchestration and aggregation tool. It does not own, host, or re-license upstream satellite imagery, trace gas models, altimetry data, or meteorological feeds. All users and organizations are strictly and solely responsible for reviewing and complying with each provider's individual license:
   - **ESA / Copernicus Sentinel Data**: Open access under the [EU Copernicus Legal Notice](https://sentinels.copernicus.eu/web/sentinel/terms-conditions) (Sentinel-1, Sentinel-2, Sentinel-3, Sentinel-5P, Sentinel-6, Copernicus DEM, ESA WorldCover).
   - **NASA Open Data Policy**: Public domain and open access under [NASA Data and Information Policy](https://www.earthdata.nasa.gov/engage/open-data-services-and-software/data-and-information-policy) (Landsat 8/9, NASA EMIT Hyperspectral, NASA FIRMS Active Fire, NASA GPM IMERG Precipitation, NASA SMAP Hydrology, Suomi-NPP / NOAA VIIRS Nighttime Lights).
   - **German Aerospace Center (DLR)**: Governed by the [DLR EnMAP Data Policy and User License](https://www.enmap.org/data/policy/).
   - **Italian Space Agency (ASI)**: Governed by the [ASI PRISMA Policy on Data Access and Utilization](https://prisma.asi.it/).
   - **Open-Meteo & ECMWF**: Open access under [CC BY 4.0](https://open-meteo.com/en/terms).
   - **ISRIC SoilGrids**: Open access under [CC BY 4.0](https://www.isric.org/about/data-policy).
   - **JAXA ALOS**: Open access under [JAXA Earth Observation Data Policy](https://earth.jaxa.jp/en/data/policy/).
   - **UC Santa Barbara CHIRPS**: Open access under [Climate Hazards Center Data Policy](https://www.chc.ucsb.edu/data/chirps).

> **Disclaimer of Liability**: OmniEarth is a decentralized data orchestration engine. The authors and maintainers of OmniEarth assume no liability and are **NOT responsible for any misuse**, unintended interpretation, commercial compliance failure, or breach of individual upstream data provider licenses committed by users of this library. Users must independently ensure their data access patterns comply with each sovereign provider's operational terms.

---

## Citation

If you use OmniEarth in your research or project, please cite:

```bibtex
@software{omniearth2026,
  author       = {Lokesh Kumar},
  title        = {OmniEarth: Universal Multi-Modal Open Earth Observation, Hyperspectral, and Weather Data Engine},
  month        = oct,
  year         = 2026,
  publisher    = {Zenodo},
  doi          = {10.5281/zenodo.23689449},
  url          = {https://github.com/lokeshsk/omniearth}
}
```

---

## Author and Maintainer

**Lokesh Kumar**  
- Email: [lokesh.skshukla@gmail.com](mailto:lokesh.skshukla@gmail.com)  
- Website: [https://lokeshsk.github.io](https://lokeshsk.github.io)  
- Project Documentation: [https://lokeshsk.github.io/omniearth/](https://lokeshsk.github.io/omniearth/)  

