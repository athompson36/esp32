"""Load device and firmware registries from JSON files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent
DEVICE_DIR = _REPO_ROOT / "registry" / "devices"
FIRMWARE_DIR = _REPO_ROOT / "registry" / "firmware"
RF_PRESETS = _REPO_ROOT / "registry" / "rf_presets.json"


def load_devices() -> dict[str, dict[str, Any]]:
    """Return {device_id: {...}} from registry/devices/*.json."""
    out: dict[str, dict[str, Any]] = {}
    if not DEVICE_DIR.is_dir():
        return out
    for p in sorted(DEVICE_DIR.glob("*.json")):
        data = json.loads(p.read_text())
        out[data.get("id", p.stem)] = data
    return out


def load_firmware() -> dict[str, dict[str, Any]]:
    """Return {firmware_id: {...}} from registry/firmware/*.json."""
    out: dict[str, dict[str, Any]] = {}
    if not FIRMWARE_DIR.is_dir():
        return out
    for p in sorted(FIRMWARE_DIR.glob("*.json")):
        data = json.loads(p.read_text())
        out[data.get("id", p.stem)] = data
    return out


def load_rf_presets() -> list[dict[str, Any]]:
    """Return list of RF presets from registry/rf_presets.json."""
    if not RF_PRESETS.is_file():
        return []
    data = json.loads(RF_PRESETS.read_text())
    return data.get("presets", [])
