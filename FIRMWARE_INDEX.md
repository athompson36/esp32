# Firmware Index — All Devices

Single reference for **every device** in the lab and **all available firmwares / OS / build systems** with their repos. Sourced from project docs and public resources. See each device’s `devices/<device>/firmware/README.md` for build notes.

---

## Meshtastic, MeshCore & Launcher — supported devices & repos

For the **full list of supported devices** and **all related repos** (firmware, web flashers, clients), see:

**[docs/MESHTASTIC_MESHCORE_LAUNCHER_DEVICES.md](docs/MESHTASTIC_MESHCORE_LAUNCHER_DEVICES.md)**

Summary:

| Firmware / project | Supported devices (canonical list) | Web flasher |
|--------------------|-----------------------------------|-------------|
| **Meshtastic** | [meshtastic.org/docs/hardware/devices/](https://meshtastic.org/docs/hardware/devices/) — RAK, LILYGO (T-Beam, T-Deck, T-Echo, LoRa, Pager), HELTEC (LoRa32, Vision Master, Mesh Node, MeshPocket), Seeed (SenseCAP, Wio), B&Q (Nano, Station), Elecrow, muzi works, RPi Pico + Linux native | [flasher.meshtastic.org](https://flasher.meshtastic.org) |
| **MeshCore** | [meshcore.co.uk/get.html](https://meshcore.co.uk/get.html), [nodakmesh.org/meshcore/devices](https://nodakmesh.org/meshcore/devices) — Heltec V3/V4/T114, LilyGo T-Beam/T-Deck/T-Deck+/T-Echo, Seeed Wio L1, SenseCAP T1000-E, RAK WisBlock/WisMesh, Station G2, Nano G2 Ultra, etc. | [flasher.meshcore.co.uk](https://flasher.meshcore.co.uk) |
| **Launcher** | T-Deck, T-Deck Plus, T-Dongle-S3, T-Display-S3, M5StickC, M5Cardputer — [bmorcelli.github.io/Launcher](https://bmorcelli.github.io/Launcher/) | [Launcher web flasher](https://bmorcelli.github.io/Launcher/webflasher.html) |
| **Bruce** | Launcher-compatible (M5Stack Cardputer/Sticks/Core, LilyGo). Red-team WiFi/BLE. | [bruce.computer/flasher](https://bruce.computer/flasher) |
| **Ghost ESP** | CYD, ESP32-S3-Cardputer, AwokMini. Pentest firmware. | [flasher.spookytools.com](https://flasher.spookytools.com) |
| **Marauder** | Many ESP32 boards (v4/v6/Mini/Kit/Flipper, CYD). WiFi/BLE toolkit. | Prebuilt + OTA; [justcallmekoko/ESP32Marauder](https://github.com/justcallmekoko/ESP32Marauder) wiki |
| **Flipper Zero** | Main unit: official, Unleashed, RogueMaster. WiFi board (ESP32 add-on): Marauder. | qFlipper, SD, mobile app; [web.unleashedflip.com](https://web.unleashedflip.com), [lab.flipper.net](https://lab.flipper.net) |

Repo index (firmware, web, web-flasher, Android, Apple, python, protos, docs): [REPOS.md](REPOS.md).

---

## flipper_zero (Flipper Zero)

| Firmware / project | Repo / URL | Notes |
|--------------------|------------|--------|
| **Official** | [flipperdevices/flipperzero-firmware](https://github.com/flipperdevices/flipperzero-firmware) | GPL-3.0. Update: qFlipper, Flipper mobile app, [flipperzero.one/update](https://flipperzero.one/update). |
| **qFlipper** | [flipperdevices/qFlipper](https://github.com/flipperdevices/qFlipper) | Desktop app for firmware update and file manager. |
| **Unleashed** | [DarkFlippers/unleashed-firmware](https://github.com/DarkFlippers/unleashed-firmware) | Community fork; Sub-GHz, rolling code, extended protocols. [web.unleashedflip.com](https://web.unleashedflip.com). |
| **RogueMaster** | [RogueMaster/flipperzero-firmware-wPlugins](https://github.com/RogueMaster/flipperzero-firmware-wPlugins) | Plugins, games, NFC/Sub-GHz extras. [lab.flipper.net](https://lab.flipper.net). |
| **Marauder (WiFi board)** | [justcallmekoko/ESP32Marauder](https://github.com/justcallmekoko/ESP32Marauder) | ESP32 WiFi add-on for Flipper; Marauder Flipper target. |

**Docs:** [docs.flipper.net](https://docs.flipper.net/zero/basics/firmware-update). Lab device layout: [docs/FLIPPER_ZERO.md](docs/FLIPPER_ZERO.md).

---

## t_beam_1w (LilyGO T-Beam 1W)

| Firmware / project | Repo / URL | Notes |
|--------------------|------------|--------|
| **MeshCore** (upstream) | [meshcore-dev/MeshCore](https://github.com/meshcore-dev/MeshCore) | Multi-hop LoRa; Companion, Repeater, Room Server. Also [ripplebiz/MeshCore](https://github.com/ripplebiz/MeshCore) (original). |
| **MeshCore T-Beam 1W** (variant) | [mintylinux/Meshcore-T-beam-1W-Firmware](https://github.com/mintylinux/Meshcore-T-beam-1W-Firmware) | Community T-Beam 1W build. |
| **Meshtastic** (upstream) | [meshtastic/firmware](https://github.com/meshtastic/firmware) | Official Meshtastic firmware; T-Beam 1W target. |
| **Meshtastic** (LilyGO fork) | [Xinyuan-LilyGO/Meshtastic_firmware](https://github.com/Xinyuan-LilyGO/Meshtastic_firmware) | Device-specific builds. |
| **Prebuilt Meshtastic** (community) | [ksjkl1/LilyGO-TTGO-T-Beam-Meshtastic](https://github.com/ksjkl1/LilyGO-TTGO-T-Beam-Meshtastic) | Pre-built binaries + install scripts. |
| **LilyGO examples** | [LilyGO/TTGO-T-Beam](https://github.com/LilyGO/TTGO-T-Beam) | Examples, factory firmware (legacy). |

---

## t_deck_plus (LilyGO T-Deck Plus)

| Firmware / project | Repo / URL | Notes |
|--------------------|------------|--------|
| **Launcher** | [bmorcelli/Launcher](https://github.com/bmorcelli/Launcher) | First-class launcher firmware; LVGL/ESP-IDF/Rust/MicroPython. |
| **Launcher docs** | [bmorcelli.github.io/Launcher](https://bmorcelli.github.io/Launcher/) | Documentation source. |
| **Map tile generator** | [JustDr00py/tdeck-maps](https://github.com/JustDr00py/tdeck-maps) | Meshtastic map tiles for T-Deck. |
| **Meshtastic** (upstream) | [meshtastic/firmware](https://github.com/meshtastic/firmware) | T-Deck / T-Deck Plus targets (e.g. `t-deck-tft`). |
| **Meshtastic** (LilyGO fork) | [Xinyuan-LilyGO/Meshtastic_firmware](https://github.com/Xinyuan-LilyGO/Meshtastic_firmware) | Device builds. |
| **T-Deck hardware / examples** | [Xinyuan-LilyGO/T-Deck](https://github.com/Xinyuan-LilyGO/T-Deck) | Schematics, board files, examples, TFT_eSPI. |

**Meshtastic org (apps/tooling):** [meshtastic](https://github.com/meshtastic) — firmware, web, Android, Apple, Python CLI, protos, docs.

---

## raspberry_pi_zero (Raspberry Pi Zero 2 W)

| Firmware / OS | Repo / URL | Notes |
|---------------|------------|--------|
| **Boot / GPU firmware** | [raspberrypi/firmware](https://github.com/raspberrypi/firmware) | Boot blobs, kernel, modules for `/boot`. |
| **Kernel** | [raspberrypi/linux](https://github.com/raspberrypi/linux) | BCM2710/BCM2835 family. |
| **Documentation** | [raspberrypi/documentation](https://github.com/raspberrypi/documentation) | Official docs. |
| **Raspberry Pi OS** | [raspberrypi.com/software](https://www.raspberrypi.com/software/) | Official OS images / Imager. |
| **Buildroot** | [buildroot/buildroot](https://github.com/buildroot/buildroot) | `board/raspberrypi`, e.g. `raspberrypi0_2w_defconfig`. |
| **Yocto BSP** | [meta-raspberrypi](https://git.yoctoproject.org/meta-raspberrypi) | Yocto layer for RPi. |

---

## raspberry_pi_v4 (Raspberry Pi 4)

| Firmware / OS | Repo / URL | Notes |
|---------------|------------|--------|
| **Boot / GPU firmware** | [raspberrypi/firmware](https://github.com/raspberrypi/firmware) | |
| **Kernel** | [raspberrypi/linux](https://github.com/raspberrypi/linux) | BCM2711. |
| **Raspberry Pi OS** | [raspberrypi.com/software](https://www.raspberrypi.com/software/) | |
| **Buildroot** | [buildroot/buildroot](https://github.com/buildroot/buildroot) | e.g. `raspberrypi4_64_defconfig`. |
| **Yocto BSP** | [agherzan/meta-raspberrypi](https://github.com/agherzan/meta-raspberrypi) | Community Yocto layer. |

---

## raspberry_pi_v5 (Raspberry Pi 5)

| Firmware / OS | Repo / URL | Notes |
|---------------|------------|--------|
| **Boot / RP1 firmware** | [raspberrypi/firmware](https://github.com/raspberrypi/firmware) | |
| **Kernel** | [raspberrypi/linux](https://github.com/raspberrypi/linux) | BCM2712, RP1. |
| **Raspberry Pi OS** | [raspberrypi.com/software](https://www.raspberrypi.com/software/) | |

---

## pine64 (Pine A64)

| Firmware / OS | Repo / URL | Notes |
|---------------|------------|--------|
| **Armbian** | [armbian/build](https://github.com/armbian/build) | Pine A64 images. |
| **linux-sunxi** | [linux-sunxi.org](https://linux-sunxi.org/) | Allwinner kernel, U-Boot. |
| **Buildroot** | [buildroot.org](https://buildroot.org/) | sunxi/a64 defconfigs. |
| **PINE64 wiki** | [wiki.pine64.org/wiki/Pine_A64](https://wiki.pine64.org/wiki/Pine_A64) | Pinout, OS list. |

---

## rock64 (PINE64 Rock64)

| Firmware / OS | Repo / URL | Notes |
|---------------|------------|--------|
| **Ayufan images** | [ayufan/rock64-images](https://github.com/ayufan/rock64-images) | Prebuilt images + build. |
| **Ayufan Linux build** | [ayufan-rock64/linux-build](https://github.com/ayufan-rock64/linux-build) | Build scripts, tools. |
| **Ayufan kernel** | [ayufan-rock64/linux-kernel](https://github.com/ayufan-rock64) | Rockchip-based kernel. |
| **Ayufan mainline** | [ayufan-rock64/linux-mainline-kernel](https://github.com/ayufan-rock64) | Mainline kernel. |
| **Ayufan packages** | [ayufan-rock64/linux-package](https://github.com/ayufan-rock64/linux-package) | Compatibility package. |
| **Armbian** | [armbian/build](https://github.com/armbian/build) | Rock64 (RK3328). |
| **Rockchip kernel** | [rockchip-linux/kernel](https://github.com/rockchip-linux/kernel) | RK3328. |
| **PINE64 wiki** | [wiki.pine64.org/wiki/ROCK64](https://wiki.pine64.org/wiki/ROCK64) | |

---

## rockpro64 (PINE64 RockPro64)

| Firmware / OS | Repo / URL | Notes |
|---------------|------------|--------|
| **Ayufan images** | [ayufan/rock64-images](https://github.com/ayufan/rock64-images) | RockPro64 supported. |
| **Ayufan build/kernel** | [ayufan-rock64](https://github.com/ayufan-rock64) | linux-build, linux-kernel, etc. |
| **Armbian** | [armbian/build](https://github.com/armbian/build) | RockPro64. |
| **Rockchip kernel** | [rockchip-linux/kernel](https://github.com/rockchip-linux/kernel) | RK3399. |
| **PINE64 wiki** | [wiki.pine64.org/wiki/ROCKPro64](https://wiki.pine64.org/wiki/ROCKPro64) | |

---

## pine_phone (PINE64 PinePhone)

| Firmware / OS | Repo / URL | Notes |
|---------------|------------|--------|
| **postmarketOS** | [postmarketOS](https://postmarketos.org/) | Mainline-based; source on postmarketos.org. |
| **Manjaro ARM** | [manjaro.org/downloads/arm/pinephone](https://manjaro.org/downloads/arm/pinephone/) | Official images. |
| **Manjaro dev (GitHub)** | [manjaro-pinephone](https://github.com/manjaro-pinephone) | plasma-mobile, phosh, gnome-mobile, lomiri, arm-profiles. |
| **Kernel** | [megi/linux-pine64-phone](https://github.com/megi/linux-pine64-phone) | PinePhone kernel tree. |
| **Mobian** | [Mobian](https://mobian-project.org/) | Debian for mobile; [droidian/mobian-recipes](https://github.com/droidian/mobian-recipes); [paralin/mobian-pinephone-tweaks](https://github.com/paralin/mobian-pinephone-tweaks). |
| **UBports (Ubuntu Touch)** | [ubuntu-touch.io](https://ubuntu-touch.io/) | |
| **PINE64 wiki** | [wiki.pine64.org/wiki/PinePhone](https://wiki.pine64.org/wiki/PinePhone) | |

---

## pine_time (PINE64 PineTime)

| Firmware / project | Repo / URL | Notes |
|--------------------|------------|--------|
| **InfiniTime** | [InfiniTimeOrg/InfiniTime](https://github.com/InfiniTimeOrg/InfiniTime) | FreeRTOS-based; PlatformIO/CMake. |
| **Zephyr (official board)** | [Zephyr pinetime_devkit0](https://docs.zephyrproject.org/latest/boards/pine64/pinetime_devkit0/doc/index.html) | Board: `pinetime_devkit0`. |
| **nRF Connect SDK** | [nrfconnect/sdk-nrf](https://github.com/nrfconnect/sdk-nrf) | Zephyr-based; PineTime support. |
| **Hypnos** (Zephyr) | [albsod/pinetime-hypnos](https://github.com/albsod/pinetime-hypnos) | Zephyr firmware; ~1 week battery, LVGL. |
| **wasp-os** (MicroPython) | [wasp-os/wasp-os](https://github.com/wasp-os/wasp-os) | MicroPython; switchable with InfiniTime. |
| **wasp-os bootloader** | [wasp-os/wasp-bootloader](https://github.com/wasp-os/wasp-bootloader) | OTA bootloader. |
| **wasp-reloader** | [wasp-os/wasp-reloader](https://github.com/wasp-os/wasp-reloader) | Switch InfiniTime ↔ wasp-os. |
| **pinotime** (MicroPython) | [MrPicklePinosaur/pinotime](https://github.com/MrPicklePinosaur/pinotime) | MicroPython dev environment. |
| **PINE64 PineTime** | [pine64.org/pinetime](https://www.pine64.org/pinetime/) | Specs, software links. |

---

## arduino_uno (Arduino Uno R3)

| Firmware / framework | Repo / URL | Notes |
|----------------------|------------|--------|
| **Arduino AVR core** | [arduino/ArduinoCore-avr](https://github.com/arduino/ArduinoCore-avr) | ATmega328P, etc. |
| **PlatformIO AVR** | [platformio/platform-atmelavr](https://github.com/platformio/platform-atmelavr) | Board `uno`. |
| **Arduino IDE** | [arduino.cc/en/software](https://www.arduino.cc/en/software) | |
| **arduino-cli** | [arduino.github.io/arduino-cli](https://arduino.github.io/arduino-cli/) | CLI build/upload. |

---

## teensy_v3 (Teensy v3.2)

| Firmware / framework | Repo / URL | Notes |
|----------------------|------------|--------|
| **Teensyduino cores** | [PaulStoffregen/cores](https://github.com/PaulStoffregen/cores) | teensy3. |
| **Teensy loader** | [paulstoffregen/teensy_loader](https://github.com/paulstoffregen/teensy_loader) | Flash from host. |
| **PlatformIO Teensy** | [platformio/platform-teensy](https://github.com/platformio/platform-teensy) | Board `teensy31` / `teensy32`. |
| **Teensyduino** | [pjrc.com/teensy/teensyduino](https://www.pjrc.com/teensy/teensyduino.html) | Arduino add-on. |
| **PJRC Teensy** | [pjrc.com/teensy](https://www.pjrc.com/teensy/) | Docs, pinout. |

---

## teensy_v4 (Teensy v4.1)

| Firmware / framework | Repo / URL | Notes |
|----------------------|------------|--------|
| **Teensyduino cores** | [PaulStoffregen/cores](https://github.com/PaulStoffregen/cores) | teensy4. |
| **Teensy loader** | [paulstoffregen/teensy_loader](https://github.com/paulstoffregen/teensy_loader) | |
| **PlatformIO Teensy** | [platformio/platform-teensy](https://github.com/platformio/platform-teensy) | Board `teensy40` / `teensy41`. |
| **Zephyr** | PlatformIO / Zephyr | Optional RTOS target. |
| **Teensyduino / PJRC** | [pjrc.com/teensy](https://www.pjrc.com/teensy/) | |

---

## Cross-cutting

| Resource | Repo / URL |
|----------|------------|
| **Meshtastic organization** | [github.com/meshtastic](https://github.com/meshtastic) — firmware, web, Meshtastic-Android, Meshtastic-Apple, python, protos, meshtastic (site), etc. |
| **Lab repo index** | [REPOS.md](REPOS.md) |

---

*Generated from project documentation and public firmware/OS sources. Prebuilt binaries and third-party forks are use-at-your-own-risk; prefer upstream where possible.*
