import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import * as dotenv from "dotenv";

export class Config {
  constructor(customPath?: string) {
    this.loadEnvironment(customPath);
  }

  public loadEnvironment(customPath?: string): void {
    const candidates: string[] = [];
    if (customPath) {
      candidates.push(customPath);
    }
    candidates.push(path.join(process.cwd(), ".env"));
    candidates.push(path.join(process.cwd(), "..", ".env"));
    candidates.push("/home/ubuntu/Documents/agri/.env");
    candidates.push(path.join(os.homedir(), ".omniearth", ".env"));

    for (const p of candidates) {
      if (fs.existsSync(p) && fs.statSync(p).isFile()) {
        dotenv.config({ path: p });
        break;
      }
    }
  }

  public get(key: string, defaultValue?: string): string | undefined {
    return process.env[key] ?? defaultValue;
  }

  public get dlrCredentials(): [string | undefined, string | undefined] {
    const u = process.env.DLR_USERNAME || process.env.EOWEB_USERNAME || process.env.DLR_USER;
    const p = process.env.DLR_PASSWORD || process.env.EOWEB_PASSWORD || process.env.DLR_PASS;
    return [u, p];
  }

  public get prismaCredentials(): [string | undefined, string | undefined] {
    const u = process.env.PRISMA_USERNAME || process.env.ASI_USERNAME;
    const p = process.env.PRISMA_PASSWORD || process.env.ASI_PASSWORD;
    return [u, p];
  }

  public get earthdataCredentials(): [string | undefined, string | undefined] {
    const u = process.env.EARTHDATA_USERNAME || process.env.NASA_USERNAME;
    const p = process.env.EARTHDATA_PASSWORD || process.env.NASA_PASSWORD;
    return [u, p];
  }

  public get defaultOutdir(): string {
    return process.env.OMNIEARTH_DEFAULT_OUTDIR || "./omniearth_downloads";
  }

  public get timeoutMs(): number {
    return parseInt(process.env.OMNIEARTH_TIMEOUT_SEC || "30", 10) * 1000;
  }
}

export const config = new Config();
