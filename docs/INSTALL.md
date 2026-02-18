# Install Wizard — Full Setup and Configuration

After cloning the repo (and once features have been tested), use the **install wizard** to set up and configure the entire software stack: dependencies, virtual environment, inventory database, optional MCP server and Docker.

---

## Prerequisites

- **Python 3.9+** — required (inventory app, map tiles, scripts).
- **Node.js 18+** — optional; needed to build the MCP server for Cursor integration.
- **Docker** — optional; needed for firmware builds in container and for running the app/MCP in containers.

---

## Run the wizard

From the **repo root**:

```bash
python scripts/install_wizard.py
```

The wizard will:

1. **Check system** — Python version, optional Node, optional Docker.
2. **Python environment** — Create a `.venv` in the repo root if missing, and install:
   - Inventory app dependencies (`inventory/app/requirements.txt`: Flask, PyYAML, OpenAI, pyserial, etc.)
   - Map tile dependencies (requests, optional Pillow).
3. **MCP server** — If Node is available, run `npm install` and `npm run build` in `mcp-server/`.
4. **Artifacts and config** — Create `artifacts/`, `artifacts/backups/`, `artifacts/device_logs/`, `artifacts/project_proposals/`. If they don’t exist, create default:
   - `artifacts/path_settings.json` (database path, backend path, MCP path, etc.)
   - `artifacts/ai_settings.json` (model, base_url; add API key later in the web app).
5. **Inventory database** — Run `inventory/scripts/build_db.py` to build the SQLite database from YAML under `inventory/items/`.
6. **Docker images (optional)** — If Docker is available, you can optionally build:
   - `platformio-lab` (firmware builds)
   - Inventory app image
   - MCP server image

At the end, the wizard prints **next steps**: activate venv, start the app, open the browser, and where to set the AI key and paths.

---

## Options

| Option | Description |
|--------|-------------|
| `--non-interactive` | Use defaults; do not prompt (e.g. for CI). |
| `--skip-docker` | Do not build Docker images. |
| `--skip-mcp` | Do not build the MCP server. |
| `--docker-only` | Only build Docker images; skip venv, DB, and config. |

Examples:

```bash
# CI or scripted install: no prompts, skip Docker
python scripts/install_wizard.py --non-interactive --skip-docker

# Only rebuild Docker images later
python scripts/install_wizard.py --docker-only
```

---

## After install

1. **Activate the virtual environment**
   - macOS/Linux: `source .venv/bin/activate`
   - Windows: `.venv\Scripts\activate`

2. **Start the web app** (from repo root)
   ```bash
   python inventory/app/app.py
   ```

3. **Open** [http://127.0.0.1:5000](http://127.0.0.1:5000)

4. **In the web app**
   - **AI settings** — Set OpenAI API key (or compatible) and model if you use AI query or project planning.
   - **Paths** — Adjust database path, Docker container name, or MCP path if needed (defaults are usually fine).

5. **Firmware builds**
   - Ensure Docker is running.
   - Use the **Backup / Flash** tab to detect devices and flash; builds use the `platformio-lab` image.

6. **MCP (Cursor)**
   - If you built the MCP server, configure Cursor to use it (stdio transport) so the agent has access to project context and tools.

---

## What the wizard does not do

- **Install Python or Node** — Install them yourself (e.g. pyenv, nvm, system package manager).
- **Install Docker** — On macOS you can install [Docker Desktop](https://www.docker.com/products/docker-desktop/) or [Colima](https://github.com/abiosoft/colima); the wizard only checks availability and builds images.
- **Flash devices** — Use the web app’s Backup / Flash tab or `esptool` on the host after setup.

---

## Troubleshooting

- **“Python 3.9+ required”** — Install a newer Python and run the wizard with that interpreter (e.g. `python3.11 scripts/install_wizard.py`).
- **“pip install failed”** — Ensure you have network access; try `pip install -r inventory/app/requirements.txt` manually inside `.venv`.
- **“build_db.py failed”** — Ensure `inventory/items/*.yaml` exist and are valid YAML; run `python inventory/scripts/build_db.py` from repo root for details.
- **Docker build fails** — Ensure Docker is running and you have enough disk space; see [docker/README.md](../docker/README.md) and [scripts/rebuild-containers.sh](../scripts/rebuild-containers.sh).

See also [docs/AGENT_SETUP_CONTEXT.md](AGENT_SETUP_CONTEXT.md) for setup wizards (paths, flash, map tiles, project planning, device config) available inside the web app.
