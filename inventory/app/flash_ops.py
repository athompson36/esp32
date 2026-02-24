"""
Backup, restore, and flash for ESP32-family devices via esptool.
Run from host (USB); when app runs in Docker, USB must be passed through or use host helper.
"""
import os
import re
import shutil
import subprocess
import tempfile
import threading
import time as _time
import urllib.error
import urllib.request
from datetime import datetime

from config import ARTIFACTS_DIR, BACKUPS_DIR, BUILD_CONFIG, FLASH_DEVICES, FIRMWARE_TARGETS, REPO_ROOT


# Backup progress: shared state so UI can poll during long chunked reads.
_backup_progress_lock = threading.Lock()
_backup_progress = {}  # {"pct": 0-100, "chunk": N, "total_chunks": N, "status": "reading"|"done"|"error", "error": "..."}


def get_backup_progress() -> dict:
    with _backup_progress_lock:
        return dict(_backup_progress)


def _set_backup_progress(**kw):
    with _backup_progress_lock:
        _backup_progress.update(kw)


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


def get_alternate_port(port: str) -> str | None:
    """Return the other port for the same device (cu <-> tty on macOS/Linux). None if no alternate exists."""
    if not port or not os.path.isabs(port):
        return None
    base = os.path.basename(port)
    dirpath = os.path.dirname(port)
    if base.startswith("cu.") and ("usbmodem" in base.lower() or "usbserial" in base.lower()):
        alt = os.path.join(dirpath, "tty." + base[3:])
    elif base.startswith("tty.") and ("usbmodem" in base.lower() or "usbserial" in base.lower()):
        alt = os.path.join(dirpath, "cu." + base[4:])
    else:
        return None
    return alt if os.path.exists(alt) else None

# Artifact .bin files that are components only — do not offer for flash (would write partial image)
_FLASH_EXCLUDE_BIN = frozenset(("bootloader.bin", "partitions.bin"))


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


def _kill_esptool_on_port(port: str) -> None:
    """Kill any running esptool process that is using this port (stale from a previous timed-out request)."""
    if not port:
        return
    try:
        out = subprocess.run(
            ["pgrep", "-af", "esptool"],
            capture_output=True, text=True, timeout=5,
        )
        for line in (out.stdout or "").splitlines():
            if port in line or (get_alternate_port(port) or "") in line:
                pid_str = line.strip().split()[0]
                try:
                    os.kill(int(pid_str), 9)
                except (ValueError, ProcessLookupError, PermissionError):
                    pass
    except Exception:
        pass


def _esptool(*args, timeout=120):
    """Run esptool with explicit kill on timeout (prefer 'esptool'; esptool.py is deprecated in v5+)."""
    for cmd in ("esptool", "esptool.py"):
        try:
            proc = subprocess.Popen(
                [cmd] + list(args),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            try:
                stdout, stderr = proc.communicate(timeout=timeout)
                return proc.returncode == 0, (stdout or "") + (stderr or "")
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)
                return False, "Timeout"
        except FileNotFoundError:
            continue
    return False, "esptool not found (pip install esptool)"


def _sanitize_backup_name(name: str) -> str:
    """Make a safe filename for backup: alphanumeric, dash, underscore; ensure .bin."""
    if not name or not name.strip():
        return ""
    s = re.sub(r"[^\w\-.]", "_", name.strip())
    s = re.sub(r"_+", "_", s).strip("_.")
    if not s:
        return ""
    return s + ".bin" if not s.lower().endswith(".bin") else s


def backup_flash(port: str, device_id: str, backup_type: str = "full", name: str = None):
    """
    Read flash to a file. backup_type: full, app (0x10000 for 0x10000 size ~1MB default), nvs.
    name: optional custom filename (saved under BACKUPS_DIR); must be safe (alphanumeric, dash, underscore).
    Returns (success, path_or_error, size_bytes).
    """
    dev = FLASH_DEVICES.get(device_id)
    if not dev:
        return False, f"Unknown device: {device_id}", 0
    if dev.get("flash_method") == "uf2":
        return False, "This device uses UF2 flashing. Use the magnetic pogo cable and copy a UF2 file to the HT-n5262 drive. See device notes (e.g. devices/ht_mesh_pocket_10000/notes/FLASHING_UF2.md).", 0
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

    custom = _sanitize_backup_name(name) if name else ""
    if custom:
        fname = custom

    if backup_type == "app":
        addr = 0x10000
    elif backup_type == "nvs":
        addr = 0x9000
    else:
        addr = 0

    path = os.path.join(BACKUPS_DIR, fname)

    if backup_type == "full":
        # Chunked read: ESP32-S3 USB-Serial/JTAG drops data on long reads.
        # Read in 1MB chunks, retry each chunk up to 3 times, then concatenate.
        ok, err = _chunked_read_flash(chip, port, addr, size, path)
        if ok:
            return True, path, size
        return False, err, 0

    ok, msg = _esptool("--chip", chip, "--port", port,
                        "read-flash", str(addr), str(size), path,
                        timeout=300)
    if ok and os.path.isfile(path):
        return True, path, size
    return False, msg or "Read failed", 0


_CHUNK_SIZE = 0x100000  # 1 MB per chunk
_CHUNK_RETRIES = 3


def _chunked_read_flash(chip: str, port: str, start_addr: int, total_size: int, out_path: str):
    """Read flash in 1MB chunks to avoid USB-Serial/JTAG corruption on long reads.
    Updates _backup_progress so the UI can poll. Returns (success, error_message_or_None)."""
    total_chunks = (total_size + _CHUNK_SIZE - 1) // _CHUNK_SIZE
    _set_backup_progress(pct=0, chunk=0, total_chunks=total_chunks, status="reading", error=None)
    tmp_dir = tempfile.mkdtemp(prefix="flash_chunks_")
    try:
        offset = start_addr
        chunk_paths = []
        remaining = total_size
        chunk_idx = 0
        while remaining > 0:
            chunk_size = min(_CHUNK_SIZE, remaining)
            chunk_file = os.path.join(tmp_dir, f"chunk_{offset:08x}.bin")
            ok = False
            last_err = ""
            for attempt in range(_CHUNK_RETRIES):
                ok, msg = _esptool(
                    "--chip", chip, "--port", port,
                    "read-flash", str(offset), str(chunk_size), chunk_file,
                    timeout=180,
                )
                if ok and os.path.isfile(chunk_file) and os.path.getsize(chunk_file) == chunk_size:
                    break
                last_err = msg or "Read failed"
                _time.sleep(2)
            if not ok:
                _set_backup_progress(status="error", error=f"Failed at 0x{offset:X}")
                return False, last_err or f"Read failed at offset 0x{offset:X}"
            chunk_paths.append(chunk_file)
            offset += chunk_size
            remaining -= chunk_size
            chunk_idx += 1
            _set_backup_progress(pct=round(100 * chunk_idx / total_chunks), chunk=chunk_idx)

        _set_backup_progress(pct=100, status="assembling")
        with open(out_path, "wb") as out_f:
            for cp in chunk_paths:
                with open(cp, "rb") as cf:
                    shutil.copyfileobj(cf, out_f)
        _set_backup_progress(status="done")
        return True, None
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def _write_flash_args(dev: dict):
    """Extra esptool write-flash args from device (flash_mode, flash_size) if set."""
    args = []
    if dev.get("flash_mode"):
        args.extend(("--flash_mode", dev["flash_mode"]))
    if dev.get("flash_size"):
        args.extend(("--flash_size", dev["flash_size"]))
    return args


def restore_flash(port: str, device_id: str, bin_path: str):
    """Write bin_path to flash at 0x0. Returns (success, message)."""
    dev = FLASH_DEVICES.get(device_id)
    if not dev:
        return False, f"Unknown device: {device_id}"
    if dev.get("flash_method") == "uf2":
        return False, "This device uses UF2 flashing. Use the magnetic pogo cable and copy a UF2 file to the HT-n5262 drive. See device notes."
    if not os.path.isfile(bin_path):
        return False, f"File not found: {bin_path}"
    chip = dev["chip"]
    extra = _write_flash_args(dev)
    ok, msg = _esptool(
        "--chip", chip,
        "--port", port,
        "write-flash", *extra, "0x0", bin_path,
        timeout=300,
    )
    return ok, msg


def flash_firmware(port: str, device_id: str, bin_path: str, addr: str = "0x0"):
    """Write firmware.bin to flash at addr. Returns (success, message)."""
    dev = FLASH_DEVICES.get(device_id)
    if not dev:
        return False, f"Unknown device: {device_id}"
    if dev.get("flash_method") == "uf2":
        return False, "This device uses UF2 flashing. Use the magnetic pogo cable and copy a UF2 file to the HT-n5262 drive. See device notes."
    if not os.path.isfile(bin_path):
        return False, f"File not found: {bin_path}"
    chip = dev["chip"]
    extra = _write_flash_args(dev)
    ok, msg = _esptool(
        "--chip", chip,
        "--port", port,
        "write-flash", *extra, addr, bin_path,
        timeout=300,
    )
    return ok, msg


def get_build_config():
    """Return BUILD_CONFIG as a list of { device_id, firmware_id, path, envs, build_subdir?, toolchain? } for the UI."""
    out = []
    for device_id, firmwares in (BUILD_CONFIG or {}).items():
        for firmware_id, cfg in firmwares.items():
            if not isinstance(cfg, dict):
                continue
            envs = cfg.get("envs") or []
            # IDF builds use lab-build.sh (no env); provide a single placeholder so UI can trigger build
            if cfg.get("toolchain") == "idf" and not envs:
                envs = ["default"]
            out.append({
                "device_id": device_id,
                "firmware_id": firmware_id,
                "path": cfg.get("path", ""),
                "envs": envs,
                "build_subdir": cfg.get("build_subdir"),
                "toolchain": cfg.get("toolchain") or "platformio",
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
    Run build for the given device/firmware. For PlatformIO: env required, pio run -e <env>, copy to artifacts.
    For ESP-IDF (toolchain idf): run scripts/lab-build.sh; no env. Optionally apply patch_paths; if clean, run clean first.
    Returns (ok: bool, path_or_error: str). path is relative to REPO_ROOT (artifact dir or firmware.bin).
    """
    if not BUILD_CONFIG or device_id not in BUILD_CONFIG or firmware_id not in BUILD_CONFIG[device_id]:
        return False, "Unknown device or firmware"
    cfg = BUILD_CONFIG[device_id][firmware_id]
    path = (cfg.get("path") or "").strip()
    toolchain = cfg.get("toolchain") or "platformio"
    envs = cfg.get("envs") or []

    # IDF path: run lab-build.sh (build in esp-idf-lab container), no env
    if toolchain == "idf":
        script = os.path.join(REPO_ROOT, "scripts", "lab-build.sh")
        if not os.path.isfile(script):
            return False, "scripts/lab-build.sh not found"
        try:
            r = subprocess.run(
                [script, device_id, firmware_id, ""],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            if r.returncode != 0:
                return False, (r.stderr or r.stdout or "IDF build failed")[:500]
            # Script writes to artifacts/<device>/<firmware>/<date>/
            version = datetime.now().strftime("%Y-%m-%d")
            artifact_dir = os.path.join(ARTIFACTS_DIR, device_id, firmware_id, version)
            if os.path.isdir(artifact_dir):
                fw_bin = os.path.join(artifact_dir, "firmware.bin")
                return True, os.path.relpath(fw_bin, REPO_ROOT) if os.path.isfile(fw_bin) else os.path.relpath(artifact_dir, REPO_ROOT)
            return True, os.path.relpath(os.path.join(ARTIFACTS_DIR, device_id, firmware_id), REPO_ROOT)
        except subprocess.TimeoutExpired:
            return False, "Build timed out"
        except Exception as e:
            return False, str(e)[:300]

    # PlatformIO path
    if env_name not in envs:
        env_name = (envs[0] if envs else "")
    if not env_name or env_name == "default":
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
                            if f.endswith(".bin") and f not in _FLASH_EXCLUDE_BIN:
                                p = os.path.join(full, f)
                                results.append({
                                    "path": os.path.relpath(p, REPO_ROOT),
                                    "name": f"{dev}/{fw}/{name}/{f}",
                                    "type": "artifact",
                                    "device": dev,
                                    "firmware": fw,
                                    "size": os.path.getsize(p) if os.path.isfile(p) else 0,
                                })
                    elif name.endswith(".bin") and name not in _FLASH_EXCLUDE_BIN:
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


def delete_artifact_or_backup(rel_path: str):
    """
    Delete a backup or artifact .bin file. rel_path is relative to REPO_ROOT (e.g. from list_artifacts_and_backups).
    Returns (success, error_message).
    """
    if not rel_path or not rel_path.strip():
        return False, "Path required"
    rel_path = rel_path.strip().lstrip("/")
    if not rel_path.lower().endswith(".bin"):
        return False, "Only .bin files under artifacts can be deleted"
    full = os.path.normpath(os.path.join(REPO_ROOT, rel_path))
    try:
        full = os.path.realpath(full)
        artifacts_real = os.path.realpath(ARTIFACTS_DIR)
    except OSError:
        return False, "Invalid path"
    if not full.startswith(artifacts_real + os.sep) and full != artifacts_real:
        return False, "Path must be under artifacts"
    if not os.path.isfile(full):
        return False, "File not found"
    try:
        os.remove(full)
        return True, None
    except OSError as e:
        return False, str(e)
