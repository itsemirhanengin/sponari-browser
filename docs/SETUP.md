# Setup

## Prerequisites

- macOS on Apple Silicon, Xcode installed (`xcode-select -p` must work)
- ~200GB free disk: ~20GB checkout + ~60GB git history + 60–100GB build output
- The first sync and the first build each take hours; plan around that

## 1. Bootstrap (fast)

```bash
python3 scripts/bootstrap.py --chromium-dir ~/chromium
```

`--chromium-dir` picks where the ~200GB checkout lives (recommended: a global
spot like `~/chromium`, not inside your projects folder). The choice is
recorded in the machine-local, gitignored `.chromium_dir` file — every script
reads it, including launchd/CI contexts that never source `.zshrc`. Omit the
flag to default to `../chromium` next to this repo.

Installs depot_tools to `~/depot_tools` if needed and writes
`../chromium/.gclient` from `.gclient.template`. Then add to `~/.zshrc`:

```bash
export PATH="$HOME/depot_tools:$PATH"
```

## 2. First sync (hours — run it yourself, leave it unattended)

```bash
python3 scripts/sync.py
```

First run clones Chromium **with full history** and syncs all DEPS
(~240 repos). Then it checks out the tag pinned in `.chromium_version` and
runs `gclient sync -D` to align dependencies to that exact release.

### Why full history (not `fetch --no-history`)?

The whole update mechanism rests on `git apply --3way`, which needs the
pre-image blobs referenced by each patch to exist in the object database.
On a shallow clone those blobs are frequently missing and 3-way degrades to
hard failure. The AI conflict resolver also needs
`git diff <old_tag>..<new_tag>` context. If you ever inherit a shallow
checkout, repair it with `git fetch --unshallow` (hours).

## 3. Apply patches + build

```bash
python3 scripts/apply_patches.py
python3 scripts/build.py            # writes args.gn + runs gn gen
cd ../chromium/src && autoninja -C out/Dev chrome   # 4-8h first time
open out/Dev/Sponari.app
```

Build args live in `scripts/gn/dev-mac-arm64.gn` (component build, no
symbols — incremental rebuilds after a patch edit take minutes).

If `gn gen` complains about the macOS SDK version, override in
`out/Dev/args.gn` (e.g. `mac_sdk_min = "..."`) — Xcode releases sometimes
run ahead of what the pinned Chromium expects.

Xcode 26+ doesn't ship the Metal shader compiler by default; the ANGLE build
step fails with "cannot execute tool 'metal'". Fix once with:

```bash
xcodebuild -downloadComponent MetalToolchain
```

then rerun autoninja — ninja resumes where it stopped.

## Checkout location resolution

Every script resolves the Chromium src dir with this precedence:

1. `SPONARI_CHROMIUM_DIR` env var (ad-hoc override)
2. `.chromium_dir` file (written by `bootstrap.py --chromium-dir`)
3. `../chromium/src` next to this repo (default)
