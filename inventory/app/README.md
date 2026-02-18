# Inventory Management Web App

AI-backed web UI for the lab inventory: search, filter by category, natural-language (AI) query, and item detail panel.

---

## Features

- **Search** — Full-text search over name, part number, model, notes, tags, manufacturer.
- **Category filter** — Restrict to SBC, controller, sensor, accessory, or component.
- **AI query** — Type a natural language question (e.g. *“What do I have for MIDI?”*, *“Teensy boards?”*, *“5V parts?”*). Uses keyword matching always; if `OPENAI_API_KEY` is set, optional OpenAI re-ranks and summarizes.
- **Detail panel** — Click a row to open specs, datasheet link, notes, tags, and used_in.
- **Project planning** — Develop an idea with the AI; it checks your inventory and suggests a parts BOM. Export BOM as CSV for **Digi-Key** (primary) or **Mouser** (backup). Save full project proposals (stored under `artifacts/project_proposals/` in the repo; when running in Docker, mount the repo with write access so proposals persist).

---

## Prerequisites

1. **Build the database** (from repo root):

   ```bash
   python3 -m venv .venv && source .venv/bin/activate  # optional
   pip install pyyaml
   python inventory/scripts/build_db.py
   ```

2. **Install app dependencies**:

   ```bash
   cd inventory/app
   pip install -r requirements.txt
   ```

   (Or use the same venv from repo root: `pip install -r inventory/app/requirements.txt`.)

---

## Run (from repo root)

```bash
python inventory/app/app.py
```

Then open **http://127.0.0.1:5050** (or set `PORT` to use another port).

To run from inside `inventory/app`:

```bash
cd inventory/app
python app.py
```

(The app resolves the DB path relative to the inventory directory.)

---

## Run with Docker

The app and AI tools (search, updates check, AI query, project planning) can run in a container. The compose file mounts the **host Docker socket** and the image includes the **Docker CLI**, so the UI can show Docker status and list/start/stop lab containers. Mount the repo so the app can read `inventory.db` and YAML; use a read-write mount if you want to **save project proposals** (they are stored under `artifacts/project_proposals/`).

**From repo root** (ensure `inventory/inventory.db` exists — run `python inventory/scripts/build_db.py` first):

```bash
docker compose -f inventory/app/docker-compose.yml up --build
```

Then open **http://127.0.0.1:5050**.

**Optional:** Pass your OpenAI key for AI answers and update summaries:

```bash
OPENAI_API_KEY=sk-... docker compose -f inventory/app/docker-compose.yml up --build
```

Or add to a `.env` file next to `docker-compose.yml` and reference it in the compose file (see `environment` in `docker-compose.yml`).

**Plain `docker run`** (from repo root; add `-v /var/run/docker.sock:/var/run/docker.sock` for Docker status in the UI):

```bash
docker build -t inventory-app -f inventory/app/Dockerfile inventory/app
docker run --rm -p 5050:5050 -v "$(pwd):/workspace" -v /var/run/docker.sock:/var/run/docker.sock -e REPO_ROOT=/workspace inventory-app
```

---

## E2E tests

With the app running (local or Docker), run all endpoint checks from repo root:

```bash
python inventory/app/e2e_test.py http://127.0.0.1:5050
```

Covers: `/`, settings, categories, items, Docker status/tools, updates, flash, projects (CRUD + exports). Exit code 0 = all passed.

---

## Optional: AI answers

Set `OPENAI_API_KEY` so the **AI query** box can return a short natural-language answer and re-ranked item list:

```bash
export OPENAI_API_KEY=sk-...
python inventory/app/app.py
```

Without the key, AI query still works using keyword matching only.

---

## Tech

- **Backend:** Flask, SQLite (reads `inventory/inventory.db`).
- **Frontend:** Vanilla JS, CSS (no build step).
- **AI:** Keyword search always; optional OpenAI (gpt-4o-mini) for answer + ranking when key is set.
