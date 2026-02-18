"""
Debug tab: live serial monitor (device logs), maintenance and troubleshooting tools.
Provides context for the AI: connected device logs, historical logs, and live device status.
"""
import os
import subprocess
import threading
import time
from collections import deque
from datetime import datetime, timezone

from flash_ops import detect_chip_on_port, list_serial_ports

# Serial monitor: one port at a time, ring buffer of last N lines
SERIAL_BUFFER_MAX_LINES = 500
_serial_buffer = deque(maxlen=SERIAL_BUFFER_MAX_LINES)
_serial_lock = threading.Lock()
_serial_stop = threading.Event()
_serial_thread = None
_serial_port = None
_serial_reader = None

# Persistent device logs (historical) for AI and troubleshooting
_historical_log_max_lines = 500
_log_file_lock = threading.Lock()


def _device_logs_path():
    """Path to persistent serial log file (artifacts/device_logs/serial.log)."""
    try:
        from config import DEVICE_LOGS_DIR
        os.makedirs(DEVICE_LOGS_DIR, exist_ok=True)
        return os.path.join(DEVICE_LOGS_DIR, "serial.log")
    except Exception:
        return None


def _append_to_persistent_log(port: str, line: str) -> None:
    """Append a single line with timestamp to persistent device log (thread-safe)."""
    path = _device_logs_path()
    if not path or not line or not line.strip():
        return
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with _log_file_lock:
        try:
            with open(path, "a", encoding="utf-8", errors="replace") as f:
                f.write(f"{ts} [{port}] {line}\n")
        except OSError:
            pass


def get_historical_log(max_lines: int = 150) -> str:
    """Return last max_lines lines from persistent device log for AI. Empty if no log file."""
    path = _device_logs_path()
    if not path or not os.path.isfile(path):
        return ""
    with _log_file_lock:
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
        except OSError:
            return ""
    lines = [ln.rstrip("\n") for ln in lines if ln.strip()]
    tail = lines[-max_lines:] if len(lines) > max_lines else lines
    return "\n".join(tail) if tail else ""


def _serial_read_loop(port: str, baud: int = 115200):
    """Background thread: read from serial port and append lines to buffer and persistent log."""
    global _serial_reader
    try:
        import serial
        _serial_reader = serial.Serial(port, baud, timeout=0.5)
    except Exception as e:
        with _serial_lock:
            _serial_buffer.append(f"[Serial open error] {port}: {e}")
        _append_to_persistent_log(port, f"[Serial open error] {e}")
        return
    line_buf = ""
    try:
        while not _serial_stop.is_set():
            try:
                chunk = _serial_reader.read(_serial_reader.in_waiting or 1)
                if chunk:
                    line_buf += chunk.decode("utf-8", errors="replace")
                    while "\n" in line_buf or "\r" in line_buf:
                        line = line_buf.split("\n")[0].split("\r")[0]
                        line_buf = line_buf[line_buf.index("\n") + 1:] if "\n" in line_buf else line_buf[line_buf.index("\r") + 1:]
                        line = line.strip()
                        if line:
                            with _serial_lock:
                                _serial_buffer.append(line)
                            _append_to_persistent_log(port, line)
                else:
                    if line_buf.strip():
                        with _serial_lock:
                            _serial_buffer.append(line_buf.strip())
                        _append_to_persistent_log(port, line_buf.strip())
                        line_buf = ""
                    time.sleep(0.05)
            except Exception as e:
                with _serial_lock:
                    _serial_buffer.append(f"[Read error] {e}")
                _append_to_persistent_log(port, f"[Read error] {e}")
                break
    finally:
        try:
            _serial_reader.close()
        except Exception:
            pass
        _serial_reader = None


def serial_start(port: str, baud: int = 115200) -> tuple[bool, str]:
    """Start serial monitor on port. Returns (success, message)."""
    global _serial_thread, _serial_port, _serial_stop
    serial_stop()
    _serial_stop.clear()
    if not port or not port.strip():
        return False, "No port specified"
    port = port.strip()
    with _serial_lock:
        _serial_buffer.clear()
    _serial_port = port
    _serial_stop.clear()
    try:
        _serial_thread = threading.Thread(target=_serial_read_loop, args=(port, baud), daemon=True)
        _serial_thread.start()
        return True, f"Listening on {port}"
    except Exception as e:
        return False, str(e)


def serial_stop() -> None:
    """Stop serial monitor and clear buffer."""
    global _serial_thread, _serial_port
    _serial_stop.set()
    if _serial_thread and _serial_thread.is_alive():
        _serial_thread.join(timeout=2.0)
    _serial_thread = None
    _serial_port = None


def serial_get_buffer() -> tuple[list[str], str | None]:
    """Return (list of lines, active_port or None)."""
    with _serial_lock:
        lines = list(_serial_buffer)
    return lines, _serial_port


def serial_is_active() -> bool:
    return _serial_port is not None and _serial_thread is not None and _serial_thread.is_alive()


def run_esptool_version() -> tuple[bool, str]:
    """Run esptool --version. Returns (success, output or error)."""
    for cmd in ("esptool", "esptool.py"):
        try:
            out = subprocess.run(
                [cmd, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            text = (out.stdout or "").strip() or (out.stderr or "").strip()
            return out.returncode == 0, text or cmd
        except FileNotFoundError:
            continue
        except Exception as e:
            return False, str(e)
    return False, "esptool not found (pip install esptool)"


def run_health_checks() -> dict:
    """Run maintenance checks. Returns { checks: [], problems: [], suggestions: [] }."""
    checks = []
    problems = []
    suggestions = []

    # Esptool
    ok_esptool, msg = run_esptool_version()
    checks.append({"name": "esptool", "ok": ok_esptool, "message": msg[:200]})
    if not ok_esptool:
        problems.append("esptool not installed or not in PATH")
        suggestions.append("Install esptool: pip install esptool")

    # Ports
    try:
        ports = list_serial_ports()
        count = len(ports)
        checks.append({"name": "serial_ports", "ok": True, "message": f"{count} port(s) found"})
        if count == 0:
            problems.append("No serial ports detected")
            suggestions.append("Connect a device via USB and ensure the correct driver is installed (e.g. CP210x, CH340)")
    except Exception as e:
        checks.append({"name": "serial_ports", "ok": False, "message": str(e)[:200]})
        problems.append("Failed to list serial ports")
        suggestions.append("Install pyserial: pip install pyserial")

    # Chip detection on first port (optional; only report as problem if esptool is available)
    try:
        ports = list_serial_ports()
        if ports:
            port = (ports[0].get("port") or ports[0].get("description") or "").strip()
            if port:
                chip, err = detect_chip_on_port(port, timeout=3)
                if chip:
                    checks.append({"name": "chip_detect", "ok": True, "message": f"{port}: {chip}"})
                else:
                    checks.append({"name": "chip_detect", "ok": False, "message": f"{port}: {err or 'unknown'}"})
                    if ok_esptool and err and "not found" not in err.lower():
                        problems.append(f"Chip detection failed on {port}: {err}")
                        suggestions.append("Connect an ESP32 in bootloader mode (hold BOOT, press RESET) or try another USB port/cable")
    except Exception as e:
        checks.append({"name": "chip_detect", "ok": False, "message": str(e)[:200]})

    # Database
    try:
        from config import get_database_path
        db_path = get_database_path()
        exists = os.path.isfile(db_path)
        checks.append({"name": "database", "ok": exists, "message": f"{'Found' if exists else 'Missing'}: {db_path}"})
        if not exists:
            problems.append("Inventory database not found")
            suggestions.append("Run build_db to generate inventory.db from YAML catalog")
    except Exception as e:
        checks.append({"name": "database", "ok": False, "message": str(e)[:200]})

    return {"checks": checks, "problems": problems, "suggestions": suggestions}


def get_debug_context() -> dict:
    """Build context for AI: live serial tail, historical logs, ports, esptool, health (live status)."""
    lines, active_port = serial_get_buffer()
    serial_tail = "\n".join(lines[-80:]) if lines else ""
    historical_log = get_historical_log(max_lines=150)
    ok_esptool, msg_esptool = run_esptool_version()
    health = run_health_checks()
    try:
        ports = list_serial_ports()
        port_names = [p.get("port") or p.get("description") or "?" for p in ports[:5]]
        ports_summary = f"{len(ports)} port(s): " + ", ".join(port_names)
    except Exception:
        ports_summary = "Failed to list ports"
    live_status = {
        "serial_active": serial_is_active(),
        "serial_port": active_port,
        "ports_summary": ports_summary,
        "esptool_ok": ok_esptool,
        "esptool_message": (msg_esptool or "")[:150],
        "health_problems": health["problems"],
        "health_suggestions": health["suggestions"],
    }
    return {
        "serial_active": serial_is_active(),
        "serial_port": active_port,
        "serial_tail": serial_tail,
        "historical_log": historical_log,
        "ports_summary": ports_summary,
        "esptool_ok": ok_esptool,
        "esptool_message": msg_esptool[:150],
        "health_problems": health["problems"],
        "health_suggestions": health["suggestions"],
        "health_checks": health["checks"],
        "live_status": live_status,
    }
