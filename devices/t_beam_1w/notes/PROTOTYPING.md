# T-Beam 1W — Prototyping Guide

**Device:** LilyGO T-Beam 1W  
**Purpose:** Free GPIOs, expansion options, and safe prototyping practices.

---

## 1. GPIO Usage Summary

### 1.1 Used by onboard peripherals (do not reassign)

| GPIO | Assigned to |
|------|-------------|
| 0 | USER_BTN / BOOT (strapping) |
| 1 | LoRa DIO1 |
| 3 | LoRa RESET (strapping) |
| 4 | Battery ADC (Meshtastic) |
| 5 | GPS RX |
| 6 | GPS TX |
| 7 | GPS PPS |
| 8 | I2C SDA |
| 9 | I2C SCL |
| 10 | SD CS |
| 11 | SPI MOSI |
| 12 | SPI MISO |
| 13 | SPI SCK |
| 14 | NTC / temp (Meshtastic) |
| 15 | LoRa NSS |
| 16 | GPS EN |
| 17 | USER_BTN2 |
| 18 | TX LED |
| 21 | LoRa CTRL (RXEN) |
| 38 | LoRa BUSY |
| 40 | LoRa LDO_EN (critical) |
| 41 | FAN_CTRL |

### 1.2 Reserved / strapping / special (avoid for prototyping)

| GPIO | Reason |
|------|--------|
| 0 | Boot mode strapping; button. |
| 3 | Strapping; LoRa RESET. |
| 45, 46 | USB D−/D+ when USB is used. |

### 1.3 Free for prototyping (use with care)

Candidates that are **not** listed in the “used” table above and are generally available on ESP32-S3:

| GPIO | Notes |
|------|--------|
| **2** | Check if broken out on board; no onboard peripheral in this BOM. |
| **19, 20** | Often used for USB Serial/JTAG; confirm board schematic. |
| **35, 36, 37** | RTC/ADC2 on some ESP32-S3 layouts; verify voltage and availability. |
| **39** | Confirm not used for flash/PSRAM on this module. |
| **42, 43, 44** | Confirm not tied to flash/PSRAM. |
| **47, 48** | If present on module; verify schematic. |

**Important:** The T-Beam 1W does **not** expose a standard 0.1" expansion header. Free pins may require soldering to test points or unpopulated pads. Always check the **actual board schematic** or LilyGO pinout for your revision before wiring.

---

## 2. Expansion Options

### 2.1 Without hardware mods

- **I2C (8, 9):** Add more I2C devices (different addresses). Avoid conflicts with 0x3C and 0x34.
- **UART:** GPS uses 5/6; second UART could use other free TX/RX pairs if available in software.
- **SPI:** Shared with LoRa and SD; adding another SPI device would need another CS on a free GPIO (e.g. 2) and careful sharing/arbitration.

### 2.2 With soldering (test points / pads)

- Use only **free** GPIOs above; do not repurpose radio, I2C, or power-control pins.
- Prefer 3.3 V logic; do not exceed 3.3 V on any GPIO.
- If driving external loads, use buffer or transistor; do not exceed ESP32-S3 current limits per pin (e.g. 40 mA typical, 80 mA max with care).

### 2.3 External boards (UART, I2C, SPI)

- **I2C:** Add devices on 8/9 with unique addresses.
- **UART:** Use a free TX/RX pair (e.g. from “free” list) for a second UART if your firmware supports it.
- **SPI:** The main SPI is shared; second SPI (if supported in software) would need MOSI/MISO/SCK/CS on free pins — check ESP32-S3 alternate SPI pins and board layout.

---

## 3. Do’s and Don’ts

### Do

- **Keep GPIO 40 HIGH** before and during radio use; it powers the SX1262 and PA.
- **Cap TX power at 22 dBm** in firmware; never drive the 1W PA beyond that.
- **Use 800 µs PA ramp time** in radio init.
- **Use a single I2C bus** (8, 9) for OLED and PMU; do not assume Wire1.
- **Use 2S battery range** (6.0–8.4 V) in firmware and in any battery UI.
- **Confirm free GPIOs** on your exact board revision (schematic / LilyGO docs) before wiring.
- **Add only 3.3 V logic** to GPIOs; level-shift if connecting to 5 V systems.

### Don’t

- **Do not** drive GPIO 40 LOW during normal operation (radio/PA lose power).
- **Do not** assign GPIO 0, 3, 40, 21 to unrelated peripherals; they are critical for boot, radio reset, radio power, and RF switch.
- **Do not** exceed 22 dBm TX power or shorten PA ramp below 800 µs.
- **Do not** use a second I2C bus (Wire1) for OLED/PMU; this board has one bus.
- **Do not** assume AXP2101 is present; handle missing PMU in firmware (fallback voltage, no NULL deref).
- **Do not** transmit without an antenna connected (RF damage risk).

---

## 4. Safety Checklist

- [ ] Antenna connected before any TX.
- [ ] TX power limited to 22 dBm in build flags and runtime.
- [ ] PA ramp time set to 800 µs in radio init.
- [ ] GPIO 40 set HIGH before `lora.begin()` (or equivalent).
- [ ] No 5 V or higher signals on GPIOs; 3.3 V only unless level-shifted.
- [ ] Battery polarity correct on JST (2S 7.4 V).
- [ ] Free GPIOs verified against your board revision.

---

## 5. References

- [HARDWARE_LAYOUT.md](../pinmaps/HARDWARE_LAYOUT.md) — pinout and power
- [PERIPHERALS.md](../pinmaps/PERIPHERALS.md) — peripheral list and constraints
- [shared/t_beam_1w/RF_PA_FAN_PMU.md](../../../shared/t_beam_1w/RF_PA_FAN_PMU.md) — canonical RF/PA/fan/PMU rules
- MeshCore repo: `firmware/meshcore/repo/T-BEAM-1W-FIXES.md` — known hardware/firmware fixes
