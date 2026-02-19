# Heltec Mesh Pocket — UF2 Flashing

Firmware is flashed via the **magnetic pogo programming interface**, not USB-C. The device appears as a **UF2 drive** (HT-n5262).

---

## Prerequisites

- **Included magnetic USB cable** (pogo pins to USB). Standard USB-C cable will not expose serial or DFU.
- Meshtastic UF2 for your variant:
  - **10000 mAh:** `firmware-heltec-mesh-pocket-10000-X.X.X.xxxx.uf2` or `firmware-heltec-mesh-pocket-inkhud-10000-X.X.X.xxxx.uf2`
  - **5000 mAh:** `firmware-heltec-mesh-pocket-5000-...` or `...-inkhud-5000-...`

Get UF2 from [Meshtastic releases](https://github.com/meshtastic/firmware/releases) or [Web Flasher](https://flasher.meshtastic.org/).

---

## Enter DFU mode

- **Double-press RST** (or, per some docs, double-click USER). A removable drive named **HT-n5262** appears on the host.

---

## Flash

1. Copy the `.uf2` file to the **HT-n5262** drive.
2. If the OS reports an error, choose **Skip**.
3. The device will reset and run the new firmware when the copy completes.

---

## Web Flasher (alternative)

1. Connect with the **magnetic cable** so the device and port are visible.
2. Open [flasher.meshtastic.org](https://flasher.meshtastic.org/).
3. Select the correct port and **Heltec Mesh Pocket** (10000 or 5000).
4. Choose **Stable** (or desired) release → **Flash** → **Download UF2**.
5. Enter DFU (double-press RST), then copy the downloaded UF2 to the **HT-n5262** drive as above.

---

## Notes

- USB-C on the Mesh Pocket is **charge and power only**; it does not enumerate as serial or storage. Always use the magnetic cable for flashing.
- First use: fully discharge then charge to 100% for accurate battery behavior.
