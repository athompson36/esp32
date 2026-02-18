# Devices Directory

All hardware targets for this lab live under `/devices`. Each device has a **strict folder contract** so builds, pinmaps, and notes stay consistent.

## Folder Contract (Required)

Every device **MUST** have:

```
device_name/
├── firmware/     # Firmware repos + overlays (meshtastic/, meshcore/, custom/)
├── configs/      # Build/config examples, channel presets, device configs
├── pinmaps/      # Hardware layout, pinout, peripheral pin assignments
└── notes/        # Prototyping, quirks, known issues, hardware variants
```

## Context Files (Per Device)

Each device should provide:

| File | Purpose |
|------|---------|
| **DEVICE_CONTEXT.md** | Device identity, MCU, summary, links to layout/peripherals/prototyping |
| **pinmaps/HARDWARE_LAYOUT.md** | Complete hardware layout: pinout table, block diagram, power tree |
| **pinmaps/PERIPHERALS.md** | Available peripherals: GPIO/bus assignments, drivers, constraints |
| **notes/PROTOTYPING.md** | Free GPIOs, expansion headers, do/don't, safety |
| **notes/SDK_AND_TOOLS.md** | SDKs, CLI tools, Docker dependencies, flash/serial |
| **firmware/README.md** | Available firmware/OS repos and build systems |

See `t_beam_1w/` for the reference implementation.

## Devices in This Lab

### ESP32 / LoRa

| Device | Description | Context |
|--------|-------------|---------|
| **t_beam_1w** | LilyGO T-Beam 1W (ESP32-S3, SX1262, 1W PA) | [DEVICE_CONTEXT.md](t_beam_1w/DEVICE_CONTEXT.md) |
| **t_deck_plus** | LilyGO T-Deck Plus (launcher, maps, Meshtastic) | [DEVICE_CONTEXT.md](t_deck_plus/DEVICE_CONTEXT.md) |

### Raspberry Pi

| Device | Description | Context |
|--------|-------------|---------|
| **raspberry_pi_zero** | Raspberry Pi Zero 2 W (BCM2710A1, 40-pin) | [DEVICE_CONTEXT.md](raspberry_pi_zero/DEVICE_CONTEXT.md) |
| **raspberry_pi_v4** | Raspberry Pi 4 Model B (BCM2711, 40-pin) | [DEVICE_CONTEXT.md](raspberry_pi_v4/DEVICE_CONTEXT.md) |
| **raspberry_pi_v5** | Raspberry Pi 5 (BCM2712 + RP1, 40-pin) | [DEVICE_CONTEXT.md](raspberry_pi_v5/DEVICE_CONTEXT.md) |

### Pine64

| Device | Description | Context |
|--------|-------------|---------|
| **pine64** | Pine A64 (Allwinner A64, Euler bus) | [DEVICE_CONTEXT.md](pine64/DEVICE_CONTEXT.md) |
| **rock64** | PINE64 Rock64 (RK3328, 40-pin RPi-compatible) | [DEVICE_CONTEXT.md](rock64/DEVICE_CONTEXT.md) |
| **rockpro64** | PINE64 RockPro64 (RK3399, 40-pin) | [DEVICE_CONTEXT.md](rockpro64/DEVICE_CONTEXT.md) |
| **pine_phone** | PINE64 PinePhone (Linux smartphone) | [DEVICE_CONTEXT.md](pine_phone/DEVICE_CONTEXT.md) |
| **pine_time** | PINE64 PineTime (nRF52832 smartwatch) | [DEVICE_CONTEXT.md](pine_time/DEVICE_CONTEXT.md) |

### Arduino / Teensy

| Device | Description | Context |
|--------|-------------|---------|
| **arduino_uno** | Arduino Uno R3 (ATmega328P) | [DEVICE_CONTEXT.md](arduino_uno/DEVICE_CONTEXT.md) |
| **teensy_v3** | PJRC Teensy v3.2 (MK20DX256, Cortex-M4) | [DEVICE_CONTEXT.md](teensy_v3/DEVICE_CONTEXT.md) |
| **teensy_v4** | PJRC Teensy v4.1 (i.MX RT1062, Cortex-M7) | [DEVICE_CONTEXT.md](teensy_v4/DEVICE_CONTEXT.md) |

## Build Container

All of the above devices are supported by the **platformio-lab** Docker image (ESP32, Arduino, Teensy via PlatformIO; Raspberry Pi and Pine64 SBCs via ARM cross-compilers). See [../docker/README.md](../docker/README.md).

## Adding a New Device

1. Create `devices/<device_name>/` with the four subdirs above.
2. Add `DEVICE_CONTEXT.md` and the pinmaps/, notes/, and firmware/README.md context files.
3. Add firmware under `firmware/` (e.g. `meshcore/repo/`, `meshtastic/repo/`) and use overlays only for customisations.
4. Update this README with the new device.
