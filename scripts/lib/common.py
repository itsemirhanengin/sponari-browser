"""Shared helpers for Sponari scripts. Python 3.9, stdlib only."""
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PATCHES_DIR = REPO_ROOT / "patches"
UPGRADE_DIR = REPO_ROOT / ".upgrade"
VERSION_FILE = REPO_ROOT / ".chromium_version"
COPY_MANIFEST = REPO_ROOT / "resources" / "branding" / "copy_manifest.json"
PROMPTS_DIR = REPO_ROOT / "automation" / "prompts"
AUTOMATION_DIR = REPO_ROOT / "automation"
# Machine-local pointer to the Chromium src dir, written by
# bootstrap.py --chromium-dir. Gitignored; unlike the env var it also
# works under launchd/CI where .zshrc is never sourced.
CHROMIUM_DIR_FILE = REPO_ROOT / ".chromium_dir"


class CommandError(RuntimeError):
    def __init__(self, cmd, proc):
        self.cmd = cmd
        self.proc = proc
        detail = (proc.stderr or "").strip()
        super().__init__(
            "command failed (exit %d): %s%s"
            % (proc.returncode, " ".join(cmd), "\n" + detail if detail else "")
        )


def info(msg):
    print("[sponari] %s" % msg)


def warn(msg):
    print("[sponari] warning: %s" % msg, file=sys.stderr)


def die(msg, code=1):
    print("[sponari] error: %s" % msg, file=sys.stderr)
    sys.exit(code)


def chromium_src():
    """SPONARI_CHROMIUM_DIR env > .chromium_dir file > ../chromium/src."""
    env = os.environ.get("SPONARI_CHROMIUM_DIR")
    if env:
        return Path(env).expanduser().resolve()
    if CHROMIUM_DIR_FILE.exists():
        configured = CHROMIUM_DIR_FILE.read_text().strip()
        if configured:
            return Path(configured).expanduser().resolve()
    return (REPO_ROOT.parent / "chromium" / "src").resolve()


def require_src():
    src = chromium_src()
    if not (src / ".git").exists():
        die(
            "Chromium checkout not found at %s\n"
            "  Run scripts/bootstrap.py first, then scripts/sync.py "
            "(or point SPONARI_CHROMIUM_DIR at an existing checkout)." % src
        )
    return src


def read_pin():
    if not VERSION_FILE.exists():
        die(".chromium_version missing at %s" % VERSION_FILE)
    return VERSION_FILE.read_text().strip()


def write_pin(version):
    VERSION_FILE.write_text(version.strip() + "\n")


def version_tuple(version):
    return tuple(int(part) for part in version.strip().split("."))


def run(cmd, cwd=None, check=True, capture=True, timeout=None):
    # capture=False streams output to the terminal, for long-running commands.
    cmd = [str(c) for c in cmd]
    proc = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
        timeout=timeout,
    )
    if check and proc.returncode != 0:
        raise CommandError(cmd, proc)
    return proc


def git(args, cwd, check=True, capture=True):
    return run(["git"] + list(args), cwd=cwd, check=check, capture=capture)
