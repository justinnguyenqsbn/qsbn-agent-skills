# Story File → Azure DevOps Field Mapping

Canonical mapping used by `qsbn-sync-to-tracker` when pushing a
`stories-<n>-<description>.md` file to Azure DevOps as a User Story.

## Field map

| Azure DevOps field | Source in the story file | Notes |
|---|---|---|
| `System.Title` | The `# <n>. [<feature-slug>] <Story title>` heading, with the leading `<n>. ` numbering stripped | Keep the `[<feature-slug>]` bracket tag — `qsbn-user-stories` already baked it in, there's nothing to prompt for here (unlike a scheme that resolves the tag at sync time). |
| `System.Description` | HTML of the As-a/I-want/So-that block, plus a trailing source-link paragraph | See "Description body" below. |
| `Microsoft.VSTS.Common.AcceptanceCriteria` | The `## Acceptance Criteria` bullets | Each `- Given ..., when ..., then ...` bullet becomes one `<li>`. |
| `System.AreaPath` | `.qsbn/config.toml`'s `[ado].area_path` | Backslash-separated when nested, e.g. `MyProject\Backend`. |
| `System.IterationPath` | `.qsbn/config.toml`'s `[ado].iteration_path` (optional) | Omit the field entirely if blank — Azure DevOps falls back to the team's default iteration. |
| `System.Tags` | `.qsbn/config.toml`'s `[tags].story` | Applied on create only; leave alone on update unless the user asks to change it. |
| Parent link (`System.LinkTypes.Hierarchy-Reverse`) | The story's `epic_id`, resolved to that epic's `ado_id` (synced in the same run) | **Never** a configured default — see "Parent resolution" below. |
| `System.State` | **Not mapped.** | Never touched by a sync. |
| Priority, Dependencies (the story's "Details" section) | **Not mapped (for now).** | Stay local-only; not pushed to any Azure DevOps field in this version. |

## Title extraction

Input heading:

```
# 3. [user-auth] Add email/password signup
```

Strip the leading `<n>. ` (a number, period, single space) to get the
`System.Title`:

```
[user-auth] Add email/password signup
```

The numbering exists for local reading order (matches the file's
`stories-<n>-...` name); it has no meaning in Azure DevOps once the
work-item ID takes over ordering, so don't carry it into the title.

## Description body

Exactly two blocks:

1. The As-a/I-want/So-that block, rendered as HTML.
2. A trailing paragraph:
   `<p><em>Source: <a href="<relative-path>"><relative-path></a></em></p>`,
   using the story file's path relative to the repo root (e.g.
   `artifacts/epic-checkout/feature-user-auth/stories-3-email-signup.md`).
   The path renders as plain text if the repo isn't browsable from
   Azure DevOps, but it's the canonical pointer back to the full story —
   the acceptance criteria's Given/When/Then detail lives there, not
   duplicated in Description.

Example:

```html
<div>
<p><strong>As a</strong> new visitor<br>
<strong>I want to</strong> create an account with email and password<br>
<strong>So that</strong> I can save my progress across sessions</p>
<p><em>Source: <a href="artifacts/epic-checkout/feature-user-auth/stories-3-email-signup.md">artifacts/epic-checkout/feature-user-auth/stories-3-email-signup.md</a></em></p>
</div>
```

## Acceptance Criteria conversion

Each bullet in the story's `## Acceptance Criteria` section becomes one
`<li>`, bolding the `Given`/`When`/`Then` keywords where they appear:

Input:

```markdown
- Given a valid email and password, when the user submits the form, then an account is created and the user is signed in.
- Given an email already in use, when the user submits the form, then a clear inline error is shown and no account is created.
```

Output:

```html
<div>
<ol>
<li><strong>Given</strong> a valid email and password, <strong>when</strong> the user submits the form, <strong>then</strong> an account is created and the user is signed in.</li>
<li><strong>Given</strong> an email already in use, <strong>when</strong> the user submits the form, <strong>then</strong> a clear inline error is shown and no account is created.</li>
</ol>
</div>
```

General markdown → HTML rules (fidelity over aesthetics; readers open the
work item in the Azure DevOps web UI, which renders the HTML directly):

| Markdown | HTML |
|---|---|
| `**bold**` | `<strong>bold</strong>` |
| Inline `` `code` `` | `<code>code</code>` |
| Blank line | New `<p>` paragraph |
| Fenced code block | `<pre><code>...</code></pre>`, with `<`, `>`, `&` escaped inside |

## Parent resolution — no configured default

A story's parent is always the `ado_id` of the epic recorded at
`artifacts/epic-<epic-slug>/epic.md`, which `qsbn-sync-to-tracker`
syncs (creating or refreshing it) in the same run, before touching any
story. There is no `default_parent_feature_id`-style config value
anywhere in this skill — the correct parent is always derivable from
the feature's actual folder location, which is exactly what
`epic_id` in the story's own frontmatter already encodes.

### Detecting drift and re-parenting

A feature can be moved between epics after stories already exist (via
`qsbn-propose-epic`'s reassignment flow). On every UPDATE:

1. Read the story's current parent relation from Azure DevOps:
   `az boards work-item relation show --id <ado_id>` (or via
   `az devops invoke` for the relations index).
2. Compare the parent's ID to the epic's `ado_id` from this run's step 3.
3. If they match, do nothing.
4. If they differ:
   ```bash
   az boards work-item relation remove --id <ado_id> --relation-type parent --target-id <OLD_PARENT_ADO_ID>
   az boards work-item relation add --id <ado_id> --relation-type parent --target-id <NEW_EPIC_ADO_ID>
   ```
   Report this re-parent in the sync summary — it's a meaningful change,
   not routine housekeeping.

Skip this check entirely on CREATE — a freshly created story is parented
correctly the first time, there's nothing to drift from yet.
