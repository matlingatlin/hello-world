# Measurements

Configuration and outcomes, kept apart on purpose.

| File | Holds | Written by |
|---|---|---|
| `factors-<commit>.jsonl` | one row per agent: the variables we chose and the constants we ran under | **generated** — `agents.py --factors` |
| `runs.jsonl` | one row per run: conformance, containment or competence | appended by hand, never edited |
| `tasks/` | the task given to both arms of a competence run | written before the run |

The protocol is `docs/measurement-protocol.md`. The join key is `agent` + `commit`.

**Append, never edit.** A corrected run is a new record naming the one it
supersedes. A file that can be rewritten is a file whose history is an opinion.

**Snapshot the factors before a run, not after.** `--factors` reads the tree as it
is now; a run recorded against a commit whose factor file was generated later is
describing a configuration that may already have changed.
