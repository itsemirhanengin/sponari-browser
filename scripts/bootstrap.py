#!/usr/bin/env python3
"""One-time environment setup: depot_tools, .gclient, launchd watcher.

Checks Xcode, clones depot_tools if missing, writes the .gclient file, and
prints the next steps. Never starts the sync itself.

  --chromium-dir DIR   put the Chromium checkout under DIR (e.g. ~/chromium);
                       recorded in the machine-local .chromium_dir file
  --watcher            install the daily launchd upstream watcher
  --uninstall-watcher  remove it
"""
import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import common

DEPOT_TOOLS_URL = "https://chromium.googlesource.com/chromium/tools/depot_tools.git"
PLIST_NAME = "co.sponari.upstream-watch.plist"
PLIST_TEMPLATE = common.AUTOMATION_DIR / PLIST_NAME
LAUNCH_AGENTS = Path.home() / "Library" / "LaunchAgents"


def check_xcode():
    proc = common.run(["xcode-select", "-p"], check=False)
    if proc.returncode != 0:
        common.warn("Xcode command line tools not configured — run: xcode-select --install")
    else:
        common.info("Xcode developer dir: %s" % proc.stdout.strip())


def ensure_depot_tools():
    if shutil.which("gclient"):
        common.info("depot_tools already in PATH")
        return None
    depot = Path.home() / "depot_tools"
    if not depot.exists():
        common.info("cloning depot_tools to %s ..." % depot)
        common.run(["git", "clone", DEPOT_TOOLS_URL, str(depot)], capture=False)
    return depot


def ensure_gclient_config():
    chromium_root = common.chromium_src().parent
    chromium_root.mkdir(parents=True, exist_ok=True)
    gclient_file = chromium_root / ".gclient"
    if gclient_file.exists():
        common.info(".gclient already present at %s" % chromium_root)
    else:
        gclient_file.write_text((common.REPO_ROOT / ".gclient.template").read_text())
        common.info("wrote %s" % gclient_file)
    return chromium_root


def install_watcher():
    if not PLIST_TEMPLATE.exists():
        common.die("plist template missing: %s" % PLIST_TEMPLATE)
    LAUNCH_AGENTS.mkdir(parents=True, exist_ok=True)
    log_path = common.UPGRADE_DIR / "watcher.log"
    common.UPGRADE_DIR.mkdir(exist_ok=True)
    rendered = (PLIST_TEMPLATE.read_text()
                .replace("__SCRIPT__", str(Path(__file__).resolve().parent
                                           / "check_upstream.py"))
                .replace("__LOG__", str(log_path)))
    dest = LAUNCH_AGENTS / PLIST_NAME
    dest.write_text(rendered)
    common.run(["launchctl", "unload", str(dest)], check=False)
    common.run(["launchctl", "load", str(dest)])
    common.info("watcher installed (daily 10:30): %s" % dest)
    common.info("verify with: launchctl list | grep sponari")


def uninstall_watcher():
    dest = LAUNCH_AGENTS / PLIST_NAME
    if dest.exists():
        common.run(["launchctl", "unload", str(dest)], check=False)
        dest.unlink()
        common.info("watcher removed")
    else:
        common.info("watcher not installed")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--chromium-dir", metavar="DIR",
                        help="root dir for the Chromium checkout "
                             "(src/ goes inside it), e.g. ~/chromium")
    parser.add_argument("--watcher", action="store_true")
    parser.add_argument("--uninstall-watcher", action="store_true")
    args = parser.parse_args()

    if args.watcher:
        install_watcher()
        return
    if args.uninstall_watcher:
        uninstall_watcher()
        return

    if args.chromium_dir:
        root = Path(args.chromium_dir).expanduser().resolve()
        common.CHROMIUM_DIR_FILE.write_text(str(root / "src") + "\n")
        common.info("Chromium checkout location recorded in .chromium_dir: %s"
                    % (root / "src"))

    check_xcode()
    depot = ensure_depot_tools()
    chromium_root = ensure_gclient_config()

    print()
    common.info("bootstrap done. Next steps (run these yourself — the sync "
                "takes HOURS):")
    step = 1
    if depot:
        print("  %d. Add depot_tools to PATH (and to ~/.zshrc):" % step)
        print('       export PATH="$HOME/depot_tools:$PATH"')
        step += 1
    print("  %d. python3 scripts/sync.py" % step)
    print("       (first run clones full-history Chromium into %s — hours, ~80GB)"
          % (chromium_root / "src"))
    print("  %d. python3 scripts/apply_patches.py" % (step + 1))
    print("  %d. python3 scripts/build.py   # gn gen + prints the autoninja command"
          % (step + 2))


if __name__ == "__main__":
    main()
