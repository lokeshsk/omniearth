import * as fs from "fs";
import * as path from "path";
import { AOI, SearchResult, Asset, Category, FilterOptions } from "../types.js";
import { config } from "../config.js";

export abstract class BaseProvider {
  abstract category: Category;
  abstract name: string;

  abstract search(
    aoi: AOI,
    startDate?: string,
    endDate?: string,
    filters?: FilterOptions
  ): Promise<SearchResult[]>;

  async download(
    result: SearchResult,
    assetKey?: string,
    outdir?: string
  ): Promise<string> {
    const targetDir = outdir || config.defaultOutdir;
    if (!fs.existsSync(targetDir)) {
      fs.mkdirSync(targetDir, { recursive: true });
    }

    let asset: Asset | undefined;
    if (assetKey && result.assets[assetKey]) {
      asset = result.assets[assetKey];
    } else if (result.assets["data"]) {
      asset = result.assets["data"];
    } else if (result.assets["visual"]) {
      asset = result.assets["visual"];
    } else if (result.assets["SPECTRAL_IMAGE_COG"]) {
      asset = result.assets["SPECTRAL_IMAGE_COG"];
    } else if (result.assets["image"]) {
      asset = result.assets["image"];
    } else {
      asset = Object.values(result.assets)[0];
    }

    if (!asset || !asset.href) {
      throw new Error(`No downloadable asset found for item '${result.id}'`);
    }

    const url = new URL(asset.href);
    let filename = path.basename(url.pathname);
    if (!filename || filename === "/") {
      filename = `${result.id}.dat`;
    }

    const destPath = path.join(targetDir, filename);
    await this.streamDownload(asset.href, destPath);
    return destPath;
  }

  protected async streamDownload(
    url: string,
    destPath: string,
    authHeaders?: Record<string, string>
  ): Promise<void> {
    const headers: Record<string, string> = {
      "User-Agent": "OmniEarth-NodeSDK/1.0.0",
      ...authHeaders
    };

    const res = await fetch(url, { headers });
    if (!res.ok) {
      throw new Error(`Download failed (HTTP ${res.status}): ${res.statusText}`);
    }

    if (!res.body) {
      throw new Error(`Response body is empty for ${url}`);
    }

    const fileStream = fs.createWriteStream(destPath);
    const reader = res.body.getReader();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      if (value) {
        fileStream.write(Buffer.from(value));
      }
    }
    fileStream.end();
  }
}
