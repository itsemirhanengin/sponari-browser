# Sponari

A Chromium-based browser. This repo does not contain Chromium's source — only
the delta: patches, branding, and the tooling that pins, rebases and rebuilds
Sponari on top of each Chromium stable release. Same model as Brave.

```
sponari-browser/   this repo: patches + scripts + automation
<chromium dir>/    full Chromium checkout, fetched locally, never committed
```

Cloning this repo is enough to reproduce the browser: fetch Chromium at the
version in `.chromium_version`, apply `patches/`, build.

## Getting started

```bash
python3 scripts/bootstrap.py --chromium-dir ~/chromium
# add depot_tools to PATH as instructed, then:
python3 scripts/sync.py          # clones full-history Chromium (~80GB)
python3 scripts/apply_patches.py
python3 scripts/build.py         # gn gen; prints the autoninja command
```

## Commands

| Command | Purpose |
|---|---|
| `scripts/apply_patches.py` | Apply `patches/` onto the checkout (3-way, idempotent) |
| `scripts/export_patches.py` | Regenerate `patches/` from edits made in `src/` |
| `scripts/reset_patches.py` | Return `src/` to the pristine pinned tag |
| `scripts/check_upstream.py` | Check for a newer Chromium stable (exit 10 = yes) |
| `scripts/upgrade.py` | Staged upgrade: `--prepare` / `--apply` / `--report` |
| `scripts/resolve_conflicts.py` | Resolve conflicted patches with headless Claude |
| `scripts/bootstrap.py --watcher` | Install the daily launchd upstream watcher |

## Docs

- `AGENTS.md` — rules and conventions for anyone (or anything) writing code here
- `docs/SETUP.md` — machine setup, first sync, first build
- `docs/PATCHES.md` — the patch model
- `docs/UPGRADE.md` — the Chromium upgrade runbook
