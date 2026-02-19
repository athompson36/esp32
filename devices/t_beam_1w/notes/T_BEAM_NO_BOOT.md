# T-Beam 1W won’t boot after flash

**Verified working flow:** Build MeshCore → erase → flash **firmware.factory.bin** at 0x0 with qio/16MB. The lab script (`ERASE=1 ./scripts/flash.sh t_beam_1w meshcore latest`) and the **Backup / Flash** UI (choose firmware.factory.bin; T-Beam 1W gets flash_mode qio and flash_size 16MB automatically) both use this. Only full images are shown in the UI (bootloader.bin and partitions.bin are excluded).

If the board doesn’t boot after flashing MeshCore or Meshtastic, work through the list below.

## 1. Use a full image at 0x0 (MeshCore)

- **MeshCore** must be flashed as a **merged image** at **0x0** (bootloader + partitions + boot_app0 + app). Flashing only `firmware.bin` at 0x10000 will not boot unless the rest of flash is already correct.
- From repo root, use the lab script so it picks the merged image:
  ```bash
  ./scripts/flash.sh t_beam_1w meshcore latest
  ```
- In the web UI, choose **firmware.factory.bin** (or a file with “merged” in the name), not plain `firmware.bin`, when flashing MeshCore.

## 2. Rebuild MeshCore (explicit merge)

The lab build now uses **merge_tbeam1w_explicit.sh**: it runs `esptool merge_bin` with fixed segments (0x0 bootloader, 0x8000 partitions, **0xe000 boot_app0**, 0x10000 app) and **qio / 16MB**, so the image no longer depends on PlatformIO’s merge. Rebuild, then erase and flash:

```bash
./scripts/lab-build.sh t_beam_1w meshcore T_Beam_1W_SX1262_repeater
ERASE=1 ./scripts/flash.sh t_beam_1w meshcore latest
```

Verify the image (optional):

```bash
esptool --chip esp32s3 image_info artifacts/t_beam_1w/meshcore/$(date +%Y-%m-%d)/firmware.factory.bin
```

You should see **Flash mode: QIO** and segments at 0x0, 0x8000, 0xe000, 0x10000.

## 3. Erase flash then flash again

Old or mixed contents in flash can prevent boot (e.g. brief green LED then nothing). **Always erase first** when recovering:

```bash
ERASE=1 ./scripts/flash.sh t_beam_1w meshcore latest
```

The script uses `firmware.factory.bin` at 0x0 with `--flash_mode qio --flash_size 16MB` for T-Beam 1W MeshCore. Or with esptool directly:

```bash
esptool --chip esp32s3 --port /dev/cu.usbmodem* erase-flash
esptool --chip esp32s3 --port /dev/cu.usbmodem* write-flash --flash_mode qio --flash_size 16MB 0x0 firmware.factory.bin
```

## 4. Bootloader mode when flashing

Put the T-Beam in bootloader mode before running the flash script:

1. Hold **BOOT**.
2. Press and release **RESET**.
3. Release **BOOT**.

Then run the flash command (or click Flash in the UI) while the board is in this mode.

## 5. Serial: "invalid header: 0xffffffff"

If the serial monitor shows **invalid header: 0xffffffff** repeating, the ESP32 is running but reading **erased flash** (0xFF) at the app partition. So either:

- Flash was erased and not re-flashed, or
- Only part of the image was written (e.g. app at 0x10000 but no bootloader at 0x0), or
- The script used **firmware.bin** (app-only) and wrote it at **0x10000** while the rest of flash is empty.

**Fix:** Erase, then flash the **full factory image** at **0x0** (see steps 1–3 above). Ensure the build produced **firmware.factory.bin** (merge step in lab-build must succeed). Then:

```bash
ERASE=1 ./scripts/flash.sh /dev/cu.usbmodemXXXX t_beam_1w meshcore latest
```

Use your actual port. The script will use `firmware.factory.bin` at 0x0 when present.

## 6. Serial: "ets_loader.c 78" then reset

If you see **mode:QIO**, **load:0x...**, then **ets_loader.c 78** and the board resets (or serial drops), the bootloader ran but failed to load the app at 0x10000. Usually the app partition is corrupt or only partly written.

**Fix:** Full erase, then re-flash the **entire** factory image so the app at 0x10000 is correct:

```bash
ERASE=1 ./scripts/flash.sh /dev/cu.usbmodemXXXX t_beam_1w meshcore latest
```

Confirm the artifact has **firmware.factory.bin** (from a successful build with host merge). The write should be ~1.2 MB at 0x0, not just a few KB.

## 7. Serial output (other)

Connect a serial monitor (e.g. 115200 baud) and power the board. You may see:

- Garbled output or nothing: wrong baud rate, or board not running the app.
- Bootloader then reset loop: bad image or wrong flash layout (use merged image at 0x0 and/or erase then re-flash).
- Clear boot log then app: firmware is running; if the display stays off, the issue may be display or config, not boot.

## 8. Summary

| Step | Action |
|------|--------|
| 1 | Use **firmware.factory.bin** (or merged) at **0x0** for MeshCore. |
| 2 | Rebuild MeshCore so the image uses QIO + 16MB, then re-flash. |
| 3 | Run **ERASE=1 ./scripts/flash.sh …** for a clean full flash. |
| 4 | Put board in bootloader (BOOT + RESET) before flashing. |
| 5 | Check serial at 115200 to see where boot stops. |
