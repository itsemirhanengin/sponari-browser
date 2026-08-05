#!/usr/bin/env python3
"""Apply the patch set onto the Chromium working tree with git apply --3way.

Per-patch outcome is applied, conflict (markers left in the file) or failed
(falls back to --reject so .rej hunks are left for the resolver). Reruns are
idempotent via the state file. The overlay (whole new files declared in
copy_manifest.json) is synced after the patches.
"""
import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import common, patchset


def apply_one(src, patch):
    proc = common.git(["apply", "--3way", str(patch)], cwd=src, check=False)
    if proc.returncode == 0:
        return "applied", ""
    stderr = (proc.stderr or "").strip()
    if "with conflicts" in stderr:
        return "conflict", stderr
    # Couldn't apply at all — drop .rej files for the resolver to work with.
    common.git(["apply", "--reject", str(patch)], cwd=src, check=False)
    return "failed", stderr


def sync_overlay(src, state, clobber=False):
    """Copy manifest files and trees into src. -> (written, removed, blocked).

    Content-compared before writing, so an unchanged overlay costs nothing and
    does not retrigger a rebuild. Writes use copyfile+copymode rather than
    copy2: copy2 would carry the repo file's mtime into src, where a genuinely
    changed file can end up older than the artifacts in out/ and get skipped by
    ninja/siso — a stale binary that looks like the edit did nothing.
    """
    plan = patchset.overlay_plan(src)
    previous = patchset.copied_digests(state)

    written, blocked = [], []
    recorded = {}
    for dest, source in sorted(plan.items()):
        digest = patchset.sha256_bytes(source.read_bytes())
        full = src / dest
        if full.exists():
            current = patchset.sha256_of(full)
            if current == digest:
                recorded[dest] = digest
                continue
            # Edited inside src/ since we put it there — don't silently lose it.
            edited_in_src = (dest in previous and previous[dest] is not None
                             and current != previous[dest])
            if edited_in_src and not clobber:
                blocked.append(dest)
                recorded[dest] = previous[dest]
                continue
        full.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, full)
        shutil.copymode(source, full)
        written.append(dest)
        recorded[dest] = digest

    # Renamed or deleted in the repo — drop the stale copy in src. A dest that
    # turns out to be tracked upstream is restored rather than unlinked, so a
    # bad manifest entry can never leave a hole in the Chromium tree.
    removed = sorted(set(previous) - set(plan))
    for dest in removed:
        full = src / dest
        tracked = common.git(["cat-file", "-e", "HEAD:%s" % dest],
                             cwd=src, check=False).returncode == 0
        if tracked:
            common.git(["checkout", "-q", "HEAD", "--", dest], cwd=src, check=False)
            common.warn("overlay had shadowed the upstream file %s — restored" % dest)
            continue
        if full.exists():
            full.unlink()
        patchset.prune_empty_dirs(src, full.parent)

    state["copied"] = recorded
    state.pop("binaries", None)
    return written, removed, blocked


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--force", action="store_true",
                        help="re-apply even if state says already applied")
    parser.add_argument("--only", action="append", metavar="PATCH_FILENAME",
                        help="only apply this patch file (repeatable)")
    parser.add_argument("--copies-only", action="store_true",
                        help="skip the patch set, only re-sync the overlay "
                             "(the inner loop while developing overlay/ code)")
    parser.add_argument("--clobber", action="store_true",
                        help="overwrite overlay files that were hand-edited in src/")
    args = parser.parse_args()

    src = common.require_src()
    pin = common.read_pin()
    state = patchset.load_state(src)
    same_version = state.get("chromium_version") == pin

    patches = [] if args.copies_only else patchset.list_patches()
    if args.only:
        wanted = set(args.only)
        patches = [p for p in patches if p.name in wanted]
        missing = wanted - {p.name for p in patches}
        if missing:
            common.die("patch file(s) not found: %s" % ", ".join(sorted(missing)))

    results = []
    bad = []
    for patch in patches:
        digest = patchset.sha256_of(patch)
        entry = state["patches"].get(patch.name, {})
        if (not args.force and same_version
                and entry.get("sha256") == digest
                and entry.get("status") == "applied"):
            results.append((patch.name, "skipped (already applied)"))
            continue
        status, error = apply_one(src, patch)
        state["patches"][patch.name] = {
            "sha256": digest,
            "target": patchset.target_path_of(patch),
            "status": status,
            "error": error[-2000:] if error else None,
        }
        results.append((patch.name, status.upper() if status != "applied" else "applied"))
        if status != "applied":
            bad.append(patch.name)

    if not args.copies_only:
        state["chromium_version"] = pin
    written, removed, blocked = sync_overlay(src, state, clobber=args.clobber)
    patchset.save_state(src, state)

    if results:
        width = max(len(name) for name, _ in results)
        for name, status in results:
            print("  %-*s  %s" % (width, name, status))
    elif not args.copies_only:
        common.info("no patches in patches/")
    if written or removed:
        common.info("overlay: %d file(s) written, %d removed" % (len(written), len(removed)))
    if blocked:
        common.die("overlay file(s) were edited inside src/ and would be lost:\n  %s\n"
                   "  Edit them under overlay/ in the Sponari repo instead, or "
                   "re-run with --clobber to discard the src-side edits."
                   % "\n  ".join(blocked))
    if bad:
        common.info("%d patch(es) did NOT apply cleanly — see docs/UPGRADE.md "
                    "(conflict markers / .rej files left in the tree)" % len(bad))
        sys.exit(1)
    if args.copies_only:
        common.info("overlay in sync")
    else:
        common.info("patch set applied against chromium %s" % pin)


if __name__ == "__main__":
    main()
