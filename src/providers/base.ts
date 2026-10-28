import * as fs from "fs";
import * as path from "path";
import { AOI, SearchResult, Asset, Category, FilterOptions } from "../types.js";
import { config } from "../config.js";

export interface DownloadOptions {
  resume?: boolean;
  multipart?: boolean;
  concurrency?: number;
  minMultipartSize?: number;
}

function formatBytes(bytes: number): string {
  if (bytes <= 0) return "0 B";
  const units = ["B", "KB", "MB", "GB", "TB"];
  let val = bytes;
  let idx = 0;
  while (val >= 1024 && idx < units.length - 1) {
    val /= 1024;
    idx++;
  }
  return `${val.toFixed(1)} ${units[idx]}`;
}

function updateProgress(transferred: number, total: number, label: string) {
  if (!process.stdout.isTTY) return;
  const barWidth = 20;
  const percent = total > 0 ? Math.min(100, Math.floor((transferred / total) * 100)) : 0;
  const filled = total > 0 ? Math.min(barWidth, Math.floor((transferred / total) * barWidth)) : 0;
  const bar = "=".repeat(filled) + (filled < barWidth ? ">" : "") + " ".repeat(Math.max(0, barWidth - filled - (filled < barWidth ? 1 : 0)));
  const sizeInfo = total > 0 ? `${formatBytes(transferred)} / ${formatBytes(total)}` : formatBytes(transferred);
  const cleanLabel = (label.length > 20 ? label.slice(0, 17) + "..." : label).padEnd(20);
  process.stdout.write(`\r${cleanLabel} [${bar}] ${percent.toString().padStart(3)}% (${sizeInfo})`);
}

function finishProgress(label: string, total: number) {
  if (!process.stdout.isTTY) return;
  const cleanLabel = (label.length > 20 ? label.slice(0, 17) + "..." : label).padEnd(20);
  const bar = "=".repeat(20);
  process.stdout.write(`\r${cleanLabel} [${bar}] 100% (${formatBytes(total)})\n`);
}

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
    outdir?: string,
    options?: DownloadOptions
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
    } else if (result.assets["dem"]) {
      asset = result.assets["dem"];
    } else if (result.assets["map"]) {
      asset = result.assets["map"];
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
    await this.streamDownload(asset.href, destPath, undefined, options);
    return destPath;
  }

  protected async multipartDownload(
    url: string,
    partPath: string,
    totalSize: number,
    headers: Record<string, string>,
    concurrency: number
  ): Promise<void> {
    // Pre-allocate part file
    const fileHandle = await fs.promises.open(partPath, "w+");
    await fileHandle.truncate(totalSize);

    const chunkSize = Math.ceil(totalSize / concurrency);
    const ranges: [number, number][] = [];
    for (let i = 0; i < concurrency; i++) {
      const start = i * chunkSize;
      const end = Math.min(totalSize - 1, (i + 1) * chunkSize - 1);
      if (start <= end) {
        ranges.push([start, end]);
      }
    }

    let completedBytes = 0;
    const desc = path.basename(partPath).replace(/\.part$/, "");

    try {
      await Promise.all(
        ranges.map(async ([start, end]) => {
          const rangeHeaders = { ...headers, Range: `bytes=${start}-${end}` };
          const res = await fetch(url, { headers: rangeHeaders });
          if (!res.ok || !res.body) {
            throw new Error(`Multipart range fetch failed (HTTP ${res.status})`);
          }
          const reader = res.body.getReader();
          let currentPos = start;
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            if (value) {
              const buf = Buffer.from(value);
              await fileHandle.write(buf, 0, buf.length, currentPos);
              currentPos += buf.length;
              completedBytes += buf.length;
              updateProgress(completedBytes, totalSize, desc);
            }
          }
        })
      );
      finishProgress(desc, totalSize);
    } finally {
      await fileHandle.close();
    }
  }

  protected async streamDownload(
    url: string,
    destPath: string,
    authHeaders?: Record<string, string>,
    options?: DownloadOptions
  ): Promise<void> {
    const resume = options?.resume ?? true;
    const multipart = options?.multipart ?? true;
    const concurrency = options?.concurrency ?? 4;
    const minMultipartSize = options?.minMultipartSize ?? (10 * 1024 * 1024);

    const headers: Record<string, string> = {
      "User-Agent": "OmniEarth-NodeSDK/1.1.0",
      ...authHeaders
    };

    const partPath = `${destPath}.part`;

    // 1. Probe remote content-length and range support via HEAD
    let totalSize = 0;
    let supportsRanges = false;
    try {
      const headRes = await fetch(url, { method: "HEAD", headers });
      if (headRes.ok) {
        const len = headRes.headers.get("content-length");
        if (len) totalSize = parseInt(len, 10);
        const acceptRanges = headRes.headers.get("accept-ranges")?.toLowerCase() || "";
        supportsRanges = acceptRanges.includes("bytes") || totalSize > 0;
      }
    } catch {
      // Continue to GET
    }

    // 2. Check if already fully downloaded
    if (fs.existsSync(destPath)) {
      const stat = fs.statSync(destPath);
      if ((totalSize > 0 && stat.size === totalSize) || (totalSize === 0 && stat.size > 0)) {
        return;
      }
    }

    // 3. Check existing part for resumption
    let existingPart = 0;
    if (fs.existsSync(partPath) && resume) {
      existingPart = fs.statSync(partPath).size;
    }

    // 4. Multipart download if eligible
    if (
      multipart &&
      concurrency > 1 &&
      supportsRanges &&
      totalSize >= minMultipartSize &&
      existingPart === 0
    ) {
      try {
        await this.multipartDownload(url, partPath, totalSize, headers, concurrency);
        fs.renameSync(partPath, destPath);
        return;
      } catch {
        if (fs.existsSync(partPath)) {
          try { fs.unlinkSync(partPath); } catch {}
        }
        existingPart = 0;
      }
    }

    // 5. Single-stream resumable download
    const reqHeaders = { ...headers };
    let isResume = false;
    if (existingPart > 0 && resume) {
      reqHeaders["Range"] = `bytes=${existingPart}-`;
    }

    let res = await fetch(url, { headers: reqHeaders });

    // Handle 416 Range Not Satisfiable
    if (res.status === 416) {
      existingPart = 0;
      delete reqHeaders["Range"];
      res = await fetch(url, { headers: reqHeaders });
    }

    if (!res.ok) {
      throw new Error(`Download failed (HTTP ${res.status}): ${res.statusText}`);
    }

    if (!res.body) {
      throw new Error(`Response body is empty for ${url}`);
    }

    if (res.status === 206) {
      isResume = true;
    } else {
      existingPart = 0;
    }

    const fileStream = fs.createWriteStream(partPath, { flags: isResume ? "a" : "w" });
    const reader = res.body.getReader();
    let currentBytes = existingPart;
    const desc = path.basename(destPath);

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      if (value) {
        fileStream.write(Buffer.from(value));
        currentBytes += value.length;
        updateProgress(currentBytes, totalSize || currentBytes, desc);
      }
    }

    await new Promise<void>((resolve, reject) => {
      fileStream.end(() => resolve());
      fileStream.on("error", reject);
    });

    finishProgress(desc, currentBytes);
    fs.renameSync(partPath, destPath);
  }
}

