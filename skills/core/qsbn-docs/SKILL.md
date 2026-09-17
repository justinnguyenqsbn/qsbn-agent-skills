---
name: qsbn-docs
description: Scout every code submodule under src/ and generate or refresh two whole-project brownfield docs — docs/architecture.md and docs/project-overview.md — following this skill's own bundled templates. One shared doc pair for the whole project, never one per submodule. Always auto-splits a doc that grows too long — never asks first.
disable-model-invocation: true
---

# qsbn Docs

Document a codebase that already exists, by reading it rather than by
interviewing anyone about it. This is the only qsbn skill that writes
under `docs/` — a third top-level tree alongside `artifacts/`
(business-level, owned by the po-pm pipeline) and `specs/` (implementation
breakdown, owned by the developer pipeline).

It produces exactly two files, both directly under `docs/`, never one per
submodule: `docs/architecture.md` and `docs/project-overview.md`, each
following this skill's own bundled template
(`templates/architecture.md`, `templates/project-overview.md`, next to
this `SKILL.md`) heading for heading. A tracking repo can hold several
`src/<repo-name>/` submodules, but the picture these two documents give is
of the *system as a whole* — that's the point of keeping them singular
instead of a separate architecture/overview pair per submodule.

`docs/project-overview.md`'s `Goals` and `Success Criteria` sections cite
`artifacts/prd.md` when it exists instead of re-deriving them from code —
a codebase can tell you what it *does*, never what it's *for*. Everything
else in both documents comes from the code itself, evidenced, never
invented just to fill a template heading.

## Workflow

1. **Resolve the mode**
   - Parse `$ARGUMENTS` for a token matching `scan`, `refresh`, or
     `brief`; default `scan` when none is given. This skill takes no
     repo-name argument — it always covers every submodule under `src/`
     together, never just one.
   - `scan` when `docs/architecture.md` or `docs/project-overview.md`
     already has real (non-placeholder) content: tell the user and
     confirm a full rebuild before overwriting either one. This is the
     one confirmation this skill ever asks for — never about which
     submodules to include, or whether to split an oversized file.

2. **Sweep every submodule**
   - Read `.qsbn/config.toml`'s `submodule_root` (default `src` if the
     config or field is missing). List every immediate subdirectory
     containing a `.git` entry — that's the full sweep set for this run,
     always all of them, never a chosen subset.
   - None found → stop and tell the user there's nothing under
     `<submodule_root>` to document.
   - **1-2 submodules**: sweep each inline, in turn — spawn overhead
     isn't worth it for so few.
   - **3+ submodules**: first make sure `qsbn-scout` is actually
     installed as a subagent (see **Materializing `qsbn-scout`** below),
     then spawn it once per submodule instead of sweeping them one at a
     time. Cap concurrency at 5 at a time; give each call a 3-minute
     timeout. A submodule whose sweep times out is skipped and logged in
     the final report as "sweep timed out — re-run to retry" rather than
     blocking the rest.
   - **What a sweep covers**, whether run inline or by `qsbn-scout` (its
     own definition carries the same steps, so the shape of findings is
     identical either way): walk the submodule, skipping `.git`,
     dependency/cache/build directories (`node_modules`, `vendor`,
     `dist`, `build`, `__pycache__`, `.venv`, etc.) and anything its own
     `.gitignore` excludes; per top- and second-level directory, count
     files and LOC; identify its manifest(s) (language, framework,
     dependencies) and entry point(s); read any docs/README/ADRs already
     inside it as primary evidence; note anything that looks like a call
     into, or dependency on, another submodule (a config value, base URL,
     env var, or import naming another repo), citing where it was found.
   - Once every submodule's findings are in hand (inline, delegated, or a
     mix), proceed to step 3, 4, or 5.

3. **`scan` — write both documents from scratch**
   - Fill this skill's own bundled `templates/architecture.md` into
     `docs/architecture.md`, same headings as the template, every
     bracketed placeholder replaced with real, evidenced content — or,
     where the sweeps found no evidence for something the template asks
     for, an explicit note that it's unresolved rather than an invented
     answer:
     - `Stack` — one table row per real layer found. With more than one
       submodule, group rows under a `### <repo-name>` subheading per
       submodule instead of flattening everything into one ambiguous
       table.
     - `System Boundaries` — one bullet per submodule (`src/<repo-name>/`)
       stating what it owns, plus its real internal folder boundaries.
       This is also where a call/dependency on another submodule belongs
       — e.g. "calls `<other-repo>` over its REST API for X" — cited to
       the evidence a sweep found. Never infer a connection from name
       similarity alone; a submodule with no evidenced connection is
       still listed, just without one claimed.
     - `Storage Model`, `Auth and Access Model` — aggregated across every
       submodule that has one; name which submodule owns which piece
       whenever there's more than one.
     - `Invariants` — cross-cutting rules the code actually enforces
       (found in validation, guards, middleware, CI checks), never
       aspirational rules; skip any the sweeps found no real evidence
       for rather than padding the list to match the template's count.
   - Fill this skill's own bundled `templates/project-overview.md` into
     `docs/project-overview.md`, same rule (every heading kept, every
     placeholder replaced or explicitly marked as a gap):
     - Title — the project name from `artifacts/prd.md`'s own title if
       it exists, else `.qsbn/config.toml`'s `ado.project`, else the
       tracking repo's own folder name.
     - `Overview` — what the system actually does today, from the
       sweeps; cross-check against `artifacts/prd.md` if present, but
       describe the *as-built* system, not the aspirational one.
     - `Goals`, `Success Criteria` — if `artifacts/prd.md` exists, cite
       its Product Goals (or equivalent) instead of re-deriving them from
       code; if it doesn't exist, write "_No product goals recorded yet —
       run `/qsbn:prd` or add them here._" rather than guessing at intent
       from code alone.
     - `Core User Flow` — the primary route(s)/entry point(s) the sweeps
       found, traced end to end wherever there's enough evidence to trace
       it; leave a step as a gap note rather than inventing a plausible
       one.
     - `Features` — feature categories inferred from the real module/
       route/page structure the sweeps found.
     - `Scope` (`In Scope` / `Out of Scope`) — In Scope from what's
       actually implemented; Out of Scope only from explicit evidence (a
       code comment, a TODO, or the PRD's own Out of Scope) — omit the
       subsection entirely rather than invent an absence with nothing
       backing it.
   - Give both files frontmatter: `generated_at`, `mode: scan`,
     `submodules` (the list swept).
   - Apply **Auto-split** (below) to both.
   - Report the resulting files and a one-line summary (submodules
     swept, languages/frameworks found, anything flagged as a gap).

4. **`refresh` — update both after code changes**
   - Requires `docs/architecture.md` and `docs/project-overview.md` (or
     their sharded folders) to already exist; if not, tell the user to
     run `scan` first.
   - Re-sweep every submodule and diff against what's already recorded —
     a new or removed submodule, a new manifest dependency, a large LOC
     swing, a newly evidenced connection between submodules. Leave a
     section alone whose backing evidence hasn't moved.
   - Update only the affected sections/subheadings in each document (or
     the specific shard that owns that part) — append what's new,
     correct what's stale, never delete a section still backed by
     evidence just because nothing changed there this run.
   - Anything in `$ARGUMENTS` beyond the mode is an extra focus area for
     this pass (e.g. "focus on the auth boundary").
   - Apply **Auto-split** to whichever file(s) changed.
   - Report which sections changed and why, one line each.

5. **`brief` — fast orientation pass, no file writes**
   - Runs the sweep (step 2) only. Writes nothing — doesn't touch
     `docs/architecture.md`, `docs/project-overview.md`, or their shards.
   - Answers in chat with a short summary: submodules found, language/
     framework per submodule, and anything that looks newly added since
     the last `scan`/`refresh`. For "just get me oriented fast" — run
     `scan` or `refresh` when the documents themselves need updating.

## Materializing `qsbn-scout` (before its first use in a run)

`qsbn-scout` isn't a separate top-level install artifact — it ships as a
sibling file inside this skill's own package, at
`skills/core/qsbn-docs/agents/qsbn-scout.md`. That's deliberate: the real
published install path (`npx skills@latest add <owner>/qsbn-agent-skills`)
only knows how to place a skill's own directory under
`.claude/skills/<name>/` — it has no notion of `.claude/agents/` at all,
so nothing outside this skill's own instructions can put `qsbn-scout`
where Claude Code actually looks for a subagent.

So this skill installs its own dependency itself, lazily, the first time a
run actually needs it — the 3+-submodule sweep path in step 2, never
earlier:

1. Read this skill's own bundled copy, at this installed skill's own
   `agents/qsbn-scout.md` (next to this `SKILL.md`).
2. Compare it to `.claude/agents/qsbn-scout.md` in the current project —
   not `~/.claude/agents/`; this stays scoped to the tracking repo, like
   every other qsbn state.
3. Missing, or present but different from the bundled copy → create
   `.claude/agents/` if needed and copy the bundled file over it. Already
   installed and identical → skip silently, no unnecessary write.
4. Only then spawn `qsbn-scout` for this run's submodules.

This is the one file this skill ever writes outside `docs/` — and only
ever this one path, only ever copied verbatim from its own bundled
source, never authored from scratch.

## Auto-split (always, every mode — never a question to the user)

After writing or updating `docs/architecture.md` or
`docs/project-overview.md` (the only two files this skill ever produces):

1. Count its lines. Read `.qsbn/config.toml`'s `docs.max_loc` (default
   `400` if the config or field is missing).
2. If it's under the limit, leave it as a flat file.
3. If it's over the limit, shard it immediately:
   - Turn `docs/architecture.md` into `docs/architecture/` (or
     `docs/project-overview.md` into `docs/project-overview/`) containing
     an `index.md` (frontmatter, a short overview, and a linked list of
     the shards in order) plus one `NN-<section-slug>.md` per top-level
     `##` section from the template, numbered in the template's order.
   - Delete the flat file once every section has moved into a shard.
   - On a later `refresh`, edit the one shard whose section changed
     instead of touching the rest; re-shard further only if that
     individual shard itself now exceeds the limit.
4. Never ask first, and never leave an oversized flat file in place — the
   split happens as part of writing the doc, and gets one line in the
   final report ("split `architecture.md` into `architecture/` — 5
   sections").

## Notes

- Bundled templates are the source of truth for shape: this skill ships
  its own `templates/architecture.md` and `templates/project-overview.md`
  (`skills/core/qsbn-docs/templates/`). The two documents it ever writes
  follow these heading for heading — to change what this skill outputs,
  edit the templates, not the prose in this file.
- One document pair for the whole project, never one per submodule.
- Depends on the `qsbn-scout` agent, bundled at this skill's own
  `agents/qsbn-scout.md` and self-installed to `.claude/agents/` on first
  use (see **Materializing `qsbn-scout`**) — it's a plain Task-tool
  subagent, not another skill, and it exists only to be spawned by this
  workflow: pinned to Haiku so fanning it out across several submodules
  stays cheap, and scoped narrowly enough (read-only, one submodule, one
  report, no delegating further) that it shouldn't get invoked for
  anything else.
- Reads `submodule_root` and `docs.max_loc` from `.qsbn/config.toml` when
  present; never writes to that file — that's `qsbn-setup`'s job alone.
- Never touches a submodule's git state (no commits, no pointer changes,
  not even a read-only `git log` beyond what the sweep needs) and never
  edits any file inside `src/<repo-name>/` itself, including its
  `README.md` — same submodule boundary `qsbn-tdd` holds to.
- Cites `artifacts/prd.md` for `Goals`/`Success Criteria` but never edits
  it, and never writes to `specs/` — those trees belong to the po-pm and
  developer pipelines respectively, not to this skill.
