---
name: qsbn-setup
description: Configure this repo's tracker connection, submodule layout, story tag, and third-party skill preferences for the qsbn workflow. Run once per tracking repo before any other /qsbn:* skill.
disable-model-invocation: true
---

# qsbn Setup

Configure `.qsbn/config.toml` for this tracking repo. Every other `/qsbn:*`
skill reads this file, so run this one first.

## Workflow

1. **Check for an existing config**
   - If `.qsbn/config.toml` already exists, print its current contents and
     ask whether to reconfigure from scratch or update specific fields. If
     updating specific fields, jump straight to the relevant step below.

2. **Choose the issue tracker**
   - Ask which tracker this project uses: Azure DevOps, GitHub, Linear, or
     Local (files only).
   - Only Azure DevOps has a working sync implementation right now
     (`qsbn-sync-to-tracker` / `qsbn-sync-to-ado`). If the user picks
     GitHub, Linear, or Local, say so plainly: "Only Azure DevOps syncs
     today — I'll save your choice, but sync-to-tracker won't do anything
     for this tracker yet." Save the choice anyway, so the field is
     already set once support lands.
   - If Azure DevOps: ask for the organization name and project name.
     Check the CLI is ready:
     ```bash
     az account show >/dev/null 2>&1 || echo "not logged in"
     az extension show --name azure-devops >/dev/null 2>&1 || echo "azure-devops extension missing"
     ```
     If not logged in, tell the user to run `az login` themselves — this
     skill never handles credentials and must not attempt login on their
     behalf. If the extension is missing, tell them to run
     `az extension add --name azure-devops`. Report the check results;
     don't run either fix yourself.

3. **Choose the submodule subfolder**
   - Ask what subfolder code repos should be pulled into as git
     submodules (default: `src`). Save it, but do not create the folder
     or add any submodule yourself — that's the user's own
     `git submodule add` step, entirely outside this skill's scope.

4. **Choose the story tag**
   - Ask what tag synced stories should carry in the tracker, so they're
     identifiable as qsbn-managed work items.

5. **Detect third-party skills and ask about delegation**
   - Check whether `superpowers` or `mattpocock-skills` (or their
     component skills — `writing-spec`, `tdd`,
     `test-driven-development`) are installed, globally or locally:
     ```bash
     ls ~/.claude/skills 2>/dev/null
     ls ~/.claude/plugins 2>/dev/null
     ls .claude/skills 2>/dev/null
     ```
   - For each one found, ask separately whether to prefer it over qsbn's
     own built-in equivalent:
     - superpowers found → ask about `writing-spec` (used by
       `/qsbn:to-spec`) and about `test-driven-development`/`tdd` (used
       by `/qsbn:tdd`).
     - mattpocock-skills found → ask about its `tdd` skill (used by
       `/qsbn:tdd`).
   - This delegation choice applies ONLY to `/qsbn:to-spec` and
     `/qsbn:tdd`. Never ask this about `/qsbn:prd` or
     `/qsbn:user-stories` — those two always run qsbn's own built-in
     logic, regardless of what's installed, with no delegation branch at
     all.
   - Save each answer as `"built-in"`, `"superpowers"`, or `"mattpocock"`.

6. **Write the config**
   - Create the `.qsbn/` folder if it doesn't exist, and write
     `.qsbn/config.toml`:
     ```toml
     tracker = "azure-devops"

     [ado]
     organization = "..."
     project = "..."

     submodule_root = "src"

     [tags]
     story = "..."

     [preferences]
     tdd = "built-in"
     writing_spec = "built-in"
     ```
   - Omit the `[ado]` section entirely if a different tracker was chosen
     — there's nothing to configure for it yet.

7. **Confirm**
   - Print the final config back to the user and confirm it looks right
     before finishing.

## Notes

- This skill only ever writes `.qsbn/config.toml`. It never touches
  `artifacts/`, `specs/`, or `src/`.
- Re-running is always safe: step 1 always shows current values before
  anything changes.
