# Meshtastic T-Beam 1W — Runtime Test Checklist (M11)

Use this checklist when testing Meshtastic firmware on real T-Beam 1W hardware. Covers FEATURE_ROADMAP M11.

**Prerequisites:** Flashed `firmware.factory.bin` (or `firmware.bin` at 0x10000) via `./scripts/flash.sh`. Serial port available (e.g. `cu.usbmodem*`).

---

## 1. Boot and serial

- [ ] Board powers on (USB or battery).
- [ ] Serial monitor shows boot log (no crash loop).
- [ ] No repeated resets or watchdogs in log.

---

## 2. SX1262 (LoRa) init

- [ ] Radio initializes (look for SX126x or LoRa init messages in serial).
- [ ] No "init failed" or SPI errors.
- [ ] If available: TX/RX test (e.g. second node or Meshtastic app).

---

## 3. GPS

- [ ] GPS module powers (antenna connected if needed).
- [ ] Serial or display shows fix or "searching" (no hang).
- [ ] If outdoors/antenna: fix acquired and coordinates shown.

---

## 4. Display (OLED SH1106)

- [ ] OLED turns on and shows Meshtastic UI (or splash).
- [ ] No permanent white/black screen or corruption.
- [ ] Buttons (if used) respond.

---

## 5. Meshtastic app discoverable

- [ ] Device appears in Meshtastic mobile/desktop app (BLE or serial).
- [ ] Node info shows correct hardware model (T-Beam 1W / TBEAM_1_WATT).
- [ ] Messaging or mesh test with another node (optional).

---

## 6. Power and thermal (optional)

- [ ] Fan (if present) runs after TX or stays off when disabled in config.
- [ ] No excessive heating; TX power cap (22 dBm) respected.

---

**Sign-off:** When all critical items pass, M11 can be marked Done in FEATURE_ROADMAP.md. See also DEVELOPMENT_PLAN Phase 7 in `firmware/meshtastic/repo/docs/`.
