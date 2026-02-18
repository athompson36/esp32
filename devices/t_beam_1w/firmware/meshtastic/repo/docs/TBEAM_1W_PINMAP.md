# LilyGO T‑Beam 1W (ESP32‑S3) Pin Map

**Status**: ✅ Verified from existing Meshtastic firmware implementation  
**Source**: `firmware/variants/esp32s3/t-beam-1w/variant.h`

## Radio (SX1262 + 1W front end)
- SPI SCK: GPIO 13
- SPI MOSI: GPIO 11
- SPI MISO: GPIO 12
- SPI CS/NSS: GPIO 15
- RESET: GPIO 3
- BUSY: GPIO 38
- DIO1: GPIO 1
- DIO2: Used as RF switch (via SX126X_DIO2_AS_RF_SWITCH)
- DIO3: TCXO voltage control (1.8V)
- RXEN / LNA_EN: GPIO 21 (must be HIGH during RX)
- Power Enable: GPIO 40 (SX126X_POWER_EN - powers SX1262 + PA via LDO)
- **CRITICAL**: GPIO 40 must be HIGH before `lora.begin()`!

## I2C bus (OLED)
- SDA: GPIO 8
- SCL: GPIO 9
- OLED address: 0x3C
- Display driver: SH1106
- Resolution: 128x64

## GNSS (Quectel L76K)
- GNSS TX -> ESP RX: GPIO 5 (GPS_RX_PIN)
- GNSS RX -> ESP TX: GPIO 6 (GPS_TX_PIN)
- PPS pin: GPIO 7 (GPS_1PPS_PIN)
- Wakeup/Enable: GPIO 16 (GPS_WAKEUP_PIN / GPS_EN_PIN)
- Baud: 9600 (GPS_BAUDRATE)

## Buttons
- BOOT: (board built-in)
- RESET: (board built-in)
- BUTTON 1: GPIO 0 (BUTTON_PIN)
- BUTTON 2: GPIO 17 (ALT_BUTTON_PIN)

## LEDs
- LED: GPIO 18 (LED_STATE_ON = 1, HIGH = ON)

## Power Management
- Battery ADC: GPIO 4 (BATTERY_PIN)
- ADC Channel: ADC1_GPIO4_CHANNEL
- ADC Multiplier: 2.9333
- Battery sense samples: 30
- NTC Temperature Sensor: GPIO 14

## SD Card
- Uses shared SPI bus
- CS: GPIO 10 (SDCARD_CS)
- SPI1 used for SD card (SDCARD_USE_SPI1)

## Fan Control
- Fan Control Pin: GPIO 41 (FAN_CTRL_PIN / RF95_FAN_EN)

## Other Features
- 32768 Hz crystal: Present (HAS_32768HZ = 1)
- TX Power Offset: 10 (TX_GAIN_LORA)
- Max Power: 22 (SX126X_MAX_POWER)
- PA Ramp Time: 800us (SX126X_PA_RAMP_US = 0x05) - Required for 1W PA stabilization

## RF Switching Configuration
The 1W PA module uses DIO2 and CTRL pin for RF switching:
- DIO2=1, CTRL=0 → TX mode (PA on, LNA off)
- DIO2=0, CTRL=1 → RX mode (PA off, LNA on)
- CTRL pin (GPIO 21) is SX126X_RXEN (LNA enable)

## Notes
- **CRITICAL**: GPIO 40 (SX126X_POWER_EN) must be set HIGH before radio initialization
- PA ramp time is set to 800us (vs default 200us) for proper 1W PA stabilization
- Radio power is controlled via LDO on GPIO 40
- DIO2 is used as RF switch (not separate TXEN/RXEN pins)
- TCXO voltage is 1.8V (configured via DIO3)
