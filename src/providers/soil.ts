import * as fs from "fs";
import * as path from "path";
import { BaseProvider } from "./base.js";
import { AOI, SearchResult, Category, FilterOptions } from "../types.js";
import { config } from "../config.js";

export class SoilProvider extends BaseProvider {
  category = Category.SOIL;
  name = "soil";

  private soilgridsUrl = "https://rest.isric.org/soilgrids/v2.0/properties/query";
  private defaultProperties = ["clay", "sand", "soc", "phh2o"];
  private defaultDepths = ["0-5cm"];

  async search(
    aoi: AOI,
    startDate?: string,
    endDate?: string,
    filters?: FilterOptions
  ): Promise<SearchResult[]> {
    const centerLon = Number(((aoi.bbox[0] + aoi.bbox[2]) / 2.0).toFixed(4));
    const centerLat = Number(((aoi.bbox[1] + aoi.bbox[3]) / 2.0).toFixed(4));

    const props = filters?.variables || this.defaultProperties;
    const depths = filters?.depth ? [filters.depth] : this.defaultDepths;

    const params = new URLSearchParams();
    params.append("lon", String(centerLon));
    params.append("lat", String(centerLat));
    for (const p of props) params.append("property", p);
    for (const d of depths) params.append("depth", d);

    const fullUrl = `${this.soilgridsUrl}?${params.toString()}`;
    const res = await fetch(fullUrl);
    if (!res.ok) {
      throw new Error(`SoilGrids query failed (HTTP ${res.status})`);
    }

    const data = await res.json();
    const layers = data?.properties?.layers || [];
    const summary: Record<string, any> = {};

    for (const lay of layers) {
      const name = lay.name;
      const dData = lay.depths || [];
      if (dData.length > 0) {
        summary[name] = {
          range: dData[0]?.label,
          mean: dData[0]?.values?.mean
        };
      }
    }

    const feedId = `soilgrids_${centerLat}_${centerLon}`;

    return [
      {
        id: feedId,
        collection: "isric-soilgrids-v2",
        category: this.category,
        provider: "isric",
        datetime: "static-3d",
        bbox: aoi.bbox,
        properties: {
          latitude: centerLat,
          longitude: centerLon,
          depths_queried: depths,
          summary_topsoil: summary,
          raw_layers: data
        },
        assets: {
          data: {
            key: "data",
            href: fullUrl,
            title: "SoilGrids v2.0 Global Profile",
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
    const rawData = result.properties?.raw_layers;

    if (rawData) {
      fs.writeFileSync(outPath, JSON.stringify(rawData, null, 2), "utf-8");
      return outPath;
    }

    const asset = result.assets["data"] || Object.values(result.assets)[0];
    if (asset?.href) {
      await this.streamDownload(asset.href, outPath);
      return outPath;
    }

    throw new Error(`Could not download soil profile for ${result.id}`);
  }
}
