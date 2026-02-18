# Project Context — Meshtastic LilyGO T‑Beam 1W (ESP32‑S3)

## Objective
Add a new Meshtastic build target for **LilyGO T‑Beam 1W (ESP32‑S3)**.

## Success criteria
- `pio run -e tbeam-1w` builds successfully.
- The resulting binary boots on the board (serial logs visible; device is discoverable in Meshtastic apps via supported transports).
- Variant pins (radio, I2C, display, GNSS, PMU, PA/LNA) are documented and not guessed.

## Repo layout assumption
We will work inside the official Meshtastic firmware repo cloned into `./firmware`.

## Implementation plan
1. Clone Meshtastic firmware into `./firmware`.
2. Add `env:tbeam-1w` to `firmware/platformio.ini` (template in `patches/platformio.env.tbeam-1w.ini`).
3. Add `firmware/variants/tbeam_1w/variant.h` and `variant.cpp` (templates in `patches/templates/variants/tbeam_1w/`).
4. Populate real GPIO pin mappings in `docs/TBEAM_1W_PINMAP.md` and copy them into `variant.h`.
5. Build with PlatformIO.
6. Flash with `esptool` (recommended for ESP32‑S3).

## Guardrails
- Do not break existing targets.
- All board-specific behavior should be behind `#ifdef LILYGO_TBEAM_1W` (or similar) defines.
- Never guess PA/LNA control pins; wrong pins can cause RF front-end issues.
