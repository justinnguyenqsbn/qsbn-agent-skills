---
name: qsbn-to-spec
description: Turn a confirmed feature (PRD + epic + stories) into an implementation spec of concrete tasks. Delegates to a configured third-party spec-writing skill if set in preferences, otherwise runs its own built-in breakdown.
disable-model-invocation: true
---

# qsbn To Spec

Read the business-level artifacts for a feature and produce an
implementation-level task breakdown — never the reverse; this skill does
not write to `artifacts/`.

## Workflow

1. **Resolve the feature**
   - Take `$ARGUMENTS` as an ADO ticket ID, a qsbn feature/story ID (e.g.
     `EPIC-<slug>`, `STORY-<feature-slug>-<n>`), or a feature name/slug.
   - Resolution order: match `ado_id` in any `epic.md`/`stories-*.md`
     frontmatter under `artifacts/epic-*/` → match `id` the same way →
     fall back to a feature-slug match on
     `artifacts/epic-*/feature-<slug>/`.
   - If nothing matches, or the feature has no stories yet, stop and tell
     the user — don't guess at scope from the identifier alone.

2. **Gather context**
   - Read the feature's `prd.md`, its epic's `epic.md`, and every
     `stories-*.md` file under that feature's folder.

3. **Check delegation preference**
   - Read `.qsbn/config.toml`'s `preferences.writing_spec`.
   - If it names a third-party skill (`superpowers`), invoke that skill
     now with the gathered context instead of continuing below, and stop
     once it finishes.
   - If it's `built-in` (or the config/field doesn't exist), continue to
     step 4.

4. **Built-in task breakdown**
   - For each story, list the concrete implementation tasks needed to
     satisfy its acceptance criteria: which files/modules are touched,
     what the new or changed behavior is, and which of the story's
     Given/When/Then criteria each task addresses.
   - Order tasks so each is independently completable and testable —
     vertical slices, not "all models then all views."
   - Flag any task whose scope depends on code you haven't seen yet as
     needing investigation first, rather than guessing.

5. **Write the spec**
   - Path: `specs/<feature-slug>/spec.md` (create `specs/` and the
     feature subfolder if needed).
   - Content:
     ```markdown
     # Spec: <Feature Title>

     Source: artifacts/epic-<epic-slug>/feature-<feature-slug>/

     ## Tasks

     ### 1. <task title>
     - Addresses: STORY-<feature-slug>-<n>, criterion "..."
     - Files: ...
     - Notes: ...

     ### 2. ...

     ## Open Questions
     - ...
     ```

## Notes

- This is the only qsbn skill besides `qsbn-tdd` with a delegation
  branch. `qsbn-prd` and `qsbn-user-stories` never check preferences.
- Never writes anywhere under `artifacts/` — that tree is business-level
  and owned by the PO/PM pipeline skills.
