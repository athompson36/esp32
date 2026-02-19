# Orchestrator

Single entry point for building firmware in the lab.

## Usage

```bash
# From repo root:
./scripts/lab-build.sh <device> <firmware> [env]

# Examples:
./scripts/lab-build.sh t_beam_1w meshcore T_Beam_1W_SX1262_repeater
./scripts/lab-build.sh t_beam_1w meshtastic t-beam-1w
```

The orchestrator:

1. Selects the correct container (`platformio-lab`)
2. Mounts the repo at `/workspace`
3. Runs `pio run -e <env>` inside the container
4. Copies artifacts to `artifacts/<device>/<firmware>/<date>/`

See also:

- `scripts/lab-build.sh` — the build script
- `scripts/flash.sh` — flash from host (USB)
- `scripts/detect-toolchain.sh` — detect build system (platformio | idf | cargo | unknown)
- `inventory/app/config.py` (`BUILD_CONFIG`) — device/firmware/env definitions used by the inventory app's Build tab
