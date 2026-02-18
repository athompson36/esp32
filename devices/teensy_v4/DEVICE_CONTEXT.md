# Device Context — Teensy v4.1

**Device ID:** `teensy_v4`  
**Board:** PJRC Teensy 4.0 or 4.1 (IMXRT1062, ARM Cortex-M7)  
**Lab contract:** `firmware/` · `configs/` · `pinmaps/` · `notes/`

---

## Summary

Teensy 4.0/4.1 use NXP i.MX RT1062 (Cortex-M7, 600–912 MHz), 1 MB RAM, 2 MB flash (4.1: more pins and optional flash). 40 (4.0) or 55 (4.1) digital I/O, 14–18 analog inputs; **3.3 V only, not 5 V tolerant**. Build with PlatformIO (teensy) or Teensyduino in container.

---

## Hardware at a Glance

| Item | Teensy 4.0 | Teensy 4.1 |
|------|------------|------------|
| **MCU** | i.MX RT1062 (Cortex-M7, 600 MHz) | i.MX RT1062 (600–912 MHz) |
| **RAM** | 1 MB | 1 MB |
| **Flash** | 2 MB | 2 MB (+ optional PSRAM/NOR) |
| **Digital** | 40 pins | 55 pins |
| **Analog** | 14 inputs | 18 inputs |
| **Voltage** | 3.3 V only; **not 5 V tolerant** | Same |

---

## Context Files

| File | Description |
|------|-------------|
| [pinmaps/HARDWARE_LAYOUT.md](pinmaps/HARDWARE_LAYOUT.md) | Pinout, 4.0 vs 4.1 |
| [pinmaps/PERIPHERALS.md](pinmaps/PERIPHERALS.md) | UART, I2C, SPI, PWM |
| [notes/PROTOTYPING.md](notes/PROTOTYPING.md) | 3.3 V only |
| [firmware/README.md](firmware/README.md) | Teensyduino, PlatformIO, firmware repos |
