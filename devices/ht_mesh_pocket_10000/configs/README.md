# Heltec Mesh Pocket (10000 mAh) — Configs

This folder holds **configuration examples** for the Mesh Pocket running Meshtastic:

- **Channel / region** — LoRa band (863–870 MHz or 902–928 MHz), spread factor, etc.
- **Device / node** — Export/import from Meshtastic app or serial.
- **Display** — InkHUD vs standard e-ink (firmware variant choice).

---

## Structure

```
configs/
├── meshtastic/
│   └── (future: exported configs or presets)
└── README.md
```

Meshtastic configuration is typically managed at runtime via the Meshtastic app (BLE) or serial; use this folder for versioned presets or exports if needed.
