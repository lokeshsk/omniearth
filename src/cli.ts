import { Command } from "commander";
import { OmniEarth } from "./client.js";
import { Category } from "./types.js";
import { config } from "./config.js";

const program = new Command();

program
  .name("omniearth")
  .description("OmniEarth: Universal Multi-Modal Open Earth Observation & Environmental Data Engine")
  .version("1.0.0");

program
  .command("categories")
  .description("List all supported modalities, satellites, and providers")
  .action(() => {
    console.log("=================================================================");
    console.log(" OmniEarth Supported Modalities & Data Providers (Node.js SDK)");
    console.log("=================================================================");
    console.log("\n[OPTICAL] - Optical Multispectral Imagery");
    console.log("   Sensors:  Sentinel-2 L2A (10m), Landsat-8/9 (30m)");
    console.log("   Backend:  AWS Open Data STAC / Element84 Earth Search");
    console.log("   Auth:     Zero-Config (Free public egress COGs)");

    console.log("\n[HYPERSPECTRAL] - Hyperspectral Data Cubes (200+ Bands)");
    console.log("   Sensors:  DLR EnMAP (224 bands), NASA EMIT (285 bands), ASI PRISMA (240 bands)");
    console.log("   Backend:  DLR EOC STAC, NASA CMR STAC, ASI PRISMA Portal");
    console.log("   Auth:     DLR Credentials (Free) / NASA Earthdata (Free)");

    console.log("\n[SAR] - Synthetic Aperture Radar (SAR)");
    console.log("   Sensors:  Sentinel-1 GRD / RTC (10m)");
    console.log("   Backend:  AWS Open Data STAC");
    console.log("   Auth:     Zero-Config (Public COGs)");

    console.log("\n[WEATHER] - Weather & Climate Profiles");
    console.log("   Sources:  Open-Meteo Zero-Config Global Model, ERA5 Reanalysis");
    console.log("   Backend:  Open-Meteo REST API");
    console.log("   Auth:     Zero-Config (No API key needed)");

    console.log("\n[SOIL] - Soil Composition & 3D Profiles");
    console.log("   Sources:  ISRIC SoilGrids v2.0 (250m global)");
    console.log("   Backend:  ISRIC REST API");
    console.log("   Auth:     Zero-Config (Public)");
    console.log("\n=================================================================");
  });

program
  .command("info")
  .description("Display engine status, versions, and credential health")
  .action(() => {
    console.log("=================================================================");
    console.log(" OmniEarth Engine v1.0.0 (Node.js SDK)");
    console.log(" Author: Lokesh Kumar (lokesh.skshukla@gmail.com)");
    console.log(" Homepage: https://lokeshsk.github.io/omniearth/");
    console.log("=================================================================");
    console.log("\n[Credential & Environment Status]");
    const [dlrU] = config.dlrCredentials;
    const [prismaU] = config.prismaCredentials;
    const [edU] = config.earthdataCredentials;

    console.log(`  • DLR Geoservice (EnMAP):     ${dlrU ? "Configured" : "Optional (Needed for EnMAP raw download)"}`);
    console.log(`  • ASI PRISMA Portal:          ${prismaU ? "Configured" : "Optional (Needed for PRISMA download)"}`);
    console.log(`  • NASA Earthdata (EMIT):       ${edU ? "Configured" : "Optional (Needed for NASA EMIT direct cubes)"}`);
    console.log("  • Open-Meteo (Weather):        Native Zero-Config");
    console.log("  • ISRIC SoilGrids (Soil):      Native Zero-Config");
    console.log("  • AWS Earth Search (S1, S2):   Native Zero-Config");
    console.log("=================================================================");
  });

program
  .command("search")
  .description("Search for satellite scenes, weather, or soil data")
  .requiredOption("-c, --category <category>", "Data category (optical, hyperspectral, sar, weather, soil)")
  .option("--bbox <coords...>", "Bounding box: min_lon min_lat max_lon max_lat")
  .option("--point <coords...>", "Point: lon lat [radius_km]")
  .option("--start <date>", "Start date (YYYY-MM-DD)")
  .option("--end <date>", "End date (YYYY-MM-DD)")
  .option("--max-cloud <percent>", "Max cloud cover percentage")
  .option("--limit <number>", "Maximum number of results", "5")
  .option("--json", "Output raw JSON format")
  .action(async (opts) => {
    const client = new OmniEarth();
    let bbox: [number, number, number, number] | undefined;
    let point: [number, number, number?] | undefined;

    if (opts.bbox) {
      const parts = opts.bbox.map(Number);
      if (parts.length === 4) {
        bbox = [parts[0], parts[1], parts[2], parts[3]];
      }
    } else if (opts.point) {
      const parts = opts.point.map(Number);
      if (parts.length >= 2) {
        point = [parts[0], parts[1], parts[2]];
      }
    }

    try {
      const results = await client.search({
        category: opts.category as Category,
        bbox,
        point,
        startDate: opts.start,
        endDate: opts.end,
        maxCloudCover: opts.maxCloud ? Number(opts.maxCloud) : undefined,
        limit: Number(opts.limit)
      });

      if (opts.json) {
        console.log(JSON.stringify(results, null, 2));
        return;
      }

      console.log("===========================================================================");
      console.log(` OmniEarth Search Results [${opts.category.toUpperCase()}] — ${results.length} item(s) found`);
      console.log("===========================================================================");

      for (let i = 0; i < results.length; i++) {
        const r = results[i];
        console.log(`\n[${i + 1}] ${r.properties?.title || r.id}`);
        console.log(`    ID:         ${r.id}`);
        console.log(`    Provider:   ${r.provider} (${r.collection})`);
        console.log(`    Datetime:   ${r.datetime || "N/A"}`);
        const assetKeys = Object.keys(r.assets);
        console.log(`    Assets (${assetKeys.length}):`);
        for (const k of assetKeys) {
          const a = r.assets[k];
          console.log(`      - ${k}: [${a.media_type || "asset"}]`);
        }
      }
      console.log("\n===========================================================================");
    } catch (err: any) {
      console.error(`Error: ${err.message}`);
      process.exit(1);
    }
  });

program
  .command("download")
  .description("Download satellite data, hyperspectral cubes, or environmental profiles")
  .requiredOption("-c, --category <category>", "Data category")
  .option("--id <id>", "Product ID to download")
  .option("--bbox <coords...>", "Bounding box to find scene for")
  .option("--asset <key>", "Specific asset key")
  .option("-o, --outdir <path>", "Output directory", "./omniearth_downloads")
  .option("--all", "Download all assets associated with the scene concurrently")
  .option("-t, --threads <number>", "Number of parallel worker threads", "4")
  .option("--no-resume", "Disable byte-range download resumption")
  .option("--no-multipart", "Disable parallel chunked multipart downloading")
  .action(async (opts) => {
    const client = new OmniEarth();
    let bbox: [number, number, number, number] | undefined;
    if (opts.bbox) {
      const parts = opts.bbox.map(Number);
      bbox = [parts[0], parts[1], parts[2], parts[3]];
    }

    const downloadOpts = {
      resume: opts.resume !== false,
      multipart: opts.multipart !== false,
      concurrency: parseInt(opts.threads, 10) || 4
    };

    try {
      let targetResult: any;
      if (opts.id) {
        targetResult = {
          id: opts.id,
          collection: opts.category,
          category: opts.category,
          provider: opts.category,
          assets: {}
        };
      } else if (bbox) {
        const results = await client.search({
          category: opts.category as Category,
          bbox,
          limit: 1
        });
        if (results.length === 0) {
          console.error("No matching scenes found to download.");
          process.exit(1);
        }
        targetResult = results[0];
      }

      if (opts.all) {
        const downloaded = await client.downloadAll(targetResult, undefined, opts.outdir, downloadOpts);
        console.log(`Successfully downloaded ${Object.keys(downloaded).length} asset(s) to: ${opts.outdir}`);
        for (const [k, p] of Object.entries(downloaded)) {
          console.log(`  • ${k}: ${p}`);
        }
      } else {
        const filePath = await client.download(targetResult, opts.asset, opts.outdir, downloadOpts);
        console.log(`Successfully downloaded: ${filePath}`);
      }
    } catch (err: any) {
      console.error(`Error: Download failed: ${err.message}`);
      process.exit(1);
    }
  });

export function runCLI() {
  program.parse(process.argv);
}

if (process.argv[1]?.endsWith("cli.js") || process.argv[1]?.endsWith("cli.ts")) {
  runCLI();
}

