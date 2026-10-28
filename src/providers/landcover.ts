import * as path from "path";
import * as fs from "fs";
import { BaseProvider, DownloadOptions } from "./base.js";
import { AOI, SearchResult, Asset, Category, FilterOptions } from "../types.js";
import { config } from "../config.js";

const ESA_WORLDCOVER_BASE = "https://esa-worldcover.s3.eu-central-1.amazonaws.com";

const WORLDCOVER_CLASSES: Record<number, string> = {
  10: "Tree cover",
  20: "Shrubland",
  30: "Grassland",
  40: "Cropland",
  50: "Built-up",
  60: "Bare / sparse vegetation",
  70: "Snow and ice",
  80: "Permanent water bodies",
  90: "Herbaceous wetland",
  95: "Mangroves",
  100: "Moss and lichen"
};

export class LandcoverProvider extends BaseProvider {
  category = Category.LANDCOVER;
  name = "landcover";

  private generateWorldCoverTile(lat: number, lon: number, year: number = 2021): SearchResult {
    const gridLat = Math.floor(lat / 3) * 3;
    const gridLon = Math.floor(lon / 3) * 3;

    const latP = gridLat >= 0 ? `N${String(gridLat).padStart(2, "0")}` : `S${String(Math.abs(gridLat)).padStart(2, "0")}`;
    const lonP = gridLon >= 0 ? `E${String(gridLon).padStart(3, "0")}` : `W${String(Math.abs(gridLon)).padStart(3, "0")}`;
    const version = year >= 2021 ? "v200" : "v100";
    const actualYear = year >= 2021 ? 2021 : 2020;

    const tileId = `ESA_WorldCover_10m_${actualYear}_${version}_${latP}${lonP}_Map`;
    const filename = `${tileId}.tif`;
    const url = `${ESA_WORLDCOVER_BASE}/${version}/${actualYear}/map/${filename}`;

    return {
      id: tileId,
      collection: `esa-worldcover-${actualYear}`,
      category: this.category,
      provider: "esa_worldcover_aws",
      datetime: `${actualYear}-01-01T00:00:00Z`,
      bbox: [gridLon, gridLat, gridLon + 3, gridLat + 3],
      properties: {
        title: `ESA WorldCover 10m (${actualYear}, ${latP}${lonP})`,
        dataset: "esa-worldcover",
        resolution: "10m",
        year: actualYear,
        version,
        classes: WORLDCOVER_CLASSES,
        grid_lat: gridLat,
        grid_lon: gridLon
      },
      assets: {
        map: {
          key: "map",
          href: url,
          media_type: "image/tiff; application=geotiff; profile=cloud-optimized",
          title: "ESA WorldCover 10m COG Map"
        },
        data: {
          key: "data",
          href: url,
          media_type: "image/tiff",
          title: "ESA WorldCover 10m Raster"
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
    let year = 2021;
    if (filters?.year) {
      year = filters.year;
    } else if (endDate && endDate.length >= 4 && !isNaN(parseInt(endDate.slice(0, 4), 10))) {
      year = parseInt(endDate.slice(0, 4), 10);
    } else if (startDate && startDate.length >= 4 && !isNaN(parseInt(startDate.slice(0, 4), 10))) {
      year = parseInt(startDate.slice(0, 4), 10);
    }

    const limit = filters?.limit || 10;
    const [minx, miny, maxx, maxy] = aoi.bbox;
    let lonStart = Math.floor(minx / 3) * 3;
    let lonEnd = Math.ceil(maxx / 3) * 3;
    let latStart = Math.floor(miny / 3) * 3;
    let latEnd = Math.ceil(maxy / 3) * 3;

    if (lonStart === lonEnd) lonEnd += 3;
    if (latStart === latEnd) latEnd += 3;

    const seen = new Set<string>();
    const results: SearchResult[] = [];

    for (let lat = latStart; lat < latEnd; lat += 3) {
      for (let lon = lonStart; lon < lonEnd; lon += 3) {
        const tile = this.generateWorldCoverTile(lat, lon, year);
        if (!seen.has(tile.id)) {
          seen.add(tile.id);
          results.push(tile);
        }
        if (results.length >= limit) return results;
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
    let targetAsset = assetKey ? result.assets[assetKey] : result.assets["map"] || result.assets["data"];
    if (!targetAsset && Object.keys(result.assets).length > 0) {
      targetAsset = Object.values(result.assets)[0];
    }

    if (!targetAsset || !targetAsset.href) {
      throw new Error(`No valid Landcover asset found for '${result.id}'`);
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
