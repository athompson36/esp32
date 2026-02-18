# Dependency Checklist — T-Beam 1W Firmware Port

Quick reference checklist for verifying all dependencies are met before starting development.

## System Dependencies

### Required Tools
- [x] **Git** — v2.50.1 (installed)
  - Verify: `git --version`
  - Install: `brew install git` (if missing)

- [x] **Homebrew** — v5.0.11 (installed)
  - Verify: `brew --version`
  - Install: Visit https://brew.sh (if missing)

- [x] **esptool** — v5.1.0 (installed)
  - Verify: `esptool version`
  - Install: `pipx install esptool` (if missing)
  - Note: Requires `pipx` — install via `brew install pipx && pipx ensurepath`

- [ ] **PlatformIO Core** — NOT INSTALLED ⚠️
  - Verify: `platformio --version`
  - Install: `brew install platformio`
  - **ACTION REQUIRED**: Install before proceeding

### Optional Tools (Helpful)
- [ ] **screen** or **minicom** — Serial terminal (usually pre-installed on macOS)
  - Verify: `which screen` or `which minicom`
  - Install: `brew install screen` (if needed)

- [ ] **Python 3** — Required for esptool (usually pre-installed)
  - Verify: `python3 --version`
  - Install: `brew install python3` (if missing)

---

## Project Dependencies

### Repository Status
- [ ] **Meshtastic Firmware** — NOT CLONED ⚠️
  - Location: `./firmware/` (project root)
  - Clone: `git clone https://github.com/meshtastic/firmware.git firmware`
  - **ACTION REQUIRED**: Clone before building

### Template Files
- [x] **Variant Header** — `patches/templates/variants/tbeam_1w/variant.h` (exists)
- [x] **Variant Source** — `patches/templates/variants/tbeam_1w/variant.cpp` (exists)
- [x] **PlatformIO Config** — `patches/platformio.env.tbeam-1w.ini` (exists)

### Documentation
- [x] **Pin Map Template** — `docs/TBEAM_1W_PINMAP.md` (exists, needs pin values)
- [x] **Build Notes** — `docs/BUILD_NOTES.md` (exists)
- [x] **Project Context** — `PROJECT_CONTEXT.md` (exists)

### Scripts
- [x] **Build Script** — `scripts/build.sh` (exists, executable)
- [x] **Flash Script** — `scripts/flash.sh` (exists, executable)

---

## Build Dependencies (Auto-Resolved by PlatformIO)

These are managed automatically when PlatformIO runs, but listed for reference:

### Platform Dependencies
- [ ] **ESP32-S3 Platform** — Auto-installed by PlatformIO
- [ ] **ESP32-S3 Toolchain** — Auto-installed by PlatformIO
- [ ] **Framework** — Arduino/ESP-IDF (defined in platformio.ini)

### Library Dependencies
- [ ] **Meshtastic Libraries** — Included in cloned firmware repo
- [ ] **Radio Drivers** — SX1262 support (included in Meshtastic)
- [ ] **Display Drivers** — SH1106/SSD1306 (included in Meshtastic)
- [ ] **GPS Libraries** — L76K support (included in Meshtastic)

---

## Configuration Dependencies

### PlatformIO Configuration
- [ ] **Base Environment** — `env:esp32s3_base` must exist in `firmware/platformio.ini`
  - Check after cloning Meshtastic firmware
  - If missing, adapt from existing ESP32-S3 environment

- [ ] **Board Definition** — `esp32-s3-devkitc-1` must be valid
  - PlatformIO should recognize this board automatically

### Variant Configuration
- [ ] **GPIO Pins** — All pins populated in `variant.h`
  - Source: `docs/TBEAM_1W_PINMAP.md`
  - **CRITICAL**: No `GPIO_NUM_NC` placeholders remaining

- [ ] **Feature Flags** — Appropriate flags enabled:
  - `LILYGO_TBEAM_1W` — Board identifier
  - `VARIANT_TBEAM_1W` — Variant identifier
  - `USE_SX1262` — Radio driver (if not auto-detected)
  - `HAS_GPS=1` — GPS support (if applicable)
  - `OLED_I2C` — I2C OLED (if applicable)
  - `USE_SH1106` — SH1106 display (if applicable)
  - `HAS_PMU_AXP2101` — PMU support (if applicable)

---

## Hardware Dependencies

### Required Hardware
- [ ] **LilyGO T-Beam 1W (ESP32-S3)** — Target board
- [ ] **USB-C Cable** — For flashing and power
- [ ] **Antenna** — LoRa antenna (usually included with board)

### Optional Hardware
- [ ] **Battery** — For portable operation (disconnect during flashing)
- [ ] **Serial Adapter** — If USB-C doesn't provide serial access

---

## Verification Commands

Run these commands to verify all dependencies:

```bash
# System tools
git --version
brew --version
platformio --version
esptool version

# Project structure
test -d firmware && echo "✓ Firmware cloned" || echo "✗ Firmware missing"
test -f firmware/platformio.ini && echo "✓ platformio.ini exists" || echo "✗ platformio.ini missing"
test -d firmware/variants/tbeam_1w && echo "✓ Variant directory exists" || echo "✗ Variant directory missing"

# PlatformIO environment
cd firmware && pio env list | grep tbeam-1w && echo "✓ Environment configured" || echo "✗ Environment missing"
```

---

## Quick Start Checklist

Before starting development, ensure:

1. [ ] PlatformIO installed (`brew install platformio`)
2. [ ] Meshtastic firmware cloned (`git clone https://github.com/meshtastic/firmware.git firmware`)
3. [ ] Variant files copied (`cp -r patches/templates/variants/tbeam_1w firmware/variants/`)
4. [ ] PlatformIO config merged (append `patches/platformio.env.tbeam-1w.ini` to `firmware/platformio.ini`)
5. [ ] Pin mapping researched and documented (`docs/TBEAM_1W_PINMAP.md`)
6. [ ] GPIO pins populated in `firmware/variants/tbeam_1w/variant.h`
7. [ ] Build test successful (`cd firmware && pio run -e tbeam-1w`)

---

## Missing Dependencies Summary

### Critical (Must Fix)
1. ❌ **PlatformIO Core** — Install: `brew install platformio`
2. ❌ **Meshtastic Firmware** — Clone: `git clone https://github.com/meshtastic/firmware.git firmware`

### Important (Must Complete)
3. ⚠️ **Pin Mapping** — Research and fill `docs/TBEAM_1W_PINMAP.md`
4. ⚠️ **GPIO Configuration** — Populate pins in `variant.h`

### Optional (Can Complete Later)
5. ⚠️ **Hardware Testing** — Requires physical board
6. ⚠️ **Feature Flags** — May need adjustment after first build

---

## Next Actions

1. **Install PlatformIO**:
   ```bash
   brew install platformio
   ```

2. **Clone Meshtastic Firmware**:
   ```bash
   git clone https://github.com/meshtastic/firmware.git firmware
   ```

3. **Research Pin Mapping**:
   - Find official T-Beam 1W documentation
   - Fill in `docs/TBEAM_1W_PINMAP.md`

4. **Apply Templates**:
   - Copy variant files to firmware directory
   - Merge PlatformIO environment config

5. **First Build**:
   ```bash
   cd firmware
   pio run -e tbeam-1w
   ```
