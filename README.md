# Cyber-Lab

Unified development environment for **ESP32**, **Arduino**, **Teensy**, **Raspberry Pi**, **Pine64**, and related hardware. **Local-first, containerized builds** — build inside containers, **flash and serial from host** (macOS). See [CONTEXT.md](CONTEXT.md) for philosophy and layout; [FEATURE_ROADMAP.md](FEATURE_ROADMAP.md) for priorities.

**Prerequisites:** Docker (for builds), Python 3 (for inventory app and scripts), [esptool](https://docs.espressif.com/projects/esptool/) on PATH (for flashing). Optional: OpenAI API key for AI query and datasheet analysis in the inventory app. **CI:** GitHub Actions build MeshCore and Meshtastic for T-Beam 1W in container; artifacts only (no flash).

---

## What this repo is

- **Lab layout and contract** — devices, firmware overlays, pinmaps, configs, notes.
- **Device context** — per-board hardware layout, peripherals, prototyping, SDKs/tools, firmware repos.
- **Docker** — single `platformio-lab` image for building all supported targets.
- **Docs** — CONTEXT (philosophy and rules), FEATURE_ROADMAP, FIRMWARE_INDEX, REPOS, current projects.

Not a single firmware: it’s the **lab** that holds (or points to) firmware, configs, and tooling.

---

## Full install (wizard)

To set up the full stack (Python venv, dependencies, inventory DB, optional MCP and Docker) after cloning:

```bash
python scripts/install_wizard.py
```

Then activate the venv, run `python inventory/app/app.py`, and open http://127.0.0.1:5050. See [docs/INSTALL.md](docs/INSTALL.md) for details and options (`--non-interactive`, `--skip-docker`, etc.).

---

## Quick start

### 1. Build in container

```bash
docker build -t platformio-lab -f docker/Dockerfile .
./scripts/lab-build.sh t_beam_1w meshcore T_Beam_1W_SX1262_repeater
```

This builds MeshCore for T-Beam 1W (repeater) and writes `artifacts/t_beam_1w/meshcore/<date>/firmware.bin`. Other envs: `T_Beam_1W_SX1262_room_server`, `T_Beam_1W_SX1262_companion_radio_ble`. See [docker/README.md](docker/README.md).

### 2. Flash from host

Prefer flashing on the host (USB is more reliable than Docker passthrough). Use the lab flash script (picks latest artifact or a given .bin):

```bash
./scripts/flash.sh
# or: ./scripts/flash.sh /dev/cu.usbmodem101 t_beam_1w meshtastic latest
# or: ./scripts/flash.sh /path/to/firmware.factory.bin
```

Or with esptool directly: `esptool --chip esp32s3 --port /dev/cu.usbmodem* write_flash 0x0 path/to/firmware.bin`

**Toolchain detection:** `./scripts/detect-toolchain.sh [path]` prints `platformio` | `idf` | `cargo` | `unknown` so the orchestrator or IDE can suggest the right build commands.

### 3. Device and firmware docs

- **Devices:** [devices/README.md](devices/README.md) — list and contract.
- **Firmware index:** [FIRMWARE_INDEX.md](FIRMWARE_INDEX.md) — all firmwares and repos per device.
- **SDKs & tools:** [docker/TOOLS_AND_SDK.md](docker/TOOLS_AND_SDK.md).
- **Current projects:** [current_project.md](current_project.md).
- **Changelog:** [CHANGELOG.md](CHANGELOG.md) — lab and artifact changes.

---

## Key docs

| Doc | Purpose |
|-----|--------|
| [CONTEXT.md](CONTEXT.md) | Philosophy, layout, device contract, containers, rules. |
| [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) | Repo layout, conventions, stacks, and dependencies (keep updated). |
| [FEATURE_ROADMAP.md](FEATURE_ROADMAP.md) | Lab and device roadmap, priorities. |
| [REPOS.md](REPOS.md) | Repo index (Meshtastic, MeshCore, Launcher, etc.). |
| [current_project.md](current_project.md) | Cyber-Lab project list (ESP32 & SBC) and lab context. |
| [inventory/README.md](inventory/README.md) | Hardware catalog: SBCs, controllers, sensors, accessories, components (specs + datasheets). |

### Rebuild containers after code changes

When you change the **inventory app** or **MCP server** code, rebuild the images so containers use the latest code:

```bash
./scripts/rebuild-containers.sh
```

Then start the inventory app with `docker compose -f inventory/app/docker-compose.yml up` (or `up -d --build` for detached). Compose uses **`restart: unless-stopped`** so containers auto-restart on failure and start when the Docker daemon starts.

---

## Devices

Supported boards live under [devices/](devices/). Each has `DEVICE_CONTEXT.md`, pinmaps, peripherals, prototyping notes, SDK/tools, and firmware links. Examples:

- **t_beam_1w** — LilyGO T-Beam 1W (MeshCore, Meshtastic).
- **t_deck_plus** — T-Deck Plus (Launcher, maps, Meshtastic).
- **raspberry_pi_***, **pine64**, **arduino_uno**, **teensy_v3.2 / teensy_v4.1** — see [devices/README.md](devices/README.md).

---

## License

See [LICENSE](LICENSE). Lab docs and structure are MIT; embedded firmware repos (MeshCore, Meshtastic, etc.) keep their own licenses.
