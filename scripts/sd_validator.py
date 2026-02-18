#!/usr/bin/env python3
"""
SD card structure validator for T-Deck / Meshtastic offline maps.
Checks: tile folder structure ({zoom}/{x}/{y}.png), metadata.json, PNG presence.
Note: FAT32 and 32KB cluster size cannot be verified from Python without mount info;
      document those requirements for the user.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def validate_tile_structure(root: Path) -> dict:
    """
    Validate T-Deck tile structure under root.
    Expected: root/{zoom}/{x}/{y}.png and root/metadata.json.
    Returns { "valid": bool, "errors": [], "warnings": [], "stats": {} }.
    """
    root = Path(root).resolve()
    errors = []
    warnings = []
    stats = {"zoom_levels": [], "tile_count": 0, "has_metadata": False}

    if not root.exists():
        return {"valid": False, "errors": [f"Path does not exist: {root}"], "warnings": [], "stats": stats}
    if not root.is_dir():
        return {"valid": False, "errors": [f"Not a directory: {root}"], "warnings": [], "stats": stats}

    # metadata.json
    meta = root / "metadata.json"
    if meta.is_file():
        stats["has_metadata"] = True
        try:
            with open(meta, encoding="utf-8") as f:
                data = json.load(f)
            for key in ("minzoom", "maxzoom", "bounds"):
                if key not in data:
                    errors.append(f"metadata.json missing '{key}'")
            if "bounds" in data and len(data["bounds"]) != 4:
                errors.append("metadata.json bounds must be [west, south, east, north]")
        except json.JSONDecodeError as e:
            errors.append(f"metadata.json invalid JSON: {e}")
    else:
        errors.append("Missing metadata.json")

    # Zoom directories
    zoom_dirs = sorted([d for d in root.iterdir() if d.is_dir() and d.name.isdigit()], key=lambda x: int(x.name))
    if not zoom_dirs:
        if not errors:
            errors.append("No zoom directories (expected e.g. 8, 9, 10)")
    else:
        stats["zoom_levels"] = [int(d.name) for d in zoom_dirs]
        for zdir in zoom_dirs:
            x_dirs = [d for d in zdir.iterdir() if d.is_dir() and d.name.isdigit()]
            for xdir in x_dirs:
                for f in xdir.iterdir():
                    if f.suffix.lower() == ".png" and f.name[:-4].isdigit():
                        stats["tile_count"] += 1
                    elif f.is_file():
                        warnings.append(f"Non-PNG or invalid name in tile dir: {f.relative_to(root)}")
            if not x_dirs and not any(zdir.iterdir()):
                warnings.append(f"Empty zoom directory: {zdir.name}")

    # Sample check: at least one tile
    if stats["tile_count"] == 0 and zoom_dirs:
        errors.append("No PNG tiles found under zoom/x/y.png structure")

    valid = len(errors) == 0
    return {"valid": valid, "errors": errors, "warnings": warnings, "stats": stats}


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate T-Deck map tile folder structure")
    parser.add_argument("path", nargs="?", default="tiles", help="Path to tiles root")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args()
    result = validate_tile_structure(Path(args.path))
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("Valid" if result["valid"] else "Invalid")
        for e in result.get("errors", []):
            print(f"  Error: {e}")
        for w in result.get("warnings", []):
            print(f"  Warning: {w}")
        if result.get("stats"):
            s = result["stats"]
            print(f"  Zoom levels: {s.get('zoom_levels', [])}")
            print(f"  Tile count: {s.get('tile_count', 0)}")
            print(f"  metadata.json: {s.get('has_metadata', False)}")
    sys.exit(0 if result["valid"] else 1)


if __name__ == "__main__":
    main()
