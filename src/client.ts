import {
  Category,
  AOI,
  SearchResult,
  SearchParams,
  FilterOptions
} from "./types.js";
import { config } from "./config.js";
import { BaseProvider } from "./providers/base.js";
import { OpticalProvider } from "./providers/optical.js";
import { HyperspectralProvider } from "./providers/hyperspectral.js";
import { SARProvider } from "./providers/sar.js";
import { WeatherProvider } from "./providers/weather.js";
import { SoilProvider } from "./providers/soil.js";

export class OmniEarth {
  private providers: Map<Category, BaseProvider> = new Map();

  constructor(envPath?: string) {
    if (envPath) {
      config.loadEnvironment(envPath);
    }

    this.providers.set(Category.OPTICAL, new OpticalProvider());
    this.providers.set(Category.HYPERSPECTRAL, new HyperspectralProvider());
    this.providers.set(Category.SAR, new SARProvider());
    this.providers.set(Category.WEATHER, new WeatherProvider());
    this.providers.set(Category.SOIL, new SoilProvider());
  }

  public listCategories(): string[] {
    return Object.values(Category);
  }

  private resolveAOI(params: SearchParams): AOI {
    if (params.aoi) {
      return params.aoi;
    }
    if (params.bbox) {
      const [min_lon, min_lat, max_lon, max_lat] = params.bbox;
      if (min_lon > max_lon || min_lat > max_lat) {
        throw new Error(`Invalid bbox bounds: [${params.bbox.join(", ")}]`);
      }
      return { bbox: params.bbox };
    }
    if (params.point) {
      const [lon, lat, radius = 5.0] = params.point;
      const degLat = radius / 111.0;
      const degLon = radius / (111.0 * Math.max(0.1, Math.abs(1.0 - lat / 90.0)));
      return {
        bbox: [
          Number((lon - degLon).toFixed(5)),
          Number((lat - degLat).toFixed(5)),
          Number((lon + degLon).toFixed(5)),
          Number((lat + degLat).toFixed(5))
        ]
      };
    }
    throw new Error("Must specify 'bbox' ([min_lon, min_lat, max_lon, max_lat]) or 'point' ([lon, lat, radius_km?])");
  }

  public async search(params: SearchParams): Promise<SearchResult[]> {
    const cat = typeof params.category === "string" ? (params.category as Category) : params.category;
    const provider = this.providers.get(cat);
    if (!provider) {
      throw new Error(`Unsupported category '${cat}'. Supported: ${this.listCategories().join(", ")}`);
    }

    const aoi = this.resolveAOI(params);
    const filters: FilterOptions = {
      maxCloudCover: params.maxCloudCover,
      bands: params.bands,
      variables: params.variables,
      depth: params.depth,
      limit: params.limit
    };

    return provider.search(aoi, params.startDate, params.endDate, filters);
  }

  public async download(
    result: SearchResult,
    assetKey?: string,
    outdir?: string
  ): Promise<string> {
    const provider = this.providers.get(result.category);
    if (!provider) {
      throw new Error(`No provider adapter found for category '${result.category}'`);
    }
    return provider.download(result, assetKey, outdir);
  }

  public async getWeather(
    bbox: [number, number, number, number],
    startDate?: string,
    endDate?: string,
    variables?: string[]
  ): Promise<SearchResult | null> {
    const results = await this.search({
      category: Category.WEATHER,
      bbox,
      startDate,
      endDate,
      variables
    });
    return results[0] || null;
  }

  public async getSoil(
    bbox: [number, number, number, number],
    depth: string = "0-5cm",
    variables?: string[]
  ): Promise<SearchResult | null> {
    const results = await this.search({
      category: Category.SOIL,
      bbox,
      depth,
      variables
    });
    return results[0] || null;
  }
}
