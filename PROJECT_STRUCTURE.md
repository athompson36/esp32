# Project Structure — Layout, Conventions, Stacks & Dependencies

**Role:** Single reference for repo layout, naming conventions, tech stacks, and dependencies. **Keep this file updated** when you add features, change structure, add/remove dependencies, or change conventions (see [.cursor/rules/project-structure.mdc](.cursor/rules/project-structure.mdc)).

---

## 1. Repo purpose

- **Embedded firmware lab** — Multi-device, multi-firmware; deterministic containerized builds; flash/serial from host (macOS).
- **Inventory & tooling** — Hardware catalog (YAML → SQLite), Flask web app (search, AI, flash, Docker status, project planning), MCP server for Cursor (context, tools).
- **Local-first** — No required cloud; optional OpenAI for AI query and setup help.

See [CONTEXT.md](CONTEXT.md) for philosophy and rules; [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) for current phase and next actions.

---

## 2. Directory structure

```
esp32/                             # repo: athompson36/esp32
├── CONTEXT.md                 # Lab contract, device layout, non‑negotiable rules
├── PROJECT_CONTEXT.md         # Current phase, next actions (keep on task)
├── PROJECT_STRUCTURE.md       # This file — layout, conventions, stacks, deps
├── README.md                  # Quick start, key docs
├── FEATURE_ROADMAP.md         # Backlog and roadmap
├── DEVELOPMENT_PLAN.md        # Phased tasks
├── FIRMWARE_INDEX.md          # Firmware and OS per device
├── REPOS.md                    # Lab repo index (Meshtastic, MeshCore, etc.)
├── current_project.md         # ESP32/SBC project ideas and links
│
├── .cursor/rules/             # Cursor agent rules (rebuild-containers, setup-context, lab-guidance, docker-and-commit, project-structure)
│
├── artifacts/                 # Generated / persisted at runtime
│   ├── ai_settings.json       # AI API key, model, base_url (from Settings)
│   ├── path_settings.json     # Docker container, paths (DB, frontend, backend, MCP)
│   ├── backups/               # Flash backups (.bin)
│   └── project_proposals/     # Project planning JSON files
│
├── devices/                   # Per-device context (one dir per device)
│   └── <device_id>/
│       ├── DEVICE_CONTEXT.md
│       ├── notes/             # SDK_AND_TOOLS.md, etc.
│       └── firmware/          # Firmware README, overlays
│
├── docs/                      # Specs and agent context
│   ├── AGENT_SETUP_CONTEXT.md
│   ├── AGENT_DATABASE_CONTEXT.md
│   ├── MESHTASTIC_MESHCORE_LAUNCHER_DEVICES.md  # Supported devices & repos (Meshtastic, MeshCore, Launcher, web flashers)
│   ├── AGENT_BACKEND_CONTEXT.md
│   ├── AGENT_DOCKER_CONTEXT.md
│   ├── AGENT_FRONTEND_CONTEXT.md
│   └── CYBERDECK_MANAGER_SPEC.md, cyberdeck_scaffold.md, etc.
│
├── docker/                    # Lab build images (toolchain-specific)
│   ├── Dockerfile             # platformio-lab (ESP32, Arduino, Teensy, ARM)
│   ├── Dockerfile.esp-idf-lab # esp-idf-lab (ESP-IDF v5, LVGL — Lumari Watch, custom ESP32)
│   ├── README.md, DEPENDENCIES.md
│   └── TOOLS_AND_SDK.md
│
├── inventory/                 # Hardware catalog and web app
│   ├── README.md
│   ├── SCHEMA.md              # Catalog field reference
│   ├── items/                 # YAML per category (sbcs, controllers, sensors, accessories, components)
│   ├── scripts/
│   │   └── build_db.py        # YAML → SQLite (inventory.db)
│   └── app/                   # Flask web app
│       ├── app.py             # Routes, Docker/status, flash, projects, AI, setup chat
│       ├── config.py          # REPO_ROOT, DB path, path_settings, AI settings, FLASH_DEVICES
│       ├── flash_ops.py       # Backup, restore, flash; list_serial_ports, get_flash_devices
│       ├── project_ops.py     # Proposals (list, load, save), BOM check, CSV/md export
│       ├── map_ops.py         # Map regions, tile estimate
│       ├── device_ops.py      # Add device wizard: catalog, scaffold devices/ + registry
│       ├── device_catalog.json # Device catalog (LilyGo, Heltec, RPi, Pine64, Arduino, Teensy)
│       ├── updates.py         # GitHub firmware update check
│       ├── requirements.txt
│       ├── Dockerfile
│       ├── docker-compose.yml
│       ├── static/            # JS, CSS
│       └── templates/         # index.html, base.html
│
├── mcp-server/                # MCP server (Cursor)
│   ├── src/index.ts           # Resources, tools (get_project_status, get_setup_help, get_lab_guidance, etc.)
│   ├── package.json
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── registry/                  # Device registry (JSON)
│   ├── README.md
│   └── devices/*.json         # t_beam_1w, t_deck_plus, etc.
│
├── regions/                   # Map tile wizard
│   ├── README.md
│   └── regions.json
│
├── scripts/                   # CLI and automation
│   ├── rebuild-containers.sh  # Build inventory + MCP images
│   ├── map_wizard.py
│   ├── map_tiles/             # meshtastic_tiles.py, README
│   └── sd_validator.py
│
├── shared/                    # Shared configs, pinmaps (per CONTEXT)
├── toolchains/                # (Optional) pinned toolchains
└── experimental/, legacy/    # Isolated work
```

---

## 3. Conventions

- **Device IDs:** Lowercase, underscores (e.g. `t_beam_1w`, `t_deck_plus`). Match `devices/<id>/` and `registry/devices/<id>.json`.
- **Catalog items:** Unique `id` (slug) across all YAML in `inventory/items/`. Categories: `sbc`, `controller`, `sensor`, `accessory`, `component`. See [inventory/SCHEMA.md](inventory/SCHEMA.md).
- **Paths:** Run Flask app from **repo root**: `python inventory/app/app.py`. DB path overridable in Settings → Paths; stored in `artifacts/path_settings.json`; used on next app start.
- **Builds:** Firmware builds in container (`platformio-lab` or `esp-idf-lab`). Flash from host (esptool). See [CONTEXT.md](CONTEXT.md).
- **Containers:** Lab images: `cyber-lab-mcp`, `inventory-app` / `app-inventory`, `platformio-lab`, `esp-idf-lab`. Compose files use `restart: unless-stopped` for auto-restart and start with daemon.
- **Agent context:** Setup and guidance in `docs/AGENT_*.md`. MCP exposes `project://setup-context`, `project://database-context`, etc., and tools `get_setup_help`, `get_lab_guidance`.
- **Add device wizard:** Catalog in `inventory/app/device_catalog.json`; scaffold via **Add device** tab (API: GET `/api/devices/catalog`, POST `/api/devices/scaffold`). Creates `devices/<id>/` and `registry/devices/<id>.json` with doc links in DEVICE_CONTEXT.

---

## 4. Stacks and runtimes

| Area | Stack | Entry / build |
|------|--------|----------------|
| **Inventory web app** | Python 3.12, Flask 3.x | `python inventory/app/app.py` (from repo root) or `docker compose -f inventory/app/docker-compose.yml up -d` |
| **MCP server** | Node ≥18, TypeScript 5 | `npm run build` in `mcp-server/`; run via Cursor (stdio) or `node dist/index.js` |
| **Firmware builds** | PlatformIO or ESP-IDF (in container) | `platformio-lab`: `pio run -e <env>`; `esp-idf-lab`: `idf.py build`. Orchestrator: `scripts/lab-build.sh <device> <firmware> [env]`. |
| **Map / scripts** | Python 3, PyYAML | `scripts/map_wizard.py`, `scripts/map_tiles/`, `inventory/scripts/build_db.py` |

---

## 5. Libraries and dependencies

### Inventory app (Python)

- **File:** [inventory/app/requirements.txt](inventory/app/requirements.txt)
- **Contents:** `flask>=3.0`, `pyyaml>=6.0`, `openai>=1.0`, `pyserial>=3.5`
- **Host deps (flash):** `esptool` (install on host for backup/restore/flash).

### MCP server (Node)

- **File:** [mcp-server/package.json](mcp-server/package.json)
- **Runtime:** `@modelcontextprotocol/sdk` ^1.0.0, `zod` ^3.23.0
- **Dev:** `typescript` ^5.0, `@types/node` ^20.0.0
- **Engines:** Node ≥18

### PlatformIO / firmware

- Per-project `platformio.ini` and envs; toolchain inside `platformio-lab` image. See [docker/](docker/) and [FIRMWARE_INDEX.md](FIRMWARE_INDEX.md).

---

## 6. Docker images and compose

| Image | Compose file | Purpose |
|-------|----------------|--------|
| **inventory-app** (or app-inventory) | `inventory/app/docker-compose.yml` | Flask app; port 5050; mount repo at /workspace; `restart: unless-stopped` |
| **cyber-lab-mcp** | `mcp-server/docker-compose.yml` | MCP server (stdio); mount repo; `restart: unless-stopped` |
| **platformio-lab** | `docker/Dockerfile` (built manually) | Firmware builds |

Rebuild after app/MCP code changes: `./scripts/rebuild-containers.sh`. See [docs/AGENT_DOCKER_CONTEXT.md](docs/AGENT_DOCKER_CONTEXT.md) for status, start/stop, and restart policy.

---

## 7. Key config and env

- **REPO_ROOT** (env): Used by Flask app (default: parent of `inventory/app`). In Docker set to `/workspace`.
- **CYBER_LAB_REPO_ROOT** (env): Used by MCP server (default: `process.cwd()`). Set to `/workspace` when running in Docker.
- **artifacts/ai_settings.json**: API key, model, base_url (env `OPENAI_API_KEY` overrides key).
- **artifacts/path_settings.json**: docker_container, frontend_path, backend_path, database_path, mcp_server_path.

---

## 8. Last updated

- **Structure / stacks / deps:** Document created; update this section and relevant sections when you add features, change layout, or change dependencies.
- **2026-02-23:** L6 esp-idf-lab added (docker/Dockerfile.esp-idf-lab), lab-build.sh IDF path and Lumari Watch, BUILD_CONFIG + FLASH_DEVICES for lumari_watch.
