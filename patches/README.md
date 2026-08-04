# patches/

The entire Sponari delta against pinned Chromium lives here — one `.patch`
per upstream file, named as the upstream path with `/` replaced by `-`
(e.g. `chrome/app/theme/chromium/BRANDING` → `chrome-app-theme-chromium-BRANDING.patch`).

Never hand-edit these files. Edit the file in the Chromium checkout and run
`scripts/export_patches.py`. See `docs/PATCHES.md`.

The first patches (the Sponari rebrand) are generated in Phase 2, once the
Chromium checkout exists.
