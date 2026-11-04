/**
 * OmniEarth Node.js & TypeScript SDK
 * ==================================
 * Universal Multi-Modal Open Earth Observation, Hyperspectral, Weather, DEM, and Land Cover Data Engine.
 *
 * Author: Lokesh Kumar (https://lokeshsk.github.io)
 * Repository: https://github.com/lokeshsk/omniearth
 */

export { OmniEarth } from "./client.js";
export {
  Category,
  AOI,
  Asset,
  SearchResult,
  FilterOptions,
  SearchParams
} from "./types.js";
export { config, Config } from "./config.js";
export { BaseProvider } from "./providers/base.js";
export { OpticalProvider } from "./providers/optical.js";
export { HyperspectralProvider } from "./providers/hyperspectral.js";
export { SARProvider } from "./providers/sar.js";
export { WeatherProvider } from "./providers/weather.js";
export { SoilProvider } from "./providers/soil.js";
export { ElevationProvider } from "./providers/elevation.js";
export { LandcoverProvider } from "./providers/landcover.js";
export { AtmosphereProvider } from "./providers/atmosphere.js";
export { FireProvider } from "./providers/fire.js";
export { OceanProvider } from "./providers/ocean.js";
export { AltimetryProvider } from "./providers/altimetry.js";
export { PrecipitationProvider } from "./providers/precipitation.js";
export { HydrologyProvider } from "./providers/hydrology.js";
export { NightlightsProvider } from "./providers/nightlights.js";
export { computeSpectralIndex, SUPPORTED_INDICES, IndexInputs, IndexStats } from "./indices.js";
