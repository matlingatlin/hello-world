# `docs/research/` — the stage-1 working directories

Four directories, and the split between them is enforced by two `PreToolUse` gates rather
than by anything either agent has been told.

| Directory | Written by | Gate |
|---|---|---|
| `commissions/` | a human, or `agent-shape` re-commissioning narrower | neither agent may write here — an agent that writes its own commission has no scope |
| `drafts/` | `domain-researcher` | `research-commission.sh`: one shape only, `drafts/<id>.md`, and only where `commissions/<id>.md` exists |
| `verdicts/` | `primary-source-verifier` | `note-promotion.sh` |
| `patches/` | `primary-source-verifier` | the route for extending a note that already exists, which a human applies |

`<id>` is lower-case, hyphenated, no subdirectories, `.md` — because three files match on it
and a case difference would silently break the join.

A note crosses into `/home/user/skills-repo/knowledge/notes/` only when
`verdicts/<id>.md` exists and the note does not. That is the gate, not a convention.

**Nothing in `commissions/`, `drafts/`, `verdicts/` or `patches/` is committed.**
`.claude/validate/research-hooks-controls.sh` stages its own fixtures under the id
`zzz-hook-control` and tears them down on exit.

That rule was bought. Fixtures for the id `migration-review` were committed once, and
`migration-review` is the id the tester brief gives to real work — so a live gate arrived
in the repository **pre-satisfied**, and an independent tester unlocked a real write into
the knowledge base with a 28-byte file. A control fixture that satisfies a live gate is
not a fixture. Stage them, tear them down, and never name one after real work.
