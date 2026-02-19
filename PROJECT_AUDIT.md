# Full Project Audit — Cyber-Lab (ESP32)

**Date:** 2026-02-17  
**Scope:** Structure, CONTEXT.md alignment, FEATURE_ROADMAP, devices, firmware, Docker, inventory, docs, and repo hygiene.

---

## 1. Executive Summary

| Area | Status | Summary |
|------|--------|--------|
| **Repo identity** | ⚠️ Inconsistent | Pushed as `athompson36/esp32`; docs/roadmap reference `cyber-lab` |
| **CONTEXT.md alignment** | 🟡 Partial | Device contract met for sampled devices; orchestrator missing; shared/ present |
| **Device contract** | 🟢 Compliant | t_beam_1w, t_deck_plus, heltec_t114_v4, teensy_v4 have firmware/, configs/, pinmaps/, notes/ |
| **Firmware strategy** | 🟢 Good | Submodules for MeshCore + Meshtastic; lab overlays as patches; apply script and README |
| **Docker** | 🟢 Present | platformio-lab Dockerfile; README, TOOLS_AND_SDK, DEPENDENCIES |
| **Orchestrator** | 🔴 Missing | No `/orchestrator`; CONTEXT expects `lab build <device> <firmware>` |
| **Artifacts** | 🟡 Stub | `artifacts/` exists (path_settings, backups, project_proposals, map_tiles); .gitignore excludes most |
| **Shared** | 🟢 Present | `shared/t_beam_1w/` with RF_PA_FAN_PMU.md; README |
| **README & license** | 🟢 Good | Root README, LICENSE (MIT), quick start, key docs |
| **.gitignore** | 🟢 Good | .pio, build, .idf, .venv, artifacts/, tiles_*, secrets; legacy paths listed |
| **Inventory app** | 🟢 Present | Flask app, BUILD_CONFIG in config.py; Meshtastic build path may need fix |
| **Docs** | 🟢 Good | CONTEXT, FEATURE_ROADMAP, PROJECT_STRUCTURE, INSTALL, agent context files |

---

## 2. Repo and Documentation Consistency

### 2.1 Repo URL and naming

- **Actual remote:** `https://github.com/athompson36/esp32.git`
- **FEATURE_ROADMAP.md** and footer say: “Prepared for `https://github.com/athompson36/cyber-lab`” and “athompson36/cyber-lab”.
- **CONTEXT.md** and **PROJECT_STRUCTURE.md** use directory name `cyber-lab/` in examples.

**Recommendation:** Either rename GitHub repo to `cyber-lab` and update README, or update FEATURE_ROADMAP (and any other docs) to `athompson36/esp32` as the canonical lab repo.

### 2.2 config.BUILD_CONFIG reference

- **devices/t_beam_1w/firmware/README.md** says: “see `inventory/app/config.BUILD_CONFIG`”.
- **Reality:** BUILD_CONFIG is a variable in `inventory/app/config.py`, not a file `config.BUILD_CONFIG`.

**Recommendation:** Change to “see `inventory/app/config.py` (BUILD_CONFIG)” or “see `docs/AGENT_BACKEND_CONTEXT.md`”.

---

## 3. CONTEXT.md Alignment

### 3.1 Directory layout (CONTEXT § Top-Level Architecture)

| Expected | Present | Notes |
|----------|---------|--------|
| docker/ | ✅ | Dockerfile, Dockerfile.cyberdeck, README, TOOLS_AND_SDK, DEPENDENCIES |
| orchestrator/ | ❌ | Missing |
| scripts/ | ✅ | install_wizard, map_tiles, schema, rebuild-containers, etc. |
| toolchains/ | ❌ | Not present (toolchains documented in docker/ and device notes) |
| shared/ | ✅ | shared/t_beam_1w/, README |
| artifacts/ | ✅ | path_settings, backups, project_proposals, map_tiles; .gitignore excludes most |
| inventory/ | ✅ | app, items, scripts, datasheets, SCHEMA |
| ota/ | ❌ | Planned in CONTEXT; not created |
| datasets/ | ❌ | Not at top level (map data under artifacts/, tiles_*, regions/) |
| devices/ | ✅ | Multiple devices with contract |
| experimental/ | ❌ | Not present |
| legacy/ | ❌ | Not present |

### 3.2 Device folder contract (CONTEXT § Device Folder Contract)

Sampled devices all have the four required dirs:

- **t_beam_1w:** firmware/, configs/, pinmaps/, notes/ ✅  
- **t_deck_plus:** firmware/, configs/, pinmaps/, notes/ ✅  
- **heltec_t114_v4:** firmware/, configs/, pinmaps/, notes/ ✅  
- **teensy_v4:** firmware/, configs/, pinmaps/, notes/ ✅  

### 3.3 Firmware layout and overlay rules

- **t_beam_1w:**  
  - `firmware/meshcore/repo` → submodule (MeshCore).  
  - `firmware/meshtastic/repo` → lab-owned scripts, patches, docs; `repo/firmware` → submodule (Meshtastic).  
- Overlay-only: lab changes in `meshtastic/repo/patches/` (e.g. 001-tdeck-trackball-calibration.patch) and `scripts/apply_lab_patches.sh`; upstream not edited in tree ✅  
- Clone workflow: `git submodule update --init --recursive` then optional `apply_lab_patches.sh` ✅  

### 3.4 Containers and toolchain detection

- **platformio-lab:** Dockerfile present (Ubuntu 22.04, PlatformIO, esptool, pyserial).  
- **esp-idf-lab / rust-embedded-lab / rf-lab:** Not present (roadmap/future).  
- Toolchain detection by `platformio.ini` / `idf.py` / `Cargo.toml`: not implemented in a single “detector”; scripts and docs assume PlatformIO for current device.

### 3.5 Orchestrator and artifacts

- **Orchestrator:** No `orchestrator/` directory. CONTEXT expects something like `lab build <device> <firmware>`.  
- **Artifacts:** Directory exists; structure `artifacts/<device>/<firmware>/<version>/` not enforced. path_settings.json, backups, project_proposals, map_tiles present.  
- **Artifacts in .gitignore:** `artifacts/` is ignored except `!artifacts/README.md`; README may need to exist if you want that exception to apply.

---

## 4. Build Config and Paths

### 4.1 BUILD_CONFIG (inventory/app/config.py)

- **t_beam_1w / meshcore:**  
  - path: `devices/t_beam_1w/firmware/meshcore/repo`  
  - platformio.ini at repo root ✅  
- **t_beam_1w / meshtastic:**  
  - path: `devices/t_beam_1w/firmware/meshtastic/repo`  
  - Actual PlatformIO project (platformio.ini) is in **repo/firmware**, and `scripts/build.sh` does `cd "$ROOT/firmware"` then `pio run -e tbeam-1w`.

So for Meshtastic, the build working directory should be `devices/t_beam_1w/firmware/meshtastic/repo/firmware`, not `repo`. If the inventory app (or any script) runs `pio run -e tbeam-1w` with `-w /workspace/devices/t_beam_1w/firmware/meshtastic/repo`, the build will fail.

**Recommendation:** Set meshtastic path in BUILD_CONFIG to `devices/t_beam_1w/firmware/meshtastic/repo/firmware`, or document that “path” is the repo root and the app must run pio from `path/firmware` for meshtastic.

---

## 5. Submodules and Clone Workflow

- **.gitmodules:**  
  - `devices/t_beam_1w/firmware/meshtastic/repo/firmware` → meshtastic/firmware  
  - `devices/t_beam_1w/firmware/meshcore/repo` → meshcore-dev/MeshCore  
- **Clone:** `git clone --recurse-submodules` or `git submodule update --init --recursive` ✅  
- **Lab patches:** `devices/t_beam_1w/firmware/meshtastic/repo/scripts/apply_lab_patches.sh` ✅  
- **Docs:** READMEs under firmware/ and meshtastic/repo describe submodule + apply flow ✅  

---

## 6. FEATURE_ROADMAP vs Current State

- **L2 (per-device contract):** Implemented for sampled devices ✅  
- **L3 (firmware layout):** t_beam_1w has meshcore + meshtastic under one device ✅  
- **L5 (platformio-lab):** Docker image present ✅  
- **L9 (orchestrator):** Not started ❌  
- **L10 (artifacts versioned):** Directory present; versioned layout not implemented ❌  
- **L12 (shared/):** Present with t_beam_1w RF/PA/fan/PMU notes ✅  
- **G2 (root README):** Done ✅  
- **G3 (.gitignore):** Done ✅  
- **G4 (no secrets):** .gitignore has secrets/, .env; worth a quick scan for accidental commits.  
- **G5 (license):** LICENSE (MIT) at root ✅  
- **G6 (devices under devices/ with contract):** Done for key devices ✅  

Update FEATURE_ROADMAP “Last updated” and status cells where appropriate (e.g. L2, L3, G2, G3, G5, G6).

---

## 7. Security and Hygiene

- **Secrets:** .gitignore includes `.env`, `.env.*`, `secrets/`, `*.local`.  
- **Build outputs:** .pio, build, .idf, *.bin, etc. ignored ✅  
- **Large data:** artifacts/, tiles_* ignored; CONTEXT says map datasets may be large and must not be deleted/compressed without approval.  

No automated scan was run; recommend an occasional `git log -p` or secret scan on staged files.

---

## 8. Inventory App and MCP

- **Inventory:** Flask app in `inventory/app/`, Dockerfile and docker-compose, REPO_ROOT and BUILD_CONFIG in config.py.  
- **MCP:** mcp-server (TypeScript), docker-compose, Cursor MCP docs; image name `cyber-lab-mcp` in docs.  
- **rebuild-containers.sh:** Rebuilds inventory app and MCP server images ✅  

---

## 9. Recommendations (Priority Order)

1. **Fix Meshtastic build path** in `inventory/app/config.py`: set meshtastic path to `devices/t_beam_1w/firmware/meshtastic/repo/firmware` (or implement logic to run pio from `path/firmware` for meshtastic).
2. **Align repo name in docs:** Decide canonical repo (esp32 vs cyber-lab) and update FEATURE_ROADMAP.md, CONTEXT.md examples, and README if needed.
3. **Fix README reference:** In `devices/t_beam_1w/firmware/README.md`, change “config.BUILD_CONFIG” to “config.py (BUILD_CONFIG)”.
4. **Orchestrator stub:** Add `orchestrator/` with a minimal script (e.g. `lab build <device> <firmware>`) that uses BUILD_CONFIG and platformio-lab (or document “orchestrator planned” in CONTEXT/FEATURE_ROADMAP).
5. **Artifacts README:** Add `artifacts/README.md` if you want it tracked while rest of artifacts/ is gitignored.
6. **FEATURE_ROADMAP:** Refresh “Last updated” and status for L2, L3, L5, L12, G2, G3, G5, G6.

---

## 10. File and Directory Summary

| Path | Purpose |
|------|--------|
| CONTEXT.md | Lab philosophy, device contract, containers, rules |
| README.md | Quick start, key docs, clone/build/flash |
| LICENSE | MIT, lab structure and docs |
| .gitignore | Build dirs, venv, artifacts, tiles, secrets |
| .gitmodules | Meshtastic + MeshCore submodules |
| FEATURE_ROADMAP.md | Lab and device roadmap (update repo URL and status) |
| PROJECT_STRUCTURE.md | Layout, stacks, dependencies |
| current_project.md | ESP32/SBC project list |
| devices/ | Per-device firmware, configs, pinmaps, notes |
| docker/ | platformio-lab, cyberdeck Dockerfile, docs |
| inventory/ | Catalog (YAML, SQLite), Flask app, device wizard |
| mcp-server/ | MCP server for Cursor |
| scripts/ | install_wizard, map_tiles, schema, rebuild-containers |
| shared/ | RF/PA/fan/PMU and board notes (e.g. t_beam_1w) |
| artifacts/ | path_settings, backups, project_proposals, map_tiles (mostly gitignored) |
| docs/ | Specs, INSTALL, agent context |
| regions/ | Region definitions for maps |
| registry/ | Device registry scaffold |

---

*End of audit.*
