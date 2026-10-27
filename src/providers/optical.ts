import { BaseProvider } from "./base.js";
import { AOI, SearchResult, Asset, Category, FilterOptions } from "../types.js";

export class OpticalProvider extends BaseProvider {
  category = Category.OPTICAL;
  name = "optical";

  private stacEndpoint = "https://earth-search.aws.element84.com/v1/search";

  async search(
    aoi: AOI,
    startDate?: string,
    endDate?: string,
    filters?: FilterOptions
  ): Promise<SearchResult[]> {
    const payload: Record<string, any> = {
      collections: ["sentinel-2-l2a"],
      bbox: aoi.bbox,
      limit: filters?.limit || 10
    };

    if (startDate && endDate) {
      payload.datetime = `${startDate}T00:00:00Z/${endDate}T23:59:59Z`;
    }

    const query: Record<string, any> = {};
    if (filters?.maxCloudCover !== undefined) {
      query["eo:cloud_cover"] = { lte: filters.maxCloudCover };
    }
    if (Object.keys(query).length > 0) {
      payload.query = query;
    }

    const res = await fetch(this.stacEndpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      throw new Error(`Optical STAC search failed (HTTP ${res.status})`);
    }

    const data = await res.json();
    const results: SearchResult[] = [];

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
        collection: feat.collection || "sentinel-2-l2a",
        category: this.category,
        provider: "aws_earth_search",
        datetime: feat.properties?.datetime,
        bbox: feat.bbox,
        properties: feat.properties || {},
        assets
      });
    }

    return results;
  }
}
