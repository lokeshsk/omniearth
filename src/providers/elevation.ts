import * as path from "path";
import * as fs from "fs";
import { BaseProvider, DownloadOptions } from "./base.js";
import { AOI, SearchResult, Asset, Category, FilterOptions } from "../types.js";
import { config } from "../config.js";

const S3_COP30_BASE = "https://copernicus-dem-30m.s3.amazonaws.com";
const OPENTOPOGRAPHY_SRTM_BASE = "https://opentopography.s3.sdsc.edu/raster/SRTM_GL1/SRTM_GL1_srtm";
const OPENTOPOGRAPHY_ALOS_BASE = "https://opentopography.s3.sdsc.edu/raster/AW3D30/AW3D30_global";

export class ElevationProvider extends BaseProvider {
  category = Category.ELEVATION;
  name = "elevation";

  private generateCopernicusTile(lat: number, lon: number): SearchResult {
    const latP = lat >= 0 ? `N${String(lat).padStart(2, "0")}` : `S${String(Math.abs(lat)).padStart(2, "0")}`;
    const lonP = lon >= 0 ? `E${String(lon).padStart(3, "0")}` : `W${String(Math.abs(lon)).padStart(3, "0")}`;
    const tileId = `Copernicus_DSM_COG_10_${latP}_00_${lonP}_00_DEM`;
    const filename = `${tileId}.tif`;
    const url = `${S3_COP30_BASE}/${tileId}/${filename}`;

    return {
      id: tileId,
      collection: "copernicus-dem-glo-30",
      category: this.category,
      provider: "aws_copernicus_dem",
      datetime: "2026-01-01T00:00:00Z",
      bbox: [lon, lat, lon + 1, lat + 1],
      properties: {
        title: `Copernicus DEM 30m (${latP}, ${lonP})`,
        dataset: "copernicus",
        resolution: "30m",
        sensor_type: "DSM",
        grid_lat: lat,
        grid_lon: lon
      },
      assets: {
        dem: {
          key: "dem",
          href: url,
          media_type: "image/tiff; application=geotiff; profile=cloud-optimized",
          title: "DEM Raster COG"
        },
        data: {
          key: "data",
          href: url,
          media_type: "image/tiff",
          title: "DEM Raster"
        }
      }
    };
  }

  private generateSrtmTile(lat: number, lon: number): SearchResult {
    const latP = lat >= 0 ? `N${String(lat).padStart(2, "0")}` : `S${String(Math.abs(lat)).padStart(2, "0")}`;
    const lonP = lon >= 0 ? `E${String(lon).padStart(3, "0")}` : `W${String(Math.abs(lon)).padStart(3, "0")}`;
    const tileId = `${latP}${lonP}`;
    const filename = `${tileId}.tif`;
    const url = `${OPENTOPOGRAPHY_SRTM_BASE}/${filename}`;

    return {
      id: `SRTM_GL1_${tileId}`,
      collection: "srtm-gl1-30m",
      category: this.category,
      provider: "opentopography_srtm",
      datetime: "2026-01-01T00:00:00Z",
      bbox: [lon, lat, lon + 1, lat + 1],
      properties: {
        title: `SRTM GL1 30m (${latP}, ${lonP})`,
        dataset: "srtm",
        resolution: "30m",
        sensor_type: "DSM",
        grid_lat: lat,
        grid_lon: lon
      },
      assets: {
        dem: {
          key: "dem",
          href: url,
          media_type: "image/tiff",
          title: "SRTM GeoTIFF"
        },
        data: {
          key: "data",
          href: url,
          media_type: "image/tiff",
          title: "SRTM GeoTIFF"
        }
      }
    };
  }

  private generateAlosTile(lat: number, lon: number): SearchResult {
    const latP = lat >= 0 ? `N${String(lat).padStart(3, "0")}` : `S${String(Math.abs(lat)).padStart(3, "0")}`;
    const lonP = lon >= 0 ? `E${String(lon).padStart(3, "0")}` : `W${String(Math.abs(lon)).padStart(3, "0")}`;
    const tileId = `ALPSMLC30_${latP}${lonP}_DSM`;
    const filename = `${tileId}.tif`;
    const url = `${OPENTOPOGRAPHY_ALOS_BASE}/${filename}`;

    return {
      id: tileId,
      collection: "alos-aw3d30-30m",
      category: this.category,
      provider: "opentopography_alos",
      datetime: "2026-01-01T00:00:00Z",
      bbox: [lon, lat, lon + 1, lat + 1],
      properties: {
        title: `ALOS World 3D 30m (${latP}, ${lonP})`,
        dataset: "alos",
        resolution: "30m",
        sensor_type: "DSM",
        grid_lat: lat,
        grid_lon: lon
      },
      assets: {
        dem: {
          key: "dem",
          href: url,
          media_type: "image/tiff",
          title: "ALOS AW3D30 GeoTIFF"
        },
        data: {
          key: "data",
          href: url,
          media_type: "image/tiff",
          title: "ALOS AW3D30 GeoTIFF"
        }
      }
    };
  }

  async search(
    aoi: AOI,
    startDate?: string,
    endDate?: string,
    filters?: FilterOptions
  ): Promise<SearchResult[]> {
    const dataset = (filters?.dataset || "copernicus").toLowerCase();
    const limit = filters?.limit || 10;

    const [minx, miny, maxx, maxy] = aoi.bbox;
    let lonStart = Math.floor(minx);
    let lonEnd = Math.ceil(maxx);
    let latStart = Math.floor(miny);
    let latEnd = Math.ceil(maxy);

    if (lonStart === lonEnd) lonEnd += 1;
    if (latStart === latEnd) latEnd += 1;

    const results: SearchResult[] = [];
    for (let lat = latStart; lat < latEnd; lat++) {
      for (let lon = lonStart; lon < lonEnd; lon++) {
        if (results.length >= limit) return results;

        if (dataset === "copernicus" || dataset === "cop30" || dataset === "glo-30") {
          results.push(this.generateCopernicusTile(lat, lon));
        } else if (dataset === "srtm" || dataset === "srtm30" || dataset === "gl1") {
          results.push(this.generateSrtmTile(lat, lon));
        } else if (dataset === "alos" || dataset === "aw3d30") {
          results.push(this.generateAlosTile(lat, lon));
        } else {
          results.push(this.generateCopernicusTile(lat, lon));
        }
      }
    }
    return results;
  }

  override async download(
    result: SearchResult,
    assetKey?: string,
    outdir?: string,
    options?: DownloadOptions
  ): Promise<string> {
    let targetAsset = assetKey ? result.assets[assetKey] : result.assets["dem"] || result.assets["data"];
    if (!targetAsset && Object.keys(result.assets).length > 0) {
      targetAsset = Object.values(result.assets)[0];
    }

    if (!targetAsset || !targetAsset.href) {
      throw new Error(`No valid DEM asset found for '${result.id}'`);
    }

    const cleanName = path.basename(targetAsset.href.split("?")[0]);
    const filename = cleanName.endsWith(".tif") || cleanName.endsWith(".tiff") ? cleanName : `${result.id}.tif`;
    const targetDir = outdir || config.defaultOutdir;
    if (!fs.existsSync(targetDir)) {
      fs.mkdirSync(targetDir, { recursive: true });
    }
    const outpath = path.resolve(targetDir, filename);

    await this.streamDownload(targetAsset.href, outpath, {}, options);
    return outpath;
  }
}
