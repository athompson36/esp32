# Device Context — LilyGO T-Beam 1W

**Device ID:** `t_beam_1w`  
**Board:** LilyGO T-Beam 1W (ESP32-S3 + SX1262 + 1W PA)  
**Lab contract:** `firmware/` · `configs/` · `pinmaps/` · `notes/`

---

## Summary

Single-board LoRa node with ESP32-S3, Semtech SX1262 sub-GHz LoRa, 1W external PA, GNSS (L76K), I2C OLED (SH1106), PMU (AXP2101 on some variants), and cooling fan. Used for MeshCore (Companion, Repeater, Room Server) and Meshtastic firmware. 7.4 V 2S LiPo via JST; USB-C for power and serial.

---

## Hardware at a Glance

| Item | Detail |
|------|--------|
| **MCU** | ESP32-S3 (dual-core Xtensa LX7, 240 MHz), 512 KB SRAM, 8 MB PSRAM option |
| **Radio** | SX1262 LoRa, 1W PA; 868/915 MHz (region-dependent) |
| **GNSS** | Quectel L76K or compatible (UART 9600) |
| **Display** | SH1106 OLED 128×64, I2C 0x3C |
| **PMU** | AXP2101 (I2C 0x34) — **optional**: cost-reduced boards omit it |
| **Power** | 7.4 V 2S LiPo (6.0–8.4 V range), USB-C 5 V |
| **I2C** | Single bus (GPIO 8 SDA, GPIO 9 SCL); OLED + PMU on same bus |

---

## Context Files in This Device

| File | Description |
|------|-------------|
| [pinmaps/HARDWARE_LAYOUT.md](pinmaps/HARDWARE_LAYOUT.md) | Full pinout, power tree, block diagram, critical sequences |
| [pinmaps/PERIPHERALS.md](pinmaps/PERIPHERALS.md) | All peripherals with GPIO/bus, drivers, and constraints |
| [notes/PROTOTYPING.md](notes/PROTOTYPING.md) | Free GPIOs, expansion, do/don’t, safety |
| [notes/SDK_AND_TOOLS.md](notes/SDK_AND_TOOLS.md) | SDKs, CLI tools, Docker deps, flash/serial |

---

## Firmware in This Lab

- **MeshCore:** Companion (BLE), Repeater, Room Server — see `firmware/meshcore/repo/`. **Flash verified working** with full factory image at 0x0 (see [notes/T_BEAM_NO_BOOT.md](notes/T_BEAM_NO_BOOT.md)).
- **Meshtastic:** Port in progress — see `firmware/meshtastic/repo/`.

---

## Flash (verified working)

MeshCore boots correctly when:

1. **Full image at 0x0** — Use **firmware.factory.bin** (bootloader + partitions + boot_app0 + app). The lab build produces it via host merge if the in-container merge fails; the **Backup / Flash** UI only lists full images (bootloader.bin and partitions.bin are excluded).
2. **Erase when recovering** — If the board won’t boot, erase then re-flash: `ERASE=1 ./scripts/flash.sh t_beam_1w meshcore latest`, or in the UI erase (or use script) then flash **firmware.factory.bin**.
3. **Flash mode/size** — T-Beam 1W is 16MB QIO. The app and `scripts/flash.sh` pass `--flash_mode qio --flash_size 16MB` for this device so writes are correct.

See [notes/T_BEAM_NO_BOOT.md](notes/T_BEAM_NO_BOOT.md) for troubleshooting (invalid header, ets_loader.c 78, etc.).

---

## Critical Hardware Rules

See **[shared/t_beam_1w/RF_PA_FAN_PMU.md](../../shared/t_beam_1w/RF_PA_FAN_PMU.md)** for canonical RF/PA/fan/PMU rules. Summary:

1. **GPIO 40** must be driven HIGH before SX1262/radio init (powers radio + PA LDO).
2. **TX power** must be capped at 22 dBm for 1W PA safety; PA ramp time ≥ 800 µs.
3. **Single I2C bus** only (Wire on 8/9); do not use Wire1.
4. **2S battery:** Use 6.0–8.4 V range for SoC; apps may need 2S-aware battery UI.

---

## References

- LilyGO: [T-Beam 1W product](https://www.lilygo.cc/products/t-beam-1w)
- Lab: [CONTEXT.md](../../CONTEXT.md), [FEATURE_ROADMAP.md](../../FEATURE_ROADMAP.md)
- **No-boot / flash:** [notes/T_BEAM_NO_BOOT.md](notes/T_BEAM_NO_BOOT.md)
- Fixes/improvements: [T-BEAM-1W-FIXES.md](firmware/meshcore/repo/T-BEAM-1W-FIXES.md), [MESHTASTIC-IMPROVEMENTS.md](firmware/meshcore/repo/MESHTASTIC-IMPROVEMENTS.md)
