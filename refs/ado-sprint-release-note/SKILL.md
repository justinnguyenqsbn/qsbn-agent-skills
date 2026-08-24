---
name: ado-sprint-release-note
description: Draft (and optionally publish) a NON-TECHNICAL, plain-language "Sprint Release Note" for a ChatMate365-style Azure DevOps sprint, grouped by feature/epic — for stakeholders, customers, or anyone outside engineering. This is distinct from the ado-sprint-release-report skill, which produces the internal, categorized (New features/Changes/Bug fixes/Enhancements) wiki report for engineering audiences. Use this skill whenever the user asks for a release note, a "what shipped this sprint" summary, a customer-facing update, a non-technical sprint recap, or something to paste into an email/Teams/Word doc for non-engineers — even if they just say "sprint 27" or "the latest sprint" and ask for a plain-English update, without naming the skill or the output format. Handles publishing to the project wiki as Markdown, generating an email-ready HTML file, or both, and can mark the wiki page as Draft.
---

# Azure DevOps sprint release note (non-technical)

Produces the audience-facing counterpart to the internal Sprint Release Report: the same underlying sprint work, rewritten so someone with no engineering context — a customer, an exec, a support lead — understands what changed and why they'd care. Grouped by **feature/epic**, not by work-item category.

If the user's request actually sounds like it wants the internal, categorized, engineering-facing report (New features / Changes / Bug fixes / Enhancements), that's the **ado-sprint-release-report** skill, not this one. When in doubt about which they want, ask.

## Step 1: Resolve the sprint

If the user names a sprint, use it. Otherwise default to the **most recently completed** sprint — a release note describes what shipped, and the in-progress sprint hasn't finished shipping it yet.

Run the bundled fetcher, which also resolves the tricky *team* iteration path string the same way the sibling skill does:

```
python scripts/fetch_release_data.py --org https://dev.azure.com/qsbnproducts --project ChatMate365 [--sprint 27]
```

Omit `--sprint` to get the most recently completed sprint automatically. Defaults: `--team "<project> Team"`. If org/project aren't obvious from the repo's config (e.g. AGENTS.md) or conversation context, ask rather than guessing.

This returns every work item in the sprint, each annotated with:
- `group`: the nearest ancestor Feature (or Epic, if no Feature exists above it) — `{id, type, title, description}` — even when that Feature/Epic isn't itself in this sprint (the usual case; Features span many sprints).
- `description`: the item's own description, HTML-stripped to plain text.
- `parent_in_sprint`: true if the item's immediate parent is also in this sprint's item list.

## Step 2: Decide what represents the sprint, and group it

Start by loading this project's saved settings — reused again in Step 5, so there's no need to fetch it twice:

```
python scripts/config.py get --org <org> --project <project>
```

`{}` means nothing saved yet for this org/project — normal on a first run. Otherwise it may contain `wiki`/`team`/`wiki_path_template` (used in Step 5) and, for projects that have opted into it, `known_clients` — a roster of customer/client names this project's work items sometimes belong to (e.g. `["SLB", "Sint Lucas", "QSBN"]` for ChatMate365). Most projects won't have a roster; that's fine, it just means every item this sprint is generic and Step 4's client-scope question gets skipped entirely.

Same "don't over-report" judgment as the internal report skill:
- Skip a **Task** whose parent is also in this sprint (`parent_in_sprint: true`) — it's implementation detail the parent story already covers.
- A Task with `parent_in_sprint: false` (parent already used up in an earlier note, or not in this sprint) may stand in for its parent if that's the most specific thing to mention.
- Not everything needs a mention — an internal refactor or a one-line polish fix that no non-technical reader would notice is fine to fold into a neighboring item's description or drop, at your judgment.

Then group the surviving items by their `group` (Feature/Epic), using each Feature's own `description` plus its stories' `description`s and titles to understand *why* the work happened — that's what turns "Voice Dictation — Agent-Streaming Concurrency" into "you can now dictate a message even while ChatMate is still replying to your last one." Items with no `group` (standalone bugs/stories with no Feature parent) go in a trailing "Other updates" section.

If `known_clients` is non-empty, also tag each surviving item with whichever client it names, if any: check the item's own title and description first, then — if the item itself reads as generic — its `group`'s title and description, since a Feature's name (e.g. `[Sint Lucas] Configure Branding, System Prompt & Teams Manifest`) is often the only place the client is named and its child tasks won't repeat it. Match loosely against the roster (`SintLucas` and `Sint Lucas` are the same client — ignore spacing/case); items matching nothing are generic. This tagging is cheap to do regardless of what gets delivered — it only actually gets used for the email deliverable in Step 4, never for wiki. If a title or description seems to name a real customer that isn't on the saved roster, don't silently guess whether it counts — ask the user whether it's a new client worth tracking (and if so, add it via `config.py set --known-clients` in Step 5, listing the existing roster plus the new one) or just an incidental mention.

## Step 3: Write the note in plain language

Write for someone who has never seen a work-item ID or an engineering ticket. Concretely:
- No jargon: no "NFR", "HITL", "spike", "PBI", work item type names, or internal codenames — translate them ("a research investigation", "an internal check", etc.) or drop them.
- Lead with what the reader would notice or benefit from, not with what the team built. "You can now expand the chat to full screen" beats "Implemented maximize/restore modal view."
- Keep each feature section to a short paragraph or a couple of tight bullets — this is a recap, not documentation.
- Still reference the underlying work item(s) so the note stays traceable, but keep the reference out of the sentence itself: append it in parentheses, `(#<id>)`, using the Feature's id for a feature-level summary or the specific story's id for a specific callout. This is the one piece of "technical" content in an otherwise plain-language document, and it's designed to be trivially removable — see Step 4.

Structure:

```
# Sprint Release Note – Sprint <N>

## <Feature/epic name in plain language>
<Paragraph or short bullets explaining what's new and why it matters.> (#<feature or story id>)

## <Next feature>
...

## Other updates
<Anything with no feature parent — standalone fixes, small polish items.> (#<id>)
```

## Step 4: Ask the user how they want it delivered

Ask before producing final files — don't assume:

1. **Format**: wiki page (Markdown), email draft (HTML file), or both.
2. If wiki is included: **Draft or published?** Draft prepends a visible indicator line at the very top of the document (e.g. `> **Draft**`); published omits it entirely — don't include a watered-down version of the indicator, either it's there or it isn't.
3. If email is included and this project has a saved `known_clients` roster (Step 2): **Client scope** — ask whether the email should be:
   - **generic** — no customer/client-specific items at all, or
   - one **specific client** from the roster, or
   - **all clients**.

   Skip this question entirely for projects with no roster — there's nothing to scope, every item is generic.

For the **wiki** version: keep the `(#<id>)` references inline exactly as written in Step 3 — that's the whole point of writing them that way, they give ADO traceability for whoever maintains the wiki. The wiki page **always includes every item**, generic and client-tagged alike, regardless of what was chosen for the email — client scoping is an email-only concept, since the wiki is the complete internal-facing record.

For the **email** version: write the plain-language content directly as simplified HTML, omitting the `(#<id>)` references entirely — an external or non-technical reader has no use for a work-item number, and copy-pasting into Outlook/Teams/Word doesn't preserve markdown syntax anyway. Use plain, inline-styled tags only (`<h2>`, `<p>`, `<ul><li>`) with no `<style>` block or external CSS/scripts — Outlook and Word strip `<style>` blocks and most pasting flows only keep inline styles.

If a client scope was chosen (question 3 above), apply it before laying out the sections:
- **Generic**: drop every item tagged with a client (Step 2) — keep only generic items and their Feature sections.
- **One specific client**: keep the generic items, plus only that client's tagged items — drop every other client's items outright, they're not relevant to this reader. Append the client's items as a single trailing `## <Client name> updates` section, after every generic Feature section.
- **All clients**: keep everything. Generic Feature sections come first, then one trailing `## <Client name> updates` section per client that has tagged items this sprint (roster order), so a reader always hits the shared product news before any client-specific items.

In every case, generic content leads and client-specific content follows — never interleave a client's items among the generic Feature sections.

Wrap the HTML in a minimal shell:

```html
<div style="font-family:Segoe UI, Arial, sans-serif; font-size:14px; color:#1a1a1a; line-height:1.5;">
  <h1 style="font-size:20px;">Sprint Release Note – Sprint 27</h1>
  <h2 style="font-size:16px; margin-top:20px;">Feature name</h2>
  <p>Plain-language paragraph...</p>
</div>
```

Save it to a `.html` file and tell the user where it is — they open it in a browser, select-all, and paste into Outlook/Teams/Word, which carries the inline styles over.

## Step 5: Resolve (or set up) the wiki page location

Reuse the config already fetched in Step 2 — no need to call `get` again.

- If it had a non-empty `wiki_path_template` (a template string containing the literal placeholder `{sprint_name}`, e.g. `/Product/Sprint Releases/Release Note - {sprint_name}`), use it along with the saved `wiki` and `team`. The template is deliberately project-name-free: `--project` and `--wiki` are already passed separately to every `az devops wiki` call, so the page path itself doesn't need to repeat the project as a leading folder.
- If it was `{}` or missing `wiki_path_template` (nothing saved yet), ask the user where they want release notes to live in the wiki. Offer as the default `/Product/Sprint Releases/Release Note - {sprint_name}`. Once confirmed, save it with `{sprint_name}` left as a literal placeholder — it's resolved per-sprint at publish time, not now:

```
python scripts/config.py set --org <org> --project <project> \
  --wiki ChatMate365.wiki --team "ChatMate365 Team" \
  --wiki-path-template "/Product/Sprint Releases/Release Note - {sprint_name}"
```

If Step 2 flagged a new client not yet on the saved `known_clients` roster and the user confirmed it's worth tracking, save the roster here too — pass the **full** roster (existing entries plus the new one), since `set` replaces it wholesale rather than appending:

```
python scripts/config.py set --org <org> --project <project> \
  --wiki ChatMate365.wiki --team "ChatMate365 Team" \
  --wiki-path-template "/Product/Sprint Releases/Release Note - {sprint_name}" \
  --known-clients "SLB,Sint Lucas,QSBN,<new client>"
```

Run this (and `get`/`reset`) through **PowerShell, not Git Bash** — any argument starting with `/`, including `--wiki-path-template`, gets silently mangled into a Windows filesystem path (e.g. `C:/Program Files/Git/...`) by Git Bash's MSYS layer before Python ever sees it. This isn't specific to `az` calls; it'll happen to this script too.

If the user wants to change the saved location later, or asks to reset/reconfigure this skill, clear it and re-ask next run:

```
python scripts/config.py reset --org <org> --project <project>
# or, to wipe every project's saved config:
python scripts/config.py reset --all
```

Substitute `{sprint_name}` with the actual sprint name (e.g. `Sprint 27`) to get the final page path.

## Step 6: Publish

Show the full draft(s) to the user before doing anything else, exactly as with the internal report skill — never publish without them seeing the content first.

Once approved, for the wiki path:

```
python scripts/publish_wiki_page.py --org <org> --project <project> --wiki <wiki> \
  --path "<resolved wiki path from Step 5>" --file-path note.md
```

Pass `--path` through PowerShell, not Git Bash — a leading `/` gets mangled into a Windows filesystem path in Git Bash and the call will fail with a confusing "ancestor page does not exist" error.

For the email path, there's nothing to "publish" — the HTML file Step 4 wrote is the deliverable. Just point the user at it.

If the user only wants the draft (e.g. to review further, or isn't ready to publish), stop after Step 4/5 — don't call the publish script unasked.
