# Changelog

Notable changes to the Cyber-Lab repo. Versioned artifacts live under `artifacts/<device>/<firmware>/<date>/`; this file tracks lab infrastructure and device/firmware support.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Lab uses calendar versioning for artifact dirs (e.g. `2026-02-17`).

---

## [Unreleased]

- **MeshCore T-Beam 1W boot fix:** Lab build now runs the `mergebin` target for MeshCore so artifacts include a full flash image (bootloader + partitions + boot_app0 + app). Flashing only `firmware.bin` at 0x10000 causes no-boot; use `firmware.factory.bin` at 0x0 (script does this automatically). See `devices/.../meshcore/repo/webflasher/README.md`.
- **MeshCore board config:** `boards/t_beam_1w.json` updated to **flash_mode: qio** and **flash_size: 16MB** (was dio / 4MB); wrong mode/size can prevent boot on T-Beam 1W.
- **Flash script:** `ERASE=1 ./scripts/flash.sh ...` erases flash before writing (fixes many no-boot cases). Troubleshooting: `devices/t_beam_1w/notes/T_BEAM_NO_BOOT.md`.
- **MeshCore merge:** `merge-bin.py` now **always injects boot_app0 at 0xe000** from the Arduino-ESP32 framework; the platform’s FLASH_EXTRA_IMAGES may omit it, which causes no-boot after flash.
- **Docker:** Pinned pip versions in platformio-lab image for reproducible builds: platformio 6.1.19, esptool 4.11.0 (from GitHub), pyserial 3.5 (see docker/Dockerfile and docker/DEPENDENCIES.md).
- Runtime hardware test checklist for T-Beam 1W (M11): boot, SX1262, GPS, display, Meshtastic app discoverable.

---

## 2026-02-17

### Added

- **Scripts:** `scripts/detect-toolchain.sh [path]` — detects platformio / idf / cargo for build suggestions (L14).
- **CI:** GitHub Actions workflow `build-tbeam1w.yml` — build MeshCore and Meshtastic for T-Beam 1W in `platformio-lab` container; upload artifacts only, no flash (G9, G10, G11).
- **Changelog:** This file (G8).

### Changed

- **Meshtastic T-Beam 1W:** `variants/esp32s3/t-beam-1w/variant.h` — added `VARIANT_TBEAM_1W` and comment documenting guards `LILYGO_TBEAM_1W`, `T_BEAM_1W`, `VARIANT_TBEAM_1W` for board-specific code (M7).

### Fixed

- (None this release.)

---

## Earlier

- **Lab structure:** CONTEXT.md, devices contract (firmware/configs/pinmaps/notes), shared/t_beam_1w (RF_PA_FAN_PMU.md).
- **Containers:** platformio-lab Docker image (mklittlefs, build in container).
- **Orchestrator:** scripts/lab-build.sh, scripts/flash.sh; artifacts layout.
- **Meshtastic port:** t-beam-1w env, variant, first build and artifacts; flash from host.
- **Repo:** README, .gitignore, LICENSE (MIT), FEATURE_ROADMAP.md; no secrets in repo.
- **Inventory app:** backup/restore/flash with friendly port-busy messages; datasheet upload and design-context generation.
