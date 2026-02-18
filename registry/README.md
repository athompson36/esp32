# Cyberdeck Manager — Registry

Structured data for the Cyberdeck Manager: devices, firmware metadata, RF presets, CAN firmware.

## Layout

- **devices/** — One JSON per device: `{device_id}.json`. Fields: id, name, mcu, radios, display, battery, storage, flash_methods, compatible_firmware, capability (chip, flash_size, rf_bands, can_support, sd_support, launcher_compatible).
- **firmware/** — Firmware metadata (from GitHub / platformio.ini); to be populated by `scripts/firmware_metadata.py`.
- **forks/** — `{device_id}/{fork_name}/` for custom forks (upstream ref, patches, build flags).
- **rf_presets.json** — Region presets (USA, EU, custom) with bands, TX limits, warnings.
- **can_firmware/** — CAN-capable firmware and bitrate/bus mode metadata.

## Device JSON

Aligned with `devices/*/DEVICE_CONTEXT.md` and `inventory/app/config.FLASH_DEVICES`. Used by:

- Device registry API
- Flash wizard (device → firmware compatibility)
- Hardware inspector (capability matrix)
- RF/CAN enforcement

See **docs/CYBERDECK_MANAGER_SPEC.md** and **docs/cyberdeck_scaffold.md**.
