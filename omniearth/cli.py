"""
OmniEarth CLI
=============
Universal command-line interface for multi-modal Earth Observation data.
"""

import sys
import os
import json
import argparse
from typing import List

import omniearth
from omniearth.client import OmniEarth
from omniearth.models import Category
from omniearth.config import config

ASCII_BANNER = r"""  ___  __  __ _   _ ___ _____    _    ____ _____ _   _ 
 / _ \|  \/  | \ | |_ _| ____|  / \  |  _ \_   _| | | |
| | | | |\/| |  \| || ||  _|   / _ \ | |_) || | | |_| |
| |_| | |  | | |\  || || |___ / ___ \|  _ < | | |  _  |
 \___/|_|  |_|_| \_|___|_____/_/   \_\_| \_\|_| |_| |_|"""


def format_size(bytes_num: int) -> str:
    """Format bytes into human-readable string."""
    if not bytes_num or bytes_num <= 0:
        return "Unknown size"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_num < 1024.0:
            return f"{bytes_num:.1f} {unit}"
        bytes_num /= 1024.0
    return f"{bytes_num:.1f} PB"


def cmd_categories(args, client: OmniEarth):
    """List supported categories and their capabilities."""
    width = 75
    print("+" + "-" * (width - 2) + "+")
    print(f"| OmniEarth Supported Modalities & Data Providers".ljust(width - 1) + "|")
    print("+" + "-" * (width - 2) + "+")
    categories = {
        "optical": {
            "name": "Optical Multispectral Imagery",
            "satellites": ["Sentinel-2 L2A (10m)", "Landsat-8/9 (30m)"],
            "backend": "AWS Open Data STAC / Element84 Earth Search",
            "auth": "Zero-Config (Free public egress COGs)"
        },
        "hyperspectral": {
            "name": "Hyperspectral Data Cubes (200+ Bands)",
            "satellites": ["DLR EnMAP (224 bands)", "NASA EMIT (285 bands)", "ASI PRISMA (240 bands)"],
            "backend": "DLR EOC STAC, NASA CMR STAC, ASI PRISMA Portal",
            "auth": "DLR Credentials (Free) / NASA Earthdata (Free)"
        },
        "sar": {
            "name": "Synthetic Aperture Radar (SAR)",
            "satellites": ["Sentinel-1 GRD / RTC (10m)"],
            "backend": "AWS Open Data STAC",
            "auth": "Zero-Config (Public COGs)"
        },
        "elevation": {
            "name": "Digital Elevation Models (DEM / DSM / DTM 30m)",
            "sources": ["Copernicus DEM GLO-30 (30m DSM)", "SRTM GL1 (30m)", "ALOS AW3D30 (30m)"],
            "backend": "AWS Open Data / OpenTopography S3",
            "auth": "Zero-Config (Free public direct COGs)"
        },
        "landcover": {
            "name": "Land Use / Land Cover Classification (10m LULC)",
            "sources": ["ESA WorldCover 10m (2020 v100, 2021 v200)"],
            "backend": "ESA WorldCover AWS Open Data S3",
            "auth": "Zero-Config (Free public direct COGs)"
        },
        "weather": {
            "name": "Weather & Climate Profiles",
            "sources": ["Open-Meteo Zero-Config Global Model", "ERA5 Reanalysis", "FAO-56 ET0", "VPD"],
            "backend": "Open-Meteo REST API",
            "auth": "Zero-Config (No API key needed)"
        },
        "soil": {
            "name": "Soil Composition & 3D Profiles",
            "sources": ["ISRIC SoilGrids v2.0 (250m global)"],
            "backend": "ISRIC REST API",
            "auth": "Zero-Config (Public)"
        },
        "atmosphere": {
            "name": "Atmospheric Composition & Trace Gases",
            "sources": ["Copernicus Sentinel-5P TROPOMI", "CAMS ECMWF Air Quality"],
            "backend": "Copernicus Data Space STAC / Open-Meteo Air Quality",
            "auth": "Zero-Config (Public)"
        },
        "fire": {
            "name": "Active Fire & Thermal Anomalies",
            "sources": ["NASA FIRMS VIIRS 375m (Suomi-NPP, NOAA-20)", "MODIS 1km"],
            "backend": "NASA FIRMS REST API",
            "auth": "Zero-Config (Public)"
        },
        "ocean": {
            "name": "Ocean Color, Marine Biology & SST",
            "sources": ["Copernicus Sentinel-3 OLCI (21 bands)", "Sentinel-3 SLSTR (SST)"],
            "backend": "Copernicus Data Space STAC / EUMETSAT",
            "auth": "Zero-Config (Public)"
        },
        "altimetry": {
            "name": "Radar Altimetry & Water Surface Levels",
            "sources": ["Copernicus Sentinel-6 Michael Freilich (Poseidon-4 SAR)", "Jason-3"],
            "backend": "PO.DAAC CMR STAC / Copernicus Marine",
            "auth": "Zero-Config (Public)"
        },
        "precipitation": {
            "name": "High-Resolution Precipitation & Rainfall Climatology",
            "sources": ["NASA GPM IMERG (0.1 deg half-hourly/daily)", "CHIRPS v2.0 (0.05 deg)"],
            "backend": "NASA CMR STAC / UCSB CHIRPS AWS Open Data",
            "auth": "Zero-Config (Public)"
        },
        "hydrology": {
            "name": "Hydrology & Root-Zone Soil Moisture",
            "sources": ["NASA SMAP (L-band Radiometer 9km/3km)", "CGLS Soil Water Index"],
            "backend": "NSIDC DAAC CMR STAC",
            "auth": "Zero-Config (Public)"
        },
        "nightlights": {
            "name": "Nighttime Lights & Nocturnal Radiance",
            "sources": ["Suomi-NPP / NOAA-20 VIIRS Day/Night Band (DNB)", "NASA Black Marble"],
            "backend": "NASA LPCLOUD CMR STAC",
            "auth": "Zero-Config (Public)"
        }
    }

    for cat_id, info in categories.items():
        print(f"\n[{cat_id.upper()}] - {info['name']}")
        if "satellites" in info:
            print(f"   Sensors:  {', '.join(info['satellites'])}")
        if "sources" in info:
            print(f"   Sources:  {', '.join(info['sources'])}")
        print(f"   Backend:  {info['backend']}")
        print(f"   Auth:     {info['auth']}")
    print("\n+" + "-" * (width - 2) + "+")


def cmd_info(args, client: OmniEarth):
    """Display system status, versions, and credential health."""
    print(ASCII_BANNER)
    width = 75
    print("+" + "-" * (width - 2) + "+")
    print(f"| OmniEarth Engine v{omniearth.__version__} Diagnostic Dashboard".ljust(width - 1) + "|")
    print(f"| Author: Lokesh Kumar (lokesh.skshukla@gmail.com)".ljust(width - 1) + "|")
    print(f"| Homepage: https://lokeshsk.github.io/omniearth/".ljust(width - 1) + "|")
    print("+" + "-" * (width - 2) + "+")

    print("\n[Credential & Environment Status]")
    dlr_u = config.get("DLR_USERNAME")
    dlr_p = config.get("DLR_PASSWORD")
    dlr_status = "Configured" if (dlr_u and dlr_p) else "Optional (Needed for EnMAP raw download)"

    prisma_u = config.get("PRISMA_USERNAME")
    prisma_status = "Configured" if prisma_u else "Optional (Needed for PRISMA download)"

    ed_u = config.get("EARTHDATA_USERNAME")
    ed_status = "Configured" if ed_u else "Optional (Needed for NASA EMIT direct cubes)"

    print(f"  * DLR Geoservice (EnMAP):     [{dlr_status}]")
    print(f"  * ASI PRISMA Portal:          [{prisma_status}]")
    print(f"  * NASA Earthdata (EMIT):       [{ed_status}]")
    print(f"  * Open-Meteo (Weather):        [Native Zero-Config]")
    print(f"  * ISRIC SoilGrids (Soil):      [Native Zero-Config]")
    print(f"  * AWS Earth Search (S1, S2):   [Native Zero-Config]")
    print(f"  * AWS Open Data (Copernicus DEM): [Native Zero-Config]")
    print(f"  * ESA WorldCover (10m LULC):   [Native Zero-Config]")
    print("+" + "-" * (width - 2) + "+")


def cmd_search(args, client: OmniEarth):
    """Search for data in a specific category."""
    bbox = None
    point = None
    geojson_raw = getattr(args, "geojson", None)
    geojson = geojson_raw if isinstance(geojson_raw, (str, dict)) else None

    if args.bbox:
        if len(args.bbox) != 4:
            print("Error: --bbox requires 4 values: min_lon min_lat max_lon max_lat", file=sys.stderr)
            sys.exit(1)
        bbox = [float(x) for x in args.bbox]
    elif args.point:
        if len(args.point) < 2:
            print("Error: --point requires at least 2 values: lon lat [radius_km]", file=sys.stderr)
            sys.exit(1)
        point = tuple([float(x) for x in args.point])
    elif not geojson:
        print("Error: Must provide either --bbox, --point, or --geojson.", file=sys.stderr)
        sys.exit(1)

    variables = args.variables.split(",") if args.variables else None

    dataset_raw = getattr(args, "dataset", None)
    dataset = dataset_raw if isinstance(dataset_raw, str) else None
    year_raw = getattr(args, "year", None)
    year = year_raw if isinstance(year_raw, int) else None
    level = getattr(args, "level", "sr")

    provider_raw = getattr(args, "provider", None)
    provider = provider_raw if isinstance(provider_raw, str) else None
    format_raw = getattr(args, "format", None)
    format_val = format_raw if isinstance(format_raw, str) else None
    bands_raw = getattr(args, "bands", None)
    bands_str = bands_raw if isinstance(bands_raw, str) else None
    bands_val = [b.strip() for b in bands_str.split(",") if b.strip()] if (bands_str and "," in bands_str) else ([bands_str] if bands_str else None)
    export_raw = getattr(args, "export", None)
    export_path = export_raw if isinstance(export_raw, str) else None
    verify_checksum = getattr(args, "verify_checksum", False) is True
    composite_raw = getattr(args, "composite", None)
    composite = composite_raw if isinstance(composite_raw, str) else None

    extra_search_kwargs = {}
    if provider is not None:
        extra_search_kwargs["provider"] = provider
    if format_val is not None:
        extra_search_kwargs["format"] = format_val
    if bands_val is not None:
        extra_search_kwargs["bands"] = bands_val

    try:
        results = client.search(
            category=args.category,
            bbox=bbox,
            point=point,
            geojson=geojson,
            start_date=args.start,
            end_date=args.end,
            max_cloud_cover=args.max_cloud,
            variables=variables,
            depth=args.depth,
            dataset=dataset,
            year=year,
            level=level,
            limit=args.limit,
            **extra_search_kwargs
        )
    except Exception as e:
        print(f"Error during search: {e}", file=sys.stderr)
        sys.exit(1)

    if export_path:
        if hasattr(results, "export"):
            out_exp = results.export(export_path)
            print(f"Exported {len(results)} search result(s) to: {out_exp}")

    if args.json:
        data = [r.to_dict() for r in results]
        print(json.dumps(data, indent=2))
        return

    width = 75
    print("+" + "-" * (width - 2) + "+")
    print(f"| OmniEarth Search Results [{args.category.upper()}] - {len(results)} item(s) found".ljust(width - 1) + "|")
    print("+" + "-" * (width - 2) + "+")

    if not results:
        print("No items found matching the specified criteria.")
        return

    for i, r in enumerate(results, 1):
        item_title = r.properties.get("title") or r.id
        platform_info = r.properties.get("platform") or r.provider
        print(f"\n[{i}] {item_title}")
        print(f"    ID:         {r.id}")
        print(f"    Provider:   {r.provider} ({r.collection})")
        print(f"    Platform:   {platform_info}")
        print(f"    Datetime:   {r.datetime}")
        if r.cloud_cover is not None:
            print(f"    Cloud:      {r.cloud_cover:.1f}%")
        print(f"    Assets ({len(r.assets)}):")
        for k, a in r.assets.items():
            sz = f" ({format_size(a.size_bytes)})" if a.size_bytes else ""
            mtype = f" [{a.media_type}]" if a.media_type else ""
            print(f"      - {k}:{mtype}{sz}")
    print("\n" + "-" * width)
    print("Tip: Download any scene using: omniearth download --category <cat> --id <ID>")
    print("+" + "-" * (width - 2) + "+")

    target_to_download = None
    if getattr(args, "download_all", False) is True:
        target_to_download = list(results)
    elif getattr(args, "download_top", None) is not None and isinstance(args.download_top, int) and args.download_top > 0:
        target_to_download = list(results[:args.download_top])
    elif getattr(args, "select", None) and isinstance(args.select, str):
        indices = []
        for part in args.select.split(","):
            part = part.strip()
            if "-" in part and not part.startswith("-"):
                bounds = part.split("-")
                if len(bounds) == 2 and bounds[0].isdigit() and bounds[1].isdigit():
                    indices.extend(range(int(bounds[0]) - 1, int(bounds[1])))
            elif part.isdigit():
                indices.append(int(part) - 1)
        target_to_download = [results[i] for i in indices if 0 <= i < len(results)]
    elif getattr(args, "interactive", False) is True:
        try:
            choice = input("\nEnter indices to download (e.g. '1,3', '1-2', 'all', or 'q' to quit): ").strip()
        except (EOFError, KeyboardInterrupt):
            choice = "q"
        if choice.lower() == "all":
            target_to_download = list(results)
        elif choice.lower() in ("q", "quit", ""):
            target_to_download = None
        else:
            indices = []
            for part in choice.split(","):
                part = part.strip()
                if "-" in part and not part.startswith("-"):
                    bounds = part.split("-")
                    if len(bounds) == 2 and bounds[0].isdigit() and bounds[1].isdigit():
                        indices.extend(range(int(bounds[0]) - 1, int(bounds[1])))
                elif part.isdigit():
                    indices.append(int(part) - 1)
            target_to_download = [results[i] for i in indices if 0 <= i < len(results)]

    if target_to_download:
        outdir = getattr(args, "outdir", None) or "./omniearth_downloads"
        resume = getattr(args, "no_resume", False) is not True
        multipart = getattr(args, "no_multipart", False) is not True
        threads_val = getattr(args, "threads", 4)
        threads = threads_val if isinstance(threads_val, int) and threads_val > 0 else 4
        print(f"\nDispatching concurrent download for {len(target_to_download)} scene(s) to: {outdir}")

        extra_dl_kwargs = {}
        if format_val is not None:
            extra_dl_kwargs["format"] = format_val
        if bands_str is not None:
            extra_dl_kwargs["bands"] = bands_str
        if verify_checksum:
            extra_dl_kwargs["verify_checksum"] = verify_checksum
        if composite is not None:
            extra_dl_kwargs["composite"] = composite

        paths = client.download_many(
            results=target_to_download,
            asset_key=getattr(args, "asset", None) if isinstance(getattr(args, "asset", None), str) else None,
            outdir=outdir,
            max_workers=threads,
            resume=resume,
            multipart=multipart,
            **extra_dl_kwargs
        )
        print(f"\nSuccessfully downloaded {len(paths)} scene(s):")
        for p in paths:
            print(f"  * {p}")


def cmd_download(args, client: OmniEarth):
    """Download an asset from search results or scene ID."""
    bbox = None
    if args.bbox:
        bbox = [float(x) for x in args.bbox]

    geojson_raw = getattr(args, "geojson", None)
    geojson = geojson_raw if isinstance(geojson_raw, (str, dict)) else None

    id_raw = getattr(args, "id", None)
    target_ids_str = id_raw if isinstance(id_raw, str) else None

    dataset_raw = getattr(args, "dataset", None)
    dataset = dataset_raw if isinstance(dataset_raw, str) else None
    year_raw = getattr(args, "year", None)
    year = year_raw if isinstance(year_raw, int) else None

    provider_raw = getattr(args, "provider", None)
    provider = provider_raw if isinstance(provider_raw, str) else None
    format_raw = getattr(args, "format", None)
    format_val = format_raw if isinstance(format_raw, str) else None
    bands_raw = getattr(args, "bands", None)
    bands_str = bands_raw if isinstance(bands_raw, str) else None
    verify_checksum = getattr(args, "verify_checksum", False) is True
    composite_raw = getattr(args, "composite", None)
    composite = composite_raw if isinstance(composite_raw, str) else None

    extra_dl_kwargs = {}
    if format_val is not None:
        extra_dl_kwargs["format"] = format_val
    if bands_str is not None:
        extra_dl_kwargs["bands"] = bands_str
    if verify_checksum:
        extra_dl_kwargs["verify_checksum"] = verify_checksum
    if composite is not None:
        extra_dl_kwargs["composite"] = composite

    target_results: List[omniearth.models.SearchResult] = []

    if target_ids_str:
        id_list = [i.strip() for i in target_ids_str.split(",") if i.strip()]
        for target_id in id_list:
            print(f"Searching for item '{target_id}' in category '{args.category}'...")
            target_result = client.get_item(args.category, target_id, provider=provider)
            search_bbox = bbox or [-180, -90, 180, 90]

            if not target_result:
                results = client.search(
                    category=args.category,
                    bbox=search_bbox if not geojson else None,
                    geojson=geojson,
                    limit=50
                )
                for r in results:
                    if r.id == target_id:
                        target_result = r
                        break

            if not target_result:
                print(f"Notice: Item not found in recent catalog page; attempting direct provider resolution...")
                prov = provider or args.category
                coll = args.category
                assets_dict = {}
                if args.category == "hyperspectral":
                    if target_id.startswith("ENMAP") or "enmap" in target_id.lower():
                        prov = "dlr_enmap"
                        coll = "enmap-hsi-l2a"
                        dl_url = f"https://geoservice.dlr.de/eoc/ogc/wcs/v1?SERVICE=WCS&VERSION=2.0.1&REQUEST=GetCoverage&COVERAGEID={target_id}"
                        assets_dict["image"] = omniearth.models.Asset(key="image", href=dl_url, title="Hyperspectral Data Cube", media_type="image/tiff")
                        assets_dict["data"] = assets_dict["image"]
                    elif target_id.startswith("EMIT") or "emit" in target_id.lower():
                        prov = "nasa_lpdaac"
                        coll = "emit-l2a-rfl"
                        dl_url = f"https://data.lpdaac.earthdatacloud.nasa.gov/lp-prod-protected/EMITL2ARFL.001/{target_id}/{target_id}.nc"
                        assets_dict["data"] = omniearth.models.Asset(key="data", href=dl_url, title="EMIT NetCDF Cube", media_type="application/x-netcdf")
                    elif target_id.startswith("PRS") or "prisma" in target_id.lower():
                        prov = "asi_prisma"
                        coll = "asi-prisma-l2d"
                        dl_url = f"https://prisma.asi.it/download/{target_id}.he5"
                        assets_dict["data"] = omniearth.models.Asset(key="data", href=dl_url, title="PRISMA HDF5 Cube", media_type="application/x-hdf5")
                    else:
                        prov = "dlr_enmap"
                        coll = "enmap-hsi-l2a"
                        dl_url = f"https://geoservice.dlr.de/eoc/ogc/wcs/v1?SERVICE=WCS&VERSION=2.0.1&REQUEST=GetCoverage&COVERAGEID={target_id}"
                        assets_dict["image"] = omniearth.models.Asset(key="image", href=dl_url, title="Hyperspectral Data Cube", media_type="image/tiff")
                        assets_dict["data"] = assets_dict["image"]
                elif args.category in ("optical", "sar", "ocean", "atmosphere"):
                    if prov == "cdse" or target_id.startswith(("S1", "S2", "S3", "S5P")) or any(x in target_id for x in ("_MSIL", "_GRD", "_RAW", ".SAFE")):
                        prov = "cdse"
                        coll = "SENTINEL-2" if args.category == "optical" else ("SENTINEL-1" if args.category == "sar" else "SENTINEL-3")
                        dl_url = f"https://dataspace.copernicus.eu/odata/v1/Products({target_id})/$value"
                        assets_dict["data"] = omniearth.models.Asset(key="data", href=dl_url, title="CDSE Product Archive", media_type="application/zip")
                elif args.category == "elevation":
                    prov = "aws_copernicus_dem"
                    coll = "copernicus-dem-glo-30"
                    dl_url = f"https://copernicus-dem-30m.s3.amazonaws.com/{target_id}/{target_id}.tif"
                    assets_dict["data"] = omniearth.models.Asset(key="data", href=dl_url, title="DEM GeoTIFF", media_type="image/tiff")
                elif args.category == "landcover":
                    prov = "aws_worldcover"
                    coll = "esa-worldcover-10m"
                    dl_url = f"https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/{target_id}.tif"
                    assets_dict["data"] = omniearth.models.Asset(key="data", href=dl_url, title="WorldCover GeoTIFF", media_type="image/tiff")

                target_result = omniearth.models.SearchResult(
                    id=target_id,
                    collection=coll,
                    category=Category(args.category),
                    provider=prov,
                    datetime="2026-01-01T00:00:00Z",
                    bbox=search_bbox,
                    assets=assets_dict
                )
            target_results.append(target_result)
    elif bbox or geojson:
        loc_desc = f"bbox {bbox}" if bbox else f"geojson '{geojson}'"
        print(f"Searching for matching scenes in {loc_desc}...")
        level = getattr(args, "level", "sr")
        limit_val = getattr(args, "limit", 1) or 1
        extra_search_kwargs = {}
        if provider is not None:
            extra_search_kwargs["provider"] = provider
        if format_val is not None:
            extra_search_kwargs["format"] = format_val

        results = client.search(
            category=args.category,
            bbox=bbox,
            geojson=geojson,
            start_date=args.start,
            end_date=args.end,
            max_cloud_cover=args.max_cloud,
            dataset=dataset,
            year=year,
            level=level,
            limit=limit_val,
            **extra_search_kwargs
        )
        if not results:
            print("No matching scenes found to download.", file=sys.stderr)
            sys.exit(1)
        if getattr(args, "all_scenes", False) or limit_val > 1:
            target_results = list(results)
            print(f"Found {len(target_results)} scene(s) matching criteria.")
        else:
            target_results = [results[0]]
            print(f"Selected latest scene: {target_results[0].id} ({target_results[0].datetime})")
    else:
        print("Error: Must specify either --id, --bbox, or --geojson to download.", file=sys.stderr)
        sys.exit(1)

    outdir = getattr(args, "outdir", None) or "./omniearth_downloads"
    resume = getattr(args, "no_resume", False) is not True
    multipart = getattr(args, "no_multipart", False) is not True
    threads_val = getattr(args, "threads", 4)
    threads = threads_val if isinstance(threads_val, int) and threads_val > 0 else 4

    width = 75
    print("+" + "-" * (width - 2) + "+")
    print(f"| OmniEarth Download Dispatch".ljust(width - 1) + "|")
    target_disp = target_results[0].id if len(target_results) == 1 else f"{len(target_results)} item(s)"
    print(f"| Target(s):  {target_disp}".ljust(width - 1) + "|")
    print(f"| Category:   {args.category}".ljust(width - 1) + "|")
    print(f"| Directory:  {outdir}".ljust(width - 1) + "|")
    print("+" + "-" * (width - 2) + "+")

    try:
        if len(target_results) == 1:
            target_result = target_results[0]
            if getattr(args, "all", False) is True:
                print(f"Downloading all assets for '{target_result.id}' with {threads} worker thread(s)...")
                paths = client.download_all(
                    target_result,
                    outdir=outdir,
                    max_workers=threads,
                    resume=resume,
                    multipart=multipart,
                    **extra_dl_kwargs
                )
                print(f"\nSuccessfully downloaded {len(paths)} asset(s) to: {outdir}")
                for k, p in paths.items():
                    print(f"  * {k}: {p}")
            else:
                path = client.download(
                    target_result,
                    asset_key=getattr(args, "asset", None) if isinstance(getattr(args, "asset", None), str) else None,
                    outdir=outdir,
                    resume=resume,
                    multipart=multipart,
                    max_workers=threads,
                    **extra_dl_kwargs
                )
                print(f"\nSuccessfully downloaded: {path}")
        else:
            print(f"Downloading {len(target_results)} scenes concurrently with {threads} worker thread(s)...")
            paths = client.download_many(
                target_results,
                asset_key=getattr(args, "asset", None) if isinstance(getattr(args, "asset", None), str) else None,
                outdir=outdir,
                max_workers=threads,
                resume=resume,
                multipart=multipart,
                **extra_dl_kwargs
            )
            print(f"\nSuccessfully downloaded {len(paths)} scene(s) to: {outdir}")
            for p in paths:
                print(f"  * {p}")
    except Exception as e:
        print(f"\nError: Download failed: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_compute(args, client: OmniEarth):
    """Compute remote sensing radiometric index on inputs."""
    try:
        def parse_val(v):
            if v is None:
                return None
            try:
                return float(v)
            except ValueError:
                # In case a list or JSON string is passed
                return json.loads(v)

        nir = parse_val(args.nir)
        red = parse_val(args.red)
        green = parse_val(args.green)
        blue = parse_val(args.blue)
        rededge = parse_val(args.rededge)
        swir = parse_val(args.swir)
        l_factor = float(getattr(args, "l_factor", 0.5) or 0.5)

        stats = client.compute_index(
            index=args.index,
            nir=nir,
            red=red,
            green=green,
            blue=blue,
            rededge=rededge,
            swir=swir,
            l_factor=l_factor,
            outpath=args.outpath
        )

        width = 75
        print("+" + "-" * (width - 2) + "+")
        print(f"| OmniEarth Radiometric Index Calculation [{args.index.upper()}]".ljust(width - 1) + "|")
        print("+" + "-" * (width - 2) + "+")
        print(f"  * Mean:  {stats['mean']:.4f}")
        print(f"  * Min:   {stats['min']:.4f}")
        print(f"  * Max:   {stats['max']:.4f}")
        print(f"  * Std:   {stats['std']:.4f}")
        if args.outpath:
            print(f"  * Saved: {args.outpath}")
        print("+" + "-" * (width - 2) + "+")
    except Exception as e:
        print(f"Error computing index: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_timeseries(args, client: OmniEarth):
    """Extract chronological observations over time."""
    bbox = [float(x) for x in args.bbox] if args.bbox else None
    geojson = getattr(args, "geojson", None)
    variables = args.variables.split(",") if args.variables else None

    if not bbox and not geojson:
        print("Error: Must provide --bbox or --geojson for timeseries.", file=sys.stderr)
        sys.exit(1)

    try:
        series = client.get_time_series(
            category=args.category,
            bbox=bbox,
            geojson=geojson,
            start_date=args.start,
            end_date=args.end,
            variables=variables,
            limit=args.limit
        )

        if args.json:
            print(json.dumps(series, indent=2))
            return

        width = 75
        print("+" + "-" * (width - 2) + "+")
        print(f"| OmniEarth Time-Series [{args.category.upper()}] - {len(series)} record(s)".ljust(width - 1) + "|")
        print("+" + "-" * (width - 2) + "+")
        for i, item in enumerate(series[:15], 1):
            dt = item.get("datetime", "N/A")
            details = ", ".join(f"{k}: {v}" for k, v in item.items() if k not in ("datetime", "id", "category", "collection"))
            print(f"[{i:02d}] {dt} | {details}")
        if len(series) > 15:
            print(f"... and {len(series) - 15} more records (use --json for complete time series)")
        print("+" + "-" * (width - 2) + "+")
    except Exception as e:
        print(f"Error extracting time-series: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    description_text = f"\n{ASCII_BANNER}\n\nOmniEarth: Universal Multi-Modal Open Earth Observation & Environmental Data Engine"
    parser = argparse.ArgumentParser(
        prog="omniearth",
        description=description_text,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--version", "-v", action="version", version=f"omniearth {omniearth.__version__}")
    parser.add_argument("--env", type=str, help="Path to custom .env file for credentials")

    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Categories command
    subparsers.add_parser("categories", help="List all supported modalities, satellites, and providers")

    # Info command
    subparsers.add_parser("info", help="Display engine status, versions, and credential health")

    # Search command
    search_p = subparsers.add_parser("search", help="Search for satellite scenes, weather, or soil data")
    search_p.add_argument("--category", "-c", required=True, choices=[c.value for c in Category], help="Data category")
    search_p.add_argument("--bbox", nargs="+", type=float, help="Bounding box: min_lon min_lat max_lon max_lat")
    search_p.add_argument("--point", nargs="+", type=float, help="Point: lon lat [radius_km]")
    search_p.add_argument("--geojson", type=str, help="Path to GeoJSON file or inline GeoJSON string")
    search_p.add_argument("--start", type=str, help="Start date (YYYY-MM-DD)")
    search_p.add_argument("--end", type=str, help="End date (YYYY-MM-DD)")
    search_p.add_argument("--max-cloud", type=float, help="Maximum cloud cover percentage (0-100)")
    search_p.add_argument("--dataset", type=str, help="Specific dataset (e.g. copernicus, srtm, alos)")
    search_p.add_argument("--year", type=int, help="Year (e.g. 2020, 2021)")
    search_p.add_argument("--limit", type=int, default=5, help="Maximum number of results (default: 5)")
    search_p.add_argument("--depth", type=str, help="Soil depth slice (e.g. 0-5cm)")
    search_p.add_argument("--variables", type=str, help="Comma-separated variables (e.g. soil or weather variables)")
    search_p.add_argument("--level", type=str, choices=["sr", "toa"], default="sr", help="Processing level for optical: 'sr' (Surface Reflectance / BOA L2A) or 'toa' (Top of Atmosphere L1C)")
    search_p.add_argument("--download-all", action="store_true", help="Download all matching search results concurrently")
    search_p.add_argument("--download-top", type=int, help="Download the top N matching search results")
    search_p.add_argument("--select", type=str, help="Comma-separated 1-based indices to download (e.g. '1,3' or '1-2')")
    search_p.add_argument("-i", "--interactive", action="store_true", help="Prompt interactively to select and download scenes from search results")
    search_p.add_argument("--outdir", "-o", type=str, default="./omniearth_downloads", help="Output directory for downloads (default: ./omniearth_downloads)")
    search_p.add_argument("--threads", "-t", type=int, default=4, help="Number of parallel worker threads (default: 4)")
    search_p.add_argument("--asset", type=str, help="Specific asset key to download (e.g. visual, dem, map, etc.)")
    search_p.add_argument("--export", type=str, help="Export search results to .geojson or .csv file")
    search_p.add_argument("--provider", type=str, help="Data provider (e.g. cdse, aws, dlr_enmap)")
    search_p.add_argument("--format", type=str, help="Product format (safe, raw, cog)")
    search_p.add_argument("--bands", type=str, help="Band preset or comma-separated bands (e.g. rgb, ndvi, B04,B03,B02)")
    search_p.add_argument("--verify-checksum", action="store_true", help="Validate cryptographic hash (MD5/SHA-256) of downloaded data")
    search_p.add_argument("--composite", type=str, choices=["rgb", "false-color", "swir"], help="Automatically generate 3-band composite GeoTIFF")
    search_p.add_argument("--no-resume", action="store_true", help="Disable byte-range download resumption")
    search_p.add_argument("--no-multipart", action="store_true", help="Disable parallel chunked multipart downloading")
    search_p.add_argument("--json", action="store_true", help="Output raw JSON format")

    # Download command
    dl_p = subparsers.add_parser("download", help="Download raw satellite data, hyperspectral cubes, or environmental profiles")
    dl_p.add_argument("--category", "-c", required=True, choices=[c.value for c in Category], help="Data category")
    dl_p.add_argument("--id", type=str, help="Specific scene/product ID or comma-separated list of IDs to download")
    dl_p.add_argument("--bbox", nargs="+", type=float, help="Bounding box to find scene for: min_lon min_lat max_lon max_lat")
    dl_p.add_argument("--geojson", type=str, help="Path to GeoJSON file or inline GeoJSON string")
    dl_p.add_argument("--asset", type=str, help="Specific asset key to download (e.g. visual, dem, map, etc.)")
    dl_p.add_argument("--provider", type=str, help="Data provider (e.g. cdse, aws, dlr_enmap)")
    dl_p.add_argument("--format", type=str, help="Product format (safe, raw, node, band, cog)")
    dl_p.add_argument("--bands", type=str, help="Band preset or comma-separated bands (e.g. rgb, ndvi, 10m, 20m, vh, vv, dual)")
    dl_p.add_argument("--verify-checksum", action="store_true", help="Validate cryptographic hash (MD5/SHA-256) of downloaded data")
    dl_p.add_argument("--composite", type=str, choices=["rgb", "false-color", "swir"], help="Automatically generate 3-band composite GeoTIFF")
    dl_p.add_argument("--level", type=str, choices=["sr", "toa"], default="sr", help="Processing level for optical: 'sr' (Surface Reflectance / BOA L2A) or 'toa' (Top of Atmosphere L1C)")
    dl_p.add_argument("--outdir", "-o", type=str, default="./omniearth_downloads", help="Output directory")
    dl_p.add_argument("--start", type=str, help="Start date filter if using bbox")
    dl_p.add_argument("--end", type=str, help="End date filter if using bbox")
    dl_p.add_argument("--max-cloud", type=float, help="Max cloud cover if using bbox")
    dl_p.add_argument("--dataset", type=str, help="Specific dataset (e.g. copernicus, srtm, alos)")
    dl_p.add_argument("--year", type=int, help="Year (e.g. 2020, 2021)")
    dl_p.add_argument("--limit", type=int, default=1, help="Maximum number of scenes to download when searching by AOI (default: 1)")
    dl_p.add_argument("--all-scenes", action="store_true", help="Download all matching scenes found in AOI up to --limit")
    dl_p.add_argument("--all", action="store_true", help="Download all assets associated with the scene concurrently")
    dl_p.add_argument("--threads", "-t", type=int, default=4, help="Number of parallel worker threads (default: 4)")
    dl_p.add_argument("--no-resume", action="store_true", help="Disable byte-range download resumption")
    dl_p.add_argument("--no-multipart", action="store_true", help="Disable parallel chunked multipart downloading")

    # Compute command
    comp_p = subparsers.add_parser("compute", help="Compute remote sensing indices (NDVI, NDWI, NDRE, EVI, NBR, SAVI, MSAVI, BSI, MNDWI)")
    comp_p.add_argument("--index", required=True, choices=["ndvi", "ndwi", "ndre", "evi", "nbr", "savi", "msavi", "bsi", "mndwi"], help="Index to compute")
    comp_p.add_argument("--nir", required=True, help="NIR value or JSON array")
    comp_p.add_argument("--red", help="Red value or JSON array")
    comp_p.add_argument("--green", help="Green value or JSON array")
    comp_p.add_argument("--blue", help="Blue value or JSON array")
    comp_p.add_argument("--rededge", help="RedEdge value or JSON array")
    comp_p.add_argument("--swir", help="SWIR value or JSON array")
    comp_p.add_argument("--l-factor", type=float, default=0.5, help="Soil adjustment factor L for SAVI (default: 0.5)")
    comp_p.add_argument("--outpath", help="Path to save output (.npy or .json)")

    # Timeseries command
    ts_p = subparsers.add_parser("timeseries", help="Extract chronological observations time series")
    ts_p.add_argument("--category", "-c", required=True, choices=[c.value for c in Category], help="Data category")
    ts_p.add_argument("--bbox", nargs="+", type=float, help="Bounding box: min_lon min_lat max_lon max_lat")
    ts_p.add_argument("--geojson", type=str, help="Path to GeoJSON file or inline GeoJSON string")
    ts_p.add_argument("--start", type=str, help="Start date (YYYY-MM-DD)")
    ts_p.add_argument("--end", type=str, help="End date (YYYY-MM-DD)")
    ts_p.add_argument("--variables", type=str, help="Comma-separated variables")
    ts_p.add_argument("--limit", type=int, default=30, help="Maximum number of time-steps")
    ts_p.add_argument("--json", action="store_true", help="Output raw JSON format")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    client = OmniEarth(env_path=args.env)

    if args.command == "categories":
        cmd_categories(args, client)
    elif args.command == "info":
        cmd_info(args, client)
    elif args.command == "search":
        cmd_search(args, client)
    elif args.command == "download":
        cmd_download(args, client)
    elif args.command == "compute":
        cmd_compute(args, client)
    elif args.command == "timeseries":
        cmd_timeseries(args, client)


if __name__ == "__main__":  # pragma: no cover
    main()
