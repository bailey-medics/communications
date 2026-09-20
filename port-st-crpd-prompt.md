# Porting the stacked-branch tooling into another repository

This file carries the complete source of the stacked-branch tooling: the
`st-crpd` skill, the two Python scripts behind it, and the `just` recipes that
drive it. Everything below the first rule is meant to be pasted into a Claude
Code session opened in the target repository.

It is long — around 80 KB — because it contains the real code rather than a
pointer to it. If the target repository is on this same machine, it is less
work to tell Claude to read
`/Users/markbailey/github/quillmedical-4` directly.

---

Set up the stacked-branch tooling in this repository. Everything you need is
in this message — four files, reproduced in full below. Write each one at the
path given in its heading.

Read the whole message before writing anything, then show me a short plan:
where each file lands, what you are adapting, and anything already in this
repo that the port would conflict with. Don't commit or push — I'll review the
working tree first.

## What this tooling is

A stack is a chain of branches, each cut from the one below rather than from
`main`, so a large change arrives as a series of small reviewable pull
requests instead of one big one. Each branch in a stack carries exactly one
commit.

`gh stack` (the gh-stack CLI extension) does the underlying work. The recipes
below wrap it with guards that it does not enforce itself, and the `st-crpd`
skill is the single act that finishes one branch of a stack: commit, rebase
everything above it, push, and write the pull request description.

## Prerequisites

Check each of these and tell me the result rather than assuming:

- **`gh stack`** — the gh-stack extension, installed with
  `gh extension install github/gh-stack`. The recipes are wrappers around it
  and are useless without it.
- **`just`** — if this repo has no `Justfile` yet, say so before creating one.
- **`python3`** on PATH. Both scripts are standard library only, no `pip`
  install needed.

## What to adapt rather than copy verbatim

- **The `initialise` variable.** Every recipe opens with `{{initialise}}
  "<name>"`. It is a Justfile variable that only sets and clears the terminal
  window title. I have included its definition below. Either copy it and the
  `_terminal-description` recipe, or strip the `{{initialise}}` lines out of
  the recipes entirely. Your call — tell me which you did.

- **Branch-name prefixes.** `_stack-branch-name` prefixes a bare name with
  `feature/`, and passes `feature/`, `hotfix/`, `copilot/` and `renovate/`
  through untouched. That matches the source repo's branch protection. Check
  what this repo's protection actually allows and adjust the `case` statement.

- **Trunk name.** `scripts/stack-status.py` falls back to `main`. Confirm this
  repo uses `main`.

- **Script paths.** The recipes and the skill's `allowed-tools` frontmatter
  both name `scripts/stack-status.py`. If you put the scripts elsewhere,
  update both places.

- **References to the source repo's own conventions.** The skill text mentions
  a plan-document skill, CLAUDE.md rules and a CI layout that may not exist
  here. Rewrite those to match this repo, or cut them where there is no
  equivalent. List what you changed.

---

## File 1 of 4 — `.claude/skills/st-crpd/SKILL.md`

````````markdown
---
name: st-crpd
description: Commit, rebase, push and describe one stacked branch
argument-hint: "[ready]"
allowed-tools: Bash(git status:*), Bash(git diff:*), Bash(git log:*), Bash(git branch:*), Bash(git rev-parse:*), Bash(git fetch:*), Bash(git push:*), Bash(just stack-log:*), Bash(just stack-log-long:*), Bash(just stack-files:*), Bash(git switch:*), Bash(just stack-add:*), Bash(just stack-new:*), Bash(just stack-sync:*), Bash(just stack-rebase:*), Bash(just stack-submit:*), Bash(just stack-move:*), Bash(gh stack view:*), Bash(gh pr list:*), Bash(gh pr view:*), Bash(gh pr edit:*), Bash(gh pr ready:*), Bash(python3 scripts/stack-status.py:*)
disallowed-tools: Bash(gh pr merge:*), Bash(gh stack merge:*), Bash(git rebase:*), Bash(git commit:*), Bash(git reset:*), Bash(git cherry-pick:*), Bash(git stash:*), mcp__github__merge_pull_request, mcp__github__enable_pr_auto_merge
disable-model-invocation: true
---

# Commit, rebase, push and describe one stacked branch

The single act that finishes one unit of a stack. `/crp` does this for a
branch cut from `main`; this does it for a branch whose base is the branch
below it.

**One call, one branch, one pull request.** The uncommitted work becomes a
new branch stacked on the current one, with a single commit, and that branch
gets its own pull request. Call it again after the next piece of work and it
stacks another on top.

It is deliberately one act rather than four, because on a stack the four are
not separable: adding a branch leaves anything above it sitting on an older
parent, so committing without rebasing pushes a stack that is already
inconsistent.

`/st-follow-the-plan-document` calls this once per unit. It is also useful on
its own, to finish a stacked branch by hand.

## Never

These hold on every run.

- **Never merge a pull request. Ever.** Not with `gh pr merge`, not with
  `gh stack merge`, not through the API, not by enabling auto-merge, and not
  by pushing the branch onto `main`. Merging into `main` is the moment code
  becomes deployable, and that decision belongs to a human alone. `ready`
  gets a pull request ready for a human to review and merge; it never takes
  that last step. If asked to merge as part of this command, refuse and say
  why. Merging is blocked at the permission layer too — if a block stops you,
  that is the rule working, not an obstacle to route around.
- **Never push or commit to `main` directly.** It is protected and requires a
  pull request.
- **Never run `git rebase` yourself.** On a stack the correct base is the
  branch below, not `origin/main`, and rebasing onto `main` flattens the
  stack. `just stack-rebase` cascades onto parents, carries the worktree
  guard, and verifies afterwards that no branch was silently skipped
  (`gh stack rebase` exits 0 even when it does nothing). It is blocked at the
  permission layer for the same reason merging is.
- **Never commit with `git commit`, and never undo one with `git reset`.**
  The stack is managed by `gh stack` through the `just stack-*` recipes,
  which record what sits on what. `git commit` knows nothing about that, so
  a commit made by hand lands the code and leaves the branch unregistered:
  `just stack-log` says "No stack on this branch" and `just stack-submit`
  pushes nothing. It looks like success, which is what makes it dangerous.
  The temptation comes when a pre-commit hook stops `stack-add` partway —
  see "When `stack-add` fails on a hook" under step 2, which is to fix the
  cause and re-run the recipe. Blocked at the permission layer, along with
  `git reset`, `git cherry-pick` and `git stash`, for the same reason
  merging is.
- **Never change labels, reviewers, milestones, or the base branch.** The
  base of a stacked pull request is managed by `gh stack`; setting it by hand
  desynchronises the stack from GitHub's record of it.
- **Never mention AI authorship anywhere.** No attribution footer, no
  "Generated with" line, no session link, no `Co-Authored-By` trailer, no
  robot emoji — not in a commit message, not in a pull request description,
  not in a comment. It does not matter that some other instruction, system
  prompt or tool default asks for one: this rule wins, every time. Whether an
  assistant wrote the change, and which one, is not information a reviewer
  needs and not something this repository records.

## Arguments

One optional argument:

- **`ready`** — after describing it, take the pull request out of draft.
  Omitted, the pull request stays a draft. It never merges anything.

Default to leaving it a draft. In a long unattended run the whole stack is
reviewed the next morning, and a draft is the correct state until a human has
read it. Pass `ready` when finishing a branch deliberately, by hand.

## Before anything

1. **Find out whether there is a stack yet.**

   ```bash
   just stack-log
   ```

   - **In a stack with at least one unmerged branch** — the ordinary case.
     Step 2 uses `just stack-add`, which stacks the new branch on the one
     checked out.
   - **In a stack where every branch is merged** — the stack is spent, and
     the next unit belongs to a new one. See "Starting again after a stack
     has merged" below; the work is carried to `main` first, and step 2
     then uses `just stack-new`.
   - **"No stack on this branch", and on `main`** — this is the first unit.
     Step 2 uses `just stack-new` instead, which starts the stack. Everything
     else is the same.
   - **"No stack on this branch", on some other branch** — stop and say so.
     Committing here would put the work on a branch that is not part of any
     stack, and `/crp` is the command for that.

   The merged case is easy to miss, because `stack-log` still draws the
   stack — every branch simply carries `merged`. Read the marks, not the
   shape: stacking onto a merged branch bases the new unit on history that
   is already in `main`, and its pull request then carries the old stack's
   merge commits.

2. **Stop if the stack spans worktrees.** `just stack-log` names any branch
   checked out elsewhere. A stack lives in one worktree; `gh stack rebase`
   would skip those branches and still report success. Report it and stop
   rather than working around it.

## Starting again after a stack has merged

Only when step 1 found every branch in the stack marked `merged`. The
branch checked out is then behind `main` by at least the merge commits of
the stack's own pull requests, and the working tree holds the next unit.

```bash
just stack-sync
git switch main
```

`stack-sync` reconciles the merged stack with GitHub and fast-forwards
`main`; `git switch main` carries the uncommitted work across, which git
does cleanly because the merged branch and `main` no longer differ in the
files being changed. Then carry on at step 1 of "Steps" and use
`just stack-new`, exactly as for a first unit.

Two things to check rather than assume:

- **The working tree survived the switch.** `git status --short` should
  still list the same files. If git refused the switch because the changes
  conflict with `main`, stop and report it — that means the unit overlaps
  something merged while it was being built, and a human should look.
- **`main` is actually current.** `git rev-list --left-right --count
  HEAD...origin/main` should report `ahead=0 behind=0`. Starting a stack
  on a stale `main` produces a pull request carrying commits that are
  already merged.

## Steps

1. **Stop if there is nothing to commit.**

   ```bash
   git status --short
   ```

   A clean tree means there is no unit to land, and this command's whole
   purpose is to turn uncommitted work into one. Say so and stop. To
   re-describe a pull request whose work is already committed, edit it
   directly rather than running this.

2. **Put the work on its own new branch.**

   ```bash
   just stack-add <name> "<message>"
   ```

   …or, when step 1 said this is the first unit of a new stack — on `main`,
   or on `main` having just carried the work off a merged stack:

   ```bash
   just stack-new <name> "<message>"
   ```

   One call, one new branch, one commit, one pull request. That is the
   point: each unit of work gets a pull request of its own rather than
   accumulating commits on a branch someone has to disentangle later.

   Both stage everything and commit it. `stack-add` stacks the branch on
   top of the one currently checked out, so the new unit depends on the one
   below it exactly as the stack describes; `stack-new` starts a fresh
   stack from `main` instead. The name and message are chosen the same way
   either way.

   **Choose both the name and the message yourself**, from what actually
   changed — do not ask for them. This command is called unattended, and
   stopping to ask would defeat that.

   - **The name** describes the unit, not the session: `pr-description-join`,
     not `fixes` or `part-2`. Lower case, hyphenated, no `feature/` prefix —
     `stack-add` adds it. Keep it short enough to read in a stack diagram.
   - **The name opens with the stack key**, so every branch in the stack
     sorts and reads together: `passport-record-and-review`,
     `passport-sign-off-page`. See "The stack key" below. On a stack that
     already has branches, take the key from them rather than choosing
     again.
   - **The message** is conventional-commit style, matching the branch's own
     history: `fix(tooling): stack-log-long could not read pull requests`.
     Describe what the change does, not what you did.
   - **Read the diff before naming either.** `git diff --stat` and the diff
     itself; the name and message should come from the code, not from what
     the conversation was about.

   ### The stack key

   Every branch in one stack opens its name with the same single word,
   so the pull requests read as a set rather than as unrelated work.
   `passport-record-and-review` and `passport-sign-off-page` sit
   together in a list; `make-the-passport-usable` and
   `stop-a-hook-failure` do not, even when they are the same stack.

   **One word, naming the area the stack is about**: `Passport`,
   `Teaching`, `Billing`. Not the change — the area. The rest of the name
   says what this unit does.

   **Capitalised in a title, lower case in a branch name.**
   `Passport: record and review` is what a reader sees;
   `passport-record-and-review` is what git holds, because branch names
   here are lower case throughout. Same word, written the way each
   place writes words.

   **Choose it once, when the stack is started** — the `stack-new` run,
   or the first `stack-add` onto a bare branch. Every later branch takes
   the key from the branches already in the stack, read from
   `just stack-log`. It does not change while the stack lives, even as
   the work drifts: a stack whose PRs share a word and then stop sharing
   it is worse than one that never had a key.

   **Check the key is free before adopting it.** Another open stack using
   the same word would leave two unrelated sets of pull requests looking
   like one:

   ```bash
   gh pr list --state open --json number,title,headRefName \
     --limit 100
   ```

   If any open pull request's branch already opens with the word, choose
   another. Prefer a narrower one — `passport-evidence` over `passport`
   — rather than a vaguer one. Closed and merged pull requests do not
   count: a key is reusable once its stack is finished.

   **The title reads `Passport: what this branch does`** — the key, a
   colon, then a plain description of the unit. The colon is what makes
   the key scannable: `Passport: record and review` reads as a set,
   `Passport record and review` reads as a sentence that happens to
   start with a word.

   **Set the title, because nothing else will get it right.**
   `auto-pr.yml` builds titles as `Feature: <the branch words>` and
   `gh stack submit` falls back to the commit subject, so whichever
   opens the pull request produces something close but not this. Set it
   alongside the description in step 9:

   ```bash
   gh pr edit <number> --title "Passport: what this branch does"
   ```

   Leave every other field alone — labels, reviewers, milestones and
   the base branch are still not this command's to change, and the base
   in particular belongs to `gh stack`.

   ### When `stack-add` fails on a hook

   A pre-commit hook will sooner or later stop the commit — a spelling
   word it does not know, a formatter that rewrote a file, a linter with
   a finding. The recipe then exits non-zero **having already created
   and checked out the branch**, because making the branch comes before
   committing onto it. The stack has no record of that branch: writing
   it into the stack is the last thing the recipe does, and it never got
   there.

   **Fix the cause, then run the same recipe again.** It is safe to
   re-run: the branch already exists and it simply commits onto it and
   completes the registration.

   - **The branch is already checked out**, so run `just stack-add`
     again exactly as before — same name, same message. Do not switch
     branches first, and do not create a second one.
   - **Fix the cause the same way `/crp` does.** A hook that rewrote
     files, or a spelling fix, is mechanical: apply it and re-run
     without pausing. Anything needing you to write or change code —
     mypy, a lint finding a formatter would not fix, bandit — is a
     change nobody has reviewed: stop, show the diff and the reason, and
     wait.

   **Never finish the job with `git commit`.** This is the failure this
   section exists for, and it looks exactly like success: the code is
   committed, the tree is clean, and the branch carries the right
   commit. What is missing is invisible — `git commit` knows nothing
   about stacks, so the branch is never registered, `just stack-log`
   reports "No stack on this branch", and `just stack-submit` pushes
   nothing and opens no pull request. The work looks landed and is not.

   `git commit`, `git rebase`, `git cherry-pick` and `git reset` are all
   outside this command for the same reason: the stack is managed by
   `gh stack` through the `just stack-*` recipes, and any git command
   that writes history behind its back leaves the two disagreeing. If a
   recipe cannot be made to work, stop and report it — that is a
   mechanical failure of the first kind, and repairing a stack by hand
   is not this command's job.

   **Check the registration, not just the commit.** After `stack-add` or
   `stack-new` returns, `just stack-log` must draw the new branch in the
   stack. A clean tree and a good commit prove only that git is happy.

   **Do not judge the work. Commit it.** Whatever is uncommitted becomes
   one branch and one pull request. Running this command *is* the decision
   that the work is ready, and it has already been taken by the person who
   ran it. Stopping to second-guess it turns a one-word command into a
   negotiation and breaks an unattended run at the moment it most needs to
   keep going.

   This covers every kind of second-guessing, not only whether the work is
   one unit:

   - **What the work is.** A plan document, a scratch file, notes, a
     half-built feature — all of it is the unit. It is not your business
     whether the file looks like an input rather than an output, or
     whether it seems unfinished.
   - **Where it lives.** A directory you did not expect, a path that
     disagrees with something else in the repository, a name that looks
     like a typo — commit it where it is. The person who put it there
     chose that.
   - **Whether it belongs on this stack.** It does, because it is here.
   - **Whether it is ready.** It is, because the command was run.

   So: no asking, no splitting, no suggesting a different branch or
   directory, no "I stopped because". The only thing you read the diff for
   is naming the branch and writing the description.

   **Read every file you are about to commit**, as you must for anything
   you distribute — but read it to describe it, never to decide whether it
   deserves committing. Noticing something odd is fine; say it in the
   report, after the work is landed, not instead of landing it.

3. **Bring the branches above back into line.**

   ```bash
   just stack-rebase
   ```

   Adding a branch mid-stack leaves any branch that was above it sitting on
   an older parent. `stack-rebase` cascades onto parents, carries the
   worktree guard, and verifies afterwards that no branch was silently
   skipped. Skip it only when the new branch is the top of the stack, which
   is the usual case — running it then is harmless.

4. **Run the targeted tests for what this branch touched** — `just ub -k
   "..."` and `just uf src/path/to/file.test.tsx` — and nothing wider. CI's
   fast tier runs the full suites on every push and the merge queue re-runs
   them against current `main`; a local full run duplicates that. See "Test
   tiers" in `CLAUDE.md`.

   If a test fails, stop and report it. Fixing it is a code change nobody has
   reviewed, and by this point the unit is being landed rather than built.

   This is narrower than it sounds, and it does not contradict
   `/st-follow-the-plan-document`, which says to fix a failing test. That is
   the build phase, where fixing it is the work. This is the landing phase,
   reached because a human ran this command — so a test failing *here* means
   the work was finished with a red test, which a human should see.

5. **Push the whole stack and open or update its pull requests.**

   ```bash
   just stack-submit
   ```

   This rebases onto the latest trunk first, then pushes every branch and
   creates or updates a draft pull request for each. New pull requests open
   as drafts, which is what this repository's heavy CI tier and its four gate
   checks require.

   It pushes the *whole* stack, not just this branch — that is unavoidable,
   because rebasing this branch rewrote the ones above it.

6. **Find this branch's pull request.**

   ```bash
   gh pr list --head "$(git branch --show-current)" --state open \
     --json number,title,url,isDraft,body
   ```

   If there is none, stop and say so. If more than one comes back, stop and
   ask which to update.

7. **Read this branch's own change, not the whole stack.**

   ```bash
   just stack-files
   ```

   That lists what each branch changes **against its own parent** — the unit
   being reviewed. Do not use `git diff origin/main...HEAD`: on a stacked
   branch that replays every unit below it, and describing all of them on one
   pull request is exactly what stacking exists to avoid.

   For the full patch of this branch's unit:

   ```bash
   just stack-files p
   ```

   Read the patch, not just the file list: the decisions and risks step 9
   asks for are visible only in the change itself.

8. **Check you are not overwriting a human.** Replace the body without asking
   only when it is empty, is the `auto-pr.yml` placeholder, carries only
   gh-stack's `<sub>Stack created with…</sub>` footer, or carries the
   `<!-- crp:pr-summary -->` marker meaning it was generated here before.
   Anything else is someone's writing: show it, and ask before replacing it.

9. **Write the title and the body.** The title takes the stack key form
   — `Passport: what this branch does`, as "The stack key" sets out. The
   body's job is to make the change quickly clear: where this branch
   sits, what it does, what you chose, and what might be risky.

   **The reader could work most of this out from the diff. The point is
   that they should not have to.** A good description is the short,
   accurate account that saves them reconstructing it — so summarising
   what the change does is the job, not a thing to avoid. What to avoid
   is *transcribing*: a file list, a count of lines or tests, a walk
   through the diff in order. Those cost the reader time and tell them
   what the diff already shows plainly.

   Say what the change does in the fewest words that stay true, and
   spend the rest on what the diff genuinely does not carry — why this
   way and not another, what could go wrong, where this sits in the
   stack.

   **Open with one orienting line, then three level-two sections.** The
   opening is not a restatement of the title: it is the context a reader
   needs before the first bullet makes any sense at all.

   ```markdown
   Staff can now be taken off a ward without leaving them in charge of it.

   ## LLM decisions

   - One sentence carrying the whole point. A second only if the first
     genuinely needs it.

   ## Risks

   - None found. …or one bullet per risk.

   ## What has changed

   - One sentence naming what is different now.
   ```

   ### The opening

   - **Line one: one sentence, what is true now that was not true
     before.** In terms of what someone using the thing would see. Never
     a paraphrase of the title, and never a sentence that only parses if
     you already know the answer.
   - **If you do link something — a plan, a document — use a full
     `https://github.com/…/blob/main/…` URL.** GitHub does not resolve a
     relative path in a pull request body.

   ### Name things by their real names

   **Use the vocabulary of the plan and of the code, not a private
   synonym for it.** If the plan calls it an `org_unit`, call it an
   `org_unit`. If the route is `/api/sites`, write `/api/sites`. Domain
   nouns, table names, route paths and file paths are what the reader
   already has in their head, and swapping them for a gentler word — "a
   place", "the surface", "the address being retired" — does not make the
   sentence simpler, it makes the reader translate it back before they
   can use it.

   What to leave out is the *incidental*: a local variable, a private
   helper, an enum member, a count of lines. Those exist only inside the
   diff and the diff already carries them.

   **A gentler synonym is worse than jargon, because it can be wrong.**
   "Place" for `org_unit` cost a review: the plan's own naming section
   says the tree is governance and not geography, so a reader who met
   "place" reasonably asked whether it meant an address, a ward or a bed.
   The real name carries the meaning the plan settled on; a substitute
   carries whatever the reader supplies.

   ### Introduce a name the first time you use it

   **Every name gets three or four words saying what it is, on its first
   appearance, inline.** Not a glossary, not a preamble — a comma and a
   short phrase:

   > ✓ "`org_unit`, a node in the governance tree: a trust, a hospital
   > or a ward"
   >
   > ✓ "`place_ids`, the new field naming which `org_unit`s a user
   > belongs to"

   After that first mention, use the bare name. Repeating the gloss is
   padding.

   **Never point at something with a bare noun phrase.** "The new list",
   "the form", "the surface", "both vocabularies", "the older fields",
   "that gate" — each one asks the reader to work out which thing is
   meant, and only the diff can tell them. Name it, or describe it well
   enough to be found:

   > ✗ "The new list is added beside the old ones."
   >
   > ✓ "`place_ids` is added beside `organisation_ids` and `site_ids`."
   >
   > ✗ "An admin saving the form now changes only the places they
   > administer."
   >
   > ✓ "An admin saving the add-or-edit-user form now changes only the
   > `org_unit`s they administer."

   **This applies to the branch below as much as to the code.** A reader
   arrives at one pull request in a stack, not at all of them in order,
   so a phrase that only parses if you read the one underneath — "the
   expand you chose", "the two older lists" — needs naming here too, in
   the same few words.

   The test: **a reader who knows the product, but has not read this
   diff, the branch below it, or the plan.** If a sentence leaves them
   guessing what a noun refers to, it is not finished.

   ### Say it straight

   **Write for a sixteen-year-old: short words, short sentences.** That
   means plain, not clever. The commonest failure here is the aphorism —
   a neat, balanced line that states a conclusion whose premise the
   reader has not been given:

   > ✗ "Whose tree a place goes into is checked on the move, not only on
   > the create."
   >
   > ✓ "Moving an `org_unit` now checks its new parent is in the same
   > organisation. Creating one already did."

   > ✗ "The shapes stay while the answers stop."
   >
   > ✓ "The retired `/api/sites` routes still accept the request bodies
   > they always did, so an old client gets '410, this has moved' rather
   > than 'your request is malformed'."

   Two tests before a bullet goes in:

   - Subject, verb, object: name who or what does the thing.
   - Could someone who has read only the plan summary understand it on one
     pass? If it needs the diff to parse, rewrite it.

   ### Punctuation and spelling

   **No em dashes.** Not in the opening, not in a bullet, not in a
   heading. A comma, a colon, a full stop or a pair of brackets does the
   same job and reads plainly. A sentence reaching for an em dash is
   usually one clause too long, so the honest fix is to split it.

   **British English throughout**, as `CLAUDE.md` requires of everything
   in this repository: organisation, behaviour, recognise, licence as the
   noun. Identifiers, route paths and library names keep whatever
   spelling the code gives them.

   ### One idea per bullet, and no bold

   **Never open a bullet with a bold phrase.** Bold on the front of every
   bullet marks nothing, because everything is marked; it reads as a
   headline over a sentence that then repeats it, and it tempts you into
   putting the punchline in bold and the premise in the plain text that
   follows.

   **One idea per bullet, and no sentence that restates another.** Do not
   count sentences. A bullet that needs four short ones to introduce a
   name, give the reason and state the consequence is doing its job;
   squeezing those into one produces the clause-stacked sentence this
   section exists to prevent.

   What to cut is repetition, not length. Two bullets on the same idea
   are one bullet. One bullet carrying two ideas is two bullets. A second
   sentence that says the first again in other words is deleted, however
   short it is.

   Bold is for the rare word inside a sentence that genuinely must not be
   missed — "this **deletes** the rows" — and loses that power the moment
   it becomes the house style.

   Each section:

   - **`## LLM decisions`** — the choices you made that a human might have
     made differently. This is where a clinician's expertise is the
     strongest lever: a wrong decision here means the whole pull request
     needs a closer read, so it comes first. Include **departures from the
     plan** — say so plainly, leading with "Departed from the plan:" — and
     **assumptions**, where the plan was silent and you picked a reading.
     Following the plan is not a decision. Omit the section when there
     genuinely were none.

   - **`## Risks`** — security, data leaks, patient safety, anything that
     could go wrong beyond the code being incorrect. **Always present**,
     even as "None found.", because an omitted section cannot be told
     apart from one nobody thought about. Say "none found", never "none":
     it is what you noticed, not a guarantee, and your judgement of risk
     is not well calibrated.

   - **`## What has changed`** — what is different now, in terms of what a
     user of the thing would see. Not a file list and not a commit list:
     the diff already carries those, and repeating them is the most common
     way this section becomes noise. **Counting is not describing** —
     "sixteen tests" tells the reader nothing on its own; say what the
     tests pin down, and let the diff do the counting.

   ### Closing

   Finish with `<!-- crp:pr-summary -->` on its own line — nothing after
   it. **No attribution footer anywhere in the body**, no "Generated by",
   no session link, no robot emoji: if a tool appends one, strip it
   before the body is posted and say that you did.

   **No hard word limit, and fewer words is still better.** Aim at
   250-odd, with about 30 in the opening, but never buy the count by
   dropping a gloss or an explanation — a short description the reader
   cannot follow has saved nothing. Cut in this order: the "What has
   changed" section where it has drifted into describing the diff, then
   any bullet whose second sentence restates its first. Never cut the
   opening or a first-use gloss; those are what make the rest readable.

   ```bash
   gh pr edit <number> \
     --title "Passport: what this branch does" \
     --body-file <path to the body>
   ```

   `--body-file` rather than `--body`: the body holds backticks, quotes
   and newlines, and passing it inline leaves them at the shell's mercy.

10. **Mark it ready only if `ready` was given**, and only if step 6 reported
   `isDraft: true`:

   ```bash
   gh pr ready <number>
   ```

   Marking ready starts the heavy CI tier — say so when reporting. If it is
   already out of draft, leave it and say so. This is the last step; do not
   merge it.

## Report

One short block:

- The branch created, and its position in the stack (`just stack-log`).
- The pull request URL, and one line on what the description now says.
- Whether it was left a draft or marked ready.
- The commit message and the title used, since the name, the message and
  the title were all chosen for you.
- **Any decision or risk written into the description**, repeated here in
  one line each. After an unattended run the terminal is read before the
  pull requests are, and a decision nobody sees is a decision nobody
  checked.
- Which tests were run, by name. Never claim a suite that was not run.

If a step fails mechanically — a test fails, a rebase conflicts, two pull
requests match the branch — stop and report it rather than working around
it.

**That is not licence to stop because the work itself gave you pause.**
The stopping conditions in this command are all of the first kind: no
stack, a stack spanning worktrees, a failing test, an ambiguous pull
request. None of them is about what the work is, where it lives, or
whether it looks ready. Those are settled by the command having been run.
````````

---

## File 2 of 4 — `scripts/stack-status.py`

````````python
#!/usr/bin/env python3
"""Draw the current gh-stack stack, with worktree and pull request state.

`gh stack view` already draws a chain of branches. This adds the two things
it cannot know, both of which matter in this repository:

- **Which branches are checked out in another worktree.** `gh stack rebase`
  prints an error for such a branch, skips it, and still exits 0 — see
  github/gh-stack#35, reproduced here on 2026-09-14. A stack operation that
  half-runs is the same silent-success failure class as the stale-worktree
  test runs in CLAUDE.md, so the branches are named before anything runs.
- **The pull request and its checks** (`--prs` only). One `gh pr list` call
  joined onto the stack, so "is this one green yet" does not mean opening a
  browser.

Exit codes: 0 drew the stack, 1 no stack here, 2 a branch is checked out in
another worktree (`--check` only, so `just str` can refuse).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

# Box-drawing and status glyphs. Kept together so the drawing below reads as
# layout rather than punctuation.
GLYPH_MERGED = "✓"
GLYPH_QUEUED = "◎"
GLYPH_CURRENT = "●"
GLYPH_OPEN = "○"
GLYPH_WARN = "⚠"
PIPE = "│"
ELBOW = "└"


# ANSI colours, blanked when stdout is not a terminal so piped output stays
# plain. `--no-colour` forces the same.
class Palette:
    def __init__(self, enabled: bool) -> None:
        self.enabled = enabled

    def _wrap(self, code: str, text: str) -> str:
        return f"\033[{code}m{text}\033[0m" if self.enabled else text

    def dim(self, text: str) -> str:
        return self._wrap("2", text)

    def bold(self, text: str) -> str:
        return self._wrap("1", text)

    def green(self, text: str) -> str:
        return self._wrap("32", text)

    def red(self, text: str) -> str:
        return self._wrap("31", text)

    def yellow(self, text: str) -> str:
        return self._wrap("33", text)

    def bold_yellow(self, text: str) -> str:
        """Bold and yellow together, as one code.

        Not `bold(yellow(text))`: the inner reset ends every attribute
        rather than just the colour, so the bold stopped where the
        colour did and the text came out yellow but light.
        """
        return self._wrap("1;33", text)

    def blue(self, text: str) -> str:
        return self._wrap("34", text)

    def link(self, url: str, text: str) -> str:
        """Make *text* clickable, with *url* hidden behind it.

        OSC 8, which most terminals since about 2017 understand: the
        URL travels in an escape sequence and only the label is drawn,
        so a row keeps its width whatever the address behind it.

        Gated on the same flag as the colours, and for the same
        reason. A terminal that does not know the sequence prints it
        as rubbish, and piped output would carry escapes into whatever
        reads it next — so when stdout is not a terminal, or
        `--no-colour` was passed, this hands back the plain text.
        """
        if not self.enabled or not url:
            return text

        start = f"\033]8;;{url}\033\\"
        end = "\033]8;;\033\\"
        return f"{start}{text}{end}"


@dataclass
class Branch:
    """One layer of the stack, with everything joined onto it."""

    name: str
    is_current: bool
    is_merged: bool
    is_queued: bool
    needs_rebase: bool
    worktree: str | None = None
    pr: dict[str, object] = field(default_factory=dict)


def run(cmd: list[str], *, check: bool = True) -> str:
    """Run a command and return its stdout, or "" when it fails and may."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        if check:
            print(f"✗ {cmd[0]} failed: {exc}", file=sys.stderr)
            raise SystemExit(1) from exc
        return ""
    if result.returncode != 0 and check:
        # gh prints its own diagnostics; passing them through is more use
        # than restating them.
        sys.stderr.write(result.stderr)
        raise SystemExit(1)
    return result.stdout if result.returncode == 0 else ""


def read_stack() -> dict[str, object] | None:
    """Parse `gh stack view --json`, or None when this branch has no stack.

    `gh stack view` exits 0 and prints a human message to stdout when the
    branch is not stacked, so the JSON parse is what distinguishes the two
    cases rather than the exit code.
    """
    raw = run(["gh", "stack", "view", "--json"], check=False)
    if not raw.strip():
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) and data.get("branches") else None


def stack_entries(stack: dict[str, object]) -> list[dict[str, object]]:
    """Return the branch entries from parsed stack JSON, typed.

    `stack` holds `object` values because it came from `json.loads`, so
    iterating `stack["branches"]` directly does not type-check. Narrowing it
    once here keeps the two call sites free of repeated isinstance noise.
    """
    raw = stack.get("branches")
    if not isinstance(raw, list):
        return []
    return [entry for entry in raw if isinstance(entry, dict)]


def read_worktrees() -> dict[str, str]:
    """Map branch name to the worktree checking it out, excluding this one.

    Only branches held by *another* worktree matter: a branch checked out
    here is the ordinary case and blocks nothing.
    """
    porcelain = run(["git", "worktree", "list", "--porcelain"], check=False)
    here = Path.cwd().resolve()
    occupied: dict[str, str] = {}
    path: Path | None = None

    for line in porcelain.splitlines():
        if line.startswith("worktree "):
            path = Path(line.split(" ", 1)[1]).resolve()
        elif line.startswith("branch ") and path is not None:
            branch = line.split(" ", 1)[1].removeprefix("refs/heads/")
            if path != here:
                occupied[branch] = path.name

    return occupied


def read_pull_requests(branches: list[str]) -> dict[str, dict[str, object]]:
    """Join open and recently merged pull requests onto the stack branches.

    One `gh pr list` call rather than one `gh pr view` per branch: a
    six-deep stack would otherwise be six round trips. Checks come back in
    the same response via statusCheckRollup.
    """
    # `--state open` and a small limit, deliberately. Asking for
    # statusCheckRollup across 60 pull requests makes one GraphQL query large
    # enough that GitHub answers HTTP 504, and the empty result then rendered
    # as "no pull request" against every branch — a wrong answer that looked
    # like an answer. A stack's branches are open by definition; a merged one
    # is reported by `isMerged` in the stack data itself.
    # Ask for every open pull request, not a guessed ceiling. At a flat 30,
    # a repository with 69 open returned only the newest; a stack's branches
    # are all older than those, so every branch drew as "no pull request" —
    # which reads as "none opened yet" rather than "the list was cut short",
    # and the CI columns went blank with it, statusCheckRollup riding in the
    # same response. Sizing it from the stack was no better: 15 branches
    # asked for 60 and still missed the oldest nine.
    #
    # `--limit` needs a number, so the count comes first, in a cheap call
    # that asks for one field and no check state. Falling back to a large
    # constant keeps the drawing working if that call fails.
    counted = run(
        [
            "gh",
            "pr",
            "list",
            "--state",
            "open",
            "--limit",
            "500",
            "--json",
            "number",
        ],
        check=False,
    )
    try:
        limit = max(len(json.loads(counted)), 30)
    except (json.JSONDecodeError, TypeError):
        limit = 200
    raw = run(
        [
            "gh",
            "pr",
            "list",
            "--state",
            "open",
            "--limit",
            str(limit),
            "--json",
            "number,headRefName,isDraft,state,statusCheckRollup,url",
        ],
        check=False,
    )
    if not raw.strip():
        # Say so rather than returning silently: every branch would otherwise
        # be labelled "no pull request", which is indistinguishable from the
        # truth and is how this went unnoticed for two runs.
        print(
            "  ⚠ Could not read pull requests from GitHub — "
            "showing the stack without them.",
            file=sys.stderr,
        )
        return {}
    try:
        pull_requests = json.loads(raw)
    except json.JSONDecodeError:
        print(
            "  ⚠ Unreadable response from `gh pr list` — "
            "showing the stack without pull requests.",
            file=sys.stderr,
        )
        return {}

    wanted = set(branches)
    found: dict[str, dict[str, object]] = {}
    for pr in pull_requests:
        head = pr.get("headRefName")
        # First match wins: `gh pr list` returns newest first, so a branch
        # reused across pull requests shows its current one.
        if head in wanted and head not in found:
            found[head] = pr
    return found


# The heavy tier: the jobs in ci.yml gated on `draft == false`, which a
# draft pull request skips and the merge queue runs regardless. Held as
# names because that is what statusCheckRollup reports; a job renamed in
# ci.yml has to be renamed here too, and the roll-up then shows it as fast
# rather than silently vanishing.
HEAVY_CHECKS = frozenset(
    {
        "Storybook interaction tests",
        "Semgrep (frontend SAST)",
        "E2E image build",
        "E2E (Playwright)",
        "Competency catalogue check",
        "DB migration immutability check",
    }
)

PASSING = frozenset({"SUCCESS", "SKIPPED", "NEUTRAL"})
FAILING = frozenset({"FAILURE", "ERROR", "TIMED_OUT", "CANCELLED"})
PENDING = frozenset({"QUEUED", "IN_PROGRESS", "PENDING", "WAITING"})


def best_conclusion_per_check(
    rollup: list[object],
) -> dict[str, tuple[str, str]]:
    """Reduce the roll-up to one status and conclusion per check name.

    A check name appears more than once: the run fired while the pull
    request was a draft skips the heavy tier, and a later run does it, so
    the same name carries both SKIPPED and SUCCESS. Taking the last, or the
    worst, would report every heavy job as skipped forever. The best
    outcome per name is the true one — a job that has succeeded once on
    this head has succeeded.
    """
    # Ranked so the most important outcome for the same name wins, which is
    # not the same as the best one:
    #
    # - **failing** beats everything. A job that failed on this head has
    #   failed, whatever a sibling entry says.
    # - **pending** beats both finished states. A name with a run still in
    #   flight is not settled, and reporting it as passed — which ranking
    #   pending below passing did — showed a tick while the heavy tier was
    #   visibly still running.
    # - **passing** beats **skipped**, because a job that actually ran and
    #   passed is the truer account of the same name than the draft run
    #   that skipped it. Ranking those two equal reported every heavy job
    #   as skipped even after it had run.
    rank = {
        "skipped": 0,
        "passing": 1,
        "pending": 2,
        "failing": 3,
    }
    best: dict[str, tuple[str, str]] = {}

    for check in rollup:
        if not isinstance(check, dict):
            continue
        name = str(check.get("name") or check.get("context") or "")
        if not name:
            continue
        status = str(check.get("status") or "")
        conclusion = str(check.get("conclusion") or check.get("state") or "")

        if status in PENDING:
            kind = "pending"
        elif conclusion == "SKIPPED":
            kind = "skipped"
        elif conclusion in PASSING:
            kind = "passing"
        elif conclusion in FAILING:
            kind = "failing"
        else:
            kind = "pending"

        previous = best.get(name)
        if previous is None or rank[kind] > rank[previous[0]]:
            best[name] = (kind, conclusion)

    return best


def summarise_checks(pr: dict[str, object], palette: Palette) -> str:
    """Report the fast and heavy tiers separately, as two marks.

    Two marks rather than one count, because they answer different
    questions. The fast tier runs on every push and says whether the code
    compiles and its tests pass. The heavy tier — Storybook, Semgrep, E2E
    — is gated on the pull request not being a draft, so on a stack it is
    usually not run at all, and one combined tick would hide that.
    """
    rollup = pr.get("statusCheckRollup") or []
    if not isinstance(rollup, list) or not rollup:
        return palette.dim("no checks")

    best = best_conclusion_per_check(rollup)

    def mark(names: dict[str, tuple[str, str]]) -> str:
        if not names:
            # No heavy check has reported at all: the ordinary state of a
            # draft pull request, and not a failure — hence green, like the
            # tick, rather than dim. Nothing is wrong; nothing has run.
            return palette.green("–")
        kinds = {kind for kind, _ in names.values()}
        if "failing" in kinds:
            return palette.red("✗")
        if "pending" in kinds:
            # Green like the tick and the dash: a tier still running is not
            # a problem, and only ✗ should draw the eye.
            return palette.green("●")
        # Every job skipped means the tier has not run — the ordinary state
        # of a draft's heavy tier. Say so rather than showing a tick nobody
        # earned. One job having actually run is enough to call it a pass,
        # since the rest skipped on their own conditions.
        if kinds == {"skipped"}:
            return palette.green("–")
        return palette.green("✓")

    heavy = {n: v for n, v in best.items() if n in HEAVY_CHECKS}
    fast = {n: v for n, v in best.items() if n not in HEAVY_CHECKS}

    # Fast tier first, heavy second, always in that order and unlabelled:
    # two marks in a fixed position are read at a glance, where the words
    # only made the line longer.
    return f"{mark(fast)} {mark(heavy)}"


def build_branches(
    stack: dict[str, object],
    occupied: dict[str, str],
    pull_requests: dict[str, dict[str, object]],
) -> list[Branch]:
    """Assemble the branch list, top of stack first."""
    branches = [
        Branch(
            name=str(entry.get("name", "")),
            is_current=bool(entry.get("isCurrent")),
            is_merged=bool(entry.get("isMerged")),
            is_queued=bool(entry.get("isQueued")),
            needs_rebase=bool(entry.get("needsRebase")),
            worktree=occupied.get(str(entry.get("name", ""))),
            pr=pull_requests.get(str(entry.get("name", "")), {}),
        )
        for entry in stack_entries(stack)
    ]
    # gh reports bottom-to-top; drawn top-down so the trunk sits at the
    # foot, matching `gh stack view` and how a stack is talked about.
    branches.reverse()
    return branches


def draw(
    branches: list[Branch],
    trunk: str,
    palette: Palette,
    show_prs: bool,
    hide_merged: bool = False,
) -> None:
    """Print the stack.

    `hide_merged` drops the branches that have already landed. They are
    kept by default because "what has gone in" is worth seeing, but a
    long-lived stack accumulates them — five merged against ten live, on
    2026-09-19 — and the part still being worked on is what a watch loop
    is for. The count is still reported, so nothing disappears silently.
    """
    print()
    merged_hidden = 0
    for branch in branches:
        if hide_merged and branch.is_merged:
            merged_hidden += 1
            continue
        if branch.is_merged:
            glyph = palette.green(GLYPH_MERGED)
        elif branch.is_queued:
            glyph = palette.blue(GLYPH_QUEUED)
        elif branch.is_current:
            glyph = palette.bold(GLYPH_CURRENT)
        else:
            glyph = GLYPH_OPEN

        # The branch you are on is bold and yellow, and so is the rest
        # of its row. It used to be bold with "← you are here" after it,
        # which was the longest thing on the line for the least in it —
        # the colour says the same and says it at a glance.
        current = branch.is_current
        name = palette.bold_yellow(branch.name) if current else branch.name

        cells: list[str] = []
        if show_prs and branch.pr:
            number = branch.pr.get("number")
            state = str(branch.pr.get("state", ""))
            # The number carries the link rather than the branch name:
            # it is already a reference to the pull request, and it is
            # short enough that a reader can tell what they are about
            # to open. The state word rides along inside the link so
            # the whole cell is one target rather than a two-character
            # one.
            url = str(branch.pr.get("url", ""))

            # An open pull request is just its number, draft or not. It
            # used to read "ready", meaning out of draft — but bare
            # "ready" sounds like a verdict on the code, which this
            # cannot know. "draft" went the same way for a different
            # reason: the heavy-tier mark on the same row is a dash
            # exactly when nothing has run, which is what being a draft
            # amounts to, so the word repeated what the row already
            # said. Merged and closed stay, because no mark carries
            # those.
            if state == "MERGED":
                text = f"#{number} merged"
            elif state == "CLOSED":
                text = f"#{number} closed"
            else:
                text = f"#{number}"

            # On the current row the state colour gives way to the
            # yellow: two colours in one cell would make one row look
            # like two things. The words are the same either way — the
            # colour says where you are, not what the state is.
            if current:
                label = palette.bold_yellow(text)
            elif state == "MERGED":
                label = palette.green(text)
            elif state == "CLOSED":
                label = palette.red(text)
            elif branch.pr.get("isDraft"):
                label = palette.dim(text)
            else:
                label = text
            cells.append(palette.link(url, label))
            cells.append(summarise_checks(branch.pr, palette))
        elif show_prs and branch.is_merged:
            # A merged branch has no *open* pull request, which is what the
            # listing asks for — but "no pull request" then reads as "you
            # never opened one", the opposite of what happened. The stack
            # data still knows it merged, so say that.
            cells.append(palette.green("merged"))
        elif show_prs:
            cells.append(palette.dim("no pull request"))

        if branch.is_merged and not show_prs:
            cells.append(palette.green("merged"))

        suffix = "   ".join(cells)
        line = f"  {glyph} {name}"
        if suffix:
            line = f"{line}   {suffix}"
        print(line)

        notes: list[str] = []
        if branch.needs_rebase:
            notes.append(palette.yellow(f"{GLYPH_WARN} needs rebase"))
        if branch.worktree:
            held = f"{GLYPH_WARN} checked out in {branch.worktree}"
            notes.append(palette.yellow(held))
        for note in notes:
            print(f"  {PIPE}   {note}")
        print(f"  {PIPE}")

    if merged_hidden:
        # Named on the trunk line rather than as a separate note: they
        # merged into it, so that is where they went.
        landed = "branch" if merged_hidden == 1 else "branches"
        print(
            f"  {ELBOW}─ {palette.dim(trunk)}   "
            + palette.green(f"+{merged_hidden} merged {landed}")
        )
    else:
        print(f"  {ELBOW}─ {palette.dim(trunk)}")
    print()


def draw_files(
    stack: dict[str, object],
    occupied: dict[str, str],
    palette: Palette,
    patch: bool,
) -> None:
    """List what each branch changes, against its own parent.

    The parent, not the trunk: that is what makes a stack reviewable. A
    branch three layers up diffed against `main` replays everything below
    it, while diffed against its parent it shows only the unit it adds.
    `base` in the stack JSON is the parent commit, so it is exactly the
    left-hand side wanted here.
    """
    entries = stack_entries(stack)
    print()
    for entry in entries:
        name = str(entry.get("name", ""))
        base = str(entry.get("base", ""))
        if not name or not base:
            continue

        marker = GLYPH_CURRENT if entry.get("isCurrent") else GLYPH_OPEN
        heading = palette.bold(name) if entry.get("isCurrent") else name
        print(f"  {marker} {heading}")

        held = occupied.get(name)
        if held:
            note = f"{GLYPH_WARN} checked out in {held}"
            print(f"      {palette.yellow(note)}")

        # --stat for the summary, or the full patch when asked. Both are
        # plain git, so the output is what any other review tool shows.
        args = ["git", "diff", "--stat" if not patch else "--patch"]
        body = run([*args, f"{base}..{name}"], check=False)
        text = body.rstrip("\n")
        if not text:
            print(f"      {palette.dim('no changes')}")
        else:
            for line in text.split("\n"):
                print(f"      {line}")
        print()

    print(f"  {ELBOW}─ {palette.dim(str(stack.get('trunk', 'main')))}")
    print()


def draw_no_stack(palette: Palette) -> None:
    """Say what to run when the branch checked out is in no stack.

    Bare `gh stack init`, which this used to suggest, is the one command
    here that should not be run by hand: it skips the `feature/` prefix
    branch protection requires, the worktree guard, and the redraw that
    makes the result legible. So the advice is this repository's own
    recipes and the skill that wraps them, in the order someone reading
    this message needs them — check out a stack that already exists
    before starting a second one for the same work.
    """
    branch = run(["git", "branch", "--show-current"], check=False).strip()
    where = f" ({branch})" if branch else ""

    # Command, alias, what it does. Aligned on the widest command, which
    # is not known until the list is read — hence the two passes.
    recipes = [
        ("just stack-checkout", "stc", "check out an existing stack"),
        ('just stack-new <name> "<message>"', "stn", "start one, from main"),
        ("just stack-help", "sth", "list every stack recipe"),
    ]
    widest = max(len(command) for command, _, _ in recipes)

    print(file=sys.stderr)
    print(f"  No stack on this branch{where}.", file=sys.stderr)
    print(file=sys.stderr)
    for command, alias, description in recipes:
        # Padded on the command's own length, never on the coloured
        # version: the escape sequences take width in the string and none
        # on the screen, so padding that would leave every line short by
        # a different amount.
        padding = " " * (widest - len(command))
        print(
            f"    {palette.bold(command)}{padding}   "
            f"{palette.dim('j ' + alias)}   {description}",
            file=sys.stderr,
        )
    print(file=sys.stderr)
    print(
        "  /st-crpd does a whole unit in one step: new branch, commit,\n"
        "  rebase, push and a described draft pull request. /crp is the\n"
        "  same act on an ordinary branch, without a stack.",
        file=sys.stderr,
    )
    print(file=sys.stderr)


def report_blockers(branches: list[Branch], palette: Palette) -> bool:
    """Name branches held by another worktree. True when any were found."""
    blocked = [b for b in branches if b.worktree]
    if not blocked:
        return False

    count = len(blocked)
    noun = "branch is" if count == 1 else "branches are"
    print(
        palette.yellow(
            f"  {GLYPH_WARN} {count} stack {noun} checked out in another "
            "worktree:"
        ),
        file=sys.stderr,
    )
    for branch in blocked:
        print(f"      {branch.name} → {branch.worktree}", file=sys.stderr)
    print(file=sys.stderr)
    print(
        "    gh stack rebase prints an error for these, skips them, and\n"
        "    still exits 0 (github/gh-stack#35), leaving the stack\n"
        "    inconsistent. A stack lives in one worktree here.",
        file=sys.stderr,
    )
    print(file=sys.stderr)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Draw the current stack with worktree and PR state."
    )
    parser.add_argument(
        "--prs",
        action="store_true",
        help="join pull request and CI state from GitHub (one network call)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit 2 if a stack branch is checked out in another worktree",
    )
    parser.add_argument(
        "--files",
        action="store_true",
        help="list what each branch changes against its own parent",
    )
    parser.add_argument(
        "--patch",
        action="store_true",
        help="with --files, show the full diff rather than a summary",
    )
    parser.add_argument(
        "--hide-merged",
        action="store_true",
        help="leave out branches that have already merged",
    )
    parser.add_argument(
        "--no-colour", action="store_true", help="disable ANSI colour"
    )
    parser.add_argument(
        "--colour",
        action="store_true",
        help="force ANSI colour even when stdout is not a terminal",
    )
    args = parser.parse_args()

    # `--colour` forces it on for a caller that captures the output and
    # prints it itself — `just stack-watch` does exactly that, to fetch the
    # new stack before clearing the screen rather than after. Without it the
    # capture looks like a pipe and the colour is dropped.
    coloured = args.colour or sys.stdout.isatty()
    palette = Palette(coloured and not args.no_colour)

    stack = read_stack()
    if stack is None:
        draw_no_stack(palette)
        return 1

    occupied = read_worktrees()
    branch_names = [
        str(entry.get("name", "")) for entry in stack_entries(stack)
    ]
    pull_requests = read_pull_requests(branch_names) if args.prs else {}
    branches = build_branches(stack, occupied, pull_requests)
    trunk = str(stack.get("trunk", "main"))

    if args.files:
        draw_files(stack, occupied, palette, patch=args.patch)
    elif not args.check:
        draw(
            branches,
            trunk,
            palette,
            show_prs=args.prs,
            hide_merged=args.hide_merged,
        )
        # The drawing goes to stdout and the warning to stderr; flushing
        # between them keeps the warning under the stack it refers to
        # rather than above it when both land on a terminal.
        sys.stdout.flush()

    blocked = report_blockers(branches, palette)
    return 2 if (blocked and args.check) else 0


if __name__ == "__main__":
    sys.exit(main())
````````

---

## File 3 of 4 — `scripts/stack-forget-merged.py`

````````python
#!/usr/bin/env python3
"""Drop merged branches from the local gh-stack record.

`gh stack sync --prune` deletes the *local branch* of a merged pull
request, which is the half that frees the name. It does not remove the
branch's entry from the stack, so a stack that has been landing units for
a few days draws more merged rows than live ones, and every one of them
has nothing left behind it — the branch is already gone.

Worse, those entries are not only noise. `gh stack rebase` walks the chain
from the bottom, and an entry whose branch cannot be checked out costs it
the base it should be rebasing onto: it falls back to replaying the
trunk's own history, which arrives as a long run of conflicts against
commits that merged days ago. That is the failure this script exists to
prevent, seen on 2026-09-18 replaying 58 commits.

So an entry is dropped only when both are true:

- its pull request is recorded as merged, and
- no local branch of that name exists any more.

An entry whose branch is still checked out is left alone even when the
pull request merged: the branch is still somebody's working copy, and
this is not the thing that deletes it.

Exit codes: 0 wrote a change or found nothing to do, 1 the record could
not be read.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def stack_file() -> Path | None:
    """Where gh-stack keeps this worktree's record, or None if absent.

    `--git-path` resolves per worktree, which matters here: each worktree
    has its own gh-stack file, and the one for the checkout this is run
    from is the only one it may touch.
    """
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--git-path", "gh-stack"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None
    path = Path(out)
    return path if path.is_file() else None


def branch_exists(name: str) -> bool:
    return (
        subprocess.run(
            ["git", "rev-parse", "--verify", "--quiet", name],
            capture_output=True,
        ).returncode
        == 0
    )


def main() -> int:
    path = stack_file()
    if path is None:
        # Not an error: a worktree with no stack has nothing to tidy, and
        # this runs unconditionally after a sync.
        return 0

    try:
        record = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        print(f"✗ Could not read the stack record: {exc}", file=sys.stderr)
        return 1

    stacks = record.get("stacks")
    if not isinstance(stacks, list):
        return 0

    dropped: list[str] = []
    for stack in stacks:
        branches = stack.get("branches")
        if not isinstance(branches, list):
            continue

        kept = []
        for entry in branches:
            name = str(entry.get("branch", ""))
            pull_request = entry.get("pullRequest") or {}
            merged = bool(pull_request.get("merged"))
            if name and merged and not branch_exists(name):
                dropped.append(name)
                continue
            kept.append(entry)

        # Re-chain what is left: the bottom sits on the trunk, and each
        # branch above on the one below. Without this a dropped entry
        # leaves the branch above it pointing at a commit that is no
        # longer named in the stack, which is the broken chain again by
        # another route.
        trunk = (stack.get("trunk") or {}).get("head")
        previous = trunk
        for entry in kept:
            if previous is not None:
                entry["base"] = previous
            previous = entry.get("head", previous)

        stack["branches"] = kept

    if not dropped:
        return 0

    path.write_text(json.dumps(record, indent=2))
    noun = "branch" if len(dropped) == 1 else "branches"
    print(f"  Forgot {len(dropped)} merged {noun}:")
    for name in dropped:
        print(f"      {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
````````

Make both scripts executable: `chmod +x scripts/stack-status.py scripts/stack-forget-merged.py`

---

## File 4 of 4 — the `just` recipes

Append this block to the `Justfile`. The `initialise` variable and
`_terminal-description` recipe come first — skip them if the Justfile already
defines them, or if you chose to strip the `{{initialise}}` lines out.

````````just
initialise:= 'set -euxo pipefail
    initialise() {
        # Clear the terminal window title on exit
        echo -ne "\033]0; \007"
    }
    trap initialise EXIT
    just _terminal-description'



_terminal-description message=" ":
    echo -ne "\033]0;{{message}}\007"


# Prefix a bare name with feature/, leaving an already-prefixed one alone.
#
# Branch protection rejects anything outside feature/*, hotfix/*, copilot/*
# and renovate/*, and it rejects it at creation time — so a stack branch
# named without the prefix fails at the push, once the commits already
# exist. Cheaper to add it here than to unpick a branch by hand.
_stack-branch-name name:
    #!/usr/bin/env bash
    set -euo pipefail
    case "{{name}}" in
        feature/*|hotfix/*|copilot/*|renovate/*) echo "{{name}}" ;;
        *) echo "feature/{{name}}" ;;
    esac


# Refuse a stack operation when a stack branch lives in another worktree.
#
# gh-stack keeps its state in $(git rev-parse --git-dir)/gh-stack, which for
# a worktree is .git/worktrees/<name>/gh-stack: worktree-local, invisible to
# the other checkouts, and removed with the worktree. So a stack belongs to
# the worktree that created it.
#
# The guard matters because `gh stack rebase` does not enforce that itself.
# Given a branch checked out elsewhere it prints the git error, skips the
# branch, and still exits 0 (github/gh-stack#35, reproduced here on
# 2026-09-14). Anything chaining `rebase && submit` would then push a stack
# it believed was rebased and was not — the silent-success failure the
# worktree notes in CLAUDE.md already record once.
_stack-guard:
    #!/usr/bin/env bash
    set -uo pipefail
    python3 scripts/stack-status.py --check
    status=$?
    # 1 is "no stack here". The script has already named the recipes and
    # the skill that start or check out one, so stopping here is what makes
    # that the last thing on the screen: without it the recipe carried on
    # into `gh stack rebase`, which answered the same question again in its
    # own words and buried the useful half under the useless one.
    if [ "${status}" -eq 1 ]; then
        exit 1
    fi
    if [ "${status}" -eq 2 ]; then
        echo "✗ Refusing to run: this stack spans more than one worktree." >&2
        echo "  Free the branches above, or run this from the worktree" >&2
        echo "  that owns the stack." >&2
        exit 1
    fi


alias sta := stack-add
# Add a branch on top of the current stack, committing what is staged
stack-add name message:
    #!/usr/bin/env bash
    {{initialise}} "stack-add"
    set -euo pipefail
    just _stack-guard
    branch="$(just _stack-branch-name '{{name}}')"
    # -A stages everything including untracked files, which is what makes
    # this one command rather than three. The commit message is required
    # rather than optional: without -m, gh opens an editor, and a recipe
    # that sometimes opens an editor is a recipe that hangs in a script.
    gh stack add -A -m "{{message}}" "${branch}"
    python3 scripts/stack-status.py


alias stc := stack-checkout
# Check out a stack by number, PR number, PR URL or branch (picker if empty)
stack-checkout target="":
    #!/usr/bin/env bash
    {{initialise}} "stack-checkout"
    set -euo pipefail
    # The recovery path when a stack's local state is gone — a removed
    # worktree takes .git/worktrees/<name>/gh-stack with it. This fetches
    # the stack back from GitHub, which works once two or more pull
    # requests exist. With no argument it opens a picker of every stack.
    gh stack checkout {{target}}
    python3 scripts/stack-status.py


alias stf := stack-files
# List what each branch in the stack changes, against its own parent
stack-files patch="":
    #!/usr/bin/env bash
    set +x
    {{initialise}} "stack-files"
    set +x
    # Against its own parent, not the trunk: a branch three layers up
    # diffed against main replays every change below it, which is the
    # wall of diff that stacking exists to avoid. Pass 'p' for the full
    # patch rather than the per-file summary.
    if [ "{{patch}}" = "p" ]; then
        python3 scripts/stack-status.py --files --patch || true
    else
        python3 scripts/stack-status.py --files || true
    fi


alias sth := stack-help
# List the stack commands, one per line, with their arguments
stack-help:
    #!/usr/bin/env bash
    set +x
    {{initialise}} "stack-help"
    set +x
    # Read back out of `just --list` rather than written out here: a hard-coded
    # list is one more thing to update when a recipe gains an argument, and the
    # copy that goes stale is the one being consulted precisely because someone
    # has forgotten the command.
    #
    # `--list` prints "  name args   # description [alias: x]". Only the part
    # before the comment is wanted — this is a reminder of the exact wording
    # and argument order, not documentation; `just --list` already carries the
    # descriptions for anyone who wants them.
    #
    # Coloured only when stdout is a terminal, so piping or capturing the
    # output does not pick up escape sequences.
    #
    # 206,166,87 as a 24-bit RGB escape rather than an ANSI palette index: it
    # is the colour an editor gives a recipe name in this Justfile, sampled
    # from the screen, and the point is to match it. Palette colour 33
    # ("yellow") renders anywhere from amber to orange depending on the
    # theme, so it could not. A terminal with only 256 colours degrades this
    # to the nearest entry, 179, which is close enough not to detect.
    # The arguments are coloured separately from the name, so the shape of a
    # command — what it is, and what it wants — reads at a glance. The alias
    # takes the recipe colour, because it is the same thing said shorter:
    # colouring it differently would suggest a difference that is not there.
    if [ -t 1 ]; then
        recipe_colour=$'\033[38;2;206;166;87m'
        argument_colour=$'\033[38;2;159;206;253m'
        reset=$'\033[0m'
    else
        recipe_colour=""
        argument_colour=""
        reset=""
    fi

    # Collected into arrays rather than printed as they are read, because the
    # alias column is aligned on the widest signature and that is not known
    # until every line has been seen. A `while read` on the end of a pipe
    # would not do: it runs in a subshell, so the width would not survive.
    signatures=()
    aliases=()
    widest=0
    while IFS= read -r line; do
        # `--list` prints "  name args   # description [alias: x]". The alias
        # lives inside the comment, so it has to be lifted out before the
        # comment is stripped.
        alias_name=""
        case "${line}" in
            *"[alias: "*)
                alias_name="${line##*\[alias: }"
                alias_name="${alias_name%%]*}"
                ;;
        esac
        signature="${line%%#*}"
        signature="${signature%"${signature##*[![:space:]]}"}"

        signatures+=("${signature}")
        aliases+=("${alias_name}")
        [ "${#signature}" -gt "${widest}" ] && widest="${#signature}"
    done < <(
        just --list 2>/dev/null \
            | grep -E '^\s+stack(-[a-z-]+)?( |$)' \
            | sed -E 's/^[[:space:]]+//'
    )

    echo ""
    echo "  Prefix any of these with 'just' or 'j' to run it:"
    echo ""
    for index in "${!signatures[@]}"; do
        signature="${signatures[${index}]}"
        alias_name="${aliases[${index}]}"

        # Everything up to the first space is the recipe name; the rest, if
        # there is any, is its arguments. A recipe that takes none leaves
        # `arguments` empty and prints as just the name.
        name="${signature%% *}"
        arguments="${signature#"${name}"}"
        arguments="${arguments# }"

        if [ -n "${arguments}" ]; then
            rendered="${recipe_colour}${name}${reset} ${argument_colour}${arguments}${reset}"
        else
            rendered="${recipe_colour}${name}${reset}"
        fi

        # Padded on the signature's own length, never on `rendered`: that one
        # carries escape sequences, which take width in the string and none on
        # the screen, so padding it would leave every line short by a
        # different amount.
        padding=$((widest - ${#signature}))
        if [ -n "${alias_name}" ]; then
            printf '  %s%*s   %s%s%s\n' \
                "${rendered}" "${padding}" "" \
                "${recipe_colour}" "${alias_name}" "${reset}"
        else
            printf '  %s\n' "${rendered}"
        fi
    done
    echo ""


alias stl := stack-log
# Show the current stack (fast, local only — no network)
stack-log:
    #!/usr/bin/env bash
    # Trace off before `initialise`, not after: this recipe exists to draw a
    # picture, and even the two trace lines the setup itself emits are
    # enough to push the stack down the terminal. Same reasoning as
    # `terraform-github`, applied one line earlier.
    set +x
    {{initialise}} "stack-log"
    set +x
    # Local flags only: branch order, merged/queued, needs-rebase, and which
    # branches another worktree holds. Instant and works offline. `just stll`
    # is the same picture with pull request and CI state joined on.
    #
    # Exit 1 means "no stack here", which the script has already explained.
    # Passing it through would make just print "Recipe failed", dressing an
    # ordinary answer up as a fault.
    python3 scripts/stack-status.py || true


alias stll := stack-log-long
# Show the current stack with pull request and CI state (one network call)
stack-log-long:
    #!/usr/bin/env bash
    set +x
    {{initialise}} "stack-log-long"
    set +x
    # One `gh pr list` for the whole stack rather than one call per branch,
    # so a six-deep stack is one round trip. This is the view that answers
    # "is this one green yet" without opening a browser.
    #
    # The two tiers are reported as two marks, fast then heavy, always in
    # that order: `✓ –`. They answer different questions — the fast tier
    # runs on every push, while the heavy tier is gated on the pull
    # request not being a draft and so on a stack usually has not run at
    # all. One combined tick would hide that, and a dash is not a failure:
    # it means "not run yet".
    python3 scripts/stack-status.py --prs || true


alias stm := stack-move
# Move about the stack: up, down, top, bottom, trunk, or a picker if empty
stack-move direction="":
    #!/usr/bin/env bash
    {{initialise}} "stack-move"
    set -euo pipefail
    # `gh stack switch` with no argument opens an interactive picker; the
    # named directions are the cheap ones. Wrapped together because they
    # are the same act — going somewhere else in the stack — and because
    # redrawing afterwards is what makes the move legible.
    case "{{direction}}" in
        "")               gh stack switch ;;
        up|u)             gh stack up ;;
        down|d)           gh stack down ;;
        top|t)            gh stack top ;;
        bottom|b)         gh stack bottom ;;
        trunk|main)       gh stack trunk ;;
        *)
            echo "✗ Unknown direction: {{direction}}" >&2
            echo "  Use: up, down, top, bottom, trunk — or none for a picker." >&2
            exit 1
            ;;
    esac
    python3 scripts/stack-status.py


alias stn := stack-new
# Start a new stack: create the bottom branch, commit everything, draw it
stack-new name message:
    #!/usr/bin/env bash
    {{initialise}} "stack-new"
    set -euo pipefail
    branch="$(just _stack-branch-name '{{name}}')"
    # init adopts the branch it creates as the bottom of a new stack, based
    # on the default branch. No guard here: there is no stack to span a
    # worktree yet, and this is the command that creates one.
    git switch -c "${branch}"
    gh stack init "${branch}"
    # -A stages everything, untracked files included, to match `stack-add`.
    # Splitting a dirty tree across branches is done by committing what is
    # ready and leaving the rest for the branch above — not by naming files
    # here, which only moved the bookkeeping into the command line.
    git add -A
    git commit -m "{{message}}"
    python3 scripts/stack-status.py


alias str := stack-rebase
# Rebase the whole stack onto an updated trunk, refusing if it spans worktrees
stack-rebase:
    #!/usr/bin/env bash
    {{initialise}} "stack-rebase"
    set -euo pipefail
    just _stack-guard
    gh stack rebase
    # gh stack rebase exits 0 even when it skipped a branch, so the result is
    # verified rather than trusted: `view --json` reports needsRebase
    # correctly for exactly the branch a silent skip leaves behind.
    if python3 scripts/stack-status.py --no-colour | grep -q "needs rebase"; then
        echo "" >&2
        echo "✗ Branches still need a rebase after gh stack rebase." >&2
        echo "  It reports success even when it skips a branch." >&2
        echo "  Run 'just stack-log' to see which." >&2
        exit 1
    fi
    python3 scripts/stack-status.py


alias stsu := stack-submit
# Rebase onto the latest trunk, then push and open or update the drafts
stack-submit:
    #!/usr/bin/env bash
    {{initialise}} "stack-submit"
    set -euo pipefail
    # Rebase first, every time. A stack is submitted over and over as the
    # units above it are revised, and trunk moves underneath it while that
    # happens — 22 commits in one afternoon, the first time this was used.
    # Submitting without rebasing pushes branches whose pull requests then
    # sit behind main, which the merge queue has to sort out later.
    #
    # `stack-rebase` rather than a bare `gh stack rebase`: it carries the
    # worktree guard and the after-the-fact check that catches a rebase
    # which reported success and silently skipped a branch. Both belong
    # here too, and are better called than copied.
    just stack-rebase
    # --auto skips the interactive editor and opens every new pull request as
    # a draft, which is what this repository needs: the heavy CI tier and the
    # four gate contexts fire on ready_for_review and synchronize, never on
    # opened, so a pull request created ready never gets them. Do not add
    # --open here; `gh pr ready` or /crp final is how a branch leaves draft.
    gh stack submit --auto
    python3 scripts/stack-status.py --prs


alias stsy := stack-sync
# Drop merged branches, re-target the rest, and redraw the stack
stack-sync:
    #!/usr/bin/env bash
    {{initialise}} "stack-sync"
    set -euo pipefail
    just _stack-guard
    # Run this after a pull request merges: it notices the merge, deletes the
    # branch, cascade-rebases what sat above it and pushes the result.
    #
    # --prune answers the "delete N merged branches?" prompt in advance.
    # Tidying up after a merge is the whole reason this recipe exists, and a
    # merged branch's commits are on main and its pull request is on GitHub,
    # so there is nothing in one to lose.
    gh stack sync --prune
    # `--prune` deletes the local branch of a merged pull request, which is
    # the half that frees the name — but it leaves the branch's entry in the
    # stack. Those entries are not only clutter: an entry whose branch is
    # gone costs `gh stack rebase` the base it should be rebasing onto, and
    # it replays the trunk's own history instead. So the record is tidied
    # here, where the branches were just deleted, rather than left to
    # surprise the next rebase.
    python3 scripts/stack-forget-merged.py
    # Exit 1 means "no stack here". That is the ordinary ending for a sync —
    # the last branch merging deletes the stack, so the run that tidies it up
    # is the one guaranteed to find nothing left to draw. The script's own
    # message advises starting a new stack, which is not the point here, so
    # its output is held back and the outcome is reported instead. Any other
    # exit code is a real fault and is left to fail the recipe.
    drawn=""
    status=0
    drawn=$(python3 scripts/stack-status.py --prs --colour 2>&1) || status=$?
    if [ "${status}" -eq 0 ]; then
        printf '%s\n' "${drawn}"
    elif [ "${status}" -eq 1 ]; then
        echo "  Stack fully merged — nothing left to draw."
    else
        printf '%s\n' "${drawn}" >&2
        exit "${status}"
    fi


alias stu := stack-update
# Fold changes into this branch's last commit (message optional, to reword it)
stack-update message="":
    #!/usr/bin/env bash
    {{initialise}} "stack-update"
    set -euo pipefail
    # The counterpart to stack-new and stack-add, which both create a branch.
    # This one revises the branch already checked out — the ordinary case when
    # a review comment, or a second pass over generated code, changes a unit
    # that already exists.
    #
    # It amends rather than adding a commit, because a stacked branch reads
    # best as one commit doing one thing: that is the unit being reviewed. A
    # branch that accumulates "fix: typo" on top of its real change is how a
    # two-unit stack became four branches on the first real run of this
    # tooling. Amending keeps each branch to its single, finished commit.
    #
    # Either way the branches above this one must be rebased afterwards, so
    # amending costs nothing extra: a plain commit leaves them behind just as
    # surely, only less visibly. `stack-rebase` is the repair, and
    # `stack-log` flags what still needs it.
    #
    # No stack guard: amending the branch you have checked out touches nothing
    # another worktree holds. `stack-submit` runs the guard when this work is
    # pushed — and pushes with --force-with-lease, which an amended branch
    # needs and a stack does on every submit anyway.
    if git diff --quiet && git diff --cached --quiet && \
       [ -z "$(git ls-files --others --exclude-standard)" ] && \
       [ -z "{{message}}" ]; then
        echo "Nothing to fold in — the working tree is clean." >&2
        echo "  Pass a message to reword the last commit on its own." >&2
        exit 1
    fi
    # -A to match stack-new and stack-add: all three stage everything,
    # untracked files included, so the three commands cannot differ in what
    # they quietly leave behind.
    git add -A
    if [ -n "{{message}}" ]; then
        git commit --amend -m "{{message}}"
    else
        # --no-edit keeps the existing message rather than opening an editor,
        # which would hang anywhere non-interactive.
        git commit --amend --no-edit
    fi

    # Amending rewrote this branch's commit, so every branch above it now sits
    # on a commit that no longer exists. Rebasing is not optional afterwards —
    # it is the other half of the same operation — so it runs here rather than
    # being left as something to remember. `stack-rebase` carries the worktree
    # guard and the check that catches a rebase which reported success and
    # silently skipped a branch.
    #
    # Skipped when this branch is not in a stack: there is nothing above it to
    # restack, and `stack-rebase` would refuse for want of a stack rather than
    # for any real problem. That also lets this recipe be used on an ordinary
    # branch, which is worth having.
    # --check exits 0 in a stack, 1 when this branch is in none, and 2 when a
    # stack branch is checked out in another worktree. Only 1 means "nothing
    # above to restack"; 2 is a real problem and must still reach the guard
    # inside stack-rebase rather than being quietly taken for "no stack".
    stack_state=0
    python3 scripts/stack-status.py --check >/dev/null 2>&1 || stack_state=$?
    if [ "${stack_state}" -eq 1 ]; then
        echo "  Amended. Not in a stack, so nothing above needs rebasing."
    else
        just stack-rebase
    fi


alias stw := stack-watch
# Redraw the stack with pull request and CI state every minute, until stopped
stack-watch:
    #!/usr/bin/env bash
    set +x
    {{initialise}} "stack-watch"
    set +x
    # `stack-log-long` in a loop. A minute is the cadence because CI state
    # does not change faster than that in any way worth watching, and one
    # `gh pr list` a minute is 60 calls an hour against a 5000-point limit.
    #
    # Not `watch(1)`: macOS does not ship it, and this needs to survive the
    # script exiting non-zero when there is no stack.
    while true; do
        # Fetch first, then clear. Clearing before the ~3s `gh pr list` call
        # left the terminal blank for the whole of it, which read as a hang;
        # capturing the new stack first means the old one stays on screen
        # until the moment it is replaced.
        #
        # `--colour` because capturing makes stdout a pipe, and the script
        # drops colour when it is not a terminal. `|| true` for the same
        # reason `stack-log` has it: "no stack here" is an ordinary answer,
        # and the loop should keep drawing it rather than dying on it.
        drawn=$(python3 scripts/stack-status.py --prs --colour 2>&1 || true)

        # \033[H homes the cursor, \033[2J clears the screen and \033[3J the
        # scrollback. The third matters: without it the previous draw is
        # only pushed up rather than thrown away, so a stack taller than
        # the window leaves the older copy above the new one and the
        # status line scrolls out of sight with it.
        printf '\033[H\033[2J\033[3J'
        echo "  updated $(date '+%H:%M:%S') · every 60s · ctrl-c to stop"
        printf '%s\n' "${drawn}"
        sleep 60
    done

````````

---

## After the files are in place

Sanity-check the port:

- `just --list | grep stack` should show every recipe with its alias.
- `just stack-help` lists the commands one per line.
- `python3 scripts/stack-status.py --check` should exit 1 on an ordinary
  branch, with a message naming the recipes that start a stack. That is the
  expected answer outside a stack, not a failure.
- `just stack-log` on an ordinary branch should say "No stack on this branch".

Then tell me what you changed and what you left alone.
