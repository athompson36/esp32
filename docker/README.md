# Lab Docker Containers

**Build in container, flash from host.** All firmware builds for this lab should run inside the container; do not mix host toolchains with lab firmware. Flash and serial from macOS (or host) only. See [CONTEXT.md](../CONTEXT.md) for the container strategy.

- **SDKs & tools (all devices):** [TOOLS_AND_SDK.md](TOOLS_AND_SDK.md)
- **Apt/pip dependencies and rationale:** [DEPENDENCIES.md](DEPENDENCIES.md)

## platformio-lab (primary)

Single image that provides toolchains for **ESP32**, **Arduino** (Uno, etc.), **Teensy** (3.x, 4.x), and **ARM cross-compilation** for **Raspberry Pi** and **Pine64** SBCs. Used for Meshtastic, MeshCore, Arduino-based firmware, and ARM Linux builds.

### Included toolchains / targets

| Target | Toolchain / tool | Notes |
|--------|------------------|--------|
| ESP32 (all variants) | PlatformIO + espressif32 | ESP-IDF or Arduino framework |
| Arduino Uno (AVR) | PlatformIO + atmelavr | ATmega328P |
| Teensy v3.2 / v4.1 | PlatformIO + teensy | ARM Cortex-M4/M7 |
| Raspberry Pi (Zero, 4, 5) | gcc-arm-linux-gnueabihf, gcc-aarch64-linux-gnu | 32-bit and 64-bit ARM |
| Pine64 SBCs (Pine64, Rock64, RockPro64, PinePhone) | gcc-aarch64-linux-gnu | 64-bit ARM |
| PineTime (nRF52832) | PlatformIO + nordicnrf52 | Zephyr/InfiniTime |

### Build

```bash
docker build -t platformio-lab -f docker/Dockerfile .
```

### Run (example)

From repo root:

```bash
docker run --rm -v "$(pwd):/workspace" -w /workspace/devices/t_beam_1w/firmware/meshcore/repo platformio-lab pio run -e T_Beam_1W_SX1262_repeater
```

Or use the minimal orchestrator (builds and copies to `artifacts/<device>/<firmware>/<version>/`):

```bash
./scripts/lab-build.sh t_beam_1w meshcore T_Beam_1W_SX1262_repeater
```

## esp-idf-lab (L6)

For **ESP-IDF native** projects (no PlatformIO): custom firmware, LVGL, Lumari Watch, T-Deck Launcher. Based on official [espressif/idf](https://hub.docker.com/r/espressif/idf) image (ESP-IDF v5.2).

### Build

```bash
docker build -t esp-idf-lab -f docker/Dockerfile.esp-idf-lab .
```

Optional: pin a different IDF version, e.g. `--build-arg IDF_TAG=v5.1`.

### Run (example)

From repo root, for a cloned Lumari Watch repo:

```bash
docker run --rm -v "$(pwd):/workspace" -w /workspace/devices/lumari_watch/firmware/lumari_watch/repo \
  -e HOME=/tmp esp-idf-lab bash -c "idf.py set-target esp32s3 && idf.py build"
```

Or use the orchestrator (builds and copies to `artifacts/<device>/<firmware>/<version>/`):

```bash
./scripts/lab-build.sh lumari_watch lumari_watch
```

### Included

- ESP-IDF (version set by `IDF_TAG`, default v5.2), `idf.py`, CMake, Ninja
- udev, libusb, picocom (serial when device passed through)
- `IDF_GIT_SAFE_DIR=/workspace` so mounted git repos do not trigger "dubious ownership"

## Other containers (future)

- **rust-embedded-lab**: PineTime (Embassy), NRF, Rust targets.
- **rf-lab**: SDR, spectrum, LoRa sniffing.

## Golden rule

Do not mix unrelated toolchains in one container. This image groups PlatformIO-based targets and ARM Linux toolchains that are commonly used together for device firmware and companion builds.
