#!/usr/bin/env python3
"""
Map tile downloader wizard: list regions, estimate tiles/size, validate SD, generate command or run download.
Uses regions/regions.json and scripts/map_tiles/meshtastic_tiles.py (tdeck-maps compatible).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Add repo root for imports
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.map_tiles.meshtastic_tiles import (
    count_tiles,
    get_region_bounds_from_json,
    load_regions_json,
    MeshtasticTileGenerator,
)

REGIONS_PATH = REPO_ROOT / "regions" / "regions.json"
AVG_TILE_KB = 15
SD_CAPACITY_GB = (16, 32, 64, 128)


def get_regions_grouped(path: Path | None = None) -> dict:
    """Load regions and group by category (continent, country, state)."""
    data = load_regions_json(path or REGIONS_PATH)
    regions = data.get("regions", [])
    grouped = {"continent": [], "country": [], "state": []}
    for r in regions:
        cat = (r.get("category") or "country").lower()
        if cat not in grouped:
            grouped[cat] = []
        grouped[cat].append({"slug": r.get("slug"), "name": r.get("name"), "country": r.get("country")})
    return grouped


def estimate_mb(tile_count: int, avg_kb: float = AVG_TILE_KB) -> float:
    return tile_count * avg_kb / 1024.0


def wizard_estimate(region_slug: str, min_zoom: int, max_zoom: int, path: Path | None = None) -> dict | None:
    """Return tile count and estimated size for a region and zoom range."""
    bounds = get_region_bounds_from_json(region_slug, path or REGIONS_PATH)
    if not bounds:
        return None
    n = count_tiles(
        bounds["north"], bounds["south"], bounds["east"], bounds["west"],
        min_zoom, max_zoom,
    )
    return {
        "region_slug": region_slug,
        "min_zoom": min_zoom,
        "max_zoom": max_zoom,
        "tile_count": n,
        "estimated_mb": round(estimate_mb(n), 1),
        "estimated_gb": round(estimate_mb(n) / 1024.0, 2),
        "sd_fits": {f"{g}GB": (estimate_mb(n) / 1024.0) <= g for g in SD_CAPACITY_GB},
    }


def wizard_list_regions(path: Path | None = None) -> dict:
    """Return full region list and grouped for UI."""
    data = load_regions_json(path or REGIONS_PATH)
    grouped = get_regions_grouped(path or REGIONS_PATH)
    return {
        "regions": data.get("regions", []),
        "grouped": grouped,
        "map_sources": data.get("map_sources", []),
    }


def validate_output_structure(output_dir: Path) -> dict:
    """Check that output_dir has T-Deck tile structure: {zoom}/{x}/{y}.png and metadata.json."""
    output_dir = Path(output_dir)
    errors = []
    if not output_dir.is_dir():
        return {"valid": False, "errors": [f"Not a directory: {output_dir}"]}
    meta = output_dir / "metadata.json"
    if not meta.is_file():
        errors.append("Missing metadata.json")
    else:
        try:
            with open(meta, encoding="utf-8") as f:
                j = json.load(f)
            if "minzoom" not in j or "maxzoom" not in j or "bounds" not in j:
                errors.append("metadata.json missing minzoom/maxzoom/bounds")
        except json.JSONDecodeError:
            errors.append("metadata.json invalid JSON")
    zoom_dirs = [d for d in output_dir.iterdir() if d.is_dir() and d.name.isdigit()]
    if not zoom_dirs and not errors:
        errors.append("No zoom directories (e.g. 8, 9, 10)")
    for zdir in zoom_dirs[:3]:  # sample first 3 zoom levels
        x_dirs = [d for d in zdir.iterdir() if d.is_dir() and d.name.isdigit()]
        for xdir in x_dirs[:2]:
            pngs = list(xdir.glob("*.png"))
            if not pngs:
                errors.append(f"Empty tile dir: {zdir.name}/{xdir.name}")
            break
    return {"valid": len(errors) == 0, "errors": errors}


def main() -> None:
    parser = argparse.ArgumentParser(description="Map tile downloader wizard (tdeck-maps compatible)")
    sub = parser.add_subparsers(dest="cmd", help="Command")
    # list: all regions
    list_p = sub.add_parser("list", help="List all regions (continents, countries, states)")
    list_p.add_argument("--json", action="store_true", help="Output JSON")
    # estimate: tile count + size for region + zoom
    est_p = sub.add_parser("estimate", help="Estimate tile count and size for region + zoom range")
    est_p.add_argument("region", help="Region slug (e.g. california, usa)")
    est_p.add_argument("--min-zoom", type=int, default=8)
    est_p.add_argument("--max-zoom", type=int, default=12)
    est_p.add_argument("--json", action="store_true")
    # validate: check output dir structure
    val_p = sub.add_parser("validate", help="Validate tile folder structure (T-Deck format)")
    val_p.add_argument("path", nargs="?", default="tiles", help="Path to tiles folder")
    val_p.add_argument("--json", action="store_true")
    # run: run the tile generator (delegate to meshtastic_tiles.py)
    run_p = sub.add_parser("run", help="Run tile download (same as meshtastic_tiles.py)")
    run_p.add_argument("--region", type=str)
    run_p.add_argument("--city", type=str)
    run_p.add_argument("--cities", type=str)
    run_p.add_argument("--coords", action="store_true")
    run_p.add_argument("--buffer", type=int, default=20)
    run_p.add_argument("--north", type=float)
    run_p.add_argument("--south", type=float)
    run_p.add_argument("--east", type=float)
    run_p.add_argument("--west", type=float)
    run_p.add_argument("--min-zoom", type=int, default=8)
    run_p.add_argument("--max-zoom", type=int, default=12)
    run_p.add_argument("--source", default="osm", choices=["osm", "satellite", "terrain", "cycle", "carto", "carto_dark", "stadia", "stadia_dark"])
    run_p.add_argument("--output-dir", default="tiles")
    run_p.add_argument("--delay", type=float, default=0.2)
    run_p.add_argument("--max-workers", type=int, default=3)
    run_p.add_argument("--format", default="meshtastic", choices=["meshtastic", "meshcore", "meshos"],
                       help="T-Deck firmware: meshtastic, meshcore, or meshos (B&W)")
    args = parser.parse_args()

    if args.cmd == "list":
        out = wizard_list_regions()
        if getattr(args, "json", False):
            print(json.dumps(out, indent=2))
        else:
            print("Regions (continents, countries, states):")
            for cat, items in out["grouped"].items():
                if items:
                    print(f"\n  {cat.upper()}")
                    for r in items:
                        print(f"    {r['slug']}: {r['name']}")
        return

    if args.cmd == "estimate":
        res = wizard_estimate(args.region, args.min_zoom, args.max_zoom)
        if not res:
            print(f"Unknown region: {args.region}", file=sys.stderr)
            sys.exit(1)
        if getattr(args, "json", False):
            print(json.dumps(res, indent=2))
        else:
            print(f"Region: {res['region_slug']}")
            print(f"Zoom: {res['min_zoom']}-{res['max_zoom']}")
            print(f"Tile count: {res['tile_count']:,}")
            print(f"Estimated size: {res['estimated_mb']} MB ({res['estimated_gb']} GB)")
            print("Fits on SD:", ", ".join(f"{k}={v}" for k, v in res["sd_fits"].items()))
        return

    if args.cmd == "validate":
        res = validate_output_structure(Path(getattr(args, "path", "tiles")))
        if getattr(args, "json", False):
            print(json.dumps(res, indent=2))
        else:
            print("Valid" if res["valid"] else "Invalid")
            for e in res.get("errors", []):
                print(f"  - {e}")
        sys.exit(0 if res["valid"] else 1)

    if args.cmd == "run":
        # Delegate to meshtastic_tiles main
        sys.argv = ["meshtastic_tiles.py"]
        if args.region:
            sys.argv += ["--region", args.region]
        elif args.city:
            sys.argv += ["--city", args.city]
        elif args.cities:
            sys.argv += ["--cities", args.cities]
        elif args.coords:
            sys.argv += ["--coords", "--north", str(args.north), "--south", str(args.south),
                        "--east", str(args.east), "--west", str(args.west)]
        else:
            print("Specify --region, --city, --cities, or --coords with bounds", file=sys.stderr)
            sys.exit(1)
        sys.argv += ["--min-zoom", str(args.min_zoom), "--max-zoom", str(args.max_zoom),
                     "--source", args.source, "--output-dir", args.output_dir,
                     "--delay", str(args.delay), "--max-workers", str(args.max_workers),
                     "--format", getattr(args, "format", "meshtastic")]
        if args.buffer and (args.city or args.cities):
            sys.argv += ["--buffer", str(args.buffer)]
        from scripts.map_tiles import meshtastic_tiles
        meshtastic_tiles.main()
        return

    parser.print_help()
    sys.exit(0)


if __name__ == "__main__":
    main()
