# Agent Backend Context — Flask App, Routes & Services

**Purpose:** Guidance for the inventory Flask backend: routes, config, services, and what is acceptable when advising or implementing API or server logic.

---

## 1. Overview

- **App:** [inventory/app/app.py](../inventory/app/app.py). Run from **repo root:** `python inventory/app/app.py`. Port 5000.
- **Config:** [inventory/app/config.py](../inventory/app/config.py) — REPO_ROOT, DB path, path_settings, AI settings, FLASH_DEVICES, PROJECT_PROPOSALS_DIR, BUILD_CONFIG.
- **REPO_ROOT:** From env `REPO_ROOT` or parent of `inventory/app`. Used for DB path, artifacts, docs, scripts.

---

## 2. Routes by group

### Settings

| Method | Path | Description |
|--------|------|-------------|
| GET    | /api/settings/ai | AI API key (masked), model, base_url. |
| POST   | /api/settings/ai | Body: api_key?, model?, base_url?. Stored in artifacts/ai_settings.json. |
| GET    | /api/settings/paths | docker_container, frontend_path, backend_path, database_path, mcp_server_path. |
| POST   | /api/settings/paths | Body: same keys (all optional). Stored in artifacts/path_settings.json. Database path used on next start. |

### Items (inventory DB)

| Method | Path | Description |
|--------|------|-------------|
| GET    | /api/items | Query: q?, category?, limit?. Returns { items, total }. |
| GET    | /api/items/<item_id> | Single item or 404. |
| GET    | /api/categories | List of category names from DB. |

### Docker

| Method | Path | Description |
|--------|------|-------------|
| GET    | /api/docker/status | docker_available, docker_message, images (lab-related). |
| GET    | /api/docker/containers | List of lab containers: id, name, image, state, status. 503 if Docker unavailable. |
| POST   | /api/docker/containers/<container_id>/<action> | action: start \| stop \| restart. Returns success/error. |
| GET    | /api/docker/tools | Lab tools (inventory-web, mcp-server, platformio-lab, etc.) and availability. |

### Devices (add-device wizard and agent)

| Method | Path | Description |
|--------|------|-------------|
| GET    | /api/devices/catalog | Optional ?vendor=, ?q=. Returns vendors, devices (with already_in_lab), existing_ids. |
| POST   | /api/devices/scaffold | Body: device_id, name, vendor?, mcu?, doc_links? (datasheet, schematic, firmware_repos), **install_sdk?** (default true). Creates devices/<id>/ and registry; if install_sdk and catalog has sdk, runs PlatformIO platform install. Response may include sdk_message, paths.sdk_install_error. |
| GET    | /api/devices/<device_id>/sdk | SDK metadata for AI/tools: device_id, platform_id, install_type, path, docs_hint (e.g. devices/<id>/notes/SDK_AND_TOOLS.md). 404 if device has no SDK in catalog. |
| GET    | /api/devices/<device_id>/structure | Returns device_dir, docs_dir, naming conventions, allowed_doc_types, existing_docs. Use before fetch-doc to know where files go. |
| POST   | /api/devices/fetch-doc | Body: device_id, url, doc_type (datasheet\|schematic\|manual\|reference\|other), optional suggested_filename. Downloads to devices/<id>/docs/ with correct naming. |
| GET    | /api/agent/device-search | Query: q=, max_results? (default 10). Web search for device content (datasheets, schematics). Returns results (title, url, snippet). Requires duckduckgo-search. |

### Map

| Method | Path | Description |
|--------|------|-------------|
| GET    | /api/map/regions | Regions and map sources for tile wizard. |
| GET    | /api/map/estimate | Query: region, min_zoom?, max_zoom?. Tile count/size estimate. |

### Flash / backup

| Method | Path | Description |
|--------|------|-------------|
| GET    | /api/flash/ports | List serial ports. ?detect=1 for chip detection. |
| GET    | /api/flash/devices | Supported devices (from config.FLASH_DEVICES). |
| GET    | /api/flash/artifacts | Firmware/backup files for dropdowns. |
| POST   | /api/flash/backup | Body: port, device_id, backup_type (full \| app \| nvs). |
| POST   | /api/flash/restore | Body: port, file (path under artifacts or upload). |
| POST   | /api/flash/flash | Body: port, file. |

### Projects (file-based proposals)

| Method | Path | Description |
|--------|------|-------------|
| GET    | /api/projects | List proposals (id, title, updated_at). |
| POST   | /api/projects | Body: title?, description?, parts_bom?, conversation?. Creates JSON file. |
| GET    | /api/projects/<id> | Full proposal. |
| PUT    | /api/projects/<id> | Update proposal. |
| GET    | /api/projects/<id>/check-inventory | BOM vs inventory DB. |
| GET    | /api/projects/<id>/bom/digikey | CSV. |
| GET    | /api/projects/<id>/bom/mouser | CSV. |
| GET    | /api/projects/<id>/export/pinout | CSV. |
| GET    | /api/projects/<id>/export/wiring | CSV. |
| GET    | /api/projects/<id>/export/schematic | Markdown. |
| GET    | /api/projects/<id>/export/enclosure | Markdown. |
| POST   | /api/projects/ai | Body: message, project_id?. Returns reply, suggested_bom, suggested_design. |
| POST   | /api/projects/ai/stream | Same; SSE stream. |

### Device configuration wizard

| Method | Path | Description |
|--------|------|-------------|
| GET    | /api/config-wizard/context | Devices (with compatible_firmware), firmware_targets, rf_presets. |
| GET    | /api/config-wizard/presets | Query: device_id, firmware. List saved presets. |
| POST   | /api/config-wizard/presets | Body: device_id, firmware, preset_name, options. Save preset to devices/<id>/configs/<firmware>/. |
| GET    | /api/config-wizard/presets/<name> | Query: device_id, firmware. Load one preset. |
| POST   | /api/config-wizard/chat | Body: message, step?, device_id?, firmware?, options?. AI assist with wizard state. |

### AI & setup

| Method | Path | Description |
|--------|------|-------------|
| POST   | /api/ai/query | Body: query. Keyword match + optional OpenAI re-rank. |
| POST   | /api/ai/query/stream | Same; SSE stream. |
| POST   | /api/setup/chat | Body: message, history?. System prompt from docs/AGENT_SETUP_CONTEXT.md. Returns { reply }. |

### Updates

| Method | Path | Description |
|--------|------|-------------|
| GET    | /api/updates | GitHub latest releases for firmware (Meshtastic, MeshCore, etc.). |

---

## 3. Services (modules)

- **flash_ops** — backup_flash, restore_flash, flash_firmware, list_serial_ports, list_artifacts_and_backups, get_flash_devices. Uses config.FLASH_DEVICES, REPO_ROOT.
- **project_ops** — list_proposals, load_proposal, save_proposal, check_bom_against_inventory, bom_csv_digikey, bom_csv_mouser. Uses PROJECT_PROPOSALS_DIR and DB connection for BOM check.
- **map_ops** — wizard_list_regions, wizard_estimate. Uses regions/ and scripts/map_tiles.
- **config** — get_database_path, get_path_settings, save_path_settings, get_openai_api_key, get_openai_model, get_openai_base_url, save_ai_settings.

---

## 4. Acceptable patterns

- **DB access:** Use `get_db()`; close or reuse per request. Read-only for catalog; no direct INSERT/UPDATE/DELETE for items in app (catalog is YAML + build_db).
- **Errors:** Return JSON with error key and appropriate HTTP status (400, 404, 503). Docker endpoints degrade to 503 when Docker is unavailable.
- **IDs:** Container IDs and proposal IDs sanitized (alphanumeric, hyphen, underscore) where used in subprocess or paths.
- **Streaming:** SSE for /api/ai/query/stream, /api/projects/ai/stream; use stream_with_context and Cache-Control: no-cache.

---

## 5. When to use this context

- User asks how to **add an API**, **change a route**, or **where a feature is implemented**.
- Implementing **new endpoints** or **backend logic** — follow existing route grouping and config usage.
- Questions about **settings storage**, **path overrides**, or **AI/setup chat** backend behavior.
