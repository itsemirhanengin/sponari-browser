#!/usr/bin/env python3
"""Staged Chromium upgrade flow.

  --prepare [--version V]  reset patches, bump the pin, record the session
                           (then run scripts/sync.py yourself — it's long)
  --apply                  re-apply patches on the new tag, write conflicts
                           to .upgrade/report.json
  --report                 print the report as a checklist

Nothing here commits anything. Review the report and the diff, build, then
land the pin bump + regenerated patches as one commit.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import common, patchset

import check_upstream

SESSION_FILE = common.UPGRADE_DIR / "session.json"
REPORT_FILE = common.UPGRADE_DIR / "report.json"
SCRIPTS_DIR = Path(__file__).resolve().parent
DIFF_TRUNCATE = 20000


def load_json(path, what):
    if not path.exists():
        common.die("no %s at %s — run the previous stage first" % (what, path))
    return json.loads(path.read_text())


def extract_conflict_hunks(text, context=6):
    lines = text.splitlines()
    blocks = []
    start = None
    for i, line in enumerate(lines):
        if line.startswith("<<<<<<<") and start is None:
            start = max(0, i - context)
        elif line.startswith(">>>>>>>") and start is not None:
            end = min(len(lines), i + 1 + context)
            blocks.append("\n".join(lines[start:end]))
            start = None
    return "\n\n[...]\n\n".join(blocks)


def truncate(text, limit=DIFF_TRUNCATE):
    if len(text) <= limit:
        return text
    return text[:limit] + "\n[... truncated %d chars ...]" % (len(text) - limit)


def cmd_prepare(args):
    src = common.require_src()
    old_version = common.read_pin()

    state = patchset.load_state(src)
    if patchset.applied_patches(state):
        common.info("patches are applied — resetting first")
        subprocess.run([sys.executable, str(SCRIPTS_DIR / "reset_patches.py")],
                       check=True)

    if args.version:
        new_version = args.version
    else:
        common.info("querying chromiumdash for the latest stable ...")
        new_version = check_upstream.fetch_latest()["version"]

    if new_version == old_version:
        common.die("already pinned to %s" % old_version)
    if (common.version_tuple(new_version) < common.version_tuple(old_version)
            and not args.allow_downgrade):
        common.die("%s is older than pin %s (use --allow-downgrade for a rehearsal)"
                   % (new_version, old_version))

    common.UPGRADE_DIR.mkdir(exist_ok=True)
    SESSION_FILE.write_text(json.dumps(
        {"old_version": old_version, "new_version": new_version}, indent=2) + "\n")
    common.write_pin(new_version)

    common.info("pin bumped %s -> %s. Next steps (you run these):\n"
                "  python3 scripts/sync.py          # long: fetch + checkout + gclient sync\n"
                "  python3 scripts/upgrade.py --apply"
                % (old_version, new_version))


def cmd_apply(_args):
    src = common.require_src()
    session = load_json(SESSION_FILE, "upgrade session")
    old_version = session["old_version"]
    new_version = session["new_version"]

    common.info("applying patch set on chromium %s ..." % new_version)
    subprocess.run([sys.executable, str(SCRIPTS_DIR / "apply_patches.py")],
                   check=False)

    state = patchset.load_state(src)
    results = []
    conflicted = 0
    for name, entry in sorted(state.get("patches", {}).items()):
        target = entry.get("target")
        item = {
            "patch": name,
            "target": target,
            "status": entry.get("status"),
            "needs_review": False,
        }
        if entry.get("status") in ("conflict", "failed") and target:
            conflicted += 1
            item["apply_error"] = entry.get("error")
            patch_file = common.PATCHES_DIR / name
            item["original_patch"] = (patch_file.read_text()
                                      if patch_file.exists() else "")
            target_file = src / target
            if entry["status"] == "conflict" and target_file.exists():
                item["conflict_hunks"] = extract_conflict_hunks(
                    target_file.read_text(errors="replace"))
            rej = src / (target + ".rej")
            if rej.exists():
                item["rej"] = rej.read_text(errors="replace")
            diff = common.git(
                ["diff", "refs/tags/%s" % old_version,
                 "refs/tags/%s" % new_version, "--", target],
                cwd=src, check=False)
            item["upstream_diff"] = (truncate(diff.stdout)
                                     if diff.returncode == 0 else
                                     "(unavailable: %s)" % (diff.stderr or "").strip())
        results.append(item)

    report = {"old_version": old_version, "new_version": new_version,
              "results": results}
    common.UPGRADE_DIR.mkdir(exist_ok=True)
    REPORT_FILE.write_text(json.dumps(report, indent=2) + "\n")

    clean = sum(1 for r in results if r["status"] == "applied")
    common.info("report written to %s" % REPORT_FILE)
    common.info("%d applied clean, %d conflicted" % (clean, conflicted))
    if conflicted:
        common.info("next: python3 scripts/resolve_conflicts.py")
        sys.exit(2)


def cmd_report(_args):
    report = load_json(REPORT_FILE, "upgrade report")
    print("Upgrade %s -> %s" % (report["old_version"], report["new_version"]))
    for item in report["results"]:
        marker = {"applied": "ok ", "ai_resolved": "AI ",
                  "conflict": "!! ", "failed": "!! "}.get(item["status"], "?  ")
        review = "  [NEEDS REVIEW]" if item.get("needs_review") else ""
        print("  %s %-60s %s%s" % (marker, item["patch"], item["status"], review))
        if item.get("explanation"):
            print("       resolver: %s" % item["explanation"].strip().replace("\n", " ")[:200])
    print("\nReview gate: git -C <src> diff, build, smoke-test; then commit the\n"
          "regenerated patches + .chromium_version bump as one upgrade commit.")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--prepare", action="store_true")
    group.add_argument("--apply", action="store_true")
    group.add_argument("--report", action="store_true")
    parser.add_argument("--version", help="target version (default: latest stable)")
    parser.add_argument("--allow-downgrade", action="store_true",
                        help="permit pinning an older version (upgrade rehearsal)")
    args = parser.parse_args()

    if args.prepare:
        cmd_prepare(args)
    elif args.apply:
        cmd_apply(args)
    else:
        cmd_report(args)


if __name__ == "__main__":
    main()
