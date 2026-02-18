# Agent Setup Context — Wizards, Docs, and Acceptability

**Purpose:** The AI agent has access to all setup wizards and documentation. Use this context to answer setup questions, give recommendations, and guide users through chat-style setup with explanations at any time.

**Agent rules (apply to all work in this repo):**

- **If errors are ever encountered:** Diagnose, fix, and verify the issue before moving on. Do not proceed to the next task until the current failure is resolved and tested.
- **If errors are encountered when installing and configuring dependencies:** Try to resolve the issue before changing tactics. Do not stray from the plan without specific verification to do so in every case.

---

## 1. How to Use This Context

- **When the user asks for setup help:** Use this document plus the referenced docs to explain steps, recommend options, and state what is acceptable in each area.
- **When the user asks "how do I…":** Point to the relevant wizard or doc and walk through it.
- **When the user is in a specific area (e.g. Flash, Map, Project planning):** Respect the acceptability rules for that area (see below).

---

## 2. Setup Wizards and Where They Live

| Area | What it is | Entry points | Docs / context |
| **Install wizard** | One-time full stack setup: Python venv, deps, inventory DB, optional MCP and Docker | CLI: `python scripts/install_wizard.py` (from repo root). Options: `--non-interactive`, `--skip-docker`, `--skip-mcp`, `--docker-only`. | [docs/INSTALL.md](INSTALL.md). Run after clone; then start app and configure AI/paths in web UI. |
|------|------------|--------------|----------------|
| **Paths** | Docker container, frontend path, backend path, database path, MCP server path | Web: **AI settings** tab → **Paths** section. Save to `artifacts/path_settings.json`. | Database path is used on next app start. Others are for reference or tooling. |
| **Flash / Backup** | Backup, restore, flash firmware to ESP32-family devices; auto-detect port and chip | Web: **Backup / Flash** tab. Click **Refresh & detect devices** to auto-detect. | `inventory/app/flash_ops.py`, `config.FLASH_DEVICES`. Device must be connected via USB; esptool on host. |
| **Map tiles** | Download offline map tiles for T-Deck / Meshtastic; regions, zoom, SD layout | CLI: `scripts/map_wizard.py list|estimate|run`, `scripts/map_tiles/meshtastic_tiles.py`. API: `GET /api/map/regions`, `GET /api/map/estimate`. | `regions/README.md`, `regions/regions.json`, `scripts/map_tiles/README.md`. T-Deck: copy tiles to SD `maps/{style}/`. |
| **Project planning** | BOM, pinouts, wiring, schematic notes, enclosure notes; export CSV/md | Web: **Project planning** tab. Chat with AI; it suggests BOM and DESIGN (pin_outs, wiring, schematic, enclosure). | Export pinout/wiring as CSV; schematic/enclosure as markdown. |
| **Device registry** | Structured device profiles (MCU, radios, flash methods, compatibility) | Data: `registry/devices/*.json`. Used by flash compatibility and Cyberdeck features. | `registry/README.md`, `docs/CYBERDECK_MANAGER_SPEC.md`. |
| **Add device wizard** | Catalog of LilyGo, Heltec, RPi, Pine64, Arduino, Teensy; scaffold `devices/<id>/` and registry | Web: **Add device** tab. Search/filter by vendor, pick device, add datasheet/schematic/firmware URLs, create structure. | `inventory/app/device_ops.py`, `device_catalog.json`; CONTEXT device folder contract. |
| **Device configuration wizard** | Pre- or post-flash device config; internal (Meshtastic/MeshCore) or Launcher compatible; region, device name, presets | Web: **Device config** tab. Steps: When (pre/post flash) → Device → Firmware target → Options (region, name) → Review; save presets to `devices/<id>/configs/<firmware>/`; AI assist available. | `inventory/app/config_wizard_ops.py`, `registry/rf_presets.json`, `registry/devices/*.json`. |
| **Docker & tools** | Status of Docker, list of lab containers, tools (inventory, MCP, PlatformIO) | Web: **Docker & tools** tab. Start/stop/restart containers. | Rebuild after code changes: `./scripts/rebuild-containers.sh`. |
| **Debug / device logs** | Live serial monitor, persistent device logs, live device status | Web: **Debug** tab (serial monitor). API: `GET /api/debug/context`, `GET /api/ai/device-context`. | The AI has access to **connected device logs**, **historical logs**, and **live device status and data** (see section 3). |

---

## 3. AI access to connected device logs, historical logs, and live status

The AI (Setup help, Config wizard chat, Inventory AI query) receives **device context** so it can answer questions about connected devices, serial output, and health.

- **Connected device logs:** Live serial output from the Debug tab serial monitor (last 80 lines in memory). Start the monitor on a port in the Debug tab to capture output.
- **Historical logs:** Persistent log file at `artifacts/device_logs/serial.log`. Each line is timestamped and tagged with the port. The AI gets the last 150 lines (or so) so it can refer to earlier output after restart or when the monitor was stopped.
- **Live device status and data:** Serial active/inactive, current port, list of serial ports, esptool availability, and health check results (problems and suggestions). Returned as `live_status` in the context.

**APIs for AI / MCP / Cursor:**

- **GET /api/ai/device-context** — Full device context for the AI: `serial_tail`, `historical_log`, `live_status`, `ports_summary`, `esptool_ok`, `health_problems`, `health_suggestions`. Use this when building prompts that need device logs or status.
- **GET /api/debug/context** — Same payload; used by the Debug tab and Setup help.

Device context is **injected automatically** into: Setup help chat (`/api/setup/chat`), Config wizard chat (`/api/config-wizard/chat`), and Inventory AI query and stream (`/api/ai/query`, `/api/ai/query/stream`). So the AI can answer “what did the device log say?”, “why isn’t my port showing?”, or “summarize the last serial output” using live and historical data.

---

## 4. Acceptability by Area

### Debug / device logs

- **Serial monitor:** One port at a time. Start from Debug tab or `POST /api/debug/serial/start` with `{ "port": "/dev/...", "baud": 115200 }`. Stop with `POST /api/debug/serial/stop`.
- **Persistent log:** Written to `artifacts/device_logs/serial.log` while the monitor is running. Format: `YYYY-MM-DDTHH:MM:SSZ [port] line`. No automatic rotation; trim or archive the file if it grows large.
- **Live buffer:** In-memory ring buffer (500 lines). Historical log is separate and persists across restarts.

### Paths (Settings)

- **Acceptable:** Any non-empty string for each path. Leave blank to use default.
- **Database path:** Must be a path to an existing (or to-be-created) SQLite DB; used at app start.
- **Docker container:** Name or ID of a lab-related container (e.g. `cyber-lab-mcp`, `app-inventory`).

### Flash / Backup

- **Port:** Must be a serial port (e.g. `/dev/cu.usbserial-*`, `/dev/ttyUSB*`). Use **Refresh & detect devices** to list and auto-detect chip.
- **Device:** Must be a key from the flash device list (e.g. `t_beam_1w`, `t_deck_plus`). Auto-selected when detection succeeds.
- **Backup type:** `full` | `app` | `nvs`.
- **Restore/Flash file:** Path under `artifacts/` or uploaded `.bin`. Must match device/flash layout when relevant.

### Map tiles

- **Region:** Slug from `regions/regions.json` (e.g. `california`, `usa`, `north_america`). Use **list** to see all.
- **City:** Single city name; use quotes if spaces (e.g. `"San Francisco"`, `"Portland, Oregon"`).
- **Cities:** Semicolon-separated, whole argument in quotes (e.g. `"New York; Los Angeles; Las Vegas"`).
- **Zoom:** Integer min/max, typically 8–12 for T-Deck; higher zoom = more tiles and storage.
- **Source:** `osm` | `satellite` | `terrain` | `cycle`. Output folder name on SD should match (e.g. `osm`, `satellite`).
- **Output structure:** Must be `{output_dir}/{zoom}/{x}/{y}.png` and `metadata.json`. Validate with `scripts/sd_validator.py`.

### Project planning

- **BOM:** Array of `{ name, part_number?, quantity }`. Part numbers optional; used for Digi-Key/Mouser export.
- **Design (pin_outs, wiring, schematic, enclosure):** Optional. Pin_outs: `{ pin, function, notes }`. Wiring: `{ from, to, net }`. Schematic/enclosure: free-form markdown for PCB/enclosure notes.

### Device registry

- **Device JSON:** Must include `id`, `name`, and capability fields used by flash/firmware (e.g. `chip`, `flash_size`, `flash_methods`, `compatible_firmware`). Align with `devices/*/DEVICE_CONTEXT.md` when possible.

### Add device wizard

- **Device ID:** Lowercase, letters/numbers/underscores only; becomes `devices/<id>/` and `registry/devices/<id>.json`. Must not already exist.
- **Documentation links:** Datasheet and schematic URLs (any string); firmware_repos: array of URLs. Stored in DEVICE_CONTEXT.md References section.
- **Scaffold:** Creates `firmware/`, `configs/`, `pinmaps/`, `notes/`, `docs/` plus stub READMEs and DEVICE_CONTEXT.md per CONTEXT device contract.
- **Agent device content:** The agent can search the web for device content (datasheets, schematics), download it, and place it in the correct structure. Use **GET /api/agent/device-search?q=...** to search; **GET /api/devices/<device_id>/structure** to see where to put files; **POST /api/devices/fetch-doc** with device_id, url, doc_type (datasheet|schematic|manual|reference|other) to download and save to `devices/<id>/docs/` with correct naming. Web search requires `pip install duckduckgo-search`.
- **Device SDKs:** When adding a device, if the catalog lists a full SDK (e.g. PlatformIO platform), it can be installed automatically (checkbox **Install device SDK**, on by default). SDKs integrate with Cyber-Lab so firmware builds use the correct platform. **AI access:** Use **GET /api/devices/<device_id>/sdk** to get SDK metadata for a device: `device_id`, `platform_id`, `install_type`, `path`, and `docs_hint` (path to `devices/<id>/notes/SDK_AND_TOOLS.md` when present). Use `docs_hint` to read per-device SDK/tool notes so the AI can reference the full feature set. See **docs/SDK_INTEGRATION.md** for what’s implemented and planned.

### Docker

- **Containers:** Only start/stop/restart lab-related containers (inventory, MCP, platformio). Rebuild images after code changes.

---

## 5. Key Documentation Paths

| Topic | Path |
|-------|------|
| **Full install (wizard)** | `docs/INSTALL.md`, `scripts/install_wizard.py` — dependencies, venv, DB, Docker. |
| Project phase and next actions | `PROJECT_CONTEXT.md` |
| Lab contract and device layout | `CONTEXT.md` |
| Roadmap and backlog | `FEATURE_ROADMAP.md` |
| Development plan (phases/tasks) | `DEVELOPMENT_PLAN.md` |
| Map regions and T-Deck tile structure | `regions/README.md`, `regions/regions.json` |
| Map tile script (tdeck-maps compatible) | `scripts/map_tiles/README.md` |
| **PCB & 3D design stack** (AI, dimensions, export, maker upload) | `docs/PCB_3D_DESIGN_STACK_SPEC.md` — part dimensions, placements, enclosure, 3D preview, export formats, maker sites. |
| **Device SDKs** (install on add, AI access) | `docs/SDK_INTEGRATION.md` — PlatformIO platform install, GET `/api/devices/<id>/sdk`, `docs_hint` for `devices/<id>/notes/SDK_AND_TOOLS.md`. |
| Flash auto-detect and backup/restore | `inventory/app/flash_ops.py`, Backup / Flash tab |
| Path settings and artifacts | `artifacts/path_settings.json`, `artifacts/ai_settings.json` |
| Cyberdeck Manager (device/firmware/map/flash) | `docs/CYBERDECK_MANAGER_SPEC.md`, `docs/cyberdeck_scaffold.md` |
| Rebuild containers | `./scripts/rebuild-containers.sh`, `README.md` |
| MCP server (Cursor agent) | `mcp-server/README.md` |

---

## 6. Chat-Style Setup

- The user may ask at any time for **setup recommendations** or **step-by-step setup** with explanations.
- Prefer: (1) identify the area (paths, flash, map, project, device, Docker), (2) point to the wizard or doc, (3) give a short sequence of steps and what’s acceptable (from section 3), (4) offer to clarify or go deeper.
- If the user is in the web UI, you can say e.g. “Open the **Backup / Flash** tab, then click **Refresh & detect devices**…” or “In **Project planning**, describe your circuit; the AI will suggest a BOM and pinouts…”

---

## 7. MCP and Cursor Agent

- **Resources:** The agent can read `project://setup-context` (this file) and other project resources (`project://context`, `project://roadmap`, `project://lab-context`, etc.).
- **Tools:** Use `get_setup_help` to retrieve setup context and wizard summary; use `get_device_context`, `list_devices`, `get_project_status`, `get_next_tasks` as needed for device or task-specific setup.

---

## 8. Deeper guidance (database, backend, Docker, frontend)

For detailed rules and acceptability in each area, use the dedicated context files (or MCP resources / tool):

| Area | Context file | MCP resource | Use when |
|------|--------------|--------------|----------|
| **Database** | [docs/AGENT_DATABASE_CONTEXT.md](AGENT_DATABASE_CONTEXT.md) | `project://database-context` | Inventory DB schema, path, build from YAML; project proposals storage. |
| **Backend** | [docs/AGENT_BACKEND_CONTEXT.md](AGENT_BACKEND_CONTEXT.md) | `project://backend-context` | Flask routes, API, config, services (flash_ops, project_ops, map_ops). |
| **Docker** | [docs/AGENT_DOCKER_CONTEXT.md](AGENT_DOCKER_CONTEXT.md) | `project://docker-context` | Status, container list, start/stop/restart, images, rebuild. |
| **Frontend** | [docs/AGENT_FRONTEND_CONTEXT.md](AGENT_FRONTEND_CONTEXT.md) | `project://frontend-context` | Tabs, panels, UI elements, which API each part uses. |

**Tool:** `get_lab_guidance` with optional `area` (`database` \| `backend` \| `docker` \| `frontend`) returns the corresponding context; omit `area` to get all four.
