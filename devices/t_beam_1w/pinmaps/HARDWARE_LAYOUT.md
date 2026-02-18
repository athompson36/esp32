# T-Beam 1W — Complete Hardware Layout

**Device:** LilyGO T-Beam 1W (ESP32-S3 + SX1262 + 1W PA)  
**Purpose:** Pinout, power tree, and block diagram for bring-up and integration.

---

## 1. Pinout Table

### 1.1 By function (GPIO → role)

| GPIO | Role | Direction | Notes |
|------|------|------------|--------|
| 0 | USER_BTN / BOOT | Input | Button 1; strapping (boot mode). Internal pull-up. |
| 1 | LoRa DIO1 | Input | SX1262 interrupt. |
| 3 | LoRa RESET | Output | SX1262 reset; strapping. **Set HIGH before radio init.** |
| 4 | Battery ADC | Input | ADC1_GPIO4; battery voltage sense (Meshtastic). |
| 5 | GPS RX | Input | UART RX ← GNSS TX (L76K). |
| 6 | GPS TX | Output | UART TX → GNSS RX. |
| 7 | GPS PPS | Input | 1PPS from GNSS (optional). |
| 8 | I2C SDA | Bidir | Wire (single bus). OLED + PMU. |
| 9 | I2C SCL | Bidir | Wire. |
| 10 | SD CS | Output | SD card chip select (shared SPI). |
| 11 | SPI MOSI | Output | Shared: LoRa + SD. |
| 12 | SPI MISO | Input | Shared: LoRa + SD. |
| 13 | SPI SCK | Output | Shared: LoRa + SD. |
| 14 | NTC / Temp | Input | NTC thermistor (Meshtastic). |
| 15 | LoRa NSS | Output | SX1262 chip select. |
| 16 | GPS EN | Output | GNSS enable/wake. |
| 17 | USER_BTN2 | Input | Button 2. |
| 18 | TX LED | Output | LED_STATE_ON = 1 (HIGH = ON). |
| 21 | LoRa CTRL (RXEN) | Output | LNA enable; HIGH during RX. RF switch control. |
| 38 | LoRa BUSY | Input | SX1262 busy. |
| 40 | LoRa LDO_EN | Output | **CRITICAL:** Powers SX1262 + PA. Must be HIGH before `lora.begin()`. |
| 41 | FAN_CTRL | Output | Cooling fan; recommend 5 s post-TX then OFF. |

### 1.2 Reserved / not broken out

- **45, 46:** USB D−/D+ (ESP32-S3 native USB). Do not use for GPIO when USB active.
- **DIO2, DIO3:** Internal to SX1262 (RF switch, TCXO). No separate GPIO.

---

## 2. Block Diagram (Logical)

```
                    ┌─────────────────────────────────────────────────────────┐
                    │                  ESP32-S3                                │
                    │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐   │
  USB-C ────────────┤  │  USB    │  │  GPIO   │  │  ADC1   │  │  I2C    │   │
  (power + serial)  │  │ 45,46   │  │ 0,17,18 │  │ 4,14    │  │ 8,9     │   │
                    │  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘   │
                    │       │            │            │            │        │
                    └───────┼────────────┼────────────┼────────────┼────────┘
                            │            │            │            │
         ┌──────────────────┘            │            │            └──────────────────┐
         │                               │            │                               │
         ▼                               ▼            ▼                               ▼
   USB serial                    Buttons/LED      Battery/NTC              ┌─────────┴─────────┐
   (flashing,                    (0, 17, 18)       (4, 14)                   │   I2C bus (8,9)   │
    console)                                                                 │  OLED 0x3C        │
                                                                            │  PMU 0x34 (opt)   │
                                                                            └──────────────────┘
         │
         │  SPI (11,12,13) + CS(15) + control
         ▼
   ┌─────────────────────────────────────────────────────────────────────────┐
   │  SX1262 + 1W PA  │  RESET=3  DIO1=1  BUSY=38  LDO_EN=40  CTRL=21        │
   │  NSS=15  MOSI=11 MISO=12 SCK=13  │  TX power ≤22 dBm  PA ramp ≥800 µs   │
   └─────────────────────────────────────────────────────────────────────────┘
         │
         │  UART (5=RX, 6=TX)  EN=16  PPS=7
         ▼
   ┌─────────────────────────────────────────────────────────────────────────┐
   │  GNSS (L76K)  9600 baud  │  PPS optional                                 │
   └─────────────────────────────────────────────────────────────────────────┘

   Fan: GPIO 41 (active after TX, 5 s then off recommended).
   SD:  SPI shared, CS=10 (optional use).
```

---

## 3. Power Tree

```
  USB-C 5 V ──┬──► VBUS ──► AXP2101 (if present) ──► 3.3 V rail ──► ESP32-S3, OLED, SX1262, L76K, etc.
              │              │
              │              └──► Battery charge + 7.4 V (2S) path
              │
  2S LiPo (7.4 V) ─────────────► AXP2101 (or direct 3.3 V LDO on cost-reduced boards)
                                      │
                                      └──► GPIO 40 (LDO_EN) gates power to SX1262 + 1W PA
```

- **Radio/PA power:** GPIO 40 enables LDO that powers SX1262 and 1W PA. Must be HIGH before any radio API init.
- **Fan:** GPIO 41; 5 V or 3.3 V depending on board; turn on after TX, off after ~5 s to save power.

---

## 4. Critical Initialization Order

1. **GPIO 40 (LDO_EN)** → HIGH (radio + PA power).
2. Short delay (e.g. 10–50 ms).
3. **I2C** (Wire) begin on 8/9 if using OLED/PMU.
4. **SX1262** init (SPI, RESET, DIO1, BUSY, CTRL); set PA ramp 800 µs, cap TX 22 dBm.
5. **GNSS** UART and EN (16) if used.
6. **Display** (SH1106 on I2C) if used.

---

## 5. Physical / Connectors

- **USB-C:** Power and USB serial (flashing: hold BOOT, plug USB, release after 5–8 s).
- **JST:** 2S LiPo (7.4 V); observe polarity.
- **Antenna:** LoRa and GNSS antennas; do not TX without antenna.
- **No standard 0.1" expansion header**; prototyping uses free GPIOs (see notes/PROTOTYPING.md).

---

## 6. Reference Documents

- Pin assignments (MeshCore): `firmware/meshcore/repo/variants/lilygo_tbeam_1w_SX1262/platformio.ini`
- Pin map (Meshtastic): `firmware/meshtastic/repo/docs/TBEAM_1W_PINMAP.md`
- Hardware fixes: `firmware/meshcore/repo/T-BEAM-1W-FIXES.md`, `MESHTASTIC-IMPROVEMENTS.md`
