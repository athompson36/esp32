"""Device wizard: catalog and scaffold devices/ + registry/ from template.
Also: agent helpers to download device docs, SDK install, and place them in correct structure."""
import json
import os
import re
import subprocess
import urllib.request
from urllib.parse import urlparse

try:
    import yaml
except ImportError:
    yaml = None

# Doc types for download_device_doc; filenames default to <type>.pdf or <type>_<n>.<ext>
DOC_TYPES = ("datasheet", "schematic", "manual", "reference", "other")
MAX_DOC_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB
DOWNLOAD_TIMEOUT = 60

# Load REPO_ROOT from config at runtime to avoid circular import in routes
def _repo_root():
    from config import REPO_ROOT
    return REPO_ROOT


def _catalog_path():
    return os.path.join(os.path.dirname(__file__), "device_catalog.json")


def load_device_catalog():
    """Load device_catalog.json. Returns { vendors: [], devices: [] } or empty."""
    path = _catalog_path()
    if not os.path.isfile(path):
        return {"vendors": [], "devices": []}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {"vendors": [], "devices": []}


def get_catalog_device(device_id: str) -> dict | None:
    """Return the catalog entry for device_id (with optional sdk block), or None."""
    data = load_device_catalog()
    device_id = _safe_id(device_id)
    for d in data.get("devices") or []:
        if (d.get("id") or "").lower() == device_id:
            return d
    return None


def install_device_sdk(device_id: str, catalog_entry: dict | None = None) -> tuple[bool, str]:
    """
    Install the SDK for a device when a full SDK is available (e.g. PlatformIO platform).
    catalog_entry: optional device dict from catalog (must include sdk if available).
    Returns (success, message). Runs platformio pkg install -g -p <platform_id> when install_type is platformio_platform.
    """
    entry = catalog_entry or get_catalog_device(device_id)
    if not entry:
        return False, f"Device not in catalog: {device_id}"
    sdk = entry.get("sdk") or {}
    if not sdk.get("available"):
        return True, "No SDK to install for this device"
    install_type = (sdk.get("install_type") or "").strip()
    platform_id = (sdk.get("platform_id") or "").strip()
    if install_type == "platformio_platform" and platform_id:
        pio = "pio"
        if not os.path.isfile(os.path.join(_repo_root(), "platformio.ini")):
            # Prefer global install so all projects can use it
            try:
                r = subprocess.run(
                    [pio, "pkg", "install", "-g", "-p", platform_id],
                    capture_output=True,
                    text=True,
                    timeout=300,
                    cwd=_repo_root(),
                )
                if r.returncode != 0:
                    return False, r.stderr or r.stdout or f"pio pkg install failed (exit {r.returncode})"
                return True, f"Installed PlatformIO platform: {platform_id}"
            except FileNotFoundError:
                return False, "PlatformIO (pio) not found. Install it (e.g. pip install platformio) or use the Docker container for builds."
            except subprocess.TimeoutExpired:
                return False, "SDK install timed out"
            except Exception as e:
                return False, str(e)[:200]
    return True, "SDK install type not supported or platform_id missing"


def get_device_sdk_path(device_id: str) -> dict | None:
    """
    Return SDK path and metadata for a device so the AI and tools can find the SDK.
    Returns None if device not in lab or no SDK; else { path, platform_id, install_type, docs_hint }.
    PlatformIO platforms are installed globally by pio; path is the platformio core dir or empty (use pio run).
    """
    entry = get_catalog_device(device_id)
    if not entry:
        return None
    sdk = entry.get("sdk") or {}
    if not sdk.get("available"):
        return None
    root = _repo_root()
    dev_id = _safe_id(device_id)
    device_dir = os.path.join(root, "devices", dev_id)
    docs_path = os.path.join(device_dir, "notes", "SDK_AND_TOOLS.md")
    docs_hint = ("devices/" + dev_id + "/notes/SDK_AND_TOOLS.md") if os.path.isfile(docs_path) else None
    return {
        "device_id": dev_id,
        "platform_id": (sdk.get("platform_id") or "").strip(),
        "install_type": (sdk.get("install_type") or "").strip(),
        "path": "",  # PlatformIO uses global packages; firmware builds use pio run in project
        "docs_hint": docs_hint,
    }


def list_devices_in_lab():
    """Return set of device IDs that already exist under devices/ or registry/devices/."""
    root = _repo_root()
    dev_dir = os.path.join(root, "devices")
    reg_dir = os.path.join(root, "registry", "devices")
    ids = set()
    if os.path.isdir(dev_dir):
        for name in os.listdir(dev_dir):
            if os.path.isdir(os.path.join(dev_dir, name)) and not name.startswith("."):
                ids.add(name)
    if os.path.isdir(reg_dir):
        for name in os.listdir(reg_dir):
            if name.endswith(".json"):
                ids.add(name[:-5])
    return ids


def _safe_id(s):
    """Canonical device_id: lowercase, underscores only."""
    return re.sub(r"[^a-z0-9_]", "_", (s or "").strip().lower()).strip("_") or "device"


# Inventory category -> YAML filename (under inventory/items/)
INVENTORY_CATEGORY_FILES = {
    "controller": "controllers.yaml",
    "sbc": "sbcs.yaml",
    "sensor": "sensors.yaml",
    "accessory": "accessories.yaml",
    "component": "components.yaml",
}


def add_item_to_inventory(device_id, name, vendor="", mcu="", category="controller", datasheet_url=None):
    """
    Append one item to inventory/items/<category>.yaml. Uses device_id as item id.
    Returns (success, message). Idempotent: if id already exists in that file, skip and return success.
    Appends as YAML text to preserve existing file comments and formatting.
    """
    if not yaml:
        return False, "PyYAML required to add to inventory"
    category = (category or "controller").strip().lower()
    if category not in INVENTORY_CATEGORY_FILES:
        return False, f"Invalid inventory category: {category}"
    root = _repo_root()
    items_dir = os.path.join(root, "inventory", "items")
    filename = INVENTORY_CATEGORY_FILES[category]
    path = os.path.join(items_dir, filename)
    if not os.path.isfile(path):
        return False, f"Inventory file not found: inventory/items/{filename}"
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except (yaml.YAMLError, OSError) as e:
        return False, f"Cannot read inventory file: {e}"
    items = data.get("items") or []
    if any((it.get("id") or "") == device_id for it in items):
        return True, "Already in inventory"
    entry = {
        "id": device_id,
        "name": (name or device_id).strip(),
        "manufacturer": (vendor or "").strip() or None,
        "part_number": None,
        "model": (mcu or "").strip() or None,
        "quantity": 1,
        "location": "",
        "specs": {"mcu": (mcu or "").strip()} if (mcu or "").strip() else {},
        "datasheet_url": (datasheet_url or "").strip() or None,
        "datasheet_file": None,
        "notes": f"Added from device wizard. See devices/{device_id}/.",
        "used_in": [device_id],
        "tags": [device_id],
    }
    # Append as a single list item so we don't rewrite the whole file (preserves comments/formatting)
    block = yaml.dump([entry], default_flow_style=False, allow_unicode=True, sort_keys=False)
    # First line is "- id: ..."; indent it to match "  - id: ..." in the file
    lines = block.strip().split("\n")
    indented = "\n".join("  " + line for line in lines)
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        if not content.rstrip().endswith("\n"):
            content = content.rstrip() + "\n"
        content = content + "\n" + indented + "\n"
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
    except OSError as e:
        return False, f"Cannot write inventory file: {e}"
    return True, f"Added to inventory/items/{filename}"


def add_bom_row_to_inventory(name, part_number=None, quantity=1, category="component"):
    """
    Append a BOM row as a new item to inventory/items/<category>.yaml.
    Generates id from name (slug). Returns (success, message).
    """
    if not yaml:
        return False, "PyYAML required to add to inventory"
    category = (category or "component").strip().lower()
    if category not in INVENTORY_CATEGORY_FILES:
        return False, f"Invalid inventory category: {category}"
    root = _repo_root()
    items_dir = os.path.join(root, "inventory", "items")
    filename = INVENTORY_CATEGORY_FILES[category]
    path = os.path.join(items_dir, filename)
    if not os.path.isfile(path):
        return False, f"Inventory file not found: inventory/items/{filename}"
    item_id = re.sub(r"[^a-z0-9_]", "_", (name or "").strip().lower()).strip("_") or "item"
    # Ensure unique id (append suffix if needed)
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except (yaml.YAMLError, OSError) as e:
        return False, f"Cannot read inventory file: {e}"
    items = data.get("items") or []
    base_id = item_id
    n = 0
    while any((it.get("id") or "") == item_id for it in items):
        n += 1
        item_id = f"{base_id}_{n}"
    entry = {
        "id": item_id,
        "name": (name or "").strip() or item_id,
        "manufacturer": None,
        "part_number": (part_number or "").strip() or None,
        "model": None,
        "quantity": int(quantity) if quantity is not None else 1,
        "location": "",
        "specs": {},
        "datasheet_url": None,
        "datasheet_file": None,
        "notes": "Added from project BOM.",
        "used_in": [],
        "tags": [],
    }
    block = yaml.dump([entry], default_flow_style=False, allow_unicode=True, sort_keys=False)
    lines = block.strip().split("\n")
    indented = "\n".join("  " + line for line in lines)
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        if not content.rstrip().endswith("\n"):
            content = content.rstrip() + "\n"
        content = content + "\n" + indented + "\n"
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
    except OSError as e:
        return False, f"Cannot write inventory file: {e}"
    return True, f"Added to inventory/items/{filename}. Run scripts/build_db.py to refresh the database."


def _references_block(doc_links):
    """Build References section markdown from doc_links dict."""
    lines = []
    if doc_links.get("datasheet"):
        lines.append(f"- **Datasheet:** {doc_links['datasheet']}")
    if doc_links.get("schematic"):
        lines.append(f"- **Schematic:** {doc_links['schematic']}")
    repos = doc_links.get("firmware_repos") or []
    if isinstance(repos, str):
        repos = [repos]
    for i, url in enumerate(repos):
        if url and isinstance(url, str) and url.strip():
            lines.append(f"- **Firmware repo {i + 1}:** {url.strip()}")
    for k, v in (doc_links or {}).items():
        if k in ("datasheet", "schematic", "firmware_repos"):
            continue
        if v and isinstance(v, str) and v.strip():
            lines.append(f"- **{k}:** {v.strip()}")
    if not lines:
        return "- (Add datasheet, schematic, and firmware repo links.)"
    return "\n".join(lines)


def scaffold_device(device_id, name, vendor="", mcu="", doc_links=None, add_to_inventory=False, inventory_category="controller"):
    """
    Create devices/<device_id>/ and registry/devices/<device_id>.json with stub files.
    doc_links: { datasheet?, schematic?, firmware_repos?: [urls], ... }
    add_to_inventory: if True, append item to inventory/items/<inventory_category>.yaml.
    inventory_category: controller | sbc | sensor | accessory | component (used when add_to_inventory=True).
    Returns (success, message, paths_dict or None).
    """
    root = _repo_root()
    device_id = _safe_id(device_id)
    if not device_id:
        return False, "Invalid device ID", None
    doc_links = doc_links or {}
    refs = _references_block(doc_links)

    device_dir = os.path.join(root, "devices", device_id)
    if os.path.isdir(device_dir):
        return False, f"Device directory already exists: devices/{device_id}", None

    vendor_name = (vendor or "Unknown").strip() or "Unknown"
    display_name = (name or device_id).strip() or device_id

    # Stub content templates
    device_context = f"""# Device Context — {display_name}

**Device ID:** `{device_id}`
**Board:** {display_name} ({mcu or '—'})
**Vendor:** {vendor_name}
**Lab contract:** `firmware/` · `configs/` · `pinmaps/` · `notes/`

---

## Summary

(Describe the board: MCU, radios, display, connectivity, power.)

---

## Hardware at a Glance

| Item | Detail |
|------|--------|
| **MCU** | {mcu or '—'} |
| **Power** | (Voltage, battery, USB) |
| **Connectivity** | (LoRa, WiFi, BLE, etc.) |

---

## Context Files in This Device

| File | Description |
|------|-------------|
| [pinmaps/HARDWARE_LAYOUT.md](pinmaps/HARDWARE_LAYOUT.md) | Pinout, power tree, block diagram |
| [pinmaps/PERIPHERALS.md](pinmaps/PERIPHERALS.md) | Peripherals, GPIO/bus assignments |
| [notes/PROTOTYPING.md](notes/PROTOTYPING.md) | Free GPIOs, expansion, safety |
| [notes/SDK_AND_TOOLS.md](notes/SDK_AND_TOOLS.md) | SDKs, tools, Docker, flash/serial |
| [firmware/README.md](firmware/README.md) | Firmware repos and build systems |

---

## References

{refs}

---

## Lab

- [CONTEXT.md](../../CONTEXT.md), [devices/README.md](../README.md)
"""

    sdk_tools = f"""# {display_name} — SDKs & Tools

**Device:** {display_name}
**Container:** platformio-lab (or host)

---

## Build

(PlatformIO env, Arduino CLI, or other build system.)

---

## Flash / deploy

(esptool, avrdude, or SD image / SSH for SBC.)

---

## Docker

See [docker/TOOLS_AND_SDK.md](../../../docker/TOOLS_AND_SDK.md).
"""

    prototyping = f"""# {display_name} — Prototyping

- **Voltage:** (Logic levels, max ratings.)
- **Current:** (Per-pin and total limits.)
- **Free GPIOs:** (List or "See HARDWARE_LAYOUT.")
"""

    hardware_layout = f"""# {display_name} — Hardware Layout

**Board:** {display_name}
**MCU:** {mcu or '—'}

---

## Pinout Summary

(Table: Pin | Function | Notes.)

---

## Power

(Voltage rails, battery, USB.)
"""

    peripherals = f"""# {display_name} — Peripherals

(UART, I2C, SPI, PWM, ADC, etc. with GPIO assignments.)
"""

    configs_readme = f"""# {display_name} — Configs

Store build configs, board options, and env configs here.
"""

    firmware_readme = f"""# {display_name} — Firmware

Per the lab contract, firmware lives here with **overlays** for customisations.

---

## Available firmwares

(Add links to upstream repos; clone into `firmware/<name>/repo/`, overlays in `firmware/<name>/overlays/`.)

---

## Layout

```
firmware/
├── meshtastic/   # or meshcore, custom, etc.
│   ├── repo/
│   └── overlays/
└── custom/
```
"""

    try:
        os.makedirs(os.path.join(device_dir, "firmware"), exist_ok=True)
        os.makedirs(os.path.join(device_dir, "configs"), exist_ok=True)
        os.makedirs(os.path.join(device_dir, "pinmaps"), exist_ok=True)
        os.makedirs(os.path.join(device_dir, "notes"), exist_ok=True)
        os.makedirs(os.path.join(device_dir, "docs"), exist_ok=True)
    except OSError as e:
        return False, f"Cannot create device directory: {e}", None

    files = [
        (os.path.join(device_dir, "DEVICE_CONTEXT.md"), device_context),
        (os.path.join(device_dir, "notes", "SDK_AND_TOOLS.md"), sdk_tools),
        (os.path.join(device_dir, "notes", "PROTOTYPING.md"), prototyping),
        (os.path.join(device_dir, "pinmaps", "HARDWARE_LAYOUT.md"), hardware_layout),
        (os.path.join(device_dir, "pinmaps", "PERIPHERALS.md"), peripherals),
        (os.path.join(device_dir, "configs", "README.md"), configs_readme),
        (os.path.join(device_dir, "firmware", "README.md"), firmware_readme),
    ]
    for path, content in files:
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
        except OSError as e:
            return False, f"Cannot write {path}: {e}", None

    # Registry JSON (minimal; flash_ops can use chip from config.FLASH_DEVICES if added there)
    reg_dir = os.path.join(root, "registry", "devices")
    try:
        os.makedirs(reg_dir, exist_ok=True)
    except OSError as e:
        return False, f"Cannot create registry dir: {e}", None

    chip = "esp32" if "esp32" in (mcu or "").lower() else ""
    if "esp32-s3" in (mcu or "").lower():
        chip = "esp32s3"
    elif "esp32-c3" in (mcu or "").lower():
        chip = "esp32c3"

    registry_entry = {
        "id": device_id,
        "name": display_name,
        "mcu": mcu or "",
        "radios": [],
        "display": "",
        "battery": "",
        "storage": "",
        "flash_methods": ["usb_direct"] if chip else [],
        "compatible_firmware": [],
        "capability": {
            "chip": chip,
            "flash_size": "4MB" if chip else "",
            "flash_mode": "dio" if chip else "",
            "rf_bands": [],
            "can_support": False,
            "sd_support": False,
            "launcher_compatible": False,
        },
    }
    reg_path = os.path.join(reg_dir, f"{device_id}.json")
    try:
        with open(reg_path, "w", encoding="utf-8") as f:
            json.dump(registry_entry, f, indent=2, ensure_ascii=False)
    except OSError as e:
        return False, f"Cannot write registry: {e}", None

    paths = {
        "device_dir": f"devices/{device_id}",
        "registry_file": f"registry/devices/{device_id}.json",
    }
    if add_to_inventory:
        inv_ok, inv_msg = add_item_to_inventory(
            device_id,
            display_name,
            vendor=vendor_name,
            mcu=mcu or "",
            category=inventory_category or "controller",
            datasheet_url=doc_links.get("datasheet") if doc_links else None,
        )
        if not inv_ok:
            return False, f"Device created but inventory failed: {inv_msg}", paths
        paths["inventory_file"] = f"inventory/items/{INVENTORY_CATEGORY_FILES.get(inventory_category or 'controller', 'controllers.yaml')}"
    return True, f"Created {device_id}", paths


# --- Agent: device docs download and structure ---

def get_device_dir(device_id: str):
    """Return absolute path to devices/<device_id> if it exists, else None."""
    root = _repo_root()
    device_id = _safe_id(device_id)
    if not device_id:
        return None
    path = os.path.join(root, "devices", device_id)
    return path if os.path.isdir(path) else None


def get_device_docs_dir(device_id: str, create: bool = True):
    """
    Return absolute path to devices/<device_id>/docs/. Create dir if create=True and device exists.
    Returns None if device dir does not exist.
    """
    dev_dir = get_device_dir(device_id)
    if not dev_dir:
        return None
    docs_dir = os.path.join(dev_dir, "docs")
    if create:
        try:
            os.makedirs(docs_dir, exist_ok=True)
        except OSError:
            return None
    return docs_dir


def _sanitize_doc_basename(name: str, ext: str = "") -> str:
    """Safe filename: alphanumeric, underscore, hyphen only; no path components."""
    base = (name or "").strip()
    base = re.sub(r"[^a-zA-Z0-9_\-.]", "_", base).strip("._") or "doc"
    if len(base) > 120:
        base = base[:120]
    if ext and not base.lower().endswith(ext.lower()):
        base = base + (ext if ext.startswith(".") else "." + ext)
    return base or "doc.pdf"


def download_device_doc(
    device_id: str,
    url: str,
    doc_type: str = "other",
    suggested_filename: str = None,
) -> tuple[bool, str]:
    """
    Download a file from url and save to devices/<device_id>/docs/ with correct naming.
    doc_type: datasheet | schematic | manual | reference | other (used for default name).
    suggested_filename: optional basename (will be sanitized); else derived from URL or doc_type.
    Returns (success, path_relative_to_repo_or_error_message).
    """
    device_id = _safe_id(device_id)
    if not device_id:
        return False, "Invalid device ID"
    doc_type = (doc_type or "other").strip().lower()
    if doc_type not in DOC_TYPES:
        doc_type = "other"
    docs_dir = get_device_docs_dir(device_id, create=True)
    if not docs_dir:
        return False, f"Device directory does not exist: devices/{device_id}"

    url = (url or "").strip()
    if not url or not url.startswith(("http://", "https://")):
        return False, "Invalid URL"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "cyber-lab-agent/1.0"})
        with urllib.request.urlopen(req, timeout=DOWNLOAD_TIMEOUT) as resp:
            data = resp.read()
            if len(data) > MAX_DOC_SIZE_BYTES:
                return False, f"File too large (max {MAX_DOC_SIZE_BYTES // (1024*1024)} MB)"
            content_type = (resp.headers.get("Content-Type") or "").split(";")[0].strip().lower()
            suggested = (suggested_filename or "").strip()
            if not suggested:
                disp = resp.headers.get("Content-Disposition")
                if disp and "filename=" in disp:
                    raw = disp.split("filename=", 1)[-1].strip().strip('"\'')
                    suggested = os.path.basename(raw)
                if not suggested:
                    parsed = urlparse(url)
                    suggested = os.path.basename(parsed.path or "")
                if not suggested or suggested == "/":
                    suggested = f"{doc_type}.pdf"
            basename = _sanitize_doc_basename(suggested, "")
            allowed_ext = (".pdf", ".png", ".jpg", ".jpeg", ".svg", ".zip", ".html", ".md", ".txt")
            if not basename.lower().endswith(allowed_ext):
                base_stem = basename.rsplit(".", 1)[0] if "." in basename else basename
                basename = base_stem + ".pdf"
            stem, ext = os.path.splitext(basename)
            final_path = os.path.join(docs_dir, basename)
            n = 1
            while os.path.isfile(final_path):
                n += 1
                final_path = os.path.join(docs_dir, f"{stem}_{n}{ext}")
            with open(final_path, "wb") as f:
                f.write(data)
            rel = os.path.relpath(final_path, _repo_root())
            return True, rel.replace("\\", "/")
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}: {e.reason}"
    except urllib.error.URLError as e:
        return False, f"URL error: {e.reason}"
    except OSError as e:
        return False, str(e)
    except Exception as e:
        return False, str(e)[:200]


def device_search(query: str, max_results: int = 10) -> tuple[list[dict], str | None]:
    """
    Search the web for device-related content (datasheets, schematics, etc.).
    Returns (list of { title, url, snippet }, error_message or None).
    Requires duckduckgo-search: pip install duckduckgo-search (optional).
    """
    query = (query or "").strip()
    if not query:
        return [], "Empty query"
    try:
        from duckduckgo_search import DDGS
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": (r.get("title") or "").strip(),
                    "url": (r.get("href") or r.get("link") or "").strip(),
                    "snippet": (r.get("body") or r.get("snippet") or "").strip()[:300],
                })
        return results, None
    except ImportError:
        return [], "Install duckduckgo-search for web search: pip install duckduckgo-search"
    except Exception as e:
        return [], str(e)[:200]


def get_device_structure(device_id: str) -> dict | None:
    """
    Return structure and naming conventions for a device so the agent knows where to place content.
    None if device does not exist.
    """
    dev_dir = get_device_dir(device_id)
    if not dev_dir:
        return None
    root = _repo_root()
    device_id = os.path.basename(dev_dir)
    rel = os.path.relpath(dev_dir, root).replace("\\", "/")
    docs_dir = os.path.join(dev_dir, "docs")
    return {
        "device_id": device_id,
        "device_dir": rel,
        "docs_dir": rel + "/docs",
        "docs_dir_absolute": docs_dir if os.path.isdir(docs_dir) else None,
        "naming": {
            "datasheet": "docs/datasheet.pdf or docs/datasheet_<vendor>.pdf",
            "schematic": "docs/schematic.pdf or docs/schematic_<name>.pdf",
            "manual": "docs/manual.pdf",
            "reference": "docs/<topic>.pdf",
        },
        "allowed_doc_types": list(DOC_TYPES),
        "existing_docs": sorted(os.listdir(docs_dir)) if os.path.isdir(docs_dir) else [],
    }
