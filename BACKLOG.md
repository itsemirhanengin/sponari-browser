# Backlog

Headed for Linear. Once the issues are there, delete this file — a task list in
two places only diverges. What is kept here is deliberately only what has not
been done; design taste ("darken the shadow", "more corner radius") does not
belong in the repo, it changes every session. Invariants that a rebase can break
silently live in AGENTS.md instead.

Current state: 31 patches. Rebranded, Settings WebUI at `chrome://sponari-settings`
(Cmd+, points at it), and a reworked top chrome — Glass Frame on by default,
grayscale theme, ~70dip header, pill-less omnibox, avatar in the tab strip,
one drop shadow around the tab+toolbar silhouette. UA still reports Chrome.

## Next up

- [ ] Install the upstream watcher: `python3 scripts/bootstrap.py --watcher`,
      then verify with `launchctl list | grep sponari`.
- [ ] Upgrade rehearsal before the first real Chromium upgrade: pin one
      stable back with `upgrade.py --prepare --version <prev> --allow-downgrade`,
      sync, `--apply`, force a synthetic conflict, run the full
      `resolve_conflicts.py` loop against the real checkout. Runbook:
      docs/UPGRADE.md. **More urgent than it was** — the patch set went from 7
      to 31 and now touches files upstream edits constantly
      (`layout_constants.cc`, `toolbar_view.cc`, `location_bar_view.cc`,
      `tab_strip_region_view.cc`).

## Top chrome, unfinished

- [ ] Avatar theming on glass: `AvatarToolbarButton` is a `ToolbarButton` using
      `kColorToolbarButtonIcon`, which is frame-state-blind, but it now sits in
      the tab strip row over a translucent frame. Its neighbours
      (`TabStripControlButton`) subscribe to
      `RegisterPaintAsActiveChangedCallback` and swap between
      `kColorNewTabButtonCRForegroundFrameActive/Inactive`. Do the same, and
      give it `SetDefaultBackgroundColorId(kColorNewTabButtonBackgroundFrameActive)`
      as a scrim under Glass Frame. Do **not** try to reuse
      `UpdateButtonBorders()`: `ToolbarButton::UpdateColorsAndInsets` calls
      `SetBorder()` unconditionally and clobbers external borders.
- [ ] Shadow repaint lag: the silhouette shadow is painted by
      `BrowserFrameViewMac`, but nothing schedules a frame repaint when the
      active tab moves. Dragging a tab or switching tabs may leave the shadow a
      frame behind. Needs a `SchedulePaint()` hook off the tab strip.

## App identity

- [ ] Sponari app icon: design an .icns, drop it under
      resources/branding/icons/, map it in copy_manifest.json
      (target: chrome/app/theme/chromium/mac/app.icns). Binary asset —
      copy manifest's `copies`, not a patch.
- [ ] Locale strings: only English is rebranded. Other locales (.xtb files)
      still say Chromium. Decide supported languages (tr first?) and extend
      the rebrand there. Sponari Settings' own strings are inline TypeScript
      today and would need a .grd at the same time.

## Infrastructure, later

- [ ] CI patch dry-run: extend .github/workflows/upstream-watch.yml with a
      sparse blobless clone of the new tag + `git apply --check` per patch,
      label the issue/PR "applies cleanly" vs "conflicts expected". Worth more
      now that the set is 31 patches deep.
- [ ] Upstream tests we knowingly broke, for whenever tests start mattering:
      `horizontal_tab_strip_region_view_interactive_uitest.cc`,
      `browser_view_unittest.cc`, `tab_unittest.cc`, plus any pixel tests.
      Expected for a fork with changed layout constants.
- [ ] Widevine DRM (Netflix, Spotify, some Udemy): short-term dev hack is
      enable_widevine + borrowing the CDM from an installed Chrome;
      the real path is a (free) Widevine license from Google + VMP-signed
      builds like Brave/Vivaldi. Decide only if/when distribution matters.
- [ ] Distribution build: is_official_build args, Developer ID signing,
      notarization, dmg packaging. Only when there's something to ship.
- [ ] Disk hygiene: `rm -rf ~/chromium/_bad_scm` (leftover from the first
      sync, a few GB).

## Done since this file was written

- Overlay mechanism for Sponari-owned source files (`overlay/`, copy_manifest
  `trees`). New files no longer travel as patches.
- Settings WebUI at `chrome://sponari-settings`; `chrome::ShowSettings()` points
  at it while every deep link stays on `chrome://settings`. Sections render but
  hold no data yet — the Mojo `PageHandler` is still to come, and that is the
  next real feature, not a design tweak.
- About page's "error checking for updates" card: sidestepped rather than fixed.
  Sponari Settings has its own About section with no updater card.

## Explicitly not doing

- sponari:// scheme alias — cosmetic, deep plumbing, Brave did it years in.
- Aggressive rebrand of code identifiers/comments — patch burden, no user
  value.
- Touching the user agent — hard invariant, see AGENTS.md.
- A design backlog. Visual iteration happens live against a build; writing
  "make the shadow stronger" down has no shelf life.
