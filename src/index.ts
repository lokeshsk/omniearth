/**
 * OmniEarth Node.js & TypeScript SDK
 * ==================================
 * Universal Multi-Modal Open Earth Observation, Hyperspectral, and Weather Data Engine.
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

