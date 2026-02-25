# AGENTS.md

## Cursor Cloud specific instructions

### Services overview

| Service | Stack | Dev command | Port |
|---------|-------|-------------|------|
| Inventory Web App | Python 3.12 / Flask | `source .venv/bin/activate && python inventory/app/app.py` | 5050 |
| MCP Server | Node 22 / TypeScript | `cd mcp-server && npm run build && node dist/index.js` | stdio (no port) |

### Running the Flask inventory app

Run from the **repo root** (not from `inventory/app/`):

```bash
source .venv/bin/activate
python inventory/app/app.py
```

The app listens on `http://127.0.0.1:5050`. The SQLite DB at `inventory/inventory.db` must exist first; rebuild it with `python inventory/scripts/build_db.py` if missing.

### Lint and test commands

- **Python lint:** `source .venv/bin/activate && ruff check inventory/app/ cyberdeck_cli/` (pre-existing warnings exist in the repo; these are not regressions)
- **TypeScript type-check:** `cd mcp-server && npx tsc --noEmit`
- **MCP build:** `cd mcp-server && npm run build`
- **E2E smoke test:** `source .venv/bin/activate && python inventory/app/e2e_test.py` (requires the Flask app to be running on port 5050)
- **Pytest (cyberdeck CLI):** `source .venv/bin/activate && pytest`

### Gotchas

- The `python3.12-venv` system package must be installed (`sudo apt-get install -y python3.12-venv`) before creating the virtualenv. The update script handles this.
- `inventory/app/app.py` uses relative imports (`from config import ...`). It auto-detects the repo root, but it **must** be launched from the repo root directory, not from inside `inventory/app/`.
- The install wizard prints port 5000 in its "Next steps" output, but the actual Flask app binds to **port 5050**.
- Docker is optional; it is only needed for firmware container builds and containerized app deployment. The Flask app runs natively without Docker.
- AI features (AI query, datasheet analysis) require an `OPENAI_API_KEY` set in the web app's AI Settings tab or as an environment variable. Without it, AI endpoints gracefully degrade.
- Config files (`artifacts/path_settings.json`, `artifacts/ai_settings.json`) are created by the install wizard and are gitignored. They persist across runs.
