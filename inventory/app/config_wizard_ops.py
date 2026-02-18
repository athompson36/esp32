"""
Device configuration wizard: pre- and post-flash, internal (Meshtastic/MeshCore) or Launcher.
Loads registry devices, RF presets, and manages config presets under devices/<id>/configs/<firmware>/.
"""
import json
import os
import re
from datetime import datetime

from config import REPO_ROOT
from flash_ops import get_flash_devices


def _repo_root():
    from config import REPO_ROOT
    return REPO_ROOT


def _registry_devices():
    """Load registry/devices/*.json; return list of { id, name, compatible_firmware, launcher_compatible }."""
    root = _repo_root()
    reg_dir = os.path.join(root, "registry", "devices")
    result = []
    if not os.path.isdir(reg_dir):
        return result
    for name in os.listdir(reg_dir):
        if not name.endswith(".json"):
            continue
        path = os.path.join(reg_dir, name)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            fid = data.get("id") or name[:-5]
            compat = data.get("compatible_firmware") or []
            cap = data.get("capability") or {}
            result.append({
                "id": fid,
                "name": data.get("name") or fid,
                "compatible_firmware": compat,
                "launcher_compatible": cap.get("launcher_compatible") is True,
            })
        except (json.JSONDecodeError, OSError):
            continue
    return result


def _rf_presets():
    """Load registry/rf_presets.json; return { presets: [...] }."""
    root = _repo_root()
    path = os.path.join(root, "registry", "rf_presets.json")
    if not os.path.isfile(path):
        return {"presets": []}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {"presets": []}


def get_config_wizard_context():
    """
    Return context for the device config wizard: devices (with compatible firmware),
    firmware targets, RF presets. Devices are merged from registry + flash list.
    """
    flash_list = get_flash_devices()
    flash_ids = {d["id"] for d in flash_list}
    reg_devices = _registry_devices()
    reg_by_id = {d["id"]: d for d in reg_devices}
    devices = []
    for d in flash_list:
        did = d.get("id", "")
        r = reg_by_id.get(did, {})
        compat = r.get("compatible_firmware") or ["meshtastic", "meshcore"]
        if "launcher" not in compat and r.get("launcher_compatible"):
            compat = list(compat) + ["launcher"]
        devices.append({
            "id": did,
            "name": d.get("description") or r.get("name") or did,
            "compatible_firmware": compat,
            "launcher_compatible": r.get("launcher_compatible") is True,
        })
    for d in reg_devices:
        if d["id"] not in flash_ids:
            devices.append({
                "id": d["id"],
                "name": d["name"],
                "compatible_firmware": d.get("compatible_firmware") or [],
                "launcher_compatible": d.get("launcher_compatible") is True,
            })
    firmware_targets = [
        {"id": "meshtastic", "name": "Meshtastic", "internal": True},
        {"id": "meshcore", "name": "MeshCore", "internal": True},
        {"id": "launcher", "name": "Launcher", "internal": False},
        {"id": "bruce", "name": "Bruce", "internal": False},
        {"id": "ghost", "name": "Ghost ESP", "internal": False},
        {"id": "marauder", "name": "Marauder", "internal": False},
        {"id": "flipper_firmware", "name": "Flipper Firmware (official)", "internal": False},
        {"id": "unleashed", "name": "Unleashed", "internal": False},
        {"id": "roguemaster", "name": "RogueMaster", "internal": False},
    ]
    rf = _rf_presets()
    return {
        "devices": devices,
        "firmware_targets": firmware_targets,
        "rf_presets": rf.get("presets", []),
    }


def _safe_preset_name(name):
    """Safe filename: alphanumeric, underscore, hyphen."""
    s = re.sub(r"[^a-zA-Z0-9_\-]", "_", (name or "").strip()).strip("_") or "preset"
    return s[:80]


def get_config_presets_dir(device_id: str, firmware: str):
    """Return path to devices/<device_id>/configs/<firmware>/; None if device dir missing."""
    root = _repo_root()
    dev_dir = os.path.join(root, "devices", device_id.strip())
    if not os.path.isdir(dev_dir):
        return None
    fw = (firmware or "").strip().lower()
    allowed = ("meshtastic", "meshcore", "launcher", "bruce", "ghost", "marauder", "flipper_firmware", "unleashed", "roguemaster")
    if fw not in allowed:
        fw = "meshtastic"
    return os.path.join(dev_dir, "configs", fw)


def list_config_presets(device_id: str, firmware: str):
    """List saved presets for device+firmware. Returns list of { name, path_rel, updated }."""
    base = get_config_presets_dir(device_id, firmware)
    if not base:
        return []
    try:
        os.makedirs(base, exist_ok=True)
    except OSError:
        return []
    root = _repo_root()
    result = []
    for name in os.listdir(base):
        if not name.endswith(".json"):
            continue
        path = os.path.join(base, name)
        if not os.path.isfile(path):
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            result.append({
                "name": data.get("name") or name[:-5],
                "path": os.path.relpath(path, root).replace("\\", "/"),
                "updated": data.get("updated_at") or "",
            })
        except (json.JSONDecodeError, OSError):
            result.append({"name": name[:-5], "path": os.path.relpath(path, root).replace("\\", "/"), "updated": ""})
    return sorted(result, key=lambda x: (x.get("updated") or ""), reverse=True)


def save_config_preset(device_id: str, firmware: str, preset_name: str, options: dict) -> tuple[bool, str]:
    """
    Save a config preset to devices/<device_id>/configs/<firmware>/<safe_name>.json.
    options: dict (region, device_name, channel, etc.). Returns (success, path_or_error).
    """
    base = get_config_presets_dir(device_id, firmware)
    if not base:
        return False, f"Device directory not found: devices/{device_id}"
    try:
        os.makedirs(base, exist_ok=True)
    except OSError as e:
        return False, str(e)
    safe = _safe_preset_name(preset_name) + ".json"
    path = os.path.join(base, safe)
    payload = {
        "device_id": device_id,
        "firmware": (firmware or "").strip().lower() or "meshtastic",
        "name": (preset_name or "preset").strip() or "preset",
        "options": options or {},
        "updated_at": datetime.utcnow().isoformat() + "Z",
    }
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        return True, os.path.relpath(path, _repo_root()).replace("\\", "/")
    except OSError as e:
        return False, str(e)


def load_config_preset(device_id: str, firmware: str, preset_name: str) -> tuple[bool, dict | str]:
    """Load a preset by name (filename without .json). Returns (success, data_or_error)."""
    base = get_config_presets_dir(device_id, firmware)
    if not base or not preset_name:
        return False, "Missing device, firmware, or preset name"
    safe = _safe_preset_name(preset_name) + ".json"
    path = os.path.join(base, safe)
    if not os.path.isfile(path):
        return False, "Preset not found"
    try:
        with open(path, "r", encoding="utf-8") as f:
            return True, json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        return False, str(e)
