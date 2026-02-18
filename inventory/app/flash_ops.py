"""
Backup, restore, and flash for ESP32-family devices via esptool.
Run from host (USB); when app runs in Docker, USB must be passed through or use host helper.
"""
import os
import re
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.request
from datetime import datetime

from config import ARTIFACTS_DIR, BACKUPS_DIR, BUILD_CONFIG, FLASH_DEVICES, FIRMWARE_TARGETS, REPO_ROOT


def _list_serial_ports_fallback():
    """Scan /dev for common USB serial device names (used when pyserial returns nothing)."""
    candidates = []
    dev = "/dev"
    if not os.path.isdir(dev):
        return []
    try:
        for name in sorted(os.listdir(dev)):
            low = name.lower()
            # macOS: cu.usbmodem*, cu.usbserial*, tty.usbmodem*, tty.usbserial*
            if name.startswith("cu.") and ("usbmodem" in low or "usbserial" in low):
                candidates.append(os.path.join(dev, name))
            elif name.startswith("tty.") and ("usbmodem" in low or "usbserial" in low):
                candidates.append(os.path.join(dev, name))
            # Linux: ttyUSB*, ttyACM*
            elif name.startswith("ttyUSB") or name.startswith("ttyACM"):
                candidates.append(os.path.join(dev, name))
    except OSError:
        pass
    return [{"port": p, "description": p} for p in candidates]


# Port path substrings to exclude (virtual/debug ports that are not ESP32 serial devices)
_SERIAL_PORT_EXCLUDE = ("debug-console", "bluetooth-incoming", "tty.debug", "cu.debug")


def _is_excluded_port(port_path: str, description: str = "") -> bool:
    """True if this port should be excluded from backup/flash/health (e.g. debug-console)."""
    combined = ((port_path or "") + " " + (description or "")).lower()
    return any(ex in combined for ex in _SERIAL_PORT_EXCLUDE)


def list_serial_ports():
    """Return list of { port, description }. Excludes virtual/debug ports (e.g. cu.debug-console)."""
    seen = {}
    try:
        import serial.tools.list_ports
        for p in serial.tools.list_ports.comports():
            path = getattr(p, "device", None) or getattr(p, "path", None)
            if path and path not in seen and not _is_excluded_port(path, p.description or ""):
                seen[path] = {"port": path, "description": (p.description or path)}
    except ImportError:
        pass
    if not seen:
        for item in _list_serial_ports_fallback():
            path = item["port"]
            if path not in seen and os.path.exists(path) and not _is_excluded_port(path, item.get("description") or ""):
                seen[path] = item
    return list(seen.values()) if seen else _list_serial_ports_fallback()


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


def _run_esptool_read_mac(cmd, port, chip=None, timeout=5):
    """Run esptool read-mac; optional --chip. Returns (combined_stdout_stderr, returncode)."""
    args = [cmd, "--port", port]
    if chip:
        args.extend(["--chip", chip])
    args.append("read-mac")
    out = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    return (out.stdout or "") + (out.stderr or ""), out.returncode


def detect_chip_on_port(port, timeout=5):
    """
    Run esptool read_mac on port to detect chip type. Returns (chip, error_message).
    chip is lowercase e.g. esp32s3, or None if detection failed.
    Tries auto-detect first, then --chip esp32s3 (T-Beam 1W, T-Deck Plus), then --chip esp32.
    """
    for cmd in ("esptool", "esptool.py"):
        try:
            last_error = None
            # Try without --chip first (auto-detect)
            try:
                combined, rc = _run_esptool_read_mac(cmd, port, chip=None, timeout=timeout)
                chip = _chip_from_esptool_output(combined)
                if chip:
                    return chip, None
                if rc != 0 and combined.strip():
                    last_error = combined.strip()[:200]
            except subprocess.TimeoutExpired:
                pass  # try explicit --chip next
            # ESP32-S3 often needs explicit --chip (e.g. T-Beam 1W in bootloader)
            for try_chip in ("esp32s3", "esp32"):
                try:
                    combined2, rc2 = _run_esptool_read_mac(cmd, port, chip=try_chip, timeout=timeout)
                    chip = _chip_from_esptool_output(combined2)
                    if chip:
                        return chip, None
                except subprocess.TimeoutExpired:
                    continue
            return None, last_error or "Could not detect chip"
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
    """Run esptool (prefer 'esptool'; esptool.py is deprecated in v5+)."""
    for cmd in ("esptool", "esptool.py"):
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
        "read-flash", str(addr), str(size), path,
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
        "write-flash", "0x0", bin_path,
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
        "write-flash", addr, bin_path,
        timeout=300,
    )
    return ok, msg


def get_build_config():
    """Return BUILD_CONFIG as a list of { device_id, firmware_id, path, envs, build_subdir? } for the UI."""
    out = []
    for device_id, firmwares in (BUILD_CONFIG or {}).items():
        for firmware_id, cfg in firmwares.items():
            if not isinstance(cfg, dict):
                continue
            out.append({
                "device_id": device_id,
                "firmware_id": firmware_id,
                "path": cfg.get("path", ""),
                "envs": cfg.get("envs") or [],
                "build_subdir": cfg.get("build_subdir"),
            })
    return out


def list_patches(device_id: str, firmware_id: str):
    """
    List available .patch files for a device/firmware. Patches live under <path>/patches/*.patch.
    Returns list of { path, name } where path is relative to the repo (e.g. "patches/001-foo.patch").
    """
    if not BUILD_CONFIG or device_id not in BUILD_CONFIG or firmware_id not in BUILD_CONFIG[device_id]:
        return []
    cfg = BUILD_CONFIG[device_id][firmware_id]
    path = (cfg.get("path") or "").strip()
    if not path:
        return []
    patches_dir = os.path.join(REPO_ROOT, path, "patches")
    if not os.path.isdir(patches_dir):
        return []
    result = []
    for name in sorted(os.listdir(patches_dir)):
        if name.endswith(".patch") and os.path.isfile(os.path.join(patches_dir, name)):
            result.append({"path": os.path.join("patches", name), "name": name})
    return result


def build_firmware(device_id: str, firmware_id: str, env_name: str, patch_paths=None, timeout: int = 300, clean: bool = False, verbose: bool = False):
    """
    Run PlatformIO build for the given device/firmware/env. Optionally apply patch_paths (list of
    paths relative to repo) before building; tree is reverted after. If clean, run clean target first.
    If verbose, pass -v to pio. Copy resulting .bin to artifacts.
    Returns (ok: bool, path_or_error: str). path is relative to REPO_ROOT.
    """
    if not BUILD_CONFIG or device_id not in BUILD_CONFIG or firmware_id not in BUILD_CONFIG[device_id]:
        return False, "Unknown device or firmware"
    cfg = BUILD_CONFIG[device_id][firmware_id]
    path = (cfg.get("path") or "").strip()
    envs = cfg.get("envs") or []
    if env_name not in envs:
        env_name = (envs[0] if envs else "")
    if not env_name:
        return False, "No build env specified"
    build_subdir = cfg.get("build_subdir")
    repo_dir = os.path.join(REPO_ROOT, path)
    work_dir = repo_dir
    if build_subdir:
        work_dir = os.path.join(repo_dir, build_subdir.strip("/"))
    if not os.path.isdir(work_dir):
        return False, f"Build dir not found: {work_dir}"
    patch_paths = [p for p in (patch_paths or []) if p and isinstance(p, str)]
    applied = False
    try:
        if patch_paths:
            # Reset work tree so we apply only the selected patches
            r = subprocess.run(
                ["git", "checkout", "-f", "."],
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if r.returncode != 0:
                return False, (r.stderr or r.stdout or "git checkout failed")[:300]
            for rel in patch_paths:
                # Patch file is at repo_dir/rel; we apply from work_dir with -p1
                patch_abs = os.path.join(REPO_ROOT, path, rel)
                if not os.path.isfile(patch_abs):
                    return False, f"Patch not found: {rel}"
                with open(patch_abs, "rb") as f:
                    r = subprocess.run(
                        ["git", "apply", "-p1", "--verbose"],
                        cwd=work_dir,
                        stdin=f,
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )
                if r.returncode != 0:
                    return False, f"Patch {rel} failed: {(r.stderr or r.stdout or '')[:300]}"
            applied = True
        # Optional: clean before build
        if clean:
            for cmd in ("pio", "platformio"):
                try:
                    subprocess.run(
                        [cmd, "run", "-t", "clean", "-e", env_name],
                        cwd=work_dir,
                        capture_output=True,
                        text=True,
                        timeout=120,
                    )
                    break
                except FileNotFoundError:
                    continue
        # PlatformIO output: .pio/build/<env>/firmware.bin (env name as-is, e.g. tbeam-1w)
        pio_build_dir = os.path.join(work_dir, ".pio", "build", env_name)
        bin_name = "firmware.bin"
        out_bin = os.path.join(pio_build_dir, bin_name)
        for cmd in ("pio", "platformio"):
            try:
                r = subprocess.run(
                    [cmd, "run", "-e", env_name] + (["-v"] if verbose else []),
                    cwd=work_dir,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )
                if r.returncode != 0:
                    if applied:
                        subprocess.run(["git", "checkout", "-f", "."], cwd=work_dir, capture_output=True, timeout=10)
                    return False, (r.stderr or r.stdout or "Build failed")[:500]
                if not os.path.isfile(out_bin):
                    if applied:
                        subprocess.run(["git", "checkout", "-f", "."], cwd=work_dir, capture_output=True, timeout=10)
                    return False, f"Build succeeded but {bin_name} not found in .pio/build/{env_name}"
                break
            except FileNotFoundError:
                continue
            except subprocess.TimeoutExpired:
                if applied:
                    subprocess.run(["git", "checkout", "-f", "."], cwd=work_dir, capture_output=True, timeout=10)
                return False, "Build timed out"
            except Exception as e:
                if applied:
                    subprocess.run(["git", "checkout", "-f", "."], cwd=work_dir, capture_output=True, timeout=10)
                return False, str(e)[:300]
        else:
            return False, "PlatformIO not found (pip install platformio)"
        # Copy to artifacts/<device_id>/<firmware_id>/build_<env>_<timestamp>/
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_env = re.sub(r"[^\w\-]", "_", env_name)
        artifact_subdir = os.path.join(ARTIFACTS_DIR, device_id, firmware_id, f"build_{safe_env}_{ts}")
        os.makedirs(artifact_subdir, exist_ok=True)
        dest = os.path.join(artifact_subdir, bin_name)
        shutil.copy2(out_bin, dest)
        return True, os.path.relpath(dest, REPO_ROOT)
    finally:
        if applied:
            subprocess.run(["git", "checkout", "-f", "."], cwd=work_dir, capture_output=True, timeout=10)


def download_release_firmware(
    owner: str,
    repo: str,
    tag: str = None,
    device_id: str = None,
    firmware_id: str = None,
    asset_filter: str = None,
    timeout: int = 120,
):
    """
    Download a .bin asset from a GitHub release to artifacts. Returns (ok, path_or_error).
    path is relative to REPO_ROOT.
    asset_filter: optional substring to match in asset name (e.g. "tbeam", "t-beam" for T-Beam).
    """
    from updates import fetch_release_with_assets
    info = fetch_release_with_assets(owner, repo, tag=tag)
    if info.get("error"):
        return False, info["error"]
    release_tag = (info.get("tag") or "").strip()
    assets = info.get("assets") or []
    # Prefer .bin assets; optionally filter by name
    candidates = [a for a in assets if (a.get("name") or "").lower().endswith(".bin")]
    if asset_filter:
        af = asset_filter.lower()
        candidates = [a for a in candidates if af in (a.get("name") or "").lower()]
    if not candidates:
        return False, "No matching .bin asset in release"
    asset = candidates[0]
    url = asset.get("browser_download_url") or ""
    name = asset.get("name") or "firmware.bin"
    if not url:
        return False, "Asset has no download URL"
    device_id = (device_id or "ota").replace(" ", "_")
    firmware_id = (firmware_id or repo).replace(" ", "_")
    ota_dir = os.path.join(ARTIFACTS_DIR, device_id, firmware_id, "ota")
    os.makedirs(ota_dir, exist_ok=True)
    safe_tag = re.sub(r"[^\w\.\-]", "_", release_tag)
    safe_name = re.sub(r"[^\w\.\-]", "_", name)
    dest_name = f"{safe_tag}_{safe_name}" if safe_tag else safe_name
    dest_path = os.path.join(ota_dir, dest_name)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Cyber-Lab-Inventory/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            with open(dest_path, "wb") as f:
                f.write(resp.read())
    except (OSError, urllib.error.URLError, Exception) as e:
        return False, str(e)[:300]
    if not os.path.isfile(dest_path):
        return False, "Download failed"
    return True, os.path.relpath(dest_path, REPO_ROOT)


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
