# Teensy v3.2 — SDKs & Tools

**Device:** PJRC Teensy 3.2 (MK20DX256, Cortex-M4)  
**Container:** platformio-lab  
**Current projects:** Maschine MK2 mod (1), MIDI controller (4).

---

## Build (in container)

| Tool / SDK | Purpose |
|------------|--------|
| **PlatformIO** | `platform = teensy`, `board = teensy31` or `teensy32`. |
| **Teensyduino cores** | Supplied by PIO platform-teensy. |

---

## Flash (host)

| Tool | Purpose |
|------|---------|
| **Teensy loader** | GUI or CLI; [paulstoffregen/teensy_loader](https://github.com/paulstoffregen/teensy_loader). PIO can upload if USB passed to container; host usually more reliable. |

---

## Docker dependencies (platformio-lab)

- PlatformIO (teensy platform).

See [docker/TOOLS_AND_SDK.md](../../../docker/TOOLS_AND_SDK.md).
