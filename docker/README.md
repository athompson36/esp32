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

## Other containers (future)

- **esp-idf-lab**: ESP-IDF native, LVGL.
- **rust-embedded-lab**: PineTime (Embassy), NRF, Rust targets.
- **rf-lab**: SDR, spectrum, LoRa sniffing.

## Golden rule

Do not mix unrelated toolchains in one container. This image groups PlatformIO-based targets and ARM Linux toolchains that are commonly used together for device firmware and companion builds.
