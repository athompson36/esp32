# SDKs & Tools — Lab Reference

Single reference for **SDKs**, **CLI tools**, and **Docker** usage across all devices. Aligned with [current_project.md](../current_project.md) and the full device/firmware list.

---

## Container: platformio-lab

**Image:** Built from `docker/Dockerfile`. Use for **build**; **flash and serial** from host (macOS) per [CONTEXT.md](../CONTEXT.md).

### Toolchains (in container)

| Target | SDK / toolchain | How | Notes |
|--------|------------------|-----|--------|
| **ESP32** (all) | PlatformIO + espressif32 | `pio run -e <env>` | Arduino or ESP-IDF framework. PIO installs toolchain on first use. |
| **ESP32** (native) | ESP-IDF | `idf.py` | Install separately if not using PIO; or use PIO framework = espidf. |
| **Arduino Uno** | PlatformIO + atmelavr | `pio run -e uno` | ATmega328P. |
| **Teensy v3.2 / v4.1** | PlatformIO + teensy | `pio run -e teensy40` etc. | Arduino-style; PIO uses Teensy toolchain. |
| **PineTime (nRF52)** | PlatformIO + nordicnrf52 | `pio run -e pinetime_devkit0` | InfiniTime/Zephyr. |
| **Raspberry Pi** | gcc-arm-linux-gnueabihf, gcc-aarch64-linux-gnu | `CROSS_COMPILE=... make` | 32-bit and 64-bit ARM. |
| **Pine64 SBCs** | gcc-aarch64-linux-gnu | Same as RPi 64-bit | Kernel/rootfs builds. |

### CLI tools (in container)

| Tool | Purpose | Install |
|------|---------|--------|
| **PlatformIO** | Build, library manager, upload (when USB passed) | `pip install platformio` |
| **esptool** | ESP32 flash/merge_bin/image_info; CI and scripts | `pip install esptool` |
| **arduino-cli** | Arduino build/upload without PIO | `pip install arduino-cli` (optional) |
| **pyserial** | Serial scripting (Python) for config/CLI automation | `pip install pyserial` |
| **picocom** / **screen** | Serial console (when device attached in container) | `apt: picocom` or `screen` |
| **cmake**, **ninja** | ESP-IDF, Zephyr, generic C++ | `apt: cmake ninja-build` |
| **git**, **curl**, **wget**, **unzip** | Clone, fetch, extract | `apt` |

### Host-only (recommended)

| Tool | Purpose | Where |
|------|---------|--------|
| **esptool** | Flash ESP32 (USB reliable on host) | Host: `pipx install esptool` or `brew` |
| **Teensy loader** | Flash Teensy (GUI or CLI) | Host: [teensy_loader](https://github.com/paulstoffregen/teensy_loader) |
| **Serial monitor** | screen, minicom, PlatformIO device monitor | Host (USB attached to host) |
| **J-Link / openocd** | SWD debug (PineTime, nRF52) | Host if debugging |

---

## By device (quick map)

| Device | Build in container | Flash / debug on host |
|--------|--------------------|------------------------|
| **t_beam_1w** | `pio run -e T_Beam_1W_SX1262_*` | esptool (merge_bin or firmware.bin @ 0x0) |
| **t_deck_plus** | Launcher: LVGL/ESP-IDF; Meshtastic: PIO | esptool |
| **raspberry_pi_*** | Kernel: make + cross-compiler; rootfs: Buildroot/Yocto | SD card / USB boot |
| **pine64 / rock64 / rockpro64** | Same as RPi (aarch64) | SD / eMMC |
| **pine_phone** | Kernel + userspace (aarch64) | Flash script / SD |
| **pine_time** | `pio run` (nordicnrf52) or Zephyr | J-Link / openocd / nRF DFU |
| **arduino_uno** | `pio run` or `arduino-cli compile` | avrdude (PIO or Arduino CLI) |
| **teensy_v3.2 / v4.1** | `pio run` | Teensy loader (host) |

---

## Project relevance (current_project.md)

| Project | Devices | SDKs / tools |
|---------|---------|--------------|
| **1. Maschine MK2 mod** | ESP32, Teensy | PlatformIO (espressif32, teensy), MIDI libs, OLED |
| **2. LoRa mesh nodes** | t_beam_1w | PlatformIO, MeshCore/Meshtastic, esptool, NFC (optional) |
| **3. Pi digital mixer** | raspberry_pi_v4 | aarch64 gcc, Buildroot/kernel optional; audio stack on Pi |
| **4. ESP32 MIDI controller** | ESP32, arduino_uno | PlatformIO, BLE/USB MIDI, OLED libs |
| **5. Sensor array + dashboard** | ESP32, raspberry_pi_* | PIO, MQTT/HTTP; on Pi: Python, Grafana/InfluxDB (host or image) |
| **6. ESP32–Pi media player** | ESP32, raspberry_pi | PIO (ESP32), aarch64 (Pi); serial/Wi‑Fi |
| **7. Pi + ESP32 access control** | raspberry_pi, ESP32 | Same as above; RFID/NFC libs on ESP32 |
| **8. Art installation controllers** | ESP32 | PIO, DMX/serial, Wi‑Fi |
| **9. Pi effects rack** | raspberry_pi | aarch64, audio build deps |
| **10. Visualizer nodes** | ESP32 | PIO, LED (WS2812/APA102), MQTT/WebSocket |

---

## Other containers (future)

- **esp-idf-lab**: ESP-IDF only, LVGL (T-Deck Launcher, custom ESP32).
- **rust-embedded-lab**: PineTime (Embassy), NRF, Cargo.
- **rf-lab**: SDR (gqrx, rtl-sdr), spectrum, LoRa sniffing.

---

## References

- [CONTEXT.md](../CONTEXT.md) — container strategy, toolchain detection
- [DEPENDENCIES.md](DEPENDENCIES.md) — apt/pip list and rationale
- [README.md](README.md) — build/run commands
