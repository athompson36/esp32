# Cyberdeck Manager — Directory Scaffold

Suggested layout for implementing the Cyberdeck Manager spec. Aligns with existing `devices/`, `inventory/`, `artifacts/`, `docker/`.

```
cyber-lab/
├── docs/
│   ├── CYBERDECK_MANAGER_SPEC.md   # Spec + implementation map
│   └── cyberdeck_scaffold.md       # This file
├── registry/
│   ├── devices/                    # Device JSON (device_id.json)
│   │   ├── t_beam_1w.json
│   │   ├── t_deck_plus.json
│   │   ├── t_deck.json
│   │   ├── heltec_t114_v3.json
│   │   ├── heltec_t114_v4.json
│   │   ├── heltec_meshpocket_10000.json
│   │   ├── raspberry_pi_v5.json
│   │   └── rockpro64.json
│   ├── firmware/                   # Firmware metadata (from GitHub)
│   │   └── (firmware_id).json
│   ├── forks/
│   │   └── {device_id}/{fork_name}/
│   ├── rf_presets.json             # USA, EU, custom
│   └── can_firmware/               # CAN-compatible firmware metadata
├── regions/                        # Map tiles: states, cities, zooms
│   └── (region_slug)/
│       └── {z}/{x}/{y}.png
├── scripts/
│   ├── schema/
│   │   └── cyberdeck_schema.sql
│   ├── map_wizard.py               # CLI + callable for Web
│   ├── sd_validator.py             # FAT32, 32KB cluster, structure
│   ├── sd_launcher/                # SD Launcher manifest + folder builder
│   ├── firmware_metadata.py        # GitHub + platformio.ini ingestion
│   ├── hardware_inspector/         # Serial/BLE/USB detection
│   └── cli/                        # Typer CLI (device, firmware, map, flash)
├── cyberdeck_cli/                  # Optional: Typer app package
│   ├── __init__.py
│   ├── main.py
│   ├── device_cmd.py
│   ├── firmware_cmd.py
│   ├── map_cmd.py
│   └── flash_cmd.py
├── cyberdeck_web/                  # Optional: FastAPI app (or extend inventory/app)
│   ├── main.py
│   ├── routers/
│   └── models/
├── docker/
│   ├── Dockerfile                  # Existing platformio-lab
│   └── Dockerfile.cyberdeck        # Python + esptool + platformio + CAN + map tools
├── inventory/                      # Existing: BOM, project planning, flash UI
│   └── app/                        # Extend with Map tab, Device registry view, Flash wizard
├── devices/                        # Existing: DEVICE_CONTEXT, pinmaps, firmware
└── artifacts/                      # Existing: backups, project_proposals, build outputs
```

## Implementation order

1. **Schema + device seeds** — Run `cyberdeck_schema.sql`; add `registry/devices/*.json`.
2. **Device registry API** — CRUD for devices; sync from JSON or DB.
3. **Firmware metadata** — Script to fetch GitHub + platformio.ini; populate `firmware` table / JSON.
4. **Flash wizard** — Extend inventory Flash UI: device → firmware → detect → method → validate → flash / SD.
5. **Map wizard** — Region scanner, tile calculator, SD validator; CLI then Web.
6. **Hardware inspector** — Detection scripts; snapshot storage; Update Status panel.
7. **RF/CAN** — Presets and CAN registry; enforce in configs.
8. **Multi-user** — Auth, RBAC, ownership (if required).
9. **CLI** — Typer commands wrapping the above.
10. **Docker** — Single image for CLI + Web + tools.

## Pyproject / CLI

If adding a dedicated CLI:

```toml
# pyproject.toml (optional, repo root or cyberdeck_cli/)
[tool.poetry]  # or [project]
name = "cyberdeck-manager"
version = "0.1.0"
description = "Device, firmware, map, and flash lifecycle manager"
readme = "docs/CYBERDECK_MANAGER_SPEC.md"

[tool.poetry.dependencies]
python = "^3.10"
typer = {extras = ["all"], version = "^0.9.0"}
rich = "^13.0.0"
httpx = "^0.25.0"
pyserial = "^3.5"
# esptool, platformio as needed
```

## Docker (optional)

```dockerfile
# docker/Dockerfile.cyberdeck
FROM python:3.12-slim
RUN apt-get update && apt-get install -y git usbutils && rm -rf /var/lib/apt/lists/*
RUN pip install esptool typer "rich[all]" httpx pyserial
WORKDIR /workspace
# Mount repo; run cli or web
```

Use with: `docker run --rm -v "$(pwd):/workspace" cyberdeck-manager cyberdeck device list`
