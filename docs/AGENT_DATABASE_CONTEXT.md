# Agent Database Context — Inventory DB & Project Storage

**Purpose:** Guidance for database handling: inventory SQLite, project proposals (file-based), paths, and what is acceptable when advising or implementing changes.

---

## 1. Inventory database (SQLite)

### Source of truth

- **Catalog:** YAML files under `inventory/items/` (sbcs, controllers, sensors, accessories, components). See [inventory/SCHEMA.md](../inventory/SCHEMA.md).
- **DB path:** Resolved by `config.get_database_path()`. Default: `inventory/inventory.db`. Overridable via **Settings → Paths → Database path** (stored in `artifacts/path_settings.json`); **used on next app start**.
- **Build:** The database is **generated** from YAML. Run from repo root:
  ```bash
  python inventory/scripts/build_db.py
  ```
  Script: [inventory/scripts/build_db.py](../inventory/scripts/build_db.py). It creates/replaces the `items` table and bulk-inserts from all category YAMLs.

### Schema (items table)

| Column        | Type    | Notes |
|---------------|---------|-------|
| id            | TEXT PK | Unique slug (e.g. `raspberry_pi_4_4gb`). |
| name          | TEXT    | Required. |
| category      | TEXT    | One of: sbc, controller, sensor, accessory, component. |
| manufacturer  | TEXT    | |
| part_number   | TEXT    | |
| model         | TEXT    | |
| quantity      | INTEGER | Default 1. |
| location      | TEXT    | |
| specs         | TEXT    | JSON object. |
| datasheet_url | TEXT    | |
| datasheet_file| TEXT    | Path under inventory/ (e.g. datasheets/foo.pdf). |
| notes         | TEXT    | |
| used_in       | TEXT    | JSON array of strings. |
| tags          | TEXT    | JSON array of strings. |

### Acceptable usage

- **Read:** App reads via `get_db()` (sqlite3, row_factory Row). Used by list_items, get_item, categories, search, AI query, project BOM check.
- **Write:** **Do not** write to the DB from the app for catalog data. Edits go in YAML; then run `build_db.py` to regenerate. Exception: there is no in-app “edit item” API; catalog is YAML-first.
- **Path:** Must be a valid path to a SQLite file (existing or to-be-created). If the path is changed in Settings, the app must be restarted to use the new DB.

### Key files

- [inventory/SCHEMA.md](../inventory/SCHEMA.md) — field reference and categories.
- [inventory/README.md](../inventory/README.md) — catalog overview and web app.
- [inventory/app/config.py](../inventory/app/config.py) — `DB_PATH`, `get_database_path()`, `PATH_SETTINGS_PATH`.

---

## 2. Project proposals (file-based, not SQLite)

- **Location:** `artifacts/project_proposals/` (under `REPO_ROOT`). Config: `config.PROJECT_PROPOSALS_DIR`.
- **Format:** One JSON file per project: `{id}.json`. Fields include: id, title, description, conversation, parts_bom, pin_outs, wiring, schematic, enclosure, updated_at, created_at.
- **API:** Create/read/update via backend: GET/POST/PUT `/api/projects`, GET/PUT `/api/projects/<id>`. Implemented in [inventory/app/project_ops.py](../inventory/app/project_ops.py) (list_proposals, load_proposal, save_proposal).
- **Acceptable:** IDs are filenames (safe chars). Do not manually edit JSON while the app might be writing. BOM check reads the inventory DB; proposals themselves are not in the DB.

---

## 3. When to use this context

- User asks how to **change the database path**, **rebuild the DB**, or **add/edit catalog items** (→ YAML + build_db.py).
- User asks about **project storage** (→ artifacts/project_proposals, project_ops).
- Implementing or advising on **any code that reads/writes inventory or project data** — stay within the schema and YAML-first flow for catalog.
