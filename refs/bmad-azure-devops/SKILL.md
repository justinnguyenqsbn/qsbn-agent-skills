---
name: bmad-azure-devops
description: Sync BMAD story files from `_bmad-output/implementation-artifacts/story-*.md` to Azure DevOps as User Stories, creating new work items or updating existing ones based on a local mapping file. Use whenever the user says "create user story in Azure DevOps", "update user story in Azure DevOps", "sync story X.Y to Azure DevOps", "push story to AzDO", or asks to mirror a BMAD story file into the Azure DevOps backlog. Reads project/feature/area config from AGENTS.md and uses the local mapping file `_bmad-output/implementation-artifacts/azure-devops.md` to decide create-vs-update without querying Azure DevOps. All Azure DevOps calls go through the `az boards` / `az devops invoke` commands (the Azure DevOps CLI extension) — never `az rest`.
---

# bmad-azure-devops

Mirror BMAD story files (`_bmad-output/implementation-artifacts/story-*.md`) into Azure DevOps as User Stories under a configured Feature, using a local mapping file as the source of truth for what already exists.

## Why this skill exists

- BMAD stores stories as markdown. Azure DevOps stores them as work items. Without a sync layer the two drift.
- Querying Azure DevOps every time to discover "does this story exist?" is slow and brittle (titles change, IDs are not in the markdown). A local mapping file pins each story file to a work-item ID.
- Only this skill should write to that mapping file. Treat it as the boundary between the BMAD workspace and Azure DevOps.

## Transport rule: Azure DevOps CLI only, never `az rest`

All Azure DevOps API calls in this skill go through the Azure DevOps CLI extension — `az boards ...` for high-level work-item operations and `az devops invoke ...` for any raw REST call that the high-level commands do not cover. **Do not use `az rest` for Azure DevOps endpoints.**

Why this matters (learned the hard way):

- **Auth path divergence.** `az rest` resolves tokens via the MSAL cache populated by `az login`. The `az devops` extension uses a separate cached credential (PAT or AAD token kept by the extension). On developer machines where `az boards work-item show` works but `az login` has not been refreshed against the current cloud tenant, `az rest` fails with `User '<email>' does not exist in MSAL token cache. Run 'az login'.` while the extension keeps working. The extension is the path that survives normal day-to-day auth state.
- **Windows `cmd.exe` argument length cap.** On Windows, `az` is invoked through `az.cmd`, which goes through `cmd.exe`. The full command line is limited to ~8,191 characters. A single User Story's description + acceptance criteria HTML routinely exceeds this. Trying to pass the HTML inline via `az boards work-item create --description "..." --fields "Microsoft.VSTS.Common.AcceptanceCriteria=..."` fails with `The command line is too long.` even though the strings themselves are valid. The fix is to push large field content via a JSON Patch document loaded from a file by `az devops invoke --in-file ...`, which is exactly what the work-items REST API accepts.
- **Quoting hazards in `--fields`.** `--fields "key=value"` becomes unreadable for multi-kilobyte HTML containing `&`, `<`, `>`, backticks, and emoji. Inline quoting on PowerShell/cmd/bash mangles different characters in different ways. A JSON Patch body file removes all of this — the JSON encoder handles escaping once, deterministically.

**Rule of thumb:**

| Operation | Use |
|---|---|
| Read a work item, list relations, query by WIQL, add a parent link, simple field tweak (short title, state) | `az boards work-item show` / `relation add` / `update` / `az boards query` — direct, ergonomic, no body file needed |
| Create or update a User Story with full Description + Acceptance Criteria HTML (i.e. anything from this skill's CREATE / UPDATE step) | `az devops invoke --area wit --resource workitems --http-method POST/PATCH --in-file <json-patch-body>.json --media-type application/json-patch+json` |
| Any work-item operation where the inline command is >7,000 chars | `az devops invoke` with `--in-file` |
| Anything else for Azure DevOps | `az devops invoke` |
| Azure DevOps REST endpoints | **Never** `az rest` |

If a future call has no `az boards` equivalent, fall back to `az devops invoke`, never to `az rest`. If the user explicitly requests `az rest`, surface this rule and ask them to confirm before proceeding.

### Windows note: bypass the `cmd.exe` wrapper when args are long

Even within the rule above, a small number of `az boards` calls (e.g. `az boards work-item update --fields "Microsoft.VSTS.Common.AcceptanceCriteria=<long-html>"`) can blow past the `cmd.exe` 8,191-char limit. If you genuinely need to keep using `az boards` for one of those, on Windows you can bypass `az.cmd` and call the Python entry directly so the limit becomes the ~32,767-char `CreateProcess` cap instead:

```powershell
& "C:\Program Files\Microsoft SDKs\Azure\CLI2\python.exe" -IBm azure.cli `
  boards work-item update --id 12345 `
  --fields "Microsoft.VSTS.Common.AcceptanceCriteria=$ac"
```

Prefer the `az devops invoke --in-file` path for anything that may grow over time. The Python-direct trick is a tactical escape hatch, not the default.

## Configuration (read from AGENTS.md)

AGENTS.md contains an **Azure DevOps Integration** section. Read it first. Required keys:

| Key | Example | Notes |
|---|---|---|
| `organization` | `https://dev.azure.com/qsbnproducts` | Full URL, not legacy `*.visualstudio.com` |
| `project` | `ChatMate365` | Project name |
| `default_parent_feature_id` | `26015` | Work-item ID of the Feature new stories are parented to |
| `default_parent_feature_title` | `To Be Triaged / Refined` | For human readability only |
| `area_path` | `ChatMate365` | Use backslash-separated form when nested, e.g. `ChatMate365\Backend` |
| `iteration_path` | *(optional)* | Leave blank to inherit team backlog default |

If any required key is missing from AGENTS.md, stop and ask the user to add it. Do not guess.

## Mapping file

Path: `_bmad-output/implementation-artifacts/azure-devops.md`

Format — a single markdown table. One row per story file. Treat the table as authoritative for whether a work item already exists.

```markdown
# BMAD ↔ Azure DevOps Story Map

Single source of truth for whether a `story-*.md` file is already mirrored to Azure DevOps. Maintained by the `bmad-azure-devops` skill — do not edit by hand unless reconciling a known drift.

| Story File | Work Item ID | Title | Parent Feature ID | Feature Prefix | Last Synced (UTC) |
|---|---|---|---|---|---|
| story-9.2-hybrid-search-parallel.md | 26165 | Parallel Hybrid Search (Keyword + Vector) | 26015 |  | 2026-05-18 |
| story-1.1-web-feedback-capture.md | 26701 | [UF] Web Feedback Capture + Event Grid Publication | 26015 | UF | 2026-05-20 |
```

Rules:
- Story File column holds the file basename only (no path), since all stories live in the same directory.
- Work Item ID is the integer Azure DevOps ID.
- Feature Prefix is the short bracket-tag (e.g. `UF`) applied to the work-item Title. Empty cell = no prefix. Set by the user the first time a story is synced (see step 2). Cached here so future syncs don't re-prompt.
- Last Synced is the date (UTC) the row was last written by this skill — used only for human auditing.
- Never delete a row programmatically. If a story is renamed, update the row in place.

## Workflow

Given a target story file (e.g. `story-9.2-hybrid-search-parallel.md`):

### 1. Load config

- Read AGENTS.md, find the **Azure DevOps Integration** section, extract the keys above.
- Confirm the Azure CLI is authenticated. Run `az devops configure --list` once to confirm `organization` and `project` match the config; if they don't, run `az devops configure --defaults organization=... project=...` to align.

### 2. Parse the story file

Extract:
- **Bare title** — strip the leading `Story X.Y: ` from the first `# ` heading. Example: `# Story 1.1: Web Feedback Capture + Event Grid Publication` → bare title is `Web Feedback Capture + Event Grid Publication`. The `Story X.Y` prefix never lands in Azure DevOps — work-item IDs already give backlog ordering, and the prefix collides with the human-friendly feature tag described below.
- **Feature prefix** — a short bracket-tag (e.g. `[UF]` for the User Feedback feature) that prepends the title in Azure DevOps. Determined as follows:
  1. Look up the story file's row in the mapping file (step 3). If the `Feature Prefix` column is non-empty, use it.
  2. If the row is missing or the column is empty, **prompt the user**: `What feature prefix should this story use in Azure DevOps? (short tag, e.g. UF for User Feedback — leave blank for no prefix)`. Accept either the bare tag (`UF`) or the bracketed form (`[UF]`); normalise to bare tag for storage, bracketed form for the title.
  3. The user's answer is cached in the `Feature Prefix` column of the mapping row so future syncs of the same story don't re-prompt.
- **Final `System.Title`** — `[<prefix>] <bare title>` when a prefix is set; otherwise the bare title alone. Example with prefix `UF`: `[UF] Web Feedback Capture + Event Grid Publication`. Example with no prefix: `Parallel Hybrid Search (Keyword + Vector)`.
- **Story (narrative)** — the `## Story` section body. This is the only narrative section that lands in the work-item Description.
- **Acceptance Criteria** — the `## Acceptance Criteria` section body. Goes to the Acceptance Criteria field.
- **Source link** — append a single paragraph to the Description with a clickable reference back to the story file (relative repo path), so reviewers can open the BMAD spec for full context.

Do **NOT** include in the work item:
- `## Tasks / Subtasks` — implementation breakdown belongs in the dev workflow, not the backlog item.
- `## Dev Notes`, `### Project Structure Notes`, `### References` — internal notes; the source link covers traceability.
- `Status:` frontmatter / preamble — never auto-translate to Azure DevOps State (also see safety rule below).

### 3. Check the mapping file

- Open `_bmad-output/implementation-artifacts/azure-devops.md`. If it does not exist, create it from the template above (header + empty table).
- Look for a row whose Story File equals the target story file basename.
- **Row exists** → UPDATE path (step 4a).
- **Row missing** → CREATE path (step 4b).

Both CREATE and UPDATE push the Description and Acceptance Criteria HTML to Azure DevOps as a JSON Patch document loaded from a file via `az devops invoke`. Inline `--description` / `--fields` arguments on `az boards work-item create/update` are not safe for this content (see the transport rule above) and must not be used here.

### Build the JSON Patch body file

For both CREATE and UPDATE, first write a JSON Patch document to a temp file (any path is fine; using the OS temp directory keeps the workspace clean). The same payload structure works for both — `az devops invoke` chooses CREATE vs UPDATE based on `--http-method` and `--route-parameters` later.

```jsonc
// body.json — JSON Patch (RFC 6902) consumed by the Azure DevOps work-items REST API
[
  { "op": "add", "path": "/fields/System.Title",                                "value": "<TITLE>" },
  { "op": "add", "path": "/fields/System.AreaPath",                             "value": "<area_path>" },
  { "op": "add", "path": "/fields/System.IterationPath",                        "value": "<iteration_path>" },
  { "op": "add", "path": "/fields/System.Description",                          "value": "<HTML_DESCRIPTION>" },
  { "op": "add", "path": "/fields/Microsoft.VSTS.Common.AcceptanceCriteria",    "value": "<HTML_AC>" }
]
```

Notes:
- For UPDATE, the `System.AreaPath` / `System.IterationPath` lines are optional — include them only if you actually want to move the work item. Title/Description/AcceptanceCriteria are the typical UPDATE payload.
- Write the file as UTF-8 (no BOM). PowerShell `[System.IO.File]::WriteAllText($path, $json, [System.Text.UTF8Encoding]::new($false))` works; in Python any default UTF-8 write is fine.
- Use HTML entities (e.g. `&#128077;` for 👍) inside the HTML strings to keep the JSON body pure ASCII — this dodges the Windows cp1252 console encoding issues that come up when `az` prints anything to stdout.

### 4a. UPDATE existing work item

```bash
az devops invoke \
  --area wit --resource workitems \
  --route-parameters project=<project> id=<WORK_ITEM_ID> \
  --api-version 7.1 \
  --media-type application/json-patch+json \
  --http-method PATCH \
  --in-file <body.json> \
  --out-file <response.json>
```

`<project>` is the `project` value from AGENTS.md (e.g. `ChatMate365`). It MUST be passed as a `--route-parameters` entry — `az devops configure --defaults project=...` only applies to top-level `--project` flags, not to invoke route placeholders. Omitting it makes the extension fall back to an org-scoped route template that doesn't exist for this endpoint, producing `The controller for path '/_apis/wit/workItems/<id>' was not found ... 404`.

If the row's Parent Feature ID does not match config `default_parent_feature_id`, list the relations, remove the existing parent (`az boards work-item relation remove`), and add the new one (`az boards work-item relation add --relation-type parent --target-id <new-parent-id>`). See `references/story-to-workitem.md`.

Then update the mapping row's `Last Synced` column.

### 4b. CREATE new work item

```bash
az devops invoke \
  --area wit --resource workitems \
  --route-parameters project=<project> type="User Story" \
  --api-version 7.1 \
  --media-type application/json-patch+json \
  --http-method POST \
  --in-file <body.json> \
  --out-file <response.json>
```

`<project>` is the `project` value from AGENTS.md (e.g. `ChatMate365`). It MUST be passed as a `--route-parameters` entry — `az devops configure --defaults project=...` does NOT inject it into route placeholders. Omitting `project=` makes the extension fall back to an org-scoped template, concatenate the raw `type` value without URL-encoding the space, and produce:

```
ERROR: The controller for path '/_apis/wit/workItems/$User Story' was not found or does not implement IController.  Operation returned a 404 status code.
```

With `project=<project>` supplied, the extension matches the project-scoped template `POST /{project}/_apis/wit/workitems/${type}`, URL-encodes `User Story` → `User%20Story`, and the call succeeds.

The `type` route parameter is the plain string `User Story` — do NOT prefix it with `$`. The extension supplies the `$` from the URL template; passing `$User Story` double-prefixes and 404s.

Read the response's `id` field (it's a JSON document with the new work item). If the response file is hard to parse because `az` printed warnings into the output stream, fall back to:

```bash
az boards query --wiql "SELECT [System.Id], [System.Title] FROM WorkItems WHERE [System.Title] = '<TITLE>' ORDER BY [System.Id] DESC" --output json
```

and pick the highest `id` matching the title you just created. Then add the parent link:

```bash
az boards work-item relation add \
  --id <NEW_ID> \
  --relation-type parent \
  --target-id <default_parent_feature_id>
```

Append a new row to the mapping table.

### 5. HTML conversion

Description and AcceptanceCriteria are HTML fields in Azure DevOps. Convert the relevant markdown sections with these minimal rules — fidelity matters more than aesthetics:

- `## H2` → `<h2>H2</h2>`
- `### H3` → `<h3>H3</h3>`
- Bullet `- item` → `<ul><li>item</li>…</ul>`
- Numbered `1. item` → `<ol><li>item</li>…</ol>`
- `**bold**` → `<strong>bold</strong>`
- Inline `` `code` `` → `<code>code</code>`
- Blank line → paragraph break `</p><p>`
- Wrap final body in `<div>…</div>`

If the markdown contains a fenced code block, render as `<pre><code>…</code></pre>` and HTML-escape `<`, `>`, `&` inside it.

Keep AC as an ordered list — the first Given/When/Then triplet per AC item should be wrapped as a single `<li>` with `<br>` between Given/When/Then, so AzDO renders it as one numbered criterion.

### 6. Report back

After the operation, show:
- Action taken (created vs updated)
- Work item ID and direct link: `https://dev.azure.com/<org-slug>/<project>/_workitems/edit/<ID>`
- The mapping-file row that was written
- Any drift detected (e.g. existing parent feature differed from config, state was non-default)

## Bulk mode

If the user says "sync all stories" or names multiple stories:
- Process them sequentially (Azure CLI does not pipeline reliably across `az boards work-item` calls).
- Resolve feature prefixes **up front** — collect every story whose mapping row is missing or has an empty `Feature Prefix`, and prompt the user once with the full list (e.g. group by epic number to make the answer easy). This avoids interrupting the run mid-loop.
- Write the mapping file once at the end, not after each row, to keep the file edit count low.
- Report a summary table: file → action → ID → prefix applied.

## Safety rules

- **Never call `az rest` for Azure DevOps endpoints.** Use `az boards` / `az devops invoke`. See the Transport rule section for why; if the user explicitly insists on `az rest`, surface this rule and confirm before doing it.
- Never change a work item's **State** unless the user explicitly asks. State transitions in Azure DevOps trigger Board automations and may notify other people.
- Never delete a work item. If a story file is removed from the BMAD workspace, leave the AzDO item and the mapping row alone, and flag it for the user.
- Never touch work items whose IDs are not in the mapping file, even if a title match suggests they're the same story — title collisions are common in early backlogs.
- Push long content (Description, Acceptance Criteria) only via a JSON Patch file consumed by `az devops invoke --in-file`. Inline `--description` / `--fields` on `az boards work-item create/update` fails on Windows for non-trivial HTML (8,191-char `cmd.exe` limit) and is fragile under any shell's quoting rules.

## References

- `references/story-to-workitem.md` — End-to-end field mapping from `story-*.md` to Azure DevOps User Story fields, with HTML conversion examples.
- `references/mapping-file-format.md` — Full schema for `azure-devops.md`, including how to handle file renames and Feature re-parenting.
- `azure-devops-cli` skill (sibling) — Use its `references/boards-and-iterations.md` for the exact `az boards` / `az devops invoke` command syntax. The sibling skill is the only sanctioned source of transport syntax for this skill; do not introduce `az rest` calls from elsewhere.
