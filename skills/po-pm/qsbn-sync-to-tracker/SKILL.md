---
name: qsbn-sync-to-tracker
description: Create or update a feature's epic and stories as work items in the configured tracker. Only Azure DevOps is implemented; other targets are recognized but do nothing yet.
disable-model-invocation: true
---

# qsbn Sync to Tracker

Push a feature's epic and stories to the configured issue tracker,
creating new work items or updating already-synced ones in place. This is
the real sync logic — `qsbn-sync-to-ado` is a thin alias over this skill.

## Why this skill works the way it does

- Each story's own frontmatter (`ado_id`, `last_synced`) is the create-vs-update
  source of truth — there's no separate mapping file to keep in sync,
  because the story file already carries its own state. Querying the
  tracker to answer "does this already exist?" would be slower and
  fragile (titles change, IDs aren't in the markdown until we write them
  back).
- A story's parent in the tracker is always **that feature's own epic** —
  never a statically configured "default parent" work item. The epic is
  synced first (step 3), in the same run, so its `ado_id` is always fresh
  before any story tries to parent to it. If a feature gets reassigned to
  a different epic (via `qsbn-propose-epic`), re-syncing detects the
  mismatch and re-parents automatically (step 4, UPDATE path) — there's
  nothing to configure and nothing that can go stale.

## Workflow

1. **Resolve the feature and target**
   - Take `$ARGUMENTS` as a feature slug, epic ID, or path under
     `artifacts/epic-*/feature-*/`. It must already be epic-assigned (has
     stories under `epic-<epic-slug>/feature-<feature-slug>/`) — if not,
     tell the user to run `/qsbn:user-stories` first.
   - Resolve the target tracker: an explicit `--target <tracker>` flag if
     given, otherwise `tracker` from `.qsbn/config.toml`.
   - If the resolved target is `github`, `linear`, or `local`: stop and
     tell the user plainly that only `azure-devops` has a working sync
     implementation right now — do not attempt a partial sync, do not
     guess at an API call for an unimplemented backend.

2. **Read the feature's current state**
   - Read the epic's `epic.md` frontmatter (`id`, `ado_id`, `status`) and
     every `stories-*.md` file's frontmatter (`id`, `ado_id`) under that
     feature's folder.
   - Confirm the CLI is ready: `az account show` succeeds and
     `az devops configure --list` shows `organization`/`project` matching
     `.qsbn/config.toml`'s `[ado]` values. If not, tell the user to run
     `az login` and/or `az devops configure --defaults organization=...
     project=...` themselves — this skill never handles credentials.

3. **Sync the epic**
   - Epic content is short (title only, no long HTML fields), so plain
     `az boards` commands are fine here — see the transport rule below
     for why that changes once we get to stories.
   - `ado_id` is `null` → create it:
     ```bash
     az boards work-item create \
       --org https://dev.azure.com/<ado.organization> \
       --project "<ado.project>" \
       --type "Epic" \
       --title "<epic title>"
     ```
     Record the returned `id` as `ado_id`, and today's date/time as
     `last_synced`, in `epic.md`'s frontmatter. Set `status: synced`.
   - `ado_id` is already set → update it in place:
     ```bash
     az boards work-item update \
       --org https://dev.azure.com/<ado.organization> \
       --id <ado_id> \
       --title "<epic title>"
     ```
     Refresh `last_synced`.

4. **Sync each story**
   - Parse the story file and build its Azure DevOps fields following
     `references/story-field-mapping.md` — title (stripping the leading
     `<n>. ` numbering, keeping the `[<feature-slug>]` tag that
     `qsbn-user-stories` already baked into the title), Description
     (the As-a/I-want/So-that block + a source link back to the story
     file), and Acceptance Criteria (the Given/When/Then bullets).
   - Because Description and Acceptance Criteria are HTML fields that can
     easily exceed a few KB, push them via a JSON Patch body file through
     `az devops invoke`, never inline `--fields` on `az boards`, and never
     `az rest`. See `references/azure-devops-transport.md` for exactly
     why (auth-path divergence, Windows `cmd.exe`'s ~8,191-char limit,
     shell-quoting hazards) and the exact command forms.
   - `ado_id` is `null` → **create**: POST the JSON Patch body (Title,
     Description, AcceptanceCriteria, AreaPath, IterationPath, Tags),
     read the new `id` from the response, then add the parent relation
     to the epic's `ado_id` (the one just synced in step 3 — never a
     configured default). Record `ado_id` and `last_synced` in the
     story's frontmatter.
   - `ado_id` already set → **update**: PATCH the same fields. Then check
     for parent drift: read the story's current parent relation from
     Azure DevOps and compare it to the epic's `ado_id` from step 3. If
     they differ (the feature was moved to a different epic since the
     last sync), remove the stale parent relation and add the correct
     one — see `references/story-field-mapping.md`'s re-parenting
     section. Refresh `last_synced`.

5. **Report the summary**
   - Print a plain count: epics created/updated, stories created,
     stories updated, and any re-parenting that happened. No further
     confirmation gate beyond this summary — the create-vs-update
     decision in steps 3-4 already reflects intent.

## Safety rules

- **Never call `az rest` for Azure DevOps endpoints.** Use `az boards` /
  `az devops invoke` only — see `references/azure-devops-transport.md`.
  If the user explicitly insists on `az rest`, surface this rule and
  confirm before doing it.
- Never change a work item's **State**. State transitions trigger board
  automations and may notify other people; nothing in this skill's model
  needs to touch it.
- Never delete a work item. If a story file is removed from the qsbn
  workspace, leave the Azure DevOps item alone and flag it to the user.
- Never touch a work item whose ID isn't already recorded in that
  story's/epic's own frontmatter, even if a title match suggests it's
  the same one — title collisions happen, frontmatter `ado_id` doesn't
  lie.

## Notes

- Authentication is external (`az login`), checked by `qsbn-setup` — this
  skill assumes it's already in place and surfaces the CLI's own error if
  not, rather than trying to detect or fix login state itself.
- `github`, `linear`, and `local` targets are recognized in config for
  forward compatibility but have no client behind them yet — don't
  implement partial/best-effort behavior for them.

## References

- `references/azure-devops-transport.md` — the JSON Patch / `az devops
  invoke` transport rule: why, exact command forms, Windows caveats.
- `references/story-field-mapping.md` — field-by-field mapping from a
  story file to Azure DevOps fields, HTML conversion rules, title
  parsing, and the re-parenting flow.
