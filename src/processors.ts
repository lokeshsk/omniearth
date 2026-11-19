import * as fs from "fs";
import * as path from "path";

/**
 * OmniEarth Geospatial Processors (TypeScript)
 * Provides file discovery and raster composite path helpers for True Color RGB,
 * False Color NIR, and SWIR imagery.
 */

export interface CompositeBands {
  red: string;
  green: string;
  blue: string;
}

export function findBandFile(files: string[], bandCode: string, altNames: string[]): string | undefined {
  const candidates = [bandCode.toLowerCase(), ...altNames.map((a) => a.toLowerCase())];
  for (const f of files) {
    const fname = path.basename(f).toLowerCase();
    const ext = path.extname(fname);
    if ([".jp2", ".tif", ".tiff"].includes(ext)) {
      for (const c of candidates) {
        if (
          fname.includes(`_${c}_`) ||
          fname.includes(`_${c}.`) ||
          fname.startsWith(`${c}_`) ||
          fname.startsWith(`${c}.`) ||
          fname.includes(`-${c}-`) ||
          fname.includes(`-${c}.`)
        ) {
          return f;
        }
      }
    }
  }
  return undefined;
}

export function resolveCompositeBands(
  directoryOrFiles: string | string[],
  compositeType: string = "rgb"
): CompositeBands {
  let files: string[] = [];
  if (Array.isArray(directoryOrFiles)) {
    files = directoryOrFiles;
  } else if (fs.existsSync(directoryOrFiles)) {
    if (fs.statSync(directoryOrFiles).isDirectory()) {
      files = fs.readdirSync(directoryOrFiles).map((f) => path.join(directoryOrFiles, f));
    } else {
      files = [directoryOrFiles];
    }
  }

  const cType = compositeType.toLowerCase();
  let bR: string | undefined;
  let bG: string | undefined;
  let bB: string | undefined;

  if (cType === "rgb" || cType === "true-color") {
    bR = findBandFile(files, "b04", ["red", "b4"]);
    bG = findBandFile(files, "b03", ["green", "b3"]);
    bB = findBandFile(files, "b02", ["blue", "b2"]);
  } else if (cType === "false-color" || cType === "cir") {
    bR = findBandFile(files, "b08", ["nir", "b8"]);
    bG = findBandFile(files, "b04", ["red", "b4"]);
    bB = findBandFile(files, "b03", ["green", "b3"]);
  } else if (cType === "swir" || cType === "geology") {
    bR = findBandFile(files, "b12", ["swir2", "b12"]);
    bG = findBandFile(files, "b8a", ["narrow_nir", "nir08"]);
    bB = findBandFile(files, "b04", ["red", "b4"]);
  } else {
    throw new Error(`Unsupported composite type: '${compositeType}'. Supported: 'rgb', 'false-color', 'swir'`);
  }

  if (!bR || !bG || !bB) {
    const missing: string[] = [];
    if (!bR) missing.push("Red/NIR band");
    if (!bG) missing.push("Green/Red band");
    if (!bB) missing.push("Blue/Green band");
    throw new Error(`Cannot create ${compositeType} composite: missing band file(s): ${missing.join(", ")}`);
  }

  return { red: bR, green: bG, blue: bB };
}

export function createCompositeFromDownloaded(
  directoryOrFiles: string | string[],
  compositeType: string = "rgb",
  outputPath?: string
): string {
  const bands = resolveCompositeBands(directoryOrFiles, compositeType);
  const dir = Array.isArray(directoryOrFiles)
    ? path.dirname(directoryOrFiles[0] || ".")
    : directoryOrFiles;
  const suffix = compositeType.toUpperCase().replace("-", "");
  const out = outputPath || path.join(dir, `${path.basename(dir)}_${suffix}.tif`);
  // Records the composite descriptor metadata alongside the band files
  const meta = {
    composite_type: compositeType,
    output_path: path.resolve(out),
    bands: {
      red: path.resolve(bands.red),
      green: path.resolve(bands.green),
      blue: path.resolve(bands.blue)
    },
    created_at: new Date().toISOString()
  };
  fs.writeFileSync(`${out}.meta.json`, JSON.stringify(meta, null, 2), "utf-8");
  return path.resolve(out);
}

