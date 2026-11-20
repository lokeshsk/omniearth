/**
 * OmniEarth Version & Update Notification Engine (Node.js & TypeScript)
 * ====================================================================
 * Provides non-blocking, cached version checks against the npm registry
 * to notify users of new releases and new features across SDK and CLI usage.
 */

import * as fs from "fs";
import * as path from "path";
import * as os from "os";

const DEFAULT_CACHE_DIR = path.join(os.homedir(), ".cache", "omniearth");
const CACHE_FILE_NAME = "npm_version_check.json";
const NPM_REGISTRY_URL = "https://registry.npmjs.org/omniearth/latest";
const CHECK_INTERVAL_MS = 86400000; // 24 hours

let _sessionNotified = false;

export interface VersionCheckOptions {
  cacheDir?: string;
  jsonMode?: boolean;
  forceCheck?: boolean;
  isCli?: boolean;
  timeoutMs?: number;
}

export function parseSemver(v: string): number[] {
  return v
    .replace(/^v/, "")
    .split(".")
    .map((num) => parseInt(num, 10) || 0);
}

export function isNewerVersion(latest: string, current: string): boolean {
  const l = parseSemver(latest);
  const c = parseSemver(current);
  for (let i = 0; i < Math.max(l.length, c.length); i++) {
    const lPart = l[i] || 0;
    const cPart = c[i] || 0;
    if (lPart > cPart) return true;
    if (lPart < cPart) return false;
  }
  return false;
}

export function isCheckDisabled(jsonMode = false, forceCheck = false): boolean {
  if (forceCheck) return false;
  if (jsonMode) return true;

  const optOut = (process.env.OMNIEARTH_NO_UPDATE_CHECK || "").trim().toLowerCase();
  if (["1", "true", "yes", "on"].includes(optOut)) return true;

  const ci = (process.env.CI || "").trim().toLowerCase();
  if (["1", "true", "yes"].includes(ci)) return true;

  if (!process.stderr.isTTY) return true;

  return false;
}

export function getCachedVersion(cachePath: string, ttl = CHECK_INTERVAL_MS): string | null {
  try {
    if (fs.existsSync(cachePath)) {
      const data = JSON.parse(fs.readFileSync(cachePath, "utf-8"));
      const lastChecked = Number(data.last_checked || 0);
      if (Date.now() - lastChecked < ttl) {
        return data.latest_version || null;
      }
    }
  } catch {
    // Ignore cache read failures
  }
  return null;
}

export function writeCachedVersion(cachePath: string, latestVersion: string): void {
  try {
    fs.mkdirSync(path.dirname(cachePath), { recursive: true });
    const data = {
      last_checked: Date.now(),
      latest_version: latestVersion,
    };
    fs.writeFileSync(cachePath, JSON.stringify(data), "utf-8");
  } catch {
    // Ignore cache write failures
  }
}

export async function fetchLatestNpmVersion(timeoutMs = 1500): Promise<string | null> {
  try {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    const resp = await fetch(NPM_REGISTRY_URL, {
      signal: controller.signal,
      headers: { Accept: "application/json" },
    });
    clearTimeout(timer);
    if (resp.ok) {
      const data = (await resp.json()) as { version?: string };
      return data.version || null;
    }
  } catch {
    // Silent fail on timeout or network errors
  }
  return null;
}

export function formatUpdateBanner(currentVersion: string, latestVersion: string, isCli = true): string {
  if (isCli) {
    const lines = [
      `OmniEarth update available: ${currentVersion} -> ${latestVersion}`,
      "To view new features: run 'npx omniearth whatsnew'",
      "To upgrade: npm install -g omniearth@latest (or 'pnpm add -g omniearth')",
      "Release Notes: https://github.com/lokeshsk/omniearth/releases",
    ];
    const maxLen = Math.max(...lines.map((l) => l.length)) + 2;
    const borderTop = "┌" + "─".repeat(maxLen) + "┐";
    const borderBot = "└" + "─".repeat(maxLen) + "┘";
    const content = lines.map((l) => `│  ${l.padEnd(maxLen - 2)}│`).join("\n");
    return `\n${borderTop}\n${content}\n${borderBot}\n`;
  } else {
    return (
      `[omniearth] A newer version v${latestVersion} is available (installed: v${currentVersion}).\n` +
      `Run 'whatsNew()' or visit https://github.com/lokeshsk/omniearth/releases to view new features.\n`
    );
  }
}

export async function checkForUpdates(
  currentVersion: string,
  options: VersionCheckOptions = {}
): Promise<string | null> {
  const {
    cacheDir = DEFAULT_CACHE_DIR,
    jsonMode = false,
    forceCheck = false,
    isCli = true,
    timeoutMs = 1500,
  } = options;

  if (isCheckDisabled(jsonMode, forceCheck)) return null;
  if (_sessionNotified && !forceCheck) return null;

  const cachePath = path.join(cacheDir, CACHE_FILE_NAME);
  let latestVersion = getCachedVersion(cachePath);

  if (!latestVersion) {
    latestVersion = await fetchLatestNpmVersion(timeoutMs);
    if (latestVersion) {
      writeCachedVersion(cachePath, latestVersion);
    }
  }

  if (latestVersion && isNewerVersion(latestVersion, currentVersion)) {
    const banner = formatUpdateBanner(currentVersion, latestVersion, isCli);
    process.stderr.write(banner);
    _sessionNotified = true;
    return latestVersion;
  }

  return null;
}

export function getWhatsNew(): string {
  return (
    "# OmniEarth - What's New\n\n" +
    "- Direct Hyperspectral Provider & Dataset Routing (NASA EMIT, DLR EnMAP)\n" +
    "- Interchangeable Elevation Flags (Copernicus DEM, SRTM, ALOS)\n" +
    "- Universal Semantic Asset Aliasing & Interactive Terminal Picker (-i)\n" +
    "- Dedicated Scene Folder Packaging (--folder) & Direct ZIP Bundling (--zip)\n" +
    "- Parallel Asset URL Deduplication\n\n" +
    "Full Release Notes: https://github.com/lokeshsk/omniearth/releases\n" +
    "Changelog: https://github.com/lokeshsk/omniearth/blob/main/CHANGELOG.md"
  );
}

export function whatsNew(): void {
  const summary = getWhatsNew();
  console.log("=".repeat(76));
  console.log(" OmniEarth - Latest Features & Release Highlights");
  console.log("=".repeat(76));
  console.log(summary);
  console.log("=".repeat(76));
  console.log("Subscribe to releases: https://github.com/lokeshsk/omniearth/releases");
  console.log("npm Release Feed: https://www.npmjs.com/package/omniearth");
  console.log("=".repeat(76));
}
