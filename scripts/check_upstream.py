#!/usr/bin/env python3
"""Compare our pin against the newest stable release on chromiumdash.

Exit codes: 0 up to date, 10 newer available, 1 error.
"""
import argparse
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import common

API = "https://chromiumdash.appspot.com/fetch_releases?channel=%s&platform=%s&num=%d"


def fetch_latest(channel="Stable", platform="Mac", num=10):
    url = API % (channel, platform, num)
    with urllib.request.urlopen(url, timeout=30) as response:
        releases = json.loads(response.read().decode("utf-8"))
    best = None
    for release in releases:
        version = release.get("version")
        if not version:
            continue
        try:
            common.version_tuple(version)
        except ValueError:
            continue
        if best is None or (common.version_tuple(version)
                            > common.version_tuple(best["version"])):
            best = release
    if best is None:
        raise RuntimeError("no parseable releases in chromiumdash response")
    return best


def notify_mac(title, message):
    common.run(["osascript", "-e",
                'display notification "%s" with title "%s"' % (message, title)],
               check=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--notify", action="store_true",
                        help="fire a macOS notification and record "
                             ".upgrade/pending_version when newer")
    parser.add_argument("--channel", default="Stable")
    parser.add_argument("--platform", default="Mac")
    args = parser.parse_args()

    current = common.read_pin()
    try:
        latest = fetch_latest(channel=args.channel, platform=args.platform)
    except Exception as exc:  # network/API failure -> exit 1
        common.die("chromiumdash query failed: %s" % exc)

    newer = common.version_tuple(latest["version"]) > common.version_tuple(current)
    payload = {
        "current": current,
        "latest": latest["version"],
        "milestone": latest.get("milestone"),
        "release_time": latest.get("time"),
        "newer": newer,
    }

    if args.as_json:
        print(json.dumps(payload))
    elif newer:
        print("NEWER: chromium %s (M%s) is out; pin is %s"
              % (payload["latest"], payload["milestone"], current))
    else:
        print("up to date: pin %s >= latest stable %s" % (current, payload["latest"]))

    if args.notify and newer:
        common.UPGRADE_DIR.mkdir(exist_ok=True)
        (common.UPGRADE_DIR / "pending_version").write_text(latest["version"] + "\n")
        notify_mac("Sponari upstream watch",
                   "Chromium %s released (pin: %s). Run upgrade.py --prepare."
                   % (latest["version"], current))

    sys.exit(10 if newer else 0)


if __name__ == "__main__":
    main()
