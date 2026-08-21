# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
scripts/list-skills.sh   # list every SKILL.md in the repo
scripts/link-skills.sh   # symlink every skill into ~/.claude/skills for local testing
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

**Packaging.** `package.json` carries the repo version (starts at `0.0.0-alpha`), bumped manually - no changesets or release automation yet. Publishing model is `npx skills@latest add <owner>/qsbn-agent-skills` only - no Claude Code plugin channel, so there's no `.claude-plugin/plugin.json` or `marketplace.json`. That installer walks the repo for `SKILL.md` files and doesn't read `package.json` at all, so it's installable the moment a `SKILL.md` exists.
