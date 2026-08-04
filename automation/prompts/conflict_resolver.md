You are resolving a patch conflict for Sponari, a Chromium-derived browser
that maintains its entire delta as a set of patches applied onto pinned
Chromium releases (Brave-style patch model).

Chromium was upgraded from $old_version to $new_version, and the patch below
no longer applies cleanly to its target file.

## Target file

$target

## The patch's intent (it applied cleanly to Chromium $old_version)

```diff
$original_patch
```

## Upstream changes to this file between $old_version and $new_version (may be truncated)

```diff
$upstream_diff
```

## Current conflict state

$conflict_details

## Your task

1. Open the target file in this working tree and re-apply the patch's INTENT
   onto the new upstream code.
2. If the file contains conflict markers (<<<<<<< ======= >>>>>>>), resolve
   them. If hunks were rejected (.rej), integrate their intent manually at
   the right place in the new code.
3. Change NOTHING beyond the patch's intent: no reformatting, no drive-by
   fixes. Keep upstream's new code intact except where the intent requires a
   change.
4. Sponari invariants you must preserve:
   - The user agent must remain Chrome-compatible (never touch UA branding).
   - Message IDs in .grd files are never renamed — only string values change.
   - is_chrome_branded stays false.
5. If you cannot resolve this confidently, make no edits and reply exactly:
   UNRESOLVED: <one-line reason>

When done, reply with one short paragraph explaining where the patch's intent
moved in the new upstream code and how you resolved the conflict.
