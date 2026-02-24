#!/usr/bin/env bash
# Flash from host (esptool). Use artifact from lab-build or a path to .bin.
# Usage:
#   ./scripts/flash.sh [PORT]                    # flash latest t_beam_1w meshtastic factory
#   ./scripts/flash.sh [PORT] t_beam_1w meshtastic [latest|YYYY-MM-DD]
#   ./scripts/flash.sh [PORT] t_beam_1w meshcore [latest|YYYY-MM-DD]
#   ./scripts/flash.sh [PORT] /path/to/firmware.bin
# PORT defaults to first /dev/cu.usbmodem* on macOS if unset.
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# Resolve port and args: first arg can be PORT or (if only arg) path to .bin
PORT=""
BIN_PATH_ARG=""
if [[ -n "${1:-}" && -f "${1}" && "${1}" == *.bin ]]; then
  BIN_PATH_ARG="$1"
  shift
else
  PORT="${1:-}"
  if [[ -n "$PORT" && -e "$PORT" ]]; then
    shift
  else
    PORT=""
  fi
fi
# Auto-detect first USB serial on macOS if PORT not set
if [[ -z "$PORT" ]]; then
  for p in /dev/cu.usbmodem* /dev/cu.usbserial*; do
    [[ -e "$p" ]] && PORT="$p" && break
  done 2>/dev/null
fi
if [[ -z "$PORT" || ! -e "$PORT" ]]; then
  echo "Usage: $0 [PORT] [device_id firmware_id version]" >&2
  echo "       $0 [PORT] /path/to/firmware.bin" >&2
  echo "  Example: $0 /dev/cu.usbmodem101 t_beam_1w meshtastic latest" >&2
  echo "  Example: $0 /path/to/firmware.factory.bin" >&2
  echo "PORT required if no /dev/cu.usbmodem* found." >&2
  exit 1
fi

# Esptool: prefer 'esptool' over 'esptool.py'
ESPTOOL=""
for cmd in esptool esptool.py; do
  if command -v "$cmd" &>/dev/null; then
    ESPTOOL="$cmd"
    break
  fi
done
if [[ -z "$ESPTOOL" ]]; then
  echo "esptool not found. Install: pip install esptool" >&2
  exit 1
fi

# If user passed a path to .bin, use it (flash at 0x0). T-Beam 1W factory images need qio/16MB.
if [[ -n "$BIN_PATH_ARG" ]]; then
  BIN_PATH="$BIN_PATH_ARG"
  ADDR="0x0"
  echo "Flashing $BIN_PATH to $PORT at $ADDR..."
  # Use qio 16MB for full-dump/factory images (e.g. MeshCore merged); safe for other images
  "$ESPTOOL" --chip esp32s3 --port "$PORT" write-flash --flash_mode qio --flash_size 16MB "$ADDR" "$BIN_PATH"
  echo "Done. Power-cycle the device if needed."
  exit 0
fi

# Else use artifacts: device_id firmware_id [version]
DEVICE_ID="${1:-t_beam_1w}"
FIRMWARE_ID="${2:-meshtastic}"
VERSION="${3:-latest}"
ARTIFACT_BASE="$ROOT/artifacts/$DEVICE_ID/$FIRMWARE_ID"
if [[ "$VERSION" == latest ]]; then
  # Most recent date dir (e.g. 2025-02-17)
  LATEST=$(find "$ARTIFACT_BASE" -maxdepth 1 -type d -name "20*" 2>/dev/null | sort -r | head -1)
  if [[ -z "$LATEST" || ! -d "$LATEST" ]]; then
    echo "No build found under $ARTIFACT_BASE (no 20XX-XX-XX version dir)." >&2
    echo "Run: ./scripts/lab-build.sh $DEVICE_ID $FIRMWARE_ID" >&2
    exit 1
  fi
  ARTIFACT_DIR="$LATEST"
else
  ARTIFACT_DIR="$ARTIFACT_BASE/$VERSION"
fi
if [[ ! -d "$ARTIFACT_DIR" ]]; then
  echo "Artifact dir not found: $ARTIFACT_DIR" >&2
  echo "Run: ./scripts/lab-build.sh $DEVICE_ID $FIRMWARE_ID" >&2
  exit 1
fi

# Optional: erase flash first (fixes many no-boot cases). Use ERASE=1 ./scripts/flash.sh ...
if [[ -n "${ERASE:-}" ]]; then
  echo "Erasing flash..."
  "$ESPTOOL" --chip esp32s3 --port "$PORT" erase-flash
  echo "Erase done. Flashing..."
fi

# ESP32/S3: prefer three-part flash (bootloader + partitions + app) when all three exist — most reliable boot
# Use DIO to match Meshtastic build (bootloader/firmware image headers say DIO); QIO can cause ets_loader.c 78
if [[ "$DEVICE_ID" == "t_beam_1w" && -f "$ARTIFACT_DIR/bootloader.bin" && -f "$ARTIFACT_DIR/partitions.bin" && -f "$ARTIFACT_DIR/firmware.bin" ]]; then
  echo "Flashing three parts to $PORT (bootloader @ 0x0, partitions @ 0x8000, firmware @ 0x10000) with DIO, 16MB..."
  "$ESPTOOL" --chip esp32s3 --port "$PORT" write-flash --flash-mode dio --flash-size 16MB \
    0x0 "$ARTIFACT_DIR/bootloader.bin" \
    0x8000 "$ARTIFACT_DIR/partitions.bin" \
    0x10000 "$ARTIFACT_DIR/firmware.bin"
  echo "Done. Power-cycle the device if needed."
  exit 0
fi

# Fallback: single image
if [[ -f "$ARTIFACT_DIR/firmware.factory.bin" ]]; then
  BIN_PATH="$ARTIFACT_DIR/firmware.factory.bin"
  ADDR="0x0"
elif [[ -f "$ARTIFACT_DIR/firmware.bin" ]]; then
  BIN_PATH="$ARTIFACT_DIR/firmware.bin"
  ADDR="0x10000"
else
  echo "No firmware.bin or firmware.factory.bin in $ARTIFACT_DIR" >&2
  exit 1
fi

FLASH_EXTRA=()
if [[ "$DEVICE_ID" == "t_beam_1w" && -f "$ARTIFACT_DIR/firmware.factory.bin" ]]; then
  # Meshtastic images are DIO; MeshCore uses QIO
  if [[ "$FIRMWARE_ID" == "meshtastic" ]]; then
    FLASH_EXTRA=(--flash-mode dio --flash-size 16MB)
  else
    FLASH_EXTRA=(--flash-mode qio --flash-size 16MB)
  fi
fi

echo "Flashing $BIN_PATH to $PORT at $ADDR..."
"$ESPTOOL" --chip esp32s3 --port "$PORT" write-flash "${FLASH_EXTRA[@]}" "$ADDR" "$BIN_PATH"
echo "Done. Power-cycle the device if needed."
