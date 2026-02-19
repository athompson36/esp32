# CONTEXT.md

## Cyber-Lab — Unified ESP32 Development Environment

**Host System:** Apple Mac Studio (Apple Silicon)\
**Operating Model:** Local-first, containerized, deterministic builds\
**Repository Type:** Embedded Mono-Lab\
**Primary Assistant:** Cursor

------------------------------------------------------------------------

# 🧠 Mission

This repository is a professional embedded firmware laboratory designed
to support multiple hardware platforms, firmware ecosystems, RF
experimentation, and reproducible builds.

The environment prioritizes:

-   deterministic toolchains\
-   hardware safety\
-   firmware isolation\
-   reproducibility\
-   local control\
-   scalability

This is not a hobby repository. Treat it like production infrastructure.

------------------------------------------------------------------------

# 🧭 Core Philosophy

## Build Anywhere → Reproduce Everywhere

Every firmware must:

✅ build inside a container\
✅ use pinned toolchains\
✅ avoid host dependencies\
✅ produce versioned artifacts

The macOS host exists primarily for:

-   USB flashing\
-   serial monitoring\
-   SDR tools\
-   logic analyzers\
-   RF debugging

Host builds are discouraged unless absolutely required.

------------------------------------------------------------------------

# 🧱 Top-Level Architecture

    esp32/                 # repo: athompson36/esp32
    │
    ├── CONTEXT.md
    │
    ├── docker/
    ├── orchestrator/      # lab build <device> <firmware> (see scripts/lab-build.sh)
    ├── scripts/
    ├── toolchains/        # (planned) pinned toolchains
    ├── shared/
    ├── artifacts/
    ├── inventory/         # Hardware catalog: SBCs, controllers, sensors, components (specs + datasheets)
    ├── ota/               # (planned) staged deployments
    ├── datasets/          # (planned) map data and region definitions
    │
    ├── devices/
    ├── experimental/      # (planned) board bring-up, risky firmware
    └── legacy/            # (planned) historical firmware

------------------------------------------------------------------------

# 🔥 Non-Negotiable Design Rules

1.  Never mix firmware toolchains\
2.  Never modify upstream repos directly\
3.  Prefer overlays instead of forks\
4.  Containers are the source of truth\
5.  Artifacts are never deleted

Storage is cheap. Reproducibility is priceless.

## Agent rules (errors and dependencies)

- **If errors are ever encountered:** Diagnose, fix, and verify the issue before moving on. Do not proceed to the next task until the current failure is resolved and tested.
- **If errors are encountered when installing and configuring dependencies:** Try to resolve the issue before changing tactics. Do not stray from the plan without specific verification to do so in every case.

------------------------------------------------------------------------

# 🛰️ Devices Directory

All boards live under:

    /devices

Example:

    devices/
        heltec_t114v3/
        heltec_t114v4/
        ht_mesh_pocket_10000/
        pine_time/
        t_deck_plus/

------------------------------------------------------------------------

# 📦 Device Folder Contract (STRICT)

Every device MUST follow:

    device_name/
        firmware/
        configs/
        pinmaps/
        notes/

------------------------------------------------------------------------

## Firmware Layout

    firmware/
        meshtastic/
            repo/
            overlays/
            
        meshcore/
            repo/
            overlays/
            
        expresslrs/
            repo/
            
        custom/

------------------------------------------------------------------------

## Firmware Rules

✅ Clone upstream firmware into /repo\
✅ Never refactor upstream structure\
✅ Never share `.pio`, `build`, or `.idf` directories\
✅ Apply customizations via overlays

------------------------------------------------------------------------

# 🧬 Overlay Patch System

Overlays allow customization without corrupting upstream repositories.

Example:

    firmware/meshtastic/
        overlays/
            board_variant/
            pa_limits/
            power_profiles/

Build scripts should apply overlays automatically.

Cursor should always prefer overlays over editing upstream code.

------------------------------------------------------------------------

# 🛰️ Special Platform: T-Deck Plus

    t_deck_plus/
        firmware/
        launcher/
        maps/
            osm_tiles/

------------------------------------------------------------------------

## Maps Dataset Policy

Maps are immutable datasets.

Cursor MUST NEVER:

-   delete\
-   compress\
-   reorganize\
-   deduplicate\
-   convert formats

without explicit approval.

These datasets may exceed 100GB.

------------------------------------------------------------------------

## Launcher

The launcher is a first-class firmware project.

Possible stacks include:

-   LVGL\
-   ESP-IDF\
-   Rust\
-   MicroPython

Cursor may assist development but must not restructure without
instruction.

------------------------------------------------------------------------

# 🐳 Container Architecture

This lab uses toolchain-specific containers.

## Golden Rule:

Never mix toolchains inside one container.

------------------------------------------------------------------------

## Container Matrix

### platformio-lab

Used for:

-   Meshtastic\
-   MeshCore\
-   Arduino-based firmware

### esp-idf-lab

Used for:

-   ESP-IDF projects\
-   LVGL builds\
-   custom firmware

### rust-embedded-lab

Used for:

-   PineTime\
-   Embassy\
-   NRF targets

### rf-lab (future)

Planned for:

-   SDR\
-   spectrum analysis\
-   LoRa sniffing

------------------------------------------------------------------------

# Example PlatformIO Container

``` dockerfile
FROM ubuntu:22.04

RUN apt-get update && apt-get install -y     git curl python3 python3-pip     build-essential cmake ninja-build     libusb-1.0-0 udev

RUN pip3 install platformio

WORKDIR /workspace
```

------------------------------------------------------------------------

# Container Strategy

Build inside containers.\
Flash from macOS host.

macOS USB is significantly more reliable than Docker passthrough.

------------------------------------------------------------------------

# 🔧 Toolchain Detection Rules

Cursor must detect the build system before recommending commands.

  Signal             Toolchain
  ------------------ ------------
  platformio.ini     PlatformIO
  idf.py             ESP-IDF
  Cargo.toml         Rust
  arduino-cli.yaml   Arduino

Never guess.

------------------------------------------------------------------------

# 🧠 Build Orchestrator (Future-Proofing)

Location:

    /orchestrator

Target behavior:

    lab build heltec_t114v4 meshtastic

The orchestrator should:

-   select the correct container\
-   mount volumes\
-   execute builds\
-   export artifacts

Cursor should design suggestions compatible with this future model.

------------------------------------------------------------------------

# 📦 Artifact System

All compiled firmware goes into:

    /artifacts

Structure:

    artifacts/device/firmware/version/

Example:

    artifacts/tbeam_1w/meshtastic/2.5.3/

Artifacts are never auto-deleted.

------------------------------------------------------------------------

# 📡 OTA Staging (Planned)

    /ota

Will support:

-   private firmware channels\
-   staged deployments\
-   beta testing

Design assumption: you will eventually operate node fleets.

------------------------------------------------------------------------

# 📚 Shared Knowledge Base

    /shared

Stores critical hardware intelligence:

-   RF tuning notes\
-   PA safety limits\
-   thermal constraints\
-   flashing offsets\
-   antenna performance\
-   board quirks

Cursor should search here FIRST during hardware debugging.

------------------------------------------------------------------------

# ⚡ Flashing Policy

Preferred workflow:

Container → Build\
Host → Flash

Never recommend Docker USB passthrough unless unavoidable.

------------------------------------------------------------------------

# 🧪 Experimental Zone

    /experimental

Use for:

-   board bring-up\
-   reverse engineering\
-   variant testing\
-   risky firmware

Cursor may be more flexible in this directory.

------------------------------------------------------------------------

# 🕰️ Legacy Folder

    /legacy

Never delete old firmware.

Historical context prevents repeated mistakes.

------------------------------------------------------------------------

# ⚠️ Cursor Behavioral Contract

## ALWAYS

-   preserve upstream repositories\
-   recommend container builds\
-   respect firmware boundaries\
-   assume future scale\
-   optimize for reproducibility

## NEVER

-   flatten directory structures\
-   merge firmware repos\
-   auto-upgrade toolchains\
-   delete artifacts\
-   rewrite upstream build systems

------------------------------------------------------------------------

# Operating Identity

This repository is a high-end embedded firmware lab.

Engineering priorities:

1.  Determinism\
2.  Hardware safety\
3.  Reproducibility\
4.  Isolation\
5.  Scalability
