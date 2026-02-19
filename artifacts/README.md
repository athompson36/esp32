# Artifacts

Compiled firmware, backups, and runtime data. This directory is **gitignored** except this README.

## Layout convention

```
artifacts/
├── README.md                    # This file (tracked)
├── <device>/<firmware>/<version_or_date>/
│   ├── firmware.bin             # App partition
│   ├── firmware.factory.bin     # Full image (bootloader + partitions + app)
│   └── ...
├── backups/                     # Flash backups (.bin) from Backup/Flash UI
├── project_proposals/           # Project planning JSON (from AI planner)
├── ai_settings.json             # AI API key/model (from Settings)
└── path_settings.json           # Docker/path config (from Settings)
```

### Examples

```
artifacts/t_beam_1w/meshcore/20260215_143000/firmware.factory.bin
artifacts/t_beam_1w/meshtastic/20260216_091500/firmware.bin
artifacts/backups/backup_t_beam_1w_full_20260219_031000.bin
```

## Rules

- **Artifacts are never auto-deleted** (CONTEXT.md rule 5: "Storage is cheap. Reproducibility is priceless.").
- Builds write here via `scripts/lab-build.sh` or the inventory app Build tab.
- Backups write here via the inventory app Backup/Flash tab.
- To track versioned builds in git, remove the `artifacts/` line from `.gitignore`.
