import * as fs from "fs";
import * as path from "path";

/**
 * OmniEarth Core Types
 */

export enum Category {
  OPTICAL = "optical",
  SAR = "sar",
  HYPERSPECTRAL = "hyperspectral",
  WEATHER = "weather",
  SOIL = "soil",
  ELEVATION = "elevation",
  LANDCOVER = "landcover",
  ATMOSPHERE = "atmosphere",
  FIRE = "fire",
  OCEAN = "ocean",
  ALTIMETRY = "altimetry",
  PRECIPITATION = "precipitation",
  HYDROLOGY = "hydrology",
  NIGHTLIGHTS = "nightlights"
}

export interface AOI {
  bbox: [number, number, number, number]; // [min_lon, min_lat, max_lon, max_lat]
  geometry?: Record<string, any>;
}

export interface Asset {
  key: string;
  href: string;
  title?: string;
  media_type?: string;
  size_bytes?: number;
  roles?: string[];
  checksum?: string;
  checksum_algorithm?: string;
}

export interface SearchResult {
  id: string;
  collection: string;
  category: Category;
  provider: string;
  datetime?: string;
  bbox?: [number, number, number, number];
  properties: Record<string, any>;
  assets: Record<string, Asset>;
  checksum?: string;
  checksum_algorithm?: string;
}

export interface FilterOptions {
  maxCloudCover?: number;
  bands?: string[];
  variables?: string[];
  depth?: string;
  dataset?: string;
  year?: number;
  level?: "sr" | "toa" | string;
  limit?: number;
  provider?: string;
  format?: string;
}

export interface SearchParams {
  category: Category | string;
  bbox?: [number, number, number, number];
  point?: [number, number, number?]; // [lon, lat, radius_km?]
  aoi?: AOI;
  geojson?: string | Record<string, any>;
  startDate?: string;
  endDate?: string;
  maxCloudCover?: number;
  bands?: string[];
  variables?: string[];
  depth?: string;
  dataset?: string;
  year?: number;
  level?: "sr" | "toa" | string;
  limit?: number;
  provider?: string;
  format?: string;
}

export class SearchResults extends Array<SearchResult> {
  public _client?: any;

  constructor(items?: SearchResult[] | number, client?: any) {
    if (typeof items === "number") {
      super(items);
      return;
    }
    super(...(items || []));
    this._client = client;
    Object.setPrototypeOf(this, SearchResults.prototype);
  }

  public first(): SearchResult | undefined {
    return this.length > 0 ? this[0] : undefined;
  }

  public filterResults(predicate: { provider?: string; collection?: string; maxCloudCover?: number }): SearchResults {
    const filtered = this.filter((r) => {
      if (predicate.provider && r.provider !== predicate.provider) return false;
      if (predicate.collection && r.collection !== predicate.collection) return false;
      if (predicate.maxCloudCover !== undefined) {
        const cc = (r.properties as any)?.cloud_cover ?? (r.properties as any)?.["eo:cloud_cover"];
        if (cc !== undefined && cc > predicate.maxCloudCover) return false;
      }
      return true;
    });
    return new SearchResults(filtered, this._client);
  }

  public exportGeoJSON(outputPath: string): string {
    const resolvedPath = path.resolve(outputPath);
    const dir = path.dirname(resolvedPath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
    const features = this.map((r) => {
      let geometry = r.properties?.geometry;
      if (!geometry && r.bbox && r.bbox.length === 4) {
        const [min_lon, min_lat, max_lon, max_lat] = r.bbox;
        if (min_lon === max_lon && min_lat === max_lat) {
          geometry = {
            type: "Point",
            coordinates: [min_lon, min_lat]
          };
        } else {
          geometry = {
            type: "Polygon",
            coordinates: [[
              [min_lon, min_lat],
              [max_lon, min_lat],
              [max_lon, max_lat],
              [min_lon, max_lat],
              [min_lon, min_lat]
            ]]
          };
        }
      }
      if (!geometry) {
        const lat = r.properties?.latitude ?? r.properties?.center_lat ?? r.properties?.lat;
        const lon = r.properties?.longitude ?? r.properties?.center_lon ?? r.properties?.lon;
        if (lat !== undefined && lon !== undefined) {
          geometry = {
            type: "Point",
            coordinates: [Number(lon), Number(lat)]
          };
        }
      }
      const dlUrl = r.assets?.data?.href || r.assets?.visual?.href || Object.values(r.assets || {})[0]?.href || "";
      return {
        type: "Feature",
        id: r.id,
        geometry: geometry || null,
        properties: {
          id: r.id,
          collection: r.collection,
          category: r.category,
          provider: r.provider,
          datetime: r.datetime,
          cloud_cover: r.properties?.cloud_cover ?? r.properties?.["eo:cloud_cover"],
          download_url: dlUrl,
          assets: Object.keys(r.assets || {}),
          ...r.properties
        }
      };
    });

    const fc = { type: "FeatureCollection", features };
    fs.writeFileSync(resolvedPath, JSON.stringify(fc, null, 2), "utf-8");
    return resolvedPath;
  }

  public exportCSV(outputPath: string): string {
    const resolvedPath = path.resolve(outputPath);
    const dir = path.dirname(resolvedPath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
    const headers = [
      "id",
      "collection",
      "category",
      "provider",
      "datetime",
      "cloud_cover",
      "latitude",
      "longitude",
      "bbox",
      "download_url",
      "assets"
    ];
    const rows = [headers.join(",")];
    for (const r of this) {
      const cc = r.properties?.cloud_cover ?? r.properties?.["eo:cloud_cover"] ?? "";
      let latVal = r.properties?.latitude ?? r.properties?.center_lat ?? r.properties?.lat;
      let lonVal = r.properties?.longitude ?? r.properties?.center_lon ?? r.properties?.lon;
      if ((latVal === undefined || lonVal === undefined) && r.bbox && r.bbox.length === 4) {
        lonVal = Math.round(((r.bbox[0] + r.bbox[2]) / 2.0) * 1000000) / 1000000;
        latVal = Math.round(((r.bbox[1] + r.bbox[3]) / 2.0) * 1000000) / 1000000;
      }
      const bboxStr = r.bbox ? r.bbox.join(";") : "";
      const dlUrl = r.assets?.data?.href || r.assets?.visual?.href || Object.values(r.assets || {})[0]?.href || "";
      const assetKeys = Object.keys(r.assets || {}).join(";");
      const row = [
        `"${r.id}"`,
        `"${r.collection}"`,
        `"${r.category}"`,
        `"${r.provider}"`,
        `"${r.datetime || ""}"`,
        `"${cc}"`,
        `"${latVal ?? ""}"`,
        `"${lonVal ?? ""}"`,
        `"${bboxStr}"`,
        `"${dlUrl}"`,
        `"${assetKeys}"`
      ];
      rows.push(row.join(","));
    }
    fs.writeFileSync(resolvedPath, rows.join("\n"), "utf-8");
    return resolvedPath;
  }

  public export(outputPath: string): string {
    if (outputPath.toLowerCase().endsWith(".csv")) {
      return this.exportCSV(outputPath);
    }
    return this.exportGeoJSON(outputPath);
  }

  public async downloadAll(assetKey?: string, outdir?: string, options?: any): Promise<string[]> {
    if (!this._client) {
      throw new Error("No OmniEarth client attached to SearchResults");
    }
    return this._client.downloadMany(this, assetKey, outdir, options);
  }

  public async downloadIndices(indices: number[], assetKey?: string, outdir?: string, options?: any): Promise<string[]> {
    if (!this._client) {
      throw new Error("No OmniEarth client attached to SearchResults");
    }
    const selected = indices.map((i) => this[i]).filter(Boolean);
    return this._client.downloadMany(selected, assetKey, outdir, options);
  }
}


