# Heltec Mesh Pocket — Documentation Index

All official documentation sources and local copies for the **10000 mAh** Mesh Pocket (Meshtastic firmware).

---

## Official sources (pull from here)

| Doc | URL | Description |
|-----|-----|-------------|
| **Heltec MeshPocket (main)** | https://docs.heltec.org/en/ready_to_use/meshpocket/index.html | Features, charging, buttons, Meshtastic, flashing |
| **Heltec product page** | https://heltec.org/project/meshpocket/ | Product info, options (5000/10000 mAh, bands, color) |
| **Heltec usage guide** | https://wiki.heltec.org/docs/devices/open-source-hardware/nrf52840-series/meshpocket/Usage | Charging, RGB indicator, buttons, serial & flashing |
| **Meshtastic hardware** | https://meshtastic.org/docs/hardware/devices/heltec-automation/meshpocket/ | Specs, flashing, firmware file names, purchase |

---

## PDFs (datasheet & user guide)

| Document | Official URL | Local copy |
|----------|--------------|------------|
| **Datasheet** (battery, RF, charging, protections) | https://resource.heltec.cn/download/MeshPocket/datasheet/MeshPocket_1.0.0.pdf | [notes/datasheet/MeshPocket_1.0.0.pdf](datasheet/MeshPocket_1.0.0.pdf) |
| **User manual** (operation guide) | https://resource.heltec.cn/download/MeshPocket/user_manual/User_Guide_Rev.1.0.1.pdf | [notes/user_manual/User_Guide_Rev.1.0.1.pdf](user_manual/User_Guide_Rev.1.0.1.pdf) |

If the local PDFs are missing, run from repo root: `./scripts/download_meshpocket_docs.sh`

---

## Local notes in this device

| File | Content |
|------|--------|
| [OFFICIAL_HELTEC_DOCS.md](OFFICIAL_HELTEC_DOCS.md) | Summary of Heltec docs (charging, indicators, buttons, flashing) |
| [MESHTASTIC_HARDWARE.md](MESHTASTIC_HARDWARE.md) | Meshtastic hardware page (specs, flashing, firmware names) |
| [FLASHING_UF2.md](FLASHING_UF2.md) | UF2 flashing steps (magnetic cable, DFU, Web Flasher) |

---

## Meshtastic firmware files (10000 mAh)

- **Standard:** `firmware-heltec-mesh-pocket-10000-X.X.X.xxxx.uf2`
- **InkHUD:** `firmware-heltec-mesh-pocket-inkhud-10000-X.X.X.xxxx.uf2`

From [Meshtastic releases](https://github.com/meshtastic/firmware/releases) or [Web Flasher](https://flasher.meshtastic.org/).
