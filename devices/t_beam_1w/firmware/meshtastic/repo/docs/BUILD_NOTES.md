# Build Notes

## Install tooling (macOS)

```bash
brew install platformio
brew install pipx
pipx ensurepath
pipx install esptool
```

Open a new terminal after `pipx ensurepath` so `~/.local/bin` is on PATH.

## Clone Meshtastic

From the project root:

```bash
git clone https://github.com/meshtastic/firmware.git firmware
```

## Apply templates

This starter includes:
- `patches/platformio.env.tbeam-1w.ini` (PlatformIO env snippet)
- `patches/templates/variants/tbeam_1w/` (variant templates)

Copy the variant folder into:

```
firmware/variants/tbeam_1w/
```

Then merge the env snippet into:

```
firmware/platformio.ini
```

## Build

```bash
cd firmware
pio run -e tbeam-1w
```

## Flash

1) Disconnect battery
2) Hold BOOT
3) Plug USB
4) Release BOOT after 5–8 seconds

Then:

```bash
esptool --port /dev/cu.usbmodemXXXX erase-flash
esptool --port /dev/cu.usbmodemXXXX write-flash -z 0x0 .pio/build/tbeam-1w/firmware.bin
```

If the port is busy:

```bash
lsof | grep usbmodem
```

Kill the process holding it.
