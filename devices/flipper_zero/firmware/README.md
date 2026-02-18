# Flipper Zero — Firmware & Repos

Flipper Zero (STM32WB55) — official and community firmware. Optional ESP32 WiFi board runs Marauder; see [ESP32Marauder](https://github.com/justcallmekoko/ESP32Marauder) (Flipper target).

**Full index:** [FIRMWARE_INDEX.md](../../FIRMWARE_INDEX.md#flipper_zero-flipper-zero) · **Lab doc:** [docs/FLIPPER_ZERO.md](../../docs/FLIPPER_ZERO.md)

## Main unit firmware

| Firmware | Repo | Update / flasher |
|----------|------|------------------|
| **Official** | [flipperdevices/flipperzero-firmware](https://github.com/flipperdevices/flipperzero-firmware) | [flipperzero.one/update](https://flipperzero.one/update), qFlipper, mobile app |
| **qFlipper** | [flipperdevices/qFlipper](https://github.com/flipperdevices/qFlipper) | Desktop updater: [flipperzero.one/downloads](https://flipperzero.one/downloads) |
| **Unleashed** | [DarkFlippers/unleashed-firmware](https://github.com/DarkFlippers/unleashed-firmware) | [web.unleashedflip.com](https://web.unleashedflip.com) |
| **RogueMaster** | [RogueMaster/flipperzero-firmware-wPlugins](https://github.com/RogueMaster/flipperzero-firmware-wPlugins) | [lab.flipper.net](https://lab.flipper.net) |

## Lab layout

Clone repos under:

- `devices/flipper_zero/firmware/flipper_firmware/repo` — official
- `devices/flipper_zero/firmware/unleashed/repo` — Unleashed
- `devices/flipper_zero/firmware/roguemaster/repo` — RogueMaster

Config presets: `devices/flipper_zero/configs/<flipper_firmware|unleashed|roguemaster>/`.

See [REPOS.md](../../REPOS.md) for the full lab repo index.
