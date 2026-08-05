#!/usr/bin/env python3
"""Put the Chromium working tree back on the pristine pinned tag.

Only touches paths the patch model knows about (patch targets, copied
binaries, their .rej/.orig leftovers) — never a blanket `git clean`, so out/
and DEPS-managed directories survive. --hard additionally runs
`git reset --hard` to the tag for trees too broken for the scoped path.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import common, patchset


def known_paths(state):
    paths = set()
    for entry in state.get("patches", {}).values():
        if entry.get("target"):
            paths.add(entry["target"])
    for patch_file in patchset.list_patches():
        target = patchset.target_path_of(patch_file)
        if target:
            paths.add(target)
    # The manifest is authoritative for what should be there now; the state
    # additionally catches overlay files renamed or deleted in the repo since
    # the last apply.
    paths.update(patchset.overlay_plan())
    paths.update(patchset.copied_paths(state))
    return sorted(paths)


def restore_path(src, path):
    common.git(["reset", "-q", "HEAD", "--", path], cwd=src, check=False)
    exists_at_head = common.git(["cat-file", "-e", "HEAD:%s" % path],
                                cwd=src, check=False).returncode == 0
    full = src / path
    if exists_at_head:
        common.git(["checkout", "-q", "--", path], cwd=src, check=False)
    elif full.exists():
        full.unlink()
    for suffix in (".rej", ".orig"):
        dropping = src / (path + suffix)
        if dropping.exists():
            dropping.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--hard", action="store_true",
                        help="git reset --hard to the pinned tag first")
    args = parser.parse_args()

    src = common.require_src()
    pin = common.read_pin()
    state = patchset.load_state(src)
    paths = known_paths(state)

    if args.hard:
        tag = common.git(["rev-parse", "-q", "--verify", "refs/tags/%s^{commit}" % pin],
                         cwd=src, check=False)
        if tag.returncode != 0:
            common.die("tag %s not present in checkout — run scripts/sync.py" % pin)
        common.git(["reset", "--hard", "refs/tags/%s" % pin], cwd=src, capture=False)

    overlay_dirs = patchset.overlay_roots(src, paths)
    for path in paths:
        restore_path(src, path)
        patchset.prune_empty_dirs(src, (src / path).parent)

    # Drop the managed ignore block *before* the status check below, otherwise
    # a failed overlay cleanup would stay invisible.
    patchset.ensure_git_exclude(src, overlay_paths=None)
    leftovers = [d for d in overlay_dirs if (src / d).exists()]
    if leftovers:
        common.warn("overlay dir(s) not fully removed: %s" % ", ".join(leftovers))

    patchset.clear_state(src)
    dirty = common.git(["status", "--porcelain"], cwd=src).stdout.strip()
    if dirty:
        common.warn("tree still has changes outside the patch model:\n%s" % dirty)
    common.info("reset %d known path(s); state cleared" % len(paths))


if __name__ == "__main__":
    main()
