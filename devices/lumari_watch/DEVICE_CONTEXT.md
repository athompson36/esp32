# Device Context — Lumari Watch

**Device ID:** `lumari_watch`  
**Board:** Waveshare ESP32-S3-Touch-AMOLED-2.06 (2.06″ 410×502 AMOLED)  
**Lab contract:** `firmware/` · `configs/` · `pinmaps/` · `notes/`

---

## Summary

ESP-IDF firmware for the Lumari watch: a living creature on your wrist with quests, XP, and a companion ecosystem. **Primary hardware:** [Waveshare ESP32-S3-Touch-AMOLED-2.06](https://www.waveshare.com/wiki/ESP32-S3-Touch-AMOLED-2.06) — 2.06″ 410×502 AMOLED (CO5300 QSPI), FT3168 I2C touch, QMI8658 IMU, PCF85063 RTC, BOOT/PWR buttons. Toolchain: **ESP-IDF v5.x**; target **esp32s3**, 8MB PSRAM. Firmware source: [athompson36/lumari_watch](https://github.com/athompson36/lumari_watch).

---

## Hardware at a Glance

| Item | Detail |
|------|--------|
| **MCU** | ESP32-S3, 8MB PSRAM |
| **Display** | 2.06″ 410×502 AMOLED (CO5300 QSPI) |
| **Touch** | FT3168 I2C (0x38) |
| **IMU** | QMI8658 (I2C) |
| **RTC** | PCF85063 (0x51, I2C) |
| **Buttons** | BOOT (GPIO 0), PWR (GPIO 10) |

Pinout and schematic: [docs/HARDWARE_REFERENCES.md](https://github.com/athompson36/lumari_watch/blob/main/docs/HARDWARE_REFERENCES.md) in the firmware repo; board config in `components/config/lumari_config.h` (`LUMARI_BOARD_WAVESHARE_ESP32_S3_AMOLED_2_06`).

---

## Firmware Source

| Item | Location |
|------|----------|
| **Firmware repo** | https://github.com/athompson36/lumari_watch |
| **Clone path in lab** | `devices/lumari_watch/firmware/lumari_watch/repo/` |
| **Build / toolchain** | ESP-IDF v5.x; `idf.py set-target esp32s3`, `idf.py build`, `idf.py flash monitor` |

---

## Required Documentation (locations)

All in the **firmware repo** ([github.com/athompson36/lumari_watch](https://github.com/athompson36/lumari_watch)):

| Doc type | Location in repo |
|----------|------------------|
| **Overview, build & flash** | `README.md` (root) |
| **Hardware, pinout, BSP links** | `docs/HARDWARE_REFERENCES.md` |
| **Board + firmware one-pager** | `docs/BOARD_FIRMWARE_CONTEXT.md` |
| **Factory firmware, input troubleshooting** | `docs/WAVESHARE_FACTORY_AND_TROUBLESHOOTING.md` |
| **Dependencies, install** | `docs/DEPENDENCIES.md`; `./scripts/install_dependencies.sh` |
| **Roadmap (phases)** | `ROADMAP.md` |
| **Config (resolution, FPS, board)** | `components/config/lumari_config.h` |

---

## Context Files in This Device

| File | Description |
|------|-------------|
| [firmware/lumari_watch/README.md](firmware/lumari_watch/README.md) | Firmware clone path, build, and artifact layout |
| [notes/DOCS_INDEX.md](notes/DOCS_INDEX.md) | Index of required documentation and locations in source repo |
| [configs/README.md](configs/README.md) | Build/runtime config presets (if any) |
| [pinmaps/README.md](pinmaps/README.md) | Pinout summary; link to canonical source in repo |

---

## References

- **Firmware source:** [github.com/athompson36/lumari_watch](https://github.com/athompson36/lumari_watch)
- Lab: [CONTEXT.md](../../CONTEXT.md), [FEATURE_ROADMAP.md](../../FEATURE_ROADMAP.md)
