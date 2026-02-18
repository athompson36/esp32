"""
Backup, restore, and flash for ESP32-family devices via esptool.
Run from host (USB); when app runs in Docker, USB must be passed through or use host helper.
"""
import os
import re
import subprocess
import tempfile
from datetime import datetime

from config import ARTIFACTS_DIR, BACKUPS_DIR, FLASH_DEVICES, FIRMWARE_TARGETS, REPO_ROOT


def list_serial_ports():
    """Return list of { port, description } using pyserial or filesystem fallback."""
    try:
        import serial.tools.list_ports
        ports = list(serial.tools.list_ports.comports())
        return [{"port": p.device, "description": p.description or p.device} for p in ports]
    except ImportError:
        pass
    # Fallback: common patterns
    candidates = []
    for base in ["/dev/cu.usb", "/dev/tty.usb", "/dev/ttyUSB", "/dev/ttyACM"]:
        parent = os.path.dirname(base)
        if os.path.isdir(parent):
            try:
                for name in os.listdir(parent):
                    if (base.split("/")[-1] in name or "usbserial" in name.lower() or "usbmodem" in name.lower()):
                        candidates.append(os.path.join(parent, name))
            except OSError:
                pass
    return [{"port": p, "description": p} for p in sorted(set(candidates))]


def get_flash_devices():
    """Return list of device dicts for API: { id, chip, flash_size, description }."""
    return [{"id": did, **dict(d)} for did, d in FLASH_DEVICES.items()]


def _chip_from_esptool_output(text):
    """Parse 'Chip is ESP32-S3 (revision 0)' or similar from esptool stdout/stderr. Returns lowercase chip name e.g. esp32s3."""
    if not text:
        return None
    import re
    m = re.search(r"Chip is (ESP32[^\s\(]*(?:\s*\([^)]*\))?)", text, re.IGNORECASE)
    if not m:
        return None
    chip = m.group(1).strip().split("(")[0].strip().lower().replace("-", "")
    # Normalize to esptool --chip values
    if chip.startswith("esp32s3"):
        return "esp32s3"
    if chip.startswith("esp32s2"):
        return "esp32s2"
    if chip.startswith("esp32c3") or chip.startswith("esp32c6"):
        return "esp32c3"  # esptool uses esp32c3 for C3/C6
    if chip.startswith("esp32"):
        return "esp32"
    return chip


def detect_chip_on_port(port, timeout=5):
    """
    Run esptool read_mac on port to detect chip type. Returns (chip, error_message).
    chip is lowercase e.g. esp32s3, or None if detection failed.
    """
    for cmd in ("esptool", "esptool.py"):
        try:
            out = subprocess.run(
                [cmd, "--port", port, "read_mac"],
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            combined = (out.stdout or "") + (out.stderr or "")
            chip = _chip_from_esptool_output(combined)
            if chip:
                return chip, None
            if out.returncode != 0 and combined.strip():
                return None, combined.strip()[:200]
            return None, "Could not detect chip"
        except FileNotFoundError:
            continue
        except subprocess.TimeoutExpired:
            return None, "Timeout"
        except Exception as e:
            return None, str(e)[:200]
    return None, "esptool not found"


def list_serial_ports_with_detection(timeout_per_port=4):
    """
    List ports and, for each, try to detect connected chip. Returns list of
    { port, description, chip, suggested_device_ids }.
    suggested_device_ids: list of device_id from FLASH_DEVICES that use this chip (user can pick).
    """
    ports = list_serial_ports()
    chip_to_devices = {}
    for device_id, dev in FLASH_DEVICES.items():
        c = (dev.get("chip") or "").lower()
        if c:
            chip_to_devices.setdefault(c, []).append(device_id)

    result = []
    for p in ports:
        port = p.get("port") or p.get("description") or ""
        if not port:
            continue
        desc = p.get("description") or port
        chip, err = detect_chip_on_port(port, timeout=timeout_per_port)
        suggested = list(chip_to_devices.get(chip, [])) if chip else []
        result.append({
            "port": port,
            "description": desc,
            "chip": chip,
            "detection_error": err if not chip else None,
            "suggested_device_ids": suggested,
        })
    return result


def _esptool(*args, timeout=120):
    """Run esptool (esptool.py or esptool)."""
    for cmd in ("esptool.py", "esptool"):
        try:
            out = subprocess.run(
                [cmd] + list(args),
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return out.returncode == 0, out.stdout + out.stderr
        except FileNotFoundError:
            continue
        except subprocess.TimeoutExpired:
            return False, "Timeout"
    return False, "esptool not found (pip install esptool)"


def backup_flash(port: str, device_id: str, backup_type: str = "full"):
    """
    Read flash to a file. backup_type: full, app (0x10000 for 0x10000 size ~1MB default), nvs.
    Returns (success, path_or_error, size_bytes).
    """
    dev = FLASH_DEVICES.get(device_id)
    if not dev:
        return False, f"Unknown device: {device_id}", 0
    chip = dev["chip"]
    flash_size = dev.get("flash_size", "8MB")
    size_map = {"4MB": 4 * 1024 * 1024, "8MB": 8 * 1024 * 1024, "16MB": 16 * 1024 * 1024}
    total_size = size_map.get(flash_size, 8 * 1024 * 1024)

    os.makedirs(BACKUPS_DIR, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if backup_type == "full":
        size = total_size
        fname = f"backup_{device_id}_full_{stamp}.bin"
    elif backup_type == "app":
        # Common: app at 0x10000, up to ~1.5MB
        size = 0x180000  # 1.5MB
        fname = f"backup_{device_id}_app_{stamp}.bin"
    elif backup_type == "nvs":
        # NVS often at 0x9000, 24KB
        size = 0x6000
        fname = f"backup_{device_id}_nvs_{stamp}.bin"
    else:
        return False, f"Unknown backup_type: {backup_type}", 0

    if backup_type == "app":
        addr = 0x10000
    elif backup_type == "nvs":
        addr = 0x9000
    else:
        addr = 0

    path = os.path.join(BACKUPS_DIR, fname)
    ok, msg = _esptool(
        "--chip", chip,
        "--port", port,
        "read_flash", str(addr), str(size), path,
        timeout=300,
    )
    if ok and os.path.isfile(path):
        return True, path, size
    return False, msg or "Read failed", 0


def restore_flash(port: str, device_id: str, bin_path: str):
    """Write bin_path to flash at 0x0. Returns (success, message)."""
    dev = FLASH_DEVICES.get(device_id)
    if not dev:
        return False, f"Unknown device: {device_id}"
    if not os.path.isfile(bin_path):
        return False, f"File not found: {bin_path}"
    chip = dev["chip"]
    ok, msg = _esptool(
        "--chip", chip,
        "--port", port,
        "write_flash", "0x0", bin_path,
        timeout=300,
    )
    return ok, msg


def flash_firmware(port: str, device_id: str, bin_path: str, addr: str = "0x0"):
    """Write firmware.bin to flash at addr. Returns (success, message)."""
    dev = FLASH_DEVICES.get(device_id)
    if not dev:
        return False, f"Unknown device: {device_id}"
    if not os.path.isfile(bin_path):
        return False, f"File not found: {bin_path}"
    chip = dev["chip"]
    ok, msg = _esptool(
        "--chip", chip,
        "--port", port,
        "write_flash", addr, bin_path,
        timeout=300,
    )
    return ok, msg


def list_artifacts_and_backups(firmware_filter=None):
    """Return list of { path, name, type: artifact|backup, device?, firmware?, size }.
    firmware_filter: if set (meshtastic|meshcore|launcher), only include artifacts under that firmware folder.
    Backups are always included (no firmware filter)."""
    results = []
    fw_filter = (firmware_filter or "").strip().lower()
    if fw_filter and fw_filter not in FIRMWARE_TARGETS:
        fw_filter = ""
    # Artifacts: artifacts/<device>/<firmware>/...
    if os.path.isdir(ARTIFACTS_DIR):
        for dev in os.listdir(ARTIFACTS_DIR):
            dev_path = os.path.join(ARTIFACTS_DIR, dev)
            if dev == "backups" or not os.path.isdir(dev_path):
                continue
            for fw in os.listdir(dev_path):
                fw_path = os.path.join(dev_path, fw)
                if not os.path.isdir(fw_path):
                    continue
                if fw_filter and fw.lower() != fw_filter:
                    continue
                for name in os.listdir(fw_path):
                    full = os.path.join(fw_path, name)
                    if os.path.isdir(full):
                        for f in os.listdir(full):
                            if f.endswith(".bin"):
                                p = os.path.join(full, f)
                                results.append({
                                    "path": os.path.relpath(p, REPO_ROOT),
                                    "name": f"{dev}/{fw}/{name}/{f}",
                                    "type": "artifact",
                                    "device": dev,
                                    "firmware": fw,
                                    "size": os.path.getsize(p) if os.path.isfile(p) else 0,
                                })
                    elif name.endswith(".bin"):
                        results.append({
                            "path": os.path.relpath(full, REPO_ROOT),
                            "name": f"{dev}/{fw}/{name}",
                            "type": "artifact",
                            "device": dev,
                            "firmware": fw,
                            "size": os.path.getsize(full) if os.path.isfile(full) else 0,
                        })
    # Backups
    if os.path.isdir(BACKUPS_DIR):
        for name in os.listdir(BACKUPS_DIR):
            if not name.endswith(".bin"):
                continue
            full = os.path.join(BACKUPS_DIR, name)
            if os.path.isfile(full):
                results.append({
                    "path": os.path.relpath(full, REPO_ROOT),
                    "name": name,
                    "type": "backup",
                    "device": None,
                    "size": os.path.getsize(full),
                })
    return results
