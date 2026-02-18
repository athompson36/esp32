#!/usr/bin/env python3
"""
Install wizard: set up and configure the full Cyber-Lab software stack.

Run from repo root after cloning:
  python scripts/install_wizard.py
  python scripts/install_wizard.py --non-interactive   # accept defaults, no prompts

Steps:
  1. System checks (Python 3.9+, optional Node 18+, optional Docker)
  2. Python venv + install dependencies (inventory app, map tiles)
  3. Optional: build MCP server (npm install, npm run build)
  4. Create artifacts dirs and default config (path_settings, ai_settings)
  5. Build inventory database from YAML (inventory/scripts/build_db.py)
  6. Optional: build Docker images (platformio-lab, inventory app, MCP)
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

# Repo root: parent of scripts/
def _repo_root() -> Path:
    p = Path(__file__).resolve().parent
    while p.name and p.name != "scripts":
        p = p.parent
    return p.parent if p.name == "scripts" else Path.cwd()


def _log(msg: str, kind: str = "info") -> None:
    prefix = {"info": "[*]", "ok": "[OK]", "warn": "[!]", "err": "[X]"}.get(kind, "[*]")
    print(f"  {prefix} {msg}", flush=True)


def _run(cmd: list[str], cwd: Path | None = None, env: dict | None = None) -> tuple[bool, str]:
    cwd = cwd or _repo_root()
    env = env or os.environ.copy()
    try:
        r = subprocess.run(
            cmd,
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            timeout=300,
        )
        if r.returncode != 0:
            return False, r.stderr or r.stdout or f"exit {r.returncode}"
        return True, r.stdout or ""
    except subprocess.TimeoutExpired:
        return False, "Timeout"
    except Exception as e:
        return False, str(e)


def check_python() -> tuple[bool, str]:
    """Require Python 3.9+."""
    v = sys.version_info
    if v.major < 3 or (v.major == 3 and v.minor < 9):
        return False, f"Python 3.9+ required; got {v.major}.{v.minor}"
    return True, f"{v.major}.{v.minor}.{v.micro}"


def check_node(root: Path) -> tuple[bool, str]:
    """Optional Node 18+ for MCP server."""
    node = shutil.which("node")
    if not node:
        return False, "Node not found (optional; needed for MCP server)"
    try:
        r = subprocess.run(
            [node, "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if r.returncode != 0:
            return False, "node --version failed"
        ver = r.stdout.strip().removeprefix("v")
        major = int(ver.split(".")[0])
        if major < 18:
            return False, f"Node 18+ required; got {ver}"
        return True, ver
    except Exception as e:
        return False, str(e)


def check_docker() -> tuple[bool, str]:
    """Optional Docker for builds and optional containerized app/MCP."""
    docker = shutil.which("docker")
    if not docker:
        return False, "Docker not found (optional; needed for firmware builds and containerized app)"
    ok, out = _run([docker, "info"])
    if not ok:
        return False, "Docker not running or not usable"
    return True, "Docker available"


def _venv_exe(venv_dir: Path, name: str) -> Path:
    """Return path to python/pip in venv (bin on Unix, Scripts on Windows)."""
    if platform.system() == "Windows":
        return venv_dir / "Scripts" / f"{name}.exe"
    return venv_dir / "bin" / name


def ensure_venv(root: Path, non_interactive: bool) -> tuple[bool, Path]:
    """Create .venv if missing; install inventory + map deps. Returns (success, python_path)."""
    venv_dir = root / ".venv"
    py = _venv_exe(venv_dir, "python")
    if venv_dir.is_dir() and py.exists():
        _log(f"Using existing venv at {venv_dir}", "ok")
        return True, py
    _log("Creating virtual environment at .venv ...", "info")
    ok, err = _run([sys.executable, "-m", "venv", str(venv_dir)], cwd=root)
    if not ok:
        _log(f"Failed to create venv: {err}", "err")
        return False, Path()
    pip = _venv_exe(venv_dir, "pip")
    if not pip.exists():
        _log("pip not found in venv", "err")
        return False, Path()

    req = root / "inventory" / "app" / "requirements.txt"
    if not req.is_file():
        _log("inventory/app/requirements.txt not found", "err")
        return False, Path()
    ok, err = _run([str(pip), "install", "-r", str(req)], cwd=root)
    if not ok:
        _log(f"pip install inventory failed: {err}", "err")
        return False, Path()
    _log("Installed inventory app dependencies", "ok")

    # Map tiles: requests (and optional Pillow)
    ok, _ = _run([str(pip), "install", "requests"], cwd=root)
    if ok:
        _log("Installed map tile dependency (requests)", "ok")
    _run([str(pip), "install", "pillow"], cwd=root)  # optional

    return True, py


def build_mcp(root: Path) -> bool:
    """npm install && npm run build in mcp-server/."""
    mcp = root / "mcp-server"
    if not (mcp / "package.json").is_file():
        _log("mcp-server/package.json not found; skipping MCP build", "warn")
        return True
    npm = shutil.which("npm")
    if not npm:
        _log("npm not found; skipping MCP build", "warn")
        return True
    _log("Installing MCP server dependencies (npm install) ...", "info")
    ok, err = _run([npm, "install"], cwd=mcp)
    if not ok:
        _log(f"MCP npm install failed: {err}", "err")
        return False
    _log("Building MCP server (npm run build) ...", "info")
    ok, err = _run([npm, "run", "build"], cwd=mcp)
    if not ok:
        _log(f"MCP build failed: {err}", "err")
        return False
    _log("MCP server built successfully", "ok")
    return True


def ensure_artifacts_and_config(root: Path) -> bool:
    """Create artifacts dirs; write default path_settings and ai_settings if missing."""
    artifacts = root / "artifacts"
    dirs = [
        artifacts,
        artifacts / "backups",
        artifacts / "device_logs",
        artifacts / "project_proposals",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    _log("Artifacts directories ready", "ok")

    path_settings = artifacts / "path_settings.json"
    if not path_settings.is_file():
        default_db = str(root / "inventory" / "inventory.db")
        payload = {
            "docker_container": "",
            "frontend_path": str(root),
            "backend_path": str(root / "inventory" / "app"),
            "database_path": default_db,
            "mcp_server_path": str(root / "mcp-server"),
        }
        with open(path_settings, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        _log("Created default path_settings.json", "ok")
    else:
        _log("path_settings.json already exists", "ok")

    ai_settings = artifacts / "ai_settings.json"
    if not ai_settings.is_file():
        payload = {"model": "gpt-4o-mini", "base_url": ""}
        with open(ai_settings, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        _log("Created default ai_settings.json (add API key in web app)", "ok")
    else:
        _log("ai_settings.json already exists", "ok")

    return True


def build_inventory_db(root: Path, python_path: Path) -> bool:
    """Run inventory/scripts/build_db.py to create SQLite DB from YAML."""
    build_script = root / "inventory" / "scripts" / "build_db.py"
    if not build_script.is_file():
        _log("inventory/scripts/build_db.py not found", "err")
        return False
    py = str(python_path) if python_path else sys.executable
    _log("Building inventory database from YAML ...", "info")
    ok, err = _run([py, str(build_script)], cwd=root)
    if not ok:
        _log(f"build_db.py failed: {err}", "err")
        return False
    db_path = root / "inventory" / "inventory.db"
    if db_path.is_file():
        _log(f"Inventory database ready at {db_path}", "ok")
    else:
        _log("Database file not created (check YAML under inventory/items/)", "warn")
    return True


def build_docker_images(root: Path) -> bool:
    """Build platformio-lab, inventory app, and MCP images if Docker available."""
    ok, _ = check_docker()
    if not ok:
        _log("Skipping Docker builds (Docker not available)", "warn")
        return True

    # platformio-lab
    dockerfile = root / "docker" / "Dockerfile"
    if dockerfile.is_file():
        _log("Building platformio-lab image (may take several minutes) ...", "info")
        ok, err = _run(["docker", "build", "-t", "platformio-lab", "-f", str(dockerfile), "."], cwd=root)
        if not ok:
            _log(f"platformio-lab build failed: {err}", "err")
            return False
        _log("platformio-lab image built", "ok")
    else:
        _log("docker/Dockerfile not found; skipping platformio-lab", "warn")

    # inventory app
    compose_inv = root / "inventory" / "app" / "docker-compose.yml"
    if compose_inv.is_file():
        _log("Building inventory app image ...", "info")
        ok, err = _run(["docker", "compose", "-f", str(compose_inv), "build"], cwd=root)
        if not ok:
            _log(f"Inventory app image build failed: {err}", "err")
            return False
        _log("Inventory app image built", "ok")

    # MCP server
    compose_mcp = root / "mcp-server" / "docker-compose.yml"
    if compose_mcp.is_file():
        _log("Building MCP server image ...", "info")
        ok, err = _run(["docker", "compose", "-f", str(compose_mcp), "build"], cwd=root)
        if not ok:
            _log(f"MCP server image build failed: {err}", "err")
            return False
        _log("MCP server image built", "ok")

    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Install and configure the Cyber-Lab software stack (dependencies, venv, DB, optional Docker)."
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Accept defaults; do not prompt (e.g. for CI).",
    )
    parser.add_argument(
        "--skip-docker",
        action="store_true",
        help="Do not build Docker images even if Docker is available.",
    )
    parser.add_argument(
        "--skip-mcp",
        action="store_true",
        help="Do not build MCP server (Node/npm required otherwise).",
    )
    parser.add_argument(
        "--docker-only",
        action="store_true",
        help="Only build Docker images; skip venv, DB, and config.",
    )
    args = parser.parse_args()
    root = _repo_root()

    print("Cyber-Lab Install Wizard")
    print("=" * 50)
    print(f"Repo root: {root}")
    if Path.cwd() != root:
        _log(f"Current directory is {Path.cwd()}; operations use repo root.", "warn")
    print()

    # System checks
    _log("Checking system ...", "info")
    ok, msg = check_python()
    if not ok:
        _log(msg, "err")
        return 1
    _log(f"Python {msg}", "ok")

    node_ok, node_msg = check_node(root)
    if node_ok:
        _log(f"Node {node_msg}", "ok")
    else:
        _log(node_msg, "warn")

    docker_ok, docker_msg = check_docker()
    if docker_ok:
        _log(docker_msg, "ok")
    else:
        _log(docker_msg, "warn")
    print()

    if args.docker_only:
        if not docker_ok:
            _log("Docker not available; cannot run --docker-only", "err")
            return 1
        return 0 if build_docker_images(root) else 1

    # Venv + Python deps
    _log("Step 1: Python environment", "info")
    ok, py_path = ensure_venv(root, args.non_interactive)
    if not ok:
        return 1
    print()

    # MCP
    if not args.skip_mcp:
        _log("Step 2: MCP server (optional)", "info")
        build_mcp(root)
    else:
        _log("Step 2: MCP server skipped (--skip-mcp)", "info")
    print()

    # Artifacts and config
    _log("Step 3: Artifacts and config", "info")
    ensure_artifacts_and_config(root)
    print()

    # DB
    _log("Step 4: Inventory database", "info")
    if not build_inventory_db(root, py_path):
        return 1
    print()

    # Docker
    if not args.skip_docker and docker_ok:
        _log("Step 5: Docker images (optional)", "info")
        if not args.non_interactive:
            try:
                r = input("  Build Docker images? [y/N]: ").strip().lower()
                do_build = r in ("y", "yes")
            except EOFError:
                do_build = False
        else:
            do_build = True
        if do_build:
            if not build_docker_images(root):
                return 1
        else:
            _log("Skipped. Run later: ./scripts/rebuild-containers.sh", "info")
    else:
        _log("Step 5: Docker images skipped", "info")
    print()

    print("=" * 50)
    print("Install complete.")
    print()
    print("Next steps:")
    print("  1. Activate the virtual environment:")
    if platform.system() == "Windows":
        print("       .venv\\Scripts\\activate")
    else:
        print("       source .venv/bin/activate")
    print("  2. Start the web app (from repo root):")
    print("       python inventory/app/app.py")
    print("  3. Open http://127.0.0.1:5000 in your browser.")
    print("  4. In the app: set AI API key (AI settings) and paths (Paths) if needed.")
    print("  5. For firmware builds: ensure Docker is running and use Backup/Flash tab.")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
