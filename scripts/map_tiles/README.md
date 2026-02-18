# Map tiles (T-Deck / Meshtastic compatible)

Compatible with [JustDr00py/tdeck-maps](https://github.com/JustDr00py/tdeck-maps). Same folder structure and naming.

## Folder structure

```
{output_dir}/
  metadata.json
  {zoom}/{x}/{y}.png
```

Example: `tiles/10/256/384.png`, `tiles/metadata.json`.

## Regions

Predefined regions (continents, countries, US states) are in **repo root** `regions/regions.json`. List them:

```bash
python scripts/map_wizard.py list
python scripts/map_wizard.py list --json
```

## Estimate

```bash
python scripts/map_wizard.py estimate california --min-zoom 8 --max-zoom 12
python scripts/map_wizard.py estimate california --min-zoom 8 --max-zoom 12 --json
```

## Generate tiles

From repo root:

```bash
# Predefined region (from regions/regions.json)
python scripts/map_tiles/meshtastic_tiles.py --region california --min-zoom 8 --max-zoom 12 --output-dir tiles

# City (Nominatim lookup)
python scripts/map_tiles/meshtastic_tiles.py --city "San Francisco" --min-zoom 8 --max-zoom 12

# Multiple cities (semicolon-separated, quoted)
python scripts/map_tiles/meshtastic_tiles.py --cities "San Francisco; Oakland; San Jose" --min-zoom 8 --max-zoom 12

# Custom bounds
python scripts/map_tiles/meshtastic_tiles.py --coords --north 40.8 --south 40.6 --east -74.0 --west -74.2 --min-zoom 10 --max-zoom 14
```

Map sources: `--source osm` (default) | `satellite` | `terrain` | `cycle` | `carto` | `carto_dark` | `stadia` | `stadia_dark`. **Dark themes (less glare):** `carto_dark` (CARTO Dark Matter) and `stadia_dark` (Stadia Alidade Smooth Dark). **Alternatives to OSM:** `carto` and `stadia`; use them if OSM blocks bulk or offline use.

## OSM tile policy and offline use

**tile.openstreetmap.org does not allow bulk downloading or offline use.** Their [Tile Usage Policy](https://operations.osmfoundation.org/policies/tiles/) states that building tile archives for later use (e.g. T-Deck offline maps) is prohibited. Requests may be blocked or rate-limited.

- **If downloads fail or you see "Access denied" / 403:** Run the diagnostic (see below) and consider using an alternative source.
- **Alternatives for offline T-Deck maps:** Self-host tiles ([switch2osm.org](https://switch2osm.org/)), use a commercial/provider tile service that allows offline use, or use [OSM-derived raster providers](https://wiki.openstreetmap.org/wiki/Raster_tile_providers) that permit it.
- The script sends a [policy-compliant User-Agent](https://operations.osmfoundation.org/policies/tiles/#31-identification) (app name + contact) so that single-tile or light use is less likely to be blocked; bulk/offline use remains against OSM’s policy.

## Diagnose tile download issues

From repo root:

```bash
python scripts/map_tiles/diagnose_tiles.py
```

This checks: Python and working directory, `requests`/Pillow, `regions/regions.json`, OSM tile server reachability (and `x-blocked` header), and a one-tile build. Fix any reported failures before running a full region download.

## Dependencies

- **requests** — required for download and city lookup
- **Pillow** — optional, for `--sample-only` test tile

```bash
pip install requests pillow
```

## Validate output

```bash
python scripts/sd_validator.py tiles
python scripts/sd_validator.py tiles --json
```

## Meshtastic Device-UI (MUI) — SD card setup

So tiles load on the T-Deck, follow the **exact** structure expected by [Meshtastic device-ui](https://github.com/meshtastic/device-ui/tree/master/maps):

1. **SD card:** Format as **FAT32** or **exFAT** (exFAT recommended). Use a card **≥ 2GB** (smaller cards are not supported for maps).
2. **Path:** At the **root** of the SD card create a folder named **`maps`** (plural).
3. **Style folder:** Inside `maps`, create a folder for this tile set, e.g. **`osm`**, **`carto`**, or **`terrain`**.
4. **Contents:** Copy the **contents** of your generated output folder (e.g. `tiles_north_dakota` or `tiles`) **into** that style folder — not the folder itself. You must end up with:
   - `maps/carto/metadata.json`
   - `maps/carto/8/` … `maps/carto/12/` (zoom folders)
   - Inside each zoom: `x/y.png` (e.g. `maps/carto/10/256/384.png`)

So the structure on SD is **`maps/<style>/z/x/y.png`** where `z` is the zoom level (8, 9, 10, …). Our script already outputs `{zoom}/{x}/{y}.png`, so `zoom` = `z`.

5. **Eject** the SD card and insert it into the T-Deck. Restart the device if needed. In MUI, open the Map screen; if you don’t see tiles, **zoom out** to at least level 6–8 so the device can load the zoom levels you downloaded.
6. **Long-press** the Map button to switch between map styles (folders under `maps`) and adjust brightness/contrast.

**If maps still don’t load:** Confirm the SD is detected (MUI home → SD card icon). Check that folder names are **maps** and e.g. **carto** (lowercase, no extra spaces). Optional: device-ui’s starter tiles use 8-bit palette PNGs; for compatibility you can convert with:  
`find tiles -name "*.png" -exec mogrify -colors 256 -depth 8 +dither -define png:color-type=3 {} \;`
