# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
scripts/list-skills.sh   # list every SKILL.md in the repo
scripts/link-skills.sh   # symlink every skill into ~/.claude/skills, and every skill-bundled agent into ~/.claude/agents, for local testing
```

There is no build, lint, or test step - skills are Markdown files with YAML frontmatter, not code that compiles or runs standalone.

## Architecture

This is a Claude Code [Agent Skills](https://code.claude.com/docs/en/skills) repository, built for one purpose: a `/qsbn:*` command namespace for Product Owner/Project Manager and Developer backlog/delivery workflows, backed by Azure DevOps. The full design rationale lives in `docs/superpowers/specs/2026-08-21-qsbn-workflow-design.md` in the `vampire-coder-skills` project this repo was designed alongside - read that spec before adding or changing a skill here, it is the source of truth for file layout, frontmatter schemas, and each skill's behavior.

**Bucket layout.** Skills are grouped under `skills/` by role:

- `core/` - shared foundation (`qsbn-setup`)
- `po-pm/` - the PRD -> epic -> user-stories -> sync-to-tracker pipeline
- `developer/` - turning a confirmed story into a spec, then implementing it (`qsbn-to-spec`, `qsbn-tdd`)
- `scrum-master/` - deferred, not yet created; see the design spec's Appendix for the agreed shape

**`SKILL.md` frontmatter contract:**

```yaml
---
name: qsbn-skill-name
description: What it does, and what /qsbn: command triggers it.
disable-model-invocation: true
---
```

Every skill in this repo is user-invoked only (`disable-model-invocation: true`, always present, never omitted). These are deliberate steps in a specific `/qsbn:*` pipeline - none of them should ever auto-trigger from Claude noticing the task fits.

**Command shim pattern.** Every skill `skills/<bucket>/qsbn-<name>/SKILL.md` is paired with a thin shim `commands/qsbn/<name>.md`, so `/qsbn:<name>` works as a real Claude Code custom slash command (colon-namespaced, directory-based). This is a different mechanism from a skill's own name-based invocation - the shim is what actually makes `/qsbn:<name>` resolve, and it just instructs Claude to invoke the matching `qsbn-<name>` skill with the given arguments.

**Skill internals.** A skill can be a single `SKILL.md`, or `SKILL.md` plus sibling reference files for material only needed on some runs (progressive disclosure - keep `SKILL.md` itself lean, push detail into a linked file loaded on demand). Reference the existing `superpowers:writing-skills` and `skill-creator:skill-creator` skills when authoring or refining a skill - this repo doesn't duplicate that guidance.

**Agents.** A skill that genuinely needs its own Task-tool subagent (a cheaper pinned model, real parallelism across independent units, or output that shouldn't share the calling skill's context - not a default way to structure a skill) bundles it as a sibling file at `skills/<bucket>/<name>/agents/qsbn-<agent-name>.md`, colocated with the `SKILL.md` that owns it, not in a separate top-level directory. This is required, not a style choice: `npx skills@latest add <owner>/qsbn-agent-skills` (the real publish path - see Packaging below - is `vercel-labs/skills`) only ever installs a skill's own directory into `.claude/skills/<name>/`; it has no concept of `.claude/agents/` at all, so anything living outside a skill's own folder would simply never reach a real install. Colocating it inside the skill's folder means it travels wherever the skill travels, through that same real installer, with no changes needed upstream.

Getting it from `.claude/skills/<name>/agents/` (where the skill installed) to `.claude/agents/` (where Claude Code actually looks for a subagent) is then the owning skill's own job, done lazily the first time a run needs it: check whether `.claude/agents/qsbn-<agent-name>.md` in the current project already matches the bundled copy; if it's missing or differs, create `.claude/agents/` if needed and copy the bundled file over it verbatim, then proceed. See `qsbn-docs`'s "Materializing `qsbn-scout`" section for a worked example. Give the agent a narrow `description` so the top-level agent doesn't reach for it outside the one skill that spawns it, and pin `model:` deliberately (e.g. `haiku` for a cheap, high-fan-out sweep) rather than leaving it unset.

`scripts/link-skills.sh` and `scripts/install-local.sh` mirror this same materialization for local development, symlinking/copying every `skills/*/*/agents/*.md` into `~/.claude/agents` (or `<target>/.claude/agents`) alongside the skills themselves - so a real end user relies on the skill's own self-install step, but local dev doesn't have to invoke the skill once just to get its agent in place.

**Packaging.** `package.json` carries the repo version (starts at `0.0.0-alpha`), bumped manually - no changesets or release automation yet. Publishing model is `npx skills@latest add <owner>/qsbn-agent-skills` only - no Claude Code plugin channel, so there's no `.claude-plugin/plugin.json` or `marketplace.json`. That installer walks the repo for `SKILL.md` files and doesn't read `package.json` at all, so it's installable the moment a `SKILL.md` exists.
