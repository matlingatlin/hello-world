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

`migration-review` and the files under `commissions/` and `verdicts/` carrying that id are
control fixtures for `.claude/validate/research-hooks-controls.sh`, not real work.
