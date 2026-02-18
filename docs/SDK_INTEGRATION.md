# Device SDK integration in Cyber-Lab

**Purpose:** Describe how full SDKs for catalog devices are installed and exposed so the AI and builds can use the full feature set.

---

## 1. Overview

- When **adding a device** via the Add device wizard, if the device has a **full SDK** in the catalog, it can be **downloaded and installed** automatically (option **Install device SDK**, **on by default**).
- SDKs are integrated so **firmware builds** (e.g. PlatformIO in `devices/<id>/firmware/`) use the correct platform and libraries.
- The **AI** can discover SDK metadata and per-device docs via the API and `docs_hint`, so it can reference SDK features when helping with code or config.

---

## 2. What’s implemented

### Catalog

- **Device catalog** (`inventory/app/device_catalog.json`): devices can have an optional **`sdk`** object:
  - `sdk.available`: true
  - `sdk.install_type`: `"platformio_platform"`
  - `sdk.platform_id`: e.g. `espressif32`, `teensy`, `atmelavr`, `raspberrypi`
  - `sdk.default_install`: true (checkbox default in UI)

Devices with SDK in catalog: LilyGo/Heltec ESP32 boards, Raspberry Pi Pico/Pico W, Arduino Uno/Nano/Mega/Leonardo, Teensy 3.x/4.x. Devices without `sdk` (no PlatformIO “full SDK” here): RPi SBCs (Zero, 4, 5), Pine64, PineTime.

### Backend

- **install_device_sdk(device_id, catalog_entry)** in `device_ops.py`: if `sdk.available` and `install_type == "platformio_platform"`, runs `pio pkg install -g -p <platform_id>`. Handles missing `pio` and timeouts; returns (success, message).
- **get_device_sdk_path(device_id)**: returns SDK metadata: `device_id`, `platform_id`, `install_type`, `path` (empty for global PIO), `docs_hint` (path to `devices/<id>/notes/SDK_AND_TOOLS.md` when that file exists).

### API

- **POST /api/devices/scaffold**: body may include **install_sdk** (default true). After a successful scaffold, if `install_sdk` is true and the catalog device has `sdk.available`, the backend calls `install_device_sdk`. Response can include `sdk_message` and, on failure, `paths.sdk_install_error`.
- **GET /api/devices/<device_id>/sdk**: returns SDK metadata (and `docs_hint`) for the AI and tools; 404 if the device has no SDK in catalog.

### Frontend

- Add device form: row **“Install device SDK (recommended)”** with checkbox (default on when device has SDK). Shown only when the selected catalog device has `sdk.available`. On submit, `install_sdk` is sent with the scaffold request; success message shows `sdk_message` and any `sdk_install_error`.

### AI access

- **AGENT_SETUP_CONTEXT.md** and **AGENT_BACKEND_CONTEXT.md** document:
  - That SDKs can be installed when adding a device (checkbox, default on).
  - **GET /api/devices/<device_id>/sdk** for SDK metadata and `docs_hint`.
  - Using `docs_hint` to read `devices/<id>/notes/SDK_AND_TOOLS.md` for per-device SDK/tools and full feature set.
- **Key Documentation Paths** in AGENT_SETUP_CONTEXT point to this file (`docs/SDK_INTEGRATION.md`).

---

## 3. Planned / not yet done

- **Vendor SDKs:** LilyGo/Heltec-specific libraries or ESP-IDF clones are not auto-installed; they can be documented in `devices/<id>/notes/SDK_AND_TOOLS.md` and added manually or via future install_type.
- **Indexing SDK docs for the AI:** No automatic indexing of SDK headers or READMEs; the AI uses `docs_hint` and project files (e.g. platformio.ini, source code) plus MCP/resources as today.
- **MCP tool/resource:** Optional future addition: list SDK-capable devices and their SDK paths or docs so the agent can enumerate and open SDK context in one call.

---

## 4. References

| Topic | Path |
|-------|------|
| Device catalog (sdk field) | `inventory/app/device_catalog.json` |
| Install and SDK path logic | `inventory/app/device_ops.py` |
| Scaffold and GET sdk routes | `inventory/app/app.py` |
| Agent setup and SDK API | `docs/AGENT_SETUP_CONTEXT.md`, `docs/AGENT_BACKEND_CONTEXT.md` |
| Per-device SDK/tools notes | `devices/<device_id>/notes/SDK_AND_TOOLS.md` |
