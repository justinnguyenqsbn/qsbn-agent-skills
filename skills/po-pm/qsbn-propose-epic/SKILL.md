---
name: qsbn-propose-epic
description: Match a feature's PRD against existing epics (or propose a new one), then move the feature folder under the confirmed epic. Also handles moving an already-assigned feature to a different epic.
disable-model-invocation: true
---

# qsbn Propose Epic

Assign a feature to an epic, creating the epic if none fits, and physically
move the feature's folder there. Never merges a feature into an epic
without the user explicitly confirming — no silent matching.

## Workflow

1. **Resolve the feature**
   - Take `$ARGUMENTS` as a PRD description, a path to a feature's
     `prd.md`, or a feature slug. Locate its folder: either
     `artifacts/<feature-slug>/` (unassigned) or
     `artifacts/epic-*/feature-<feature-slug>/` (already assigned — this
     is the reassignment case, go to step 5 after finding candidates in
     step 2).

2. **Find candidate epics**
   - Read `artifacts/epics.md` and every `artifacts/epic-*/epic.md` for
     title and any topic/domain hints in their body. Compare against the
     feature's PRD (title, overview, problem statement).
   - Present the best 1-3 candidates (or none) to the user, each with a
     one-line reason it might fit, plus an explicit "none of these — make
     a new epic" option.

3. **Confirm with the user**
   - Wait for the user to pick an existing epic, or confirm creating a
     new one. Never auto-select the top match.

4. **New epic (if chosen)**
   - Ask for the epic's title if not obvious from the feature. Generate
     `<epic-slug>` (kebab-case, same collision-suffix rule as feature
     slugs: `-2`, `-3`, ...).
   - Create `artifacts/epic-<epic-slug>/epic.md`:
     ```markdown
     ---
     id: EPIC-<epic-slug>
     ado_id: null
     last_synced: null
     title: <Title>
     status: draft
     ---

     # Epic: <Title>

     ## Features
     ```
   - Append a row to `artifacts/epics.md` (create the file with a header
     row if it doesn't exist yet):
     ```markdown
     | ID | Title | Status | Link |
     | --- | --- | --- | --- |
     | EPIC-<epic-slug> | <Title> | draft | [epic.md](./epic-<epic-slug>/epic.md) |
     ```

5. **Move the feature folder**
   - First-time assignment: `git mv artifacts/<feature-slug>/
     artifacts/epic-<chosen-epic-slug>/feature-<feature-slug>/`.
   - Reassignment: `git mv artifacts/epic-<old-epic-slug>/feature-<feature-slug>/
     artifacts/epic-<new-epic-slug>/feature-<feature-slug>/`.
   - If the destination epic folder doesn't exist yet (new epic case),
     `git mv` still works once step 4 has created `epic.md` inside it.

6. **Update the epic(s)' Features sections**
   - Add a line to the chosen epic's `## Features` section:
     `- [<Title>](./feature-<feature-slug>/prd.md)`.
   - Reassignment only: also remove the corresponding line from the old
     epic's `## Features` section.

7. **Update the product PRD link**
   - In `artifacts/prd.md`'s Features section, update the feature's link
     to its new path (`epic-<epic-slug>/feature-<feature-slug>/prd.md`).

8. **`artifacts/epics.md` stays untouched on a move**
   - It indexes epics only, not features, so reassigning a feature
     between epics never requires editing it. Only editing an epic's
     title or status (not covered by this skill) would.

## Notes

- This skill never syncs to a tracker. `epic.md`'s `ado_id` and
  `last_synced` fields are populated by `qsbn-sync-to-tracker`, not here.
- Reject `prd` and `epics` as epic slugs too, for the same reason they're
  reserved as feature slugs (collision with the two root files one level
  up).
