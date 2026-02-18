# Cyberdeck Manager — Features Specification & Implementation Map

**Version:** 1.0  
**Scope:** Device Registry, Firmware Registry, Map Manager, Flash System, Hardware Inspector, RF/CAN, CAD Automation  
**Target:** Linux (Dockerized), CLI + Web UI  
**Repo alignment:** This doc maps the spec to the existing Cyber-Lab layout (`devices/`, `inventory/`, `artifacts/`, `docker/`).

---

## 1. Overview

Cyberdeck Manager extends the lab into a unified **Device + Firmware + RF + CAN + Map + Flash + Hardware Lifecycle** platform.

| Spec Section | Repo / Implementation |
|--------------|------------------------|
| Map Management | New: `regions/`, `scripts/map_wizard.py`, Web: Map Manager tab |
| Device Registry | `registry/devices/{id}.json` + DB `devices` table; aligns with `devices/*/DEVICE_CONTEXT.md` |
| Firmware Registry | `registry/firmware/`, GitHub metadata; aligns with `FIRMWARE_INDEX.md`, `BUILD_CONFIG` |
| Flash System | Extend `inventory/app` flash_ops + new Flash Wizard; SD Launcher under `scripts/sd_launcher/` |
| Hardware Inspector | New service: serial/BLE/USB detection; DB `hardware_snapshots` |
| RF/CAN | `registry/rf_presets.json`, `registry/can_firmware/`; configs in `devices/*/configs/` |
| Multi-user | DB `users`, RBAC; optional auth in FastAPI/Flask |
| CAD/AI PCB & 3D | Extend project planning pinouts/wiring/schematic/enclosure; KiCad/SKiDL/OpenSCAD scripts |
| CLI + Web | Typer CLI in `cyberdeck_cli/` or `scripts/cli/`; Web: extend inventory app or FastAPI service |

---

## 2. Map Management

- **Region scanner:** Scan `/regions/` for states, cities, bounding boxes, zoom levels, tile counts.
- **Map wizard (CLI + Web):** Select region → zoom range → tile count & size → SD compliance → folder structure.
- **Tile size calculator:** Total tiles × avg size → GB; SD capacity comparison; over-limit warnings.
- **SD structure validator:** FAT32, 32KB cluster, root folders, tile path format, PNG presence.

**Scaffold:** `regions/`, `scripts/map_wizard.py`, `scripts/sd_validator.py`, Web route `/map`.

---

## 3. Device Registry

- **Profile:** JSON per device at `registry/devices/{device_id}.json`: MCU, radios, display, battery, storage, flash methods, compatible firmware.
- **Initial set:** Heltec T114 v3/v4, MeshPocket 10000mAh, T-Deck, T-Deck Plus, T-Beam, RPi 5, RockPro64 (align with existing `devices/`).
- **Capability matrix:** MCU, RF bands, CAN, SD, Launcher, flash methods, secure element — drives Flash UI and compatibility.

**Scaffold:** `registry/devices/*.json`; DB table `devices`; sync with `devices/*/DEVICE_CONTEXT.md`.

---

## 4. Firmware Registry

- **Metadata:** GitHub repos, releases, branches, `platformio.ini`, README, supported boards.
- **Types:** Meshtastic, MeshCore, Launcher, Bruce, Ghost, custom forks.
- **Compatibility:** Supported devices, build targets, latest release, flash method, partition scheme.
- **Forks:** `registry/forks/{device_id}/{fork_name}/` — upstream, patches, build flags.

**Scaffold:** `registry/firmware/`, `scripts/firmware_metadata.py`; DB `firmware`, `forks`; align with `inventory/app/config.BUILD_CONFIG`.

---

## 5. Flash System

- **Dual methods:** (A) USB direct — esptool/platformio/idf.py, serial detection, chip validation; (B) SD Launcher — manifest, FAT32 structure, version metadata.
- **Flash wizard:** Device → Firmware → Detect hardware → Method → Validate → Flash / Prepare SD → Log.
- **History:** User, device, firmware, method, timestamp, success/failure (audit/fleet).

**Scaffold:** Extend `inventory/app/flash_ops.py` and Flash UI; add `scripts/sd_launcher/`; DB `flash_history`.

---

## 6. Hardware Inspector

- **Components:** MCU, radio, bootloader, app firmware, SD firmware, CAN, secure element.
- **Detection:** Serial, BLE, USB VID/PID, file inspection, SSH (SBC).
- **Update panel:** Component | Current | Latest | Status (up-to-date / update available / unknown).
- **Fleet snapshots:** Historical firmware states, ownership, compliance.

**Scaffold:** `scripts/hardware_inspector/` or service; DB `hardware_snapshots`.

---

## 7. RF & CAN

- **RF presets:** USA, EU, custom; bands, TX limits, channel spacing, warnings.
- **Enforcement:** From device capability matrix; restrict bands, warn illegal TX.
- **CAN registry:** CAN firmware, bitrate, bus modes, injection, safety; listen-only default, bitrate presets.

**Scaffold:** `registry/rf_presets.json`, `registry/can_firmware/`; DB `rf_presets`; configs in `devices/*/configs/`.

---

## 8. Multi-User & DB

- **Roles:** Admin, Standard User, Viewer.
- **Tables:** users, devices, firmware, forks, flash_history, map_builds, rf_presets, hardware_snapshots.
- **RBAC, audit, device ownership.**

**Scaffold:** `scripts/schema/cyberdeck_schema.sql`; auth in FastAPI or Flask.

---

## 9. Docker & Stack

- **Image:** Python, Git, esptool, platformio, CAN tools, GitHub client, map tools.
- **Mounts:** devices, forks, regions, DB volume.
- **Reproducible builds.**

**Scaffold:** `docker/Dockerfile.cyberdeck`, `docker-compose.cyberdeck.yml` (optional).

---

## 10. AI PCB & 3D (Integration)

**Full spec:** [PCB_3D_DESIGN_STACK_SPEC.md](PCB_3D_DESIGN_STACK_SPEC.md) — dimension-aware parts, AI enclosure suggestions, 3D preview, export formats (Gerber, STL, STEP, 3MF), maker site upload with account sync.

- **PCB:** KiCad, SKiDL, FreeRouting, Ngspice; generate schematic, footprints, route, DRC, Gerbers, BOM.
- **BOM:** DigiKey/Mouser API, MPN, price, stock (align with inventory app BOM export).
- **3D:** OpenSCAD, FreeCAD, STEP; STL/STEP/3MF (align with project planning enclosure export).
- **AI:** Access to full PCB and 3D stacks; mock-ups from part dimensions and placement; AI-optimized enclosures from project docs and use case; simple 3D model display; export in common formats; upload to JLCPCB, PCBWay, Printables, Thingiverse, etc. with account syncing.

**Scaffold:** Extend `inventory/app` project planning; optional `scripts/cad/` for KiCad/OpenSCAD automation.

---

## 11. CLI + Web

- **CLI (Typer + Rich):** device wizard, firmware wizard, map wizard, flash, hardware inspect.
- **Web:** FastAPI or extend Flask app: dashboard, devices, firmware, map manager, hardware inspector, flash console.

**Scaffold:** `cyberdeck_cli/` or `scripts/cli/`; optional `cyberdeck_web/` FastAPI app or extend `inventory/app`.

---

## 12. Reference Files in This Repo

| Artifact | Path |
|----------|------|
| This spec | `docs/CYBERDECK_MANAGER_SPEC.md` |
| Directory scaffold | `docs/cyberdeck_scaffold.md` |
| Database schema | `scripts/schema/cyberdeck_schema.sql` |
| Device JSON seeds | `registry/devices/*.json` |
| FEATURE_ROADMAP (lab) | `FEATURE_ROADMAP.md` |
| Device contract | `devices/README.md` |
| Inventory + Flash UI | `inventory/app/` |
| Build config | `inventory/app/config.py` (BUILD_CONFIG, FLASH_DEVICES) |

---

## 13. Future Expansion

OTA deployment, SDR registry, CAN DBC, RF heatmaps, automated build pipelines, CI, fleet provisioning — noted in schema and scaffold for extension.
