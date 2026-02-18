"""Inventory app config."""
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# When running in Docker, set REPO_ROOT to the mounted workspace (e.g. /workspace)
REPO_ROOT = os.environ.get("REPO_ROOT") or os.path.dirname(os.path.dirname(BASE_DIR))
INVENTORY_DIR = os.path.join(REPO_ROOT, "inventory")
DB_PATH = os.path.join(INVENTORY_DIR, "inventory.db")
ARTIFACTS_DIR = os.path.join(REPO_ROOT, "artifacts")
# Persistent device/serial logs for AI and troubleshooting (historical logs)
DEVICE_LOGS_DIR = os.path.join(ARTIFACTS_DIR, "device_logs")

# AI settings file (persisted in artifacts; env OPENAI_API_KEY overrides file)
AI_SETTINGS_PATH = os.path.join(ARTIFACTS_DIR, "ai_settings.json")

# Path settings (docker container, frontend, backend, database, MCP server) - persisted in artifacts
PATH_SETTINGS_PATH = os.path.join(ARTIFACTS_DIR, "path_settings.json")

# Optional: set OPENAI_API_KEY for AI (env takes precedence over file)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")


def _load_ai_settings_file():
    """Read AI settings from file. Returns dict with api_key, model, base_url (never expose api_key to clients)."""
    path = AI_SETTINGS_PATH
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_ai_settings(api_key=None, model=None, base_url=None):
    """Update and persist AI settings. Pass None for a key to leave unchanged; pass '' to clear."""
    os.makedirs(os.path.dirname(AI_SETTINGS_PATH), exist_ok=True)
    current = _load_ai_settings_file()
    if api_key is not None:
        current["api_key"] = (api_key or "").strip()
    if model is not None:
        current["model"] = (model or "gpt-4o-mini").strip() or "gpt-4o-mini"
    if base_url is not None:
        current["base_url"] = (base_url or "").strip()
    current.setdefault("model", "gpt-4o-mini")
    with open(AI_SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(current, f, indent=2)
    return current


def get_openai_api_key():
    """API key for OpenAI: env OPENAI_API_KEY overrides file."""
    return (OPENAI_API_KEY or "").strip() or (_load_ai_settings_file().get("api_key") or "").strip()


def get_openai_model():
    """Model name for chat (e.g. gpt-4o-mini)."""
    return _load_ai_settings_file().get("model") or "gpt-4o-mini"


def get_openai_base_url():
    """Optional base URL for API (e.g. for OpenAI-compatible proxies)."""
    return (_load_ai_settings_file().get("base_url") or "").strip()


def get_ai_settings_public():
    """Settings safe to expose to the UI: api_key_set (bool), model, base_url. Never the actual key."""
    return {
        "api_key_set": bool(get_openai_api_key()),
        "model": get_openai_model(),
        "base_url": get_openai_base_url(),
    }


def _load_path_settings_file():
    """Read path settings from file. Returns dict with docker_container, frontend_path, backend_path, database_path, mcp_server_path."""
    path = PATH_SETTINGS_PATH
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def get_path_settings_defaults():
    """Default path values (used when not set in file)."""
    mcp_default = os.path.join(REPO_ROOT, "mcp-server")
    if not os.path.isdir(mcp_default):
        mcp_default = REPO_ROOT
    return {
        "docker_container": "",
        "frontend_path": REPO_ROOT,
        "backend_path": BASE_DIR,
        "database_path": DB_PATH,
        "mcp_server_path": mcp_default,
    }


def get_path_settings():
    """Return path settings for UI: each key with effective value (default or override)."""
    defaults = get_path_settings_defaults()
    overrides = _load_path_settings_file()
    return {
        "docker_container": (overrides.get("docker_container") or "").strip() or defaults["docker_container"],
        "frontend_path": (overrides.get("frontend_path") or "").strip() or defaults["frontend_path"],
        "backend_path": (overrides.get("backend_path") or "").strip() or defaults["backend_path"],
        "database_path": (overrides.get("database_path") or "").strip() or defaults["database_path"],
        "mcp_server_path": (overrides.get("mcp_server_path") or "").strip() or defaults["mcp_server_path"],
    }


def save_path_settings(docker_container=None, frontend_path=None, backend_path=None, database_path=None, mcp_server_path=None):
    """Update and persist path settings. Pass None to leave unchanged."""
    os.makedirs(os.path.dirname(PATH_SETTINGS_PATH), exist_ok=True)
    current = _load_path_settings_file()
    if docker_container is not None:
        current["docker_container"] = (docker_container or "").strip()
    if frontend_path is not None:
        current["frontend_path"] = (frontend_path or "").strip()
    if backend_path is not None:
        current["backend_path"] = (backend_path or "").strip()
    if database_path is not None:
        current["database_path"] = (database_path or "").strip()
    if mcp_server_path is not None:
        current["mcp_server_path"] = (mcp_server_path or "").strip()
    with open(PATH_SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(current, f, indent=2)
    return get_path_settings()


def get_database_path():
    """Database path: override from path_settings if set, else default DB_PATH."""
    overrides = _load_path_settings_file()
    path = (overrides.get("database_path") or "").strip()
    return path or DB_PATH

# GitHub repos to check for firmware/OS updates (owner/repo)
FIRMWARE_REPOS_FOR_UPDATES = [
    {"owner": "meshtastic", "repo": "firmware", "name": "Meshtastic", "device": "t_beam_1w"},
    {"owner": "meshcore-dev", "repo": "MeshCore", "name": "MeshCore", "device": "t_beam_1w"},
    {"owner": "mintylinux", "repo": "Meshcore-T-beam-1W-Firmware", "name": "MeshCore T-Beam 1W", "device": "t_beam_1w"},
]

# Flash/backup: device_id -> esptool chip and flash params (for backup/restore/flash)
FLASH_DEVICES = {
    "t_beam_1w": {
        "chip": "esp32s3",
        "flash_size": "8MB",
        "flash_mode": "dio",
        "description": "LilyGO T-Beam 1W (ESP32-S3)",
    },
    "t_deck_plus": {
        "chip": "esp32s3",
        "flash_size": "16MB",
        "flash_mode": "dio",
        "description": "LilyGO T-Deck Plus",
    },
}

# Backups stored here (relative to REPO_ROOT); create if missing
BACKUPS_DIR = os.path.join(REPO_ROOT, "artifacts", "backups")

# Firmware targets for flash UI: filter artifacts by Meshtastic / MeshCore / Launcher / Bruce / Ghost / Marauder / Flipper (folder names under artifacts/<device>/)
FIRMWARE_TARGETS = ["meshtastic", "meshcore", "launcher", "bruce", "ghost", "marauder", "flipper_firmware", "unleashed", "roguemaster"]

# Project proposals (saved in container mount under REPO_ROOT)
PROJECT_PROPOSALS_DIR = os.path.join(REPO_ROOT, "artifacts", "project_proposals")

# Build config: device_id -> firmware_id -> { path (relative to REPO_ROOT), env (PlatformIO env) }
BUILD_CONFIG = {
    "t_beam_1w": {
        "meshcore": {
            "path": "devices/t_beam_1w/firmware/meshcore/repo",
            "envs": ["T_Beam_1W_SX1262_repeater", "T_Beam_1W_SX1262_room_server", "T_Beam_1W_SX1262_companion_radio_ble"],
        },
        "meshtastic": {
            "path": "devices/t_beam_1w/firmware/meshtastic/repo",
            "envs": ["tbeam-1w"],
        },
    },
}
