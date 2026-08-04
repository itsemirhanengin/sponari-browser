#!/usr/bin/env python3
"""Fetch and check out the pinned Chromium tag, then gclient sync.

User-run and slow: the first run clones full-history Chromium (hours,
~80GB); later runs fetch one tag and re-align DEPS in minutes. Refuses to
run while patches are applied.
"""
import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import common, patchset


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--force", action="store_true",
                        help="pass --force to gclient sync")
    parser.add_argument("--no-sync", action="store_true",
                        help="checkout the tag only, skip gclient sync")
    args = parser.parse_args()

    if not shutil.which("gclient"):
        common.die("depot_tools not in PATH.\n"
                   "  Run scripts/bootstrap.py, then add to ~/.zshrc:\n"
                   '  export PATH="$HOME/depot_tools:$PATH"')

    src = common.chromium_src()
    chromium_root = src.parent
    pin = common.read_pin()

    if not (chromium_root / ".gclient").exists():
        common.die("no .gclient at %s — run scripts/bootstrap.py first" % chromium_root)

    first_run = not (src / ".git").exists()
    if first_run:
        common.info("first sync: cloning Chromium with FULL history — this takes "
                    "hours and ~80GB. Safe to leave unattended.")
        common.run(["gclient", "sync", "--nohooks"], cwd=chromium_root, capture=False)
    else:
        state = patchset.load_state(src)
        if patchset.applied_patches(state):
            common.die("patches are currently applied — run scripts/reset_patches.py "
                       "before syncing")

    tag_ref = "refs/tags/%s" % pin
    have_tag = common.git(["rev-parse", "-q", "--verify", tag_ref + "^{commit}"],
                          cwd=src, check=False).returncode == 0
    if not have_tag:
        common.info("fetching tag %s ..." % pin)
        common.git(["fetch", "origin", "tag", pin], cwd=src, capture=False)

    common.info("checking out %s (detached) ..." % tag_ref)
    common.git(["checkout", "-f", tag_ref], cwd=src, capture=False)

    if not args.no_sync:
        cmd = ["gclient", "sync", "-D"]
        if args.force or first_run:
            cmd.append("--force")
        common.info("running %s (long) ..." % " ".join(cmd))
        common.run(cmd, cwd=chromium_root, capture=False)

    common.info("src is on %s. Next:\n"
                "  python3 scripts/apply_patches.py\n"
                "  python3 scripts/build.py" % pin)


if __name__ == "__main__":
    main()
