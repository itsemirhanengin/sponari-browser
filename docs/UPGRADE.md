# Chromium Upgrade Runbook

Chromium ships a new stable roughly every four weeks. This is the procedure
for taking one in.

## 0. Detection

- launchd watcher (install: `python3 scripts/bootstrap.py --watcher`) runs
  `check_upstream.py --notify` daily at 10:30 and fires a macOS notification
  when a newer stable exists.
- Manual check: `python3 scripts/check_upstream.py` (exit 10 = newer).
- GitHub Actions (`upstream-watch.yml`) opens an issue on the repo.

## 1. Prepare (seconds)

```bash
python3 scripts/upgrade.py --prepare          # latest stable, or --version X.Y.Z.W
```

Resets any applied patches, records the session, bumps `.chromium_version`.

## 2. Sync (long — you run it)

```bash
python3 scripts/sync.py
```

Fetches the new tag, checks it out, `gclient sync -D`.

## 3. Re-apply patches

```bash
python3 scripts/upgrade.py --apply
```

Applies the patch set with 3-way merge. Writes `.upgrade/report.json` with,
per failed patch: the original patch (its intent), conflict hunks / `.rej`
content, and the upstream diff `old_tag..new_tag` for the target file.
Exit 2 means conflicts.

## 4. AI conflict resolution

```bash
python3 scripts/resolve_conflicts.py          # or --patch <name> for one at a time
```

Per conflicted patch it runs headless Claude Code (`claude -p`, tools limited
to Read/Edit, cwd = the checkout) with a structured prompt
(`automation/prompts/conflict_resolver.md`). Claude edits the real working
tree; the script validates (no markers left, non-empty diff), regenerates the
`.patch`, and marks it `ai_resolved` + `needs_review`. Anything Claude can't
confidently do stays `unresolved` for manual work.

`--dry-run` prints the prompts without invoking Claude.

## 5. Human review gate (never skipped)

```bash
python3 scripts/upgrade.py --report     # checklist
git -C ../chromium/src diff             # read every ai_resolved change
autoninja -C out/Dev chrome             # it must build
```

Smoke-test the browser (About page, UA in DevTools, a Google login).

## 6. Land it

One commit in this repo: the `.chromium_version` bump + regenerated
`patches/`. Message: `Upgrade to Chromium <version>`.

## Rehearsal (recommended before the first real upgrade)

```bash
python3 scripts/upgrade.py --prepare --version <previous-stable> --allow-downgrade
python3 scripts/sync.py
python3 scripts/upgrade.py --apply
# then upgrade back to the pin the same way
```

Cheap syncs (tags are close), real 3-way exercise. Force a synthetic conflict
by editing a patched region in `src/` first if you want to see the AI loop.
