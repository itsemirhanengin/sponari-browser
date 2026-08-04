#!/usr/bin/env python3
"""Set up the GN build dir and print the build command.

Copies scripts/gn/dev-mac-arm64.gn to <src>/out/Dev/args.gn and runs
`gn gen`. The build itself is always started by the user.
"""
import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import common

ARGS_TEMPLATE = Path(__file__).resolve().parent / "gn" / "dev-mac-arm64.gn"


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", default="out/Dev", help="build dir relative to src")
    parser.add_argument("--print-only", action="store_true",
                        help="write args.gn but skip gn gen")
    args = parser.parse_args()

    src = common.require_src()
    out_dir = src / args.out
    out_dir.mkdir(parents=True, exist_ok=True)
    args_gn = out_dir / "args.gn"

    template = ARGS_TEMPLATE.read_text()
    if args_gn.exists() and args_gn.read_text() != template:
        common.warn("overwriting existing %s (previous copy at args.gn.bak)" % args_gn)
        shutil.copy2(args_gn, out_dir / "args.gn.bak")
    args_gn.write_text(template)
    common.info("wrote %s" % args_gn)

    if not args.print_only:
        if not shutil.which("gn"):
            common.die("gn not in PATH — add depot_tools (see scripts/bootstrap.py)")
        common.run(["gn", "gen", args.out], cwd=src, capture=False)

    print()
    common.info("build it yourself (first build: 4-8h on Apple Silicon):")
    print("  cd %s && autoninja -C %s chrome" % (src, args.out))


if __name__ == "__main__":
    main()
