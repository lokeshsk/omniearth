import test from "node:test";
import assert from "node:assert/strict";
import * as os from "node:os";
import * as path from "node:path";
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
