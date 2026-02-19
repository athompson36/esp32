# T-Beam 1W — Firmware

Per the lab contract, all firmware for this device lives under this directory, with **overlays** for customisations (no direct edits to upstream repos).

---

## Available firmwares & repos

**Full index:** [FIRMWARE_INDEX.md](../../../FIRMWARE_INDEX.md#t_beam_1w-lilygo-t-beam-1w)

| Firmware / project | Repo | Notes |
|--------------------|------|--------|
| **MeshCore** (upstream) | [meshcore-dev/MeshCore](https://github.com/meshcore-dev/MeshCore) | Multi-hop LoRa; Companion, Repeater, Room Server. Also [ripplebiz/MeshCore](https://github.com/ripplebiz/MeshCore). |
| **MeshCore T-Beam 1W** | [mintylinux/Meshcore-T-beam-1W-Firmware](https://github.com/mintylinux/Meshcore-T-beam-1W-Firmware) | Community variant. |
| **Meshtastic** (upstream) | [meshtastic/firmware](https://github.com/meshtastic/firmware) | Official; T-Beam 1W target. |
| **Meshtastic** (LilyGO fork) | [Xinyuan-LilyGO/Meshtastic_firmware](https://github.com/Xinyuan-LilyGO/Meshtastic_firmware) | Device-specific builds. |
| **Prebuilt Meshtastic** | [ksjkl1/LilyGO-TTGO-T-Beam-Meshtastic](https://github.com/ksjkl1/LilyGO-TTGO-T-Beam-Meshtastic) | Binaries + install scripts. |
| **LilyGO examples** | [LilyGO/TTGO-T-Beam](https://github.com/LilyGO/TTGO-T-Beam) | Examples, factory (legacy). |

**MeshCore flash (verified):** Build with `./scripts/lab-build.sh t_beam_1w meshcore T_Beam_1W_SX1262_repeater`; flash **firmware.factory.bin** at 0x0 (script: `ERASE=1 ./scripts/flash.sh t_beam_1w meshcore latest`; or Backup/Flash UI — select firmware.factory.bin; T-Beam 1W uses qio 16MB). See [../notes/T_BEAM_NO_BOOT.md](../notes/T_BEAM_NO_BOOT.md) if the board won’t boot.

---

## Target layout (CONTEXT.md)

```
firmware/
├── meshcore/
│   ├── repo/          # Upstream MeshCore clone
│   └── overlays/      # Board variant, PA limits, power profiles
├── meshtastic/
│   ├── repo/          # Upstream Meshtastic firmware clone
│   └── overlays/      # T-Beam 1W variant, platformio env
├── expresslrs/       # (optional)
└── custom/            # Custom firmware
```

## Device layout: symlink vs copy

**Goal:** Map upstream firmware repos into this device folder so builds and overlays stay under the lab contract.

### Option A — Symlink (current, minimal change)

- Clone repos **outside** this directory (e.g. repo root) so they remain in `.gitignore`.
- **Symlink** from `devices/t_beam_1w/firmware/` into those clones so paths are consistent.

| Firmware   | Location (under this device)   |
|------------|--------------------------------|
| MeshCore   | `firmware/meshcore/repo/`      |
| Meshtastic | `firmware/meshtastic/repo/`    |

**Current state:** Upstream firmware is tracked as **git submodules**. Clone with:

```bash
git clone --recurse-submodules <this-repo>
# or, if already cloned:
git submodule update --init --recursive
```

- **MeshCore:** `firmware/meshcore/repo` → [meshcore-dev/MeshCore](https://github.com/meshcore-dev/MeshCore)
- **Meshtastic:** `firmware/meshtastic/repo/firmware` → [meshtastic/firmware](https://github.com/meshtastic/firmware)

Lab overlays (e.g. T-Deck trackball calibration) are in **patches**; apply after submodule update:

```bash
cd devices/t_beam_1w/firmware/meshtastic/repo && ./scripts/apply_lab_patches.sh
```

Build from `firmware/<name>/repo`; config uses these paths (see `inventory/app/config.BUILD_CONFIG`).

## Build

Use the lab orchestrator from repo root (builds in container, writes to `artifacts/<device>/<firmware>/<version>/`):

```bash
./scripts/lab-build.sh t_beam_1w meshcore T_Beam_1W_SX1262_repeater
./scripts/lab-build.sh t_beam_1w meshtastic t-beam-1w
```

- **MeshCore:** Envs `T_Beam_1W_SX1262_repeater`, `T_Beam_1W_SX1262_room_server`, `T_Beam_1W_SX1262_companion_radio_ble`.
- **Meshtastic:** Env `t-beam-1w`. Requires **mklittlefs** in the build image; the lab `platformio-lab` Docker image includes it (rebuild with `docker build -t platformio-lab -f docker/Dockerfile .` if needed).

**Flash from host:** From repo root, `./scripts/flash.sh` (uses latest Meshtastic or MeshCore artifact) or `./scripts/flash.sh [PORT] /path/to/firmware.factory.bin`.

See [FEATURE_ROADMAP.md](../../../FEATURE_ROADMAP.md) for orchestrator and artifact paths. See [REPOS.md](../../../REPOS.md) for the full lab repo index.
