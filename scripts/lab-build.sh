#!/usr/bin/env bash
# Minimal orchestrator: build device firmware in platformio-lab container, write to artifacts/.
# Usage: lab-build.sh [device_id] [firmware_id] [env_name]
# Example: ./scripts/lab-build.sh t_beam_1w meshcore T_Beam_1W_SX1262_repeater
# Build in container, flash from host. See CONTEXT.md and docker/README.md.
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

DEVICE_ID="${1:-t_beam_1w}"
FIRMWARE_ID="${2:-meshcore}"
ENV_NAME="${3:-}"

# Resolve work dir: devices/<device>/firmware/<firmware>/repo or repo/firmware (Meshtastic)
WORK_DIR="$ROOT/devices/$DEVICE_ID/firmware/$FIRMWARE_ID"
[ -d "$WORK_DIR/repo" ] && WORK_DIR="$WORK_DIR/repo"
if [ ! -f "$WORK_DIR/platformio.ini" ] && [ -f "$WORK_DIR/firmware/platformio.ini" ]; then
  WORK_DIR="$WORK_DIR/firmware"
fi
if [ ! -f "$WORK_DIR/platformio.ini" ]; then
  echo "lab-build: no platformio.ini at $WORK_DIR" >&2
  exit 1
fi
WORK_REL="${WORK_DIR#$ROOT/}"

# Default env per device/firmware
if [ -z "$ENV_NAME" ]; then
  case "$DEVICE_ID/$FIRMWARE_ID" in
    t_beam_1w/meshcore)   ENV_NAME="T_Beam_1W_SX1262_repeater" ;;
    t_beam_1w/meshtastic) ENV_NAME="t-beam-1w" ;;
    *) echo "lab-build: pass env name as third argument (e.g. pio run -e <env>)" >&2; exit 1 ;;
  esac
fi

# Version dir: date or env slug
VERSION="${4:-$(date +%Y-%m-%d)}"
ARTIFACT_DIR="$ROOT/artifacts/$DEVICE_ID/$FIRMWARE_ID/$VERSION"
mkdir -p "$ARTIFACT_DIR"

echo "lab-build: device=$DEVICE_ID firmware=$FIRMWARE_ID env=$ENV_NAME -> $ARTIFACT_DIR"
echo "Running in container (platformio-lab)..."
if [ "$FIRMWARE_ID" = "meshcore" ]; then
  # Build then explicit merge in same container (framework packages needed for boot_app0).
  # Merge can fail if esptool not on PATH; copy boot_app0 out so host can merge.
  ARTIFACT_REL="artifacts/$DEVICE_ID/$FIRMWARE_ID/$VERSION"
  docker run --rm \
    -v "$ROOT:/workspace" \
    -w "/workspace/$WORK_REL" \
    -e "ARTIFACT_REL=$ARTIFACT_REL" \
    platformio-lab \
    bash -c "pio run -e '$ENV_NAME'; ( chmod +x merge_tbeam1w_explicit.sh 2>/dev/null; ./merge_tbeam1w_explicit.sh '$ENV_NAME' ) || true; mkdir -p \"/workspace/\$ARTIFACT_REL\" && for b in /root/.platformio/packages/framework-arduinoespressif32 \$HOME/.platformio/packages/framework-arduinoespressif32; do [ -f \"\$b/tools/partitions/boot_app0.bin\" ] && cp \"\$b/tools/partitions/boot_app0.bin\" \"/workspace/\$ARTIFACT_REL/boot_app0.bin\" && echo 'Copied boot_app0 to artifact dir' && break; done"
else
  docker run --rm \
    -v "$ROOT:/workspace" \
    -w "/workspace/$WORK_REL" \
    platformio-lab \
    pio run -e "$ENV_NAME"
fi

# Copy build output (MeshCore: firmware.bin + firmware-merged.bin; Meshtastic: firmware*.bin and .factory.bin)
BUILD_OUT="$WORK_DIR/.pio/build/$ENV_NAME"
FIRM_BIN=""
if [ -f "$BUILD_OUT/firmware.bin" ]; then
  FIRM_BIN="$BUILD_OUT/firmware.bin"
elif [ -d "$BUILD_OUT" ]; then
  FIRM_BIN=$(find "$BUILD_OUT" -maxdepth 1 -name "firmware*.bin" ! -name "*.factory.bin" ! -name "*-merged.bin" -type f | head -1)
fi
if [ -n "$FIRM_BIN" ] && [ -f "$FIRM_BIN" ]; then
  cp "$FIRM_BIN" "$ARTIFACT_DIR/firmware.bin"
  echo "Copied $(basename "$FIRM_BIN") -> $ARTIFACT_DIR/firmware.bin"
  [ -f "$BUILD_OUT/partitions.bin" ] && cp "$BUILD_OUT/partitions.bin" "$ARTIFACT_DIR/" && echo "  + partitions.bin"
  [ -f "$BUILD_OUT/bootloader.bin" ] && cp "$BUILD_OUT/bootloader.bin" "$ARTIFACT_DIR/" && echo "  + bootloader.bin"
  # Prefer explicit factory image (MeshCore) or .factory.bin (Meshtastic) for full flash at 0x0
  if [ -f "$BUILD_OUT/firmware.factory.bin" ]; then
    cp "$BUILD_OUT/firmware.factory.bin" "$ARTIFACT_DIR/firmware.factory.bin"
    echo "  + firmware.factory.bin (explicit merge: flash at 0x0)"
  elif [ -f "$BUILD_OUT/firmware-merged.bin" ]; then
    cp "$BUILD_OUT/firmware-merged.bin" "$ARTIFACT_DIR/firmware.factory.bin"
    echo "  + firmware.factory.bin (merged: flash at 0x0)"
  else
    FACTORY=$(find "$BUILD_OUT" -maxdepth 1 -name "*.factory.bin" -type f | head -1)
    [ -n "$FACTORY" ] && cp "$FACTORY" "$ARTIFACT_DIR/firmware.factory.bin" && echo "  + firmware.factory.bin (flash at 0x0)"
  fi
  # MeshCore: if factory image still missing, merge on host (container merge may have failed)
  if [ "$FIRMWARE_ID" = "meshcore" ] && [ ! -f "$ARTIFACT_DIR/firmware.factory.bin" ] && [ -f "$ARTIFACT_DIR/bootloader.bin" ] && [ -f "$ARTIFACT_DIR/partitions.bin" ] && [ -f "$ARTIFACT_DIR/firmware.bin" ]; then
    echo "  Merging on host (bootloader + partitions + boot_app0 + app) -> firmware.factory.bin..."
    BOOT_APP0="$ARTIFACT_DIR/boot_app0.bin"
    if [ ! -f "$BOOT_APP0" ]; then
      docker run --rm -v "$ROOT:/workspace" -w "/workspace/$WORK_REL" platformio-lab \
        sh -c 'for b in /root/.platformio/packages/framework-arduinoespressif32 "$HOME/.platformio/packages/framework-arduinoespressif32"; do [ -f "$b/tools/partitions/boot_app0.bin" ] && cat "$b/tools/partitions/boot_app0.bin" && exit 0; done; exit 1' > "$BOOT_APP0" 2>/dev/null || true
      [ ! -s "$BOOT_APP0" ] && rm -f "$BOOT_APP0"
    fi
    if [ -f "$BOOT_APP0" ]; then
      ESPTOOL_HOST=""
      for cmd in esptool esptool.py; do command -v "$cmd" >/dev/null 2>&1 && ESPTOOL_HOST="$cmd" && break; done
      if [ -n "$ESPTOOL_HOST" ]; then
        ( cd "$ARTIFACT_DIR" && "$ESPTOOL_HOST" --chip esp32s3 merge_bin -o firmware.factory.bin --flash_mode qio --flash_freq 80m --flash_size 16MB 0x0 bootloader.bin 0x8000 partitions.bin 0xe000 boot_app0.bin 0x10000 firmware.bin ) && echo "  + firmware.factory.bin (host merge: flash at 0x0)"
      fi
    fi
  fi
else
  echo "lab-build: no firmware.bin at $BUILD_OUT" >&2
  exit 1
fi
echo "Done. Flash from host: ./scripts/flash.sh (uses firmware.factory.bin at 0x0 when present)"
