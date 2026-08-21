---
name: qsbn-tdd
description: Implement a spec's tasks test-first inside a specified code submodule, one red-green-refactor cycle at a time. Delegates to a configured third-party TDD skill if set in preferences, otherwise runs its own built-in loop.
disable-model-invocation: true
---

# qsbn TDD

Implement a feature's spec inside its code repo, test-first. This skill
never touches, inspects, or bumps the git state of any submodule under
`src/` in any way — not the pointer, not its commit history, not even a
read-only `git log`. Checking a submodule's progress is entirely the
user's own responsibility, done manually, at any time, by whatever means
they choose. This is a hard rule, not a default to weigh against
convenience.

## Workflow

1. **Resolve the spec and target repo**
   - Take `$ARGUMENTS` as a feature identifier (same resolution as
     `qsbn-to-spec`) plus which `src/<repo-name>/` submodule to work in —
     the caller must specify the repo explicitly; never infer it.
   - Read `specs/<feature-slug>/spec.md` for the task list. If it doesn't
     exist, tell the user to run `/qsbn:to-spec` first.

2. **Check delegation preference**
   - Read `.qsbn/config.toml`'s `preferences.tdd`.
   - If it names a third-party skill (`superpowers`, `mattpocock`),
     invoke that skill now (pointing it at the spec's task list and the
     target `src/<repo-name>/` path) instead of continuing below, and
     stop once it finishes.
   - If it's `built-in` (or the config/field doesn't exist), continue to
     step 3.

3. **Built-in red-green-refactor loop**
   - Work through the spec's tasks one at a time, each as its own cycle:
     1. **Red**: write a failing test for the task's behavior, inside
        `src/<repo-name>/`, at the seam that behavior is observed
        through — not against internals.
     2. **Green**: write the minimum code to pass that test. No
        speculative extras, nothing addressing a later task.
     3. **Refactor**: clean up only what this cycle touched.
   - One task, one seam, one test, one minimal implementation per cycle.
     Don't batch multiple tasks' tests before implementing any of them.
   - Commit inside `src/<repo-name>/`'s own history when a cycle is
     complete (a commit local to that submodule's repo). Do not run
     `git add src/<repo-name>` or any other command from the tracking
     repo's root that would touch the submodule pointer — that is
     explicitly out of scope, per the rule at the top of this skill.

4. **Track progress against the spec**
   - As each task completes, note it (in your own working notes or the
     chat, not by editing `specs/<feature-slug>/spec.md` unless the user
     asks) so a resumed session picks up where the last one left off.

## Notes

- This is the only other qsbn skill besides `qsbn-to-spec` with a
  delegation branch.
- If the target submodule doesn't exist at the expected path, stop and
  tell the user — do not run `git submodule add` or any other submodule
  management command; that's entirely the user's setup step, outside
  this skill's scope (see the rule at the top).
