# Project Context — Single Source of Truth

**Role:** Keep development straight and on task. Read this first (and use the lab MCP server) when resuming work or when an assistant needs to align with the roadmap.

---

## 1. What This Repo Is

- **Embedded firmware lab** — Multi-device, multi-firmware layout with a strict contract (see [CONTEXT.md](CONTEXT.md)).
- **Build in container, flash from host** — Deterministic builds; USB/serial on macOS.
- **Current primary device:** T-Beam 1W (MeshCore ✅; Meshtastic port in progress).

---

## 2. Current Phase

**Phase:** **2 — Build & test (Meshtastic T-Beam 1W) (P2)** — complete (M11 Done 2026-02-23)

**Goal:** Meshtastic tbeam-1w build, flash, and runtime validated on real T-Beam 1W.

**Next actions (in order):**

1. Pick next roadmap item: future containers (L6–L8), MeshCore upstream tracking (MC1–MC7), or other P4 items. See FEATURE_ROADMAP.md §7–§8.

---

## 3. Roadmap Priorities (from FEATURE_ROADMAP)

| Priority | Focus | Status |
|----------|--------|--------|
| **P0** | Repo hygiene, README, .gitignore, no secrets | Done (Phase 0) |
| **P1** | Lab structure, one device (t_beam_1w), shared/, artifacts/ | Done (Phase 1 complete) |
| **P2** | Meshtastic tbeam-1w build, artifact path, flash script | Done (M11 runtime test passed 2026-02-23) |
| **P3** | Orchestrator, scripts, toolchain detection | Not started |
| **P4** | CI, extra containers, OTA, changelog | Future |

---

## 4. Key Documents

| Doc | Use when |
|-----|----------|
| [CONTEXT.md](CONTEXT.md) | Understanding lab rules, device contract, containers. |
| [FEATURE_ROADMAP.md](FEATURE_ROADMAP.md) | Full backlog and roadmap items (L1–L15, G1–G11, T1–MC7). |
| [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md) | Phased task list; what to do in order. |
| **PROJECT_CONTEXT.md** (this file) | Current phase, next actions, how to stay on task. |
| [current_project.md](current_project.md) | Cyber-Lab project ideas (ESP32/SBC) and lab context links. |
| [docker/TOOLS_AND_SDK.md](docker/TOOLS_AND_SDK.md) | SDKs and tools per device. |

---

## 5. How to Stay on Task

1. **Start here:** Read "Current Phase" and "Next actions" above (or ask the MCP server for `get_next_tasks`).
2. **Pick one task:** Take the next uncompleted item from DEVELOPMENT_PLAN for the current phase.
3. **Check contract:** If the task touches devices, ensure `firmware/`, `configs/`, `pinmaps/`, `notes/` and context files are respected (CONTEXT.md).
4. **Build in container:** Use `platformio-lab` for builds; flash from host.
5. **Update when done:** Mark the task ✅ in DEVELOPMENT_PLAN.md; if the phase is complete, update "Current Phase" and "Next actions" in this file.

---

## 6. MCP Server (Lab Context)

The **lab MCP server** exposes project context, roadmap summary, setup wizards, and tools so assistants can stay aligned.

- **Resources:** `project://context`, `project://roadmap`, `project://development-plan`, `project://setup-context` (wizards and acceptability)
- **Tools:** `get_project_status`, `get_next_tasks`, `get_device_context`, `list_devices`, `get_setup_help`

Use **get_setup_help** or read **project://setup-context** when the user asks for setup recommendations or chat-style setup. See [docs/AGENT_SETUP_CONTEXT.md](docs/AGENT_SETUP_CONTEXT.md).

See [mcp-server/README.md](mcp-server/README.md) for setup and Cursor configuration.

---

## 7. Last Updated

- **Phase / next actions:** Phase 2 complete. M11 Done 2026-02-23 (Meshtastic boots; DIO flash fix in scripts/flash.sh).
- **Review:** Update "Current Phase" and "Next actions" when a phase completes or focus shifts.
