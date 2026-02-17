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
    flash_firmware,
    get_flash_devices,
    list_artifacts_and_backups,
    list_serial_ports,
    list_serial_ports_with_detection,
    restore_flash,
)
from project_ops import (
    bom_csv_digikey,
    bom_csv_mouser,
    check_bom_against_inventory,
    list_proposals,
    load_proposal,
    save_proposal,
)

PROJECT_PLANNING_SYSTEM = (
    "You are a project planning assistant for electronics/hardware projects. "
    "The user has an inventory list below; use it to suggest parts they might already have or need to buy. "
    "Help them develop their idea into a concrete plan. "
    "When you suggest specific parts, end your reply with a line starting exactly with 'BOM:' followed by a JSON array of objects, each with keys: name (string), part_number (string, optional), quantity (integer). "
    "Example: BOM: [{\"name\": \"ESP32 DevKit C\", \"part_number\": \"\", \"quantity\": 2}, {\"name\": \"10k resistor\", \"part_number\": \"\", \"quantity\": 10}] "
    "When the project involves a circuit or PCB, also output a DESIGN block for pinouts, wiring, schematic, and enclosure. "
    "Use exactly: DESIGN: then a single JSON object with keys: pin_outs (array of {pin, function, notes}), wiring (array of {from, to, net}), schematic (string: markdown description or block diagram notes for a schematic), enclosure (string: markdown notes for 3D-printed enclosure, dimensions and mounting). "
    "Example: DESIGN: {\"pin_outs\": [{\"pin\": \"GPIO21\", \"function\": \"I2C SDA\", \"notes\": \"\"}], \"wiring\": [{\"from\": \"ESP32.GPIO21\", \"to\": \"OLED.SDA\", \"net\": \"I2C_SDA\"}], \"schematic\": \"ESP32 I2C to OLED...\", \"enclosure\": \"Box 80x60x30mm, cutouts for USB and display.\"}"
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


@app.route("/api/items")
def list_items():
    conn = get_db()
    if not conn:
        return jsonify({"error": "Database not found. Run inventory/scripts/build_db.py first."}), 503
    q = (request.args.get("q") or "").strip()
    category = (request.args.get("category") or "").strip().lower()
    limit = request.args.get("limit", type=int) or 500
    offset = request.args.get("offset", type=int) or 0

    sql = "SELECT * FROM items WHERE 1=1"
    params = []
    if category:
        sql += " AND category = ?"
        params.append(category)
    if q:
        # Search name, part_number, model, notes, tags (stored as JSON array string)
        sql += " AND (name LIKE ? OR part_number LIKE ? OR model LIKE ? OR notes LIKE ? OR tags LIKE ? OR manufacturer LIKE ?)"
        pattern = f"%{q}%"
        params.extend([pattern] * 6)
    sql += " ORDER BY category, name LIMIT ? OFFSET ?"
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
    if q:
        count_sql += " AND (name LIKE ? OR part_number LIKE ? OR model LIKE ? OR notes LIKE ? OR tags LIKE ? OR manufacturer LIKE ?)"
        pattern = f"%{q}%"
        count_params.extend([pattern] * 6)
    total = conn.execute(count_sql, count_params).fetchone()[0]
    conn.close()

    return jsonify({"items": items, "total": total})


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
        wanted = {"esp32-lab-mcp", "inventory-app", "app-inventory", "platformio-lab"}
        return [img for img in all_images if img.split(":")[0] in wanted]
    except Exception:
        return []


# Lab-related image/name prefixes for container list (only show these)
_DOCKER_LAB_NAMES = {"app-inventory", "inventory-app", "esp32-lab-mcp", "platformio-lab", "inventory", "mcp", "platformio"}


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
            if image_base not in _DOCKER_LAB_NAMES and not any(n in name_lower for n in ("inventory", "esp32-lab", "platformio")):
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
            "available": "esp32-lab-mcp" in image_names,
            "command": "docker run --rm -i -v REPO:/workspace -e ESP32_LAB_REPO_ROOT=/workspace esp32-lab-mcp",
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
            user_content = "\n\n".join(parts) + f"\n\nUser question: {query}"
            resp = client.chat.completions.create(
                model=get_openai_model(),
                messages=[
                    {"role": "system", "content": "You are an inventory and lab assistant. You can answer about hardware inventory and firmware updates. Given items and/or update info and a user question, reply with a short helpful answer. If the question is only about updates, summarize the updates. If listing item IDs, end with a line 'IDS: [\"id1\", \"id2\"]'."},
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
        full_text = ""
        try:
            client = _openai_client()
            stream = client.chat.completions.create(
                model=get_openai_model(),
                messages=[
                    {"role": "system", "content": "You are an inventory and lab assistant. You can answer about hardware inventory and firmware updates. Given items and/or update info and a user question, reply with a short helpful answer. If the question is only about updates, summarize the updates. If listing item IDs, end with a line 'IDS: [\"id1\", \"id2\"]'."},
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


# --- Backup / Restore / Flash ---

@app.route("/api/flash/ports")
def api_flash_ports():
    """List serial ports. Query ?detect=1 to auto-detect chip on each port (slower)."""
    try:
        if request.args.get("detect") == "1":
            ports = list_serial_ports_with_detection(timeout_per_port=4)
        else:
            ports = list_serial_ports()
        return jsonify({"ports": ports})
    except Exception as e:
        return jsonify({"error": str(e), "ports": []}), 500


@app.route("/api/flash/devices")
def api_flash_devices():
    """List devices supported for flash/backup (esptool chip, flash_size)."""
    return jsonify({"devices": get_flash_devices()})


@app.route("/api/flash/artifacts")
def api_flash_artifacts():
    """List firmware artifacts and backups (paths for flash/restore)."""
    try:
        return jsonify({"files": list_artifacts_and_backups()})
    except Exception as e:
        return jsonify({"error": str(e), "files": []}), 500


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
        return jsonify({"error": path_or_err}), 500
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
        return jsonify({"success": False, "error": msg}), 500
    finally:
        if used_temp and bin_path and os.path.isfile(bin_path):
            try:
                os.remove(bin_path)
            except OSError:
                pass


@app.route("/api/flash/flash", methods=["POST"])
def api_flash_flash():
    """Flash firmware from path (artifacts/backups) or uploaded .bin."""
    port = (request.form.get("port") or "").strip()
    device_id = (request.form.get("device_id") or "").strip()
    path_arg = (request.form.get("path") or "").strip()
    addr = (request.form.get("addr") or "0x0").strip()
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
        return jsonify({"success": False, "error": msg}), 500
    finally:
        if used_temp and bin_path and os.path.isfile(bin_path):
            try:
                os.remove(bin_path)
            except OSError:
                pass


# --- Project planning ---

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
                "pin_outs", "wiring", "schematic", "enclosure"):
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
