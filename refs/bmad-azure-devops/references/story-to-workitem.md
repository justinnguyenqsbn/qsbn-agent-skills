# Story File → Azure DevOps User Story Field Mapping

This is the canonical mapping used by `bmad-azure-devops`. When the story file format changes, update this reference first, then the skill body.

## Field map

| Azure DevOps field | Source in `story-N.M-slug.md` | Notes |
|---|---|---|
| `System.Title` | First `# ` heading, after stripping `Story X.Y: ` prefix, then prepending `[<feature-prefix>] ` if a prefix is configured for this story | Trim whitespace. Do not include trailing period. Feature prefix is the short bracket-tag (e.g. `[UF]` for User Feedback) cached in the mapping file's `Feature Prefix` column; when empty, the title has no bracket prefix at all. |
| `System.Description` | HTML of the `## Story` section + a "Source" link paragraph pointing back to the story file | See "Description body" below. |
| `Microsoft.VSTS.Common.AcceptanceCriteria` | `## Acceptance Criteria` section only | Convert each numbered AC into one `<li>` with `<br>` between Given/When/Then. |
| `System.AreaPath` | AGENTS.md `area_path` | Use backslash separator: `ChatMate365\Backend` not `/`. |
| `System.IterationPath` | AGENTS.md `iteration_path` (optional) | If blank, omit the flag — Azure DevOps falls back to team default. |
| Parent link (relation `System.LinkTypes.Hierarchy-Reverse`) | AGENTS.md `default_parent_feature_id` | Added via `az boards work-item relation add --relation-type parent`. |
| `System.Tags` | Optional — pull from story frontmatter `tags:` if present | Semicolon-separated in AzDO. |
| `System.State` | **NOT mapped.** | Never change state during sync. Treat as out-of-band. |

### Sections deliberately excluded from the work item

The following sections of the story file are **not** copied to Azure DevOps:

- `## Tasks / Subtasks` — implementation checklist, owned by the dev workflow.
- `## Dev Notes`, `### Project Structure Notes` — internal context for the implementer; pollutes the backlog view.
- `### References` — covered by the Source link in the Description.
- `Status:` line — never auto-translate to AzDO State.

If a reviewer needs any of the above, they open the linked story file. Keeping the work item focused on narrative + AC makes the backlog scannable.

### Description body

The Description has exactly two blocks:

1. The `## Story` section rendered as HTML (under an `<h2>Story</h2>` heading).
2. A trailing `<p>` paragraph: `<p><em>Source: <a href="<relative-path>"><relative-path></a></em></p>`.

Use the story file path relative to the repo root (e.g. `_bmad-output/implementation-artifacts/story-9.2-hybrid-search-parallel.md`). The path renders as plain text in AzDO if the repo is not browsable, but it is the canonical reference users can paste into their editor or Git tooling.

## Title extraction example

Step 1 — strip the `Story X.Y:` prefix from the markdown heading. This part is mechanical and uses the same regex regardless of which story you're syncing.

Input markdown:

```
# Story 9.2: Parallel Hybrid Search (Keyword + Vector)
```

Bare title:

```
Parallel Hybrid Search (Keyword + Vector)
```

Regex (illustrative): `^#\s+Story\s+\d+\.\d+:\s+(.+?)\s*$`

Step 2 — apply the feature prefix from the mapping file's `Feature Prefix` column (or the user's prompt answer when the row is new). The prefix wraps in `[ ]` and joins the bare title with a single space.

| Bare title | Feature Prefix | `System.Title` |
|---|---|---|
| `Parallel Hybrid Search (Keyword + Vector)` | *(empty)* | `Parallel Hybrid Search (Keyword + Vector)` |
| `Web Feedback Capture + Event Grid Publication` | `UF` | `[UF] Web Feedback Capture + Event Grid Publication` |
| `Admin Feedback Metrics Dashboard` | `UF` | `[UF] Admin Feedback Metrics Dashboard` |

The prefix is per-story (cached in the mapping file), not derived from the story file path or the epic number, because BMAD epics and Azure DevOps features don't always line up 1:1.

## HTML conversion rules

Description and AcceptanceCriteria are stored as HTML. Convert the relevant markdown sections with these transforms. Fidelity beats prettiness — readers will open the work item in the AzDO web UI which renders the HTML directly.

| Markdown | HTML |
|---|---|
| `## Heading` | `<h2>Heading</h2>` |
| `### Heading` | `<h3>Heading</h3>` |
| Paragraph text | `<p>text</p>` |
| `- item` (bullet list) | `<ul><li>item</li>...</ul>` |
| `1. item` (numbered list) | `<ol><li>item</li>...</ol>` |
| `- [ ] item` (task checkbox) | `<ul><li>☐ item</li>...</ul>` — AzDO does not render GFM task syntax. |
| `**bold**` | `<strong>bold</strong>` |
| `*italic*` or `_italic_` | `<em>italic</em>` |
| Inline `` `code` `` | `<code>code</code>` |
| Fenced code block ` ```lang ` | `<pre><code>...</code></pre>` with `<`, `>`, `&` HTML-escaped |
| `[label](url)` | `<a href="url">label</a>` |
| Blank line | New `<p>` paragraph |

### Acceptance Criteria special case

BMAD ACs use the Given/When/Then triplet inside one numbered item:

```markdown
1. **Given** a user query
   **When** the search function executes
   **Then** two Azure AI Search requests are issued concurrently...
```

Render as one `<li>`:

```html
<li><strong>Given</strong> a user query<br>
<strong>When</strong> the search function executes<br>
<strong>Then</strong> two Azure AI Search requests are issued concurrently...</li>
```

This keeps the AzDO Acceptance Criteria pane readable as a single numbered list rather than splitting Given/When/Then into separate items.

## Passing HTML to Azure DevOps

Push Description + Acceptance Criteria HTML to Azure DevOps **only** via `az devops invoke --in-file <body.json>` with a JSON Patch document. This is the canonical transport for both CREATE and UPDATE in this skill — see SKILL.md "Transport rule: Azure DevOps CLI only, never `az rest`" for the rationale (auth path divergence + Windows `cmd.exe` 8,191-char limit + shell-quoting hazards).

Build a JSON Patch body file and POST/PATCH it:

```jsonc
// body.json
[
  { "op": "add", "path": "/fields/System.Title",                              "value": "Parallel Hybrid Search (Keyword + Vector)" },
  { "op": "add", "path": "/fields/System.Description",                        "value": "<div><h2>Story</h2><p>As a developer…</p>…</div>" },
  { "op": "add", "path": "/fields/Microsoft.VSTS.Common.AcceptanceCriteria",  "value": "<div><ol><li><strong>Given</strong>…</li></ol></div>" }
]
```

UPDATE existing work item:

```bash
az devops invoke --area wit --resource workitems \
  --route-parameters id=26165 \
  --api-version 7.1 \
  --media-type application/json-patch+json \
  --http-method PATCH \
  --in-file body.json
```

CREATE new User Story (note: plain `User Story` route value, no leading `$`):

```bash
az devops invoke --area wit --resource workitems \
  --route-parameters type="User Story" \
  --api-version 7.1 \
  --media-type application/json-patch+json \
  --http-method POST \
  --in-file body.json
```

Body-file hygiene:

- Write UTF-8 without BOM. PowerShell: `[System.IO.File]::WriteAllText($path, $json, [System.Text.UTF8Encoding]::new($false))`.
- Encode characters above ASCII as HTML entities inside the HTML strings (e.g. `&#128077;` for 👍). The JSON itself stays pure ASCII, which sidesteps the Windows cp1252 console codec exploding when `az` prints the response.
- The JSON encoder handles all `&` / `<` / `>` / backtick / quote escaping for you. Do not hand-escape.

Inline `az boards work-item update --description "<html>" --fields "Microsoft.VSTS.Common.AcceptanceCriteria=<html>"` is **not** supported for this skill — it fails on Windows once the HTML grows past ~8 KB combined and is brittle under PowerShell/bash quoting. If a future call genuinely needs to keep using `az boards` for a short field update, on Windows you can bypass the `az.cmd` wrapper by invoking the Python entry directly to lift the limit to ~32 KB:

```powershell
& "C:\Program Files\Microsoft SDKs\Azure\CLI2\python.exe" -IBm azure.cli `
  boards work-item update --id 26165 `
  --fields "Microsoft.VSTS.Common.AcceptanceCriteria=$ac"
```

Treat that as a tactical escape hatch, not the default path. Never reach for `az rest`.

## Parent re-parenting

To change parent feature:

1. List existing relations: `az boards work-item relation show --id <ID>` (or via `az devops invoke` for relation index).
2. Remove the existing parent: `az boards work-item relation remove --id <ID> --relation-type parent --target-id <OLD_PARENT_ID>`.
3. Add the new parent: `az boards work-item relation add --id <ID> --relation-type parent --target-id <NEW_PARENT_ID>`.

If the existing parent already matches `default_parent_feature_id`, skip both calls.
