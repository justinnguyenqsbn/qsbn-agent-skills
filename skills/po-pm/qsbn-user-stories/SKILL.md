---
name: qsbn-user-stories
description: Write INVEST-checked user stories with Given/When/Then acceptance criteria for a feature already assigned to an epic. Built-in only — never delegates to a third-party story-writing skill.
disable-model-invocation: true
---

# qsbn User Stories

Break a feature's PRD into user stories. Always runs its own logic below —
never checks `.qsbn/config.toml` preferences and never delegates to
`/user-story`, `bmad-create-epics-and-stories`, or any other third-party
skill, regardless of what's installed.

## Workflow

1. **Resolve the feature**
   - Take `$ARGUMENTS` as a path to a feature's `prd.md` or a feature
     slug. It must resolve to `artifacts/epic-<epic-slug>/feature-<feature-slug>/prd.md`
     — i.e. already assigned to an epic. If it's still sitting at
     `artifacts/<feature-slug>/` (unassigned), stop and tell the user to
     run `/qsbn:propose-epic` first; don't write stories for an
     unassigned feature.
   - Read the feature's `prd.md` and its epic's `epic.md` for context.

2. **Draft stories**
   - Decompose the feature into vertical slices, each completable in
     roughly 1-3 days, each delivering end-to-end value on its own.
   - Apply INVEST: Independent, Negotiable, Valuable, Estimable, Small,
     Testable. Format: "As a [persona], I want to [action], so that
     [benefit]."
   - Each story must be a demoable, meaningful slice of a user's
     journey — something a stakeholder could watch happen end-to-end.
     Don't cut stories along technical layers (e.g. "build the database
     schema" is not a story). A technical-only story (infra, migration,
     no direct demo) is the exception, not the norm: use one only when
     there's a genuine non-demoable prerequisite that can't be reframed
     as user-facing, and treat that as a deliberate call, not a default
     taken for convenience.

3. **Write acceptance criteria per story**
   - Given/When/Then format, 3-7 criteria per story.
   - Cover the happy path, at least one edge case, and at least one error
     state.

4. **Add story metadata**
   - Priority: must-have, should-have, or nice-to-have.
   - Dependencies on other stories from this same feature, if any.

5. **Write one file per story**
   - Path: `artifacts/epic-<epic-slug>/feature-<feature-slug>/stories-<n>-<short-description>.md`,
     `<n>` numbered in implementation order starting at 1,
     `<short-description>` a few kebab-case words.
   - Content:
     ```markdown
     ---
     id: STORY-<feature-slug>-<n>
     epic_id: EPIC-<epic-slug>
     ado_id: null
     last_synced: null
     ---

     # <n>. [<feature-slug>] <Story title>

     **As a** <persona>
     **I want to** <action>
     **So that** <benefit>

     ## Acceptance Criteria

     - Given ..., when ..., then ...
     - ...

     ## Details

     - Priority: must-have | should-have | nice-to-have
     - Dependencies: <story IDs, or "none">
     ```
     For the technical-only exception from step 2, the title becomes
     `# <n>. [<feature-slug>] [TECH] <Story title>`.

6. **Summarize**
   - After writing all files, list them with a one-line description each,
     the suggested implementation order, and which stories form the MVP
     subset (deliver the core value with the fewest stories).

## Notes

- This skill never syncs to a tracker — `ado_id` and `last_synced` stay
  `null` until `qsbn-sync-to-tracker` runs.
- This skill never touches `epic.md`'s Features section or
  `artifacts/epics.md` — those are `qsbn-propose-epic`'s responsibility.
