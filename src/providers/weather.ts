import * as fs from "fs";
import * as path from "path";
import { BaseProvider } from "./base.js";
import { AOI, SearchResult, Category, FilterOptions } from "../types.js";
import { config } from "../config.js";

export class WeatherProvider extends BaseProvider {
  category = Category.WEATHER;
  name = "weather";

  private forecastUrl = "https://api.open-meteo.com/v1/forecast";
  private historicalUrl = "https://archive-api.open-meteo.com/v1/archive";

  private defaultHourlyVars = [
    "temperature_2m",
    "relative_humidity_2m",
    "precipitation",
    "soil_temperature_0cm",
    "soil_moisture_0_to_1cm",
    "soil_moisture_1_to_3cm",
    "soil_moisture_3_to_9cm"
  ];

  async search(
    aoi: AOI,
    startDate?: string,
    endDate?: string,
    filters?: FilterOptions
  ): Promise<SearchResult[]> {
    const centerLon = Number(((aoi.bbox[0] + aoi.bbox[2]) / 2.0).toFixed(4));
    const centerLat = Number(((aoi.bbox[1] + aoi.bbox[3]) / 2.0).toFixed(4));

    const hourlyVars = filters?.variables || this.defaultHourlyVars;
    const isHistorical = Boolean(startDate && endDate && startDate < "2026-10-20");
    const apiUrl = isHistorical ? this.historicalUrl : this.forecastUrl;

    const params = new URLSearchParams({
      latitude: String(centerLat),
      longitude: String(centerLon),
      hourly: hourlyVars.join(","),
      timezone: "auto"
    });

    if (startDate && endDate) {
      params.append("start_date", startDate);
      params.append("end_date", endDate);
    }

    const fullUrl = `${apiUrl}?${params.toString()}`;
    const res = await fetch(fullUrl);
    if (!res.ok) {
      throw new Error(`Open-Meteo API query failed (HTTP ${res.status})`);
    }

    const data = await res.json();
    const feedId = `openmeteo_${centerLat}_${centerLon}_${startDate || "latest"}`;

    return [
      {
        id: feedId,
        collection: "open-meteo-weather",
        category: this.category,
        provider: "open_meteo",
        datetime: startDate ? `${startDate} to ${endDate}` : "now",
        bbox: aoi.bbox,
        properties: {
          latitude: centerLat,
          longitude: centerLon,
          elevation: data.elevation,
          timezone: data.timezone,
          utc_offset_seconds: data.utc_offset_seconds,
          raw_feed: data
        },
        assets: {
          data: {
            key: "data",
            href: fullUrl,
            title: "Hourly Meteorological & Soil Feed",
            media_type: "application/json"
          }
        }
      }
    ];
  }

  override async download(
    result: SearchResult,
    assetKey?: string,
    outdir?: string
  ): Promise<string> {
    const targetDir = outdir || config.defaultOutdir;
    if (!fs.existsSync(targetDir)) {
      fs.mkdirSync(targetDir, { recursive: true });
    }

    const outPath = path.join(targetDir, `${result.id}.json`);
    const rawData = result.properties?.raw_feed || result.properties?._raw_data;

    if (rawData) {
      fs.writeFileSync(outPath, JSON.stringify(rawData, null, 2), "utf-8");
      return outPath;
    }

    const asset = result.assets["data"] || Object.values(result.assets)[0];
    if (asset?.href) {
      await this.streamDownload(asset.href, outPath);
      return outPath;
    }

    throw new Error(`Could not download weather feed for ${result.id}`);
  }
}

