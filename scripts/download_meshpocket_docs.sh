#!/usr/bin/env bash
# Download official Heltec MeshPocket PDFs into device notes.
# Run from repo root: ./scripts/download_meshpocket_docs.sh
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BASE="$ROOT/devices/ht_mesh_pocket_10000/notes"
mkdir -p "$BASE/datasheet" "$BASE/user_manual"

echo "Downloading MeshPocket datasheet..."
curl -sL -o "$BASE/datasheet/MeshPocket_1.0.0.pdf" \
  "https://resource.heltec.cn/download/MeshPocket/datasheet/MeshPocket_1.0.0.pdf"

echo "Downloading MeshPocket user guide..."
curl -sL -o "$BASE/user_manual/User_Guide_Rev.1.0.1.pdf" \
  "https://resource.heltec.cn/download/MeshPocket/user_manual/User_Guide_Rev.1.0.1.pdf"

echo "Done. PDFs in devices/ht_mesh_pocket_10000/notes/datasheet/ and .../user_manual/"
