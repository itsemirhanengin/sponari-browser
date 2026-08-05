# The Patch Model

The entire Sponari delta is `patches/` — one `.patch` per upstream file,
applied to the Chromium working tree, **never committed inside `src/`**.
`src` HEAD always sits exactly on the pinned tag, so `git -C src diff` shows
precisely what Sponari changes.

## Naming

Upstream path with `/` → `-`:

```
chrome/app/theme/chromium/BRANDING  →  patches/chrome-app-theme-chromium-BRANDING.patch
```

The real target path is parsed from the patch's `diff --git` header; the
filename is just for humans. One file per patch keeps conflicts isolated
and reviewable.

## Lifecycle

```bash
# make a change
vim ../chromium/src/chrome/app/chromium_strings.grd
python3 scripts/export_patches.py        # regenerates patches/ from the delta
git add patches/ && git commit           # the patch is the artifact

# round-trip check (also what CI-of-the-future runs)
python3 scripts/reset_patches.py         # back to pristine tag
python3 scripts/apply_patches.py         # re-apply from patches/
python3 scripts/export_patches.py        # must be byte-identical
```

Rules:

- **Patches are for editing files that already exist upstream.** Whole new
  files go through the overlay instead — see below.
- **Binary assets** never travel as patches. Put them under
  `resources/branding/` and map them in `copy_manifest.json`'s `copies`;
  `apply_patches.py` copies them after the patch set.
- **Renames** are not supported by the one-patch-per-file model — express
  them as delete+add or avoid them.
- Patch state lives in `src/.sponari_patch_state.json` (auto-added to
  `src/.git/info/exclude`). `apply_patches.py` is idempotent thanks to it.

## The overlay: new files

`overlay/` mirrors the `src/` layout. Everything under it is copied into the
checkout by `apply_patches.py` and deleted again by `reset_patches.py`. The
copies stay *untracked* inside `src`, so `git -C <src> diff` keeps meaning
exactly "the patch set" and `export_patches.py` never sees them.

```bash
vim overlay/chrome/browser/ui/webui/sponari_settings/sponari_settings_ui.cc
python3 scripts/apply_patches.py --copies-only    # fast re-sync, no git apply
autoninja -C out/Dev chrome                       # in the Chromium checkout
```

Why not one patch per new file: `export_patches.py` reads `git diff HEAD`, so
new files would have to be `git add`-ed inside `src` — a scratch tree that
`sync.py` runs `git checkout -f` on. Worse, when `apply_patches.py` falls back
to `git apply --reject` the file lands untracked, drops out of `git diff HEAD`,
and the next `export_patches.py --prune` deletes its patch. The overlay has no
such failure mode, and it keeps the source reviewable as normal files.

Guard rails, all enforced by the scripts:

- Edit under `overlay/`, never in `src`. A copy that was hand-edited on the
  `src` side is **not** overwritten — apply fails with the file list, and
  `--clobber` discards those edits deliberately.
- An overlay file that would shadow a path existing upstream is rejected. New
  files only; use a patch to edit an upstream file.
- Files removed from `overlay/` are removed from `src` on the next apply, and
  emptied directories are pruned.
- If an overlay file gets `git add`-ed in `src`, `export_patches.py` refuses to
  run rather than letting it travel through both channels.
- `.git/info/exclude` gets a managed, per-file block so `git status` in `src`
  stays clean — per file, not per directory, so anything unexpected inside an
  overlay directory still shows up as untracked.

## Invariants

- User agent stays Chrome-compatible — never patch UA branding.
- `.grd` message IDs are never renamed; only string values change.
- `is_chrome_branded` stays `false`.

## When a patch grows too big

Brave's escape hatch is a `chromium_src/` override directory (whole-file
redefinitions wired into the GN include path). We deliberately don't have it
yet — if a patch becomes a rebase burden, that is the mechanism to adopt.
Same for real Sponari-owned source: if/when we grow our own C++, migrate to
the Brave model (our repo mounted at `src/sponari` via `.gclient`).
