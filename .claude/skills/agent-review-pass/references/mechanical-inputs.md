# What is already mechanical — take the output, do not re-derive it

Opened by step 2 of `agent-review-pass`.

You hold no `Bash`. That is deliberate: a reviewer that could execute could also rewrite
what it reviews, and the gate that would prevent it is not installed. The consequence is
that everything below is an **input** the caller hands you, or a **stop**.

A reviewer that re-derives a mechanical answer by reading is *worse* than one that runs
the checker: it trades a deterministic answer for a probabilistic one, and its rows
cannot be re-run by the person who reads them. This repo has already committed that
defect one layer down — five checks restated in prose, the program that implements them
named nowhere, found independently by two audits.

## The programs, and what each already decides

| Command | What it settles, so you do not | Where its rules live |
|---|---|---|
| `python3 .claude/validate/agents.py` | frontmatter parses line-anchored; `tools:` is explicit; preloads exist and are within the house cap; descriptions within limits and free of angle brackets; names kebab-case and unreserved; hook commands exist and are executable; matchers anchored, in agent frontmatter **and** in `.claude/settings*.json`; every referenced `references/`/`assets/` file exists; skill bodies within the word guidance; NOT-clause targets resolve; every agent is named by some eval artefact; the roster's shared description budget | `.claude/validate/agents.py` — declared the single home of the construction rules |
| `bash .claude/validate/selftest.sh` | whether the checker above can fail at all. A checker that cannot fail proves nothing, so a CLEAN with no self-test behind it is not evidence | same |
| `bash .claude/validate/*-controls.sh` | whether a given hook denies and allows the cases it claims. One harness per wall; several walls have none, and *that absence* is an L3 finding you can make without running anything | the harness scripts |
| `git log`, `git show`, `git ls-tree` | who authored an artefact and when, and whether a claimed file has ever existed | — |

## How to use them

Exit 0 from the validator is clean; exit 1 lists failures with a provenance tag — `[A]`
Anthropic's spec, `[B]`/`[C]` the docs, `[M]` a measured house rule. **A defect it names
belongs to the agent under review, not to the checker.** The tag matters: `[M]` is this
project binding itself to its own measured finding, not a spec violation, and a review
that reports it as a spec violation has lent a house rule borrowed authority.

Quote the **raw output**, never a summary of it. A summary of a check is a claim about a
check.

## When an input is missing

Stop the pass. Return, in your final message, the exact commands the caller must run and
the request to re-dispatch you with their output. Do not proceed on the reading. Do not
mark the rows `not checkable` and continue — a document full of `not checkable` rows
where a command would have answered is the *"something small"* failure: work that looks
like diligence and decides nothing.

The one thing you may do without them: record, as a finding, that a wall has no
re-runnable harness, or that a claimed check has no call site. Those are absences,
visible by listing, and they are among the highest-yield rows this repo's reviews have
produced.

## What no program here can see

Say this in the accounting block, every time. The mechanical layer is entirely
path-shaped and syntax-shaped. It cannot see whether a verdict was reached by reading
anything, whether a sweep answered the question it was given, whether a rule is grounded
in an observed failure, or whether a number is still true. Those are content and speech,
they are the whole reason this agent exists, and no green run from any command above is
evidence about them.
