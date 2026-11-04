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
- **Unified Multi-Provider Descending Sort**: In multi-satellite modalities (such as Hyperspectral merging German DLR EnMAP, NASA EMIT, and Italian ASI PRISMA), OmniEarth queries each archive, aggregates results, and enforces global chronological descending ordering (`reverse=True`).
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
- **Italian Space Agency (ASI)**: Governed by the [ASI PRISMA Policy on Data Access and Utilization](https://prisma.asi.it/).
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
