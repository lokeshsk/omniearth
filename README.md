# OmniEarth 🌍

[![CI/CD](https://github.com/lokeshsk/omniearth/actions/workflows/ci.yml/badge.svg)](https://github.com/lokeshsk/omniearth/actions)
[![PyPI version](https://img.shields.io/pypi/v/omniearth.svg?color=blue)](https://pypi.org/project/omniearth/)
[![npm version](https://img.shields.io/npm/v/omniearth.svg?color=green)](https://www.npmjs.com/package/omniearth)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23689449.svg)](https://doi.org/10.5281/zenodo.23689449)
[![Python uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![pnpm](https://img.shields.io/badge/maintained%20with-pnpm-cc00ff.svg)](https://pnpm.io/)
[![License](https://img.shields.io/badge/License-OmniEarth_Attribution_1.0-orange.svg)](LICENSE)

**OmniEarth** is an open-source, universal multi-modal Earth Observation (EO), hyperspectral cube, and environmental data aggregation engine. It provides a unified **Python SDK**, **Node.js / TypeScript SDK**, and **Universal CLI** to discover, query, filter, and stream open earth observation data across all modalities:

- **Optical Multispectral**: Sentinel-2 (L2A 10m COGs), Landsat-8/9 (30m) via AWS Open Data STAC.
- **Hyperspectral Cubes**: DLR EnMAP (224 spectral bands), NASA EMIT (285 bands), and ASI PRISMA (240 bands).
- **Synthetic Aperture Radar (SAR)**: Sentinel-1 (GRD / RTC VV/VH 10m COGs).
- **Weather & Climate Profiles**: Open-Meteo zero-config global forecasts, hourly soil moisture (0-9cm), and ERA5 historical reanalysis.
- **Soil & 3D Topography**: ISRIC SoilGrids v2.0 (250m global physical & chemical soil profiles) and Copernicus DEM GLO-30.

---

## ⚡ Installation

OmniEarth is managed with modern, high-performance tooling: **Astral `uv`** for Python and **`pnpm`** for Node.js.

### Python SDK & CLI

Using [Astral uv](https://github.com/astral-sh/uv) (recommended):
```bash
uv pip install omniearth
# or add to your uv project:
uv add omniearth
```

Using standard `pip`:
```bash
pip install omniearth
```

### Node.js / TypeScript SDK & CLI

Using [pnpm](https://pnpm.io/) (recommended):
```bash
pnpm add omniearth
# or global CLI
pnpm add -g omniearth
```

Using `npm`:
```bash
npm install omniearth
# or global CLI
npm install -g omniearth
```

---

## Quickstart

### 1. Python SDK

```python
import omniearth as oe

client = oe.OmniEarth()

# 1. Search Hyperspectral Data Cubes (e.g. DLR EnMAP 224 bands)
scenes = client.search(
    category="hyperspectral",
    bbox=[78.50, 20.65, 78.60, 20.72],
    max_cloud_cover=20,
    limit=5
)

for scene in scenes:
    print(f"Scene: {scene.id} | Datetime: {scene.datetime} | Provider: {scene.provider}")

# Download full 224-band Cloud-Optimized GeoTIFF (COG)
if scenes:
    file_path = client.download(scenes[0], asset_key="SPECTRAL_IMAGE_COG", outdir="./downloads")
    print(f"Downloaded cube to: {file_path}")

# 2. Instant Weather & Soil Moisture Profile (Zero-Config)
weather = client.get_weather(bbox=[78.50, 20.65, 78.60, 20.72])
print(f"Elevation: {weather.properties['elevation']}m")

# 3. ISRIC SoilGrids 3D Physical/Chemical Profile
soil = client.get_soil(bbox=[78.50, 20.65, 78.60, 20.72], depth="0-5cm")
print("Topsoil Summary:", soil.properties["summary_topsoil"])
```

### 2. Node.js / TypeScript SDK

```typescript
import { OmniEarth, Category } from "omniearth";

const client = new OmniEarth();

// 1. Search Sentinel-2 Cloud-Optimized GeoTIFFs (10m Optical)
const scenes = await client.search({
  category: Category.OPTICAL,
  bbox: [78.50, 20.65, 78.60, 20.72],
  maxCloudCover: 15,
  limit: 3
});

for (const s of scenes) {
  console.log(`Found: ${s.id} | Date: ${s.datetime} | Assets: ${Object.keys(s.assets).join(", ")}`);
}

// 2. Download Visual RGB GeoTIFF
if (scenes.length > 0) {
  const filePath = await client.download(scenes[0], "visual", "./downloads");
  console.log(`Saved RGB COG: ${filePath}`);
}

// 3. Instant Weather Profile
const weather = await client.getWeather([78.50, 20.65, 78.60, 20.72]);
console.log("Weather Feed:", weather?.properties.latitude, weather?.properties.elevation);
```

---

## Universal CLI

OmniEarth provides a standalone command-line interface available in both Python and Node.js environments.

```bash
# Check provider status and detected credentials
omniearth info

# List all supported modalities, sensors, and backends
omniearth categories

# Search Optical Sentinel-2 scenes with max 10% cloud cover
omniearth search --category optical --bbox 78.50 20.65 78.60 20.72 --max-cloud 10

# Search DLR EnMAP Hyperspectral 224-band scenes
omniearth search --category hyperspectral --bbox 78.50 20.65 78.60 20.72 --limit 3

# Search Sentinel-1 SAR GRD radar passes
omniearth search --category sar --point 78.55 20.68 5.0

# Fetch zero-config weather and soil moisture profile
omniearth search --category weather --point 78.55 20.68 --json

# Direct download by Scene ID or latest AOI match
omniearth download --category hyperspectral --bbox 78.50 20.65 78.60 20.72 --asset SPECTRAL_IMAGE_COG
```

---

## Supported Modalities & Provider Matrix

| Modality | Sensors / Datasets | Resolution / Bands | Provider Backend | Authentication |
| :--- | :--- | :--- | :--- | :--- |
| **Optical** | Sentinel-2 L2A, Landsat-8/9 | 10m–30m, 12 bands | AWS Earth Search STAC | **Zero-Config** (Free public COGs) |
| **SAR** | Sentinel-1 GRD / RTC | 10m, VV / VH dual-pol | AWS Earth Search STAC | **Zero-Config** (Free public COGs) |
| **Hyperspectral** | DLR EnMAP | 30m, 224 bands (420–2450 nm) | DLR EOC STAC + Geoservice | Free DLR EOC Account |
| **Hyperspectral** | NASA EMIT | 60m, 285 bands (381–2493 nm) | NASA CMR STAC | Free NASA Earthdata Login |
| **Hyperspectral** | ASI PRISMA | 30m, 240 bands | ASI PRISMA Portal | Free ASI Account |
| **Weather** | Open-Meteo, ERA5 Reanalysis | Global 1–11km, hourly | Open-Meteo REST API | **Zero-Config** (Completely open) |
| **Soil & 3D** | ISRIC SoilGrids v2.0 | 250m 3D profiles (0–200cm) | ISRIC REST API | **Zero-Config** (Completely open) |

---

## Authentication & Configuration

OmniEarth automatically discovers credentials from local `.env` files, parent folders, or system environment variables:

Copy the `.env.example` template:
```bash
cp .env.example .env
```

```env
# DLR Geoservice (Required for downloading raw EnMAP hyperspectral cubes)
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

*(Note: Optical Sentinel-2, Landsat-8/9, Sentinel-1 SAR, Open-Meteo Weather, and ISRIC SoilGrids require **zero credentials** and work out of the box!)*

---

## License & Compliance Disclaimers

### License
OmniEarth is distributed under the **OmniEarth Open Source License with Mandatory Attribution & Academic Citation**. See [LICENSE](LICENSE) for the full text.

1. **Academic Citation**: Any research, paper, or published study utilizing OmniEarth must cite the software using Zenodo DOI or the citation below.
2. **Corporate Attribution**: Any commercial product, website, SaaS application, or internal service utilizing OmniEarth must display prominent attribution:  
   *`"Powered by OmniEarth (https://github.com/lokeshsk/omniearth)"`* in user interfaces and technical documentation.
3. **Upstream Data Provider Liability**: OmniEarth is an orchestration and aggregation tool. It does not own, re-license, or host upstream satellite imagery or sensor data. Users are strictly responsible for complying with the respective upstream terms of service:
   - **Copernicus Sentinel Data**: Free, full, and open access under the [EU Copernicus Legal Notice](https://sentinels.copernicus.eu/web/sentinel/terms-conditions).
   - **DLR EnMAP Data**: Governed by the [DLR EnMAP Data Policy](https://www.enmap.org/data/policy/).
   - **NASA EMIT / USGS Landsat**: Open public domain under [NASA Data and Information Policy](https://www.earthdata.nasa.gov/engage/open-data-services-and-software/data-and-information-policy).
   - **Open-Meteo**: Non-commercial open access under [CC BY 4.0](https://open-meteo.com/en/terms).
   - **ISRIC SoilGrids**: Open access under [CC BY 4.0](https://www.isric.org/about/data-policy).

---

## Citation

If you use OmniEarth in your scientific research or software, please cite:

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

## Author & Maintainer

**Lokesh Kumar**  
- Email: [lokesh.skshukla@gmail.com](mailto:lokesh.skshukla@gmail.com)  
- Website: [https://lokeshsk.github.io](https://lokeshsk.github.io)  
- Project Page: [https://lokeshsk.github.io/omniearth/](https://lokeshsk.github.io/omniearth/)  
