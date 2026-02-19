# Docker Dependencies — platformio-lab

Explicit list of **apt** and **pip** packages in the primary lab image, with rationale. Use this to maintain [Dockerfile](Dockerfile) and to reason about adding/removing tools.

---

## Apt packages

| Package | Purpose |
|---------|--------|
| **build-essential** | gcc, g++, make — C/C++ builds (kernel, ESP-IDF, generic). |
| **cmake** | ESP-IDF, Zephyr, MeshCore/Meshtastic, Launcher. |
| **ninja-build** | Fast builds; used by ESP-IDF and many CMake projects. |
| **git** | Clone repos (firmware, overlays, Buildroot). |
| **curl** | Download scripts, SDK installers. |
| **python3** | PlatformIO, esptool, scripts. |
| **python3-pip** | Install pip tools (platformio, esptool, pyserial). |
| **python3-venv** | Isolated Python envs if needed. |
| **libusb-1.0-0** | USB access for flashing/debug (when used in container). |
| **udev** | Device node rules for USB serial. |
| **gcc-arm-linux-gnueabihf** | 32-bit ARM (RPi 0/1/2/3 32-bit OS). |
| **g++-arm-linux-gnueabihf** | C++ for same. |
| **gcc-aarch64-linux-gnu** | 64-bit ARM (RPi 3/4/5, Pine64 SBCs). |
| **g++-aarch64-linux-gnu** | C++ for same. |
| **picocom** | Serial console (MeshCore/Meshtastic CLI, config). |
| **screen** | Alternative serial console. |
| **wget** | Fetch toolchains, SDK tarballs. |
| **unzip** | Extract PIO packages, SDKs. |

### Optional (not in base image)

- **libncurses5-dev flex bison** — ESP-IDF menuconfig (PIO often ships these via platform).
- **openocd** — SWD/JTAG debug (PineTime, nRF52); can be added if debugging in container.
- **adafruit-nrfutil** — nRF52 DFU (MeshCore nRF devices); `pip install adafruit-nrfutil` when needed.

---

## Pip packages (pinned in Dockerfile for reproducible builds)

| Package | Pinned version | Purpose |
|---------|----------------|---------|
| **platformio** | 6.1.19 | Build and library manager for ESP32, Arduino, Teensy, nRF52. |
| **esptool** | 4.11.0 (from GitHub tag v4.11.0) | ESP32 flash, merge_bin, image_info. PyPI sdists have broken metadata; Dockerfile installs from git. |
| **pyserial** | 3.5 | Python serial access for config scripts, repeater/room-server CLI automation. |
| **arduino-cli** | (optional, unpinned) | Arduino builds without PIO. Install may fail; image still usable. |

To change versions: set `ARG PLATFORMIO_VERSION=...` (and `ESPTOOL_VERSION`, `PYSERIAL_VERSION`) in the Dockerfile, then update this table.

---

## Other tools (binary in image)

| Tool | Purpose |
|------|---------|
| **mklittlefs** | LittleFS filesystem image builder; required for Meshtastic `t-beam-1w` (data partition). From [earlephilhower/mklittlefs](https://github.com/earlephilhower/mklittlefs) releases. |

---

## Version notes

- **Ubuntu base:** 22.04 (default); change via `BASE_IMAGE`.
- **Python:** Use system Python 3 for pip installs; avoid `--break-system-packages` where possible (container is ephemeral).
- **PlatformIO:** Pinned for reproducibility; installs its own per-platform toolchains (espressif32, atmelavr, teensy, nordicnrf52) on first build.
- **mklittlefs:** 4.1.0 (commit 42acb97); see Dockerfile `MKLITTLEFS_VERSION` / `MKLITTLEFS_COMMIT`.

---

## Adding a dependency

1. Add **apt**: `RUN apt-get update && apt-get install -y --no-install-recommends <pkg> && rm -rf /var/lib/apt/lists/*`
2. Add **pip**: `RUN pip3 install --no-cache-dir <pkg>`
3. Document here and in [TOOLS_AND_SDK.md](TOOLS_AND_SDK.md) if it’s a user-facing tool.
