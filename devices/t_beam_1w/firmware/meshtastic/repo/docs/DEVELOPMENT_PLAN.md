# Development Plan — T-Beam 1W Firmware Port

## Executive Summary

This document outlines the complete development plan for adding Meshtastic firmware support for the LilyGO T-Beam 1W (ESP32-S3) board. The project requires cloning the upstream Meshtastic firmware, applying custom templates, configuring GPIO pins, and ensuring all dependencies are met.

---

## 1. Dependency Status

### ✅ Installed Dependencies
- **Git**: v2.50.1 (Apple Git-155) — Required for cloning Meshtastic firmware
- **Homebrew**: v5.0.11 — Package manager for macOS
- **esptool**: v5.1.0 — ESP32 flashing tool (installed via pipx)

### ❌ Missing Dependencies
- **PlatformIO Core**: Not installed — Required for building firmware
  - Install: `brew install platformio`
  - Verify: `platformio --version`

### 📦 External Dependencies (To Be Cloned)
- **Meshtastic Firmware**: Not cloned — Upstream repository
  - Clone: `git clone https://github.com/meshtastic/firmware.git firmware`
  - Location: `./firmware/` (project root)

---

## 2. Project Structure Status

### ✅ Existing Assets
- **Templates**: `patches/templates/variants/tbeam_1w/` (variant.h, variant.cpp)
- **PlatformIO Config**: `patches/platformio.env.tbeam-1w.ini`
- **Documentation**: Pin map template, build notes, project context
- **Scripts**: `scripts/build.sh`, `scripts/flash.sh` (executable)

### ⚠️ Incomplete Assets
- **Pin Mapping**: `docs/TBEAM_1W_PINMAP.md` — Template exists but pins not filled in
  - **CRITICAL**: Must be populated from official LilyGO T-Beam 1W documentation/schematic
  - **RISK**: Wrong PA/LNA pins can damage RF front-end

---

## 3. Development Phases

### Phase 1: Environment Setup ✅ (Current Status)

**Tasks:**
1. ✅ Verify system dependencies (git, homebrew, esptool)
2. ❌ Install PlatformIO Core
3. ❌ Clone Meshtastic firmware repository

**Commands:**
```bash
# Install PlatformIO
brew install platformio

# Verify installation
platformio --version

# Clone Meshtastic firmware
cd /Users/andrew/Documents/fs-tech/meshtastic-tbeam-1w-firmware
git clone https://github.com/meshtastic/firmware.git firmware
```

**Verification:**
- [ ] PlatformIO installed and accessible
- [ ] `firmware/` directory exists
- [ ] `firmware/platformio.ini` exists

---

### Phase 2: Pin Mapping Research 🔍

**Tasks:**
1. Research LilyGO T-Beam 1W (ESP32-S3) pinout
2. Document GPIO pins in `docs/TBEAM_1W_PINMAP.md`
3. Verify pin assignments against schematic (if available)

**Required Pin Categories:**
- **LoRa Radio (SX1262)**:
  - SPI pins (SCK, MOSI, MISO, CS/NSS)
  - Control pins (RESET, BUSY, DIO1)
  - Front-end control (TXEN/PA_EN, RXEN/LNA_EN)
- **I2C Bus**:
  - SDA, SCL
  - OLED address (typically 0x3C)
  - PMU address (AXP2101, typically 0x34)
- **GNSS (L76K)**:
  - UART TX/RX pins
  - Baud rate (typically 9600)
- **Display**:
  - Driver type (SH1106 verification needed)
  - Resolution
- **Buttons/LEDs**:
  - User button GPIO
  - LED GPIO (if present)

**Sources to Check:**
- LilyGO official documentation
- T-Beam 1W schematic (if available)
- Community forums/pinout diagrams
- Existing T-Beam variants in Meshtastic firmware (for reference)

**Verification:**
- [ ] All GPIO pins documented in `TBEAM_1W_PINMAP.md`
- [ ] No placeholder values (`GPIO_NUM_NC` or `__`) remain
- [ ] PA/LNA pins verified from official source

---

### Phase 3: Template Application 🔧

**Tasks:**
1. Copy variant files to Meshtastic firmware
2. Merge PlatformIO environment configuration
3. Populate pin definitions in variant.h

**Commands:**
```bash
# Copy variant directory
cp -r patches/templates/variants/tbeam_1w firmware/variants/

# Verify variant files exist
ls -la firmware/variants/tbeam_1w/
```

**PlatformIO Configuration:**
1. Open `firmware/platformio.ini`
2. Locate `[env:esp32s3_base]` (or equivalent ESP32-S3 base environment)
3. Append contents of `patches/platformio.env.tbeam-1w.ini` to `platformio.ini`
4. Verify `extends = env:esp32s3_base` references a valid environment

**Variant.h Updates:**
1. Open `firmware/variants/tbeam_1w/variant.h`
2. Replace all `GPIO_NUM_NC` placeholders with actual GPIO numbers from `TBEAM_1W_PINMAP.md`
3. Uncomment and configure feature flags as needed:
   - `USE_SH1106` (if display is SH1106)
   - `HAS_PMU_AXP2101` (if PMU is AXP2101)

**Verification:**
- [ ] `firmware/variants/tbeam_1w/variant.h` exists
- [ ] `firmware/variants/tbeam_1w/variant.cpp` exists
- [ ] `[env:tbeam-1w]` section added to `platformio.ini`
- [ ] All GPIO pins populated (no `GPIO_NUM_NC`)

---

### Phase 4: Build Configuration Verification 🔍

**Tasks:**
1. Verify PlatformIO environment dependencies
2. Check for required build flags
3. Verify variant include paths

**PlatformIO Environment Checks:**
- [ ] `env:esp32s3_base` exists in `platformio.ini`
- [ ] Board definition `esp32-s3-devkitc-1` is valid
- [ ] Build flags include:
  - `-D LILYGO_TBEAM_1W`
  - `-D VARIANT_TBEAM_1W`
  - `-I variants/tbeam_1w`

**Additional Build Flags (May Be Required):**
Check Meshtastic firmware version and add if needed:
- `-D USE_SX1262` (if not auto-detected)
- `-D HAS_GPS=1` (if GPS support needed)
- `-D OLED_I2C` (if I2C OLED)
- `-D USE_SH1106` (if SH1106 display)

**Verification:**
- [ ] PlatformIO can parse `platformio.ini` without errors
- [ ] Environment `tbeam-1w` appears in `pio env list`

---

### Phase 5: Initial Build Test 🏗️

**Tasks:**
1. Attempt first build
2. Resolve compilation errors
3. Verify build artifacts

**Commands:**
```bash
cd firmware
pio run -e tbeam-1w
```

**Expected Issues & Solutions:**
- **Missing base environment**: Copy settings from existing ESP32-S3 environment
- **Undefined GPIO pins**: Ensure all pins populated in variant.h
- **Missing feature flags**: Add required `-D` flags to build_flags
- **Include path errors**: Verify `-I variants/tbeam_1w` in build_flags
- **Variant function not found**: Check if Meshtastic version expects `variantInit()` call

**Verification:**
- [ ] Build completes without errors
- [ ] Firmware binary generated: `.pio/build/tbeam-1w/firmware.bin`
- [ ] Build size is reasonable (check for bloat)

---

### Phase 6: Code Integration Points 🔗

**Tasks:**
1. Identify where variant.h is included in Meshtastic codebase
2. Verify compile-time flag usage (`#ifdef LILYGO_TBEAM_1W`)
3. Check for variant initialization hooks

**Key Files to Review:**
- Radio driver initialization (SX1262)
- I2C initialization (OLED, PMU)
- GPS/UART initialization
- Display driver initialization
- Power management (PMU)

**Search Patterns:**
```bash
cd firmware
grep -r "LILYGO_TBEAM" src/
grep -r "variant.h" src/
grep -r "variantInit" src/
```

**Verification:**
- [ ] Variant header is included where needed
- [ ] Board-specific code uses `#ifdef LILYGO_TBEAM_1W`
- [ ] No hardcoded GPIO pins conflict with T-Beam 1W

---

### Phase 7: Hardware Testing 🧪

**Tasks:**
1. Flash firmware to T-Beam 1W board
2. Verify serial output
3. Test basic functionality

**Flash Procedure:**
1. Disconnect battery
2. Hold BOOT button
3. Plug in USB-C cable
4. Release BOOT after 5-8 seconds
5. Flash firmware

**Commands:**
```bash
# Find USB port
ls /dev/cu.usbmodem*

# Flash (replace PORT with actual port)
./scripts/flash.sh /dev/cu.usbmodemXXXX
```

**Serial Monitoring:**
```bash
# Monitor serial output (baud rate may vary)
screen /dev/cu.usbmodemXXXX 115200
# or
pio device monitor -e tbeam-1w
```

**Test Checklist:**
- [ ] Board boots (serial logs visible)
- [ ] Radio initializes (check for SX1262 init messages)
- [ ] GPS detected (if applicable)
- [ ] Display works (if applicable)
- [ ] Device discoverable in Meshtastic app
- [ ] No RF front-end errors (check PA/LNA pin behavior)

---

### Phase 8: Refinement & Documentation 📝

**Tasks:**
1. Fix any runtime issues discovered
2. Update documentation with actual pin values
3. Document any Meshtastic version-specific notes
4. Create troubleshooting guide

**Documentation Updates:**
- [ ] `docs/TBEAM_1W_PINMAP.md` — Final pin values documented
- [ ] `docs/BUILD_NOTES.md` — Add any version-specific build notes
- [ ] `README.md` — Update with verified build/flash commands

**Verification:**
- [ ] All documentation reflects actual implementation
- [ ] Build commands work reliably
- [ ] Flash procedure documented and tested

---

## 4. Risk Assessment

### High Risk Items
1. **Incorrect PA/LNA GPIO pins** — Can damage RF front-end
   - **Mitigation**: Verify from official schematic/documentation only
   
2. **Missing base PlatformIO environment** — Build will fail
   - **Mitigation**: Check Meshtastic firmware version, adapt base env if needed

3. **Pin conflicts with existing code** — Runtime failures
   - **Mitigation**: Use compile-time flags, isolate board-specific code

### Medium Risk Items
1. **Meshtastic firmware version incompatibility** — API changes
   - **Mitigation**: Test with stable Meshtastic release, check changelog

2. **Display driver mismatch** — Display won't work
   - **Mitigation**: Verify display type (SH1106 vs SSD1306) from hardware

### Low Risk Items
1. **Build tool version differences** — Minor compatibility issues
   - **Mitigation**: Use recommended PlatformIO version

---

## 5. Success Criteria

### Build Success
- ✅ `pio run -e tbeam-1w` completes without errors
- ✅ Firmware binary generated: `.pio/build/tbeam-1w/firmware.bin`
- ✅ Build size within ESP32-S3 flash limits

### Runtime Success
- ✅ Board boots and shows serial output
- ✅ Radio (SX1262) initializes correctly
- ✅ GPS module detected (if applicable)
- ✅ Display functional (if applicable)
- ✅ Device discoverable in Meshtastic mobile app
- ✅ No RF front-end errors or warnings

### Code Quality
- ✅ All GPIO pins documented and verified
- ✅ Board-specific code isolated behind `#ifdef` flags
- ✅ No breaking changes to existing Meshtastic targets
- ✅ Code follows Meshtastic formatting/style guidelines

---

## 6. Next Steps (Immediate Actions)

1. **Install PlatformIO**:
   ```bash
   brew install platformio
   ```

2. **Clone Meshtastic Firmware**:
   ```bash
   git clone https://github.com/meshtastic/firmware.git firmware
   ```

3. **Research Pin Mapping**:
   - Find official T-Beam 1W pinout documentation
   - Fill in `docs/TBEAM_1W_PINMAP.md`

4. **Apply Templates**:
   - Copy variant files
   - Merge PlatformIO config
   - Populate GPIO pins

5. **First Build Attempt**:
   ```bash
   cd firmware
   pio run -e tbeam-1w
   ```

---

## 7. Dependencies Summary

### System Dependencies
- ✅ Git (installed)
- ✅ Homebrew (installed)
- ✅ esptool (installed)
- ❌ PlatformIO Core (needs installation)

### Project Dependencies
- ❌ Meshtastic firmware repository (needs cloning)
- ⚠️ T-Beam 1W pin mapping documentation (needs research)

### Build Dependencies (Managed by PlatformIO)
- ESP32-S3 toolchain (auto-installed by PlatformIO)
- Meshtastic firmware libraries (included in cloned repo)
- PlatformIO packages (auto-resolved from platformio.ini)

---

## 8. Timeline Estimate

- **Phase 1 (Setup)**: 15 minutes
- **Phase 2 (Pin Research)**: 1-2 hours (depends on documentation availability)
- **Phase 3 (Template Application)**: 30 minutes
- **Phase 4 (Build Config)**: 30 minutes
- **Phase 5 (Initial Build)**: 1-2 hours (depends on issues)
- **Phase 6 (Integration)**: 1-2 hours
- **Phase 7 (Hardware Testing)**: 1-2 hours
- **Phase 8 (Documentation)**: 30 minutes

**Total Estimated Time**: 6-10 hours (excluding waiting for hardware testing)

---

## 9. Notes

- This is a fork/starter project — Meshtastic firmware must be cloned separately
- All changes should be minimal and isolated to avoid breaking upstream
- Pin mapping is the most critical step — do not proceed without verified pins
- Test on actual hardware before considering complete
- Keep upstream Meshtastic formatting/style when making changes
