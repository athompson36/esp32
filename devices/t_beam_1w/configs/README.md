# T-Beam 1W — Configs

This folder holds **configuration examples** for the T-Beam 1W:

- **Build/config presets** — e.g. region (868/915 MHz), default passwords, advert names.
- **Channel or mesh configs** — export/import for MeshCore or Meshtastic.
- **Device-specific defaults** — battery limits, display, GPS baud, etc.

## Structure

```
configs/
├── meshcore/
│   ├── companion_example.env   # Companion (BLE) — ADVERT_NAME, ADMIN_PASSWORD
│   ├── repeater_example.env    # Repeater — ADVERT_NAME, ADMIN_PASSWORD
│   └── room_server_example.env # Room Server — ADVERT_NAME, ADMIN_PASSWORD, ROOM_PASSWORD
├── meshtastic/
│   └── (future: protobuf or config exports)
└── README.md                  # This file
```

## Current firmware locations

- **MeshCore:** `firmware/meshcore/repo` — env defaults are in `platformio.ini` per env (e.g. `ADMIN_PASSWORD`, `ROOM_PASSWORD`, `ADVERT_NAME`).
- **Meshtastic:** `firmware/meshtastic/repo` — config applied at runtime via app or serial.

Copy or adapt values from those locations into files here for versioned, shareable presets.
