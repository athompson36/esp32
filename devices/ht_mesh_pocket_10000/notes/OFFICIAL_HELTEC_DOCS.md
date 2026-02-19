# Heltec MeshPocket — Official Docs Summary

Pulled from:
- https://docs.heltec.org/en/ready_to_use/meshpocket/index.html
- https://wiki.heltec.org/docs/devices/open-source-hardware/nrf52840-series/meshpocket/Usage

---

## Summary

MeshPocket is a Qi2 magnetic power bank with integrated nRF52840 (BLE) and SX1262 (LoRa), 2.13" e-ink display. Compatible with Meshtastic. 5000 mAh or 10000 mAh; supports 5W–15W wireless charging, USB-C PD (9V–2.22A, 5V–3A), and protocols: PD, AFC, Huawei. Protections: input over/undervoltage, output overcurrent/short-circuit, battery undervoltage, NTC/chip temperature, charging timeout.

---

## Charging

- **First use:** Fully discharge, then charge to 100%.
- **Wireless output:** Click CTRL = on; double-click CTRL = off. Supports MPP, EPP, Samsung 10W, Apple 7.5W, BPP.
- **USB-C output:** Connect cable to device; long-press CTRL = turn off wireless + wired output.
- **USB-C input (power bank):** Connect charger to USB-C; LED flashes, remaining capacity shown.

### Battery level indicator (power bank)

| Remaining | Indicator |
|-----------|------------|
| 71–100% | Green steady |
| 31–70% | Yellow steady |
| 11–30% | Red steady |
| 5–10% | Red slow flash 0.5 Hz |
| ≤5% | Output off; wireless section can still be powered |

---

## RGB indicator (Meshtastic / status)

| Status | Battery | Indicator |
|--------|---------|-----------|
| Over-discharge / no power | ≤5% | Red 2 Hz, then off after 5 s |
| | 1–30% | Red slow 0.5 Hz |
| | 31–70% | Yellow slow 0.5 Hz |
| | 71–100% | Green slow 0.5 Hz |
| Fully charged | — | Green steady |
| Standby (button) | — | Current level color flashes |
| FOD | — | Yellow 2 Hz |
| Fault | — | Off, output off |

---

## Buttons

**Warning:** USER/RST behavior depends on Meshtastic firmware version; see meshtastic.org.

| Button | Action | Description |
|--------|--------|-------------|
| **CTRL** | Single click | Turn on output; show battery via LED |
| | Double click | Turn off wireless output |
| | Long press | Turn off wireless + wired output |
| **USER** | Single click | Toggle Meshtastic options |
| | Long press | Select option / Turn off Meshtastic |
| **RST** | Single click | Reset / wake Meshtastic |

---

## Serial & firmware flashing

- Use the **side-mounted magnetic programming interface** (included magnetic cable). USB-C does **not** provide serial or flashing.
- To get serial port: connect with **magnetic cable**; standard USB-only connection will not show the port.

### Meshtastic (default firmware)

- **Web Flasher:** [flasher.meshtastic.org](https://flasher.meshtastic.org/) → select device/port → choose Stable → Flash → Download UF2. Double-press **RST** → drive **HT-n5262** appears → copy UF2 to drive (choose “Skip” if error).
- **Manual:** Get UF2 → connect with magnetic cable → double-click **USER** → drive **HT-n5262** → copy firmware to drive. Transfer completes automatically.

---

## Device firmware customization

Firmware updates and custom builds are done via the same magnetic programming interface; Heltec provides support for custom firmware development.
