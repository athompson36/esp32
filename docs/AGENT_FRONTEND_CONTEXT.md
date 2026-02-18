# Agent Frontend Context — Tabs, Panels & UI Guidance

**Purpose:** Guidance for the inventory web UI: tabs, main panels, API usage from the frontend, and what is acceptable when advising or implementing UI changes.

---

## 1. Entry & layout

- **Single-page app:** [inventory/app/templates/index.html](../inventory/app/templates/index.html) (extends base.html). Main content: nav tabs + tab panels. Session storage key `inventory-app-tab` remembers last tab.
- **Scripts:** [inventory/app/static/js/app.js](../inventory/app/static/js/app.js). **Styles:** [inventory/app/static/css/style.css](../inventory/app/static/css/style.css).

---

## 2. Tabs (in order)

| Tab ID       | Label          | Panel ID        | Purpose |
|-------------|----------------|-----------------|---------|
| search      | Search         | panel-search    | Search bar, category filter, AI query input, results count, inventory table. |
| settings    | AI settings    | panel-settings  | AI API key, model, base URL; Paths (Docker, frontend, backend, database, MCP). |
| docker      | Docker & tools | panel-docker    | Docker status, containers table (name, image, state, status, actions: start/stop/restart), tools list. |
| flash       | Backup / Flash | panel-flash     | Port/device select, Backup (type), Restore (file), Flash (file). Refresh & detect devices. |
| projects    | Project planning| panel-projects | Project select, title/description, AI chat, BOM table, hardware (pinout, wiring, schematic, enclosure), save. |
| inventory   | Inventory      | panel-inventory| Results count and full items table (same data as search results). |
| setup-help  | Setup help     | panel-setup-help| Chat with setup context (wizards, acceptability). |
| add-device  | Add device     | panel-add-device| Device wizard: vendor/search, expandable device list, form (ID, name, MCU, datasheet, schematic, firmware repos); creates `devices/<id>/` and registry. |

Tab buttons: `.tab-btn`, `data-tab="<id>"`, `id="tab-btn-<id>"`. Panels: `.tab-panel`, `id="panel-<id>"`. Switch with `switchTab(tabId)`; only one panel visible.

---

## 3. Key elements & API usage

### Search

- `#search`, `#category`, `#btn-search` → GET `/api/items?q=...&category=...&limit=500`. Results in `#tbody`, count in `#results-count`.
- `#ai-query`, `#btn-ai` → POST `/api/ai/query` or stream via `/api/ai/query/stream`; answer in `#ai-answer`.

### Settings

- AI: `#settings-api-key`, `#settings-model`, `#settings-base-url`, `#btn-settings-save` → GET/POST `/api/settings/ai`.
- Paths: `#settings-docker-container`, `#settings-frontend-path`, `#settings-backend-path`, `#settings-database-path`, `#settings-mcp-server-path`, `#btn-settings-paths-save` → GET/POST `/api/settings/paths`.

### Docker

- `#docker-status` — filled from GET `/api/docker/status`.
- `#docker-containers-table` (tbody `#docker-containers-tbody`) — GET `/api/docker/containers`; actions POST `/api/docker/containers/<id>/<action>` (start/stop/restart).
- `#docker-tools` — GET `/api/docker/tools` (tools list).

### Flash

- `#flash-port`, `#flash-device` — GET `/api/flash/ports` (optional ?detect=1), GET `/api/flash/devices`. Backup: POST `/api/flash/backup`. Restore: POST `/api/flash/restore`. Flash: POST `/api/flash/flash`. Dropdowns for files from GET `/api/flash/artifacts`.

### Project planning

- `#project-select`, `#project-title`, `#project-description`, `#project-messages`, `#project-message`, `#btn-project-send` → GET/POST/PUT `/api/projects`, POST `/api/projects/ai/stream`. BOM table `#project-bom-tbody`; design tables and pre blocks for pinout, wiring, schematic, enclosure. Save → PUT project; exports → GET `/api/projects/<id>/bom/digikey` etc.

### Setup help

- `#setup-help-messages`, `#setup-help-message`, `#btn-setup-help-send` → POST `/api/setup/chat` with `message` and `history`. Renders user/assistant bubbles (reuses `.project-messages`, `.project-msg`).

### Add device

- `#device-wizard-vendor`, `#device-wizard-search` → GET `/api/devices/catalog?vendor=&q=`. List in `#device-wizard-list` (grouped by vendor, expandable). Form: `#device-form-id`, `#device-form-name`, `#device-form-mcu`, `#device-form-datasheet`, `#device-form-schematic`, `#device-form-firmware-repos` (.device-form-repo), `#device-form-submit` → POST `/api/devices/scaffold` with device_id, name, vendor, mcu, doc_links.

### Inventory (table)

- Same `#tbody` and `#results-count` as search; table `#inventory-table`. Data loaded when search runs or when switching to Inventory with existing results.

### Detail panel

- `#detail-panel`, `#detail-content`, `#close-detail` — overlay for item detail (e.g. row click). Can load GET `/api/items/<id>` for full item.

---

## 4. Acceptable patterns

- **Tabs:** Add new tab by adding a `.tab-btn` and a `.tab-panel` with matching `data-tab` and `id="panel-<id>"`. Ensure `switchTab` and session storage handle the new id.
- **API:** All API base is relative (same origin). Use fetch with JSON for POST/PUT; for SSE use `response.body.getReader()` and parse `data: ` lines.
- **IDs:** Keep existing element IDs when adding features so existing listeners and CSS still apply. Use existing classes (e.g. `.project-messages`) for consistency.

---

## 5. When to use this context

- User asks **where something is in the UI** (which tab, which panel) or **how to add a new tab/panel**.
- Implementing **new UI** that calls existing APIs — use the same fetch/error/success patterns as in app.js.
- Guidance on **Docker & tools** UI (status, container actions), **Flash** UI (ports, backup/restore/flash), **Setup help** chat, or **Project planning** flow.
