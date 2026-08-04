#!/usr/bin/env python3
"""Drive headless Claude Code over patches that failed to apply.

For each conflicted entry in .upgrade/report.json this builds a prompt from
automation/prompts/conflict_resolver.md, runs `claude -p` (Read/Edit only,
cwd=src) so Claude fixes the actual working tree, validates the result,
regenerates the .patch and marks it ai_resolved + needs_review. Never
commits anything.
"""
import argparse
import json
import string
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import common, patchset

REPORT_FILE = common.UPGRADE_DIR / "report.json"
TEMPLATE_FILE = common.PROMPTS_DIR / "conflict_resolver.md"
SCRIPTS_DIR = Path(__file__).resolve().parent


def build_prompt(item, report):
    template = string.Template(TEMPLATE_FILE.read_text())
    conflict_details = []
    if item.get("conflict_hunks"):
        conflict_details.append("The file contains 3-way conflict markers:\n\n"
                                + item["conflict_hunks"])
    if item.get("rej"):
        conflict_details.append("Rejected hunks (.rej) that must be integrated "
                                "manually:\n\n" + item["rej"])
    if item.get("apply_error"):
        conflict_details.append("git apply said:\n" + item["apply_error"])
    return template.safe_substitute(
        target=item["target"],
        old_version=report["old_version"],
        new_version=report["new_version"],
        original_patch=item.get("original_patch", ""),
        upstream_diff=item.get("upstream_diff", "(unavailable)"),
        conflict_details="\n\n".join(conflict_details) or "(none captured)",
    )


def mark(item, status, note):
    item["status"] = status
    item["resolver_note"] = note


def resolve_one(item, report, src, args):
    prompt = build_prompt(item, report)
    if args.dry_run:
        print("\n===== PROMPT for %s =====\n%s" % (item["patch"], prompt))
        return

    cmd = [args.claude_bin, "-p", prompt,
           "--output-format", "json",
           "--allowedTools", "Read,Edit",
           "--max-turns", str(args.max_turns)]
    common.info("resolving %s (claude -p, timeout %ds) ..."
                % (item["patch"], args.timeout))
    try:
        proc = common.run(cmd, cwd=src, check=False, timeout=args.timeout)
    except subprocess.TimeoutExpired:
        mark(item, "unresolved", "claude timed out")
        return
    if proc.returncode != 0:
        mark(item, "unresolved", "claude exited %d: %s"
             % (proc.returncode, (proc.stderr or "")[-500:]))
        return

    try:
        result_text = json.loads(proc.stdout).get("result", "")
    except ValueError:
        result_text = proc.stdout or ""

    if result_text.strip().startswith("UNRESOLVED"):
        mark(item, "unresolved", result_text.strip()[:1000])
        return

    target = item["target"]
    target_file = src / target
    if not target_file.exists():
        mark(item, "unresolved", "target file missing after resolution attempt")
        return
    content = target_file.read_text(errors="replace")
    if "<<<<<<<" in content:
        mark(item, "unresolved", "conflict markers still present")
        return
    diff = common.git(["diff", "HEAD", "--", target], cwd=src)
    if not diff.stdout.strip():
        mark(item, "unresolved", "no change against HEAD after resolution")
        return

    export = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "export_patches.py"), "--only", target],
        capture_output=True, text=True)
    if export.returncode != 0:
        mark(item, "unresolved", "patch regeneration failed: %s"
             % (export.stderr or export.stdout)[-500:])
        return

    rej = src / (target + ".rej")
    if rej.exists():
        rej.unlink()

    item["status"] = "ai_resolved"
    item["needs_review"] = True
    item["explanation"] = result_text[-4000:]

    # Update apply-state so a rerun of apply_patches.py sees this as applied.
    state = patchset.load_state(src)
    entry = state["patches"].setdefault(item["patch"], {})
    entry.update({
        "status": "applied",
        "target": target,
        "sha256": patchset.sha256_of(common.PATCHES_DIR / item["patch"]),
        "error": None,
    })
    patchset.save_state(src, state)
    common.info("%s -> ai_resolved (needs human review)" % item["patch"])


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--patch", action="append",
                        help="only resolve this patch filename (repeatable)")
    parser.add_argument("--timeout", type=int, default=900,
                        help="seconds per patch (default 900)")
    parser.add_argument("--max-turns", type=int, default=40)
    parser.add_argument("--claude-bin", default="claude")
    parser.add_argument("--dry-run", action="store_true",
                        help="print the prompts instead of invoking claude")
    args = parser.parse_args()

    src = common.require_src()
    if not REPORT_FILE.exists():
        common.die("no %s — run upgrade.py --apply first" % REPORT_FILE)
    report = json.loads(REPORT_FILE.read_text())

    todo = [item for item in report["results"]
            if item["status"] in ("conflict", "failed", "unresolved")]
    if args.patch:
        wanted = set(args.patch)
        todo = [item for item in todo if item["patch"] in wanted]
    if not todo:
        common.info("nothing to resolve")
        return

    for item in todo:
        resolve_one(item, report, src, args)

    REPORT_FILE.write_text(json.dumps(report, indent=2) + "\n")
    resolved = sum(1 for i in report["results"] if i["status"] == "ai_resolved")
    unresolved = sum(1 for i in report["results"]
                     if i["status"] in ("conflict", "failed", "unresolved"))
    common.info("done: %d ai_resolved (review them!), %d still unresolved"
                % (resolved, unresolved))
    common.info("next: python3 scripts/upgrade.py --report")


if __name__ == "__main__":
    main()
