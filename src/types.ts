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


