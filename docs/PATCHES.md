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

- **New files** must be `git add`-ed inside `src/` before export (git diff
  HEAD only sees tracked content).
- **Binary assets** never travel as patches. Put them under
  `resources/branding/` and map them in `copy_manifest.json`;
  `apply_patches.py` copies them after the patch set.
- **Renames** are not supported by the one-patch-per-file model — express
  them as delete+add or avoid them.
- Patch state lives in `src/.sponari_patch_state.json` (auto-added to
  `src/.git/info/exclude`). `apply_patches.py` is idempotent thanks to it.

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
