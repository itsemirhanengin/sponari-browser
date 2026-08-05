# Backlog

Current state: Phase 0-2 done. First build works — Sponari Browser.app runs,
About page and settings are rebranded, UA still reports Chrome. 7 patches in
the set. Repo is on GitHub (itsemirhanengin/sponari-browser).

## Next up

- [ ] Push the latest commits to GitHub (`git push origin main`).
- [ ] Install the upstream watcher: `python3 scripts/bootstrap.py --watcher`,
      then verify with `launchctl list | grep sponari`.
- [ ] Upgrade rehearsal before the first real Chromium upgrade: pin one
      stable back with `upgrade.py --prepare --version <prev> --allow-downgrade`,
      sync, `--apply`, force a synthetic conflict, run the full
      `resolve_conflicts.py` loop against the real checkout. Runbook:
      docs/UPGRADE.md.

## App identity

- [ ] Sponari app icon: design an .icns, drop it under
      resources/branding/icons/, map it in copy_manifest.json
      (target: chrome/app/theme/chromium/mac/app.icns). Binary asset —
      copy manifest, not a patch.
- [ ] Locale strings: only English is rebranded. Other locales (.xtb files)
      still say Chromium. Decide supported languages (tr first?) and extend
      the rebrand there.

## Product features

- [ ] First Sponari feature — parked by choice until the core felt solid.
      Design note: prefer the highest layer (WebUI first; see AGENTS.md).

## Infrastructure, later

- [ ] CI patch dry-run: extend .github/workflows/upstream-watch.yml with a
      sparse blobless clone of the new tag + `git apply --check` per patch,
      label the issue/PR "applies cleanly" vs "conflicts expected".
- [ ] About page shows "error checking for updates" — dev builds have no
      updater. Either hide the card via patch or (much later) build an
      update channel.
- [ ] Widevine DRM (Netflix, Spotify, some Udemy): short-term dev hack is
      enable_widevine + borrowing the CDM from an installed Chrome;
      the real path is a (free) Widevine license from Google + VMP-signed
      builds like Brave/Vivaldi. Decide only if/when distribution matters.
- [ ] Distribution build: is_official_build args, Developer ID signing,
      notarization, dmg packaging. Only when there's something to ship.
- [ ] Disk hygiene: `rm -rf ~/chromium/_bad_scm` (leftover from the first
      sync, a few GB).

## Explicitly not doing

- sponari:// scheme alias — cosmetic, deep plumbing, Brave did it years in.
- Aggressive rebrand of code identifiers/comments — patch burden, no user
  value.
- Touching the user agent — hard invariant, see AGENTS.md.
