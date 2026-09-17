# qsbn-agent-skills

Claude Code [Agent Skills](https://code.claude.com/docs/en/skills) that help
Product Owners/Project Managers and Developers create a backlog and run the
delivery process for a project: PRDs, epics, user stories, syncing to Azure
DevOps, and turning approved stories into implementation work.

**This repo must NOT be installed globally.** Install it into the specific
git repository that tracks a single project's backlog and delivery process —
never into `~/.claude/skills`. Each tracking repo gets its own copy, its own
`.qsbn/config.toml`, and its own `artifacts/`/`specs/` trees. See the design
spec (`docs/superpowers/specs/2026-08-21-qsbn-workflow-design.md` in the
`vampire-coder-skills` project) for the full rationale.

## Skills

- **core** — shared setup (`qsbn-setup`)
- **po-pm** — PRD → epic → user stories → sync-to-tracker pipeline
- **developer** — turn a story into a spec, then implement it test-first

See [`skills/README.md`](./skills/README.md) for the current skill list per
bucket, and [`CLAUDE.md`](./CLAUDE.md) for the `SKILL.md` authoring contract.

A `scrum-master` bucket is planned but not yet built — see the design spec's
Appendix for what's agreed so far.

## Local development

```bash
scripts/list-skills.sh   # list every SKILL.md in the repo
scripts/link-skills.sh   # symlink every skill/agent into ~/.claude/skills and ~/.claude/agents for local testing
```

`link-skills.sh` is for testing this repo's own skills locally only. End
users install per-project via `skills.sh` (`npx skills@latest add
<owner>/qsbn-agent-skills`), never by symlinking into `~/.claude/skills` —
symlinking would violate the "not installed globally" rule above.

Re-run `link-skills.sh` after adding, removing, or renaming a skill.
