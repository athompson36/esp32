# Device Context — Teensy v3.2

**Device ID:** `teensy_v3`  
**Board:** PJRC Teensy 3.2 (MK20DX256, ARM Cortex-M4)  
**Lab contract:** `firmware/` · `configs/` · `pinmaps/` · `notes/`

---

## Summary

Teensy 3.2 uses NXP MK20DX256VLH7 (ARM Cortex-M4, 72 MHz), 256 KB flash, 64 KB RAM. 34 digital I/O, 21 analog inputs, 12 PWM; 5 V tolerant I/O. Build with PlatformIO (teensy) or Teensyduino in container.

---

## Hardware at a Glance

| Item | Detail |
|------|--------|
| **MCU** | MK20DX256VLH7 (Cortex-M4, 72 MHz), 256 KB flash, 64 KB SRAM |
| **Digital** | 34 pins; 5 V tolerant (check per-pin); 12 PWM |
| **Analog** | 21 analog inputs (12-bit ADC); 1 DAC output |
| **Voltage** | 3.3 V native; many pins 5 V tolerant (see schematic) |

---

## Context Files

| File | Description |
|------|-------------|
| [pinmaps/HARDWARE_LAYOUT.md](pinmaps/HARDWARE_LAYOUT.md) | Pinout, 2×14 grid |
| [pinmaps/PERIPHERALS.md](pinmaps/PERIPHERALS.md) | UART, I2C, SPI, PWM, ADC |
| [notes/PROTOTYPING.md](notes/PROTOTYPING.md) | 5 V tolerant pins, current |
| [firmware/README.md](firmware/README.md) | Teensyduino, PlatformIO, firmware repos |
