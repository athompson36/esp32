# Heltec Mesh Pocket — Pinmaps

The Mesh Pocket is a **closed** product (nRF52840 + SX1262 + e-ink on a single board). User-accessible interfaces:

- **4-pin magnetic pogo** — programming and serial (SWD/serial to nRF52840).
- **USB-C** — power/charge only (no data).
- **Buttons** — CTRL, USER, RST (see [notes/OFFICIAL_HELTEC_DOCS.md](../notes/OFFICIAL_HELTEC_DOCS.md)).

---

## Hardware summary (from docs)

| Block | Part | Notes |
|-------|------|--------|
| MCU | nRF52840 | BLE 5.0 |
| LoRa | SX1262 | 863–870 or 902–928 MHz |
| Display | 2.13" e-ink | GxEPD2_213_B74, 250×122 |

Detailed pinout/schematic: see **datasheet** in [notes/datasheet/](../notes/datasheet/) or official Heltec resource page.
