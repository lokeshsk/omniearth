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
  LANDCOVER = "landcover"
}

export interface AOI {
  bbox: [number, number, number, number]; // [min_lon, min_lat, max_lon, max_lat]
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
  limit?: number;
}

