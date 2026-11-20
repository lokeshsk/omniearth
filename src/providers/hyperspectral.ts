import * as fs from "fs";
import * as path from "path";
import { BaseProvider } from "./base.js";
import { AOI, SearchResult, Asset, Category, FilterOptions, resolveAssetKey } from "../types.js";
import { config } from "../config.js";

export class HyperspectralProvider extends BaseProvider {
  category = Category.HYPERSPECTRAL;
  name = "hyperspectral";

  private enmapStacUrl = "https://geoservice.dlr.de/eoc/ogc/stac/collections/ENMAP_HSI_L2A/items";
  private emitStacUrl = "https://cmr.earthdata.nasa.gov/stac/LPCLOUD/search";

  async search(
    aoi: AOI,
    startDate?: string,
    endDate?: string,
    filters?: FilterOptions
  ): Promise<SearchResult[]> {
    const limit = filters?.limit || 10;
    const target = (filters?.provider || filters?.dataset || "").toLowerCase();

    if (target.includes("prisma")) {
      return this.queryPrisma(aoi, startDate, endDate, limit);
    }
    if (target.includes("enmap")) {
      return this.queryEnmap(aoi, startDate, endDate, limit);
    }
    if (target.includes("emit")) {
      return this.queryEmit(aoi, startDate, endDate, limit);
    }

    const enmapResults = await this.queryEnmap(aoi, startDate, endDate, limit);
    const emitResults = await this.queryEmit(aoi, startDate, endDate, limit);
    const results = [...enmapResults, ...emitResults];
    if (results.length < limit) {
      const prismaResults = await this.queryPrisma(aoi, startDate, endDate, limit - results.length);
      results.push(...prismaResults);
    }

    results.sort((a, b) => (b.datetime || "").localeCompare(a.datetime || ""));
    return results.slice(0, limit);
  }

  async queryEnmap(aoi: AOI, startDate?: string, endDate?: string, limit: number = 10): Promise<SearchResult[]> {
    const results: SearchResult[] = [];
    try {
      const bboxStr = `${aoi.bbox[0]},${aoi.bbox[1]},${aoi.bbox[2]},${aoi.bbox[3]}`;
      const params = new URLSearchParams({
        bbox: bboxStr,
        limit: String(limit)
      });
      if (startDate && endDate) {
        params.append("datetime", `${startDate}T00:00:00Z/${endDate}T23:59:59Z`);
      } else if (startDate) {
        params.append("datetime", `${startDate}T00:00:00Z/..`);
      } else if (endDate) {
        params.append("datetime", `../${endDate}T23:59:59Z`);
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
      // Continue
    }
    return results;
  }

  async queryEmit(aoi: AOI, startDate?: string, endDate?: string, limit: number = 10): Promise<SearchResult[]> {
    const results: SearchResult[] = [];
    try {
      const payload: Record<string, any> = {
        collections: ["EMITL2ARFL_001"],
        bbox: aoi.bbox,
        limit,
        sortby: [{ field: "properties.datetime", direction: "desc" }]
      };
      if (startDate && endDate) {
        payload.datetime = `${startDate}T00:00:00Z/${endDate}T23:59:59Z`;
      } else if (startDate) {
        payload.datetime = `${startDate}T00:00:00Z/..`;
      } else if (endDate) {
        payload.datetime = `../${endDate}T23:59:59Z`;
      }

      const res = await fetch(this.emitStacUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
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
    return results;
  }

  async queryPrisma(aoi: AOI, startDate?: string, endDate?: string, limit: number = 10): Promise<SearchResult[]> {
    const results: SearchResult[] = [];
    try {
      const bboxStr = `${aoi.bbox[0]},${aoi.bbox[1]},${aoi.bbox[2]},${aoi.bbox[3]}`;
      const params = new URLSearchParams({
        bbox: bboxStr,
        limit: String(limit)
      });
      if (startDate) params.append("start", startDate);
      if (endDate) params.append("end", endDate);

      const headers: Record<string, string> = {};
      const [u, p] = config.prismaCredentials;
      if (u && p) {
        headers["Authorization"] = `Basic ${Buffer.from(`${u}:${p}`).toString("base64")}`;
      }

      const res = await fetch(`https://prisma.asi.it/api/v1/search?${params.toString()}`, { headers });
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
            collection: "asi-prisma-l2d",
            category: this.category,
            provider: "asi_prisma",
            datetime: feat.properties?.datetime,
            bbox: feat.bbox,
            properties: { ...feat.properties, platform: "prisma" },
            assets
          });
        }
      }
    } catch {
      // Handled
    }
    return results;
  }

  override async getItem(itemId: string): Promise<SearchResult | null> {
    // 1. DLR EnMAP STAC direct item endpoint
    if (itemId.startsWith("ENMAP") || itemId.includes("ENMAP")) {
      try {
        const res = await fetch(`${this.enmapStacUrl}/${itemId}`);
        if (res.ok) {
          const feat = await res.json();
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
          return {
            id: feat.id,
            collection: "enmap-hsi-l2a",
            category: this.category,
            provider: "dlr_enmap",
            datetime: feat.properties?.datetime,
            bbox: feat.bbox,
            properties: { ...feat.properties, platform: "enmap" },
            assets
          };
        }
      } catch {
        // Fallback
      }
    }

    // 2. NASA EMIT STAC direct item endpoint
    if (itemId.startsWith("EMIT") || itemId.includes("EMIT")) {
      try {
        const res = await fetch(`https://cmr.earthdata.nasa.gov/stac/LPCLOUD/collections/EMITL2ARFL_001/items/${itemId}`);
        if (res.ok) {
          const feat = await res.json();
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
          return {
            id: feat.id,
            collection: "emit-l2a-rfl",
            category: this.category,
            provider: "nasa_emit",
            datetime: feat.properties?.datetime,
            bbox: feat.bbox,
            properties: { ...feat.properties, platform: "emit" },
            assets
          };
        }
      } catch {
        // Fallback
      }
    }

    return null;
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

    let providerName = result.provider;
    if (providerName === "hyperspectral") {
      if (result.id.startsWith("ENMAP") || result.id.includes("ENMAP")) {
        providerName = "dlr_enmap";
      } else if (result.id.startsWith("EMIT") || result.id.includes("EMIT")) {
        providerName = "nasa_emit";
      } else if (result.id.startsWith("PRS") || result.id.includes("PRISMA")) {
        providerName = "asi_prisma";
      }
    }

    let authHeaders: Record<string, string> | undefined;
    if (providerName === "dlr_enmap") {
      const [u, p] = config.dlrCredentials;
      if (u && p) {
        const token = Buffer.from(`${u}:${p}`).toString("base64");
        authHeaders = { Authorization: `Basic ${token}` };
      }
    }

    const resolvedKey = resolveAssetKey(result, assetKey);
    const key = resolvedKey || assetKey || "data";
    const asset = (resolvedKey ? result.assets[resolvedKey] : undefined) || result.assets[key] || result.assets["data"] || Object.values(result.assets)[0];

    if (!asset || !asset.href) {
      throw new Error(`Asset '${key}' not found in hyperspectral scene ${result.id}`);
    }

    const ext = path.extname(asset.href.split("?")[0]) || ".nc";
    const baseKey = path.basename(key) || key.replace(/\//g, "_");
    const filename = baseKey.endsWith(ext)
      ? (baseKey.startsWith(result.id) ? baseKey : `${result.id}_${baseKey}`)
      : (baseKey.startsWith(result.id) ? `${baseKey}${ext}` : `${result.id}_${baseKey}${ext}`);
    const destPath = path.join(targetDir, filename);

    await this.streamDownload(asset.href, destPath, authHeaders);
    return destPath;
  }
}

