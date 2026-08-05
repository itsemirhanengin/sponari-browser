# overlay/

Whole new files that Sponari adds to the Chromium tree. The directory mirrors
the `src/` layout exactly, so `overlay/chrome/browser/ui/webui/foo/bar.cc`
lands at `<src>/chrome/browser/ui/webui/foo/bar.cc`.

These are **not** patches. `scripts/apply_patches.py` copies them in after the
patch set and `scripts/reset_patches.py` deletes them again. They stay
untracked inside `src`, so `git -C <src> diff` keeps meaning exactly "the patch
set" and `export_patches.py` never sees them.

Edit files **here**, never in `src` — `apply_patches.py` refuses to overwrite a
copy that was hand-edited on the other side (pass `--clobber` to discard those
edits deliberately).

Inner loop while working on overlay code:

    python3 scripts/apply_patches.py --copies-only
    autoninja -C out/Dev chrome    # in the Chromium checkout

Only edits to files that already exist upstream go through `patches/`.
`*.md` files here are excluded from the copy (see `copy_manifest.json`), so
this README never reaches the Chromium tree.
