set shell := ["bash", "-c"]

default:
    just --list

initialise:= 'set -euxo pipefail
    initialise() {
        # Clear the terminal window title on exit
        echo -ne "\033]0; \007"
    }
    trap initialise EXIT
    just _terminal-description'


alias a := app
# Run the web app
app:
    #!/usr/bin/env bash
    {{initialise}} "web app"
    poetry run python app/app.py
    
_terminal-description message=" ":
    echo -ne "\033]0;{{message}}\007"

alias s := setup-terminal-description
# Set up the description for terminal windows
setup-terminal-description:
    #!/usr/bin/env bash
    {{initialise}} setup-terminal-description
    alias_definition="alias j='just'"

    if grep -Fxq "$alias_definition" ~/.zshrc
    then
        echo "Alias already exists in ~/.zshrc"
    else
        echo "$alias_definition" >> ~/.zshrc
        echo "Alias added to ~/.zshrc"
    fi
    
    echo "Please run the following command to apply the changes to this terminal:"
    echo "source ~/.zshrc"


# Turn the name given to stack-new or stack-add into a branch name.
#
# A pass-through today, because `main` here carries no branch protection and
# no ruleset: any branch name pushes. The recipe exists anyway because the
# place to enforce a naming rule is at creation, not at the push — a branch
# named wrongly fails once the commits already exist on it, and unpicking
# that by hand is the expensive part.
#
# If protection is added later, list the permitted prefixes here and give
# a bare name a default, as the repo this came from does:
#
#     case "{{name}}" in
#         feature/*|hotfix/*) echo "{{name}}" ;;
#         *) echo "feature/{{name}}" ;;
#     esac
_stack-branch-name name:
    #!/usr/bin/env bash
    set -euo pipefail
    echo "{{name}}"


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
# it believed was rebased and was not.
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
    # sit behind main, which someone has to sort out at merge time.
    #
    # `stack-rebase` rather than a bare `gh stack rebase`: it carries the
    # worktree guard and the after-the-fact check that catches a rebase
    # which reported success and silently skipped a branch. Both belong
    # here too, and are better called than copied.
    just stack-rebase
    # --auto skips the interactive editor and opens every new pull request as
    # a draft. Draft is the right default on a stack: the branches above this
    # one get rewritten by every later rebase, so a pull request is not worth
    # a reviewer's attention until the branch below it has settled. Do not add
    # --open here; `gh pr ready` is how a branch leaves draft.
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
