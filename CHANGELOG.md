# Changelog

All notable changes to **OmniEarth** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

## [1.5.3] - 2026-11-23

### Fixed
- **DLR EnMAP Hyperspectral OGC STAC Route**:
  - Upgraded DLR STAC URL to official `/v1/` route (`https://geoservice.dlr.de/eoc/ogc/stac/v1/collections/ENMAP_HSI_L2A/items`), resolving HTTP 502 Bad Gateway responses and restoring full hyperspectral scene discovery across Python and TypeScript SDKs and CLI.

---

## [1.5.2] - 2026-11-20

### Added
- **Non-Blocking Version & Update Notification Engine**:
  - Automatic background checks against PyPI and npm registries cached for 24 hours (`~/.cache/omniearth/version_check.json` and `npm_version_check.json`).
  - Terminal stderr notification banner alerting active users when a newer release is published, without breaking CLI pipelines or piped JSON output.
  - New `omniearth whatsnew` CLI command and `whats_new()` SDK function displaying formatted release notes, highlights, and changelog URLs.
  - Opt-out support via `OMNIEARTH_NO_UPDATE_CHECK=1` or `CI=true`.
- **Automated GitHub Release & Provenance Pipeline**:
  - `publish.yml` automatically creates structured GitHub Releases with release notes generated from pull requests and commits upon tag push.

### Changed
- Hyperspectral provider routing focused on NASA EMIT (285 bands) and DLR EnMAP (224 bands); decoupled PRISMA until external automated download protocol is validated.

---

## [1.5.1] - 2026-11-20

### Added
- **Direct Hyperspectral Provider & Dataset Routing**:
  - Direct selection of NASA EMIT (`--provider emit` / `--dataset emit`) and DLR EnMAP (`--provider enmap` / `--dataset enmap`).
- **Interchangeable Elevation Flags**:
  - Full interchangeable support for `--provider` and `--dataset` flags across Copernicus DEM (`copernicus`), NASA SRTM (`srtm`), and JAXA ALOS (`alos`).
- **Synchronized TypeScript / Node.js SDK**:
  - Full feature parity for EMIT, EnMAP, and DEM routing in `src/client.ts` and `src/cli.ts`.

### Fixed
- Elevation parameter resolution bug when passing `--provider copernicus` with spatial bounding boxes.

---

## [1.5.0] - 2026-11-20

### Added
- **Universal Semantic Asset Aliasing (`resolve_asset_key` / `resolveAssetKey`)**:
  - Normalizes asset selection across all 14 modalities (e.g. `cube`, `rfl`, `visual`, `rgb`, `dem`, `map`, `sar`, `no2`).
- **Interactive Terminal Asset Picker (`-i` / `--interactive`)**:
  - Displays asset keys, MIME types, and file sizes, prompting the user for selection.
- **Dedicated Scene Folder Packaging (`--folder` / `folder=True`)**:
  - Automatically isolates downloaded assets into `<outdir>/<scene_id>/`.
- **Direct ZIP Archive Packaging (`--zip` / `zip=True`)**:
  - Compresses scene assets directly into a portable `.zip` archive.
- **Parallel Asset URL Deduplication**:
  - Prevents redundant downloads when STAC catalogs map multiple aliases to identical URLs.

---

## [1.4.0] - 2026-11-19

### Added
- **Multi-Modal Timeseries Engine (`timeseries` / `extract_timeseries`)**:
  - Chronological observation extraction across optical, weather, and soil categories.
- **SoilGrids v2.0 Deep Profiling**:
  - 3D physical and chemical soil properties across standard depths (0-200cm).
- **Open-Meteo & ERA5 Reanalysis Integration**:
  - Hourly meteorological observations, FAO-56 reference evapotranspiration, and vapor pressure deficit.

---

## [1.3.0] - 2026-11-15

### Added
- **Hyperspectral Data Cube Streaming**:
  - Support for NASA EMIT L2A (285 bands) and DLR EnMAP L2A (224 bands).
- **Automated Spectral Index Computation (`compute`)**:
  - Native vectorized computation of NDVI, NDWI, NDRE, EVI, NBR, SAVI, MSAVI, BSI, and MNDWI.

---

## [1.2.0] - 2026-11-02

### Added
- **SAR & Elevation Modalities**:
  - Sentinel-1 GRD / RTC dual-polarization (VV/VH 10m) cloud-optimized GeoTIFFs.
  - Copernicus DEM GLO-30, SRTM GL1, and ALOS World 3D (AW3D30).
- **ESA WorldCover 10m Global Maps**:
  - 2020 v100 and 2021 v200 land use / land cover classification rasters.

---

## [1.1.0] - 2026-10-27

### Added
- **Parallel Multipart Chunked Downloader**:
  - Byte-range resumption and concurrent chunk assembly for high-throughput egress.
- **Cryptographic Hash Verification (`--verify-checksum`)**:
  - Automated MD5 and SHA-256 validation against STAC catalog assets.

---

## [1.0.0] - 2026-10-25

### Added
- Initial public release of OmniEarth:
  - Universal Python SDK, TypeScript SDK, and CLI.
  - Optical multispectral imagery (Sentinel-2 L2A/L1C and Landsat-8/9) via AWS Earth Search STAC.
  - Zero-config public cloud-optimized GeoTIFF streaming.

[Unreleased]: https://github.com/lokeshsk/omniearth/compare/v1.5.3...HEAD
[1.5.3]: https://github.com/lokeshsk/omniearth/compare/v1.5.2...v1.5.3
[1.5.2]: https://github.com/lokeshsk/omniearth/compare/v1.5.1...v1.5.2
[1.5.1]: https://github.com/lokeshsk/omniearth/compare/v1.5.0...v1.5.1
[1.5.0]: https://github.com/lokeshsk/omniearth/compare/v1.4.0...v1.5.0
[1.4.0]: https://github.com/lokeshsk/omniearth/compare/v1.3.0...v1.4.0
[1.3.0]: https://github.com/lokeshsk/omniearth/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/lokeshsk/omniearth/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/lokeshsk/omniearth/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/lokeshsk/omniearth/releases/tag/v1.0.0
