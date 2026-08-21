---
name: qsbn-sync-to-tracker
description: Create or update a feature's epic and stories as work items in the configured tracker. Only Azure DevOps is implemented; other targets are recognized but do nothing yet.
disable-model-invocation: true
---

# qsbn Sync to Tracker

Push a feature's epic and stories to the configured issue tracker,
creating new work items or updating already-synced ones in place. This is
the real sync logic — `qsbn-sync-to-ado` is a thin alias over this skill.

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

3. **Sync the epic**
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
   - For each story, `ado_id` is `null` → create it as a User Story, tag
     it with `tags.story` from config, and link it as a child of the
     epic's `ado_id`:
     ```bash
     az boards work-item create \
       --org https://dev.azure.com/<ado.organization> \
       --project "<ado.project>" \
       --type "User Story" \
       --title "<story title>" \
       --fields "Tags=<tags.story>"

     az boards work-item relation add \
       --org https://dev.azure.com/<ado.organization> \
       --id <new-story-ado-id> \
       --relation-type parent \
       --target-id <epic-ado-id>
     ```
     Record the returned `id` as that story's `ado_id`, refresh
     `last_synced` in its frontmatter.
   - `ado_id` already set → update it in place (title, description if
     changed) via `az boards work-item update --id <ado_id> ...`. Refresh
     `last_synced`. Don't re-add the parent relation — it's already
     there from the original create.

5. **Report the summary**
   - Print a plain count: epics created/updated, stories created,
     stories updated. No further confirmation gate beyond this summary —
     the create-vs-update decision in steps 3-4 already reflects intent.

## Notes

- Authentication is external (`az login`), checked by `qsbn-setup` — this
  skill assumes it's already in place and surfaces the CLI's own error if
  not, rather than trying to detect or fix login state itself.
- `github`, `linear`, and `local` targets are recognized in config for
  forward compatibility but have no client behind them yet — don't
  implement partial/best-effort behavior for them.
