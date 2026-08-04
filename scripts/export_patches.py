#!/usr/bin/env python3
"""Regenerate patches/ from the working tree's diff against HEAD.

HEAD must sit on the pinned tag. New files need `git add` in src first
(git diff HEAD only sees tracked content). Binary changes are rejected —
those go through resources/branding/ + copy_manifest.json.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import common, patchset


def head_matches_pin(src, pin):
    tag = common.git(["rev-parse", "-q", "--verify", "refs/tags/%s^{commit}" % pin],
                     cwd=src, check=False)
    if tag.returncode != 0:
        return False, "tag %s not found in checkout" % pin
    head = common.git(["rev-parse", "HEAD"], cwd=src).stdout.strip()
    if tag.stdout.strip() != head:
        return False, "HEAD is not on refs/tags/%s" % pin
    return True, ""


def modified_files(src, scope):
    cmd = ["diff", "--numstat", "HEAD"]
    if scope:
        cmd += ["--"] + scope
    out = common.git(cmd, cwd=src).stdout
    text_paths, binary_paths, renames = [], [], []
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        added, deleted, path = parts
        if " => " in path:
            renames.append(path)
            continue
        if added == "-" and deleted == "-":
            binary_paths.append(path)
        else:
            text_paths.append(path)
    return text_paths, binary_paths, renames


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--only", action="append", metavar="UPSTREAM_PATH",
                        help="export only this upstream file (repeatable)")
    parser.add_argument("--prune", action="store_true",
                        help="delete patch files whose upstream file is no longer modified")
    parser.add_argument("--no-verify", action="store_true",
                        help="skip the HEAD==pinned-tag check (use with care)")
    args = parser.parse_args()

    src = common.require_src()
    pin = common.read_pin()

    if not args.no_verify:
        ok, why = head_matches_pin(src, pin)
        if not ok:
            common.die("%s — refusing to export (run scripts/sync.py, or --no-verify "
                       "if you know what you are doing)" % why)

    text_paths, binary_paths, renames = modified_files(src, args.only)

    common.PATCHES_DIR.mkdir(parents=True, exist_ok=True)
    written = []
    for path in text_paths:
        diff = common.git(["diff", "--full-index", "HEAD", "--", path], cwd=src).stdout
        if not diff.strip():
            continue
        patch_file = common.PATCHES_DIR / patchset.patch_name_for(path)
        patch_file.write_text(diff)
        written.append(patch_file.name)

    if args.prune and not args.only:
        keep = {patchset.patch_name_for(p) for p in text_paths}
        for patch_file in patchset.list_patches():
            if patch_file.name not in keep:
                patch_file.unlink()
                common.info("pruned %s" % patch_file.name)

    for name in written:
        print("  wrote patches/%s" % name)
    if renames:
        common.warn("renames are not supported by the one-patch-per-file model, "
                    "skipped: %s" % ", ".join(renames))
    if binary_paths:
        common.die("binary change(s) detected: %s\n"
                   "  Patches cannot carry binaries. Put the asset under "
                   "resources/branding/ and map it in copy_manifest.json."
                   % ", ".join(binary_paths))
    if not written:
        common.info("working tree has no exportable delta against %s" % pin)
    else:
        common.info("exported %d patch(es)" % len(written))


if __name__ == "__main__":
    main()
