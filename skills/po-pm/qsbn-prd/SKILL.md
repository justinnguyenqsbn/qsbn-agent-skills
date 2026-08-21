---
name: qsbn-prd
description: Interview the user about a feature and write a PRD, bootstrapping the whole-product PRD on first use. Built-in only — never delegates to a third-party interview skill.
disable-model-invocation: true
---

# qsbn PRD

Write a Product Requirements Document through a one-question-at-a-time
interview. This skill always runs its own interview logic below — it never
checks `.qsbn/config.toml` preferences and never delegates to
`grill-with-docs`, `superpowers:brainstorming`, or any other third-party
skill, regardless of what's installed or configured.

## Workflow

1. **Check whether the product PRD exists yet**
   - If `artifacts/prd.md` does NOT exist, this is the first-ever run in
     this repo. Go to step 2 (product interview) before anything else.
   - If it already exists, skip to step 3 (feature interview), reading
     `artifacts/prd.md` as context first.

2. **Product-level interview (first run only)**
   - Ask, one question at a time:
     - What is this product? (one or two sentences)
     - What problem does it solve, and for whom?
     - Who are the target users/personas?
     - What are the product's top 2-4 goals?
   - Write `artifacts/prd.md`:
     ```markdown
     # Product PRD

     ## Overview
     ...

     ## Problem Statement
     ...

     ## Target Users
     ...

     ## Product Goals
     ...

     ## Features
     <!-- appended by qsbn-prd as features are added -->
     ```
   - Continue straight to step 3 for the feature the user originally asked
     about — don't make them re-invoke the skill.

3. **Detect multi-feature requests**
   - Read the feature description given as `$ARGUMENTS`. If it clearly
     bundles multiple independent features (e.g. "add commenting,
     notifications, and a moderation dashboard"), stop and confirm the
     split with the user before asking any detail questions: list the
     features you'd separate it into, ask if that split is right, and
     let them adjust it.
   - If confirmed, repeat steps 4-6 once per split-out feature, each
     getting its own feature-slug and its own PRD file. Otherwise treat
     it as a single feature and continue.

4. **Feature-level interview**
   - Ask, one question at a time, only what isn't already answered by the
     description given:
     - What's the purpose of this feature — what can a user do after it
       ships that they can't do now?
     - Who uses it, and in what scenario?
     - What constraints apply (technical, timeline, compliance, etc.)?
     - What does success look like? (a metric or observable behavior)
     - What's explicitly out of scope?
   - Prefer multiple-choice questions where a small set of reasonable
     options exists; open-ended is fine otherwise. One question per
     message.

5. **Generate the feature slug**
   - kebab-case the feature title. If it collides with an existing
     `artifacts/<slug>/` or `artifacts/epic-*/feature-<slug>/` folder,
     suffix `-2`, `-3`, etc.
   - Reject (regenerate from a fuller title, or ask the user) the slugs
     `prd` and `epics` — those are reserved for the two root files.

6. **Write the feature PRD**
   - Create `artifacts/<feature-slug>/prd.md`:
     ```markdown
     # Feature PRD: <Title>

     ## Overview
     ...

     ## Problem / Motivation
     ...

     ## Target Users
     ...

     ## Success Criteria
     - ...

     ## Scope

     ### In Scope
     - ...

     ### Out of Scope
     - ...

     ## Constraints
     - ...
     ```

7. **Update the product PRD**
   - Append a link to the new feature under `artifacts/prd.md`'s
     **Features** section: `- [<Title>](./<feature-slug>/prd.md)`.
   - On a later run (product PRD already existed), also ask — don't
     assume — whether this feature changes anything at the product level
     (new goal, expanded target users, etc.). Only edit those sections if
     the user confirms a change.

## Notes

- Output paths only ever land at `artifacts/prd.md` (product) and
  `artifacts/<feature-slug>/prd.md` (feature, pre-epic-assignment). Moving
  a feature under an epic folder is `qsbn-propose-epic`'s job, not this
  skill's.
- This skill never reads or writes `.qsbn/config.toml`.
