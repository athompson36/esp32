# Teensy v4.1 — SDKs & Tools

**Device:** PJRC Teensy 4.0 or 4.1 (i.MX RT1062, Cortex-M7)  
**Container:** platformio-lab  
**Current projects:** Maschine MK2 mod (1), MIDI controller (4).

---

## Build (in container)

| Tool / SDK | Purpose |
|------------|--------|
| **PlatformIO** | `board = teensy40` or `teensy41`. |
| **Zephyr** | Optional RTOS target via PIO. |

---

## Flash (host)

| Tool | Purpose |
|------|---------|
| **Teensy loader** | [paulstoffregen/teensy_loader](https://github.com/paulstoffregen/teensy_loader). |

---

## Docker dependencies (platformio-lab)

- PlatformIO (teensy platform).

See [docker/TOOLS_AND_SDK.md](../../../docker/TOOLS_AND_SDK.md).
