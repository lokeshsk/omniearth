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
    print("=" * 65)
    print(" OmniEarth Supported Modalities & Data Providers")
    print("=" * 65)
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
        "weather": {
            "name": "Weather & Climate Profiles",
            "sources": ["Open-Meteo Zero-Config Global Model", "ERA5 Reanalysis"],
            "backend": "Open-Meteo REST API",
            "auth": "Zero-Config (No API key needed)"
        },
        "soil": {
            "name": "Soil Composition & 3D Profiles",
            "sources": ["ISRIC SoilGrids v2.0 (250m global)"],
            "backend": "ISRIC REST API",
            "auth": "Zero-Config (Public)"
        }
    }

    for cat_id, info in categories.items():
        print(f"\n📂 [{cat_id.upper()}] - {info['name']}")
        if "satellites" in info:
            print(f"   Sensors:  {', '.join(info['satellites'])}")
        if "sources" in info:
            print(f"   Sources:  {', '.join(info['sources'])}")
        print(f"   Backend:  {info['backend']}")
        print(f"   Auth:     {info['auth']}")
    print("\n" + "=" * 65)


def cmd_info(args, client: OmniEarth):
    """Display system status, versions, and credential health."""
    print("=" * 65)
    print(f" OmniEarth Engine v{omniearth.__version__}")
    print(f" Author: Lokesh Kumar (lokesh.skshukla@gmail.com)")
    print(f" Homepage: https://lokeshsk.github.io/omniearth/")
    print("=" * 65)

    print("\n[Credential & Environment Status]")
    dlr_u = config.get("DLR_USERNAME")
    dlr_p = config.get("DLR_PASSWORD")
    dlr_status = "✅ Configured" if (dlr_u and dlr_p) else "⚪ Optional (Needed for EnMAP raw download)"

    prisma_u = config.get("PRISMA_USERNAME")
    prisma_status = "✅ Configured" if prisma_u else "⚪ Optional (Needed for PRISMA download)"

    ed_u = config.get("EARTHDATA_USERNAME")
    ed_status = "✅ Configured" if ed_u else "⚪ Optional (Needed for NASA EMIT direct cubes)"

    print(f"  • DLR Geoservice (EnMAP):     {dlr_status}")
    print(f"  • ASI PRISMA Portal:          {prisma_status}")
    print(f"  • NASA Earthdata (EMIT):       {ed_status}")
    print(f"  • Open-Meteo (Weather):        ✅ Native Zero-Config")
    print(f"  • ISRIC SoilGrids (Soil):      ✅ Native Zero-Config")
    print(f"  • AWS Earth Search (S1, S2):   ✅ Native Zero-Config")
    print("=" * 65)


def cmd_search(args, client: OmniEarth):
    """Search for data in a specific category."""
    bbox = None
    point = None

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
    else:
        print("Error: Must provide either --bbox or --point.", file=sys.stderr)
        sys.exit(1)

    variables = args.variables.split(",") if args.variables else None

    try:
        results = client.search(
            category=args.category,
            bbox=bbox,
            point=point,
            start_date=args.start,
            end_date=args.end,
            max_cloud_cover=args.max_cloud,
            variables=variables,
            depth=args.depth,
            limit=args.limit
        )
    except Exception as e:
        print(f"Error during search: {e}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        data = [r.to_dict() for r in results]
        print(json.dumps(data, indent=2))
        return

    print("=" * 75)
    print(f" OmniEarth Search Results [{args.category.upper()}] — {len(results)} item(s) found")
    print("=" * 75)

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
    print("\n" + "=" * 75)
    print("Tip: Download any scene using: omniearth download --category <cat> --id <ID>")


def cmd_download(args, client: OmniEarth):
    """Download an asset from search results or scene ID."""
    bbox = None
    if args.bbox:
        bbox = [float(x) for x in args.bbox]

    target_result = None

    if args.id:
        # Search specifically for this ID
        print(f"Searching for item '{args.id}' in category '{args.category}'...")
        # For point search or broader search if bbox is provided
        search_bbox = bbox or [-180, -90, 180, 90]
        results = client.search(category=args.category, bbox=search_bbox, limit=50)
        for r in results:
            if r.id == args.id:
                target_result = r
                break
        
        if not target_result:
            # Fallback direct synthetic result with default assets if possible
            print(f"Notice: Item not found in recent catalog page; attempting direct provider resolution...")
            target_result = omniearth.models.SearchResult(
                id=args.id,
                collection=args.category,
                category=Category(args.category),
                provider=args.category,
                datetime="2026-01-01T00:00:00Z",
                bbox=search_bbox,
                assets={}
            )
    elif bbox:
        # Fetch latest matching scene in this bbox
        print(f"Searching for matching scenes in bbox {bbox}...")
        results = client.search(
            category=args.category,
            bbox=bbox,
            start_date=args.start,
            end_date=args.end,
            max_cloud_cover=args.max_cloud,
            limit=1
        )
        if not results:
            print("No matching scenes found to download.", file=sys.stderr)
            sys.exit(1)
        target_result = results[0]
        print(f"Selected latest scene: {target_result.id} ({target_result.datetime})")
    else:
        print("Error: Must specify either --id or --bbox to download.", file=sys.stderr)
        sys.exit(1)

    outdir = args.outdir or "./omniearth_downloads"
    try:
        path = client.download(target_result, asset_key=args.asset, outdir=outdir)
        print(f"\n Successfully downloaded: {path}")
    except Exception as e:
        print(f"\n❌ Download failed: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        prog="omniearth",
        description="OmniEarth: Universal Multi-Modal Open Earth Observation & Environmental Data Engine"
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
    search_p.add_argument("--start", type=str, help="Start date (YYYY-MM-DD)")
    search_p.add_argument("--end", type=str, help="End date (YYYY-MM-DD)")
    search_p.add_argument("--max-cloud", type=float, help="Maximum cloud cover percentage (0-100)")
    search_p.add_argument("--limit", type=int, default=5, help="Maximum number of results (default: 5)")
    search_p.add_argument("--depth", type=str, help="Soil depth slice (e.g. 0-5cm)")
    search_p.add_argument("--variables", type=str, help="Comma-separated variables (e.g. soil or weather variables)")
    search_p.add_argument("--json", action="store_true", help="Output raw JSON format")

    # Download command
    dl_p = subparsers.add_parser("download", help="Download raw satellite data, hyperspectral cubes, or environmental profiles")
    dl_p.add_argument("--category", "-c", required=True, choices=[c.value for c in Category], help="Data category")
    dl_p.add_argument("--id", type=str, help="Specific scene/product ID to download")
    dl_p.add_argument("--bbox", nargs="+", type=float, help="Bounding box to find scene for: min_lon min_lat max_lon max_lat")
    dl_p.add_argument("--asset", type=str, help="Specific asset key to download (e.g. visual, SPECTRAL_IMAGE_COG, etc.)")
    dl_p.add_argument("--outdir", "-o", type=str, default="./omniearth_downloads", help="Output directory")
    dl_p.add_argument("--start", type=str, help="Start date filter if using bbox")
    dl_p.add_argument("--end", type=str, help="End date filter if using bbox")
    dl_p.add_argument("--max-cloud", type=float, help="Max cloud cover if using bbox")

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


if __name__ == "__main__":
    main()
