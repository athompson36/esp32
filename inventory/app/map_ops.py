"""Map tile wizard: load regions, estimate tiles/size. Uses regions/regions.json (tdeck-maps compatible)."""
import json
import math
import os

from config import REPO_ROOT


def _regions_path():
    return os.path.join(REPO_ROOT, "regions", "regions.json")


def load_regions():
    """Load regions.json; return dict with regions and map_sources."""
    path = _regions_path()
    if not os.path.isfile(path):
        return {"regions": [], "map_sources": []}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def get_regions_grouped():
    """Return regions grouped by category (continent, country, state)."""
    data = load_regions()
    regions = data.get("regions", [])
    grouped = {"continent": [], "country": [], "state": []}
    for r in regions:
        cat = (r.get("category") or "country").lower()
        if cat not in grouped:
            grouped[cat] = []
        grouped[cat].append({"slug": r.get("slug"), "name": r.get("name"), "country": r.get("country")})
    return grouped


def get_region_bounds(region_slug):
    """Return bounds dict (north, south, east, west) for slug or None."""
    data = load_regions()
    for r in data.get("regions", []):
        if (r.get("slug") or "").lower() == region_slug.lower():
            return r.get("bounds")
    return None


def deg2num(lat_deg, lon_deg, zoom):
    """Web Mercator tile index from lat/lon and zoom."""
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    x = int((lon_deg + 180.0) / 360.0 * n)
    y = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return (x, y)


def count_tiles(north, south, east, west, min_zoom, max_zoom):
    """Total tile count for bounds and zoom range."""
    total = 0
    for zoom in range(min_zoom, max_zoom + 1):
        x_min, y_max = deg2num(south, west, zoom)
        x_max, y_min = deg2num(north, east, zoom)
        if x_min > x_max:
            x_min, x_max = x_max, x_min
        if y_min > y_max:
            y_min, y_max = y_max, y_min
        total += (x_max - x_min + 1) * (y_max - y_min + 1)
    return total


def estimate_mb(tile_count, avg_kb=15):
    return tile_count * avg_kb / 1024.0


def wizard_list_regions():
    """Full list and grouped for API."""
    data = load_regions()
    return {
        "regions": data.get("regions", []),
        "grouped": get_regions_grouped(),
        "map_sources": data.get("map_sources", []),
    }


def wizard_estimate(region_slug, min_zoom=8, max_zoom=12):
    """Estimate tile count and size for region + zoom. Returns dict or None."""
    bounds = get_region_bounds(region_slug)
    if not bounds:
        return None
    n = count_tiles(
        bounds["north"], bounds["south"], bounds["east"], bounds["west"],
        min_zoom, max_zoom,
    )
    mb = estimate_mb(n)
    return {
        "region_slug": region_slug,
        "min_zoom": min_zoom,
        "max_zoom": max_zoom,
        "tile_count": n,
        "estimated_mb": round(mb, 1),
        "estimated_gb": round(mb / 1024.0, 2),
        "sd_fits": {f"{g}GB": (mb / 1024.0) <= g for g in (16, 32, 64, 128)},
    }
