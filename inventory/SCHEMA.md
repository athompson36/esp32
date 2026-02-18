# Inventory Schema

Canonical field reference for catalog entries. All category YAML files under `items/` use this shape.

---

## Categories

| Category      | Description |
|---------------|-------------|
| `sbc`         | Single-board computers (Raspberry Pi, Pine64, etc.) |
| `controller`  | MCU boards and dev kits (ESP32, Arduino, Teensy, T-Beam) |
| `sensor`      | Sensors and sensor modules (temp, humidity, IMU, air quality) |
| `accessory`   | Antennas, cases, cables, expansion boards, displays |
| `component`   | Discrete parts and ICs (resistors, connectors, regulators, transceivers) |

---

## Fields (per item)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| **id** | string | Yes | Unique slug (e.g. `raspberry_pi_4_4gb`, `bme280_module`). Use lowercase, underscores. |
| **name** | string | Yes | Human-readable name. |
| **manufacturer** | string | No | Brand or manufacturer. |
| **part_number** | string | No | Manufacturer part number (MPN). |
| **model** | string | No | Model or variant name. |
| **quantity** | number | No | Count on hand; default 1. |
| **location** | string | No | Where stored or installed (e.g. "Lab drawer A", "Installed in T-Beam #2"). |
| **specs** | object | No | Key-value technical specs. Use consistent keys where possible (see below). |
| **datasheet_url** | string | No | URL to official or vendor datasheet. |
| **datasheet_file** | string | No | Path to local PDF under `inventory/` (e.g. `datasheets/part123.pdf`). |
| **notes** | string | No | Freeform notes, variants, gotchas. |
| **used_in** | list[string] | No | Project or device IDs from this repo (e.g. `t_beam_1w`, `digital_mixer`). |
| **tags** | list[string] | No | Searchable tags (e.g. `esp32`, `i2c`, `5v`). |

---

## Suggested `specs` keys by category

Use these when applicable; add others as needed.

### SBCs / Controllers

- `soc` / `mcu` — SoC or MCU part number  
- `ram_mb` / `ram_gb` — RAM  
- `storage` — e.g. "eMMC 8GB", "microSD"  
- `interfaces` — Short list: USB, Ethernet, GPIO count, display, etc.  
- `power_v` — Operating voltage (V)  
- `power_a` — Typical or max current (A)  
- `gpio_pins` — Number or "40-pin"  
- `wireless` — WiFi, BLE, LoRa, etc.

### Sensors

- `interface` — I2C, SPI, UART, analog  
- `address_i2c` — I2C address if applicable (e.g. `0x76`)  
- `voltage_v` — Operating voltage range  
- `accuracy` — e.g. "±0.5°C"  
- `range` — Measurement range if relevant  
- `resolution` — e.g. "16-bit ADC"

### Accessories / Components

- `voltage_v` / `voltage_range_v`  
- `current_a` / `current_max_a`  
- `interface` — Connector or bus  
- `dimensions_mm` — e.g. "25.4×25.4"  
- `package` — e.g. "SOT-23", "through-hole"

### Mechanical / PCB & 3D design stack (optional)

For AI-driven enclosure and layout (see [docs/PCB_3D_DESIGN_STACK_SPEC.md](../docs/PCB_3D_DESIGN_STACK_SPEC.md)):

- `length_mm`, `width_mm`, `height_mm` — Part dimensions (mm) for placement and enclosure fit.
- `footprint` — PCB footprint name (e.g. `SOT-23-5`, `ESP32-WROOM-32`).
- `mounting` — `pcb`, `standoff`, `panel`, `none`.
- `model_3d_url` — Optional URL or path to STEP/STL for 3D preview.
- `model_3d_embed` — Optional primitive: `box`, `cylinder`, or shared shape ID.

---

## File layout

```
inventory/
├── README.md
├── SCHEMA.md          # This file
├── items/
│   ├── sbcs.yaml
│   ├── controllers.yaml
│   ├── sensors.yaml
│   ├── accessories.yaml
│   └── components.yaml
├── datasheets/        # Local PDFs (optional)
│   └── .gitkeep
├── inventory.db       # Generated SQLite DB (optional, from build_db script)
└── scripts/
    └── build_db.py   # YAML → SQLite
```

IDs must be unique across **all** category files if you merge into a single database.
