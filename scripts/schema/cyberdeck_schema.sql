-- Cyberdeck Manager — Database Schema
-- Multi-user device/firmware/map/flash/hardware lifecycle
-- SQLite-compatible (use INTEGER for bool, TEXT for JSON where needed)

-- Users & RBAC
CREATE TABLE IF NOT EXISTS users (
  id TEXT PRIMARY KEY,
  username TEXT UNIQUE NOT NULL,
  password_hash TEXT,
  role TEXT NOT NULL DEFAULT 'viewer',  -- admin, standard, viewer
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

-- Device registry (synced with registry/devices/*.json)
CREATE TABLE IF NOT EXISTS devices (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  mcu TEXT,
  radios TEXT,  -- JSON array
  display TEXT,
  battery TEXT,
  storage TEXT,
  flash_methods TEXT,  -- JSON: usb_direct, sd_launcher
  compatible_firmware TEXT,  -- JSON array
  capability_json TEXT,  -- full capability matrix
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

-- Firmware registry (from GitHub + platformio.ini)
CREATE TABLE IF NOT EXISTS firmware (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  repo_owner TEXT,
  repo_name TEXT,
  firmware_type TEXT,  -- meshtastic, meshcore, launcher, bruce, ghost, custom
  supported_devices TEXT,  -- JSON array of device_id
  build_targets TEXT,  -- JSON
  latest_release_tag TEXT,
  latest_release_at TEXT,
  flash_method TEXT,  -- usb_direct, sd_launcher
  partition_scheme TEXT,
  launcher_compatible INTEGER DEFAULT 0,
  metadata_json TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

-- Custom forks per device
CREATE TABLE IF NOT EXISTS forks (
  id TEXT PRIMARY KEY,
  device_id TEXT NOT NULL REFERENCES devices(id),
  fork_name TEXT NOT NULL,
  upstream_ref TEXT,
  patch_notes TEXT,
  build_flags TEXT,
  path TEXT,  -- registry/forks/{device_id}/{fork_name}
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(device_id, fork_name)
);

-- Flash history (audit & fleet)
CREATE TABLE IF NOT EXISTS flash_history (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id TEXT REFERENCES users(id),
  device_id TEXT NOT NULL REFERENCES devices(id),
  firmware_id TEXT REFERENCES firmware(id),
  flash_method TEXT NOT NULL,  -- usb_direct, sd_launcher
  port TEXT,
  success INTEGER NOT NULL,
  message TEXT,
  created_at TEXT NOT NULL
);

-- Map builds (region, zoom, tile count, output path)
CREATE TABLE IF NOT EXISTS map_builds (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id TEXT REFERENCES users(id),
  region_slug TEXT NOT NULL,
  zoom_min INTEGER NOT NULL,
  zoom_max INTEGER NOT NULL,
  tile_count INTEGER NOT NULL,
  estimated_gb REAL,
  output_path TEXT,
  sd_valid INTEGER DEFAULT 0,
  created_at TEXT NOT NULL
);

-- RF presets (USA, EU, custom)
CREATE TABLE IF NOT EXISTS rf_presets (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  region TEXT NOT NULL,
  allowed_bands TEXT,  -- JSON
  tx_power_limits TEXT,  -- JSON
  channel_spacing TEXT,
  legal_warning TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

-- Hardware snapshots (fleet firmware state per device instance)
CREATE TABLE IF NOT EXISTS hardware_snapshots (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id TEXT REFERENCES users(id),
  device_id TEXT REFERENCES devices(id),
  serial_or_uid TEXT,
  mcu_version TEXT,
  radio_version TEXT,
  bootloader_version TEXT,
  app_firmware_version TEXT,
  sd_firmware_version TEXT,
  can_version TEXT,
  secure_element TEXT,
  raw_json TEXT,
  created_at TEXT NOT NULL
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_flash_history_device ON flash_history(device_id);
CREATE INDEX IF NOT EXISTS idx_flash_history_user ON flash_history(user_id);
CREATE INDEX IF NOT EXISTS idx_flash_history_created ON flash_history(created_at);
CREATE INDEX IF NOT EXISTS idx_hardware_snapshots_device ON hardware_snapshots(device_id);
CREATE INDEX IF NOT EXISTS idx_hardware_snapshots_user ON hardware_snapshots(user_id);
CREATE INDEX IF NOT EXISTS idx_forks_device ON forks(device_id);
