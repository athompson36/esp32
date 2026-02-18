# Lab Repositories Index

Central index of firmware, tools, and documentation repos used in this lab.

- **Full firmware list (all devices):** [FIRMWARE_INDEX.md](FIRMWARE_INDEX.md)
- **Meshtastic / MeshCore / Launcher devices & repos:** [docs/MESHTASTIC_MESHCORE_LAUNCHER_DEVICES.md](docs/MESHTASTIC_MESHCORE_LAUNCHER_DEVICES.md) — supported devices, web flashers, full repo list.
- **Per-device details:** `devices/<device>/firmware/README.md`

---

## Meshtastic (organization)

| Repo | Description |
|------|-------------|
| [meshtastic/firmware](https://github.com/meshtastic/firmware) | Official Meshtastic firmware (PlatformIO). 100+ device targets. |
| [meshtastic/web](https://github.com/meshtastic/web) | Web monorepo: client (client.meshtastic.org), core, transports (Bluetooth, serial, HTTP), protobufs. |
| [meshtastic/web-flasher](https://github.com/meshtastic/web-flasher) | Official online flasher — ESP32, nRF52, Pico UF2. **Live:** [flasher.meshtastic.org](https://flasher.meshtastic.org) |
| [meshtastic/Meshtastic-Android](https://github.com/meshtastic/Meshtastic-Android) | Android app. |
| [meshtastic/Meshtastic-Apple](https://github.com/meshtastic/Meshtastic-Apple) | iOS app. |
| [meshtastic/python](https://github.com/meshtastic/python) | Python CLI and library. |
| [meshtastic/protobufs](https://github.com/meshtastic/protobufs) | Shared protobuf definitions. |
| [meshtastic/meshtastic](https://github.com/meshtastic/meshtastic) | Documentation site (meshtastic.org). |

**Supported devices (official list):** [meshtastic.org/docs/hardware/devices/](https://meshtastic.org/docs/hardware/devices/) — RAK, LILYGO, HELTEC, Seeed, B&Q, Elecrow, muzi works, Raspberry Pi.

---

## MeshCore & T-Beam 1W

| Repo | Description |
|------|-------------|
| [meshcore-dev/MeshCore](https://github.com/meshcore-dev/MeshCore) | MeshCore — multi-hop LoRa (Companion, Repeater, Room Server). ESP32, nRF52, RP2040. |
| [mintylinux/Meshcore-T-beam-1W-Firmware](https://github.com/mintylinux/Meshcore-T-beam-1W-Firmware) | MeshCore T-Beam 1W firmware (community/variant). |
| [ripplebiz/MeshCore](https://github.com/ripplebiz/MeshCore) | Original/alternate MeshCore upstream. |

**Web flasher:** [flasher.meshcore.co.uk](https://flasher.meshcore.co.uk) — device list: [meshcore.co.uk/get.html](https://meshcore.co.uk/get.html), [nodakmesh.org/meshcore/devices](https://nodakmesh.org/meshcore/devices).

---

## Launcher (T-Deck, M5Stack)

| Repo | Description |
|------|-------------|
| [bmorcelli/Launcher](https://github.com/bmorcelli/Launcher) | Launcher firmware — T-Deck, T-Deck Plus, T-Dongle-S3, T-Display-S3, M5StickC, M5Cardputer. |
| Launcher docs & catalog | [bmorcelli.github.io/Launcher](https://bmorcelli.github.io/Launcher/) — web flasher, firmware catalog. |

**Web flasher:** [bmorcelli.github.io/Launcher/webflasher.html](https://bmorcelli.github.io/Launcher/webflasher.html)

---

## Bruce, Ghost ESP & Marauder (ESP32 security / pentest)

Often used with **Launcher** so multiple firmwares can be switched on the same device. Applicable to Launcher-compatible boards: T-Deck, T-Deck Plus, T-Display-S3, T-Dongle-S3, M5StickC, M5Cardputer, CYD (Cheap Yellow Display).

| Repo | Description | Web flasher |
|------|-------------|-------------|
| [BruceDevices/firmware](https://github.com/BruceDevices/firmware) | Bruce — ESP32 red-team firmware (WiFi/BLE, evil portal, BadBLE, Wireguard). M5Stack Cardputer/Sticks/Core, LilyGo. AGPL-3.0. | [bruce.computer/flasher](https://bruce.computer/flasher) |
| [Spooks4576/Ghost_ESP](https://github.com/Spooks4576/Ghost_ESP) | Ghost ESP — ESP32 pentest firmware (Evil Portal, SD, Web UI). CYD, ESP32-S3-Cardputer, AwokMini, Crowtech LCD. | [flasher.spookytools.com](https://flasher.spookytools.com) |
| [justcallmekoko/ESP32Marauder](https://github.com/justcallmekoko/ESP32Marauder) | ESP32 Marauder — WiFi/BLE offensive & defensive toolkit. Marauder v4/v6/Mini/Kit/Flipper variants, CYD, many ESP32 boards. | Prebuilt binaries + OTA; see repo wiki. |

**Applicable devices (this lab):** T-Deck Plus, and any Launcher-compatible device (see Launcher catalog). Clone under `devices/<device_id>/firmware/bruce/`, `firmware/ghost/`, or `firmware/marauder/` per the device contract.

---

## Flipper Zero

Multi-tool handheld (STM32WB55): Sub-GHz, RFID, NFC, IR, iButton, BadUSB. Optional **WiFi board** (ESP32 add-on) runs Marauder — see [justcallmekoko/ESP32Marauder](https://github.com/justcallmekoko/ESP32Marauder) (Flipper target).

| Repo | Description | Update / flasher |
|------|-------------|------------------|
| [flipperdevices/flipperzero-firmware](https://github.com/flipperdevices/flipperzero-firmware) | Official Flipper Zero firmware (GPL-3.0). | [flipperzero.one/update](https://flipperzero.one/update); qFlipper desktop; Flipper mobile app (BLE). |
| [flipperdevices/qFlipper](https://github.com/flipperdevices/qFlipper) | Desktop app (PC/Mac/Linux) for firmware update, file manager, CLI. | [flipperzero.one/downloads](https://flipperzero.one/downloads) |
| [DarkFlippers/unleashed-firmware](https://github.com/DarkFlippers/unleashed-firmware) | Unleashed — community fork; Sub-GHz enhancements, rolling code, extended protocols. | [web.unleashedflip.com](https://web.unleashedflip.com) |
| [RogueMaster/flipperzero-firmware-wPlugins](https://github.com/RogueMaster/flipperzero-firmware-wPlugins) | RogueMaster — plugins, games, NFC/Sub-GHz extras. | [lab.flipper.net](https://lab.flipper.net) |

**Docs:** [docs.flipper.net](https://docs.flipper.net/zero/basics/firmware-update). In this lab: device id `flipper_zero`; clone firmware under `devices/flipper_zero/firmware/<flipper_firmware|unleashed|roguemaster>/repo` per device contract.

---

## T-Deck / LilyGO tooling

| Repo | Description |
|------|-------------|
| [JustDr00py/tdeck-maps](https://github.com/JustDr00py/tdeck-maps) | Meshtastic map tile generator for the T-Deck. |
| [Xinyuan-LilyGO/T-Deck](https://github.com/Xinyuan-LilyGO/T-Deck) | T-Deck hardware, schematics, TFT_eSPI, examples. |
| [Xinyuan-LilyGO/Meshtastic_firmware](https://github.com/Xinyuan-LilyGO/Meshtastic_firmware) | LilyGO device-specific Meshtastic builds. |

---

## Device mapping (this lab)

- **T-Deck Plus:** Launcher, Bruce, Ghost, Marauder (via Launcher), tdeck-maps, Meshtastic. See [devices/t_deck_plus/firmware/README.md](devices/t_deck_plus/firmware/README.md).
- **T-Beam 1W:** MeshCore (upstream + mintylinux variant), Meshtastic. See [devices/t_beam_1w/firmware/README.md](devices/t_beam_1w/firmware/README.md).
- **Flipper Zero:** Official, Unleashed, RogueMaster. Optional WiFi board (ESP32) runs Marauder. See [docs/FLIPPER_ZERO.md](docs/FLIPPER_ZERO.md).

For the full list of supported devices per firmware (Meshtastic, MeshCore, Launcher, Bruce, Ghost, Marauder) and all repo URLs, see [docs/MESHTASTIC_MESHCORE_LAUNCHER_DEVICES.md](docs/MESHTASTIC_MESHCORE_LAUNCHER_DEVICES.md).
