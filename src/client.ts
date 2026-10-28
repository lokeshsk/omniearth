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
    const filters: FilterOptions = {
      maxCloudCover: params.maxCloudCover,
      bands: params.bands,
      variables: params.variables,
      depth: params.depth,
      dataset: params.dataset,
      year: params.year,
      limit: params.limit
    };

    return provider.search(aoi, params.startDate, params.endDate, filters);
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

  public computeIndex(
    index: string,
    inputs: {
      nir: number[] | number;
      red?: number[] | number;
      green?: number[] | number;
      blue?: number[] | number;
      rededge?: number[] | number;
      swir?: number[] | number;
    }
  ): number | number[] {
    const calc = (n: number, r?: number, g?: number, b?: number, re?: number, s?: number): number => {
      const idx = index.toLowerCase();
      if (idx === "ndvi") {
        if (r === undefined) throw new Error("Red band required to compute NDVI");
        return (n - r) / (n + r + 1e-8);
      } else if (idx === "ndwi") {
        if (g === undefined) throw new Error("Green band required to compute NDWI");
        return (g - n) / (g + n + 1e-8);
      } else if (idx === "ndre") {
        if (re === undefined) throw new Error("RedEdge band required to compute NDRE");
        return (n - re) / (n + re + 1e-8);
      } else if (idx === "evi") {
        if (r === undefined || b === undefined) throw new Error("Red and Blue bands required to compute EVI");
        return 2.5 * ((n - r) / (n + 6.0 * r - 7.5 * b + 1.0 + 1e-8));
      } else if (idx === "nbr") {
        if (s === undefined) throw new Error("SWIR band required to compute NBR");
        return (n - s) / (n + s + 1e-8);
      }
      throw new Error(`Unsupported index '${index}'. Supported: ndvi, ndwi, ndre, evi, nbr`);
    };

    if (Array.isArray(inputs.nir)) {
      const redArr = Array.isArray(inputs.red) ? inputs.red : [];
      const greenArr = Array.isArray(inputs.green) ? inputs.green : [];
      const blueArr = Array.isArray(inputs.blue) ? inputs.blue : [];
      const rededgeArr = Array.isArray(inputs.rededge) ? inputs.rededge : [];
      const swirArr = Array.isArray(inputs.swir) ? inputs.swir : [];

      return inputs.nir.map((val, i) => calc(val, redArr[i], greenArr[i], blueArr[i], rededgeArr[i], swirArr[i]));
    } else {
      return calc(inputs.nir, inputs.red as number, inputs.green as number, inputs.blue as number, inputs.rededge as number, inputs.swir as number);
    }
  }

  public async getTimeSeries(params: SearchParams): Promise<any[]> {
    const results = await this.search(params);
    const cat = typeof params.category === "string" ? params.category : params.category;
    if (cat === Category.WEATHER && results.length > 0) {
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
