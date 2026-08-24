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
   - If Azure DevOps: ask for the organization name, project name, and
     area path (e.g. `MyProject\Backend`). Ask for the iteration path
     too, but make clear it's optional — leave it blank to let Azure
     DevOps fall back to the team's default iteration.
   - Do not ask for a default parent epic/feature. `qsbn-sync-to-tracker`
     always parents a story to its own feature's epic (synced in the
     same run), never to a statically configured work item — there's
     nothing to collect here.
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
   - Check whether the `azure-devops-cli` skill is installed, globally or
     locally:
     ```bash
     ls ~/.claude/skills 2>/dev/null | grep -i azure-devops-cli
     ls ~/.claude/plugins 2>/dev/null | grep -i azure-devops-cli
     ls .claude/skills 2>/dev/null | grep -i azure-devops-cli
     ```
     `qsbn-sync-to-tracker`'s exact `az boards` / `az devops invoke`
     command syntax depends on this skill being present, so treat it as
     required, not optional, for the Azure DevOps tracker. If none of
     the checks find it, tell the user it's required and ask them to
     confirm before installing it — do not run the install command
     without an explicit yes:
     ```
     npx -y skills@latest add https://github.com/github/awesome-copilot --skill azure-devops-cli
     ```
     Only run it after the user confirms. If they decline, stop this
     step and tell them Azure DevOps sync won't work correctly without
     it — don't silently continue as if it were optional.

3. **Choose the submodule subfolder**
   - Ask what subfolder code repos should be pulled into as git
     submodules (default: `src`).
   - Create the folder (`mkdir -p <folder>`) and add it to `.gitignore`,
     so an empty placeholder directory doesn't need a tracked file to
     exist. Do not add any submodule yourself — `git submodule add` is
     entirely the user's own step, outside this skill's scope.
   - Note for the user: because the folder is gitignored, adding a
     submodule under it later will require `git submodule add -f`
     (git otherwise refuses to add a path inside an ignored directory).

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
     area_path = "..."
     iteration_path = ""

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

- This skill writes `.qsbn/config.toml` and creates the submodule
  subfolder from step 3. It never touches `artifacts/`, `specs/`, or
  the contents of `src/` beyond creating the empty folder itself.
- Re-running is always safe: step 1 always shows current values before
  anything changes.
