import test from "node:test";
import assert from "node:assert/strict";
import * as os from "node:os";
import * as path from "node:path";
import * as fs from "node:fs";
import { OmniEarth } from "../src/client.js";
import { Category } from "../src/types.js";

test("OmniEarth initializes and lists categories", () => {
  const client = new OmniEarth();
  const categories = client.listCategories();
  assert.ok(categories.includes("optical"));
  assert.ok(categories.includes("hyperspectral"));
  assert.ok(categories.includes("sar"));
  assert.ok(categories.includes("weather"));
  assert.ok(categories.includes("soil"));
  assert.ok(categories.includes("elevation"));
  assert.ok(categories.includes("landcover"));
  assert.ok(categories.includes("atmosphere"));
  assert.ok(categories.includes("fire"));
  assert.ok(categories.includes("ocean"));
  assert.ok(categories.includes("altimetry"));
  assert.ok(categories.includes("precipitation"));
  assert.ok(categories.includes("hydrology"));
  assert.ok(categories.includes("nightlights"));
});

test("OmniEarth resolves bounding boxes correctly and parses search results", async () => {
  const client = new OmniEarth();

  // Mock global fetch for reliable, instant CI execution without external network latency
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async (url: any) => {
    return {
      ok: true,
      status: 200,
      json: async () => ({
        latitude: 20.68,
        longitude: 78.55,
        elevation: 254.0,
        hourly: {
          time: ["2026-10-27T00:00"],
          temperature_2m: [25.0]
        }
      })
    } as any;
  };

  try {
    const weather = await client.search({
      category: Category.WEATHER,
      bbox: [78.50, 20.65, 78.60, 20.72]
    });
    assert.equal(weather.length, 1);
    assert.equal(weather[0].category, Category.WEATHER);
    assert.ok(weather[0].assets["data"]);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("OmniEarth rejects invalid bounding boxes", async () => {
  const client = new OmniEarth();
  await assert.rejects(
    async () => {
      await client.search({
        category: Category.OPTICAL,
        bbox: [78.60, 20.72, 78.50, 20.65] // min > max
      });
    },
    /Invalid bbox bounds/
  );
});

test("OmniEarth searches Optical STAC and parses items", async () => {
  const client = new OmniEarth();
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => ({
    ok: true,
    status: 200,
    json: async () => ({
      type: "FeatureCollection",
      features: [
        {
          id: "S2B_20261022_MOCK",
          properties: { datetime: "2026-10-22T05:30:00Z", "eo:cloud_cover": 3.2 },
          bbox: [78.5, 20.65, 78.6, 20.72],
          assets: {
            visual: { href: "https://aws.com/s2/visual.tif", type: "image/tiff" }
          }
        }
      ]
    })
  }) as any;

  try {
    const results = await client.search({
      category: Category.OPTICAL,
      bbox: [78.50, 20.65, 78.60, 20.72],
      maxCloudCover: 20
    });
    assert.equal(results.length, 1);
    assert.equal(results[0].id, "S2B_20261022_MOCK");
    assert.equal(results[0].category, Category.OPTICAL);
    assert.ok(results[0].assets["visual"]);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("OmniEarth searches SAR STAC and parses items", async () => {
  const client = new OmniEarth();
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => ({
    ok: true,
    status: 200,
    json: async () => ({
      type: "FeatureCollection",
      features: [
        {
          id: "S1_GRD_MOCK",
          properties: { datetime: "2026-10-20T00:00:00Z", "sar:polarizations": ["VV", "VH"] },
          bbox: [78.5, 20.65, 78.6, 20.72],
          assets: {
            vv: { href: "https://aws.com/s1/vv.tif", type: "image/tiff" }
          }
        }
      ]
    })
  }) as any;

  try {
    const results = await client.search({
      category: Category.SAR,
      bbox: [78.50, 20.65, 78.60, 20.72]
    });
    assert.equal(results.length, 1);
    assert.equal(results[0].id, "S1_GRD_MOCK");
    assert.equal(results[0].category, Category.SAR);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("OmniEarth searches SoilGrids and parses profile", async () => {
  const client = new OmniEarth();
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async (url: any) => ({
    ok: true,
    status: 200,
    url: "https://rest.isric.org/soilgrids/v2.0/properties/query",
    json: async () => ({
      properties: {
        layers: [
          {
            name: "clay",
            depths: [{ label: "0-5cm", values: { mean: 412 } }]
          }
        ]
      }
    })
  }) as any;

  try {
    const results = await client.search({
      category: Category.SOIL,
      bbox: [78.50, 20.65, 78.60, 20.72],
      depth: "0-5cm"
    });
    assert.equal(results.length, 1);
    assert.equal(results[0].category, Category.SOIL);
    assert.ok(results[0].properties["summary_topsoil"]);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("OmniEarth searches Hyperspectral and parses DLR EnMAP", async () => {
  const client = new OmniEarth();
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => ({
    ok: true,
    status: 200,
    json: async () => ({
      features: [
        {
          id: "ENMAP_HSI_MOCK",
          properties: { datetime: "2026-10-15T00:00:00Z" },
          bbox: [78.5, 20.65, 78.6, 20.72],
          assets: {
            image: { href: "https://dlr.de/enmap.tif", type: "image/tiff" }
          }
        }
      ]
    })
  }) as any;

  try {
    const results = await client.search({
      category: Category.HYPERSPECTRAL,
      bbox: [78.50, 20.65, 78.60, 20.72]
    });
    assert.ok(results.length >= 1);
    assert.equal(results[0].id, "ENMAP_HSI_MOCK");
    assert.equal(results[0].category, Category.HYPERSPECTRAL);

    // Direct provider targeting
    const prismaRes = await client.search({
      category: Category.HYPERSPECTRAL,
      bbox: [78.50, 20.65, 78.60, 20.72],
      provider: "prisma"
    });
    assert.ok(Array.isArray(prismaRes));

    const emitRes = await client.search({
      category: Category.HYPERSPECTRAL,
      bbox: [78.50, 20.65, 78.60, 20.72],
      provider: "emit"
    });
    assert.ok(Array.isArray(emitRes));
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("OmniEarth supports point search resolution and shortcuts", async () => {
  const client = new OmniEarth();
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => ({
    ok: true,
    status: 200,
    json: async () => ({
      latitude: 20.68,
      longitude: 78.55,
      elevation: 250,
      hourly: { time: ["2026-10-27T00:00"], temperature_2m: [25] }
    })
  }) as any;

  try {
    const res = await client.search({
      category: Category.WEATHER,
      point: [78.55, 20.68, 5.0]
    });
    assert.equal(res.length, 1);

    const wx = await client.getWeather([78.50, 20.65, 78.60, 20.72]);
    assert.ok(wx);
    assert.equal(wx.category, Category.WEATHER);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("OmniEarth Config checks credentials and environment", async () => {
  const { config } = await import("../src/config.js");
  assert.ok(config.defaultOutdir);
  assert.ok(config.timeoutMs > 0);
  assert.equal(config.get("NONEXISTENT_KEY_123", "fallback_val"), "fallback_val");

  const [du, dp] = config.dlrCredentials;
  const [pu, pp] = config.prismaCredentials;
  const [eu, ep] = config.earthdataCredentials;
  assert.ok(Array.isArray(config.dlrCredentials));
});

test("OmniEarth download handles cached files and downloads", async () => {
  const client = new OmniEarth();
  const res = {
    id: "wx_test_dl",
    collection: "weather",
    category: Category.WEATHER,
    provider: "open_meteo",
    properties: {
      _raw_data: { test: "data" }
    },
    assets: {
      data: { key: "data", href: "https://example.com/wx.json" }
    }
  };

  const testDir = path.join(os.tmpdir(), "omniearth_js_test");
  const dlPath = await client.download(res, undefined, testDir);
  assert.ok(dlPath.includes("wx_test_dl.json"));
});

function makeStream(chunks: Uint8Array[]) {
  return new ReadableStream({
    start(controller) {
      for (const c of chunks) {
        controller.enqueue(c);
      }
      controller.close();
    }
  });
}

test("OmniEarth downloadAll and downloadMany", async () => {
  const client = new OmniEarth();
  const res1: any = {
    id: "scene_all_1",
    collection: "sentinel-2-l2a",
    category: Category.OPTICAL,
    provider: "aws",
    assets: {
      visual: { key: "visual", href: "https://example.com/vis1.tif" },
      preview: { key: "preview", href: "https://example.com/vis1.tif" },
      data: { key: "data", href: "https://example.com/data1.tif" }
    }
  };
  const res2: any = {
    id: "scene_all_2",
    collection: "sentinel-2-l2a",
    category: Category.OPTICAL,
    provider: "aws",
    assets: {
      visual: { key: "visual", href: "https://example.com/vis2.tif" }
    }
  };

  const originalFetch = globalThis.fetch;
  globalThis.fetch = async (url: any, init?: any) => {
    if (init?.method === "HEAD") {
      return {
        ok: true,
        status: 200,
        headers: new Headers({ "content-length": "10", "accept-ranges": "bytes" })
      } as any;
    }
    return {
      ok: true,
      status: 200,
      headers: new Headers({ "content-length": "10" }),
      body: makeStream([Buffer.from("mockdata10")])
    } as any;
  };

  try {
    const testDir = path.join(os.tmpdir(), "omniearth_js_all_test_" + Date.now());
    const downloaded = await client.downloadAll(res1, undefined, testDir, { concurrency: 2 });
    assert.equal(Object.keys(downloaded).length, 3);
    assert.ok(downloaded["visual"].includes("vis1.tif"));
    assert.ok(downloaded["data"].includes("data1.tif"));
    assert.equal(downloaded["preview"], downloaded["visual"]);

    const manyDownloaded = await client.downloadMany([res1, res2], "visual", testDir, { concurrency: 2 });
    assert.equal(manyDownloaded.length, 2);

    const emptyMany = await client.downloadMany([]);
    assert.deepEqual(emptyMany, []);

    await assert.rejects(
      async () => client.downloadAll({ ...res1, assets: {} }),
      /No assets found to download/
    );
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("OmniEarth streamDownload resumable (206) and 416 fallback", async () => {
  const client = new OmniEarth();
  const testDir = path.join(os.tmpdir(), "omniearth_js_resume_test_" + Date.now());
  fs.mkdirSync(testDir, { recursive: true });

  const destPath = path.join(testDir, "resumable.tif");
  const partPath = `${destPath}.part`;
  fs.writeFileSync(partPath, Buffer.from("existing_part_"));

  const originalFetch = globalThis.fetch;
  let rangeRequested = "";

  globalThis.fetch = async (url: any, init?: any) => {
    if (init?.method === "HEAD") {
      return {
        ok: true,
        status: 200,
        headers: new Headers({ "content-length": "24", "accept-ranges": "bytes" })
      } as any;
    }
    rangeRequested = (init?.headers as any)?.["Range"] || "";
    return {
      ok: true,
      status: 206,
      headers: new Headers({ "content-length": "10" }),
      body: makeStream([Buffer.from("appended10")])
    } as any;
  };

  const res: any = {
    id: "resume_scene",
    collection: "sentinel-2-l2a",
    category: Category.OPTICAL,
    provider: "aws",
    assets: {
      visual: { key: "visual", href: "https://example.com/resumable.tif" }
    }
  };

  try {
    const downloaded = await client.download(res, "visual", testDir, { resume: true, multipart: false });
    assert.ok(rangeRequested.startsWith("bytes="));
    assert.ok(fs.existsSync(downloaded));
    const content = fs.readFileSync(downloaded, "utf-8");
    assert.equal(content, "existing_part_appended10");
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("OmniEarth multipartDownload parallel range fetching", async () => {
  const client = new OmniEarth();
  const testDir = path.join(os.tmpdir(), "omniearth_js_mp_test_" + Date.now());
  fs.mkdirSync(testDir, { recursive: true });

  const originalFetch = globalThis.fetch;
  const requestedRanges: string[] = [];

  globalThis.fetch = async (url: any, init?: any) => {
    if (init?.method === "HEAD") {
      return {
        ok: true,
        status: 200,
        headers: new Headers({ "content-length": "4000", "accept-ranges": "bytes" })
      } as any;
    }
    const range = (init?.headers as any)?.["Range"] || "";
    requestedRanges.push(range);
    return {
      ok: true,
      status: 206,
      headers: new Headers({ "content-length": "1000" }),
      body: makeStream([Buffer.from("A".repeat(1000))])
    } as any;
  };

  const res: any = {
    id: "mp_scene",
    collection: "sentinel-2-l2a",
    category: Category.OPTICAL,
    provider: "aws",
    assets: {
      visual: { key: "visual", href: "https://example.com/big_mp.tif" }
    }
  };

  try {
    const downloaded = await client.download(res, "visual", testDir, {
      multipart: true,
      concurrency: 4,
      minMultipartSize: 1000
    });
    assert.ok(fs.existsSync(downloaded));
    assert.equal(requestedRanges.length, 4);
    assert.ok(requestedRanges[0].startsWith("bytes=0-"));
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("OmniEarth ElevationProvider search and download", async () => {
  const client = new OmniEarth();
  const testDir = path.join(os.tmpdir(), "omniearth_js_elev_test_" + Date.now());
  fs.mkdirSync(testDir, { recursive: true });

  const cop = await client.search({
    category: Category.ELEVATION,
    bbox: [78.1, 20.2, 78.9, 20.8],
    dataset: "copernicus"
  });
  assert.ok(cop.length >= 1);
  assert.equal(cop[0].category, Category.ELEVATION);
  assert.ok(cop[0].id.startsWith("Copernicus_DSM_COG"));
  assert.ok(cop[0].assets["dem"]);

  const srtm = await client.search({
    category: Category.ELEVATION,
    bbox: [78.1, 20.2, 78.9, 20.8],
    dataset: "srtm"
  });
  assert.ok(srtm.length >= 1);
  assert.ok(srtm[0].id.startsWith("SRTM_GL1_"));

  const alos = await client.search({
    category: Category.ELEVATION,
    bbox: [78.1, 20.2, 78.9, 20.8],
    dataset: "alos"
  });
  assert.ok(alos.length >= 1);
  assert.ok(alos[0].id.startsWith("ALPSMLC30_"));

  // Mock download
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => ({
    ok: true,
    status: 200,
    headers: new Headers({ "content-length": "20" }),
    body: makeStream([Buffer.from("dummy dem content")])
  }) as any;

  try {
    const downloaded = await client.download(cop[0], "dem", testDir, { multipart: false });
    assert.ok(fs.existsSync(downloaded));
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("OmniEarth LandcoverProvider search and download", async () => {
  const client = new OmniEarth();
  const testDir = path.join(os.tmpdir(), "omniearth_js_lc_test_" + Date.now());
  fs.mkdirSync(testDir, { recursive: true });

  const tiles2021 = await client.search({
    category: Category.LANDCOVER,
    bbox: [78.1, 20.2, 78.9, 20.8],
    year: 2021
  });
  assert.ok(tiles2021.length >= 1);
  assert.equal(tiles2021[0].category, Category.LANDCOVER);
  assert.ok(tiles2021[0].id.includes("2021"));
  assert.ok(tiles2021[0].assets["map"]);

  const tiles2020 = await client.search({
    category: Category.LANDCOVER,
    bbox: [78.1, 20.2, 78.9, 20.8],
    year: 2020
  });
  assert.ok(tiles2020.length >= 1);
  assert.ok(tiles2020[0].id.includes("2020"));

  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => ({
    ok: true,
    status: 200,
    headers: new Headers({ "content-length": "20" }),
    body: makeStream([Buffer.from("dummy landcover content")])
  }) as any;

  try {
    const downloaded = await client.download(tiles2021[0], "map", testDir, { multipart: false });
    assert.ok(fs.existsSync(downloaded));
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("OmniEarth GeoJSON AOI resolution and search", async () => {
  const client = new OmniEarth();
  const geojsonObj = {
    type: "FeatureCollection",
    features: [
      {
        type: "Feature",
        geometry: {
          type: "Polygon",
          coordinates: [
            [
              [78.0, 20.0],
              [78.5, 20.0],
              [78.5, 20.5],
              [78.0, 20.5],
              [78.0, 20.0]
            ]
          ]
        }
      }
    ]
  };

  const aoi = client.aoiFromGeoJSON(geojsonObj);
  assert.deepEqual(aoi.bbox, [78.0, 20.0, 78.5, 20.5]);

  const results = await client.search({
    category: Category.ELEVATION,
    geojson: JSON.stringify(geojsonObj)
  });
  assert.ok(results.length >= 1);

  assert.throws(() => client.aoiFromGeoJSON({ type: "Point", coordinates: [] }), /No valid coordinates/);
});

test("OmniEarth computeIndex and getTimeSeries", async () => {
  const client = new OmniEarth();

  // Scalar calculations
  const ndvi = client.computeIndex("ndvi", { nir: 0.8, red: 0.2 });
  assert.ok(typeof ndvi === "number");
  assert.ok(Math.abs((ndvi as number) - 0.6) < 0.01);

  const ndwi = client.computeIndex("ndwi", { nir: 0.8, green: 0.3 });
  assert.ok(typeof ndwi === "number");

  const ndre = client.computeIndex("ndre", { nir: 0.8, rededge: 0.4 });
  assert.ok(typeof ndre === "number");

  const evi = client.computeIndex("evi", { nir: 0.8, red: 0.2, blue: 0.1 });
  assert.ok(typeof evi === "number");

  const nbr = client.computeIndex("nbr", { nir: 0.8, swir: 0.3 });
  assert.ok(typeof nbr === "number");

  const savi = client.computeIndex("savi", { nir: 0.8, red: 0.2, lFactor: 0.5 });
  assert.ok(typeof savi === "number");

  const msavi = client.computeIndex("msavi", { nir: 0.8, red: 0.2 });
  assert.ok(typeof msavi === "number");

  const bsi = client.computeIndex("bsi", { nir: 0.8, red: 0.2, blue: 0.1, swir: 0.4 });
  assert.ok(typeof bsi === "number");

  const mndwi = client.computeIndex("mndwi", { nir: 0.0, green: 0.6, swir: 0.2 });
  assert.ok(typeof mndwi === "number");

  // Array calculation
  const arrNdvi = client.computeIndex("ndvi", { nir: [0.8, 0.9], red: [0.2, 0.1] }) as number[];
  assert.equal(arrNdvi.length, 2);

  assert.throws(() => client.computeIndex("unknown_idx", { nir: 0.8 }), /Unsupported index/);
  assert.throws(() => client.computeIndex("ndvi", { nir: 0.8 }), /Red band required/);
  assert.throws(() => client.computeIndex("savi", { nir: 0.8 }), /Red band required/);
  assert.throws(() => client.computeIndex("msavi", { nir: 0.8 }), /Red band required/);
  assert.throws(() => client.computeIndex("bsi", { nir: 0.8, red: 0.2 }), /Red, Blue, and SWIR bands required/);
  assert.throws(() => client.computeIndex("mndwi", { nir: 0.8, green: 0.5 }), /Green and SWIR bands required/);

  // Time-series
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => ({
    ok: true,
    status: 200,
    json: async () => ({
      hourly: {
        time: ["2026-10-27T00:00", "2026-10-27T01:00"],
        temperature_2m: [22.5, 23.0]
      }
    })
  }) as any;

  try {
    const ts = await client.getTimeSeries({
      category: Category.WEATHER,
      bbox: [78.0, 20.0, 78.5, 20.5]
    });
    assert.equal(ts.length, 2);
    assert.equal(ts[0].datetime, "2026-10-27T00:00");
    assert.equal(ts[0].temperature_2m, 22.5);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test("OmniEarth searches and downloads new modalities (Atmosphere, Fire, Ocean, Altimetry, Precipitation, Hydrology, Nightlights)", async () => {
  const client = new OmniEarth();
  const tmpDir = path.join(os.tmpdir(), "omniearth_modalities_test");
  fs.mkdirSync(tmpDir, { recursive: true });

  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => ({
    ok: true,
    status: 200,
    json: async () => ({
      elevation: 250.0,
      hourly: {
        time: ["2026-10-25T00:00"],
        nitrogen_dioxide: [11.2],
        pm10: [15.0]
      }
    })
  }) as any;

  try {
    // 1. Atmosphere
    const atmo = await client.getAtmosphere([78.0, 20.0, 78.5, 20.5], "2026-10-20", "2026-10-22");
    assert.ok(atmo);
    assert.equal(atmo.category, Category.ATMOSPHERE);
    const atmoPath = await client.download(atmo, undefined, tmpDir);
    assert.ok(fs.existsSync(atmoPath));

    // 2. Fire
    const fire = await client.getFire([78.0, 20.0, 78.5, 20.5], "2026-10-28");
    assert.ok(fire);
    assert.equal(fire.category, Category.FIRE);
    const firePath = await client.download(fire, undefined, tmpDir);
    assert.ok(fs.existsSync(firePath));

    // 3. Ocean
    const ocean = await client.getOcean([78.0, 20.0, 78.5, 20.5], "2026-10-25");
    assert.ok(ocean);
    assert.equal(ocean.category, Category.OCEAN);
    const oceanPath = await client.download(ocean, undefined, tmpDir);
    assert.ok(fs.existsSync(oceanPath));

    // 4. Altimetry
    const alti = await client.getAltimetry([78.0, 20.0, 78.5, 20.5], "2026-10-25");
    assert.ok(alti);
    assert.equal(alti.category, Category.ALTIMETRY);
    const altiPath = await client.download(alti, undefined, tmpDir);
    assert.ok(fs.existsSync(altiPath));

    // 5. Precipitation
    const precip = await client.getPrecipitation([78.0, 20.0, 78.5, 20.5], "2026-10-25");
    assert.ok(precip);
    assert.equal(precip.category, Category.PRECIPITATION);
    const precipPath = await client.download(precip, undefined, tmpDir);
    assert.ok(fs.existsSync(precipPath));

    // 6. Hydrology
    const hydro = await client.getHydrology([78.0, 20.0, 78.5, 20.5], "2026-10-25");
    assert.ok(hydro);
    assert.equal(hydro.category, Category.HYDROLOGY);
    const hydroPath = await client.download(hydro, undefined, tmpDir);
    assert.ok(fs.existsSync(hydroPath));

    // 7. Nightlights
    const ntl = await client.getNightlights([78.0, 20.0, 78.5, 20.5], "2026-10-25");
    assert.ok(ntl);
    assert.equal(ntl.category, Category.NIGHTLIGHTS);
    const ntlPath = await client.download(ntl, undefined, tmpDir);
    assert.ok(fs.existsSync(ntlPath));

    // 8. Optical TOA and shortcuts
    let requestedCollection = "";
    globalThis.fetch = async (url: any, init?: any) => {
      if (init?.body) {
        const body = JSON.parse(init.body);
        if (body.collections) {
          requestedCollection = body.collections[0];
        }
      }
      return {
        ok: true,
        status: 200,
        json: async () => ({
          type: "FeatureCollection",
          features: [
            {
              id: "S2_TOA_MOCK",
              collection: requestedCollection,
              properties: { datetime: "2026-10-25T00:00:00Z" },
              assets: { visual: { href: "https://aws.com/vis.tif" } }
            }
          ]
        })
      } as any;
    };

    const optToa = await client.getOptical([78.0, 20.0, 78.5, 20.5], { level: "toa" });
    assert.ok(optToa);
    assert.equal(requestedCollection, "sentinel-2-l1c");

    const sarItem = await client.getSar([78.0, 20.0, 78.5, 20.5]);
    assert.ok(sarItem);
  } finally {
    globalThis.fetch = originalFetch;
    fs.rmSync(tmpDir, { recursive: true, force: true });
  }
});

test("OmniEarth SearchResults fluent methods and searchAndDownload", async () => {
  const { SearchResults } = await import("../src/types.js");
  const client = new OmniEarth();
  const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "omniearth_chain_"));

  const mockItem1 = {
    id: "SCENE_1",
    collection: "sentinel-2-l2a",
    category: Category.OPTICAL,
    provider: "aws",
    datetime: "2026-05-01T00:00:00Z",
    properties: { cloud_cover: 5.0 },
    assets: { visual: { key: "visual", href: "https://example.com/s1.tif" } }
  };
  const mockItem2 = {
    id: "SCENE_2",
    collection: "sentinel-2-l2a",
    category: Category.OPTICAL,
    provider: "aws",
    datetime: "2026-04-01T00:00:00Z",
    properties: { cloud_cover: 25.0 },
    assets: { visual: { key: "visual", href: "https://example.com/s2.tif" } }
  };

  const results = new SearchResults([mockItem1, mockItem2], client);
  assert.equal(results.first()?.id, "SCENE_1");

  const emptyRes = new SearchResults([], client);
  assert.equal(emptyRes.first(), undefined);

  // Filter
  const filtered = results.filterResults({ maxCloudCover: 10.0 });
  assert.equal(filtered.length, 1);
  assert.equal(filtered[0].id, "SCENE_1");

  const filterByProvider = results.filterResults({ provider: "aws", collection: "sentinel-2-l2a" });
  assert.equal(filterByProvider.length, 2);

  // Mock download
  const origDownload = client.download.bind(client);
  client.download = async (res: any) => path.join(tmpDir, `${res.id}.tif`);

  try {
    const downloadedAll = await results.downloadAll(undefined, tmpDir);
    assert.equal(downloadedAll.length, 2);

    const downloadedIndices = await results.downloadIndices([1], undefined, tmpDir);
    assert.equal(downloadedIndices.length, 1);
    assert.ok(downloadedIndices[0].includes("SCENE_2"));

    // Detached client check
    const detached = new SearchResults([mockItem1]);
    await assert.rejects(async () => detached.downloadAll(), /No OmniEarth client attached/);
    await assert.rejects(async () => detached.downloadIndices([0]), /No OmniEarth client attached/);

    // searchAndDownload
    client.search = async () => new SearchResults([mockItem1], client);
    const searchDl = await client.searchAndDownload({ category: Category.OPTICAL, bbox: [0, 0, 1, 1] }, undefined, tmpDir);
    assert.equal(searchDl.length, 1);
    assert.ok(searchDl[0].includes("SCENE_1"));
  } finally {
    client.download = origDownload;
    fs.rmSync(tmpDir, { recursive: true, force: true });
  }
});

test("SearchResults GIS exportGeoJSON, exportCSV, and export", async () => {
  const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "oe-export-test-"));
  try {
    const item = {
      id: "S2A_MSIL2A_TEST",
      collection: "sentinel-2-l2a",
      category: Category.OPTICAL,
      provider: "cdse",
      datetime: "2026-11-19T00:00:00Z",
      bbox: [78.0, 20.0, 78.5, 20.5] as [number, number, number, number],
      properties: { cloud_cover: 5.0 },
      assets: { visual: { key: "visual", href: "https://example.com/vis.jp2" } }
    };
    const { SearchResults } = await import("../src/types.js");
    const results = new SearchResults([item]);

    // GeoJSON export
    const geojsonPath = path.join(tmpDir, "results.geojson");
    const outGeo = results.exportGeoJSON(geojsonPath);
    assert.equal(outGeo, path.resolve(geojsonPath));
    const geoData = JSON.parse(fs.readFileSync(geojsonPath, "utf-8"));
    assert.equal(geoData.type, "FeatureCollection");
    assert.equal(geoData.features.length, 1);
    assert.equal(geoData.features[0].id, "S2A_MSIL2A_TEST");
    assert.equal(geoData.features[0].geometry.type, "Polygon");

    // CSV export
    const csvPath = path.join(tmpDir, "results.csv");
    const outCsv = results.exportCSV(csvPath);
    assert.equal(outCsv, path.resolve(csvPath));
    const csvText = fs.readFileSync(csvPath, "utf-8");
    assert.ok(csvText.includes("S2A_MSIL2A_TEST"));
    assert.ok(csvText.includes("sentinel-2-l2a"));

    // Auto export
    const autoGeo = results.export(path.join(tmpDir, "auto.geojson"));
    assert.ok(fs.existsSync(autoGeo));
    const autoCsv = results.export(path.join(tmpDir, "auto.csv"));
    assert.ok(fs.existsSync(autoCsv));

    // Test all 14 modalities export
    const allCategories = [
      Category.OPTICAL, Category.SAR, Category.HYPERSPECTRAL, Category.WEATHER,
      Category.SOIL, Category.ELEVATION, Category.LANDCOVER, Category.ATMOSPHERE,
      Category.FIRE, Category.OCEAN, Category.ALTIMETRY, Category.PRECIPITATION,
      Category.HYDROLOGY, Category.NIGHTLIGHTS
    ];
    const items14 = allCategories.map((cat, idx) => ({
      id: `scene_${cat}_${idx}`,
      collection: `${cat}-col`,
      category: cat,
      provider: `prov_${cat}`,
      datetime: "2026-11-19T00:00:00Z",
      bbox: (idx % 2 === 0 ? [78.0, 20.0, 78.5, 20.5] : [78.5, 20.5, 78.5, 20.5]) as [number, number, number, number],
      properties: {
        latitude: 20.5,
        longitude: 78.5,
        cloud_cover: 2.5
      },
      assets: { data: { key: "data", href: `https://example.com/${cat}.tif` } }
    }));
    const results14 = new SearchResults(items14);
    const geo14 = results14.exportGeoJSON(path.join(tmpDir, "all_14.geojson"));
    const geo14Data = JSON.parse(fs.readFileSync(geo14, "utf-8"));
    assert.equal(geo14Data.features.length, 14);

    const csv14 = results14.exportCSV(path.join(tmpDir, "all_14.csv"));
    const csv14Text = fs.readFileSync(csv14, "utf-8");
    assert.ok(csv14Text.includes("weather"));
    assert.ok(csv14Text.includes("soil"));
    assert.ok(csv14Text.includes("fire"));
  } finally {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  }
});

test("CDSEAuthManager and CDSEProvider operations", async () => {
  const { CDSEAuthManager, CDSEProvider } = await import("../src/providers/cdse.js");
  const auth = new CDSEAuthManager("test_user", "test_pass");

  const origFetch = globalThis.fetch;
  globalThis.fetch = async (url: any, opts: any) => {
    const urlStr = String(url);
    if (urlStr.includes("openid-connect/token")) {
      return {
        ok: true,
        status: 200,
        json: async () => ({ access_token: "test_bearer_token_123" })
      } as any;
    }
    if (urlStr.includes("stac.dataspace.copernicus.eu/v1/search")) {
      return {
        ok: true,
        status: 200,
        json: async () => ({
          features: [
            {
              id: "S2A_MSIL2A_20261119_TEST",
              properties: { id: "cdse-uuid-123", title: "S2A_MSIL2A_20261119_TEST", "eo:cloud_cover": 2.0 },
              bbox: [78.0, 20.0, 78.5, 20.5],
              assets: {
                B04: { href: "https://download.dataspace.copernicus.eu/B04.jp2", type: "image/jp2" }
              }
            }
          ]
        })
      } as any;
    }
    if (urlStr.includes("catalogue.dataspace.copernicus.eu/odata/v1/Products")) {
      return {
        ok: true,
        status: 200,
        json: async () => ({
          value: [
            {
              Id: "cdse-uuid-123",
              Name: "S2A_MSIL2A_20261119_TEST",
              ContentLength: 1048576,
              Checksum: [{ Value: "d41d8cd98f00b204e9800998ecf8427e", Algorithm: "MD5" }],
              Attributes: [{ Name: "cloudCover", Value: "2.0" }]
            }
          ]
        })
      } as any;
    }
    return { ok: false, status: 404 } as any;
  };

  try {
    const token = await auth.getToken();
    assert.equal(token, "test_bearer_token_123");

    const cdse = new CDSEProvider(auth);
    const searchRes = await cdse.search({ bbox: [78.0, 20.0, 78.5, 20.5] });
    assert.equal(searchRes.length, 1);
    assert.equal(searchRes[0].id, "S2A_MSIL2A_20261119_TEST");
    assert.equal(searchRes[0].provider, "cdse");

    // Band presets
    const rgbBands = cdse.resolveRequestedBands("rgb", "sentinel2");
    assert.deepEqual(rgbBands, ["TCI", "B04", "B03", "B02"]);
    const dualPol = cdse.resolveRequestedBands("dual", "sentinel1");
    assert.deepEqual(dualPol, ["vh", "vv"]);
    const customBands = cdse.resolveRequestedBands("B01,B02", "sentinel2");
    assert.deepEqual(customBands, ["B01", "B02"]);
  } finally {
    globalThis.fetch = origFetch;
  }
});

test("Processors resolveCompositeBands and createCompositeFromDownloaded", async () => {
  const { resolveCompositeBands, createCompositeFromDownloaded } = await import("../src/processors.js");
  const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "oe-proc-test-"));
  try {
    const rFile = path.join(tmpDir, "T32TMT_B04_10m.jp2");
    const gFile = path.join(tmpDir, "T32TMT_B03_10m.jp2");
    const bFile = path.join(tmpDir, "T32TMT_B02_10m.jp2");
    const nirFile = path.join(tmpDir, "T32TMT_B08_10m.jp2");
    fs.writeFileSync(rFile, "fake-red");
    fs.writeFileSync(gFile, "fake-green");
    fs.writeFileSync(bFile, "fake-blue");
    fs.writeFileSync(nirFile, "fake-nir");

    const rgbBands = resolveCompositeBands(tmpDir, "rgb");
    assert.equal(rgbBands.red, rFile);
    assert.equal(rgbBands.green, gFile);
    assert.equal(rgbBands.blue, bFile);

    const falseColorBands = resolveCompositeBands(tmpDir, "false-color");
    assert.equal(falseColorBands.red, nirFile);
    assert.equal(falseColorBands.green, rFile);
    assert.equal(falseColorBands.blue, gFile);

    const compTif = createCompositeFromDownloaded(tmpDir, "rgb");
    assert.ok(compTif.endsWith(".tif"));
    assert.ok(fs.existsSync(`${compTif}.meta.json`));

    // Missing bands check
    assert.throws(() => resolveCompositeBands([rFile, gFile], "rgb"), /missing band file/);
    assert.throws(() => resolveCompositeBands(tmpDir, "invalid-type"), /Unsupported composite type/);
  } finally {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  }
});

test("BaseProvider getItem coordinate-encoded ID resolution", async () => {
  const { WeatherProvider } = await import("../src/providers/weather.js");
  const wp = new WeatherProvider();
  const origSearch = wp.search;
  wp.search = async () => [{
    id: "openmeteo_20.68_78.55_latest",
    collection: "openmeteo",
    category: Category.WEATHER,
    provider: "open_meteo",
    properties: { latitude: 20.68, longitude: 78.55 },
    assets: { data: { key: "data", href: "https://example.com/wx.json" } }
  } as any];

  try {
    const item = await wp.getItem("openmeteo_20.68_78.55_latest");
    assert.ok(item);
    assert.equal(item?.id, "openmeteo_20.68_78.55_latest");

    const noItem = await wp.getItem("invalid_id_no_nums");
    assert.equal(noItem, null);
  } finally {
    wp.search = origSearch;
  }
});

test("resolveAssetKey resolves semantic aliases and falls back appropriately", async () => {
  const { resolveAssetKey } = await import("../src/types.js");
  const sampleResult: any = {
    id: "EMIT_L2A_RFL_TEST",
    assets: {
      browse: { key: "browse", href: "https://example.com/browse.jpeg" },
      "001/EMIT/EMIT_DATA": { key: "001/EMIT/EMIT_DATA", href: "https://example.com/EMIT_DATA.nc" },
      "001/EMIT/EMIT_UNCERT": { key: "001/EMIT/EMIT_UNCERT", href: "https://example.com/EMIT_UNCERT.nc" },
      "001/EMIT/EMIT_MASK": { key: "001/EMIT/EMIT_MASK", href: "https://example.com/EMIT_MASK.nc" },
      "s3_raw": { key: "s3_raw", href: "s3://example.com/raw.nc" },
      metadata: { key: "metadata", href: "https://example.com/meta.xml" }
    }
  };

  assert.equal(resolveAssetKey(sampleResult, "browse"), "browse");
  assert.equal(resolveAssetKey(sampleResult, "rfl"), "001/EMIT/EMIT_DATA");
  assert.equal(resolveAssetKey(sampleResult, "cube"), "001/EMIT/EMIT_DATA");
  assert.equal(resolveAssetKey(sampleResult, "uncert"), "001/EMIT/EMIT_UNCERT");
  assert.equal(resolveAssetKey(sampleResult, "mask"), "001/EMIT/EMIT_MASK");
  assert.equal(resolveAssetKey(sampleResult, "xml"), "metadata");
  assert.equal(resolveAssetKey(sampleResult, undefined), "001/EMIT/EMIT_DATA");
  assert.equal(resolveAssetKey({ id: "no_assets" } as any, "data"), undefined);

  const multiResult: any = {
    id: "multi_test_ts",
    assets: {
      visual_cog: { key: "visual_cog", href: "https://example.com/visual.tif" },
      dem_raster: { key: "dem_raster", href: "https://example.com/dem.tif" },
      map_cover: { key: "map_cover", href: "https://example.com/map.tif" },
      vv_amplitude: { key: "vv_amplitude", href: "https://example.com/vv.tif" },
      tropospheric_no2_grid: { key: "tropospheric_no2_grid", href: "https://example.com/no2.nc" },
      chlorophyll_a_surface: { key: "chlorophyll_a_surface", href: "https://example.com/chla.nc" },
      altimetry_l2_pass: { key: "altimetry_l2_pass", href: "https://example.com/alt.nc" },
      gpm_imerg_daily_accum: { key: "gpm_imerg_daily_accum", href: "https://example.com/gpm.nc" },
      surface_soil_moisture_level: { key: "surface_soil_moisture_level", href: "https://example.com/ssm.nc" },
      dnb_radiance_night: { key: "dnb_radiance_night", href: "https://example.com/dnb.tif" },
      weather_feed: { key: "weather_feed", href: "https://example.com/wx.json" },
      soil_profile: { key: "soil_profile", href: "https://example.com/soil.json" },
      safe_package: { key: "safe_package", href: "https://example.com/s2.zip" }
    }
  };

  assert.equal(resolveAssetKey(multiResult, "visual"), "visual_cog");
  assert.equal(resolveAssetKey(multiResult, "dem"), "dem_raster");
  assert.equal(resolveAssetKey(multiResult, "map"), "map_cover");
  assert.equal(resolveAssetKey(multiResult, "sar"), "vv_amplitude");
  assert.equal(resolveAssetKey(multiResult, "no2"), "tropospheric_no2_grid");
  assert.equal(resolveAssetKey(multiResult, "ocean"), "chlorophyll_a_surface");
  assert.equal(resolveAssetKey(multiResult, "altimetry"), "altimetry_l2_pass");
  assert.equal(resolveAssetKey(multiResult, "precipitation"), "gpm_imerg_daily_accum");
  assert.equal(resolveAssetKey(multiResult, "hydrology"), "surface_soil_moisture_level");
  assert.equal(resolveAssetKey(multiResult, "nightlights"), "dnb_radiance_night");
  assert.equal(resolveAssetKey(multiResult, "weather"), "weather_feed");
  assert.equal(resolveAssetKey(multiResult, "soil"), "soil_profile");
  assert.equal(resolveAssetKey(multiResult, "safe"), "safe_package");
});
