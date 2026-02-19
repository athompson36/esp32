# Meshtastic — Heltec MeshPocket (Hardware Page)

Pulled from: https://meshtastic.org/docs/hardware/devices/heltec-automation/meshpocket/

---

## Overview

MeshPocket (Heltec) is a compact device combining **Qi2 magnetic wireless charging** with an integrated low-power Meshtastic node: **nRF52840** MCU, **SX1262** LoRa, **2.13" e-ink** display. Available in **5000** or **10000 mAh** battery. For everyday use, outdoor use, and off-grid messaging.

---

## Specifications

| Item | Detail |
|------|--------|
| **MCU** | nRF52840, Bluetooth 5.0 |
| **LoRa** | Semtech SX1262 |
| **Bands** | 902–928 MHz, or 863–870 MHz |
| **Antenna** | Integrated LoRa antenna |
| **Connectors** | 4-pin magnetic (programming/Meshtastic), USB-C (charge/power only) |

### Features

- 5000 or 10000 mAh battery
- 2.13" e-ink display
- Qi2 wireless charger with integrated Meshtastic

---

## Flashing

1. Use the **included magnetic pogo cable** on the side of the device. The **USB-C port is for charging/power only** — no data or flashing.
2. Enter DFU: **double-press RST**; removable drive appears.
3. Copy the **UF2** firmware file onto the drive. Flashing completes when copy finishes.

---

## Firmware files (Meshtastic releases)

**5000 mAh:**

- `firmware-heltec-mesh-pocket-inkhud-5000-X.X.X.xxxx.uf2`
- `firmware-heltec-mesh-pocket-5000-X.X.X.xxxx.uf2`

**10000 mAh:**

- `firmware-heltec-mesh-pocket-inkhud-10000-X.X.X.xxxx.uf2`
- `firmware-heltec-mesh-pocket-10000-X.X.X.xxxx.uf2`

Replace `X.X.X.xxxx` with the release version.

---

## Resources

- **Purchase (international):** [Heltec Mesh Pocket 10000](https://msh.to/heltec-mesh-pocket-10000/)
- **Meshtastic firmware:** [GitHub releases](https://github.com/meshtastic/firmware/releases), [Web Flasher](https://flasher.meshtastic.org/)
