import * as fs from "fs";
import * as path from "path";
import { BaseProvider } from "./base.js";
import { AOI, SearchResult, Asset, Category, FilterOptions } from "../types.js";
import { config } from "../config.js";

export class HyperspectralProvider extends BaseProvider {
  category = Category.HYPERSPECTRAL;
  name = "hyperspectral";

  private enmapStacUrl = "https://geoservice.dlr.de/eoc/ogc/stac/collections/ENMAP_HSI_L2A/items";
  private emitStacUrl = "https://cmr.earthdata.nasa.gov/stac/LPCLOUD/collections/EMITL2ARFL.v001/items";

  async search(
    aoi: AOI,
    startDate?: string,
    endDate?: string,
    filters?: FilterOptions
  ): Promise<SearchResult[]> {
    const results: SearchResult[] = [];
    const limit = filters?.limit || 10;

    // 1. Query DLR EnMAP STAC
    try {
      const bboxStr = `${aoi.bbox[0]},${aoi.bbox[1]},${aoi.bbox[2]},${aoi.bbox[3]}`;
      const params = new URLSearchParams({
        bbox: bboxStr,
        limit: String(limit)
      });
      if (startDate && endDate) {
        params.append("datetime", `${startDate}T00:00:00Z/${endDate}T23:59:59Z`);
      }

      const res = await fetch(`${this.enmapStacUrl}?${params.toString()}`);
      if (res.ok) {
        const data = await res.json();
        for (const feat of data.features || []) {
          const assets: Record<string, Asset> = {};
          for (const [k, a] of Object.entries<any>(feat.assets || {})) {
            assets[k] = {
              key: k,
              href: a.href,
              title: a.title,
              media_type: a.type,
              roles: a.roles
            };
          }

          results.push({
            id: feat.id,
            collection: "enmap-hsi-l2a",
            category: this.category,
            provider: "dlr_enmap",
            datetime: feat.properties?.datetime,
            bbox: feat.bbox,
            properties: { ...feat.properties, platform: "enmap" },
            assets
          });
        }
      }
    } catch {
      // Continue to EMIT fallback
    }

    // 2. Query NASA EMIT CMR STAC if results < limit
    if (results.length < limit) {
      try {
        const bboxStr = `${aoi.bbox[0]},${aoi.bbox[1]},${aoi.bbox[2]},${aoi.bbox[3]}`;
        const params = new URLSearchParams({
          bbox: bboxStr,
          limit: String(limit - results.length)
        });
        if (startDate && endDate) {
          params.append("datetime", `${startDate}T00:00:00Z/${endDate}T23:59:59Z`);
        }

        const res = await fetch(`${this.emitStacUrl}?${params.toString()}`);
        if (res.ok) {
          const data = await res.json();
          for (const feat of data.features || []) {
            const assets: Record<string, Asset> = {};
            for (const [k, a] of Object.entries<any>(feat.assets || {})) {
              assets[k] = {
                key: k,
                href: a.href,
                title: a.title,
                media_type: a.type,
                roles: a.roles
              };
            }

            results.push({
              id: feat.id,
              collection: "emit-l2a-rfl",
              category: this.category,
              provider: "nasa_emit",
              datetime: feat.properties?.datetime,
              bbox: feat.bbox,
              properties: { ...feat.properties, platform: "emit" },
              assets
            });
          }
        }
      } catch {
        // Handled
      }
    }

    return results;
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

    let authHeaders: Record<string, string> | undefined;
    if (result.provider === "dlr_enmap") {
      const [u, p] = config.dlrCredentials;
      if (u && p) {
        const token = Buffer.from(`${u}:${p}`).toString("base64");
        authHeaders = { Authorization: `Basic ${token}` };
      }
    }

    const key = assetKey || "SPECTRAL_IMAGE_COG";
    const asset = result.assets[key] || result.assets["data"] || Object.values(result.assets)[0];

    if (!asset || !asset.href) {
      throw new Error(`Asset '${key}' not found in hyperspectral scene ${result.id}`);
    }

    const filename = `${result.id}_${key}.tif`;
    const destPath = path.join(targetDir, filename);

    await this.streamDownload(asset.href, destPath, authHeaders);
    return destPath;
  }
}

