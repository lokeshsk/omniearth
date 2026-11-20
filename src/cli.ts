import { Command } from "commander";
import { OmniEarth } from "./client.js";
import { Category, resolveAssetKey } from "./types.js";
import { config } from "./config.js";

const ASCII_BANNER = `  ___  __  __ _   _ ___ _____    _    ____ _____ _   _ 
 / _ \\|  \\/  | \\ | |_ _| ____|  / \\  |  _ \\_   _| | | |
| | | | |\\/| |  \\| || ||  _|   / _ \\ | |_) || | | |_| |
| |_| | |  | | |\\  || || |___ / ___ \\|  _ < | | |  _  |
 \\___/|_|  |_|_| \\_|___|_____/_/   \\_\\_| \\_\\|_| |_| |_|`;

const program = new Command();

program
  .name("omniearth")
  .description("OmniEarth: Universal Multi-Modal Open Earth Observation & Environmental Data Engine")
  .version("1.5.0")
  .addHelpText("before", `\n${ASCII_BANNER}\n`);

program
  .command("categories")
  .description("List all supported modalities, satellites, and providers")
  .action(() => {
    const width = 75;
    console.log("+" + "-".repeat(width - 2) + "+");
    console.log("| OmniEarth Supported Modalities & Data Providers (Node.js SDK)".padEnd(width - 1) + "|");
    console.log("+" + "-".repeat(width - 2) + "+");
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

    console.log("\n[ELEVATION] - Digital Elevation Models (DEM / DSM / DTM 30m)");
    console.log("   Sources:  Copernicus DEM GLO-30 (30m DSM), SRTM GL1 (30m), ALOS AW3D30 (30m)");
    console.log("   Backend:  AWS Open Data / OpenTopography S3");
    console.log("   Auth:     Zero-Config (Free public direct COGs)");

    console.log("\n[LANDCOVER] - Land Use / Land Cover Classification (10m LULC)");
    console.log("   Sources:  ESA WorldCover 10m (2020 v100, 2021 v200)");
    console.log("   Backend:  ESA WorldCover AWS Open Data S3");
    console.log("   Auth:     Zero-Config (Free public direct COGs)");

    console.log("\n[WEATHER] - Weather & Climate Profiles");
    console.log("   Sources:  Open-Meteo Zero-Config Global Model, ERA5 Reanalysis, FAO-56 ET0, VPD");
    console.log("   Backend:  Open-Meteo REST API");
    console.log("   Auth:     Zero-Config (No API key needed)");

    console.log("\n[SOIL] - Soil Composition & 3D Profiles");
    console.log("   Sources:  ISRIC SoilGrids v2.0 (250m global)");
    console.log("   Backend:  ISRIC REST API");
    console.log("   Auth:     Zero-Config (Public)");

    console.log("\n[ATMOSPHERE] - Atmospheric Composition & Trace Gases");
    console.log("   Sources:  Copernicus Sentinel-5P TROPOMI (NO2, CO, CH4, SO2), CAMS ECMWF Air Quality");
    console.log("   Backend:  Copernicus Data Space STAC / Open-Meteo Air Quality");
    console.log("   Auth:     Zero-Config (Public)");

    console.log("\n[FIRE] - Active Fire & Thermal Anomalies");
    console.log("   Sources:  NASA FIRMS VIIRS 375m (Suomi-NPP, NOAA-20), MODIS 1km");
    console.log("   Backend:  NASA FIRMS REST API");
    console.log("   Auth:     Zero-Config (Public)");

    console.log("\n[OCEAN] - Ocean Color, Marine Biology & SST");
    console.log("   Sources:  Copernicus Sentinel-3 OLCI (21 bands Chlorophyll-a), Sentinel-3 SLSTR (SST)");
    console.log("   Backend:  Copernicus Data Space STAC / EUMETSAT Data Store");
    console.log("   Auth:     Zero-Config (Public)");

    console.log("\n[ALTIMETRY] - Radar Altimetry & Water Surface Levels");
    console.log("   Sources:  Copernicus Sentinel-6 Michael Freilich (Poseidon-4 SAR Altimeter), Jason-3");
    console.log("   Backend:  PO.DAAC CMR STAC / Copernicus Marine");
    console.log("   Auth:     Zero-Config (Public)");

    console.log("\n[PRECIPITATION] - High-Resolution Precipitation & Rainfall Climatology");
    console.log("   Sources:  NASA GPM IMERG (0.1 deg half-hourly/daily), CHIRPS v2.0 (0.05 deg daily)");
    console.log("   Backend:  NASA CMR STAC / UCSB CHIRPS AWS Open Data");
    console.log("   Auth:     Zero-Config (Public)");

    console.log("\n[HYDROLOGY] - Hydrology & Root-Zone Soil Moisture");
    console.log("   Sources:  NASA SMAP (L-band Radiometer 9km/3km), CGLS Soil Water Index");
    console.log("   Backend:  NSIDC DAAC CMR STAC");
    console.log("   Auth:     Zero-Config (Public)");

    console.log("\n[NIGHTLIGHTS] - Nighttime Lights & Nocturnal Radiance");
    console.log("   Sources:  Suomi-NPP / NOAA-20 VIIRS Day/Night Band (DNB), NASA Black Marble");
    console.log("   Backend:  NASA LPCLOUD CMR STAC");
    console.log("   Auth:     Zero-Config (Public)");
    console.log("\n+" + "-".repeat(width - 2) + "+");
  });

program
  .command("info")
  .description("Display engine status, versions, and credential health")
  .action(() => {
    console.log(ASCII_BANNER);
    const width = 75;
    console.log("+" + "-".repeat(width - 2) + "+");
    console.log("| OmniEarth Engine v1.5.0 (Node.js SDK) Diagnostic Dashboard".padEnd(width - 1) + "|");
    console.log("| Author: Lokesh Kumar (lokesh.skshukla@gmail.com)".padEnd(width - 1) + "|");
    console.log("| Homepage: https://lokeshsk.github.io/omniearth/".padEnd(width - 1) + "|");
    console.log("+" + "-".repeat(width - 2) + "+");
    console.log("\n[Credential & Environment Status]");
    const [dlrU] = config.dlrCredentials;
    const [prismaU] = config.prismaCredentials;
    const [edU] = config.earthdataCredentials;

    console.log(`  * DLR Geoservice (EnMAP):     [${dlrU ? "Configured" : "Optional (Needed for EnMAP raw download)"}]`);
    console.log(`  * ASI PRISMA Portal:          [${prismaU ? "Configured" : "Optional (Needed for PRISMA download)"}]`);
    console.log(`  * NASA Earthdata (EMIT):       [${edU ? "Configured" : "Optional (Needed for NASA EMIT direct cubes)"}]`);
    console.log("  * Open-Meteo (Weather):        [Native Zero-Config]");
    console.log("  * ISRIC SoilGrids (Soil):      [Native Zero-Config]");
    console.log("  * AWS Earth Search (S1, S2):   [Native Zero-Config]");
    console.log("  * AWS Open Data (DEM GLO-30):  [Native Zero-Config]");
    console.log("  * ESA WorldCover (10m LULC):   [Native Zero-Config]");
    console.log("+" + "-".repeat(width - 2) + "+");
  });

program
  .command("search")
  .description("Search for satellite scenes, weather, elevation, land cover, or soil data")
  .requiredOption("-c, --category <category>", "Data category (optical, hyperspectral, sar, elevation, landcover, weather, soil)")
  .option("--bbox <coords...>", "Bounding box: min_lon min_lat max_lon max_lat")
  .option("--point <coords...>", "Point: lon lat [radius_km]")
  .option("--geojson <path_or_str>", "Path to GeoJSON file or inline GeoJSON string")
  .option("--start <date>", "Start date (YYYY-MM-DD)")
  .option("--end <date>", "End date (YYYY-MM-DD)")
  .option("--max-cloud <percent>", "Max cloud cover percentage")
  .option("--dataset <dataset>", "Specific dataset (e.g. copernicus, srtm, alos)")
  .option("--year <year>", "Specific year (e.g. 2020, 2021)")
  .option("--level <level>", "Processing level for optical: 'sr' (Surface Reflectance L2A) or 'toa' (Top of Atmosphere L1C)", "sr")
  .option("--limit <number>", "Maximum number of results", "5")
  .option("--download-all", "Download all matching search results concurrently")
  .option("--download-top <number>", "Download the top N matching search results")
  .option("--select <indices>", "Comma-separated 1-based indices to download (e.g. '1,3' or '1-2')")
  .option("-i, --interactive", "Prompt interactively to select and download scenes from search results")
  .option("-o, --outdir <path>", "Output directory for downloads", "./omniearth_downloads")
  .option("-t, --threads <number>", "Number of parallel worker threads", "4")
  .option("--asset <key>", "Specific asset key to download")
  .option("--export <path>", "Export search results to .geojson or .csv file")
  .option("--provider <provider>", "Data provider (e.g. cdse, aws, dlr_enmap)")
  .option("--format <format>", "Product format (safe, raw, cog)")
  .option("--bands <bands>", "Band preset or comma-separated bands (e.g. rgb, ndvi, B04,B03,B02)")
  .option("--verify-checksum", "Validate cryptographic hash of downloaded data")
  .option("--composite <type>", "Automatically generate 3-band composite GeoTIFF (rgb, false-color, swir)")
  .option("--no-resume", "Disable byte-range download resumption")
  .option("--no-multipart", "Disable parallel chunked multipart downloading")
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
      const bandsList = opts.bands
        ? (opts.bands as string).split(",").map((s) => s.trim()).filter(Boolean)
        : undefined;

      const results = await client.search({
        category: opts.category as Category,
        bbox,
        point,
        geojson: opts.geojson,
        startDate: opts.start,
        endDate: opts.end,
        maxCloudCover: opts.maxCloud ? Number(opts.maxCloud) : undefined,
        dataset: opts.dataset,
        year: opts.year ? parseInt(opts.year, 10) : undefined,
        level: opts.level,
        limit: Number(opts.limit),
        provider: opts.provider,
        format: opts.format,
        bands: bandsList
      });

      if (opts.export) {
        const outExp = results.export(opts.export);
        console.log(`Exported ${results.length} search result(s) to: ${outExp}`);
      }

      if (opts.json) {
        console.log(JSON.stringify(results, null, 2));
        return;
      }

      const width = 75;
      console.log("+" + "-".repeat(width - 2) + "+");
      console.log(`| OmniEarth Search Results [${opts.category.toUpperCase()}] - ${results.length} item(s) found`.padEnd(width - 1) + "|");
      console.log("+" + "-".repeat(width - 2) + "+");

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
          console.log(`      * ${k}: [${a.media_type || "asset"}]`);
        }
      }
      console.log("\n" + "-".repeat(width));
      console.log("Tip: Download any scene using: omniearth download --category <cat> --id <ID>");
      console.log("+" + "-".repeat(width - 2) + "+");

      let targetToDownload: any[] | null = null;
      if (opts.downloadAll) {
        targetToDownload = [...results];
      } else if (opts.downloadTop) {
        targetToDownload = results.slice(0, parseInt(opts.downloadTop, 10));
      } else if (opts.select) {
        const indices: number[] = [];
        for (const part of (opts.select as string).split(",")) {
          const p = part.trim();
          if (p.includes("-") && !p.startsWith("-")) {
            const [start, end] = p.split("-").map((x) => parseInt(x, 10));
            if (!isNaN(start) && !isNaN(end)) {
              for (let idx = start; idx <= end; idx++) indices.push(idx - 1);
            }
          } else {
            const idx = parseInt(p, 10);
            if (!isNaN(idx)) indices.push(idx - 1);
          }
        }
        targetToDownload = indices.map((i) => results[i]).filter(Boolean);
      } else if (opts.interactive) {
        const readline = await import("readline");
        const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
        const answer = await new Promise<string>((resolve) => {
          rl.question("\nEnter indices to download (e.g. '1,3', '1-2', 'all', or 'q' to quit): ", (ans) => {
            rl.close();
            resolve(ans.trim());
          });
        });
        if (answer.toLowerCase() === "all") {
          targetToDownload = [...results];
        } else if (!["q", "quit", ""].includes(answer.toLowerCase())) {
          const indices: number[] = [];
          for (const part of answer.split(",")) {
            const p = part.trim();
            if (p.includes("-") && !p.startsWith("-")) {
              const [start, end] = p.split("-").map((x) => parseInt(x, 10));
              if (!isNaN(start) && !isNaN(end)) {
                for (let idx = start; idx <= end; idx++) indices.push(idx - 1);
              }
            } else {
              const idx = parseInt(p, 10);
              if (!isNaN(idx)) indices.push(idx - 1);
            }
          }
          targetToDownload = indices.map((i) => results[i]).filter(Boolean);
        }
      }

      if (targetToDownload && targetToDownload.length > 0) {
        const outdir = opts.outdir || "./omniearth_downloads";
        const downloadOpts = {
          resume: opts.resume !== false,
          multipart: opts.multipart !== false,
          concurrency: parseInt(opts.threads, 10) || 4,
          format: opts.format,
          bands: opts.bands,
          verifyChecksum: Boolean(opts.verifyChecksum),
          composite: opts.composite
        };
        console.log(`\nDispatching concurrent download for ${targetToDownload.length} scene(s) to: ${outdir}`);
        const paths = await client.downloadMany(targetToDownload, opts.asset, outdir, downloadOpts);
        console.log(`\nSuccessfully downloaded ${paths.length} scene(s):`);
        for (const p of paths) {
          console.log(`  * ${p}`);
        }
      }
    } catch (err: any) {
      console.error(`Error: ${err.message}`);
      process.exit(1);
    }
  });

program
  .command("download")
  .description("Download satellite data, hyperspectral cubes, or environmental profiles")
  .requiredOption("-c, --category <category>", "Data category")
  .option("--id <id>", "Product ID or comma-separated list of IDs to download")
  .option("--bbox <coords...>", "Bounding box to find scene for")
  .option("--geojson <path_or_str>", "Path to GeoJSON file or inline GeoJSON string")
  .option("--dataset <dataset>", "Specific dataset (e.g. copernicus, srtm, alos)")
  .option("--year <year>", "Specific year (e.g. 2020, 2021)")
  .option("--level <level>", "Processing level for optical: 'sr' (Surface Reflectance L2A) or 'toa' (Top of Atmosphere L1C)", "sr")
  .option("--asset <key>", "Specific asset key")
  .option("--provider <provider>", "Data provider (e.g. cdse, aws, dlr_enmap)")
  .option("--format <format>", "Product format (safe, raw, node, band, cog)")
  .option("--bands <bands>", "Band preset or comma-separated bands (e.g. rgb, ndvi, 10m, 20m, vh, vv, dual)")
  .option("--verify-checksum", "Validate cryptographic hash of downloaded data")
  .option("--composite <type>", "Automatically generate 3-band composite GeoTIFF (rgb, false-color, swir)")
  .option("-o, --outdir <path>", "Output directory", "./omniearth_downloads")
  .option("--limit <number>", "Maximum number of scenes to download when searching by AOI", "1")
  .option("--all-scenes", "Download all matching scenes found in AOI up to --limit")
  .option("--all", "Download all assets associated with the scene concurrently")
  .option("-i, --interactive", "Prompt interactively to choose specific assets or download all")
  .option("--folder", "Download scene assets into a dedicated subfolder named by the scene ID")
  .option("--zip", "Package downloaded scene assets into a .zip archive")
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
      concurrency: parseInt(opts.threads, 10) || 4,
      format: opts.format,
      bands: opts.bands,
      verifyChecksum: Boolean(opts.verifyChecksum),
      composite: opts.composite
    };

    try {
      const targetResults: any[] = [];
      if (opts.id) {
        const idList = (opts.id as string).split(",").map((s) => s.trim()).filter(Boolean);
        for (const tid of idList) {
          let item = await client.getItem(opts.category as Category, tid, opts.provider);
          if (!item) {
            let prov = opts.provider || opts.category;
            let coll = opts.category;
            const assetsDict: Record<string, any> = {};
            if (opts.category === "hyperspectral") {
              if (tid.startsWith("ENMAP") || tid.toLowerCase().includes("enmap")) {
                prov = "dlr_enmap";
                coll = "enmap-hsi-l2a";
                const dlUrl = `https://geoservice.dlr.de/eoc/ogc/wcs/v1?SERVICE=WCS&VERSION=2.0.1&REQUEST=GetCoverage&COVERAGEID=${tid}`;
                assetsDict["image"] = { key: "image", href: dlUrl, title: "Hyperspectral Data Cube", mediaType: "image/tiff" };
                assetsDict["data"] = assetsDict["image"];
              } else if (tid.startsWith("EMIT") || tid.toLowerCase().includes("emit")) {
                prov = "nasa_lpdaac";
                coll = "emit-l2a-rfl";
                const dlUrl = `https://data.lpdaac.earthdatacloud.nasa.gov/lp-prod-protected/EMITL2ARFL.001/${tid}/${tid}.nc`;
                assetsDict["data"] = { key: "data", href: dlUrl, title: "EMIT NetCDF Cube", mediaType: "application/x-netcdf" };
              } else if (tid.startsWith("PRS") || tid.toLowerCase().includes("prisma")) {
                prov = "asi_prisma";
                coll = "asi-prisma-l2d";
                const dlUrl = `https://prisma.asi.it/download/${tid}.he5`;
                assetsDict["data"] = { key: "data", href: dlUrl, title: "PRISMA HDF5 Cube", mediaType: "application/x-hdf5" };
              } else {
                prov = "dlr_enmap";
                coll = "enmap-hsi-l2a";
                const dlUrl = `https://geoservice.dlr.de/eoc/ogc/wcs/v1?SERVICE=WCS&VERSION=2.0.1&REQUEST=GetCoverage&COVERAGEID=${tid}`;
                assetsDict["image"] = { key: "image", href: dlUrl, title: "Hyperspectral Data Cube", mediaType: "image/tiff" };
                assetsDict["data"] = assetsDict["image"];
              }
            } else if (["optical", "sar", "ocean", "atmosphere"].includes(opts.category)) {
              if (prov === "cdse" || tid.startsWith("S1") || tid.startsWith("S2") || tid.startsWith("S3") || tid.startsWith("S5P")) {
                prov = "cdse";
                coll = opts.category === "optical" ? "SENTINEL-2" : (opts.category === "sar" ? "SENTINEL-1" : "SENTINEL-3");
                const dlUrl = `https://dataspace.copernicus.eu/odata/v1/Products(${tid})/$value`;
                assetsDict["data"] = { key: "data", href: dlUrl, title: "CDSE Product Archive", mediaType: "application/zip" };
              }
            } else if (opts.category === "elevation") {
              prov = "aws_copernicus_dem";
              coll = "copernicus-dem-glo-30";
              const dlUrl = `https://copernicus-dem-30m.s3.amazonaws.com/${tid}/${tid}.tif`;
              assetsDict["data"] = { key: "data", href: dlUrl, title: "DEM GeoTIFF", mediaType: "image/tiff" };
            } else if (opts.category === "landcover") {
              prov = "aws_worldcover";
              coll = "esa-worldcover-10m";
              const dlUrl = `https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/${tid}.tif`;
              assetsDict["data"] = { key: "data", href: dlUrl, title: "WorldCover GeoTIFF", mediaType: "image/tiff" };
            }
            item = {
              id: tid,
              collection: coll,
              category: opts.category,
              provider: prov,
              assets: assetsDict,
              properties: {}
            };
          }
          targetResults.push(item);
        }
      } else if (bbox || opts.geojson) {
        const limitVal = parseInt(opts.limit, 10) || 1;
        const results = await client.search({
          category: opts.category as Category,
          bbox,
          geojson: opts.geojson,
          dataset: opts.dataset,
          year: opts.year ? parseInt(opts.year, 10) : undefined,
          level: opts.level,
          limit: limitVal,
          provider: opts.provider,
          format: opts.format
        });
        if (results.length === 0) {
          console.error("No matching scenes found to download.");
          process.exit(1);
        }
        if (opts.allScenes || limitVal > 1) {
          targetResults.push(...results);
          console.log(`Found ${targetResults.length} scene(s) matching criteria.`);
        } else {
          targetResults.push(results[0]);
          console.log(`Selected latest scene: ${results[0].id} (${results[0].datetime})`);
        }
      } else {
        console.error("Error: Must specify either --id, --bbox, or --geojson to download.");
        process.exit(1);
      }

      const width = 75;
      console.log("+" + "-".repeat(width - 2) + "+");
      console.log("| OmniEarth Download Dispatch (Node.js)".padEnd(width - 1) + "|");
      const targetDisp = targetResults.length === 1 ? (targetResults[0].id || opts.id || "Search Match") : `${targetResults.length} item(s)`;
      console.log(`| Target(s):  ${targetDisp}`.padEnd(width - 1) + "|");
      console.log(`| Category:   ${opts.category}`.padEnd(width - 1) + "|");
      console.log(`| Directory:  ${opts.outdir}`.padEnd(width - 1) + "|");
      console.log("+" + "-".repeat(width - 2) + "+");

      if (targetResults.length === 1) {
        const targetResult = targetResults[0];
        if (opts.interactive && targetResult.assets) {
          const availKeys = Object.keys(targetResult.assets).filter((k) => !k.startsWith("s3_") && (!targetResult.assets[k].href || !targetResult.assets[k].href.startsWith("s3://")));
          if (availKeys.length > 0) {
            console.log(`\nAvailable assets for '${targetResult.id}':`);
            availKeys.forEach((k, idx) => {
              const a = targetResult.assets[k];
              const baseName = (k.split("/").pop() || k);
              const mtype = a.mediaType || a.media_type ? ` [${a.mediaType || a.media_type}]` : "";
              console.log(`  [${idx + 1}] ${baseName}${mtype}`);
            });
            console.log("  [a] all (download all assets into dedicated folder)");
            const readline = await import("readline");
            const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
            const answer: string = await new Promise((resolve) => {
              rl.question("\nSelect asset to download (1-N, 'all', or 'q' to quit): ", (ans) => {
                rl.close();
                resolve(ans.trim().toLowerCase());
              });
            });
            if (answer === "q" || answer === "quit" || !answer) {
              console.log("Download cancelled.");
              return;
            } else if (answer === "a" || answer === "all") {
              opts.all = true;
            } else {
              const num = parseInt(answer, 10);
              if (num >= 1 && num <= availKeys.length) {
                opts.asset = availKeys[num - 1];
              }
            }
          }
        }

        const resolvedKey = resolveAssetKey(targetResult, opts.asset);
        const finalAssetKey = resolvedKey || opts.asset;

        if (opts.all || (opts.zip && !opts.asset)) {
          const downloaded = await client.downloadAll(targetResult, undefined, opts.outdir, { ...downloadOpts, folder: true, zip: opts.zip });
          if (opts.zip && downloaded["zip"]) {
            console.log(`\nSuccessfully archived scene package: ${downloaded["zip"]}`);
          } else {
            const targetDirDisp = (opts.folder || opts.all) ? `${opts.outdir}/${targetResult.id}` : opts.outdir;
            console.log(`Successfully downloaded ${Object.keys(downloaded).length} asset(s) to: ${targetDirDisp}`);
            for (const [k, p] of Object.entries(downloaded)) {
              console.log(`  * ${k}: ${p}`);
            }
          }
        } else {
          const filePath = await client.download(targetResult, finalAssetKey, opts.outdir, { ...downloadOpts, folder: opts.folder || opts.zip, zip: opts.zip });
          if (opts.zip) {
            console.log(`\nSuccessfully archived scene package: ${filePath}`);
          } else {
            console.log(`Successfully downloaded: ${filePath}`);
          }
        }
      } else {
        console.log(`Downloading ${targetResults.length} scenes concurrently with ${downloadOpts.concurrency} worker thread(s)...`);
        const paths = await client.downloadMany(targetResults, opts.asset, opts.outdir, downloadOpts);
        console.log(`\nSuccessfully downloaded ${paths.length} scene(s) to: ${opts.outdir}`);
        for (const p of paths) {
          console.log(`  * ${p}`);
        }
      }
    } catch (err: any) {
      console.error(`Error: Download failed: ${err.message}`);
      process.exit(1);
    }
  });

program
  .command("compute")
  .description("Compute remote sensing radiometric index on inputs (NDVI, NDWI, NDRE, EVI, NBR, SAVI, MSAVI, BSI, MNDWI)")
  .requiredOption("--index <index>", "Index to compute: ndvi, ndwi, ndre, evi, nbr, savi, msavi, bsi, mndwi")
  .requiredOption("--nir <nir>", "NIR value or JSON array")
  .option("--red <red>", "Red value or JSON array")
  .option("--green <green>", "Green value or JSON array")
  .option("--blue <blue>", "Blue value or JSON array")
  .option("--rededge <rededge>", "RedEdge value or JSON array")
  .option("--swir <swir>", "SWIR value or JSON array")
  .option("--l-factor <factor>", "Soil adjustment factor L for SAVI (default: 0.5)", "0.5")
  .action((opts) => {
    const client = new OmniEarth();
    const parse = (v?: string) => {
      if (!v) return undefined;
      try {
        return JSON.parse(v);
      } catch {
        return parseFloat(v);
      }
    };
    try {
      const res = client.computeIndex(opts.index, {
        nir: parse(opts.nir),
        red: parse(opts.red),
        green: parse(opts.green),
        blue: parse(opts.blue),
        rededge: parse(opts.rededge),
        swir: parse(opts.swir),
        lFactor: opts.lFactor ? parseFloat(opts.lFactor) : 0.5
      });
      const width = 75;
      console.log("+" + "-".repeat(width - 2) + "+");
      console.log(`| OmniEarth Radiometric Index Calculation [${opts.index.toUpperCase()}]`.padEnd(width - 1) + "|");
      console.log("+" + "-".repeat(width - 2) + "+");
      console.log(`  Result: ${JSON.stringify(res)}`);
      console.log("+" + "-".repeat(width - 2) + "+");
    } catch (err: any) {
      console.error(`Error computing index: ${err.message}`);
      process.exit(1);
    }
  });

program
  .command("timeseries")
  .description("Extract chronological observations over time")
  .requiredOption("-c, --category <category>", "Data category")
  .option("--bbox <coords...>", "Bounding box: min_lon min_lat max_lon max_lat")
  .option("--geojson <path_or_str>", "Path to GeoJSON file or inline GeoJSON string")
  .option("--start <date>", "Start date (YYYY-MM-DD)")
  .option("--end <date>", "End date (YYYY-MM-DD)")
  .option("--limit <number>", "Maximum number of items", "30")
  .option("--json", "Output raw JSON format")
  .action(async (opts) => {
    const client = new OmniEarth();
    let bbox: [number, number, number, number] | undefined;
    if (opts.bbox) {
      const parts = opts.bbox.map(Number);
      if (parts.length === 4) {
        bbox = [parts[0], parts[1], parts[2], parts[3]];
      }
    }
    try {
      const series = await client.getTimeSeries({
        category: opts.category as Category,
        bbox,
        geojson: opts.geojson,
        startDate: opts.start,
        endDate: opts.end,
        limit: Number(opts.limit)
      });

      if (opts.json) {
        console.log(JSON.stringify(series, null, 2));
        return;
      }

      const width = 75;
      console.log("+" + "-".repeat(width - 2) + "+");
      console.log(`| OmniEarth Time-Series [${opts.category.toUpperCase()}] - ${series.length} record(s)`.padEnd(width - 1) + "|");
      console.log("+" + "-".repeat(width - 2) + "+");
      for (let i = 0; i < Math.min(series.length, 15); i++) {
        const item = series[i];
        console.log(`[${String(i + 1).padStart(2, "0")}] ${item.datetime || "N/A"} | ${JSON.stringify(item)}`);
      }
      if (series.length > 15) {
        console.log(`... and ${series.length - 15} more records (use --json for complete time series)`);
      }
      console.log("+" + "-".repeat(width - 2) + "+");
    } catch (err: any) {
      console.error(`Error extracting time-series: ${err.message}`);
      process.exit(1);
    }
  });

export function runCLI() {
  program.parse(process.argv);
}

if (process.argv[1]?.endsWith("cli.js") || process.argv[1]?.endsWith("cli.ts")) {
  runCLI();
}
