# Heltec Mesh Pocket (10000 mAh) — Meshtastic Firmware

This device runs **Meshtastic** on **nRF52840 + SX1262** with a **2.13" e-ink** display. Flashing is **UF2** via the **magnetic pogo interface** (see [notes/FLASHING_UF2.md](../../notes/FLASHING_UF2.md)).

---

## Firmware builds (Meshtastic upstream)

Official Meshtastic firmware provides UF2 for Heltec Mesh Pocket:

| Variant | Env name | UF2 filename pattern |
|---------|-----------|------------------------|
| 10000 mAh | `heltec-mesh-pocket-10000` | `firmware-heltec-mesh-pocket-10000-X.X.X.xxxx.uf2` |
| 10000 mAh InkHUD | `heltec-mesh-pocket-10000-inkhud` | `firmware-heltec-mesh-pocket-inkhud-10000-X.X.X.xxxx.uf2` |
| 5000 mAh | `heltec-mesh-pocket-5000` | `firmware-heltec-mesh-pocket-5000-X.X.X.xxxx.uf2` |
| 5000 mAh InkHUD | `heltec-mesh-pocket-5000-inkhud` | `firmware-heltec-mesh-pocket-inkhud-5000-X.X.X.xxxx.uf2` |

- **Releases:** https://github.com/meshtastic/firmware/releases  
- **Web Flasher:** https://flasher.meshtastic.org/ (select Heltec Mesh Pocket 10000 / 5000)

---

## Building from source (optional)

Meshtastic firmware repo: https://github.com/meshtastic/firmware  

The **heltec_mesh_pocket** variant lives under:

- `firmware/variants/nrf52840/heltec_mesh_pocket/`

PlatformIO envs (this device = 10000 mAh):

- `heltec-mesh-pocket-10000` — standard e-ink
- `heltec-mesh-pocket-10000-inkhud` — InkHUD UI

Build produces UF2; copy to the device’s HT-n5262 drive in DFU mode (double-press RST).

---

## Lab layout

Per CONTEXT.md, firmware for this device lives under:

```
firmware/
├── meshtastic/
│   ├── README.md     # This file
│   └── repo/         # Optional: clone of meshtastic/firmware for local builds
└── (other firmware types if added)
```

**repo/:** Clone or submodule [meshtastic/firmware](https://github.com/meshtastic/firmware) here if you want to build locally; otherwise use official releases or Web Flasher.
