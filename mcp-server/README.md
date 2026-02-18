# Cyber-Lab MCP Server

MCP server that exposes **project context**, **roadmap**, **development plan**, and **device context**, **inventory**, and **firmware index** so assistants (e.g. Cursor) can stay aligned with the repo’s goals and tasks.

## Resources

| URI | Description |
|-----|-------------|
| `project://context` | [PROJECT_CONTEXT.md](../PROJECT_CONTEXT.md) — current phase, next actions, priorities |
| `project://roadmap` | [FEATURE_ROADMAP.md](../FEATURE_ROADMAP.md) — full roadmap |
| `project://development-plan` | [DEVELOPMENT_PLAN.md](../DEVELOPMENT_PLAN.md) — phased tasks |
| `project://lab-context` | [CONTEXT.md](../CONTEXT.md) — lab rules and device contract |
| `project://inventory` | [inventory/README.md](../inventory/README.md) — hardware catalog (SBCs, controllers, sensors, components) |
| `project://firmware-index` | [FIRMWARE_INDEX.md](../FIRMWARE_INDEX.md) — firmware and OS per device |
| `project://repos` | [REPOS.md](../REPOS.md) — lab repo index (Meshtastic, MeshCore, Launcher, etc.) |
| `project://setup-context` | [docs/AGENT_SETUP_CONTEXT.md](../docs/AGENT_SETUP_CONTEXT.md) — setup wizards and acceptability (agent setup help) |
| `project://database-context` | [docs/AGENT_DATABASE_CONTEXT.md](../docs/AGENT_DATABASE_CONTEXT.md) — database handling (inventory DB, project proposals) |
| `project://backend-context` | [docs/AGENT_BACKEND_CONTEXT.md](../docs/AGENT_BACKEND_CONTEXT.md) — Flask routes, services, config |
| `project://docker-context` | [docs/AGENT_DOCKER_CONTEXT.md](../docs/AGENT_DOCKER_CONTEXT.md) — Docker status, containers, start/stop, images |
| `project://frontend-context` | [docs/AGENT_FRONTEND_CONTEXT.md](../docs/AGENT_FRONTEND_CONTEXT.md) — frontend tabs, panels, UI guidance |

## Tools

| Tool | Description |
|------|-------------|
| `get_project_status` | Returns current phase, next actions, and priority focus (PROJECT_CONTEXT.md). Use to stay on task. |
| `get_next_tasks` | Returns next uncompleted tasks from DEVELOPMENT_PLAN.md for the current phase. |
| `get_device_context` | Returns device context and SDK/tools for a given device (`device_id`, e.g. `t_beam_1w`, `t_deck_plus`). |
| `list_devices` | Lists all device IDs under `devices/`. |
| `get_inventory_summary` | Returns inventory README and list of catalog categories (sbcs, controllers, sensors, accessories, components). |
| `get_setup_help` | Returns setup context and wizard summary. Use when the user asks for setup recommendations, how to configure something, or chat-style setup with explanations. |
| `get_lab_guidance` | Returns context for database, backend, Docker, or frontend. Optional `area`: `database` \| `backend` \| `docker` \| `frontend` (omit for all four). Use when the user asks about DB handling, API/services, Docker status/containers, or UI/tabs. |

## Build & run (local)

- **Prereqs:** Node.js ≥18, `npm install` in this directory.
- **Build:** `npm run build`
- **Run (stdio):** `node dist/index.js` — intended to be spawned by an MCP client (e.g. Cursor); reads repo files relative to current working directory.

**Repo root:** By default the server uses `process.cwd()` as the repo root. To override (e.g. when Cursor runs from a different cwd), set `CYBER_LAB_REPO_ROOT` to the absolute path of the repo.

## Run with Docker

The server runs over **stdio** (no HTTP). Use Docker so the same image runs everywhere; mount the repo so the server can read project context, devices, and inventory.

**Build the image** (from repo root):

```bash
docker compose -f mcp-server/docker-compose.yml build
```

Or: `docker build -t cyber-lab-mcp -f mcp-server/Dockerfile mcp-server`

**Test** (from repo root): `docker compose -f mcp-server/docker-compose.yml run --rm -v "$(pwd)":/workspace -e CYBER_LAB_REPO_ROOT=/workspace mcp`

Use **Cursor** with the Docker command so it spawns the container and talks over stdio (see Cursor configuration below).

## Cursor configuration

Add the lab MCP server in Cursor so it can call tools and read resources.

1. Open **Cursor Settings → MCP** (or edit the MCP config file directly).
2. Choose one option (replace `REPO_ROOT` with your **absolute** repo path, e.g. `/Users/andrew/Documents/fs-tech/cyber-lab`):

**Option A — Docker (recommended)**

```json
{
  "mcpServers": {
    "cyber-lab": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-v", "REPO_ROOT:/workspace:ro",
        "-e", "CYBER_LAB_REPO_ROOT=/workspace",
        "cyber-lab-mcp"
      ]
    }
  }
}
```

Build the image first (see "Run with Docker" above).

**Option B — Node (local)**

```json
{
  "mcpServers": {
    "cyber-lab": {
      "command": "node",
      "args": ["REPO_ROOT/mcp-server/dist/index.js"],
      "cwd": "REPO_ROOT",
      "env": {}
    }
  }
}
```

**Option C — Example file**

- Node: [cursor-mcp-example.json](cursor-mcp-example.json)
- Docker: [cursor-mcp-example-docker.json](cursor-mcp-example-docker.json) — replace `/ABSOLUTE/PATH/TO/cyber-lab` with your repo path, then merge into your Cursor MCP config.

3. Restart Cursor or reload MCP so the server is available.

**If the server will not start:**

- **Docker:** Ensure the image is built: `docker compose -f mcp-server/docker-compose.yml build` (from repo root). In Cursor MCP config, replace `REPO_ROOT` with your **absolute** repo path (e.g. `/Users/you/Documents/fs-tech/cyber-lab`).
- **Node (local):** Use the **absolute** path to `mcp-server/dist/index.js` in `args`, and set `cwd` to the **repo root** (so `CYBER_LAB_REPO_ROOT` can be omitted, or set it to the same path). Run `npm run build` inside `mcp-server/` so `dist/` exists.
- Check Cursor’s MCP / Developer logs for stderr: a successful start prints `[cyber-lab-mcp] Server running on stdio (repo: ...)`; failures print `[cyber-lab-mcp] Fatal: ...`.

After that you can:
- Use **Resources** to open project context, roadmap, development plan, inventory, firmware index, or repos.
- Use **Tools** (e.g. `get_project_status`, `get_next_tasks`, `get_device_context`, `list_devices`, `get_inventory_summary`) in agent/chats to stay on task.

## License

Same as the repo (MIT). See [../LICENSE](../LICENSE).
