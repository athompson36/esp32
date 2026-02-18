# Full Feature Roadmap — Cyber-Lab

**Repository:** Prepared for `https://github.com/athompson36/cyber-lab`  
**Context:** Cyber-Lab — unified ESP32 development environment (local-first, containerized, deterministic)  
**Last updated:** 2025-02-17

---

## 1. Executive Summary

This roadmap aligns the **embedded firmware lab** (CONTEXT.md) with current **T-Beam 1W** work (MeshCore + Meshtastic port), **MeshCore upstream** roadmap, and **repo readiness** for GitHub. Priorities: determinism, hardware safety, reproducibility, isolation, and scalability.

---

## 2. Lab Infrastructure (CONTEXT.md Alignment)

### 2.1 Directory & Contract Compliance

| ID | Feature | Status | Notes |
|----|---------|--------|--------|
| L1 | Adopt CONTEXT.md device layout under `/devices` | 🟢 Done | Root device folders migrated to `devices/` with correct naming; T-Beam 1W firmware under `devices/t_beam_1w/firmware/{meshcore,meshtastic}/repo` |
| L2 | Per-device contract: `firmware/`, `configs/`, `pinmaps/`, `notes/` | 🔴 Not started | Each device folder must have these four subdirs |
| L3 | Firmware layout: `meshtastic/`, `meshcore/`, `expresslrs/`, `custom/` under device | 🟡 Partial | MeshCore present; Meshtastic port in separate project; unify under one device |
| L4 | Overlay-only customization; no direct upstream edits | 🟢 Followed | MeshCore/Meshtastic use overlays/patches; preserve |

**Actions:**

- Create `devices/t_beam_1w/` (or `tbeam_1w`) with `firmware/`, `configs/`, `pinmaps/`, `notes/`.
- MeshCore and Meshtastic repos now live under `devices/t_beam_1w/firmware/meshcore/repo` and `firmware/meshtastic/repo`; apply overlays in `firmware/*/overlays/`.
- Move or reference Meshtastic port → `devices/t_beam_1w/firmware/meshtastic/` (repo + overlays).
- Populate `pinmaps/` from `TBEAM_1W_PINMAP.md` and variant docs; `notes/` from T-BEAM-1W-FIXES, MESHTASTIC-IMPROVEMENTS, BATTERY-FIX.

### 2.2 Containers & Toolchains

| ID | Feature | Status | Notes |
|----|---------|--------|--------|
| L5 | `platformio-lab` container (Meshtastic, MeshCore, Arduino) | 🔴 Not started | CONTEXT: never mix toolchains; build in container |
| L6 | `esp-idf-lab` container (ESP-IDF, LVGL) | 🔴 Not started | For custom/ESP-IDF-based firmware |
| L7 | `rust-embedded-lab` (PineTime, Embassy, NRF) | 🔴 Not started | Future |
| L8 | `rf-lab` (SDR, spectrum, LoRa sniffing) | 🔴 Planned | Future |

**Actions:**

- Add `docker/` with Dockerfiles for `platformio-lab` (Ubuntu 22.04 + PlatformIO), `esp-idf-lab` as needed.
- Document “build in container, flash from macOS” and avoid Docker USB passthrough unless required.

### 2.3 Build Orchestrator & Artifacts

| ID | Feature | Status | Notes |
|----|---------|--------|--------|
| L9 | `/orchestrator` — single entry point: `lab build <device> <firmware>` | 🔴 Not started | Select container, mount volumes, run build, export artifacts |
| L10 | `/artifacts` — versioned outputs: `artifacts/<device>/<firmware>/<version>/` | 🔴 Not started | Never auto-delete artifacts |
| L11 | `/ota` — staging, private channels, fleet deployments | 🔴 Planned | Future |
| L12 | `/shared` — RF tuning, PA limits, thermal, flashing offsets, board quirks | 🔴 Not started | Central place for hardware intelligence; Cursor searches here first |

**Actions:**

- Create `artifacts/`, `shared/`, optional stubs for `orchestrator/`, `ota/`.
- Implement minimal orchestrator (e.g. shell script) that invokes correct container and writes to `artifacts/`.
- Migrate T-Beam 1W RF/PA/fan/PMU notes into `shared/` (e.g. `shared/t_beam_1w/`).

### 2.4 Scripts & Toolchain Detection

| ID | Feature | Status | Notes |
|----|---------|--------|--------|
| L13 | Top-level `scripts/` for build/flash/validate | 🟡 Partial | Build/flash scripts exist under meshtastic-tbeam-1w-firmware; generalize for lab |
| L14 | Toolchain detection by presence of `platformio.ini`, `idf.py`, `Cargo.toml`, etc. | 🔴 Not started | Cursor/orchestrator must detect before suggesting commands |

### 2.5 Mobile / Companion Webapp

| ID | Feature | Status | Notes |
|----|---------|--------|--------|
| L15 | Webapp for iOS / iPadOS / Android | 🔴 Planned | PWA or native wrapper: inventory search, AI query, project planning, Docker/device status; responsive layout and installable on mobile |
| L16 | **iOS / WatchOS native app** (voice + text AI Agent chat) | 🔴 Future | Native iOS and WatchOS app with voice and text AI Agent chat; same lab context (devices, firmware, config, flash) as web app. **Prerequisite:** Web app fully tested and stable. |

---

## 3. T-Beam 1W — MeshCore (Current Implementation)

### 3.1 Hardware & Variant

| ID | Feature | Status | Notes |
|----|---------|--------|--------|
| T1 | LilyGO T-Beam 1W (ESP32-S3 + SX1262 + 1W PA) variant | 🟢 Done | `lilygo_tbeam_1w_SX1262` in meshcore |
| T2 | Single I2C bus (GPIO 8/9), PMU on Wire | 🟢 Done | T-BEAM-1W-FIXES |
| T3 | TX power cap 22 dBm, PA ramp 800 µs, smart fan 5 s post-TX | 🟢 Done | MESHTASTIC-IMPROVEMENTS, BATTERY-FIX |
| T4 | 7.4 V 2S LiPo battery range (6.0–8.4 V) | 🟢 Done | Firmware; apps may need 2S support |
| T5 | PMU (AXP2101) init order, NULL-safe battery, fallback 7400 mV | 🟢 Done | T-BEAM-1W-FIXES |
| T6 | GPS (persistent flags, skip-detect), boot screen timing | 🟢 Done | T-BEAM-1W-FIXES |
| T7 | Pinmap doc (TBEAM_1W_PINMAP.md) and variant alignment | 🟢 Done | Meshtastic pinmap filled; MeshCore pins in T-BEAM-1W-FIXES |

**Remaining:**

- Document cost-reduced variant (no AXP2101): keep fallback, document in `shared/` and device `notes/`.
- Optional: temperature-based fan, adaptive TX power, duty-cycle limit (see MESHTASTIC-IMPROVEMENTS “Future”).

### 3.2 MeshCore Firmware Variants

| ID | Feature | Status | Notes |
|----|---------|--------|--------|
| T8 | Companion Radio (BLE) — build, flash, run | 🟢 Done | UI, battery, BLE |
| T9 | Room Server — build, flash, run | 🟢 Done | BBS, serial CLI, remote mgmt |
| T10 | Repeater — build, flash, run | 🟢 Done | OLED, serial CLI |

**Actions:**

- Ensure all three are buildable via lab orchestrator and artifacts path once L9/L10 are in place.
- Add `configs/` examples for each variant under device folder.

---

## 4. T-Beam 1W — Meshtastic Port

### 4.1 Environment & Repo

| ID | Feature | Status | Notes |
|----|---------|--------|--------|
| M1 | PlatformIO installed (e.g. `brew install platformio`) | 🟡 Unknown | DEPENDENCY_CHECKLIST |
| M2 | Meshtastic firmware cloned in `firmware/` | 🟡 Unknown | meshtastic-tbeam-1w-firmware layout |
| M3 | `env:tbeam-1w` (or equivalent) in `platformio.ini` | 🟡 Template ready | patches/platformio.env.tbeam-1w.ini |
| M4 | Variant files in `firmware/variants/tbeam_1w/` (variant.h, variant.cpp) | 🟡 Template ready | DEVELOPMENT_PLAN Phase 3 |

**Actions:**

- Verify PlatformIO + clone in CI or README.
- Apply template: copy variant, merge platformio env, populate pins from TBEAM_1W_PINMAP.md (and MeshCore variant for consistency).
- Align Meshtastic variant with MeshCore pinmap (GPIO 40 power-enable, 21 RXEN, ramp, 22 dBm, fan GPIO 41).

### 4.2 Pin Mapping & Safety

| ID | Feature | Status | Notes |
|----|---------|--------|--------|
| M5 | All GPIOs documented, no placeholders | 🟢 Done | TBEAM_1W_PINMAP.md populated |
| M6 | PA/LNA (or DIO2/CTRL) and power-enable verified; no guess | 🟢 Done | Pinmap + MeshCore fixes |
| M7 | Board-specific code behind `#ifdef LILYGO_TBEAM_1W` / VARIANT_TBEAM_1W | 🟡 Pending | Ensure in Meshtastic port |

### 4.3 Build & Hardware Test

| ID | Feature | Status | Notes |
|----|---------|--------|--------|
| M8 | `pio run -e tbeam-1w` (or chosen env) succeeds | 🔴 Pending | After M1–M4 |
| M9 | Binary in `.pio/build/.../firmware.bin`; size reasonable | 🔴 Pending | |
| M10 | Flash from host (esptool); serial monitor | 🔴 Pending | scripts/flash.sh |
| M11 | Runtime: boot, SX1262 init, GPS, display, Meshtastic app discoverable | 🔴 Pending | DEVELOPMENT_PLAN Phase 7 |

**Actions:**

- Execute DEVELOPMENT_PLAN Phases 1–5 (setup, pins, template, config, first build).
- Then Phase 6 (integration points), Phase 7 (hardware test), Phase 8 (docs).

---

## 5. MeshCore Upstream Roadmap (Integration)

Items from MeshCore README “Road-Map / To-Do” that affect this lab or T-Beam 1W:

| ID | Feature | Status (upstream) | Lab action |
|----|---------|--------------------|------------|
| MC1 | Repeater/Bridge: standardise Transport Codes (zoning/filtering) | 🔴 Todo | Track; test when released |
| MC2 | Core: round-trip manual path support | 🔴 Todo | Track |
| MC3 | Companion + Apps: multiple sub-meshes, off-grid client repeat | 🔴 Todo | Track; may need app + firmware matrix |
| MC4 | Core + Apps: LZW message compression | 🔴 Todo | Track |
| MC5 | Core: dynamic CR for weak vs strong hops | 🔴 Todo | Track |
| MC6 | Core: multiple virtual nodes on one device | 🔴 Todo | Track |
| MC7 | V2 protocol: path hashes, new encryption, etc. | 🔴 Todo | Track; may affect overlays |

**Actions:**

- In `shared/` or `docs/`, keep a short “MeshCore roadmap” summary and version compatibility notes.
- When upstream adds features, re-run builds and hardware smoke tests; update overlays if needed.

---

## 6. Repo Readiness for GitHub (athompson36/cyber-lab)

### 6.1 Structure & Hygiene

| ID | Feature | Status | Notes |
|----|---------|--------|--------|
| G1 | Single root CONTEXT.md for lab philosophy and layout | 🟢 Done | |
| G2 | README.md at root: purpose, quick start, link to CONTEXT.md | 🔴 Not started | Add “Embedded Firmware Lab” README |
| G3 | .gitignore: build dirs (.pio, build, .idf), artifacts (optional), IDE | 🔴 Not started | Avoid committing build outputs and toolchain caches |
| G4 | No secrets or local paths in committed files | 🟡 Verify | Check scripts and env files |
| G5 | License file (e.g. MIT) if publishing | 🔴 Not started | Match or clarify vs Meshtastic/MeshCore |

**Actions:**

- Add root README.md (lab overview, prerequisites, “build in container, flash from host”, link to CONTEXT.md and FEATURE_ROADMAP.md).
- Add .gitignore; optionally keep `artifacts/` in git or document as optional.
- Decide whether `athompson36/cyber-lab` is the canonical lab repo; if so, document in README.

### 6.2 Device Layout and Docs

| ID | Feature | Status | Notes |
|----|---------|--------|--------|
| G6 | Devices under `devices/<name>/` with contract (L2) | 🔴 Not started | Unify T-Beam 1W under one device folder |
| G7 | FEATURE_ROADMAP.md at root (this file) | 🟢 Done | |
| G8 | Changelog or release notes (optional) | 🔴 Not started | For versioned artifacts / OTA later |

### 6.3 CI (Optional)

| ID | Feature | Status | Notes |
|----|---------|--------|--------|
| G9 | CI: build MeshCore T-Beam 1W variants in container | 🔴 Not started | platformio-lab |
| G10 | CI: build Meshtastic tbeam-1w in container | 🔴 Not started | After M8 |
| G11 | CI: no flash step (host-only); artifacts as build outputs | 🔴 Not started | |

---

## 7. Priority Overview

### P0 — Repo and safety

- G2 README, G3 .gitignore, G4 no secrets.
- M5/M6 pin safety and PA/power-enable already documented; keep enforced in both MeshCore and Meshtastic.

### P1 — Lab structure and one device

- L1/L2/L3: `devices/t_beam_1w/` with contract; move or link MeshCore + Meshtastic there; pinmaps/ and notes/.
- L12: Create `shared/` and move T-Beam 1W RF/PA/fan/PMU notes.

### P2 — Build and test

- M1–M4: PlatformIO, clone, apply Meshtastic variant, pins.
- M8–M9: First successful Meshtastic build and artifact path.
- L5: platformio-lab container and document “build in container”.
- L10: Artifact directory and orchestrator (even minimal script).

### P3 — Orchestrator and multi-device

- L9: Orchestrator entry point.
- L13/L14: Scripts and toolchain detection.
- G6/G9/G10: CI for at least T-Beam 1W (MeshCore + Meshtastic).

### P4 — Future

- L6–L8 containers, L11 OTA, G8 changelog.
- **L15** Webapp for iOS / iPadOS / Android (PWA or native wrapper: inventory, project planning, device status on mobile).
- MeshCore roadmap items MC1–MC7 as upstream lands.
- Additional devices (e.g. Heltec, T-Deck Plus) per CONTEXT.md.

---

## 8. Quick Reference

| Area | Key doc | Key location |
|------|---------|--------------|
| Lab rules | CONTEXT.md | Repo root |
| T-Beam 1W MeshCore | T-BEAM-1W-FIXES.md, MESHTASTIC-IMPROVEMENTS.md | devices/t_beam_1w/firmware/meshcore/repo/ |
| T-Beam 1W Meshtastic port | DEVELOPMENT_PLAN.md, PROJECT_CONTEXT.md, TBEAM_1W_PINMAP.md | devices/t_beam_1w/firmware/meshtastic/repo/ |
| Dependencies | DEPENDENCY_CHECKLIST.md | devices/t_beam_1w/firmware/meshtastic/repo/docs/ |
| MeshCore roadmap | README “Road-Map / To-Do” | devices/t_beam_1w/firmware/meshcore/repo/README.md |

---

## 16. Cyberdeck Manager (Unified Platform)

**Spec:** [docs/CYBERDECK_MANAGER_SPEC.md](docs/CYBERDECK_MANAGER_SPEC.md)  
**Scaffold:** [docs/cyberdeck_scaffold.md](docs/cyberdeck_scaffold.md)  
**Schema:** [scripts/schema/cyberdeck_schema.sql](scripts/schema/cyberdeck_schema.sql)  
**Device registry seeds:** [registry/devices/](registry/devices/)

The Cyberdeck Manager extends the lab into a **device + firmware + map + flash + hardware lifecycle** platform:

| Area | Status | Notes |
|------|--------|-------|
| Device registry (JSON + DB) | 🟡 Scaffold | `registry/devices/*.json`; schema `devices` table |
| Firmware registry | 🔴 Planned | GitHub metadata, compatibility mapping |
| Map manager (regions, tiles, SD) | 🔴 Planned | Region scanner, wizard, tile calculator, SD validator |
| Flash (USB + SD Launcher) | 🟡 Partial | Inventory app flash + auto-detect; add SD Launcher path |
| Hardware inspector | 🔴 Planned | Serial/BLE/USB detection, fleet snapshots |
| RF/CAN presets | 🟡 Scaffold | `registry/rf_presets.json`; CAN registry |
| Multi-user & DB | 🟡 Schema | users, flash_history, map_builds, hardware_snapshots |
| CLI (Typer) + Web (FastAPI) | 🔴 Planned | See scaffold; optional `cyberdeck_cli/`, extend or add web |
| Docker | 🟡 Reference | `docker/Dockerfile.cyberdeck`; pyproject.cyberdeck.toml |

---

## 17. PCB & 3D Design Stack (AI, Export, Maker Upload)

**Spec:** [docs/PCB_3D_DESIGN_STACK_SPEC.md](docs/PCB_3D_DESIGN_STACK_SPEC.md)

Full AI-aware PCB and 3D-printing design stack: dimension-aware part mock-ups, AI-optimized enclosures, simple 3D preview, export in common formats, optional upload to maker sites with account syncing.

| Area | Status | Notes |
|------|--------|-------|
| Part dimensions in catalog | 🔴 Planned | specs: length_mm, width_mm, height_mm, footprint, mounting; optional model_3d_url (see spec §2.1). |
| Design placements & enclosure_params | 🔴 Planned | Extend project DESIGN with placements (x,y,z, ref_des), enclosure_params (box, cutouts); AI suggests from BOM + dimensions + use case. |
| AI context (dimensions + use case) | 🔴 Planned | Inject part dimensions into project planning prompt; AI outputs structured placements and enclosure; extend DESIGN block. |
| Simple 3D viewer (parts + enclosure) | 🔴 Planned | Primitive-based (boxes from dimensions) in project planning UI; Three.js or equivalent; phase 2. |
| Export: enclosure STL/STEP/3MF/OBJ | 🔴 Planned | Parametric → script (OpenSCAD/FreeCAD) → STL/STEP; API + UI “Export as”. |
| Export: PCB Gerber/ODB++/netlist | 🔴 Planned | Via KiCad or script from netlist + placements; API + UI. |
| Maker site upload + account sync | 🔴 Planned | JLCPCB, PCBWay, OSHPark (PCB); Printables, Thingiverse, Thangs (3D); store tokens, project/revision links (spec §6). |

Phases: (1) Data & AI, (2) 3D preview, (3) Export formats, (4) Maker upload. See spec for API and artifact paths.

---

**Prepared for:** `https://github.com/athompson36/cyber-lab`  
*(Note: If the repo is private or not yet created, create it and push this lab; use this roadmap as the initial backlog.)*
