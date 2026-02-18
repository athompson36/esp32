#!/usr/bin/env bash
set -euo pipefail

# Build Meshtastic firmware with the custom T-Beam 1W env.
# Assumes you cloned Meshtastic into ./firmware

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if [[ ! -d "$ROOT/firmware" ]]; then
  echo "ERROR: $ROOT/firmware not found. Clone Meshtastic firmware repo into ./firmware first." >&2
  exit 1
fi

cd "$ROOT/firmware"
pio run -e tbeam-1w
