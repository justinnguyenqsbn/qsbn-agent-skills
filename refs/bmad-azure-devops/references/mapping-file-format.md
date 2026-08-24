# Mapping File Format — `azure-devops.md`

Path: `_bmad-output/implementation-artifacts/azure-devops.md`

This file is the local source of truth for "does an Azure DevOps work item already exist for this BMAD story?" The skill consults it before issuing any `az` commands, so a correct mapping file means zero create-or-update queries against Azure DevOps.

## File structure

The file has exactly two sections: a short header explaining its purpose, and one markdown table. Nothing else.

```markdown
# BMAD ↔ Azure DevOps Story Map

Single source of truth for whether a `story-*.md` file is already mirrored to Azure DevOps. Maintained by the `bmad-azure-devops` skill — do not edit by hand unless reconciling a known drift.

| Story File | Work Item ID | Title | Parent Feature ID | Feature Prefix | Last Synced (UTC) |
|---|---|---|---|---|---|
| story-9.2-hybrid-search-parallel.md | 26165 | Parallel Hybrid Search (Keyword + Vector) | 26015 |  | 2026-05-18 |
| story-10.1-followup-cot-spike.md | 26301 | Follow-up CoT Spike | 26015 |  | 2026-05-18 |
| story-1.1-web-feedback-capture.md | 26701 | [UF] Web Feedback Capture + Event Grid Publication | 26015 | UF | 2026-05-20 |
```

## Column contract

| Column | Type | Required | Notes |
|---|---|---|---|
| Story File | string (basename) | yes | Just the filename, no directory. All stories live in `_bmad-output/implementation-artifacts/`. |
| Work Item ID | integer | yes | Azure DevOps numeric ID. Quote-free. |
| Title | string | yes | The Azure DevOps title cached for human auditing — already includes the `[<prefix>]` bracket-tag when one is set. AzDO is authoritative; this column is a cache. |
| Parent Feature ID | integer | yes | The Feature this story was last parented to. Used to detect "config changed parent feature, need to re-parent." |
| Feature Prefix | string (bare tag, no brackets) | no | Short feature tag (e.g. `UF` for User Feedback) that gets wrapped in `[ ]` and prepended to the work-item Title. Empty cell = no prefix. Set by the user the first time a story is synced; never auto-derived. |
| Last Synced (UTC) | ISO date `YYYY-MM-DD` | yes | When this row was last written by the skill. Auditing only. |

Add new columns by extending the table — but never reorder existing ones, and never rename column headers, since the skill parses by position and header name.

## Update rules

- **New story**: append a row. Do not sort. Populate `Feature Prefix` from the user's prompt answer (blank if they chose no prefix).
- **Existing story, content refreshed**: rewrite the row in place. Update `Title` and `Last Synced`; leave `Work Item ID`, `Parent Feature ID`, and `Feature Prefix` unchanged unless the user explicitly asks to change them.
- **Existing story, parent feature changed in AGENTS.md**: rewrite `Parent Feature ID` after the re-parent call succeeds. If the re-parent call fails, leave the column as-is — the file must reflect reality.
- **Story file renamed in BMAD**: rewrite the `Story File` column to the new basename. Do not create a second row.
- **Story file deleted from BMAD**: do not delete the row. Flag it to the user; leave the row for traceability.

## Conflict detection

Before writing, sanity-check:

1. The `Title` in the table matches the title parsed from the story file. If it doesn't, this is likely a Title field drift in Azure DevOps — ask the user whether to overwrite the AzDO title or update the local file.
2. The `Parent Feature ID` matches the configured `default_parent_feature_id`. If it doesn't, the configured parent has changed since the last sync — execute the re-parent flow described in `story-to-workitem.md`.

Both checks are cheap; perform them on every update.

## Why not query Azure DevOps directly

Querying AzDO with `az boards query` works but has three costs:

1. Slow — every sync needs a round-trip even when nothing changed.
2. Title-based lookup is fragile — two stories with similar titles are indistinguishable.
3. Tag-based lookup needs a convention that has to be enforced in both directions.

The mapping file makes the relationship explicit, fast to read, and committable alongside the story files themselves so the BMAD workspace remains self-contained.

## Example: first-time bootstrap

If `azure-devops.md` doesn't exist when the skill runs, create it with the header above and an empty table:

```markdown
# BMAD ↔ Azure DevOps Story Map

Single source of truth for whether a `story-*.md` file is already mirrored to Azure DevOps. Maintained by the `bmad-azure-devops` skill — do not edit by hand unless reconciling a known drift.

| Story File | Work Item ID | Title | Parent Feature ID | Feature Prefix | Last Synced (UTC) |
|---|---|---|---|---|---|
```

The next sync will append the first real row.
