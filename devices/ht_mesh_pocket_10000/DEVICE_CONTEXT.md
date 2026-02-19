# Device Context — Heltec Mesh Pocket (10000 mAh)

**Device ID:** `ht_mesh_pocket_10000`  
**Board:** Heltec Mesh Pocket — Qi2 magnetic power bank + Meshtastic (nRF52840 + SX1262 + e-ink)  
**Lab contract:** `firmware/` · `configs/` · `pinmaps/` · `notes/`

---

## Summary

Portable power bank with integrated Meshtastic node: nRF52840 (BLE), Semtech SX1262 (LoRa), 2.13" e-ink display. Available in 5000 mAh and **10000 mAh** variants. Qi2 wireless charging; USB-C PD input/output. Flashing is via **magnetic pogo programming interface** (UF2), not USB-C data. Default firmware: Meshtastic.

---

## Hardware at a Glance

| Item | Detail |
|------|--------|
| **MCU** | nRF52840 (BLE 5.0) |
| **Radio** | Semtech SX1262 LoRa |
| **Bands** | 902–928 MHz or 863–870 MHz (region) |
| **Display** | 2.13" e-ink (GxEPD2_213_B74), 250×122 px |
| **Battery** | 5000 mAh or 10000 mAh (this device: 10000 mAh) |
| **Charging** | Qi2 (5W–15W), USB-C PD 9V–2.22A / 5V–3A; simultaneous charge + discharge |
| **Programming** | 4-pin magnetic pogo; DFU mode → UF2 drive (HT-n5262) |
| **Buttons** | CTRL (power/output), USER (Meshtastic), RST (reset/DFU) |

---

## Context Files in This Device

| File | Description |
|------|-------------|
| [notes/DOCS_INDEX.md](notes/DOCS_INDEX.md) | Index of all official docs and PDFs |
| [notes/OFFICIAL_HELTEC_DOCS.md](notes/OFFICIAL_HELTEC_DOCS.md) | Heltec docs summary (charging, buttons, flashing) |
| [notes/MESHTASTIC_HARDWARE.md](notes/MESHTASTIC_HARDWARE.md) | Meshtastic hardware page (specs, flashing, firmware names) |
| [notes/FLASHING_UF2.md](notes/FLASHING_UF2.md) | UF2 flashing via magnetic cable |
| [notes/datasheet/](notes/datasheet/) | Datasheet PDF (battery, RF, protections) |
| [notes/user_manual/](notes/user_manual/) | User guide PDF (operation) |
| [firmware/meshtastic/README.md](firmware/meshtastic/README.md) | Meshtastic firmware (UF2) and build envs |

---

## Firmware in This Lab

- **Meshtastic** (default): Official firmware; UF2 builds for `heltec-mesh-pocket-10000` and `heltec-mesh-pocket-10000-inkhud`. See [Meshtastic hardware docs](https://meshtastic.org/docs/hardware/devices/heltec-automation/meshpocket/) and [firmware/meshtastic/README.md](firmware/meshtastic/README.md).

---

## Critical Notes

1. **USB-C is charge/power only** — no data. Use the **included magnetic pogo cable** for serial/flashing.
2. **DFU mode:** Double-press **RST** (or double-click USER per some docs); drive **HT-n5262** appears; copy UF2 to drive.
3. **First use:** Fully discharge then charge to 100% before relying on capacity.

---

## References

- [Heltec MeshPocket docs](https://docs.heltec.org/en/ready_to_use/meshpocket/index.html)
- [Heltec product page](https://heltec.org/project/meshpocket/)
- [Meshtastic — Heltec MeshPocket](https://meshtastic.org/docs/hardware/devices/heltec-automation/meshpocket/)
- Lab: [CONTEXT.md](../../CONTEXT.md), [FEATURE_ROADMAP.md](../../FEATURE_ROADMAP.md)
