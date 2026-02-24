# Lumari Watch — Pinmaps

**Canonical source:** Firmware repo [docs/HARDWARE_REFERENCES.md](https://github.com/athompson36/lumari_watch/blob/main/docs/HARDWARE_REFERENCES.md) and **Waveshare wiki** [ESP32-S3-Touch-AMOLED-2.06](https://www.waveshare.com/wiki/ESP32-S3-Touch-AMOLED-2.06) (schematic, pinout).

## Lumari pinout (Waveshare 2.06 — from `lumari_config.h`)

| Function | Pins / bus |
|----------|------------|
| **Display (CO5300 QSPI)** | CS=12, PCLK=11, DATA0–3=4,5,6,7, RST=8 |
| **Touch (FT3168 I2C)** | 0x38; RST=9, INT=38; I2C SDA=15, SCL=14 |
| **IMU (QMI8658)** | Same I2C bus |
| **RTC (PCF85063)** | 0x51, same I2C bus |
| **Buttons** | BOOT=0 (active low), PWR=10 (active high) |
