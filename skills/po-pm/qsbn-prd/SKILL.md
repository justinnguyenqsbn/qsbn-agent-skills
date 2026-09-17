---
name: qsbn-prd
description: Interview the user about a feature and write a PRD, bootstrapping the whole-product PRD on first use. Built-in only — never delegates to a third-party interview skill.
disable-model-invocation: true
---

# qsbn PRD

Write a Product Requirements Document through an adaptive interview. This
skill always runs its own interview logic below — it never checks
`.qsbn/config.toml` delegation preferences and never delegates to
`grill-with-docs`, `superpowers:brainstorming`, or any other third-party
skill, regardless of what's installed or configured.

## Workflow

1. **Check whether the product PRD exists yet**
   - If `artifacts/prd.md` does NOT exist, this is the first-ever run in
     this repo. Go to step 3 (product interview) before anything else.
   - If it already exists, skip to step 4 (feature interview), reading
     `artifacts/prd.md` as context first.

2. **Scout the project folder**
   - Read `.qsbn/config.toml`'s `submodule_root` value. If the file
     doesn't exist yet, or the field is missing/empty, skip this step
     entirely and go straight to the interview — don't block on setup,
     don't guess a default path (`src` is `qsbn-setup`'s default, not this
     skill's to assume).
   - If the resolved folder exists and has content:
     - Identify project type/language/framework from its manifest
       (`package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml`, etc.).
     - Glob/grep inside it for files or modules whose name or content
       overlaps with keywords in `$ARGUMENTS`, or with existing feature
       titles already read from `artifacts/` on a later run.
     - Skim the folder's own `README.md`/`docs/*.md` if present.
   - If nothing overlaps, or the folder is empty/missing, skip silently —
     don't produce a scout summary when there's nothing to report.
   - When something is found, post a short 3-6 bullet summary to the user
     (e.g. "Here's what I found in `<submodule_root>` relevant to this
     feature") *before* asking any interview question that references it.
     Never ask a question grounded in scout findings the user hasn't seen
     in visible text yet.
   - This is the only field this skill reads from `.qsbn/config.toml` — it
     still never reads delegation preferences, never reads any other
     field, and never writes the file.

3. **Product-level interview (first run only)**
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
   - Continue straight to step 4 for the feature the user originally asked
     about — don't make them re-invoke the skill.

4. **Detect multi-feature requests**
   - Read the feature description given as `$ARGUMENTS`. If it clearly
     bundles multiple independent features (e.g. "add commenting,
     notifications, and a moderation dashboard"), stop and confirm the
     split with the user before asking any detail questions: list the
     features you'd separate it into, ask if that split is right, and
     let them adjust it.
   - If confirmed, repeat steps 5-7 once per split-out feature, each
     getting its own feature-slug and its own PRD file. Otherwise treat
     it as a single feature and continue.

5. **Feature-level interview**
   - Cover these topics, but treat them as topics to satisfy, not a fixed
     script — rephrase, reorder, merge, or skip any that the description
     given in `$ARGUMENTS` (or step 2's scout findings) already answers
     clearly:
     - Purpose: what can a user do after this ships that they can't do now?
     - Who/scenario: who uses it, and in what situation?
     - Constraints: technical, timeline, compliance, or other limits?
     - Success criteria: what does success look like — a metric or
       observable behavior?
     - Out of scope: what's explicitly excluded?
     - Touchpoints: does this touch or extend an existing module/feature?
       Offer step 2's candidates as options if any were found, otherwise
       ask open-ended.
   - **Choosing one-at-a-time vs. batched:**
     - Ask **one question at a time** whenever you're offering the user a
       set of suggested options to pick from (multiple-choice) — don't
       stack several option-based questions in one message, that forces
       the user to hold multiple option sets in their head at once.
     - Ask **multiple questions together** when they're open-ended and
       naturally answerable in free-form prose in one pass (e.g. purpose +
       who/scenario often come out together in one or two sentences) —
       don't force artificial one-at-a-time pacing on things the user could
       just as easily answer in a single paragraph.
     - Default to one-at-a-time whenever unsure which mode fits.
   - **No blackbox answers.** After every response (whether to a single
     question or a batch), check each covered topic for genuine clarity —
     vague, hedged, contradictory, or partial answers ("some users I
     guess", "probably fast enough") are not acceptable as final. Ask a
     targeted follow-up on exactly the unclear part before moving on;
     don't let an ambiguous answer get written into the PRD verbatim.
   - Keep looping — more questions on a topic, or new topics prompted by
     what the user just said — until every topic above is concrete enough
     to write down without guessing. This can mean more than one round per
     topic; there's no fixed question count.
   - **Optional deeper mode (`--deep`)**: when the user passes `--deep` to
     `/qsbn:prd`, or the description names a specific technical mechanism
     rather than a user outcome (a sign of a pre-chosen solution), also
     ask: "what's not working today that this solves, and what happens if
     we don't build it?" Record the answer, plus any assumption raised and
     its risk-if-wrong, as a `## Problem Validation` section written in
     step 7. Skip this entirely by default — it's opt-in, not part of the
     normal fast path.

6. **Generate the feature slug**
   - kebab-case the feature title. If it collides with an existing
     `artifacts/<slug>/` or `artifacts/epic-*/feature-<slug>/` folder,
     suffix `-2`, `-3`, etc.
   - Reject (regenerate from a fuller title, or ask the user) the slugs
     `prd` and `epics` — those are reserved for the two root files.

7. **Write the feature PRD**
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

     ## Touchpoints
     - ... (existing modules, files, or features this touches, from steps
       2 and 5 — omit this section entirely if none were identified)

     ## Problem Validation
     ... (only present when the `--deep` mode in step 5 triggered; omit
     otherwise)
     ```

8. **Update the product PRD**
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
- This skill reads exactly one field from `.qsbn/config.toml`
  (`submodule_root`, for scouting) and nothing else — it never reads
  delegation preferences and never writes the file.
- Scouting is best-effort and silent when it finds nothing. It must never
  block PRD writing on missing setup, a missing submodule folder, or an
  empty one — a brand-new product with no code yet is a normal case, not
  an error.
