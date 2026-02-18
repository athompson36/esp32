#!/usr/bin/env python3
"""
Deep diagnostic for map tile download and build.
Run from repo root: python scripts/map_tiles/diagnose_tiles.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Repo root: parent of scripts/
def _repo_root():
    p = Path(__file__).resolve().parent
    while p.name and p.name != "scripts":
        p = p.parent
    return p.parent if p.name == "scripts" else Path.cwd()

def run():
    root = _repo_root()
    errors = []
    warnings = []
    info = []

    # 1. Python
    info.append(f"Python: {sys.version.split()[0]} ({sys.executable})")
    if sys.version_info < (3, 9):
        warnings.append("Python 3.9+ recommended for type hints and pathlib.")

    # 2. CWD vs repo root
    cwd = Path.cwd()
    if cwd != root:
        warnings.append(f"Current working directory is {cwd}; repo root is {root}. Run from repo root for regions.json.")
    else:
        info.append(f"Working directory: repo root {root}")

    # 3. requests
    try:
        import requests
        info.append(f"requests: {getattr(requests, '__version__', 'unknown')}")
    except ImportError:
        errors.append("requests not installed. Install with: pip install requests")
        requests = None

    # 4. Pillow (optional)
    try:
        from PIL import Image
        info.append("Pillow: installed (optional, for --sample-only and B&W conversion)")
    except ImportError:
        warnings.append("Pillow not installed. Optional for --sample-only and MeshOS B&W conversion. pip install pillow")

    # 5. regions.json
    regions_path = root / "regions" / "regions.json"
    if not regions_path.is_file():
        errors.append(f"regions/regions.json not found at {regions_path}")
    else:
        try:
            with open(regions_path, encoding="utf-8") as f:
                data = json.load(f)
            regions = data.get("regions", [])
            slugs = [r.get("slug") for r in regions if r.get("slug")]
            info.append(f"regions/regions.json: {len(slugs)} regions (e.g. {slugs[:5]})")
            if not slugs:
                warnings.append("regions.json has no regions with slug.")
        except Exception as e:
            errors.append(f"Failed to load regions.json: {e}")

    # 6. OSM tile server reachability and policy
    if requests:
        url = "https://tile.openstreetmap.org/10/163/395.png"
        # Use same User-Agent as tile generator (OSM policy requires app identity + contact)
        headers = {"User-Agent": "MeshtasticTileGenerator/1.0 (+https://github.com/JustDr00py/tdeck-maps; T-Deck offline maps)"}
        try:
            r = requests.get(url, headers=headers, timeout=15)
            blocked = r.headers.get("x-blocked", "").lower()
            if "access denied" in blocked or "blocked" in blocked:
                errors.append(
                    "OSM tile server returned 'x-blocked: Access denied'. "
                    "tile.openstreetmap.org does not allow bulk/offline downloading (see https://operations.osmfoundation.org/policies/tiles/). "
                    "Use a self-hosted tile server or a provider that allows offline use (see scripts/map_tiles/README.md)."
                )
            elif r.status_code != 200:
                errors.append(f"OSM tile test request failed: HTTP {r.status_code}")
            else:
                size = len(r.content)
                if size < 100:
                    warnings.append(f"OSM tile response very small ({size} bytes); may be an error page.")
                else:
                    info.append(f"OSM tile test: HTTP 200, {size} bytes (single tile reachable)")
        except requests.exceptions.SSLError as e:
            errors.append(f"SSL error reaching OSM: {e}")
        except requests.exceptions.ConnectionError as e:
            errors.append(f"Cannot reach tile server (network/proxy/firewall): {e}")
        except requests.exceptions.Timeout:
            errors.append("Timeout reaching tile server.")
        except Exception as e:
            errors.append(f"Error testing OSM tile: {e}")

    # 7. One-tile download + output structure (if no critical errors yet)
    if requests and not errors and regions_path.is_file():
        try:
            sys.path.insert(0, str(root))
            from scripts.map_tiles.meshtastic_tiles import (
                MeshtasticTileGenerator,
                get_region_bounds_from_json,
            )
            bounds = get_region_bounds_from_json("california", regions_path)
            if bounds:
                gen = MeshtasticTileGenerator(output_dir=root / "tiles_diagnostic_out", delay=0)
                # Single zoom, tiny area → 1 tile
                n, s, e, w = bounds["north"], bounds["south"], bounds["east"], bounds["west"]
                mid_lat = (n + s) / 2
                mid_lon = (e + w) / 2
                delta = 0.01
                gen.generate_tiles(
                    north=mid_lat + delta, south=mid_lat - delta,
                    east=mid_lon + delta, west=mid_lon - delta,
                    min_zoom=10, max_zoom=10, source="osm", max_workers=1,
                )
                out = gen.output_dir
                meta = out / "metadata.json"
                if meta.exists():
                    info.append(f"One-tile build OK: {out} (metadata.json present)")
                else:
                    warnings.append("One-tile build ran but metadata.json missing.")
                # Clean up
                import shutil
                if out.exists():
                    shutil.rmtree(out, ignore_errors=True)
            else:
                warnings.append("Could not get california bounds for one-tile test.")
        except Exception as e:
            errors.append(f"One-tile build failed: {e}")

    # Report
    print("=== Map tile diagnostic ===\n")
    for line in info:
        print(f"  [OK] {line}")
    for line in warnings:
        print(f"  [WARN] {line}")
    for line in errors:
        print(f"  [FAIL] {line}")

    print("\n--- OSM policy note ---")
    print("  tile.openstreetmap.org does not allow bulk downloading or offline use.")
    print("  For T-Deck offline maps, use self-hosted tiles or a provider that allows it.")
    print("  See: https://operations.osmfoundation.org/policies/tiles/")
    print("  See: scripts/map_tiles/README.md for alternatives.\n")

    if errors:
        print("Result: FAILED (fix errors above).")
        return 1
    if warnings:
        print("Result: OK with warnings.")
        return 0
    print("Result: All checks passed.")
    return 0

if __name__ == "__main__":
    sys.exit(run())
