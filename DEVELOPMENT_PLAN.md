# Systematic Development Plan — Embedded Firmware Lab

**Purpose:** Achieve [FEATURE_ROADMAP.md](FEATURE_ROADMAP.md) in ordered phases. Stay on task via [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) and the lab MCP server.

---

## Phase 0: Hygiene & Repo (P0)

**Goal:** Repo ready for collaboration; no secrets; clear entry points.

| # | Task | Roadmap ID | Done |
|---|------|------------|------|
| 0.1 | Root README.md (purpose, quick start, link CONTEXT) | G2 | ✅ |
| 0.2 | Root .gitignore (build dirs, IDE, artifacts optional) | G3 | ✅ |
| 0.3 | LICENSE (MIT) at root | G5 | ✅ |
| 0.4 | Audit scripts/config for secrets and local paths | G4 | ✅ |

**Exit criteria:** New clone can read CONTEXT and build container; no credentials in repo.

---

## Phase 1: Lab Structure & One Device (P1)

**Goal:** T-Beam 1W fully under device contract; shared hardware knowledge in one place.

| # | Task | Roadmap ID | Done |
|---|------|------------|------|
| 1.1 | Create `shared/` and `shared/t_beam_1w/` | L12 | ✅ |
| 1.2 | Move T-Beam 1W RF/PA/fan/PMU notes to `shared/t_beam_1w/` | L12 | ✅ |
| 1.3 | Create `artifacts/` (and optionally .gitkeep or README) | L10 | ✅ |
| 1.4 | Document device layout: symlink or copy strategy for `t-beam 1w meshcore` → device firmware | L1, L3 | ✅ (migrated to devices/t_beam_1w/firmware/meshcore/repo) |
| 1.5 | Ensure `devices/t_beam_1w/` has firmware/, configs/, pinmaps/, notes/ and all context files | L2 | ✅ (already present) |
| 1.6 | Add configs examples for Companion, Repeater, Room Server under device | T8–T10 | ✅ |

**Exit criteria:** One device (t_beam_1w) satisfies contract; `shared/` is the place for hardware intelligence; `artifacts/` exists.

---

## Phase 2: Build & Test — Meshtastic T-Beam 1W (P2)

**Goal:** Meshtastic firmware builds for tbeam-1w; artifact path defined; flash from host documented.

| # | Task | Roadmap ID | Done |
|---|------|------------|------|
| 2.1 | Verify PlatformIO available (host or container) | M1 | ✅ (container) |
| 2.2 | Clone or confirm Meshtastic firmware under lab layout | M2 | ✅ |
| 2.3 | Apply variant template + platformio env; populate pins from pinmap | M3, M4 | ✅ |
| 2.4 | First successful `pio run -e tbeam-1w` (or env name) | M8 | ✅ (lab-build.sh) |
| 2.5 | Document artifact path (e.g. `.pio/build/.../firmware.bin` → `artifacts/`) | L10 | ✅ (artifacts/README.md) |
| 2.6 | scripts/flash.sh (or equivalent) for host flash with esptool | M10 | ✅ |
| 2.7 | platformio-lab Dockerfile built and documented | L5 | ✅ (Dockerfile present) |

**Exit criteria:** Meshtastic tbeam-1w build succeeds; flash procedure documented; artifacts directory used.

---

## Phase 3: Orchestrator & Scripts (P3)

**Goal:** Single entry point to build by device/firmware; toolchain detection for Cursor/scripts.

| # | Task | Roadmap ID | Done |
|---|------|------------|------|
| 3.1 | Create `orchestrator/` with minimal script: `lab build <device> <firmware>` | L9 | ✅ (scripts/lab-build.sh) |
| 3.2 | Orchestrator selects container (platformio-lab or esp-idf-lab), mounts workspace, runs build | L9 | ✅ |
| 3.3 | Orchestrator writes build output to `artifacts/<device>/<firmware>/<version>/` | L10 | ✅ |
| 3.4 | Top-level `scripts/` for build, flash, validate (or link from orchestrator) | L13 | ✅ |
| 3.5 | Toolchain detection: document or implement detection of platformio.ini, idf.py, Cargo.toml | L14 | ✅ (detect-toolchain.sh) |

**Exit criteria:** `lab build t_beam_1w meshtastic` (or similar) works; artifacts under `artifacts/`.

---

## Phase 4: CI (Optional)

**Goal:** CI builds MeshCore and Meshtastic for T-Beam 1W; no flash in CI.

| # | Task | Roadmap ID | Done |
|---|------|------------|------|
| 4.1 | CI workflow: build platformio-lab (or use prebuilt image) | G9 | ⬜ |
| 4.2 | CI: build MeshCore T-Beam 1W variants in container | G9 | ⬜ |
| 4.3 | CI: build Meshtastic tbeam-1w in container | G10 | ⬜ |
| 4.4 | Artifacts as workflow outputs; no flash step | G11 | ⬜ |

**Exit criteria:** Push triggers build; firmware binaries available as artifacts.

---

## Phase 5: Future (P4)

**Goal:** Additional containers, OTA, more devices as needed.

| # | Task | Roadmap ID | Done |
|---|------|------------|------|
| 5.1 | esp-idf-lab container (ESP-IDF, LVGL) if T-Deck Launcher or custom ESP32 | L6 | ✅ |
| 5.2 | OTA staging layout under `ota/` | L11 | ⬜ |
| 5.3 | Changelog or release notes for versioned artifacts | G8 | ⬜ |
| 5.4 | Track MeshCore upstream roadmap (MC1–MC7); update overlays as needed | §5 | ⬜ |
| 5.5 | Webapp for iOS / iPadOS / Android (PWA or wrapper: inventory, project planning, status) | L15 | ⬜ |

---

## Dependency Graph (concise)

```
Phase 0 ──► Phase 1 ──► Phase 2 ──► Phase 3 ──► Phase 4
   │            │            │            │            │
   └────────────┴────────────┴────────────┴────────────┴──► Phase 5 (parallel / future)
```

---

## How to Use This Plan

1. **Current focus:** See [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) for "current phase" and "next actions".
2. **Track progress:** Mark tasks ✅ in this file (or use MCP server / project board later).
3. **Before starting a task:** Check roadmap ID and dependency (phase order).
4. **After a task:** Update PROJECT_CONTEXT.md if the current phase or next actions change.
