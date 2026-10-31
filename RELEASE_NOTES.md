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
