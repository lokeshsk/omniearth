import * as fs from "fs";
import {
  Category,
  AOI,
  SearchResult,
  SearchParams,
  FilterOptions
} from "./types.js";
import { config } from "./config.js";
import { BaseProvider, DownloadOptions } from "./providers/base.js";
import { OpticalProvider } from "./providers/optical.js";
import { HyperspectralProvider } from "./providers/hyperspectral.js";
import { SARProvider } from "./providers/sar.js";
import { WeatherProvider } from "./providers/weather.js";
import { SoilProvider } from "./providers/soil.js";
import { ElevationProvider } from "./providers/elevation.js";
import { LandcoverProvider } from "./providers/landcover.js";
import { AtmosphereProvider } from "./providers/atmosphere.js";
import { FireProvider } from "./providers/fire.js";
import { OceanProvider } from "./providers/ocean.js";
import { AltimetryProvider } from "./providers/altimetry.js";
import { PrecipitationProvider } from "./providers/precipitation.js";
import { HydrologyProvider } from "./providers/hydrology.js";
import { NightlightsProvider } from "./providers/nightlights.js";
import { computeSpectralIndex, IndexInputs } from "./indices.js";

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
    this.providers.set(Category.ELEVATION, new ElevationProvider());
    this.providers.set(Category.LANDCOVER, new LandcoverProvider());
    this.providers.set(Category.ATMOSPHERE, new AtmosphereProvider());
    this.providers.set(Category.FIRE, new FireProvider());
    this.providers.set(Category.OCEAN, new OceanProvider());
    this.providers.set(Category.ALTIMETRY, new AltimetryProvider());
    this.providers.set(Category.PRECIPITATION, new PrecipitationProvider());
    this.providers.set(Category.HYDROLOGY, new HydrologyProvider());
    this.providers.set(Category.NIGHTLIGHTS, new NightlightsProvider());
  }

  public listCategories(): string[] {
    return Object.values(Category);
  }

  public aoiFromGeoJSON(geojson: string | Record<string, any>): AOI {
    let data: any = geojson;
    if (typeof geojson === "string") {
      try {
        if (fs.existsSync(geojson)) {
          data = JSON.parse(fs.readFileSync(geojson, "utf-8"));
        } else {
          data = JSON.parse(geojson);
        }
      } catch {
        data = JSON.parse(geojson);
      }
    }
    const coords: [number, number][] = [];
    const extract = (obj: any) => {
      if (!obj) return;
      if (Array.isArray(obj)) {
        if (obj.length >= 2 && typeof obj[0] === "number" && typeof obj[1] === "number") {
          coords.push([obj[0], obj[1]]);
        } else {
          for (const item of obj) extract(item);
        }
      } else if (typeof obj === "object") {
        if (obj.coordinates) extract(obj.coordinates);
        else if (obj.features) {
          for (const f of obj.features) extract(f.geometry);
        } else if (obj.geometry) extract(obj.geometry);
        else if (obj.geometries) {
          for (const g of obj.geometries) extract(g);
        }
      }
    };
    extract(data);
    if (coords.length === 0) {
      throw new Error("No valid coordinates found in GeoJSON structure");
    }
    const min_lon = Math.min(...coords.map((c) => c[0]));
    const max_lon = Math.max(...coords.map((c) => c[0]));
    const min_lat = Math.min(...coords.map((c) => c[1]));
    const max_lat = Math.max(...coords.map((c) => c[1]));
    return { bbox: [min_lon, min_lat, max_lon, max_lat] };
  }

  private resolveAOI(params: SearchParams): AOI {
    if (params.aoi) {
      return params.aoi;
    }
    if (params.geojson) {
      return this.aoiFromGeoJSON(params.geojson);
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
    throw new Error("Must specify 'bbox' ([min_lon, min_lat, max_lon, max_lat]), 'point' ([lon, lat, radius_km?]), or 'geojson'");
  }

  public async search(params: SearchParams): Promise<SearchResult[]> {
    const cat = typeof params.category === "string" ? (params.category as Category) : params.category;
    const provider = this.providers.get(cat);
    if (!provider) {
      throw new Error(`Unsupported category '${cat}'. Supported: ${this.listCategories().join(", ")}`);
    }

    const aoi = this.resolveAOI(params);
    let startDate = params.startDate;
    let endDate = params.endDate;
    if (params.year && !startDate && !endDate) {
      startDate = `${params.year}-01-01`;
      endDate = `${params.year}-12-31`;
    }

    const filters: FilterOptions = {
      maxCloudCover: params.maxCloudCover,
      bands: params.bands,
      variables: params.variables,
      depth: params.depth,
      dataset: params.dataset,
      year: params.year,
      level: params.level,
      limit: params.limit
    };

    return provider.search(aoi, startDate, endDate, filters);
  }

  public async download(
    result: SearchResult,
    assetKey?: string,
    outdir?: string,
    options?: DownloadOptions
  ): Promise<string> {
    const provider = this.providers.get(result.category);
    if (!provider) {
      throw new Error(`No provider adapter found for category '${result.category}'`);
    }
    return provider.download(result, assetKey, outdir, options);
  }

  public async downloadAll(
    result: SearchResult,
    assetKeys?: string[],
    outdir?: string,
    options?: DownloadOptions
  ): Promise<Record<string, string>> {
    const keys = assetKeys || Object.keys(result.assets);
    if (keys.length === 0) {
      throw new Error(`No assets found to download for item '${result.id}'`);
    }

    const downloaded: Record<string, string> = {};
    const concurrency = options?.concurrency || 4;

    for (let i = 0; i < keys.length; i += concurrency) {
      const batch = keys.slice(i, i + concurrency);
      await Promise.all(
        batch.map(async (k) => {
          const filePath = await this.download(result, k, outdir, { ...options, multipart: false });
          downloaded[k] = filePath;
        })
      );
    }
    return downloaded;
  }

  public async downloadMany(
    results: SearchResult[],
    assetKey?: string,
    outdir?: string,
    options?: DownloadOptions
  ): Promise<string[]> {
    if (results.length === 0) return [];
    const concurrency = options?.concurrency || 4;
    const paths: string[] = [];

    for (let i = 0; i < results.length; i += concurrency) {
      const batch = results.slice(i, i + concurrency);
      const batchPaths = await Promise.all(
        batch.map((r) => this.download(r, assetKey, outdir, { ...options, multipart: false }))
      );
      paths.push(...batchPaths);
    }
    return paths;
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

  public async getElevation(
    bbox: [number, number, number, number],
    dataset: string = "copernicus"
  ): Promise<SearchResult | null> {
    const results = await this.search({
      category: Category.ELEVATION,
      bbox,
      dataset
    });
    return results[0] || null;
  }

  public async getLandcover(
    bbox: [number, number, number, number],
    year: number = 2021
  ): Promise<SearchResult | null> {
    const results = await this.search({
      category: Category.LANDCOVER,
      bbox,
      year
    });
    return results[0] || null;
  }

  public async getAtmosphere(
    bbox: [number, number, number, number],
    startDate?: string,
    endDate?: string,
    variables?: string[]
  ): Promise<SearchResult | null> {
    const results = await this.search({
      category: Category.ATMOSPHERE,
      bbox,
      startDate,
      endDate,
      variables
    });
    return results[0] || null;
  }

  public async getFire(
    bbox: [number, number, number, number],
    startDate?: string
  ): Promise<SearchResult | null> {
    const results = await this.search({
      category: Category.FIRE,
      bbox,
      startDate
    });
    return results[0] || null;
  }

  public async getOcean(
    bbox: [number, number, number, number],
    startDate?: string
  ): Promise<SearchResult | null> {
    const results = await this.search({
      category: Category.OCEAN,
      bbox,
      startDate
    });
    return results[0] || null;
  }

  public async getAltimetry(
    bbox: [number, number, number, number],
    startDate?: string
  ): Promise<SearchResult | null> {
    const results = await this.search({
      category: Category.ALTIMETRY,
      bbox,
      startDate
    });
    return results[0] || null;
  }

  public async getPrecipitation(
    bbox: [number, number, number, number],
    startDate?: string
  ): Promise<SearchResult | null> {
    const results = await this.search({
      category: Category.PRECIPITATION,
      bbox,
      startDate
    });
    return results[0] || null;
  }

  public async getHydrology(
    bbox: [number, number, number, number],
    startDate?: string
  ): Promise<SearchResult | null> {
    const results = await this.search({
      category: Category.HYDROLOGY,
      bbox,
      startDate
    });
    return results[0] || null;
  }

  public async getNightlights(
    bbox: [number, number, number, number],
    startDate?: string
  ): Promise<SearchResult | null> {
    const results = await this.search({
      category: Category.NIGHTLIGHTS,
      bbox,
      startDate
    });
    return results[0] || null;
  }

  public async getOptical(
    bbox: [number, number, number, number],
    options?: { maxCloudCover?: number; level?: "sr" | "toa" | string; startDate?: string; endDate?: string }
  ): Promise<SearchResult | null> {
    const results = await this.search({
      category: Category.OPTICAL,
      bbox,
      maxCloudCover: options?.maxCloudCover ?? 20.0,
      level: options?.level ?? "sr",
      startDate: options?.startDate,
      endDate: options?.endDate,
      limit: 1
    });
    return results[0] || null;
  }

  public async getSar(
    bbox: [number, number, number, number],
    options?: { startDate?: string; endDate?: string }
  ): Promise<SearchResult | null> {
    const results = await this.search({
      category: Category.SAR,
      bbox,
      startDate: options?.startDate,
      endDate: options?.endDate,
      limit: 1
    });
    return results[0] || null;
  }

  public computeIndex(
    index: string,
    inputs: IndexInputs
  ): number | number[] {
    const res = computeSpectralIndex(index, inputs);
    return res.data;
  }

  public async getTimeSeries(params: SearchParams): Promise<any[]> {
    const results = await this.search(params);
    const cat = typeof params.category === "string" ? params.category : params.category;
    if ((cat === Category.WEATHER || cat === Category.ATMOSPHERE) && results.length > 0) {
      const raw = results[0].properties?.raw_feed || results[0].properties?._raw_data || {};
      const hourly = raw.hourly || {};
      const times: string[] = hourly.time || [];
      return times.map((t, idx) => {
        const item: Record<string, any> = { datetime: t };
        for (const [k, v] of Object.entries(hourly)) {
          if (k !== "time" && Array.isArray(v)) {
            item[k] = v[idx];
          }
        }
        return item;
      });
    }

    return results
      .slice()
      .sort((a, b) => (a.datetime || "").localeCompare(b.datetime || ""))
      .map((r) => ({
        id: r.id,
        datetime: r.datetime,
        category: r.category,
        collection: r.collection,
        cloudCover: r.properties?.["eo:cloud_cover"],
        assets: Object.keys(r.assets)
      }));
  }
}
