# Lumari Watch — Firmware

**Source:** [github.com/athompson36/lumari_watch](https://github.com/athompson36/lumari_watch)

**Toolchain:** ESP-IDF v5.x · target **esp32s3** · 8MB PSRAM

## Clone (lab layout)

From repo root:

```bash
git clone https://github.com/athompson36/lumari_watch.git devices/lumari_watch/firmware/lumari_watch/repo
```

Or add as submodule:

```bash
git submodule add https://github.com/athompson36/lumari_watch.git devices/lumari_watch/firmware/lumari_watch/repo
```

## Build & flash

From `devices/lumari_watch/firmware/lumari_watch/repo/` (or from repo root with `-C` to that path):

```bash
# Set up ESP-IDF (e.g. source $IDF_PATH/export.sh)
idf.py set-target esp32s3
idf.py build
idf.py -p /dev/cu.usbmodem* flash monitor
```

**Blank screen after flash:** Release BOOT, then press Reset (or PWR) once. See source repo [README](https://github.com/athompson36/lumari_watch#build-and-run) and `docs/WAVESHARE_FACTORY_AND_TROUBLESHOOTING.md`.

Dependencies (CO5300, QMI8658) are pulled via IDF component manager (`idf_component.yml` in components). One-shot deps install: `./scripts/install_dependencies.sh` (see `docs/DEPENDENCIES.md`).

## Artifacts

Build outputs live in `repo/build/`. To publish lab artifacts, copy `build/*.bin` (or the merged image) to `artifacts/lumari_watch/lumari_watch/<date>/` per lab convention.

## Lab orchestrator

This firmware uses **ESP-IDF**, not PlatformIO. To integrate with `scripts/lab-build.sh`, add an `esp-idf-lab` container (FEATURE_ROADMAP L6) and extend the build config for `lumari_watch` + `lumari_watch` so `./scripts/lab-build.sh lumari_watch lumari_watch` runs `idf.py build` in the repo and copies artifacts.
