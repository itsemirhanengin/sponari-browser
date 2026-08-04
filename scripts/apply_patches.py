#!/usr/bin/env python3
"""Apply the patch set onto the Chromium working tree with git apply --3way.

Per-patch outcome is applied, conflict (markers left in the file) or failed
(falls back to --reject so .rej hunks are left for the resolver). Reruns are
idempotent via the state file. Binary assets from copy_manifest.json are
copied after the patches.
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


def copy_binaries(src, state):
    copied = []
    for entry in patchset.load_copy_manifest():
        source = common.REPO_ROOT / entry["source"]
        dest = src / entry["dest"]
        if not source.exists():
            common.warn("copy_manifest source missing, skipped: %s" % entry["source"])
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)
        copied.append(entry["dest"])
        binaries = state.setdefault("binaries", [])
        if entry["dest"] not in binaries:
            binaries.append(entry["dest"])
    return copied


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--force", action="store_true",
                        help="re-apply even if state says already applied")
    parser.add_argument("--only", action="append", metavar="PATCH_FILENAME",
                        help="only apply this patch file (repeatable)")
    args = parser.parse_args()

    src = common.require_src()
    pin = common.read_pin()
    state = patchset.load_state(src)
    same_version = state.get("chromium_version") == pin

    patches = patchset.list_patches()
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

    state["chromium_version"] = pin
    copied = copy_binaries(src, state)
    patchset.save_state(src, state)

    if results:
        width = max(len(name) for name, _ in results)
        for name, status in results:
            print("  %-*s  %s" % (width, name, status))
    else:
        common.info("no patches in patches/")
    if copied:
        common.info("copied %d binary asset(s)" % len(copied))
    if bad:
        common.info("%d patch(es) did NOT apply cleanly — see docs/UPGRADE.md "
                    "(conflict markers / .rej files left in the tree)" % len(bad))
        sys.exit(1)
    common.info("patch set applied against chromium %s" % pin)


if __name__ == "__main__":
    main()
