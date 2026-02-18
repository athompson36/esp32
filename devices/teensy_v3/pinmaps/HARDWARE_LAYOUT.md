# Teensy v3.2 — Hardware Layout

**Board:** PJRC Teensy 3.2  
**MCU:** NXP MK20DX256VLH7 (Cortex-M4, 72 MHz)

---

## Pinout

- **Layout:** 2×14 (28 pins) plus additional pins; first 28 pins match Teensy 3.x / 4.x grid for compatibility.
- **Digital:** 34 total; 12 PWM-capable.
- **Analog:** 21 inputs (12-bit); 1 DAC (A14).
- **Serial:** Multiple UARTs; I2C and SPI on alternate pins (see PJRC pinout card).
- **5 V tolerant:** Many pins; verify [PJRC pinout](https://www.pjrc.com/teensy/pinout.html) and schematic for each pin.

---

## Power

- 3.3 V regulator on board; USB 5 V or VIN. 3.3 V and GND on header.

---

## References

- [PJRC Teensy 3.2](https://www.pjrc.com/store/teensy32.html)
- [Teensy pinout](https://www.pjrc.com/teensy/pinout.html)
