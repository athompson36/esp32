# Meshtastic T‑Beam 1W (ESP32‑S3) — Cursor Starter

This is a **Cursor starter project** to build a custom Meshtastic firmware target for the **LilyGO T‑Beam 1W (ESP32‑S3, USB‑C)**.

The zip does **not** bundle Meshtastic source. Instead, it provides:
- a repeatable clone/build workflow
- templates for a new PlatformIO environment and `variants/tbeam_1w` files
- a place to record the board’s pin mapping

## What you do with this
1. Clone Meshtastic firmware into `./firmware/` (instructions below)
2. Apply the templates in `./patches/` (Cursor can do this quickly)
3. Fill in the real pin mapping in `docs/TBEAM_1W_PINMAP.md`
4. Build with PlatformIO
5. Flash with `esptool` (works reliably on ESP32‑S3)

## Prereqs (macOS)
- Homebrew
- PlatformIO Core: `brew install platformio`
- Python tools for flashing: `pipx install esptool`

## Clone Meshtastic
From the project root:

```bash
git clone https://github.com/meshtastic/firmware.git firmware
```

## Build (after you add the new env)
```bash
cd firmware
pio run -e tbeam-1w
```

## Flash (example)
Put the board in bootloader mode (hold BOOT while plugging in USB; battery disconnected), then:

```bash
esptool --port /dev/cu.usbmodemXXXX erase-flash
esptool --port /dev/cu.usbmodemXXXX write-flash -z 0x0 .pio/build/tbeam-1w/firmware.bin
```

## Notes
- The provided variant/env templates are intentionally conservative. You will likely need to adjust:
  - SX1262 pins (SPI + DIO1/BUSY/RESET)
  - PA/LNA enable pins (1W front end)
  - OLED driver + I2C pins
