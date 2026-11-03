/**
 * OmniEarth Spectral and Biophysical Index Engine (TypeScript)
 * ==========================================================
 * Computes sensor-agnostic radiometric and biophysical indices.
 */

export const SUPPORTED_INDICES = [
  "ndvi",
  "ndwi",
  "ndre",
  "evi",
  "nbr",
  "savi",
  "msavi",
  "bsi",
  "mndwi"
] as const;

export type SupportedIndex = typeof SUPPORTED_INDICES[number];

const EPSILON = 1e-8;

export interface IndexInputs {
  nir: number[] | number;
  red?: number[] | number;
  green?: number[] | number;
  blue?: number[] | number;
  rededge?: number[] | number;
  swir?: number[] | number;
  lFactor?: number;
}

export interface IndexStats {
  index: string;
  mean: number;
  min: number;
  max: number;
  std: number;
  data: number | number[];
}

function calcScalar(
  idx: string,
  n: number,
  r?: number,
  g?: number,
  b?: number,
  re?: number,
  s?: number,
  lFactor = 0.5
): number {
  switch (idx.toLowerCase()) {
    case "ndvi":
      if (r === undefined) throw new Error("Red band required to compute NDVI");
      return (n - r) / (n + r + EPSILON);
    case "ndwi":
      if (g === undefined) throw new Error("Green band required to compute NDWI");
      return (g - n) / (g + n + EPSILON);
    case "ndre":
      if (re === undefined) throw new Error("RedEdge band required to compute NDRE");
      return (n - re) / (n + re + EPSILON);
    case "evi":
      if (r === undefined || b === undefined) throw new Error("Red and Blue bands required to compute EVI");
      return 2.5 * ((n - r) / (n + 6.0 * r - 7.5 * b + 1.0 + EPSILON));
    case "nbr":
      if (s === undefined) throw new Error("SWIR band required to compute NBR");
      return (n - s) / (n + s + EPSILON);
    case "savi":
      if (r === undefined) throw new Error("Red band required to compute SAVI");
      return (1.0 + lFactor) * (n - r) / (n + r + lFactor + EPSILON);
    case "msavi":
      if (r === undefined) throw new Error("Red band required to compute MSAVI");
      const term = Math.max(0, Math.pow(2.0 * n + 1.0, 2) - 8.0 * (n - r));
      return (2.0 * n + 1.0 - Math.sqrt(term)) / 2.0;
    case "bsi":
      if (r === undefined || b === undefined || s === undefined) throw new Error("Red, Blue, and SWIR bands required to compute BSI");
      const num = (s + r) - (n + b);
      const denom = (s + r) + (n + b) + EPSILON;
      return num / denom;
    case "mndwi":
      if (g === undefined || s === undefined) throw new Error("Green and SWIR bands required to compute MNDWI");
      return (g - s) / (g + s + EPSILON);
    default:
      throw new Error(`Unsupported index '${idx}'. Supported: ${SUPPORTED_INDICES.join(", ")}`);
  }
}

export function computeSpectralIndex(
  index: string,
  inputs: IndexInputs
): IndexStats {
  const idx = index.toLowerCase();
  const { nir, red, green, blue, rededge, swir, lFactor = 0.5 } = inputs;

  if (Array.isArray(nir)) {
    const rList = Array.isArray(red) ? red : red !== undefined ? new Array(nir.length).fill(red) : undefined;
    const gList = Array.isArray(green) ? green : green !== undefined ? new Array(nir.length).fill(green) : undefined;
    const bList = Array.isArray(blue) ? blue : blue !== undefined ? new Array(nir.length).fill(blue) : undefined;
    const reList = Array.isArray(rededge) ? rededge : rededge !== undefined ? new Array(nir.length).fill(rededge) : undefined;
    const sList = Array.isArray(swir) ? swir : swir !== undefined ? new Array(nir.length).fill(swir) : undefined;

    const data = nir.map((nVal, i) =>
      calcScalar(
        idx,
        nVal,
        rList ? rList[i] : undefined,
        gList ? gList[i] : undefined,
        bList ? bList[i] : undefined,
        reList ? reList[i] : undefined,
        sList ? sList[i] : undefined,
        lFactor
      )
    );

    const sum = data.reduce((a, b) => a + b, 0);
    const mean = data.length > 0 ? sum / data.length : 0;
    const min = data.length > 0 ? Math.min(...data) : 0;
    const max = data.length > 0 ? Math.max(...data) : 0;
    const variance = data.length > 0 ? data.reduce((acc, v) => acc + Math.pow(v - mean, 2), 0) / data.length : 0;
    const std = Math.sqrt(variance);

    return { index: idx, mean, min, max, std, data };
  } else {
    const val = calcScalar(
      idx,
      nir,
      red as number | undefined,
      green as number | undefined,
      blue as number | undefined,
      rededge as number | undefined,
      swir as number | undefined,
      lFactor
    );
    return {
      index: idx,
      mean: val,
      min: val,
      max: val,
      std: 0,
      data: val
    };
  }
}
