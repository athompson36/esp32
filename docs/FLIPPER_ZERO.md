# Flipper Zero — Lab Support

Flipper Zero is a multi-tool handheld (STM32WB55) with Sub-GHz, 125 kHz RFID, NFC, IR, iButton, and BadUSB. This doc covers how it’s represented in the lab and how to use official and community firmware.

---

## Device in this lab

- **Registry:** [registry/devices/flipper_zero.json](../registry/devices/flipper_zero.json)
- **Device id:** `flipper_zero`
- **Compatible firmware (main unit):** `flipper_firmware` (official), `unleashed`, `roguemaster`

Optional **WiFi board** (ESP32 add-on) runs [ESP32 Marauder](https://github.com/justcallmekoko/ESP32Marauder) (Flipper target); that firmware is tracked under Marauder, not as a separate device here.

---

## Repos and update methods

| Firmware | Repo | Update / flasher |
|----------|------|------------------|
| **Official** | [flipperdevices/flipperzero-firmware](https://github.com/flipperdevices/flipperzero-firmware) | [flipperzero.one/update](https://flipperzero.one/update), qFlipper, Flipper mobile app (BLE) |
| **qFlipper** | [flipperdevices/qFlipper](https://github.com/flipperdevices/qFlipper) | Desktop app: [flipperzero.one/downloads](https://flipperzero.one/downloads) |
| **Unleashed** | [DarkFlippers/unleashed-firmware](https://github.com/DarkFlippers/unleashed-firmware) | [web.unleashedflip.com](https://web.unleashedflip.com) |
| **RogueMaster** | [RogueMaster/flipperzero-firmware-wPlugins](https://github.com/RogueMaster/flipperzero-firmware-wPlugins) | [lab.flipper.net](https://lab.flipper.net) |

Official docs: [docs.flipper.net — Firmware update](https://docs.flipper.net/zero/basics/firmware-update).

---

## Lab layout (device contract)

Per-device layout under `devices/<device_id>/`:

- **Firmware:** clone under `devices/flipper_zero/firmware/<target>/repo`:
  - `devices/flipper_zero/firmware/flipper_firmware/repo` — official
  - `devices/flipper_zero/firmware/unleashed/repo` — Unleashed
  - `devices/flipper_zero/firmware/roguemaster/repo` — RogueMaster
- **Configs:** `devices/flipper_zero/configs/<flipper_firmware|unleashed|roguemaster>/` for presets
- **pinmaps/** — optional
- **notes/** — optional

Flash methods in registry: `qflipper`, `sd_update`, `mobile_app`, `dfu`. Flipper is not flashed via esptool (no entry in the inventory app’s ESP32 flash device list); use qFlipper or SD/mobile/DFU as above.

---

## Inventory and config wizard

- **Registry:** Flipper Zero is loaded from `registry/devices/flipper_zero.json`, so it appears in the device config wizard as a selectable device.
- **Firmware dropdown:** For `flipper_zero`, the wizard offers **Flipper Firmware (official)**, **Unleashed**, and **RogueMaster**.
- **Presets:** Config presets can be saved under `devices/flipper_zero/configs/<firmware>/` for the chosen firmware type.
- **Flash UI:** The flash/backup panel is for ESP32 (esptool) only; Flipper updates are done with qFlipper or the web installers above.

---

## WiFi board (ESP32 Marauder)

The optional Flipper WiFi board is an ESP32 add-on. Marauder has a dedicated Flipper target; see [justcallmekoko/ESP32Marauder](https://github.com/justcallmekoko/ESP32Marauder) and [REPOS.md — Bruce, Ghost ESP & Marauder](../REPOS.md). Flashing the WiFi board uses the usual ESP32 tooling (esptool / web flasher), not qFlipper.
