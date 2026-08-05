"""Patch naming, enumeration, overlay planning and apply-state tracking.

Two delivery channels into the Chromium tree:

  patches/     — one patch per *existing* upstream file. The filename is the
                 upstream path with '/' replaced by '-', but the real target
                 path is parsed from the diff header.
  overlay/     — whole *new* files, mirroring the src/ layout, copied in
                 verbatim. They stay untracked inside src so export_patches.py
                 never sees them and `git -C src diff` remains exactly the
                 patch set. Declared by copy_manifest.json's "trees".

Apply state lives in <src>/.sponari_patch_state.json, kept out of git via
.git/info/exclude so Chromium's .gitignore stays untouched.
"""
import fnmatch
import hashlib
import json
import re
from pathlib import Path, PurePosixPath

from . import common

STATE_BASENAME = ".sponari_patch_state.json"
_DIFF_HEADER_RE = re.compile(r"^diff --git a/(.+) b/(.+)$")

# Never copied, whatever the manifest says.
DEFAULT_EXCLUDES = ["**/.DS_Store", "**/__pycache__/**", "**/*.pyc"]

_EXCLUDE_BEGIN = "# BEGIN sponari overlay (managed by scripts/apply_patches.py)"
_EXCLUDE_END = "# END sponari overlay"


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
    return sha256_bytes(path.read_bytes())


def sha256_bytes(data):
    digest = hashlib.sha256()
    digest.update(data)
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
    return {"chromium_version": None, "patches": {}, "copied": {}}


def save_state(src, state):
    # Derived from the state so incidental savers (resolve_conflicts.py) keep
    # the managed ignore block intact rather than dropping it.
    ensure_git_exclude(src, copied_paths(state))
    state_path(src).write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")


def clear_state(src):
    path = state_path(src)
    if path.exists():
        path.unlink()


def ensure_git_exclude(src, overlay_paths=None):
    """Keep the state file and the overlay files out of `git status` in src.

    Excludes are listed per file rather than per directory on purpose: anything
    unexpected inside an overlay directory — a stale copy, a stray build
    artifact — then still shows up as untracked instead of being hidden.

    The block is regenerated from scratch every time, so passing
    overlay_paths=None (what reset_patches.py does) removes it again. Ignore
    rules never apply to tracked files, so real modifications to upstream files
    stay visible.
    """
    git_dir = src / ".git"
    if not git_dir.is_dir():
        return
    exclude = git_dir / "info" / "exclude"
    exclude.parent.mkdir(parents=True, exist_ok=True)
    lines = exclude.read_text().splitlines() if exclude.exists() else []
    if _EXCLUDE_BEGIN in lines and _EXCLUDE_END in lines:
        begin, end = lines.index(_EXCLUDE_BEGIN), lines.index(_EXCLUDE_END)
        if begin < end:
            lines = lines[:begin] + lines[end + 1:]
    if STATE_BASENAME not in lines:
        lines.append(STATE_BASENAME)
    if overlay_paths:
        lines += ([_EXCLUDE_BEGIN]
                  + ["/%s" % p for p in sorted(overlay_paths)]
                  + [_EXCLUDE_END])
    exclude.write_text("\n".join(lines) + "\n")


def applied_patches(state):
    return [
        name
        for name, entry in state.get("patches", {}).items()
        if entry.get("status") in ("applied", "conflict", "failed")
    ]


def load_copy_manifest():
    """-> (files, trees). "copies" keeps its original single-file meaning."""
    if not common.COPY_MANIFEST.exists():
        return [], []
    data = json.loads(common.COPY_MANIFEST.read_text())
    return data.get("copies", []), data.get("trees", [])


def _check_dest(dest):
    """Reject anything that would write outside the checkout."""
    pure = PurePosixPath(dest)
    if pure.is_absolute() or ".." in pure.parts:
        common.die("copy_manifest dest escapes the checkout: %s" % dest)
    return pure.as_posix()


def _excluded(rel, patterns):
    """Match a tree-relative posix path against the exclude globs.

    fnmatch has no notion of '**', so "**/*.md" alone would miss a file at the
    tree root. Patterns are therefore also tried with a leading '**/' stripped,
    and a slash-free pattern is tried against the basename at any depth.
    """
    name = PurePosixPath(rel).name
    for pattern in patterns:
        if fnmatch.fnmatch(rel, pattern):
            return True
        if pattern.startswith("**/") and fnmatch.fnmatch(rel, pattern[3:]):
            return True
        if "/" not in pattern and fnmatch.fnmatch(name, pattern):
            return True
    return False


def _expand_tree(entry):
    """-> [(abs source, src-relative dest)] for one "trees" entry."""
    root = common.REPO_ROOT / entry["source"]
    dest_root = PurePosixPath(entry.get("dest", "."))
    patterns = list(entry.get("exclude", [])) + DEFAULT_EXCLUDES
    out = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if _excluded(rel, patterns):
            continue
        out.append((path, _check_dest((dest_root / rel).as_posix())))
    return out


def overlay_plan(src=None):
    """-> {src-relative dest: abs source} for the whole manifest.

    Pass src to also verify that no "trees" entry shadows a file that exists
    upstream. Trees carry *new* files only; editing an existing upstream file
    is a patch, and replacing an upstream binary is a "copies" entry. Without
    this check a stray file in overlay/ silently clobbers Chromium's own copy.
    """
    files, trees = load_copy_manifest()
    plan = {}
    for entry in files:
        source = common.REPO_ROOT / entry["source"]
        if not source.exists():
            common.warn("copy_manifest source missing, skipped: %s" % entry["source"])
            continue
        plan[_check_dest(entry["dest"])] = source
    tree_dests = []
    for entry in trees:
        root = common.REPO_ROOT / entry["source"]
        if not root.is_dir():
            common.warn("copy_manifest tree missing, skipped: %s" % entry["source"])
            continue
        for source, dest in _expand_tree(entry):
            if dest in plan:
                common.die("copy_manifest: two sources map to %s" % dest)
            plan[dest] = source
            tree_dests.append(dest)
    if src is not None and tree_dests:
        shadowed = [d for d in tree_dests
                    if common.git(["cat-file", "-e", "HEAD:%s" % d],
                                  cwd=src, check=False).returncode == 0]
        if shadowed:
            common.die("overlay would overwrite file(s) that exist upstream:\n  %s\n"
                       "  Overlay trees are for new files only — use a patch to "
                       "edit an upstream file, or a copy_manifest \"copies\" entry "
                       "to replace an upstream binary." % "\n  ".join(sorted(shadowed)))
    return plan


def copied_paths(state):
    """Dests written on the previous apply, tolerating the old state shape."""
    recorded = state.get("copied")
    if isinstance(recorded, dict):
        return sorted(set(recorded) | set(state.get("binaries", [])))
    return sorted(set(recorded or []) | set(state.get("binaries", [])))


def copied_digests(state):
    """-> {dest: sha256}. Legacy list-shaped state yields unknown digests."""
    recorded = state.get("copied")
    if isinstance(recorded, dict):
        return dict(recorded)
    return {dest: None for dest in copied_paths(state)}


def overlay_roots(src, dests):
    """Shallowest ancestor of each dest that does not exist at HEAD.

    For our layout that is one directory per new Chromium subtree — exactly
    what belongs in .git/info/exclude.
    """
    roots = set()
    for dest in dests:
        parts = PurePosixPath(dest).parts[:-1]
        for i in range(1, len(parts) + 1):
            candidate = PurePosixPath(*parts[:i]).as_posix()
            missing = common.git(["cat-file", "-e", "HEAD:%s" % candidate],
                                 cwd=src, check=False).returncode != 0
            if missing:
                roots.add(candidate)
                break
    return sorted(roots)


def prune_empty_dirs(src, directory):
    """rmdir upwards from `directory` until something is non-empty or we hit src."""
    src = Path(src).resolve()
    directory = Path(directory).resolve()
    while directory != src and src in directory.parents:
        try:
            directory.rmdir()
        except OSError:
            return
        directory = directory.parent
