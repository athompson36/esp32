# Meshtastic T-Beam 1W — Runtime Test Checklist (M11)

Use this checklist when testing Meshtastic firmware on real T-Beam 1W hardware. Covers FEATURE_ROADMAP M11.

**Prerequisites:** Flashed `firmware.factory.bin` (or `firmware.bin` at 0x10000) via `./scripts/flash.sh`. Serial port available (e.g. `cu.usbmodem*`).

**How to run (from repo root):**
1. Build: `./scripts/lab-build.sh t_beam_1w meshtastic t-beam-1w` (or use latest in `artifacts/t_beam_1w/meshtastic/`).
2. Flash: `./scripts/flash.sh` (pass artifact path or use default).
3. Optional: use a serial monitor (e.g. `screen /dev/cu.usbmodem* 115200` or inventory app Debug tab) to watch boot/log.
4. Work through sections 1–5 below; when all critical items pass, mark M11 Done in [FEATURE_ROADMAP.md](../../../FEATURE_ROADMAP.md).

---

## 1. Boot and serial

- [x] Board powers on (USB or battery). *(2026-02-23: port present, serial output received.)*
- [x] Serial monitor shows boot log (no crash loop). *(Captured; see artifacts/device_logs/.)*
- [x] No repeated resets or watchdogs in log.

---

## 2. SX1262 (LoRa) init

- [x] Radio initializes (look for SX126x or LoRa init messages in serial). *(RadioLibWrapper noise_floor in log.)*
- [x] No "init failed" or SPI errors.
- [ ] If available: TX/RX test (e.g. second node or Meshtastic app).

---

## 3. GPS

- [x] GPS module powers (antenna connected if needed). *(detected=1, test command sent in log.)*
- [ ] Serial or display shows fix or "searching" (no hang).
- [ ] If outdoors/antenna: fix acquired and coordinates shown.

---

## 4. Display (OLED SH1106)

- [ ] OLED turns on and shows Meshtastic UI (or splash). *(Manual: check visually.)*
- [ ] No permanent white/black screen or corruption.
- [ ] Buttons (if used) respond.

---

## 5. Meshtastic app discoverable

- [ ] Device appears in Meshtastic mobile/desktop app (BLE or serial). *(Manual: open app and connect.)*
- [ ] Node info shows correct hardware model (T-Beam 1W / TBEAM_1_WATT).
- [ ] Messaging or mesh test with another node (optional).

---

## 6. Power and thermal (optional)

- [ ] Fan (if present) runs after TX or stays off when disabled in config.
- [ ] No excessive heating; TX power cap (22 dBm) respected.

---

**Sign-off:** When all critical items pass, M11 can be marked Done in FEATURE_ROADMAP.md. See also DEVELOPMENT_PLAN Phase 7 in `firmware/meshtastic/repo/docs/`.
