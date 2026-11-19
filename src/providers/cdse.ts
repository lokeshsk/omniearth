import * as fs from "fs";
import * as path from "path";
import { AOI, SearchResult, Asset, Category, FilterOptions } from "../types.js";
import { BaseProvider, DownloadOptions } from "./base.js";
import { config } from "../config.js";

export const UUID_REGEX = /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/;

export const S2_BAND_PRESETS: Record<string, string[]> = {
  rgb: ["TCI", "B04", "B03", "B02"],
  tci: ["TCI"],
  vnir: ["B02", "B03", "B04", "B08"],
  ndvi: ["B04", "B08"],
  ndwi: ["B03", "B08"],
  swir: ["B11", "B12", "B8A"],
  scl: ["SCL"],
  "10m": ["B02", "B03", "B04", "B08", "TCI"],
  "20m": ["B05", "B06", "B07", "B8A", "B11", "B12", "SCL"],
  all: [
    "B01", "B02", "B03", "B04", "B05", "B06", "B07", "B08",
    "B8A", "B09", "B11", "B12", "TCI", "SCL", "AOT", "WVP"
  ]
};

export const S1_POLARIZATION_PRESETS: Record<string, string[]> = {
  vh: ["vh"],
  vv: ["vv"],
  dual: ["vh", "vv"],
  hh: ["hh"],
  hv: ["hv"],
  all: ["vh", "vv", "hh", "hv"]
};

export class CDSEAuthManager {
  private static IDENTITY_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token";
  private static TOKEN_LIFETIME_SEC = 540; // 9 minutes

  private token: string | null = null;
  private tokenTimestamp: number = 0;
  private username?: string;
  private password?: string;

  constructor(username?: string, password?: string) {
    this.username = username;
    this.password = password;
  }

  public getCredentials(): [string | undefined, string | undefined] {
    const [cfgU, cfgP] = config.cdseCredentials;
    const u = this.username || cfgU;
    const p = this.password || cfgP;
    return [u, p];
  }

  public async getToken(forceRefresh: boolean = false): Promise<string> {
    const [u, p] = this.getCredentials();
    if (!u || !p) {
      throw new Error(
        "Missing CDSE credentials for official Copernicus download. " +
        "Set CDSE_USERNAME and CDSE_PASSWORD (or SENTINEL_USER and SENTINEL_PASS) in .env " +
        "or pass them to OmniEarth. Free registration: https://dataspace.copernicus.eu/"
      );
    }

    const now = Date.now() / 1000;
    if (!forceRefresh && this.token && now - this.tokenTimestamp < CDSEAuthManager.TOKEN_LIFETIME_SEC) {
      return this.token;
    }

    try {
      const body = new URLSearchParams({
        grant_type: "password",
        username: u,
        password: p,
        client_id: "cdse-public"
      });

      const res = await fetch(CDSEAuthManager.IDENTITY_URL, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: body.toString()
      });

      if (res.status === 400 || res.status === 401) {
        throw new Error(
          `CDSE authentication failed (${res.status}): Invalid username or password. ` +
          "Please verify your credentials at https://dataspace.copernicus.eu/"
        );
      }

      if (!res.ok) {
        throw new Error(`CDSE auth request failed with HTTP ${res.status}`);
      }

      const data = (await res.json()) as any;
      if (!data.access_token) {
        throw new Error("CDSE authentication response did not contain an access_token.");
      }
      this.token = data.access_token;
      this.tokenTimestamp = Date.now() / 1000;
      return this.token!;
    } catch (err) {
      if (err instanceof Error && err.message.includes("CDSE authentication failed")) {
        throw err;
      }
      throw new Error(`Network error connecting to CDSE authentication service: ${(err as Error).message}`);
    }
  }
}

export class CDSEProvider extends BaseProvider {
  category: Category = Category.OPTICAL;
  name: string = "cdse";

  public static CATALOGUE_URL = "https://catalogue.dataspace.copernicus.eu/odata/v1";
  public static DOWNLOAD_URL = "https://download.dataspace.copernicus.eu/odata/v1";
  public static STAC_URL = "https://stac.dataspace.copernicus.eu/v1";

  public auth: CDSEAuthManager;

  constructor(authManager?: CDSEAuthManager) {
    super();
    this.auth = authManager || new CDSEAuthManager();
  }

  private async apiGet(url: string, params?: Record<string, any>): Promise<any> {
    let token = await this.auth.getToken();
    const query = params ? "?" + new URLSearchParams(params).toString() : "";
    let res = await fetch(url + query, {
      headers: {
        Authorization: `Bearer ${token}`,
        Accept: "application/json"
      }
    });

    if (res.status === 401 || res.status === 403) {
      token = await this.auth.getToken(true);
      res = await fetch(url + query, {
        headers: {
          Authorization: `Bearer ${token}`,
          Accept: "application/json"
        }
      });
    }

    if (!res.ok) {
      throw new Error(`CDSE API request failed (HTTP ${res.status}): ${res.statusText}`);
    }
    return res.json();
  }

  private extractValues(jsonData: any): any[] {
    if (jsonData && typeof jsonData === "object") {
      if (Array.isArray(jsonData.value)) return jsonData.value;
      if (Array.isArray(jsonData.result)) return jsonData.result;
      if (Array.isArray(jsonData)) return jsonData;
      return [jsonData];
    }
    return [];
  }

  private resolveCollection(category: Category, requested?: string): string {
    if (requested) {
      const up = requested.toUpperCase();
      if (up === "SENTINEL-1" || up === "S1") return "SENTINEL-1";
      if (up === "SENTINEL-2" || up === "S2") return "SENTINEL-2";
      if (up === "SENTINEL-3" || up === "S3") return "SENTINEL-3";
      if (up === "SENTINEL-5P" || up === "S5P") return "SENTINEL-5P";
      return up;
    }
    if (category === Category.SAR) return "SENTINEL-1";
    if (category === Category.OCEAN) return "SENTINEL-3";
    if (category === Category.ATMOSPHERE) return "SENTINEL-5P";
    return "SENTINEL-2";
  }

  async search(
    aoi: AOI,
    startDate?: string,
    endDate?: string,
    filters?: FilterOptions
  ): Promise<SearchResult[]> {
    const limit = filters?.limit ?? 10;
    const collection = this.resolveCollection(this.category, filters?.dataset);

    try {
      return await this.searchSTAC(aoi, collection, startDate, endDate, filters, limit);
    } catch {
      return await this.searchOData(aoi, collection, startDate, endDate, filters, limit);
    }
  }

  private async searchSTAC(
    aoi: AOI,
    collection: string,
    startDate?: string,
    endDate?: string,
    filters?: FilterOptions,
    limit: number = 10
  ): Promise<SearchResult[]> {
    const searchUrl = `${CDSEProvider.STAC_URL}/search`;
    const payload: Record<string, any> = {
      collections: [collection],
      limit
    };
    if (aoi && aoi.bbox) {
      payload.bbox = aoi.bbox;
    }
    if (startDate && endDate) {
      const s = startDate.includes("T") ? startDate : `${startDate}T00:00:00Z`;
      const e = endDate.includes("T") ? endDate : `${endDate}T23:59:59Z`;
      payload.datetime = `${s}/${e}`;
    } else if (startDate) {
      const s = startDate.includes("T") ? startDate : `${startDate}T00:00:00Z`;
      payload.datetime = `${s}/..`;
    } else if (endDate) {
      const e = endDate.includes("T") ? endDate : `${endDate}T23:59:59Z`;
      payload.datetime = `../${e}`;
    }

    if (filters && filters.maxCloudCover !== undefined) {
      payload.query = { "eo:cloud_cover": { lte: filters.maxCloudCover } };
    }

    let token: string | undefined;
    try {
      token = await this.auth.getToken();
    } catch {}

    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (token) headers["Authorization"] = `Bearer ${token}`;

    const res = await fetch(searchUrl, {
      method: "POST",
      headers,
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error(`STAC search failed HTTP ${res.status}`);

    const data = (await res.json()) as any;
    const features = data.features || [];

    return features.map((feat: any): SearchResult => {
      const props = feat.properties || {};
      const featId = feat.id || "";
      const cdseId = props.id || featId;
      const productName = props.title || featId;
      const cloud = props["eo:cloud_cover"];
      const dt = props.datetime;
      const bbox = feat.bbox || aoi.bbox;

      const assetsDict: Record<string, Asset> = {};
      for (const [k, a] of Object.entries<any>(feat.assets || {})) {
        assetsDict[k] = {
          key: k,
          href: a.href || "",
          title: a.title || k,
          media_type: a.type,
          roles: a.roles || []
        };
      }

      if (!assetsDict["full"] && !assetsDict["safe"]) {
        assetsDict["full"] = {
          key: "full",
          href: `${CDSEProvider.DOWNLOAD_URL}/Products(${cdseId})/$value`,
          title: `${productName}.zip`,
          media_type: "application/zip",
          roles: ["archive", "safe"]
        };
      }

      return {
        id: productName,
        collection,
        category: this.category,
        provider: "cdse",
        datetime: dt,
        bbox,
        properties: {
          cdse_id: cdseId,
          title: productName,
          cloud_cover: cloud,
          geometry: feat.geometry
        },
        assets: assetsDict
      };
    });
  }

  private async searchOData(
    aoi: AOI,
    collection: string,
    startDate?: string,
    endDate?: string,
    filters?: FilterOptions,
    limit: number = 10
  ): Promise<SearchResult[]> {
    const filterParts = [`Collection/Name eq '${collection}'`];
    if (startDate) {
      const s = startDate.includes("T") ? startDate : `${startDate}T00:00:00.000Z`;
      filterParts.push(`ContentDate/Start ge ${s}`);
    }
    if (endDate) {
      const e = endDate.includes("T") ? endDate : `${endDate}T23:59:59.999Z`;
      filterParts.push(`ContentDate/Start le ${e}`);
    }
    if (aoi && aoi.bbox) {
      const [min_lon, min_lat, max_lon, max_lat] = aoi.bbox;
      const polyWkt = `POLYGON((${min_lon} ${min_lat}, ${max_lon} ${min_lat}, ${max_lon} ${max_lat}, ${min_lon} ${max_lat}, ${min_lon} ${min_lat}))`;
      filterParts.push(`OData.CSC.Intersects(area=geography'SRID=4326;${polyWkt}')`);
    }
    if (filters && filters.maxCloudCover !== undefined) {
      filterParts.push(
        `Attributes/OData.CSC.DoubleAttribute/any(att:att/Name eq 'cloudCover' and att/OData.CSC.DoubleAttribute/Value le ${filters.maxCloudCover})`
      );
    }

    const params = {
      $filter: filterParts.join(" and "),
      $top: limit.toString(),
      $orderby: "ContentDate/Start desc",
      $expand: "Attributes,Checksum"
    };

    const data = await this.apiGet(`${CDSEProvider.CATALOGUE_URL}/Products`, params);
    const items = this.extractValues(data);
    return items.map((it) => this.buildSearchResultFromOData(it, collection));
  }

  private buildSearchResultFromOData(data: any, collection: string): SearchResult {
    const productId = data.Id || "";
    const productName = data.Name || "";
    let checksumVal: string | undefined;
    let checksumAlgo = "MD5";
    const chkList = data.Checksum || [];
    if (Array.isArray(chkList) && chkList.length > 0) {
      checksumVal = chkList[0].Value;
      checksumAlgo = chkList[0].Algorithm || "MD5";
    }

    let cloud: number | undefined;
    for (const att of data.Attributes || []) {
      if (att.Name === "cloudCover") {
        cloud = parseFloat(att.Value || "0");
        break;
      }
    }

    const assetsDict: Record<string, Asset> = {
      full: {
        key: "full",
        href: `${CDSEProvider.DOWNLOAD_URL}/Products(${productId})/$value`,
        title: `${productName}.zip`,
        media_type: "application/zip",
        size_bytes: data.ContentLength,
        roles: ["archive", "safe"],
        checksum: checksumVal,
        checksum_algorithm: checksumAlgo
      }
    };

    const contentDate = data.ContentDate || {};
    const dt = contentDate.Start || data.PublicationDate;

    return {
      id: productName,
      collection,
      category: this.category,
      provider: "cdse",
      datetime: dt,
      checksum: checksumVal,
      checksum_algorithm: checksumAlgo,
      properties: {
        cdse_id: productId,
        title: productName,
        cloud_cover: cloud,
        checksum: checksumVal,
        checksum_algorithm: checksumAlgo,
        content_length: data.ContentLength,
        geometry: data.GeoFootprint
      },
      assets: assetsDict
    };
  }

  async getItem(itemId: string): Promise<SearchResult | null> {
    const cleanId = itemId.trim();
    try {
      if (UUID_REGEX.test(cleanId)) {
        const url = `${CDSEProvider.CATALOGUE_URL}/Products(${cleanId})`;
        const data = await this.apiGet(url, { $expand: "Attributes,Checksum" });
        const collection = data.Collection?.Name || "SENTINEL-2";
        return this.buildSearchResultFromOData(data, collection);
      }

      const url = `${CDSEProvider.CATALOGUE_URL}/Products`;
      const data = await this.apiGet(url, {
        $filter: `Name eq '${cleanId}'`,
        $expand: "Attributes,Checksum"
      });
      const items = this.extractValues(data);
      if (items.length > 0) {
        const collection = items[0].Collection?.Name || "SENTINEL-2";
        return this.buildSearchResultFromOData(items[0], collection);
      }
    } catch {}
    return null;
  }

  private async findFilesRecursive(node: any): Promise<any[]> {
    const files: any[] = [];
    const nodesUri = node.Nodes?.uri;

    if (!nodesUri) {
      const nodeId = node.Id;
      files.push({
        id: nodeId,
        name: node.Name || "",
        download_url: `${CDSEProvider.CATALOGUE_URL}/Nodes(${nodeId})/$value`,
        size_bytes: node.ContentLength || 0
      });
      return files;
    }

    const childResponse = await this.apiGet(nodesUri);
    const children = this.extractValues(childResponse);

    for (const child of children) {
      if ((child.ChildrenNumber || 0) === 0) {
        const childUri = child.Nodes?.uri || "";
        const downloadUrl = childUri ? childUri.replace(/\/Nodes$/, "/$value") : `${CDSEProvider.CATALOGUE_URL}/Nodes(${child.Id})/$value`;
        files.push({
          id: child.Id || "",
          name: child.Name || "",
          download_url: downloadUrl,
          size_bytes: child.ContentLength || 0
        });
      } else {
        const rec = await this.findFilesRecursive(child);
        files.push(...rec);
      }
    }
    return files;
  }

  public async listProductFiles(productIdOrName: string): Promise<any[]> {
    const item = await this.getItem(productIdOrName);
    if (!item) {
      throw new Error(`Product '${productIdOrName}' not found on CDSE.`);
    }
    const cdseId = item.properties?.cdse_id || item.id;
    const rootUrl = `${CDSEProvider.CATALOGUE_URL}/Products(${cdseId})/Nodes`;
    const rootNodes = this.extractValues(await this.apiGet(rootUrl));
    const files: any[] = [];
    for (const rootNode of rootNodes) {
      const rec = await this.findFilesRecursive(rootNode);
      files.push(...rec);
    }
    return files;
  }

  public resolveRequestedBands(requested?: string, mission: string = "sentinel2"): string[] {
    if (!requested) {
      return mission === "sentinel2" ? S2_BAND_PRESETS["rgb"] : S1_POLARIZATION_PRESETS["dual"];
    }
    const clean = requested.trim().toLowerCase();
    if (mission === "sentinel2" && S2_BAND_PRESETS[clean]) {
      return S2_BAND_PRESETS[clean];
    }
    if (mission === "sentinel1" && S1_POLARIZATION_PRESETS[clean]) {
      return S1_POLARIZATION_PRESETS[clean];
    }
    return requested.split(",").map((b) => b.trim()).filter(Boolean);
  }

  public async findFilesForBands(productIdOrName: string, requestedBands?: string): Promise<any[]> {
    const allFiles = await this.listProductFiles(productIdOrName);
    const isS1 = productIdOrName.toUpperCase().includes("S1");
    const mission = isS1 ? "sentinel1" : "sentinel2";
    const targetBands = this.resolveRequestedBands(requestedBands, mission).map((b) => b.toLowerCase());

    const matched: any[] = [];
    for (const pfile of allFiles) {
      const fname = (pfile.name || "").toLowerCase();
      if (!isS1) {
        if (fname.endsWith(".jp2")) {
          for (const band of targetBands) {
            if (fname.includes(`_${band}_`) || fname.includes(`_${band}.`) || fname.startsWith(`${band}_`)) {
              if (!matched.some((m) => m.id === pfile.id)) {
                matched.push(pfile);
              }
            }
          }
        }
      } else {
        if (fname.endsWith(".tiff") || fname.endsWith(".tif")) {
          for (const pol of targetBands) {
            if (fname.includes(`-${pol}-`) || fname.includes(`_${pol}_`) || fname.includes(pol)) {
              if (!matched.some((m) => m.id === pfile.id)) {
                matched.push(pfile);
              }
            }
          }
        }
      }
    }
    return matched;
  }

  async download(
    result: SearchResult,
    assetKey?: string,
    outdir?: string,
    options?: DownloadOptions
  ): Promise<string> {
    const targetDir = outdir || config.defaultOutdir;
    if (!fs.existsSync(targetDir)) {
      fs.mkdirSync(targetDir, { recursive: true });
    }

    const token = await this.auth.getToken();
    const headers = { Authorization: `Bearer ${token}` };

    const bandsStr = Array.isArray(options?.bands) ? options.bands.join(",") : options?.bands;
    if (options?.format === "node" || options?.format === "band" || bandsStr) {
      const cdseId = result.properties?.cdse_id || result.id;
      const matchedFiles = await this.findFilesForBands(cdseId, bandsStr);
      if (matchedFiles.length === 0) {
        throw new Error(`No matching band files found for '${bandsStr}' in product '${result.id}'`);
      }
      const productFolder = path.join(targetDir, result.id);
      if (!fs.existsSync(productFolder)) {
        fs.mkdirSync(productFolder, { recursive: true });
      }

      const dlPaths: string[] = [];
      for (const f of matchedFiles) {
        const outpath = path.join(productFolder, f.name);
        await this.streamDownload(f.download_url, outpath, headers, options);
        dlPaths.push(outpath);
      }
      return dlPaths.length === 1 ? dlPaths[0] : productFolder;
    }

    const targetAsset = result.assets?.[assetKey || "full"] || result.assets?.["safe"];
    const cdseId = result.properties?.cdse_id || result.id;
    const dlUrl = targetAsset?.href || `${CDSEProvider.DOWNLOAD_URL}/Products(${cdseId})/$value`;

    const outFilename = result.id.endsWith(".zip") ? result.id : `${result.id}.zip`;
    const outpath = path.join(targetDir, outFilename);

    const downloadOpts: DownloadOptions = {
      ...options,
      expectedChecksum: result.checksum || result.properties?.checksum,
      checksumAlgorithm: result.checksum_algorithm || result.properties?.checksum_algorithm || "MD5",
      verifyChecksum: options?.verifyChecksum ?? false
    };

    await this.streamDownload(dlUrl, outpath, headers, downloadOpts);
    return outpath;
  }
}
