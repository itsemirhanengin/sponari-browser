"""Patch naming, enumeration and apply-state tracking.

One patch per upstream file; the filename is the upstream path with '/'
replaced by '-', but the real target path is parsed from the diff header.
Apply state lives in <src>/.sponari_patch_state.json, kept out of git via
.git/info/exclude so Chromium's .gitignore stays untouched.
"""
import hashlib
import json
import re

from . import common

STATE_BASENAME = ".sponari_patch_state.json"
_DIFF_HEADER_RE = re.compile(r"^diff --git a/(.+) b/(.+)$")


def patch_name_for(upstream_path):
    return upstream_path.strip("/").replace("/", "-") + ".patch"


def list_patches():
    if not common.PATCHES_DIR.is_dir():
        return []
    return sorted(common.PATCHES_DIR.glob("*.patch"))


def target_path_of(patch_file):
    for line in patch_file.read_text(errors="replace").splitlines():
        m = _DIFF_HEADER_RE.match(line)
        if m:
            return m.group(2)
    return None


def sha256_of(path):
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def state_path(src):
    return src / STATE_BASENAME


def load_state(src):
    path = state_path(src)
    if path.exists():
        try:
            return json.loads(path.read_text())
        except ValueError:
            common.warn("corrupt %s — starting fresh" % STATE_BASENAME)
    return {"chromium_version": None, "patches": {}, "binaries": []}


def save_state(src, state):
    ensure_git_exclude(src)
    state_path(src).write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")


def clear_state(src):
    path = state_path(src)
    if path.exists():
        path.unlink()


def ensure_git_exclude(src):
    git_dir = src / ".git"
    if not git_dir.is_dir():
        return
    exclude = git_dir / "info" / "exclude"
    exclude.parent.mkdir(parents=True, exist_ok=True)
    lines = exclude.read_text().splitlines() if exclude.exists() else []
    if STATE_BASENAME not in lines:
        lines.append(STATE_BASENAME)
        exclude.write_text("\n".join(lines) + "\n")


def applied_patches(state):
    return [
        name
        for name, entry in state.get("patches", {}).items()
        if entry.get("status") in ("applied", "conflict", "failed")
    ]


def load_copy_manifest():
    if not common.COPY_MANIFEST.exists():
        return []
    data = json.loads(common.COPY_MANIFEST.read_text())
    return data.get("copies", [])
