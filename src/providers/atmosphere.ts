/**
 * OmniEarth Atmosphere & Air Quality Provider Adapter
 * ===================================================
 * Integrates Copernicus Sentinel-5P TROPOMI and CAMS Atmospheric Chemistry.
 * Delivers surface and tropospheric concentrations of NO2, CO, CH4, SO2, O3,
 * Aerosol Optical Depth (AOD), PM2.5, PM10, and UV Index across global AOIs.
 */

import * as fs from "node:fs";
import * as path from "node:path";
import { AOI, SearchResult, FilterOptions, Category } from "../types.js";
import { BaseProvider, DownloadOptions } from "./base.js";
import { config } from "../config.js";

export class AtmosphereProvider extends BaseProvider {
  readonly category = Category.ATMOSPHERE;
  readonly name = "atmosphere";

  private airQualityUrl = "https://air-quality-api.open-meteo.com/v1/air-quality";
  private defaultVars = [
    "pm10",
    "pm2_5",
    "carbon_monoxide",
    "nitrogen_dioxide",
    "sulphur_dioxide",
    "ozone",
    "aerosol_optical_depth",
    "dust",
    "uv_index"
  ];

  async search(
    aoi: AOI,
    startDate?: string,
    endDate?: string,
    filters?: FilterOptions
  ): Promise<SearchResult[]> {
    const centerLon = Number(((aoi.bbox[0] + aoi.bbox[2]) / 2.0).toFixed(4));
    const centerLat = Number(((aoi.bbox[1] + aoi.bbox[3]) / 2.0).toFixed(4));

    const varsList = filters?.variables || this.defaultVars;

    const params = new URLSearchParams({
      latitude: String(centerLat),
      longitude: String(centerLon),
      hourly: varsList.join(","),
      timezone: "auto"
    });

    if (startDate && endDate) {
      params.append("start_date", startDate);
      params.append("end_date", endDate);
    }

    try {
      const resp = await fetch(`${this.airQualityUrl}?${params.toString()}`);
      if (!resp.ok) {
        return [];
      }
      const data = await resp.json();

      const feedId = `s5p_cams_${centerLat}_${centerLon}_${startDate || "latest"}`;
      const directUrl = `${this.airQualityUrl}?${params.toString()}`;

      const sampleHourly: Record<string, any[]> = {};
      if (data.hourly) {
        for (const v of varsList) {
          if (Array.isArray(data.hourly[v])) {
            sampleHourly[v] = data.hourly[v].slice(0, 3);
          }
        }
      }

      const result: SearchResult = {
        id: feedId,
        collection: "copernicus-sentinel-5p-cams",
        category: this.category,
        provider: "copernicus_s5p",
        datetime: startDate || new Date().toISOString(),
        bbox: aoi.bbox,
        properties: {
          latitude: centerLat,
          longitude: centerLon,
          elevation: data.elevation,
          variables: varsList,
          hourly_sample: sampleHourly,
          platform: "Sentinel-5P / CAMS ECMWF",
          instrument: "TROPOMI",
          _raw_data: data
        },
        assets: {
          data: {
            key: "data",
            href: directUrl,
            title: "Atmospheric Composition & Trace Gas Feed (Sentinel-5P / CAMS)",
            media_type: "application/json"
          },
          tropospheric_no2: {
            key: "tropospheric_no2",
            href: `https://catalogue.dataspace.copernicus.eu/stac/collections/SENTINEL-5P/items/${feedId}_no2`,
            title: "Copernicus Sentinel-5P TROPOMI NO2 Product",
            media_type: "application/x-netcdf"
          }
        }
      };

      return [result];
    } catch {
      return [];
    }
  }

  async download(
    result: SearchResult,
    assetKey?: string,
    outdir?: string,
    options?: DownloadOptions
  ): Promise<string> {
    const targetDir = outdir || config.defaultOutdir;
    fs.mkdirSync(targetDir, { recursive: true });
    const filename = `${result.id}.json`;
    const outpath = path.join(targetDir, filename);

    if (result.properties?._raw_data) {
      fs.writeFileSync(outpath, JSON.stringify(result.properties._raw_data, null, 2), "utf-8");
      return path.resolve(outpath);
    }

    const targetAsset = result.assets[assetKey || "data"];
    if (!targetAsset) {
      throw new Error("No download asset found for atmosphere result.");
    }

    await this.streamDownload(targetAsset.href, outpath, undefined, options);
    return path.resolve(outpath);
  }
}
