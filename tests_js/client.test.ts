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
    assert.equal(Object.keys(downloaded).length, 2);
    assert.ok(downloaded["visual"].includes("vis1.tif"));
    assert.ok(downloaded["data"].includes("data1.tif"));

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
