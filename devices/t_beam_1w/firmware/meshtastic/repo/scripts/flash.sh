#!/usr/bin/env bash
set -euo pipefail

# Usage: ./scripts/flash.sh /dev/cu.usbmodemXXXX

PORT="${1:-}"
if [[ -z "$PORT" ]]; then
  echo "Usage: $0 /dev/cu.usbmodemXXXX" >&2
  exit 1
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FW="$ROOT/firmware/.pio/build/tbeam-1w/firmware.bin"

if [[ ! -f "$FW" ]]; then
  echo "ERROR: Built firmware not found: $FW" >&2
  echo "Run: ./scripts/build.sh" >&2
  exit 1
fi

echo "Erasing flash on $PORT..."
esptool --port "$PORT" erase-flash

echo "Flashing $FW to $PORT..."
esptool --port "$PORT" write-flash -z 0x0 "$FW"

echo "Done. Power-cycle the device (unplug USB + battery, wait 10s, replug) and do NOT hold BOOT."
