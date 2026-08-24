# Azure DevOps Transport — CLI Only, Never `az rest`

All Azure DevOps API calls in this skill go through the Azure DevOps CLI
extension — `az boards ...` for short, simple field operations and
`az devops invoke ...` for anything that needs to carry HTML content.
**Do not use `az rest` for Azure DevOps endpoints.**

## Why this matters

- **Auth path divergence.** `az rest` resolves tokens via the MSAL cache
  populated by `az login`. The `az devops` extension uses a separate
  cached credential (PAT or AAD token kept by the extension). On a
  machine where `az boards work-item show` works but `az login` hasn't
  been refreshed against the current cloud tenant, `az rest` fails with
  `User '<email>' does not exist in MSAL token cache. Run 'az login'.`
  while the extension keeps working. The extension is the path that
  survives normal day-to-day auth state.
- **Windows `cmd.exe` argument length cap.** On Windows, `az` runs
  through `az.cmd`, which goes through `cmd.exe`. The full command line
  is capped at ~8,191 characters. A single story's Description +
  Acceptance Criteria HTML routinely exceeds this. Passing it inline via
  `az boards work-item create --description "..." --fields
  "Microsoft.VSTS.Common.AcceptanceCriteria=..."` fails with `The
  command line is too long.` even though the strings are individually
  valid. The fix is a JSON Patch document loaded from a file via
  `az devops invoke --in-file ...`, which is exactly what the work-items
  REST API accepts.
- **Quoting hazards in `--fields`.** `--fields "key=value"` becomes
  unreadable for multi-kilobyte HTML containing `&`, `<`, `>`, backticks,
  and emoji — inline quoting mangles different characters differently
  across PowerShell/cmd/bash. A JSON Patch body file removes all of
  this; the JSON encoder handles escaping once, deterministically.

## Rule of thumb

| Operation | Use |
|---|---|
| Read a work item, list relations, query by WIQL, add/remove a parent link, simple field tweak (short title, tag) | `az boards work-item show` / `relation add` / `relation remove` / `update` / `az boards query` — direct, no body file needed |
| Create or update a story with full Description + Acceptance Criteria HTML | `az devops invoke --area wit --resource workitems --http-method POST/PATCH --in-file <body>.json --media-type application/json-patch+json` |
| Any work-item call where the inline command would exceed ~7,000 chars | `az devops invoke` with `--in-file` |
| Azure DevOps REST endpoints, ever | **Never** `az rest` |

If a future call has no `az boards` equivalent, fall back to
`az devops invoke`, never to `az rest`. If the user explicitly requests
`az rest`, surface this rule and ask them to confirm before proceeding.

## Building the JSON Patch body

```jsonc
// body.json — JSON Patch (RFC 6902) consumed by the work-items REST API
[
  { "op": "add", "path": "/fields/System.Title",                             "value": "<TITLE>" },
  { "op": "add", "path": "/fields/System.AreaPath",                          "value": "<area_path>" },
  { "op": "add", "path": "/fields/System.IterationPath",                     "value": "<iteration_path>" },
  { "op": "add", "path": "/fields/System.Description",                       "value": "<HTML_DESCRIPTION>" },
  { "op": "add", "path": "/fields/Microsoft.VSTS.Common.AcceptanceCriteria", "value": "<HTML_AC>" },
  { "op": "add", "path": "/fields/System.Tags",                              "value": "<tags.story>" }
]
```

- Omit the `System.IterationPath` line if `.qsbn/config.toml`'s
  `[ado].iteration_path` is blank — Azure DevOps falls back to the
  team's default iteration.
- For UPDATE, all of the above are optional to include — send only the
  fields that changed. Title/Description/AcceptanceCriteria are the
  typical set.
- Write the file as UTF-8 without BOM.
- Use HTML entities (e.g. `&#128077;` for 👍) for anything above ASCII
  inside the HTML strings, keeping the JSON body itself pure ASCII —
  this sidesteps Windows console cp1252 encoding issues when `az` prints
  the response.

## CREATE

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

- `project=<project>` **must** be passed as a `--route-parameters`
  entry. `az devops configure --defaults project=...` only applies to
  top-level `--project` flags, not to invoke route placeholders —
  omitting it makes the extension fall back to an org-scoped route
  template that doesn't exist for this endpoint, producing `The
  controller for path '/_apis/wit/workItems/<id>' was not found ...
  404`.
- `type` is the plain string `User Story`, no leading `$` — the extension
  supplies the `$` from the URL template itself. Passing `$User Story`
  double-prefixes and 404s. With `project=` supplied correctly, the
  extension URL-encodes the space to `User%20Story` and the call
  succeeds.
- Read the response's `id` field. If the response is hard to parse
  because `az` printed warnings into the output stream, fall back to:
  ```bash
  az boards query --wiql "SELECT [System.Id], [System.Title] FROM WorkItems WHERE [System.Title] = '<TITLE>' ORDER BY [System.Id] DESC" --output json
  ```
  and take the highest `id` matching the title just created.
- Add the parent relation as a separate call (not part of the JSON
  Patch body):
  ```bash
  az boards work-item relation add \
    --id <NEW_ID> \
    --relation-type parent \
    --target-id <epic-ado-id>
  ```

## UPDATE

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

Same `project=` route-parameter requirement as CREATE.

## Windows escape hatch (tactical, not default)

If a future short field update genuinely needs to stay on `az boards`
but still blows past the `cmd.exe` limit, bypass `az.cmd` and call the
Python entry directly — this lifts the cap to the ~32,767-char
`CreateProcess` limit instead:

```powershell
& "C:\Program Files\Microsoft SDKs\Azure\CLI2\python.exe" -IBm azure.cli `
  boards work-item update --id 12345 `
  --fields "Microsoft.VSTS.Common.AcceptanceCriteria=$ac"
```

Prefer the `az devops invoke --in-file` path for anything that may grow
over time — treat this as an escape hatch, not the default.
