#!/usr/bin/env python3
"""
Meshtastic Map Tile Generator for T-Deck (tdeck-maps compatible).
Folder structure: {output_dir}/{zoom}/{x}/{y}.png + metadata.json.
Compatible with https://github.com/JustDr00py/tdeck-maps

Note: tile.openstreetmap.org does not allow bulk/offline downloading (see
https://operations.osmfoundation.org/policies/tiles/). For offline T-Deck maps
use a self-hosted tile server or a provider that permits it; see README.md.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FuturesTimeoutError

# Per-tile result timeout (seconds) so one stuck download does not hang the whole run
TILE_RESULT_TIMEOUT = 60

# User-Agent for tile requests: OSM policy requires a clear app identity and contact (see operations.osmfoundation.org/policies/tiles/)
TILE_USER_AGENT = "MeshtasticTileGenerator/1.0 (+https://github.com/JustDr00py/tdeck-maps; T-Deck offline maps)"

def _log(msg: str, file=None) -> None:
    """Print and flush so progress is visible when stdout is buffered (e.g. piped/non-TTY)."""
    print(msg, file=file or sys.stdout, flush=True)

try:
    import requests
except ImportError:
    requests = None
try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    Image = ImageDraw = ImageFont = None


def _repo_root():
    """Repo root: parent of scripts/."""
    p = Path(__file__).resolve().parent
    while p.name and p.name != "scripts":
        p = p.parent
    return p.parent if p.name == "scripts" else Path.cwd()


def load_regions_json(path: Path | None = None) -> dict:
    """Load regions from regions/regions.json; return dict with 'regions' list."""
    if path is None:
        path = _repo_root() / "regions" / "regions.json"
    if not path.is_file():
        return {"regions": []}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def get_region_bounds_from_json(region_slug: str, path: Path | None = None) -> dict | None:
    """Return bounds dict (north, south, east, west) for a region slug from regions.json."""
    data = load_regions_json(path)
    for r in data.get("regions", []):
        if (r.get("slug") or "").lower() == region_slug.lower():
            return r.get("bounds")
    return None


class CityLookup:
    """Lookup city coordinates via OpenStreetMap Nominatim."""

    def __init__(self):
        self.session = requests.Session() if requests else None
        if self.session:
            self.session.headers.update({"User-Agent": TILE_USER_AGENT})

    def get_coordinates(self, city: str, state: str | None = None, country: str | None = None) -> dict | None:
        if not self.session:
            return None
        base_url = "https://nominatim.openstreetmap.org/search"
        query = city
        if state:
            query += f", {state}"
        if country:
            query += f", {country}"
        params = {"q": query, "format": "json", "limit": 1, "addressdetails": 1}
        try:
            r = self.session.get(base_url, params=params, timeout=10)
            r.raise_for_status()
            data = r.json()
            if not data:
                return None
            result = data[0]
            return {
                "name": result.get("display_name", "Unknown"),
                "lat": float(result["lat"]),
                "lon": float(result["lon"]),
                "type": result.get("type", "unknown"),
            }
        except Exception as e:
            print(f"Error looking up coordinates for {query}: {e}", file=sys.stderr)
            return None

    def get_bounding_box_for_cities(self, cities: list[str], buffer_km: float = 10) -> dict | None:
        all_coords = []
        for city_str in cities:
            city_str = city_str.strip()
            result = self.get_coordinates(city_str)
            if result:
                all_coords.append(result)
                print(f"  ✓ {city_str}: {result['lat']:.4f}, {result['lon']:.4f}")
            else:
                print(f"  ✗ {city_str}: Not found")
        if not all_coords:
            return None
        lats = [c["lat"] for c in all_coords]
        lons = [c["lon"] for c in all_coords]
        buffer_deg = buffer_km / 111.0
        return {
            "north": max(lats) + buffer_deg,
            "south": min(lats) - buffer_deg,
            "east": max(lons) + buffer_deg,
            "west": min(lons) - buffer_deg,
            "cities": all_coords,
        }


class MeshtasticTileGenerator:
    """Generate tiles in T-Deck/Meshtastic format: {output_dir}/{zoom}/{x}/{y}.png + metadata.json."""

    TILE_SOURCES = {
        "osm": "https://tile.openstreetmap.org/{zoom}/{x}/{y}.png",
        "satellite": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{zoom}/{y}/{x}",
        "terrain": "https://tile.opentopomap.org/{zoom}/{x}/{y}.png",
        "cycle": "https://tile.thunderforest.com/cycle/{zoom}/{x}/{y}.png",
        # CARTO Light (Positron) — OSM-based, light style; standard XYZ. Attribution: Map tiles by CARTO, CC BY 3.0. Data © OSM.
        "carto": "https://a.basemaps.cartocdn.com/light_all/{zoom}/{x}/{y}.png",
        # CARTO Dark Matter — dark background, easier on the eyes; same XYZ. Attribution: Map tiles by CARTO, CC BY 3.0. Data © OSM.
        "carto_dark": "https://a.basemaps.cartocdn.com/dark_all/{zoom}/{x}/{y}.png",
        # Stadia Alidade Smooth — free tier for non-commercial; no registration for local dev.
        "stadia": "https://tiles.stadiamaps.com/tiles/alidade_smooth/{zoom}/{x}/{y}.png",
        # Stadia Alidade Smooth Dark — dark theme, good contrast for outdoor/T-Deck.
        "stadia_dark": "https://tiles.stadiamaps.com/tiles/alidade_smooth_dark/{zoom}/{x}/{y}.png",
    }

    def __init__(self, output_dir: str | Path = "tiles", tile_size: int = 256, delay: float = 0.1):
        self.output_dir = Path(output_dir)
        self.tile_size = tile_size
        self.delay = delay
        self.session = requests.Session() if requests else None
        if self.session:
            self.session.headers.update({"User-Agent": TILE_USER_AGENT})
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def deg2num(lat_deg: float, lon_deg: float, zoom: int) -> tuple[int, int]:
        lat_rad = math.radians(lat_deg)
        n = 2.0 ** zoom
        x = int((lon_deg + 180.0) / 360.0 * n)
        y = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
        return (x, y)

    @staticmethod
    def num2deg(x: int, y: int, zoom: int) -> tuple[float, float]:
        n = 2.0 ** zoom
        lon_deg = x / n * 360.0 - 180.0
        lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * y / n)))
        return (math.degrees(lat_rad), lon_deg)

    def get_tile_url(self, x: int, y: int, zoom: int, source: str = "osm") -> str:
        tpl = self.TILE_SOURCES.get(source, self.TILE_SOURCES["osm"])
        return tpl.format(zoom=zoom, x=x, y=y)

    def download_tile(self, x: int, y: int, zoom: int, source: str = "osm") -> tuple[Path | None, bool]:
        url = self.get_tile_url(x, y, zoom, source)
        tile_dir = self.output_dir / str(zoom) / str(x)
        tile_dir.mkdir(parents=True, exist_ok=True)
        tile_path = tile_dir / f"{y}.png"
        if tile_path.exists():
            return tile_path, True
        if not self.session:
            return None, False
        try:
            r = self.session.get(url, timeout=10)
            r.raise_for_status()
            tile_path.write_bytes(r.content)
            time.sleep(self.delay)
            return tile_path, True
        except Exception as e:
            _log(f"Error downloading tile {x},{y},{zoom}: {e}", file=sys.stderr)
            return None, False

    def generate_tiles(
        self,
        north: float,
        south: float,
        east: float,
        west: float,
        min_zoom: int = 8,
        max_zoom: int = 16,
        source: str = "osm",
        max_workers: int = 4,
    ) -> None:
        if north <= south or east <= west:
            _log("Error: Invalid bounds (north>south, east>west)", file=sys.stderr)
            return
        total_tiles = 0
        downloaded = 0
        for zoom in range(min_zoom, max_zoom + 1):
            x_min, y_max = self.deg2num(south, west, zoom)
            x_max, y_min = self.deg2num(north, east, zoom)
            if x_min > x_max:
                x_min, x_max = x_max, x_min
            if y_min > y_max:
                y_min, y_max = y_max, y_min
            n = (x_max - x_min + 1) * (y_max - y_min + 1)
            total_tiles += n
            _log(f"Zoom {zoom}: {n} tiles (x:{x_min}-{x_max}, y:{y_min}-{y_max})")
        _log(f"Total tiles: {total_tiles}")
        if total_tiles == 0:
            return
        firmware = getattr(self, "_firmware", "meshtastic")
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for zoom in range(min_zoom, max_zoom + 1):
                x_min, y_max = self.deg2num(south, west, zoom)
                x_max, y_min = self.deg2num(north, east, zoom)
                if x_min > x_max:
                    x_min, x_max = x_max, x_min
                if y_min > y_max:
                    y_min, y_max = y_max, y_min
                for x in range(x_min, x_max + 1):
                    for y in range(y_min, y_max + 1):
                        futures.append(executor.submit(self.download_tile, x, y, zoom, source))
            for f in as_completed(futures):
                try:
                    _, ok = f.result(timeout=TILE_RESULT_TIMEOUT)
                    if ok:
                        downloaded += 1
                    if downloaded % 100 == 0 and downloaded:
                        _log(f"Downloaded {downloaded}/{total_tiles} tiles")
                except FuturesTimeoutError:
                    _log(f"Timeout waiting for tile (skipping); downloaded {downloaded}/{total_tiles} so far.", file=sys.stderr)
                except Exception as e:
                    _log(f"Tile future error: {e}", file=sys.stderr)
        _log(f"Completed: {downloaded}/{total_tiles} tiles")
        self.generate_metadata(north, south, east, west, min_zoom, max_zoom, source, firmware=firmware)
        if firmware == "meshos":
            self.convert_tiles_to_bw()

    def convert_tiles_to_bw(self, threshold: int = 128) -> None:
        """Convert all PNG tiles in output_dir to simple black-and-white (MeshOS-style). In-place."""
        if not Image:
            _log("PIL/Pillow required for B&W conversion (pip install pillow)", file=sys.stderr)
            return
        count = 0
        for zdir in sorted(
            (d for d in self.output_dir.iterdir() if d.is_dir() and d.name.isdigit()),
            key=lambda x: int(x.name),
        ):
            if not zdir.is_dir() or not zdir.name.isdigit():
                continue
            for xdir in zdir.iterdir():
                if not xdir.is_dir() or not xdir.name.isdigit():
                    continue
                for png in xdir.glob("*.png"):
                    if not png.name[:-4].isdigit():
                        continue
                    try:
                        img = Image.open(png).convert("RGB")
                        gray = img.convert("L")
                        bw = gray.point(lambda p: 255 if p >= threshold else 0, mode="1").convert("RGB")
                        bw.save(png, "PNG")
                        count += 1
                    except Exception as e:
                        _log(f"Warning: could not convert {png}: {e}", file=sys.stderr)
        if count:
            _log(f"Converted {count} tiles to B&W (MeshOS format)")

    def generate_metadata(
        self,
        north: float,
        south: float,
        east: float,
        west: float,
        min_zoom: int,
        max_zoom: int,
        source: str,
        firmware: str = "meshtastic",
    ) -> None:
        desc = "Map tiles for Meshtastic T-Deck"
        if firmware == "meshos":
            desc = "Map tiles for T-Deck (MeshOS simple black and white)"
        elif firmware == "meshcore":
            desc = "Map tiles for MeshCore T-Deck"
        # Meshtastic Device-UI (MUI) expects maps/<style>/z/x/y.png and metadata.json.
        # Include both lowercase and camelCase zoom keys for parser compatibility.
        metadata = {
            "name": f"Generated tiles ({source})",
            "description": desc,
            "bounds": [west, south, east, north],
            "minzoom": min_zoom,
            "maxzoom": max_zoom,
            "minZoom": min_zoom,
            "maxZoom": max_zoom,
            "format": "png",
            "type": "baselayer",
            "source": source,
            "tileSize": self.tile_size,
            "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        path = self.output_dir / "metadata.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
        _log(f"Metadata saved to {path}")

    def create_sample_tile(self, text: str = "Sample Tile") -> None:
        if not Image:
            print("PIL/Pillow required for sample tile", file=sys.stderr)
            return
        img = Image.new("RGB", (self.tile_size, self.tile_size), color="lightblue")
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except Exception:
            font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        draw.text(((self.tile_size - tw) // 2, (self.tile_size - th) // 2), text, fill="black", font=font)
        sample_dir = self.output_dir / "sample"
        sample_dir.mkdir(exist_ok=True)
        img.save(sample_dir / "sample.png")
        print(f"Sample tile saved to {sample_dir / 'sample.png'}")


def count_tiles(north: float, south: float, east: float, west: float, min_zoom: int, max_zoom: int) -> int:
    total = 0
    for zoom in range(min_zoom, max_zoom + 1):
        x_min, y_max = MeshtasticTileGenerator.deg2num(south, west, zoom)
        x_max, y_min = MeshtasticTileGenerator.deg2num(north, east, zoom)
        if x_min > x_max:
            x_min, x_max = x_max, x_min
        if y_min > y_max:
            y_min, y_max = y_max, y_min
        total += (x_max - x_min + 1) * (y_max - y_min + 1)
    return total


def main() -> None:
    root = _repo_root()
    regions_path = root / "regions" / "regions.json"
    data = load_regions_json(regions_path)
    region_slugs = [r["slug"] for r in data.get("regions", []) if r.get("slug")]

    parser = argparse.ArgumentParser(description="Generate map tiles for Meshtastic T-Deck (tdeck-maps compatible)")
    method = parser.add_mutually_exclusive_group(required=False)
    method.add_argument("--region", type=str, choices=region_slugs, help="Predefined region from regions/regions.json")
    method.add_argument("--city", type=str, help='City name (e.g. "San Francisco" or "Portland, Oregon")')
    method.add_argument("--cities", type=str, help='Multiple cities separated by semicolons (e.g. "SF; Oakland; San Jose")')
    method.add_argument("--coords", action="store_true", help="Use --north/--south/--east/--west")
    parser.add_argument("--buffer", type=int, default=20, help="Buffer around city/cities in km (default 20)")
    parser.add_argument("--north", type=float)
    parser.add_argument("--south", type=float)
    parser.add_argument("--east", type=float)
    parser.add_argument("--west", type=float)
    parser.add_argument("--min-zoom", type=int, default=8)
    parser.add_argument("--max-zoom", type=int, default=12)
    parser.add_argument("--source", default="osm", choices=list(MeshtasticTileGenerator.TILE_SOURCES))
    parser.add_argument("--output-dir", default="tiles")
    parser.add_argument("--delay", type=float, default=0.2)
    parser.add_argument("--max-workers", type=int, default=3)
    parser.add_argument("--sample-only", action="store_true")
    parser.add_argument(
        "--format",
        choices=["meshtastic", "meshcore", "meshos"],
        default="meshtastic",
        help="T-Deck firmware format: meshtastic (default), meshcore (same layout), meshos (simple B&W)",
    )
    parser.add_argument(
        "--convert-bw-only",
        metavar="DIR",
        help="Only convert existing tiles in DIR to B&W (MeshOS); no download.",
    )
    args = parser.parse_args()

    if args.convert_bw_only:
        gen_bw = MeshtasticTileGenerator(output_dir=args.convert_bw_only)
        gen_bw.convert_tiles_to_bw()
        # Update metadata description for MeshOS
        meta_path = Path(args.convert_bw_only) / "metadata.json"
        if meta_path.exists():
            try:
                with open(meta_path, encoding="utf-8") as f:
                    meta = json.load(f)
                meta["description"] = "Map tiles for T-Deck (MeshOS simple black and white)"
                with open(meta_path, "w", encoding="utf-8") as f:
                    json.dump(meta, f, indent=2)
                _log(f"Updated {meta_path}")
            except Exception as e:
                _log(f"Warning: could not update metadata: {e}", file=sys.stderr)
        sys.exit(0)

    gen = MeshtasticTileGenerator(output_dir=args.output_dir, delay=args.delay)
    gen._firmware = args.format
    if args.sample_only:
        gen.create_sample_tile()
        return

    if not any([args.region, args.city, args.cities, args.coords]):
        _log("Error: specify one of --region, --city, --cities, or --coords", file=sys.stderr)
        sys.exit(1)
    if not requests:
        _log("Install requests: pip install requests", file=sys.stderr)
        sys.exit(1)
    _log(f"Starting tile download: region={getattr(args, 'region', None)}, output={args.output_dir}, zoom={args.min_zoom}-{args.max_zoom}")
    north = south = east = west = None
    if args.region:
        bounds = get_region_bounds_from_json(args.region, regions_path)
        if not bounds:
            _log(f"Unknown region: {args.region}", file=sys.stderr)
            sys.exit(1)
        north, south, east, west = bounds["north"], bounds["south"], bounds["east"], bounds["west"]
    elif args.city:
        lookup = CityLookup()
        coord = lookup.get_coordinates(args.city)
        if not coord:
            _log(f"Could not find: {args.city}", file=sys.stderr)
            sys.exit(1)
        buf_deg = args.buffer / 111.0
        north = coord["lat"] + buf_deg
        south = coord["lat"] - buf_deg
        east = coord["lon"] + buf_deg
        west = coord["lon"] - buf_deg
    elif args.cities:
        lookup = CityLookup()
        cities = [c.strip() for c in args.cities.split(";") if c.strip()]
        bbox = lookup.get_bounding_box_for_cities(cities, args.buffer)
        if not bbox:
            sys.exit(1)
        north, south, east, west = bbox["north"], bbox["south"], bbox["east"], bbox["west"]
    elif args.coords:
        if None in (args.north, args.south, args.east, args.west):
            _log("Error: --coords requires --north, --south, --east, --west", file=sys.stderr)
            sys.exit(1)
        north, south, east, west = args.north, args.south, args.east, args.west
    else:
        sys.exit(1)

    if north is None:
        _log("Error: Could not determine coordinates", file=sys.stderr)
        sys.exit(1)

    gen.generate_tiles(
        north=north, south=south, east=east, west=west,
        min_zoom=args.min_zoom, max_zoom=args.max_zoom,
        source=args.source, max_workers=args.max_workers,
    )


if __name__ == "__main__":
    main()
