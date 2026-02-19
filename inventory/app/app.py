#!/usr/bin/env python3
"""
Inventory management web app with search, filters, and optional AI query.
Run from repo root: python inventory/app/app.py
Then open http://127.0.0.1:5000
"""
import json
import os
import re
import sqlite3
import subprocess
import sys
import tempfile
from urllib.parse import unquote

from flask import Flask, Response, jsonify, render_template, request, send_file, stream_with_context

# Ensure we run from repo root for DB path
if os.path.basename(os.getcwd()) == "app":
    os.chdir(os.path.dirname(os.getcwd()))

from config import (
    ARTIFACTS_DIR,
    BACKUPS_DIR,
    BUILD_CONFIG,
    get_ai_settings_public,
    get_database_path,
    get_openai_api_key,
    get_openai_base_url,
    get_openai_model,
    REPO_ROOT,
    save_ai_settings,
    get_path_settings,
    save_path_settings,
)
from updates import get_updates
from flash_ops import (
    backup_flash,
    build_firmware,
    download_release_firmware,
    flash_firmware,
    get_build_config,
    get_flash_devices,
    list_artifacts_and_backups,
    list_patches,
    list_serial_ports,
    list_serial_ports_with_detection,
    restore_flash,
)
from project_ops import (
    bom_csv_digikey,
    bom_csv_mouser,
    check_bom_against_inventory,
    get_controllers_in_inventory,
    list_proposals,
    load_proposal,
    save_proposal,
)
from project_templates import get_templates, list_controllers
from map_ops import wizard_estimate, wizard_list_regions
from device_ops import (
    add_bom_row_to_inventory,
    device_search,
    download_device_doc,
    get_device_structure,
    load_device_catalog,
    list_devices_in_lab,
    scaffold_device,
)
from debug_ops import (
    get_debug_context,
    run_esptool_version,
    run_health_checks,
    serial_clear_buffer,
    serial_get_buffer,
    serial_is_active,
    serial_start,
    serial_stop,
)
from config_wizard_ops import (
    get_config_wizard_context,
    list_config_presets,
    load_config_preset,
    save_config_preset,
)

PROJECT_PLANNING_SYSTEM = (
    "You are a project planning assistant for electronics/hardware projects. "
    "The user has an inventory list below; use it to suggest parts they might already have or need to buy. "
    "Help them develop their idea into a concrete plan. "
    "When you suggest specific parts, end your reply with a line starting exactly with 'BOM:' followed by a JSON array of objects, each with keys: name (string), part_number (string, optional), quantity (integer). "
    "Example: BOM: [{\"name\": \"ESP32 DevKit C\", \"part_number\": \"\", \"quantity\": 2}, {\"name\": \"10k resistor\", \"part_number\": \"\", \"quantity\": 10}] "
    "When the project involves a circuit or PCB, also output a DESIGN block for pinouts, wiring, schematic, and enclosure. "
    "Use exactly: DESIGN: then a single JSON object with keys: pin_outs (array of {pin, function, notes}), wiring (array of {from, to, net}), schematic (string: markdown description or block diagram notes for a schematic), enclosure (string: markdown notes for 3D-printed enclosure, dimensions and mounting). "
    "Example: DESIGN: {\"pin_outs\": [{\"pin\": \"GPIO21\", \"function\": \"I2C SDA\", \"notes\": \"\"}], \"wiring\": [{\"from\": \"ESP32.GPIO21\", \"to\": \"OLED.SDA\", \"net\": \"I2C_SDA\"}], \"schematic\": \"ESP32 I2C to OLED...\", \"enclosure\": \"Box 80x60x30mm, cutouts for USB and display.\"} "
    "You can also help with moving parts: to add an inventory item to this project's BOM, tell the user to open the Inventory tab, click the item, and use 'Add to project' to choose this project. To add a BOM row to their inventory, tell them to use 'Add to inventory' next to that row in the Parts BOM section."
)

app = Flask(__name__, static_folder="static", template_folder="templates")


def get_db():
    db_path = get_database_path()
    if not os.path.isfile(db_path):
        return None
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def row_to_item(row):
    if row is None:
        return None
    d = dict(row)
    for key in ("specs", "used_in", "tags"):
        if d.get(key) and isinstance(d[key], str):
            try:
                d[key] = json.loads(d[key])
            except (json.JSONDecodeError, TypeError):
                pass
    return d


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/settings/ai", methods=["GET"])
def api_settings_ai_get():
    """Return AI settings safe for UI: api_key_set, model, base_url (never the key)."""
    try:
        return jsonify(get_ai_settings_public())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/settings/ai", methods=["POST"])
def api_settings_ai_post():
    """Update AI settings. Body: api_key (optional, set or '' to clear), model, base_url."""
    data = request.get_json() or {}
    api_key = data.get("api_key") if "api_key" in data else None
    model = data.get("model") if "model" in data else None
    base_url = data.get("base_url") if "base_url" in data else None
    try:
        save_ai_settings(api_key=api_key, model=model, base_url=base_url)
        return jsonify(get_ai_settings_public())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/settings/paths", methods=["GET"])
def api_settings_paths_get():
    """Return path settings for UI: docker_container, frontend_path, backend_path, database_path, mcp_server_path."""
    try:
        return jsonify(get_path_settings())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/settings/paths", methods=["POST"])
def api_settings_paths_post():
    """Update path settings. Body: docker_container, frontend_path, backend_path, database_path, mcp_server_path (all optional)."""
    data = request.get_json() or {}
    try:
        save_path_settings(
            docker_container=data.get("docker_container"),
            frontend_path=data.get("frontend_path"),
            backend_path=data.get("backend_path"),
            database_path=data.get("database_path"),
            mcp_server_path=data.get("mcp_server_path"),
        )
        return jsonify(get_path_settings())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Allowed sort columns for /api/items (whitelist for SQL safety)
ITEMS_SORT_COLUMNS = {"id", "name", "category", "quantity", "part_number", "location", "manufacturer"}


@app.route("/api/items")
def list_items():
    conn = get_db()
    if not conn:
        return jsonify({"error": "Database not found. Run inventory/scripts/build_db.py first."}), 503
    q = (request.args.get("q") or "").strip()
    category = (request.args.get("category") or "").strip().lower()
    manufacturer = (request.args.get("manufacturer") or "").strip()
    sort = (request.args.get("sort") or "category").strip().lower()
    order = (request.args.get("order") or "asc").strip().lower()
    limit = request.args.get("limit", type=int) or 500
    offset = request.args.get("offset", type=int) or 0

    if sort not in ITEMS_SORT_COLUMNS:
        sort = "category"
    order = "DESC" if order == "desc" else "ASC"

    sql = "SELECT * FROM items WHERE 1=1"
    params = []
    if category:
        sql += " AND category = ?"
        params.append(category)
    if manufacturer:
        sql += " AND manufacturer LIKE ?"
        params.append(f"%{manufacturer}%")
    if q:
        # Search name, part_number, model, notes, tags (stored as JSON array string)
        sql += " AND (name LIKE ? OR part_number LIKE ? OR model LIKE ? OR notes LIKE ? OR tags LIKE ? OR manufacturer LIKE ?)"
        pattern = f"%{q}%"
        params.extend([pattern] * 6)
    sql += f" ORDER BY {sort} {order}, id ASC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    try:
        cur = conn.execute(sql, params)
        rows = cur.fetchall()
        items = [row_to_item(r) for r in rows]
    finally:
        conn.close()

    # Count total (without limit)
    conn = get_db()
    count_sql = "SELECT COUNT(*) FROM items WHERE 1=1"
    count_params = []
    if category:
        count_sql += " AND category = ?"
        count_params.append(category)
    if manufacturer:
        count_sql += " AND manufacturer LIKE ?"
        count_params.append(f"%{manufacturer}%")
    if q:
        count_sql += " AND (name LIKE ? OR part_number LIKE ? OR model LIKE ? OR notes LIKE ? OR tags LIKE ? OR manufacturer LIKE ?)"
        pattern = f"%{q}%"
        count_params.extend([pattern] * 6)
    total = conn.execute(count_sql, count_params).fetchone()[0]
    conn.close()

    return jsonify({"items": items, "total": total})


@app.route("/api/items/manufacturers")
def list_manufacturers():
    """Return distinct manufacturers for filter dropdown."""
    conn = get_db()
    if not conn:
        return jsonify({"manufacturers": []})
    try:
        rows = conn.execute("SELECT DISTINCT manufacturer FROM items WHERE manufacturer IS NOT NULL AND manufacturer != '' ORDER BY manufacturer").fetchall()
        return jsonify({"manufacturers": [r[0] for r in rows]})
    finally:
        conn.close()


@app.route("/api/items/<item_id>")
def get_item(item_id):
    conn = get_db()
    if not conn:
        return jsonify({"error": "Database not found."}), 503
    row = conn.execute("SELECT * FROM items WHERE id = ?", (unquote(item_id),)).fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "Not found"}), 404
    return jsonify(row_to_item(row))


@app.route("/api/items/<item_id>", methods=["PUT"])
def update_item(item_id):
    """Update an inventory item in the database. Body: name, category, quantity, manufacturer, part_number, model, location, notes, datasheet_url, specs?, used_in?, tags?."""
    item_id = unquote(item_id)
    conn = get_db()
    if not conn:
        return jsonify({"error": "Database not found."}), 503
    row = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "Not found"}), 404
    data = request.get_json() or {}
    # Build UPDATE: only allow updating these columns (id is primary key, do not change)
    updates = []
    params = []
    for key in ("name", "category", "manufacturer", "part_number", "model", "location", "notes", "datasheet_url", "datasheet_file"):
        if key in data:
            val = data[key]
            if val is None:
                val = ""
            if isinstance(val, (dict, list)):
                val = json.dumps(val, ensure_ascii=False)
            updates.append(f"{key} = ?")
            params.append(str(val).strip() if val else "")
    if "quantity" in data:
        try:
            qty = int(data["quantity"])
            updates.append("quantity = ?")
            params.append(max(0, qty))
        except (TypeError, ValueError):
            pass
    for key in ("specs", "used_in", "tags"):
        if key in data:
            val = data[key]
            if isinstance(val, str):
                try:
                    json.loads(val)
                except json.JSONDecodeError:
                    val = "[]" if key != "specs" else "{}"
            else:
                val = json.dumps(val, ensure_ascii=False) if val is not None else ("[]" if key != "specs" else "{}")
            updates.append(f"{key} = ?")
            params.append(val)
    if not updates:
        conn.close()
        return jsonify(row_to_item(row))
    params.append(item_id)
    try:
        conn.execute("UPDATE items SET " + ", ".join(updates) + " WHERE id = ?", params)
        conn.commit()
    except Exception as e:
        conn.close()
        return jsonify({"error": str(e)[:200]}), 500
    row = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    conn.close()
    return jsonify(row_to_item(row))


@app.route("/api/categories")
def list_categories():
    conn = get_db()
    if not conn:
        return jsonify({"categories": []})
    rows = conn.execute("SELECT DISTINCT category FROM items ORDER BY category").fetchall()
    conn.close()
    return jsonify({"categories": [r[0] for r in rows]})


def keyword_match_query(conn, query: str, limit: int = 50):
    """Match items by keywords in name, tags, notes, part_number, used_in."""
    tokens = re.findall(r"\w+", query.lower())
    if not tokens:
        return []
    # One (name LIKE ? OR ... ) per token, OR'd together
    one_clause = "(name LIKE ? OR part_number LIKE ? OR model LIKE ? OR notes LIKE ? OR tags LIKE ? OR manufacturer LIKE ?)"
    clause = " OR ".join(one_clause for _ in tokens)
    params = []
    for t in tokens:
        p = f"%{t}%"
        params.extend([p] * 6)
    params.append(limit)
    sql = f"SELECT * FROM items WHERE ({clause}) ORDER BY quantity DESC, name LIMIT ?"
    cur = conn.execute(sql, params)
    return [row_to_item(r) for r in cur.fetchall()]


def _docker_available():
    """Return (ok, message_or_version)."""
    try:
        out = subprocess.run(
            ["docker", "version", "--format", "{{.Server.Version}}"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if out.returncode == 0 and out.stdout.strip():
            return True, out.stdout.strip()
        return False, "Docker not running or not installed"
    except FileNotFoundError:
        return False, "Docker not installed"
    except subprocess.TimeoutExpired:
        return False, "Docker timeout"
    except Exception as e:
        return False, str(e)


def _docker_images():
    """Return list of repo:tag for lab-related images."""
    try:
        out = subprocess.run(
            ["docker", "images", "--format", "{{.Repository}}:{{.Tag}}"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if out.returncode != 0:
            return []
        all_images = [line.strip() for line in out.stdout.strip().splitlines() if line.strip()]
        wanted = {"cyber-lab-mcp", "inventory-app", "app-inventory", "platformio-lab"}
        return [img for img in all_images if img.split(":")[0] in wanted]
    except Exception:
        return []


# Lab-related image/name prefixes for container list (only show these)
_DOCKER_LAB_NAMES = {"app-inventory", "inventory-app", "cyber-lab-mcp", "platformio-lab", "inventory", "mcp", "platformio"}


def _docker_containers():
    """Return list of lab-related containers: id, name, image, state, status."""
    try:
        out = subprocess.run(
            ["docker", "ps", "-a", "--format", "{{.ID}}\t{{.Names}}\t{{.Image}}\t{{.State}}\t{{.Status}}"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if out.returncode != 0:
            return []
        result = []
        for line in out.stdout.strip().splitlines():
            if not line.strip():
                continue
            parts = line.split("\t", 4)
            if len(parts) < 5:
                continue
            cid, names, image, state, status = parts[0], parts[1], parts[2], parts[3], parts[4]
            image_base = image.split(":")[0] if image else ""
            name_lower = (names or "").lower()
            if image_base not in _DOCKER_LAB_NAMES and not any(n in name_lower for n in ("inventory", "cyber-lab", "platformio")):
                continue
            result.append({
                "id": cid,
                "name": names or cid[:12],
                "image": image or "—",
                "state": state,
                "status": status,
            })
        return result
    except Exception:
        return []


def _docker_container_action(container_id: str, action: str):
    """Run docker start/stop/restart on container_id. Returns (success, message)."""
    if action not in ("start", "stop", "restart"):
        return False, "Invalid action"
    if not container_id or not container_id.strip():
        return False, "Container ID required"
    # Sanitize: only allow hex and a-z (container ids and names)
    safe_id = "".join(c for c in container_id.strip() if c.isalnum() or c in "-_")
    if not safe_id:
        return False, "Invalid container ID"
    try:
        out = subprocess.run(
            ["docker", action, safe_id],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if out.returncode == 0:
            return True, f"Container {action} initiated."
        return False, (out.stderr or out.stdout or f"Exit {out.returncode}").strip()[:500]
    except subprocess.TimeoutExpired:
        return False, "Timeout"
    except FileNotFoundError:
        return False, "Docker CLI not available"
    except Exception as e:
        return False, str(e)[:500]


def _docker_status_message(ok, msg):
    """If Docker unavailable and app likely in container, return a clearer message."""
    if ok:
        return msg
    if REPO_ROOT == "/workspace":
        return "Unavailable (app in container; mount host Docker socket to see status)"
    return msg


@app.route("/api/docker/status")
def api_docker_status():
    """Docker daemon status and lab images. Never 500: degrade to docker_available=false on any error."""
    try:
        ok, msg = _docker_available()
        display_msg = _docker_status_message(ok, msg)
        images = _docker_images() if ok else []
        return jsonify({
            "docker_available": ok,
            "docker_message": display_msg,
            "images": images,
        })
    except Exception as e:
        return jsonify({
            "docker_available": False,
            "docker_message": str(e)[:200],
            "images": [],
        })


@app.route("/api/docker/containers")
def api_docker_containers():
    """List lab-related containers (inventory, mcp, platformio). Requires Docker socket access."""
    ok, msg = _docker_available()
    if not ok:
        return jsonify({"error": msg, "containers": []}), 503
    return jsonify({"containers": _docker_containers()})


@app.route("/api/docker/containers/<container_id>/<action>", methods=["POST"])
def api_docker_container_action(container_id, action):
    """Start, stop, or restart a container. Action: start, stop, restart."""
    if action not in ("start", "stop", "restart"):
        return jsonify({"error": "Invalid action"}), 400
    ok, msg = _docker_available()
    if not ok:
        return jsonify({"error": msg}), 503
    success, message = _docker_container_action(container_id, action)
    if success:
        return jsonify({"success": True, "message": message})
    return jsonify({"success": False, "error": message}), 500


@app.route("/api/docker/tools")
def api_docker_tools():
    """Lab tools (Docker images, scripts, docs) and whether they're available."""
    ok, _ = _docker_available()
    images = _docker_images() if ok else []
    image_names = {img.split(":")[0] for img in images}

    tools = [
        {
            "id": "inventory-web",
            "name": "Inventory web app",
            "description": "This UI: search, AI query, updates, Docker status & tools.",
            "type": "app",
            "available": True,
            "command": "python inventory/app/app.py or docker compose -f inventory/app/docker-compose.yml up",
        },
        {
            "id": "mcp-server",
            "name": "MCP server (Cursor)",
            "description": "Project context, roadmap, devices, inventory, firmware index. Stdio transport for Cursor.",
            "type": "docker",
            "available": "cyber-lab-mcp" in image_names,
            "command": "docker run --rm -i -v REPO:/workspace -e CYBER_LAB_REPO_ROOT=/workspace cyber-lab-mcp",
            "build": "docker compose -f mcp-server/docker-compose.yml build",
        },
        {
            "id": "platformio-lab",
            "name": "PlatformIO / build image",
            "description": "ESP32, Arduino, Teensy, ARM. Build firmware in container.",
            "type": "docker",
            "available": "platformio-lab" in image_names,
            "command": "docker run --rm -v REPO:/workspace -w /workspace platformio-lab pio run -e ENV",
            "build": "docker build -t platformio-lab -f docker/Dockerfile .",
        },
        {
            "id": "firmware-updates",
            "name": "Firmware update check",
            "description": "GitHub latest releases for Meshtastic, MeshCore, etc.",
            "type": "api",
            "available": True,
            "command": "GET /api/updates (or ask AI: 'check for updates')",
        },
        {
            "id": "build-db",
            "name": "Inventory DB build",
            "description": "Regenerate inventory.db from YAML catalog.",
            "type": "script",
            "available": True,
            "command": "python inventory/scripts/build_db.py",
        },
    ]
    return jsonify({
        "docker_available": ok,
        "tools": tools,
    })


@app.route("/api/devices/catalog")
def api_devices_catalog():
    """Device wizard catalog: vendors and devices. Optional ?vendor= & ?q= for filter/search."""
    vendor_filter = (request.args.get("vendor") or "").strip().lower()
    q = (request.args.get("q") or "").strip().lower()
    data = load_device_catalog()
    existing = list_devices_in_lab()
    vendors = data.get("vendors") or []
    devices = data.get("devices") or []
    for d in devices:
        d["already_in_lab"] = d.get("id", "") in existing
    if vendor_filter:
        devices = [d for d in devices if (d.get("vendor") or "").lower() == vendor_filter]
    if q:
        devices = [
            d for d in devices
            if q in (d.get("id") or "").lower()
            or q in (d.get("name") or "").lower()
            or q in (d.get("mcu") or "").lower()
            or q in (d.get("description") or "").lower()
        ]
    flasher_base = data.get("flasher_image_base") or "https://flasher.meshtastic.org/img/devices"
    return jsonify({"vendors": vendors, "devices": devices, "existing_ids": list(existing), "flasher_image_base": flasher_base})


@app.route("/api/devices/analyze-datasheet", methods=["POST"])
def api_devices_analyze_datasheet():
    """Upload a datasheet PDF; AI extracts specs and either assigns to existing item or suggests new device. Writes design_context/<id>.md for PCB/3D AI."""
    import tempfile
    from datasheet_ops import (
        extract_text_from_pdf,
        analyze_datasheet_with_ai,
        write_design_context,
        save_datasheet_to_design_context,
    )
    if not get_openai_api_key():
        return jsonify({"error": "OpenAI API key required. Set it in Settings."}), 400
    f = request.files.get("file") or request.files.get("datasheet")
    if not f or not f.filename or not (f.filename.lower().endswith(".pdf") or f.content_type == "application/pdf"):
        return jsonify({"error": "Upload a PDF file (datasheet)"}), 400
    tmp = None
    try:
        fd, tmp = tempfile.mkstemp(suffix=".pdf")
        os.close(fd)
        f.save(tmp)
        text = extract_text_from_pdf(tmp)
        conn = get_db()
        existing_items = []
        if conn:
            try:
                rows = conn.execute("SELECT id, name, category FROM items LIMIT 500").fetchall()
                existing_items = [{"id": r[0], "name": r[1] or "", "category": r[2] or ""} for r in rows]
            finally:
                conn.close()
        client = _openai_client()
        extracted = analyze_datasheet_with_ai(
            text, existing_items, client, model=get_openai_model()
        )
        if extracted.get("error"):
            return jsonify({"error": extracted["error"], "action": "create", "extracted": extracted}), 400
        suggested_id = (extracted.get("suggested_id") or "device").strip() or "device"
        design_context_path = write_design_context(suggested_id, extracted)
        if extracted.get("action") == "assign" and extracted.get("matched_item_id"):
            mid = (extracted["matched_item_id"] or "").strip()
            if mid:
                rel_pdf = save_datasheet_to_design_context(tmp, mid)
                if rel_pdf:
                    conn = get_db()
                    if conn:
                        try:
                            conn.execute(
                                "UPDATE items SET datasheet_file = ? WHERE id = ?",
                                (rel_pdf, mid),
                            )
                            conn.commit()
                        finally:
                            conn.close()
                design_context_path = write_design_context(mid, extracted) or design_context_path
                return jsonify({
                    "success": True,
                    "action": "assign",
                    "item_id": mid,
                    "design_context_path": design_context_path,
                    "datasheet_file": rel_pdf or None,
                    "message": f"Datasheet assigned to item '{mid}'. Design context saved.",
                    "extracted": extracted,
                })
        return jsonify({
            "success": True,
            "action": "create",
            "suggested_id": suggested_id,
            "design_context_path": design_context_path,
            "message": "New device/item suggested. Create device structure or add to inventory.",
            "extracted": extracted,
        })
    except Exception as e:
        return jsonify({"error": str(e)[:300]}), 500
    finally:
        if tmp and os.path.isfile(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass


@app.route("/api/devices/scaffold", methods=["POST"])
def api_devices_scaffold():
    """Create devices/<id>/ and registry entry from wizard. Body: device_id, name, vendor?, mcu?, doc_links?, add_to_inventory?, inventory_category?, install_sdk?."""
    from device_ops import get_catalog_device, install_device_sdk
    body = request.get_json() or {}
    device_id = (body.get("device_id") or "").strip()
    name = (body.get("name") or "").strip()
    vendor = (body.get("vendor") or "").strip()
    mcu = (body.get("mcu") or "").strip()
    doc_links = body.get("doc_links") or {}
    add_to_inventory = bool(body.get("add_to_inventory"))
    inventory_category = (body.get("inventory_category") or "controller").strip().lower()
    install_sdk = body.get("install_sdk", True)  # default True when SDK available
    if not device_id and not name:
        return jsonify({"error": "device_id or name required"}), 400
    if not device_id:
        device_id = name
    success, message, paths = scaffold_device(
        device_id, name, vendor=vendor, mcu=mcu, doc_links=doc_links,
        add_to_inventory=add_to_inventory, inventory_category=inventory_category,
    )
    if not success:
        return jsonify({"success": False, "error": message}), 400
    sdk_message = None
    if install_sdk:
        catalog_entry = get_catalog_device(device_id)
        if catalog_entry and (catalog_entry.get("sdk") or {}).get("available"):
            sdk_ok, sdk_message = install_device_sdk(device_id, catalog_entry=catalog_entry)
            if not sdk_ok and paths:
                paths["sdk_install_error"] = sdk_message
    return jsonify({"success": True, "message": message, "paths": paths, "sdk_message": sdk_message})


@app.route("/api/devices/<device_id>/sdk")
def api_device_sdk(device_id):
    """Return SDK path and metadata for the device so the AI and tools can use the SDK. 404 if no SDK."""
    from device_ops import get_device_sdk_path
    info = get_device_sdk_path(device_id)
    if not info:
        return jsonify({"error": "No SDK for this device"}), 404
    return jsonify(info)


@app.route("/api/devices/<device_id>/structure")
def api_device_structure(device_id):
    """Return folder structure and naming conventions for a device (for agent: where to place docs)."""
    structure = get_device_structure(device_id)
    if structure is None:
        return jsonify({"error": f"Device not found: {device_id}"}), 404
    return jsonify(structure)


@app.route("/api/devices/fetch-doc", methods=["POST"])
def api_devices_fetch_doc():
    """Download a document from URL and save to devices/<device_id>/docs/ with correct naming.
    Body: device_id, url, doc_type (datasheet|schematic|manual|reference|other), optional suggested_filename.
    Agent uses this after finding a URL (e.g. from device-search or its own search)."""
    data = request.get_json() or request.form or {}
    device_id = (data.get("device_id") or "").strip()
    url = (data.get("url") or "").strip()
    doc_type = (data.get("doc_type") or "other").strip().lower()
    suggested_filename = (data.get("suggested_filename") or "").strip() or None
    if not device_id or not url:
        return jsonify({"success": False, "error": "device_id and url required"}), 400
    ok, path_or_err = download_device_doc(device_id, url, doc_type=doc_type, suggested_filename=suggested_filename)
    if ok:
        return jsonify({"success": True, "path": path_or_err})
    return jsonify({"success": False, "error": path_or_err}), 400


@app.route("/api/agent/device-search")
def api_agent_device_search():
    """Search the web for device content (datasheets, schematics). Query: q=, max_results= (default 10).
    Agent can use this then POST to /api/devices/fetch-doc with the chosen URL."""
    q = (request.args.get("q") or "").strip()
    max_results = min(int(request.args.get("max_results") or 10), 20)
    if not q:
        return jsonify({"error": "query q required", "results": []}), 400
    results, err = device_search(q, max_results=max_results)
    if err:
        return jsonify({"results": [], "message": err})
    return jsonify({"results": results})


# --- Device configuration wizard (pre/post flash, internal or Launcher) ---

CONFIG_WIZARD_SYSTEM = (
    "You are an assistant for the device configuration wizard. "
    "The user is configuring a device (Meshtastic, MeshCore, or Launcher firmware) either before or after flashing. "
    "Help with region choice (RF compliance), device name, channel/LoRa settings, and any step-specific questions. "
    "Be concise; suggest values when relevant (e.g. region for their location, safe TX power). "
)

@app.route("/api/config-wizard/context")
def api_config_wizard_context():
    """Context for device config wizard: devices, firmware targets, RF presets."""
    try:
        return jsonify(get_config_wizard_context())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/config-wizard/presets")
def api_config_wizard_presets():
    """List saved config presets for device + firmware. Query: device_id, firmware."""
    device_id = (request.args.get("device_id") or "").strip()
    firmware = (request.args.get("firmware") or "").strip()
    if not device_id or not firmware:
        return jsonify({"presets": [], "error": "device_id and firmware required"})
    presets = list_config_presets(device_id, firmware)
    return jsonify({"presets": presets})


@app.route("/api/config-wizard/presets", methods=["POST"])
def api_config_wizard_save_preset():
    """Save a config preset. Body: device_id, firmware, preset_name, options."""
    data = request.get_json() or request.form or {}
    device_id = (data.get("device_id") or "").strip()
    firmware = (data.get("firmware") or "").strip()
    preset_name = (data.get("preset_name") or data.get("name") or "preset").strip()
    options = data.get("options") or {}
    if not device_id or not firmware:
        return jsonify({"success": False, "error": "device_id and firmware required"}), 400
    ok, path_or_err = save_config_preset(device_id, firmware, preset_name, options)
    if ok:
        return jsonify({"success": True, "path": path_or_err})
    return jsonify({"success": False, "error": path_or_err}), 400


@app.route("/api/config-wizard/presets/<preset_name>")
def api_config_wizard_load_preset(preset_name):
    """Load one preset. Query: device_id, firmware."""
    device_id = (request.args.get("device_id") or "").strip()
    firmware = (request.args.get("firmware") or "").strip()
    if not device_id or not firmware:
        return jsonify({"error": "device_id and firmware required"}), 400
    ok, data_or_err = load_config_preset(device_id, firmware, preset_name)
    if not ok:
        return jsonify({"error": data_or_err}), 404
    return jsonify(data_or_err)


def _device_context_block_for_ai():
    """Build a compact device context block (logs + live status) for injection into AI prompts."""
    try:
        ctx = get_debug_context()
        parts = []
        if ctx.get("serial_active"):
            parts.append("Live status: serial active on " + (ctx.get("serial_port") or ""))
        else:
            parts.append("Live status: serial inactive")
        parts.extend([
            "Ports: " + ctx.get("ports_summary", "unknown"),
            "esptool: " + ("ok" if ctx.get("esptool_ok") else "missing/failed"),
        ])
        if ctx.get("serial_tail"):
            parts.append("Live device log (last 80 lines):\n" + (ctx["serial_tail"][-2500:] or ""))
        if ctx.get("historical_log"):
            parts.append("Historical device log:\n" + (ctx["historical_log"][-3000:] or ""))
        if ctx.get("health_problems"):
            parts.append("Problems: " + ", ".join(ctx["health_problems"]))
        return "\n\n".join(parts)
    except Exception:
        return ""


@app.route("/api/config-wizard/chat", methods=["POST"])
def api_config_wizard_chat():
    """Chat for wizard assist: message + optional step/device/firmware/options for context."""
    data = request.get_json() or {}
    message = (data.get("message") or "").strip()
    step = (data.get("step") or "").strip()
    device_id = (data.get("device_id") or "").strip()
    firmware = (data.get("firmware") or "").strip()
    options = data.get("options") or {}
    if not message:
        return jsonify({"error": "message required"}), 400
    system = CONFIG_WIZARD_SYSTEM
    if step or device_id or firmware or options:
        system += "\n\nCurrent wizard state: step=%s, device_id=%s, firmware=%s. Options so far: %s" % (
            step or "—", device_id or "—", firmware or "—", json.dumps(options)[:500])
    device_block = _device_context_block_for_ai()
    if device_block:
        system += "\n\n--- Device context (connected device logs, historical logs, live status) ---\n" + device_block[:4000]
    messages = [{"role": "system", "content": system}, {"role": "user", "content": message}]
    reply = ""
    if get_openai_api_key():
        try:
            client = _openai_client()
            resp = client.chat.completions.create(
                model=get_openai_model(),
                messages=messages,
                max_tokens=500,
            )
            reply = (resp.choices[0].message.content or "").strip()
        except Exception as e:
            reply = f"(AI error: {e})"
    else:
        reply = "Set an API key in AI settings to use wizard assist."
    return jsonify({"reply": reply})


@app.route("/api/map/regions")
def api_map_regions():
    """List all map regions (continents, countries, states) and map sources for the wizard."""
    try:
        return jsonify(wizard_list_regions())
    except Exception as e:
        return jsonify({"error": str(e), "regions": [], "grouped": {}, "map_sources": []}), 500


@app.route("/api/map/estimate")
def api_map_estimate():
    """Estimate tile count and size for a region and zoom range. Query: region, min_zoom, max_zoom."""
    try:
        region = (request.args.get("region") or "").strip()
        min_zoom = int(request.args.get("min_zoom") or 8)
        max_zoom = int(request.args.get("max_zoom") or 12)
        if not region:
            return jsonify({"error": "region required"}), 400
        result = wizard_estimate(region, min_zoom=min_zoom, max_zoom=max_zoom)
        if result is None:
            return jsonify({"error": f"Unknown region: {region}"}), 404
        return jsonify(result)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/updates")
def api_updates():
    """Return available firmware/OS updates (GitHub latest releases)."""
    try:
        return jsonify({"updates": get_updates()})
    except Exception as e:
        return jsonify({"error": str(e), "updates": []}), 500


def _openai_client():
    """Build OpenAI client from config (key, optional base_url)."""
    import openai
    key = get_openai_api_key()
    base_url = get_openai_base_url()
    if base_url:
        return openai.OpenAI(api_key=key, base_url=base_url)
    return openai.OpenAI(api_key=key)


@app.route("/api/ai/query", methods=["POST"])
def ai_query():
    """Natural language / keyword search. Optional OpenAI if API key set."""
    data = request.get_json() or {}
    query = (data.get("query") or "").strip()
    if not query:
        return jsonify({"error": "query required", "items": []}), 400

    conn = get_db()
    if not conn:
        return jsonify({"error": "Database not found.", "items": []}), 503

    # If user asks about updates, fetch and include in response
    updates_info = None
    if "update" in query.lower():
        try:
            updates_info = get_updates()
        except Exception:
            updates_info = []

    # 1) Keyword match always
    items = keyword_match_query(conn, query, limit=30)
    conn.close()

    # 2) Optional: use OpenAI to re-rank or refine (include updates context if relevant)
    if get_openai_api_key() and (items or updates_info):
        try:
            client = _openai_client()
            parts = []
            if items:
                parts.append("Inventory items:\n" + "\n".join(
                    f"- {it['name']} (id={it['id']}, category={it['category']}, qty={it.get('quantity', 0)})"
                    for it in items[:25]
                ))
            if updates_info:
                parts.append("Firmware updates (latest GitHub release):\n" + "\n".join(
                    f"- {u['name']} ({u['device']}): {u.get('tag') or u.get('error', '?')} — {u.get('url', '')}"
                    for u in updates_info
                ))
            device_block = _device_context_block_for_ai()
            system_content = (
                "You are an inventory and lab assistant. You can answer about hardware inventory, firmware updates, "
                "and connected devices (serial logs, live status). Given items and/or update info and optional device context, "
                "reply with a short helpful answer. If the question is only about updates, summarize the updates. "
                "If the user asks about device logs or status, use the device context (live and historical logs, ports, esptool). "
                "If listing item IDs, end with a line 'IDS: [\"id1\", \"id2\"]'."
            )
            if device_block:
                system_content += "\n\n--- Device context (connected device logs, historical logs, live status) ---\n" + device_block[:4000]
            user_content = "\n\n".join(parts) + f"\n\nUser question: {query}"
            resp = client.chat.completions.create(
                model=get_openai_model(),
                messages=[
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": user_content},
                ],
                max_tokens=400,
            )
            text = resp.choices[0].message.content or ""
            ids_match = re.search(r"IDS:\s*\[([^\]]+)\]", text, re.I)
            if ids_match and items:
                id_list = re.findall(r'"([^"]+)"', ids_match.group(1))
                id_set = set(id_list)
                items = [it for it in items if it["id"] in id_set] + [it for it in items if it["id"] not in id_set]
            ai_answer = text.split("IDS:")[0].strip() if "IDS:" in text else text
        except Exception as e:
            ai_answer = f"(AI unavailable: {e})"
    else:
        ai_answer = None
        if updates_info is not None and "update" in query.lower():
            lines = []
            for u in updates_info:
                if u.get("error"):
                    lines.append(f"{u['name']}: error — {u['error']}")
                else:
                    lines.append(f"{u['name']} ({u['device']}): {u.get('tag', '?')} — {u.get('url', '')}")
            ai_answer = "Firmware updates:\n" + "\n".join(lines) if lines else "No update info available."

    return jsonify({
        "items": items,
        "ai_answer": ai_answer,
        "updates": updates_info,
    })


def _sse_event(data):
    """Encode a dict as a single SSE data line."""
    return "data: " + json.dumps(data, ensure_ascii=False) + "\n\n"


@app.route("/api/ai/query/stream", methods=["POST"])
def ai_query_stream():
    """Stream AI answer as SSE; final event includes items (for IDS re-rank)."""
    data = request.get_json() or {}
    query = (data.get("query") or "").strip()
    if not query:
        return jsonify({"error": "query required"}), 400

    conn = get_db()
    if not conn:
        return jsonify({"error": "Database not found."}), 503

    updates_info = None
    if "update" in query.lower():
        try:
            updates_info = get_updates()
        except Exception:
            updates_info = []

    items = keyword_match_query(conn, query, limit=30)

    def generate():
        if not get_openai_api_key() or not (items or updates_info):
            if updates_info is not None and "update" in query.lower():
                lines = []
                for u in updates_info:
                    if u.get("error"):
                        lines.append(f"{u['name']}: error — {u['error']}")
                    else:
                        lines.append(f"{u['name']} ({u['device']}): {u.get('tag', '?')} — {u.get('url', '')}")
                text = "Firmware updates:\n" + "\n".join(lines) if lines else "No update info available."
            else:
                text = "No matching items or updates to summarize."
            yield _sse_event({"delta": text})
            yield _sse_event({"done": True, "items": items})
            conn.close()
            return

        parts = []
        if items:
            parts.append("Inventory items:\n" + "\n".join(
                f"- {it['name']} (id={it['id']}, category={it['category']}, qty={it.get('quantity', 0)})"
                for it in items[:25]
            ))
        if updates_info:
            parts.append("Firmware updates (latest GitHub release):\n" + "\n".join(
                f"- {u['name']} ({u['device']}): {u.get('tag') or u.get('error', '?')} — {u.get('url', '')}"
                for u in updates_info
            ))
        user_content = "\n\n".join(parts) + f"\n\nUser question: {query}"
        system_content = (
            "You are an inventory and lab assistant. You can answer about hardware inventory, firmware updates, "
            "and connected devices (serial logs, live status). If the user asks about device logs or status, use the device context."
        )
        device_block = _device_context_block_for_ai()
        if device_block:
            system_content += "\n\n--- Device context (connected device logs, historical logs, live status) ---\n" + device_block[:4000]
        full_text = ""
        try:
            client = _openai_client()
            stream = client.chat.completions.create(
                model=get_openai_model(),
                messages=[
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": user_content},
                ],
                max_tokens=400,
                stream=True,
            )
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_text += content
                    yield _sse_event({"delta": content})
        except Exception as e:
            full_text = ""
            yield _sse_event({"delta": f"(AI unavailable: {e})"})

        ids_match = re.search(r"IDS:\s*\[([^\]]+)\]", full_text, re.I)
        if ids_match and items:
            id_list = re.findall(r'"([^"]+)"', ids_match.group(1))
            id_set = set(id_list)
            items = [it for it in items if it["id"] in id_set] + [it for it in items if it["id"] not in id_set]
        conn.close()
        yield _sse_event({"done": True, "items": items})

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _load_setup_context():
    """Load docs/AGENT_SETUP_CONTEXT.md from repo root. Return empty string if missing."""
    path = os.path.join(REPO_ROOT, "docs", "AGENT_SETUP_CONTEXT.md")
    if not os.path.isfile(path):
        return ""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""


SETUP_HELP_SYSTEM_PREFIX = (
    "You are a setup assistant for this lab. Use the following context to answer. "
    "The user can ask for setup recommendations, step-by-step wizard guidance, or explanations of what is acceptable in each area (paths, flash, map tiles, project planning, device registry, Docker). "
    "Be concise and point to the relevant wizard or doc when appropriate.\n\n"
)


@app.route("/api/setup/chat", methods=["POST"])
def api_setup_chat():
    """Chat for setup help: system prompt from AGENT_SETUP_CONTEXT.md, optional history, debug context for problem suggestions."""
    data = request.get_json() or {}
    message = (data.get("message") or "").strip()
    history = data.get("history") or []
    if not message:
        return jsonify({"error": "message required"}), 400

    setup_doc = _load_setup_context()
    system_content = SETUP_HELP_SYSTEM_PREFIX + (setup_doc or "Setup context file (docs/AGENT_SETUP_CONTEXT.md) not found.")

    # Inject device context: connected device logs, historical logs, live status (so AI can suggest fixes)
    try:
        ctx = get_debug_context()
        debug_block = (
            "\n\n--- Device context (connected device logs, historical logs, live status) ---\n"
            f"Live status: Serial monitor {'active on ' + (ctx.get('serial_port') or '') if ctx.get('serial_active') else 'inactive'}. "
            f"Ports: {ctx.get('ports_summary', 'unknown')}. "
            f"esptool: {'ok' if ctx.get('esptool_ok') else 'missing/failed'} ({ctx.get('esptool_message', '')}). "
        )
        if ctx.get("serial_tail"):
            debug_block += f"\nLive device log (last 80 lines):\n{ctx['serial_tail'][-3000:]}\n"
        if ctx.get("historical_log"):
            debug_block += f"\nHistorical device log (last 150 lines from persistent log):\n{ctx['historical_log'][-4000:]}\n"
        if ctx.get("health_problems"):
            debug_block += f"\nDetected problems: {', '.join(ctx['health_problems'])}. "
            if ctx.get("health_suggestions"):
                debug_block += f"Possible fixes: {'; '.join(ctx['health_suggestions'])}. "
            debug_block += "If the user has not asked something specific, briefly suggest what to do about these problems."
        system_content += debug_block
    except Exception:
        pass

    messages = [{"role": "system", "content": system_content}]
    for h in history[-10:]:
        role = (h.get("role") or "user").strip().lower()
        if role not in ("user", "assistant"):
            role = "user"
        content = (h.get("content") or "").strip()
        if content:
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": message})

    reply = ""
    if get_openai_api_key():
        try:
            client = _openai_client()
            resp = client.chat.completions.create(
                model=get_openai_model(),
                messages=messages,
                max_tokens=800,
            )
            reply = (resp.choices[0].message.content or "").strip()
        except Exception as e:
            reply = f"(AI error: {e})"
    else:
        reply = "Set an API key in AI API settings to use setup help."

    # Return problems/suggestions so frontend can show banner and prompt user
    payload = {"reply": reply}
    try:
        ctx = get_debug_context()
        if ctx.get("health_problems"):
            payload["problems"] = ctx["health_problems"]
            payload["suggestions"] = ctx.get("health_suggestions") or []
    except Exception:
        pass
    return jsonify(payload)


# --- Debug: live device logs, maintenance, troubleshooting ---

@app.route("/api/debug/context")
def api_debug_context():
    """Return debug context for AI and UI: serial tail, historical log, ports, esptool, health, live_status."""
    try:
        return jsonify(get_debug_context())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/ai/device-context")
def api_ai_device_context():
    """Return full device context for AI: connected device logs, historical logs, live device status and data.
    Use this so the AI (or MCP / Cursor) can include device logs and status in prompts."""
    try:
        return jsonify(get_debug_context())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/debug/serial", methods=["GET"])
def api_debug_serial():
    """Get current serial monitor buffer and active port."""
    lines, port = serial_get_buffer()
    return jsonify({"lines": lines, "active_port": port, "active": serial_is_active()})


@app.route("/api/debug/serial/start", methods=["POST"])
def api_debug_serial_start():
    """Start serial monitor on given port. Body: { port [, baud ] }."""
    data = request.get_json() or request.form or {}
    port = (data.get("port") or "").strip()
    baud = int(data.get("baud") or 115200)
    ok, msg = serial_start(port, baud)
    if ok:
        return jsonify({"success": True, "message": msg})
    return jsonify({"success": False, "error": msg}), 400


@app.route("/api/debug/serial/stop", methods=["POST"])
def api_debug_serial_stop():
    """Stop serial monitor."""
    serial_stop()
    return jsonify({"success": True})


@app.route("/api/debug/serial/clear", methods=["POST"])
def api_debug_serial_clear():
    """Clear serial buffer (display and AI). Does not stop the monitor."""
    serial_clear_buffer()
    return jsonify({"success": True})


@app.route("/api/debug/tools/health")
def api_debug_tools_health():
    """Run health checks (esptool, ports, chip detect, DB). Returns problems and suggestions."""
    try:
        return jsonify(run_health_checks())
    except Exception as e:
        return jsonify({"checks": [], "problems": [str(e)], "suggestions": []}), 500


@app.route("/api/debug/tools/esptool-version")
def api_debug_tools_esptool():
    """Return esptool version output."""
    ok, msg = run_esptool_version()
    return jsonify({"ok": ok, "message": msg})


# --- Backup / Restore / Flash ---

@app.route("/api/flash/ports")
def api_flash_ports():
    """List serial ports. Query ?detect=1 to auto-detect chip on each port (slower)."""
    try:
        if request.args.get("detect") == "1":
            ports = list_serial_ports_with_detection(timeout_per_port=4)
        else:
            ports = list_serial_ports()
        payload = {"ports": ports}
        # When app runs in Docker, USB/serial is not available (host devices not in container /dev)
        if REPO_ROOT == "/workspace":
            payload["in_container_no_usb"] = True
        return jsonify(payload)
    except Exception as e:
        return jsonify({"error": str(e), "ports": []}), 500


@app.route("/api/flash/devices")
def api_flash_devices():
    """List devices supported for flash/backup (esptool chip, flash_size)."""
    return jsonify({"devices": get_flash_devices()})


@app.route("/api/flash/artifacts")
def api_flash_artifacts():
    """List firmware artifacts and backups (paths for flash/restore).
    Optional ?firmware=meshtastic|meshcore|launcher to filter artifacts by target (internal, launcher-compatible)."""
    from config import FIRMWARE_TARGETS
    firmware = (request.args.get("firmware") or "").strip().lower()
    if firmware and firmware not in FIRMWARE_TARGETS:
        firmware = ""
    try:
        return jsonify({"files": list_artifacts_and_backups(firmware_filter=firmware or None)})
    except Exception as e:
        return jsonify({"error": str(e), "files": []}), 500


@app.route("/api/flash/build-config")
def api_flash_build_config():
    """List device/firmware/envs available for build (from BUILD_CONFIG)."""
    try:
        return jsonify({"builds": get_build_config()})
    except Exception as e:
        return jsonify({"error": str(e), "builds": []}), 500


@app.route("/api/flash/patches")
def api_flash_patches():
    """List available patches for device/firmware. Query: device_id, firmware_id."""
    device_id = (request.args.get("device_id") or "").strip()
    firmware_id = (request.args.get("firmware_id") or "").strip()
    if not device_id or not firmware_id:
        return jsonify({"patches": []})
    try:
        return jsonify({"patches": list_patches(device_id, firmware_id)})
    except Exception as e:
        return jsonify({"error": str(e), "patches": []}), 500


@app.route("/api/flash/build", methods=["POST"])
def api_flash_build():
    """Build firmware. Body: device_id, firmware_id, env_name; optional: patch_paths, clean, verbose, timeout, flash_after, port. Returns { success, path?, flashed?, error? }."""
    data = request.get_json() or request.form or {}
    device_id = (data.get("device_id") or "").strip()
    firmware_id = (data.get("firmware_id") or "").strip()
    env_name = (data.get("env_name") or "").strip()
    patch_paths = data.get("patch_paths")
    if isinstance(patch_paths, str):
        patch_paths = [p.strip() for p in patch_paths.split(",") if p.strip()]
    elif not isinstance(patch_paths, list):
        patch_paths = []
    patch_paths = [p.strip() for p in patch_paths if p and isinstance(p, str)]
    clean = bool(data.get("clean"))
    verbose = bool(data.get("verbose"))
    timeout = int(data.get("timeout") or 300)
    timeout = max(60, min(3600, timeout))
    flash_after = bool(data.get("flash_after"))
    port = (data.get("port") or "").strip()
    flash_device_id = (data.get("flash_device_id") or data.get("device_id") or "").strip()
    if not device_id or not firmware_id:
        return jsonify({"success": False, "error": "device_id and firmware_id required"}), 400
    try:
        ok, path_or_err = build_firmware(
            device_id, firmware_id, env_name,
            patch_paths=patch_paths, timeout=timeout, clean=clean, verbose=verbose,
        )
        if not ok:
            return jsonify({"success": False, "error": path_or_err}), 500
        if flash_after and port and flash_device_id:
            abs_path = os.path.join(REPO_ROOT, path_or_err)
            if not os.path.isfile(abs_path):
                return jsonify({"success": True, "path": path_or_err, "error": "Built but flash file not found"}), 500
            flashed_ok, flash_msg = flash_firmware(port, flash_device_id, abs_path)
            if not flashed_ok:
                return jsonify({"success": True, "path": path_or_err, "flashed": False, "flash_error": flash_msg})
            return jsonify({"success": True, "path": path_or_err, "flashed": True})
        return jsonify({"success": True, "path": path_or_err})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)[:300]}), 500


@app.route("/api/flash/download-release", methods=["POST"])
def api_flash_download_release():
    """Download a .bin from a GitHub release to artifacts. Body: owner, repo, tag?, device_id?, firmware_id?, asset_filter?."""
    data = request.get_json() or request.form or {}
    owner = (data.get("owner") or "").strip()
    repo = (data.get("repo") or "").strip()
    tag = (data.get("tag") or "").strip() or None
    device_id = (data.get("device_id") or "").strip() or None
    firmware_id = (data.get("firmware_id") or "").strip() or None
    asset_filter = (data.get("asset_filter") or "").strip() or None
    if not owner or not repo:
        return jsonify({"success": False, "error": "owner and repo required"}), 400
    try:
        ok, path_or_err = download_release_firmware(
            owner=owner, repo=repo, tag=tag,
            device_id=device_id, firmware_id=firmware_id, asset_filter=asset_filter,
        )
        if ok:
            return jsonify({"success": True, "path": path_or_err})
        return jsonify({"success": False, "error": path_or_err}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)[:300]}), 500


def _flash_error_message(raw: str) -> str:
    """Strip ANSI codes and return a clear message for common errors (e.g. port busy, timeout)."""
    if not raw:
        return "Unknown error"
    s = re.sub(r"\x1b\[[0-9;]*m", "", raw)
    s = s.replace("\r", " ").replace("\n", " ").strip()
    if "port is busy" in s.lower() or "resource temporarily unavailable" in s.lower() or "could not exclusively lock" in s.lower():
        return "Port is busy or in use. Close Serial Monitor (Debug tab) and any other app using the port, then try again."
    if "could not open" in s.lower() and ("port" in s.lower() or "doesn't exist" in s.lower()):
        return "Could not open port. Close Serial Monitor and other apps using it, then try again."
    if s.strip().lower() == "timeout":
        return "Backup timed out. Full flash can take 10+ minutes; try again or use a smaller backup (e.g. App partition only)."
    return s[:400] if len(s) > 400 else s


@app.route("/api/flash/backup", methods=["POST"])
def api_flash_backup():
    """Backup device flash (full, app, or nvs). Returns .bin file download."""
    data = request.get_json() or request.form or {}
    port = (data.get("port") or request.form.get("port") or "").strip()
    device_id = (data.get("device_id") or request.form.get("device_id") or "").strip()
    backup_type = (data.get("backup_type") or request.form.get("backup_type") or "full").strip().lower()
    if not port or not device_id:
        return jsonify({"error": "port and device_id required"}), 400
    ok, path_or_err, _ = backup_flash(port, device_id, backup_type)
    if not ok:
        return jsonify({"error": _flash_error_message(path_or_err)}), 500
    if not os.path.isfile(path_or_err):
        return jsonify({"error": "Backup file not created"}), 500
    return send_file(
        path_or_err,
        as_attachment=True,
        download_name=os.path.basename(path_or_err),
        mimetype="application/octet-stream",
    )


@app.route("/api/flash/restore", methods=["POST"])
def api_flash_restore():
    """Restore flash from uploaded .bin file or from path (artifacts/backups)."""
    port = (request.form.get("port") or "").strip()
    device_id = (request.form.get("device_id") or "").strip()
    path_arg = (request.form.get("path") or "").strip()
    if not port or not device_id:
        return jsonify({"error": "port and device_id required"}), 400
    bin_path = None
    used_temp = False
    if path_arg:
        bin_path = os.path.join(REPO_ROOT, path_arg.lstrip("/"))
        if not os.path.isfile(bin_path):
            return jsonify({"error": f"File not found: {path_arg}"}), 400
    elif "file" in request.files:
        f = request.files["file"]
        if f.filename and f.filename.endswith(".bin"):
            fd, bin_path = tempfile.mkstemp(suffix=".bin")
            os.close(fd)
            f.save(bin_path)
            used_temp = True
        else:
            return jsonify({"error": "Upload a .bin file"}), 400
    else:
        return jsonify({"error": "Provide path or upload file"}), 400
    try:
        ok, msg = restore_flash(port, device_id, bin_path)
        if ok:
            return jsonify({"success": True, "message": msg or "Restore complete"})
        return jsonify({"success": False, "error": _flash_error_message(msg)}), 500
    finally:
        if used_temp and bin_path and os.path.isfile(bin_path):
            try:
                os.remove(bin_path)
            except OSError:
                pass


def _flash_addr_from_path(path_arg: str) -> str:
    """Infer write address from path so UI matches scripts/flash.sh behavior.
    firmware.factory.bin / *merged*.bin / backups → 0x0; app-only firmware.bin in artifacts → 0x10000."""
    if not path_arg:
        return "0x0"
    p = path_arg.lower()
    base = os.path.basename(p)
    if "firmware.factory.bin" in p or "merged" in base or "backup_" in p:
        return "0x0"
    if base == "firmware.bin" and ("artifacts" in p or "artifact" in p):
        return "0x10000"  # app partition only; full image would be firmware.factory.bin
    return "0x0"


@app.route("/api/flash/flash", methods=["POST"])
def api_flash_flash():
    """Flash firmware from path (artifacts/backups) or uploaded .bin."""
    port = (request.form.get("port") or "").strip()
    device_id = (request.form.get("device_id") or "").strip()
    path_arg = (request.form.get("path") or "").strip()
    addr = (request.form.get("addr") or "").strip()
    if not addr and path_arg:
        addr = _flash_addr_from_path(path_arg)
    if not addr:
        addr = "0x0"
    if not port or not device_id:
        return jsonify({"error": "port and device_id required"}), 400
    bin_path = None
    used_temp = False
    if path_arg:
        bin_path = os.path.join(REPO_ROOT, path_arg.lstrip("/"))
        if not os.path.isfile(bin_path):
            return jsonify({"error": f"File not found: {path_arg}"}), 400
    elif "file" in request.files:
        f = request.files["file"]
        if f.filename and f.filename.endswith(".bin"):
            fd, bin_path = tempfile.mkstemp(suffix=".bin")
            os.close(fd)
            f.save(bin_path)
            used_temp = True
        else:
            return jsonify({"error": "Upload a .bin file"}), 400
    else:
        return jsonify({"error": "Provide path or upload file"}), 400
    try:
        ok, msg = flash_firmware(port, device_id, bin_path, addr)
        if ok:
            return jsonify({"success": True, "message": msg or "Flash complete"})
        return jsonify({"success": False, "error": _flash_error_message(msg)}), 500
    finally:
        if used_temp and bin_path and os.path.isfile(bin_path):
            try:
                os.remove(bin_path)
            except OSError:
                pass


# --- Project planning ---

@app.route("/api/projects/templates")
def api_projects_templates():
    """List project templates, optionally filtered by controller. Returns inventory_controller_ids when no filter."""
    controller = (request.args.get("controller") or "").strip()
    try:
        out = get_templates(controller or None)
        if not controller:
            conn = get_db()
            out["inventory_controller_ids"] = get_controllers_in_inventory(conn) if conn else []
        return jsonify(out)
    except Exception as e:
        return jsonify({"error": str(e), "controllers": [], "templates": [], "inventory_controller_ids": []}), 500


@app.route("/api/projects", methods=["GET"])
def api_projects_list():
    """List saved project proposals (id, title, updated_at)."""
    try:
        return jsonify({"projects": list_proposals()})
    except Exception as e:
        return jsonify({"error": str(e), "projects": []}), 500


@app.route("/api/projects", methods=["POST"])
def api_projects_create():
    """Create a new project proposal. Body: title, description?, parts_bom?, conversation_summary?."""
    data = request.get_json() or {}
    if not (data.get("title") or "").strip():
        return jsonify({"error": "title required"}), 400
    data.setdefault("parts_bom", [])
    data.setdefault("conversation", [])
    try:
        pid = save_proposal(data)
        return jsonify({"id": pid, "project": load_proposal(pid)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/projects/<proposal_id>", methods=["GET"])
def api_projects_get(proposal_id):
    """Load one project proposal."""
    proj = load_proposal(proposal_id)
    if proj is None:
        return jsonify({"error": "Not found"}), 404
    return jsonify(proj)


@app.route("/api/projects/<proposal_id>", methods=["PUT"])
def api_projects_update(proposal_id):
    """Update project proposal. Body: full or partial (title, description, parts_bom, conversation)."""
    existing = load_proposal(proposal_id)
    if existing is None:
        return jsonify({"error": "Not found"}), 404
    data = request.get_json() or {}
    for key in ("title", "description", "idea_summary", "parts_bom", "conversation", "conversation_summary",
                "pin_outs", "wiring", "schematic", "enclosure", "controller"):
        if key in data:
            existing[key] = data[key]
    existing["id"] = proposal_id
    try:
        save_proposal(existing)
        return jsonify(load_proposal(proposal_id))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def _parse_bom_from_ai_text(text):
    """Extract BOM JSON array from AI reply. Looks for BOM: [...] or ```json [...] ```."""
    if not text:
        return []
    # Find "BOM:" then extract balanced [...] (handles nested braces)
    idx = text.upper().find("BOM:")
    if idx >= 0:
        start = text.find("[", idx)
        if start >= 0:
            depth = 1
            i = start + 1
            while i < len(text) and depth > 0:
                c = text[i]
                if c == "[" or c == "{":
                    depth += 1
                elif c == "]" or c == "}":
                    depth -= 1
                elif c == '"' and depth > 0:
                    # Skip string contents
                    i += 1
                    while i < len(text) and (text[i] != '"' or text[i - 1] == "\\"):
                        i += 1
                i += 1
            if depth == 0:
                try:
                    return json.loads(text[start : i])
                except json.JSONDecodeError:
                    pass
    # Fallback: ```json [...] ```
    m = re.search(r"```(?:json)?\s*(\[[\s\S]*?\])\s*```", text)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    return []


def _parse_design_from_ai_text(text):
    """Extract hardware design from AI reply: pin_outs, wiring, schematic, enclosure.
    Looks for DESIGN: { ... } JSON, or PINOUTS:/WIRING:/SCHEMATIC:/ENCLOSURE: sections."""
    out = {"pin_outs": [], "wiring": [], "schematic": "", "enclosure": ""}
    if not text:
        return out
    # Try DESIGN: { ... } single JSON object
    idx = text.upper().find("DESIGN:")
    if idx >= 0:
        start = text.find("{", idx)
        if start >= 0:
            depth = 1
            i = start + 1
            while i < len(text) and depth > 0:
                c = text[i]
                if c == "[" or c == "{":
                    depth += 1
                elif c == "]" or c == "}":
                    depth -= 1
                elif c == '"' and depth > 0:
                    i += 1
                    while i < len(text) and (text[i] != '"' or text[i - 1] == "\\"):
                        i += 1
                i += 1
            if depth == 0:
                try:
                    obj = json.loads(text[start:i])
                    out["pin_outs"] = obj.get("pin_outs") if isinstance(obj.get("pin_outs"), list) else out["pin_outs"]
                    out["wiring"] = obj.get("wiring") if isinstance(obj.get("wiring"), list) else out["wiring"]
                    if isinstance(obj.get("schematic"), str):
                        out["schematic"] = obj["schematic"].strip()
                    if isinstance(obj.get("enclosure"), str):
                        out["enclosure"] = obj["enclosure"].strip()
                    return out
                except json.JSONDecodeError:
                    pass
    # Section markers (optional fallback)
    for marker, key in [("PINOUTS:", "pin_outs"), ("WIRING:", "wiring")]:
        i = text.upper().find(marker)
        if i >= 0:
            start = text.find("[", i)
            if start >= 0:
                depth = 1
                j = start + 1
                while j < len(text) and depth > 0:
                    c = text[j]
                    if c in "[{": depth += 1
                    elif c in "]}": depth -= 1
                    j += 1
                if depth == 0:
                    try:
                        out[key] = json.loads(text[start:j])
                    except json.JSONDecodeError:
                        pass
    for marker, key in [("SCHEMATIC:", "schematic"), ("ENCLOSURE:", "enclosure")]:
        i = text.upper().find(marker)
        if i >= 0:
            end = len(text)
            for other in ["DESIGN:", "BOM:", "PINOUTS:", "WIRING:", "SCHEMATIC:", "ENCLOSURE:"]:
                if other == marker:
                    continue
                j = text.upper().find(other, i + len(marker))
                if 0 <= j < end:
                    end = j
            out[key] = text[i + len(marker):end].strip()
    return out


@app.route("/api/projects/ai", methods=["POST"])
def api_projects_ai():
    """Chat for project planning: develop idea with AI, get suggested BOM checked against inventory."""
    data = request.get_json() or {}
    message = (data.get("message") or "").strip()
    project_id = (data.get("project_id") or "").strip()
    if not message:
        return jsonify({"error": "message required"}), 400

    conn = get_db()
    inventory_summary = ""
    if conn:
        try:
            cur = conn.execute(
                "SELECT id, name, part_number, category, quantity FROM items ORDER BY category, name LIMIT 500"
            )
            rows = cur.fetchall()
            inventory_summary = "\n".join(
                f"- {r[1]} (id={r[0]}, part_number={r[2] or '—'}, category={r[3]}, qty={r[4]})"
                for r in rows
            )
        except Exception:
            pass
        if not inventory_summary:
            inventory_summary = "No inventory items loaded."
    else:
        inventory_summary = "Inventory database not available."

    project_context = ""
    existing_bom = []
    if project_id:
        proj = load_proposal(project_id)
        if proj:
            project_context = f"Project: {proj.get('title') or 'Untitled'}. {proj.get('description') or ''}"
            conv = proj.get("conversation") or []
            if conv:
                project_context += "\nPrevious conversation:\n" + "\n".join(
                    f"{c.get('role', 'user')}: {c.get('content', '')[:200]}"
                    for c in conv[-8:]
                )
            existing_bom = proj.get("parts_bom") or []

    system = PROJECT_PLANNING_SYSTEM
    user_content = f"Inventory (id, name, part_number, category, qty):\n{inventory_summary}\n\n"
    if project_context:
        user_content += f"{project_context}\n\n"
    if existing_bom:
        user_content += f"Current BOM: {json.dumps(existing_bom)}\n\n"
    user_content += f"User: {message}"

    reply_text = ""
    suggested_bom = []
    suggested_design = {"pin_outs": [], "wiring": [], "schematic": "", "enclosure": ""}

    if get_openai_api_key():
        try:
            client = _openai_client()
            resp = client.chat.completions.create(
                model=get_openai_model(),
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_content},
                ],
                max_tokens=1200,
            )
            reply_text = (resp.choices[0].message.content or "").strip()
            suggested_bom = _parse_bom_from_ai_text(reply_text)
            suggested_design = _parse_design_from_ai_text(reply_text)
        except Exception as e:
            reply_text = f"(AI error: {e})"
    else:
        reply_text = "Set an API key in AI API settings to use project planning with AI."

    # Check suggested BOM against inventory
    bom_with_stock = []
    if suggested_bom and conn:
        try:
            bom_with_stock = check_bom_against_inventory(conn, suggested_bom)
        except Exception:
            bom_with_stock = [{"name": r.get("name"), "part_number": r.get("part_number"), "quantity": r.get("quantity", 0), "in_stock": None, "qty_on_hand": None, "shortfall": None} for r in suggested_bom]
    elif suggested_bom:
        bom_with_stock = [{"name": r.get("name"), "part_number": r.get("part_number"), "quantity": r.get("quantity", 0), "in_stock": None, "qty_on_hand": None, "shortfall": None} for r in suggested_bom]

    if conn:
        conn.close()

    return jsonify({
        "reply": reply_text,
        "suggested_bom": bom_with_stock,
        "suggested_design": suggested_design,
        "project_id": project_id or None,
    })


@app.route("/api/projects/ai/stream", methods=["POST"])
def api_projects_ai_stream():
    """Stream project planning AI reply as SSE; final event includes suggested_bom."""
    data = request.get_json() or {}
    message = (data.get("message") or "").strip()
    project_id = (data.get("project_id") or "").strip()
    if not message:
        return jsonify({"error": "message required"}), 400

    conn = get_db()
    inventory_summary = ""
    if conn:
        try:
            cur = conn.execute(
                "SELECT id, name, part_number, category, quantity FROM items ORDER BY category, name LIMIT 500"
            )
            rows = cur.fetchall()
            inventory_summary = "\n".join(
                f"- {r[1]} (id={r[0]}, part_number={r[2] or '—'}, category={r[3]}, qty={r[4]})"
                for r in rows
            )
        except Exception:
            pass
        if not inventory_summary:
            inventory_summary = "No inventory items loaded."
    else:
        inventory_summary = "Inventory database not available."

    project_context = ""
    existing_bom = []
    if project_id:
        proj = load_proposal(project_id)
        if proj:
            project_context = f"Project: {proj.get('title') or 'Untitled'}. {proj.get('description') or ''}"
            conv = proj.get("conversation") or []
            if conv:
                project_context += "\nPrevious conversation:\n" + "\n".join(
                    f"{c.get('role', 'user')}: {c.get('content', '')[:200]}"
                    for c in conv[-8:]
                )
            existing_bom = proj.get("parts_bom") or []

    system = PROJECT_PLANNING_SYSTEM
    user_content = f"Inventory (id, name, part_number, category, qty):\n{inventory_summary}\n\n"
    if project_context:
        user_content += f"{project_context}\n\n"
    if existing_bom:
        user_content += f"Current BOM: {json.dumps(existing_bom)}\n\n"
    user_content += f"User: {message}"

    def generate():
        reply_text = ""
        if not get_openai_api_key():
            yield _sse_event({"delta": "Set an API key in AI API settings to use project planning with AI."})
            yield _sse_event({"done": True, "suggested_bom": [], "suggested_design": {"pin_outs": [], "wiring": [], "schematic": "", "enclosure": ""}})
            return
        try:
            client = _openai_client()
            stream = client.chat.completions.create(
                model=get_openai_model(),
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_content},
                ],
                max_tokens=1200,
                stream=True,
            )
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    reply_text += content
                    yield _sse_event({"delta": content})
        except Exception as e:
            reply_text = ""
            yield _sse_event({"delta": f"(AI error: {e})"})

        suggested_bom = _parse_bom_from_ai_text(reply_text)
        suggested_design = _parse_design_from_ai_text(reply_text)
        bom_with_stock = []
        if suggested_bom and conn:
            try:
                bom_with_stock = check_bom_against_inventory(conn, suggested_bom)
            except Exception:
                bom_with_stock = [{"name": r.get("name"), "part_number": r.get("part_number"), "quantity": r.get("quantity", 0), "in_stock": None, "qty_on_hand": None, "shortfall": None} for r in suggested_bom]
        elif suggested_bom:
            bom_with_stock = [{"name": r.get("name"), "part_number": r.get("part_number"), "quantity": r.get("quantity", 0), "in_stock": None, "qty_on_hand": None, "shortfall": None} for r in suggested_bom]
        if conn:
            conn.close()
        yield _sse_event({"done": True, "suggested_bom": bom_with_stock, "suggested_design": suggested_design})

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.route("/api/projects/<proposal_id>/bom/items", methods=["POST"])
def api_projects_bom_add_item(proposal_id):
    """Add an inventory item to this project's BOM. Body: { item_id, quantity? }."""
    proj = load_proposal(proposal_id)
    if proj is None:
        return jsonify({"error": "Project not found"}), 404
    data = request.get_json() or {}
    item_id = (data.get("item_id") or "").strip()
    if not item_id:
        return jsonify({"error": "item_id required"}), 400
    conn = get_db()
    if not conn:
        return jsonify({"error": "Database not found"}), 503
    row = conn.execute("SELECT id, name, part_number, quantity FROM items WHERE id = ?", (unquote(item_id),)).fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "Inventory item not found"}), 404
    qty = int(data.get("quantity") or row[3] or 1)
    if qty < 1:
        qty = 1
    bom = proj.get("parts_bom") or []
    entry = {"name": row[1], "part_number": row[2] or "", "quantity": qty}
    if entry.get("part_number") == "":
        del entry["part_number"]
    bom.append(entry)
    proj["parts_bom"] = bom
    try:
        save_proposal(proj)
        return jsonify(load_proposal(proposal_id))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/projects/<proposal_id>/bom/items/<int:index>", methods=["DELETE"])
def api_projects_bom_remove_item(proposal_id, index):
    """Remove BOM row at index (0-based)."""
    proj = load_proposal(proposal_id)
    if proj is None:
        return jsonify({"error": "Project not found"}), 404
    bom = proj.get("parts_bom") or []
    if index < 0 or index >= len(bom):
        return jsonify({"error": "Invalid BOM index"}), 400
    bom.pop(index)
    proj["parts_bom"] = bom
    try:
        save_proposal(proj)
        return jsonify(load_proposal(proposal_id))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/inventory/from-bom", methods=["POST"])
def api_inventory_from_bom():
    """Add a project BOM row to inventory YAML. Body: { project_id, bom_index, category? }."""
    data = request.get_json() or {}
    project_id = (data.get("project_id") or "").strip()
    bom_index = data.get("bom_index")
    category = (data.get("category") or "component").strip().lower()
    if not project_id:
        return jsonify({"error": "project_id required"}), 400
    if bom_index is None or not isinstance(bom_index, int):
        return jsonify({"error": "bom_index (integer) required"}), 400
    proj = load_proposal(project_id)
    if proj is None:
        return jsonify({"error": "Project not found"}), 404
    bom = proj.get("parts_bom") or []
    if bom_index < 0 or bom_index >= len(bom):
        return jsonify({"error": "Invalid bom_index"}), 400
    row = bom[bom_index]
    name = (row.get("name") or "").strip() or "Part"
    part_number = (row.get("part_number") or "").strip() or None
    quantity = int(row.get("quantity") or 1)
    ok, msg = add_bom_row_to_inventory(name=name, part_number=part_number, quantity=quantity, category=category)
    if not ok:
        return jsonify({"error": msg}), 400
    return jsonify({"ok": True, "message": msg})


@app.route("/api/projects/<proposal_id>/check-inventory", methods=["GET"])
def api_projects_check_inventory(proposal_id):
    """Check project's parts_bom against inventory; return rows with in_stock, qty_on_hand, shortfall."""
    proj = load_proposal(proposal_id)
    if proj is None:
        return jsonify({"error": "Not found"}), 404
    bom = proj.get("parts_bom") or []
    conn = get_db()
    if not conn:
        return jsonify({"bom": [], "error": "Database not available"})
    try:
        rows = check_bom_against_inventory(conn, bom)
        return jsonify({"bom": rows})
    finally:
        conn.close()


@app.route("/api/projects/<proposal_id>/bom/digikey", methods=["GET"])
def api_projects_bom_digikey(proposal_id):
    """Download BOM as CSV for Digi-Key (Manufacturer Part Number, Quantity, Description)."""
    proj = load_proposal(proposal_id)
    if proj is None:
        return jsonify({"error": "Not found"}), 404
    bom = proj.get("parts_bom") or []
    csv_content = bom_csv_digikey(bom)
    from io import BytesIO
    buf = BytesIO(csv_content.encode("utf-8"))
    return send_file(
        buf,
        mimetype="text/csv",
        as_attachment=True,
        download_name=f"bom_digikey_{proposal_id}.csv",
    )


@app.route("/api/projects/<proposal_id>/bom/mouser", methods=["GET"])
def api_projects_bom_mouser(proposal_id):
    """Download BOM as CSV for Mouser (Manufacturer Part Number, Quantity, Description)."""
    proj = load_proposal(proposal_id)
    if proj is None:
        return jsonify({"error": "Not found"}), 404
    bom = proj.get("parts_bom") or []
    csv_content = bom_csv_mouser(bom)
    from io import BytesIO
    buf = BytesIO(csv_content.encode("utf-8"))
    return send_file(
        buf,
        mimetype="text/csv",
        as_attachment=True,
        download_name=f"bom_mouser_{proposal_id}.csv",
    )


def _pinout_csv(rows):
    """CSV for pin assignments: Pin, Function, Notes."""
    lines = ["Pin,Function,Notes"]
    for r in rows or []:
        pin = (r.get("pin") or "").replace('"', '""')
        fn = (r.get("function") or "").replace('"', '""')
        notes = (r.get("notes") or "").replace('"', '""')
        lines.append(f'"{pin}","{fn}","{notes}"')
    return "\n".join(lines)


def _wiring_csv(rows):
    """CSV for wiring/netlist: From, To, Net."""
    lines = ["From,To,Net"]
    for r in rows or []:
        fr = (r.get("from") or "").replace('"', '""')
        to = (r.get("to") or "").replace('"', '""')
        net = (r.get("net") or "").replace('"', '""')
        lines.append(f'"{fr}","{to}","{net}"')
    return "\n".join(lines)


@app.route("/api/projects/<proposal_id>/export/pinout", methods=["GET"])
def api_projects_export_pinout(proposal_id):
    """Download pin assignments as CSV for PCB/CAD use."""
    proj = load_proposal(proposal_id)
    if proj is None:
        return jsonify({"error": "Not found"}), 404
    rows = proj.get("pin_outs") or []
    from io import BytesIO
    buf = BytesIO(_pinout_csv(rows).encode("utf-8"))
    return send_file(buf, mimetype="text/csv", as_attachment=True, download_name=f"pinout_{proposal_id}.csv")


@app.route("/api/projects/<proposal_id>/export/wiring", methods=["GET"])
def api_projects_export_wiring(proposal_id):
    """Download wiring/netlist as CSV for schematic/PCB tools."""
    proj = load_proposal(proposal_id)
    if proj is None:
        return jsonify({"error": "Not found"}), 404
    rows = proj.get("wiring") or []
    from io import BytesIO
    buf = BytesIO(_wiring_csv(rows).encode("utf-8"))
    return send_file(buf, mimetype="text/csv", as_attachment=True, download_name=f"wiring_{proposal_id}.csv")


@app.route("/api/projects/<proposal_id>/export/schematic", methods=["GET"])
def api_projects_export_schematic(proposal_id):
    """Download schematic notes as markdown."""
    proj = load_proposal(proposal_id)
    if proj is None:
        return jsonify({"error": "Not found"}), 404
    text = proj.get("schematic") or "# Schematic\n\n(No schematic notes yet.)"
    from io import BytesIO
    buf = BytesIO(text.encode("utf-8"))
    return send_file(buf, mimetype="text/markdown", as_attachment=True, download_name=f"schematic_{proposal_id}.md")


@app.route("/api/projects/<proposal_id>/export/enclosure", methods=["GET"])
def api_projects_export_enclosure(proposal_id):
    """Download enclosure/CAD notes as markdown for 3D printing or mechanical design."""
    proj = load_proposal(proposal_id)
    if proj is None:
        return jsonify({"error": "Not found"}), 404
    text = proj.get("enclosure") or "# Enclosure\n\n(No enclosure notes yet.)"
    from io import BytesIO
    buf = BytesIO(text.encode("utf-8"))
    return send_file(buf, mimetype="text/markdown", as_attachment=True, download_name=f"enclosure_{proposal_id}.md")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    debug = os.environ.get("FLASK_DEBUG", "").lower() in ("1", "true", "yes")
    print(f"Using DB: {get_database_path()}")
    print(f"Open http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=debug)
