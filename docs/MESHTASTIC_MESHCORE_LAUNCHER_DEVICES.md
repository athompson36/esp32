# Meshtastic, MeshCore & Launcher — Supported Devices & Repos

Single reference for **supported devices** and **all related repos** (firmware, web flashers, clients, docs). Sourced from official Meshtastic, MeshCore, and Launcher documentation.

---

## 1. Repositories index

### Meshtastic (organization)

| Repo | Description | URL |
|------|-------------|-----|
| **firmware** | Official Meshtastic firmware (PlatformIO). 100+ device targets. | [github.com/meshtastic/firmware](https://github.com/meshtastic/firmware) |
| **web** | Web monorepo: client (client.meshtastic.org), core, transports (Bluetooth, serial, HTTP, Node, Deno), protobufs. | [github.com/meshtastic/web](https://github.com/meshtastic/web) |
| **web-flasher** | Official online flasher for Meshtastic (Nuxt/Vue, esptool.js, nRF52/Pico UF2). | [github.com/meshtastic/web-flasher](https://github.com/meshtastic/web-flasher) |
| **Meshtastic-Android** | Android app. | [github.com/meshtastic/Meshtastic-Android](https://github.com/meshtastic/Meshtastic-Android) |
| **Meshtastic-Apple** | iOS app. | [github.com/meshtastic/Meshtastic-Apple](https://github.com/meshtastic/Meshtastic-Apple) |
| **python** | Python CLI and library. | [github.com/meshtastic/python](https://github.com/meshtastic/python) |
| **protobufs** | Shared protobuf definitions (submodule in web). | [github.com/meshtastic/protobufs](https://github.com/meshtastic/protobufs) |
| **meshtastic** | Documentation site (meshtastic.org). | [github.com/meshtastic/meshtastic](https://github.com/meshtastic/meshtastic) |

**Web flasher (live):** [flasher.meshtastic.org](https://flasher.meshtastic.org) — supports ESP32, nRF52, RP2040 (Pico) devices. Chrome/Edge recommended.

**Device docs (canonical list):** [meshtastic.org/docs/hardware/devices/](https://meshtastic.org/docs/hardware/devices/)

---

### MeshCore

| Repo | Description | URL |
|------|-------------|-----|
| **MeshCore** | Multi-hop LoRa firmware (Companion, Repeater, Room Server). ESP32, nRF52, RP2040. | [github.com/meshcore-dev/MeshCore](https://github.com/meshcore-dev/MeshCore) |
| **MeshCore T-Beam 1W** (variant) | Community T-Beam 1W build. | [github.com/mintylinux/Meshcore-T-beam-1W-Firmware](https://github.com/mintylinux/Meshcore-T-beam-1W-Firmware) |
| **ripplebiz/MeshCore** | Original/alternate upstream. | [github.com/ripplebiz/MeshCore](https://github.com/ripplebiz/MeshCore) |

**Web flasher (live):** [flasher.meshcore.co.uk](https://flasher.meshcore.co.uk) — Chrome/Edge. Device list and setup: [meshcore.co.uk/get.html](https://meshcore.co.uk/get.html), [nodakmesh.org/meshcore/devices](https://nodakmesh.org/meshcore/devices).

---

### Launcher (T-Deck & M5Stack)

| Repo | Description | URL |
|------|-------------|-----|
| **Launcher** | GRUB-like launcher for ESP32 devices: T-Deck, T-Deck Plus, T-Dongle-S3, T-Display-S3, M5StickC, M5Cardputer. LVGL/ESP-IDF. | [github.com/bmorcelli/Launcher](https://github.com/bmorcelli/Launcher) |
| **Launcher docs & catalog** | Documentation, web flasher, firmware catalog. | [bmorcelli.github.io/Launcher](https://bmorcelli.github.io/Launcher/) |

**Web flasher (live):** [bmorcelli.github.io/Launcher/webflasher.html](https://bmorcelli.github.io/Launcher/webflasher.html)  
**Firmware catalog:** [bmorcelli.github.io/Launcher/catalog.html](https://bmorcelli.github.io/Launcher/catalog.html)

---

### Bruce, Ghost ESP & Marauder (ESP32 security / pentest)

These firmwares are **applicable to Launcher-compatible devices** (T-Deck, T-Deck Plus, T-Display-S3, T-Dongle-S3, M5StickC, M5Cardputer, CYD). Often used with Launcher to switch between Meshtastic, Bruce, Ghost, Marauder, etc. on the same hardware.

| Repo | Description | Web flasher |
|------|-------------|-------------|
| **Bruce** | [BruceDevices/firmware](https://github.com/BruceDevices/firmware) — WiFi/BLE red-team (evil portal, BadBLE, Wireguard). M5Stack Cardputer/Sticks/Core, LilyGo. | [bruce.computer/flasher](https://bruce.computer/flasher) |
| **Ghost ESP** | [Spooks4576/Ghost_ESP](https://github.com/Spooks4576/Ghost_ESP) — ESP32 pentest (Evil Portal, SD, Web UI). CYD, ESP32-S3-Cardputer, AwokMini. | [flasher.spookytools.com](https://flasher.spookytools.com) |
| **Marauder** | [justcallmekoko/ESP32Marauder](https://github.com/justcallmekoko/ESP32Marauder) — WiFi/BLE toolkit. Marauder v4/v6/Mini/Kit/Flipper, CYD, many ESP32 boards. | Prebuilt + OTA; see repo wiki |

**In this lab:** For T-Deck Plus and other Launcher-compatible devices, clone or add Bruce/Ghost/Marauder under `devices/<device_id>/firmware/bruce/`, `firmware/ghost/`, or `firmware/marauder/` (with `repo/` and optional `overlays/` per the device contract). Flash UI and device config wizard can filter by these targets when artifacts exist.

---

### Map tiles & T-Deck tooling

| Repo | Description | URL |
|------|-------------|-----|
| **tdeck-maps** | Meshtastic map tile generator for T-Deck (offline maps). | [github.com/JustDr00py/tdeck-maps](https://github.com/JustDr00py/tdeck-maps) |
| **LilyGO T-Deck** | T-Deck hardware, schematics, TFT_eSPI, examples. | [github.com/Xinyuan-LilyGO/T-Deck](https://github.com/Xinyuan-LilyGO/T-Deck) |
| **LilyGO Meshtastic_firmware** | LilyGO device-specific Meshtastic builds. | [github.com/Xinyuan-LilyGO/Meshtastic_firmware](https://github.com/Xinyuan-LilyGO/Meshtastic_firmware) |

---

## 2. Meshtastic — supported devices (official)

Canonical list: [meshtastic.org/docs/hardware/devices/](https://meshtastic.org/docs/hardware/devices/). Summary by vendor.

### RAK®

- **WisBlock:** RAK4631 (nRF52840), RAK11310 (RP2040), RAK3312 (ESP32-S3); base boards 5005-O, 19007, 19003, 19001; peripherals (GPS, buzzer, IO, sensors, displays).
- **WisMesh:** Pocket V2, Pocket Mini, Tag, TAP, Board ONE, 1W Booster, Repeater, Repeater Mini, Ethernet MQTT Gateway, WiFi MQTT Gateway.

### LILYGO®

- **T-Beam:** T-Beam S3-Core, T-BeamSUPREME (ESP32-S3, SX1262, GPS).
- **T-Echo:** T-Echo (nRF52840, SX1262, E-Ink, GPS).
- **LoRa:** LoRa32 T3-S3 V1.0 (ESP32-S3, SX1262/SX1276/SX1280/LR1121).
- **T-Deck:** T-Deck, T-Deck Plus, T-Deck Pro (ESP32-S3FN8, SX1262, keyboard, display).
- **T-Lora Pager:** T-Lora Pager (ESP32-S3, LR1121, GPS).

### HELTEC®

- **LoRa 32:** LoRa32 V4, V3/3.1, Wireless Stick Lite V3, Wireless Tracker v1.0/v1.1, Wireless Paper v1.0/v1.1 (ESP32-S3, SX1262).
- **Vision Master:** E213, E290, T190 (ESP32-S3R8, SX1262, E-Ink).
- **Mesh Node:** Mesh Node T114 (nRF52840, SX1262).
- **MeshPocket:** MeshPocket (nRF52840, SX1262, QI2).

### Seeed Studio

- **SenseCAP:** Card Tracker T1000-E (nRF52840, LR1110), SenseCAP Indicator (ESP32/RP2040), SenseCAP Solar Node (nRF52840).
- **Wio:** Wio Tracker L1 (nRF52840, SX1262), XIAO nRF52840 & Wio-SX1262 Kit.

### B&Q Consulting

- **Nano:** Nano G2 Ultra (nRF52840, SX1262).
- **Station:** Station G2 (ESP32-S3 WROOM-1, SX1262).

### Elecrow

- **ThinkNode:** M1 (nRF52840), M2 (ESP32-S3), M3 (nRF52840, LR1110).
- **CrowPanel Advance:** 2.4/2.8/3.5/4.3/5.0/7.0" (ESP32-S3, SX1262).

### muzi ᴡᴏʀᴋꜱ

- **R1 Neo:** R1 Neo (nRF52840, SX1262, GPS).
- **BASE:** Base Uno (nRF52840, SX1262), Base Duo (nRF52840, LR1121).

### Raspberry Pi

- **Pico:** Raspberry Pi Pico (RP2040, SX1262). Peripherals: SSD1306/SH1106 OLED, CardKB.
- **Zero/2/3/4/400/5:** Linux native via **meshtasticd** — see [Linux Native Hardware](https://meshtastic.org/docs/hardware/devices/linux-native-hardware/).

---

## 3. MeshCore — supported devices

Sources: [meshcore.co.uk/get.html](https://meshcore.co.uk/get.html), [nodakmesh.org/meshcore/devices](https://nodakmesh.org/meshcore/devices).

| Device | MCU | Notes |
|--------|-----|--------|
| **Heltec V3** | ESP32-S3 | LoRa32, OLED, WiFi/BT. |
| **Heltec V4** | ESP32-S3 | Solar interface, 28 dBm. |
| **LilyGo T-Beam** | ESP32 | SX1262 or SX1276 variant. |
| **LilyGo T-Deck** | ESP32-S3 | Keyboard, display, trackball. |
| **LilyGo T-Deck Plus** | ESP32-S3 | GPS, maps, full standalone. |
| **LilyGo T-Echo** | nRF52840 | E-Ink, GPS, UF2. |
| **Heltec T114** | nRF52840 | Mesh Node, 1.14" TFT, solar. |
| **Seeed Wio Tracker L1** | nRF52840 | GPS, OLED, rugged. |
| **SenseCAP T1000-E** | nRF52840 | Card tracker, IP65, BT. |
| **RAK WisBlock** | nRF52840 | 19007+4631 starter kit, UF2. |
| **RAK WisMesh Tag** | nRF52840 | Compact tracker. |
| **RAK WisMesh Pocket** | nRF52840 | Enclosed, OLED, GPS. |
| **Station G2** | ESP32-S3 | High power, USB-C PD. |
| **Nano G2 Ultra** | nRF52840 | Wideband, OLED. |
| **Heltec Wireless Paper** | ESP32-S3 | E-Ink, ultra-thin. |
| **Heltec Capsule (CT62)** | ESP32-C3 | DIY stamp; firmware coming soon. |
| **RAK WisMesh 1W Booster** | nRF52840 | MeshCore firmware not yet released; Meshtastic supported. |

Firmware variants: Companion Radio (BT), Repeater, Room Server, Sensor Node.

---

## 4. Launcher — supported devices

Source: [bmorcelli.github.io/Launcher](https://bmorcelli.github.io/Launcher/), [github.com/bmorcelli/Launcher](https://github.com/bmorcelli/Launcher).

| Device | Notes |
|--------|--------|
| **LilyGO T-Deck** | ESP32-S3, keyboard, display. |
| **LilyGO T-Deck Plus** | ESP32-S3, GPS, maps. |
| **LilyGO T-Dongle-S3** | Port added in 2.4.x. |
| **LilyGO T-Display-S3** | Port added in 2.4.x. |
| **M5StickC** | M5Stack. |
| **M5StickC Plus** | M5Stack. |
| **M5StickC Plus 2** | M5Stack. |
| **M5Cardputer** | M5Stack. |

Pre-built binaries and device-specific builds in [Launcher releases](https://github.com/bmorcelli/Launcher/releases) and [catalog](https://bmorcelli.github.io/Launcher/catalog.html).

---

## 5. Web flashers summary

| Firmware / project | Web flasher URL | Devices |
|--------------------|-----------------|--------|
| **Meshtastic** | [flasher.meshtastic.org](https://flasher.meshtastic.org) | All Meshtastic-supported (ESP32, nRF52, RP2040). Chrome/Edge. |
| **MeshCore** | [flasher.meshcore.co.uk](https://flasher.meshcore.co.uk) | MeshCore-compatible list above. Chrome/Edge. |
| **Launcher** | [bmorcelli.github.io/Launcher/webflasher.html](https://bmorcelli.github.io/Launcher/webflasher.html) | T-Deck, T-Display-S3, T-Dongle-S3, M5StickC, M5Cardputer. |

---

## 6. Lab alignment

- **This repo’s device catalog** (Add device wizard): [inventory/app/device_catalog.json](../inventory/app/device_catalog.json) — LilyGo, Heltec, RPi, Pine64, Arduino, Teensy; extend as needed to match the lists above.
- **Registry:** [registry/devices/](../registry/devices/) — device JSON for flash compatibility; align IDs with Meshtastic/MeshCore where relevant (e.g. `t_beam_1w`, `t_deck_plus`, `heltec_t114_v3`, `flipper_zero`).
- **Firmware index (per device):** [FIRMWARE_INDEX.md](../FIRMWARE_INDEX.md) — firmwares and OS per lab device; see also [REPOS.md](../REPOS.md).
- **Flipper Zero:** [FLIPPER_ZERO.md](FLIPPER_ZERO.md) — Flipper Zero (STM32) and optional ESP32 WiFi board (Marauder); registry id `flipper_zero`.

---

*Last updated from meshtastic.org/docs/hardware/devices, meshcore.co.uk, nodakmesh.org/meshcore/devices, bmorcelli.github.io/Launcher, and Meshtastic/MeshCore/Launcher GitHub repos.*
