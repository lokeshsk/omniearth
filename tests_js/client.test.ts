import test from "node:test";
import assert from "node:assert/strict";
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
