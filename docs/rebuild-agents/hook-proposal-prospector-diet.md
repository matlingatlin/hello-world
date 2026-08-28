# Hook proposal — `rebuild-prospector-diet`

**For:** `rebuild-prospector`  **Event:** `PreToolUse`  **Matcher:** `^(Read|Write)$`

`agent-builder` may not write `.claude/hooks/`. A builder that can author
executable hooks can delete its own wall. **A human installs this.**

---

## What must be impossible, and why

**1 · The prospector must not be able to read the existing system's solution
vocabulary.** Not the 85 standing proposals in `/home/user/scio/docs/next/`, not
`/home/user/scio/docs/as-built/`, not `triage/` or `mined/`, and not this repo's
own architecture, layer, PRD, strategy, design, backlog or ADR documents.

If it can, the agent stops being a generator and becomes a restatement engine.
Measured: seeding a generator with existing good ideas produced cosine
similarity **0.403–0.428 against a base of 0.377** — *worse than no seed at all*
— and human-written seeds moved nothing (p = .95). Models given background
material produce output experts score at narrowness **1.00–1.55** against human
**0.47**. Five independent measurements converge on the same instruction:
starve the generator.

**2 · That impossibility cannot be a sentence.** This repo has already run the
experiment. `docs/RETHINK-BRIEF.md:16` says *"**Write Pass A before opening the
codebase, before reading the reviews, and before reading the appendix of this
file.** Everything you learn afterwards makes it impossible to write honestly."*
and `:145` says *"**Do not read this until step 5.**"* The same file, at `:8`,
records that instruction already failing: *"An earlier draft of this document
did the exact thing it warned against: it told the blank-slate pass what the
answer was… A blank slate handed a conclusion is not a blank slate."*

The general result behind that instance: eight anchoring-warning variants —
before and after, generic and specific, pointing the right way and the wrong way
— were **all indistinguishable from no warning**, and *"try not to restrict your
ideas; be as different as possible"* moved conformity the wrong way, .25 → .33.

A `PreToolUse` hook runs before every permission check, `bypassPermissions`
included, and can only tighten. That is why this is here and not in the prompt.

**3 · The prospector must not write outside its candidate directory.** Its
output is raw material for an adjudicator that has not seen it. A generator that
can edit the dossier grades its own supply.

**What the hook does not do, stated rather than papered over.** `WebSearch` and
`WebFetch` are ungated — the sweep is the point of them. The sibling repository
is not published, so fetching it is not currently a route; if it is ever
mirrored, this hook does not cover that and the matcher must grow. And a
subagent loads the whole `CLAUDE.md` hierarchy regardless of tools (measured,
canary probe), so the prospector will know the product category and the names of
files it cannot open. Accepted.

---

## The script

Install at `.claude/hooks/rebuild-prospector-diet.sh`, `chmod +x`.

```bash
#!/usr/bin/env bash
# PreToolUse diet gate for the `rebuild-prospector` subagent.
#
# The prospector proposes what a product in this problem space could be. It must
# do that WITHOUT the existing system's solution vocabulary, because a generator
# seeded with the existing solution measures worse than one given nothing.
#
# A sentence asking it not to look is the single most thoroughly measured
# non-intervention available. This is a wall: PreToolUse runs before every
# permission check, bypassPermissions included, and can only tighten.
#
# The prospector holds no Bash, no Agent, no Grep and no Glob, so Read and Write
# are the whole of its filesystem surface and this gate is complete over it.
#
# Contract: stdin is the PreToolUse payload. Always exit 0; the decision travels
# in JSON on stdout. Deny — never silently allow — when the payload cannot be
# parsed or carries no path: a call whose scope cannot be checked must not run.
set -uo pipefail

payload=$(cat)
root="${CLAUDE_PROJECT_DIR:-$PWD}"

deny() {
  # shell-quote nothing into the JSON; the reason strings below are all literal.
  printf '%s' "{\"hookSpecificOutput\":{\"hookEventName\":\"PreToolUse\",\"permissionDecision\":\"deny\",\"permissionDecisionReason\":\"rebuild-prospector-diet: $1\"}}"
  exit 0
}

parsed=$(printf '%s' "$payload" | python3 -c '
import json, os, sys
try:
    d = json.load(sys.stdin)
except Exception:
    print("__MALFORMED__\t"); sys.exit(0)
tool = d.get("tool_name") or ""
ti = d.get("tool_input") or {}
p = ti.get("file_path") or ti.get("notebook_path") or ""
if not isinstance(p, str) or not p:
    print("__NOPATH__\t" + tool); sys.exit(0)
root = os.path.realpath(sys.argv[1])
if not os.path.isabs(p):
    p = os.path.join(root, p)
# realpath resolves the basename too: a symlink named brief.md must not become
# a read of docs/next/LAYER-E-BUILD.md.
p = os.path.realpath(p)
if p != root and not p.startswith(root + os.sep):
    print("__OUTSIDE__\t" + tool); sys.exit(0)
print(os.path.relpath(p, root) + "\t" + tool)
' "$root" 2>/dev/null) || deny "could not resolve the target path."

rel=${parsed%%$'\t'*}
tool=${parsed#*$'\t'}

case "$rel" in
  __MALFORMED__) deny "the tool payload could not be parsed, so its scope cannot be checked." ;;
  __NOPATH__)    deny "no file path in the tool call, so its scope cannot be checked." ;;
  __OUTSIDE__)   deny "that path is outside this repository. The prospector reads its brief and nothing else; the sibling repository at /home/user/scio is exactly what it must not see." ;;
  "")            deny "empty path." ;;
esac

case "$tool" in
  Read)
    case "$rel" in
      docs/rebuild/brief/*.md)
        exit 0 ;;
      .claude/skills/architecture-decision/references/far-domain-analogy.md)
        exit 0 ;;
    esac
    deny "the prospector reads only docs/rebuild/brief/*.md and the far-domain analogy reference. It proposes from the problem, not from the existing solution — read anything else and it stops being a generator." ;;
  Write)
    case "$rel" in
      docs/rebuild/candidates/*)
        exit 0 ;;
    esac
    deny "the prospector writes only under docs/rebuild/candidates/. Its output is raw material for an adjudicator that has not seen it." ;;
esac

deny "unexpected tool \`$tool\` for this gate."
```

Two details that are load-bearing and easy to lose in a rewrite:

- The tool name is read from the payload because **the two allowlists differ**.
  A single merged allowlist would let the prospector read whatever it may write,
  and vice versa.
- `case` patterns end at a `/` or an extension, so `docs/rebuild/briefing/x.md`
  and `docs/rebuild/brief-old.md` do not match `docs/rebuild/brief/*.md`. That is
  the prefix-lookalike control, and it is the one a rewrite usually breaks by
  reaching for `startswith`.

---

## Controls — all must be run before installing

Run each by piping the JSON to the script and reading stdout. **Positive
controls are not optional: a gate that denies everything passes every deny case,
and only the allow rows prove it is a gate rather than a wall.**

| # | Tool | Input path | Expected | Result |
|---|---|---|---|---|
| 1 | `Read` | `docs/rebuild/brief/2026-08-28-a.md` | **allow** (silence) | |
| 2 | `Read` | `/home/user/hello-world/docs/rebuild/brief/2026-08-28-a.md` (absolute form of #1) | **allow** | |
| 3 | `Read` | `.claude/skills/architecture-decision/references/far-domain-analogy.md` | **allow** | |
| 4 | `Write` | `docs/rebuild/candidates/run-01.md` | **allow** | |
| 5 | `Read` | `/home/user/scio/docs/next/LAYER-E-BUILD.md` | deny — outside the repository | |
| 6 | `Read` | `/home/user/scio/docs/as-built/LAYER-A-INTAKE.md` | deny — outside the repository | |
| 7 | `Read` | `docs/ARCHITECTURE.md` | deny — not on the read allowlist | |
| 8 | `Read` | `docs/decisions/0001-graph-is-standard.md` | deny | |
| 9 | `Read` | `docs/rebuild/candidates/run-01.md` (its own output; write-allowed, read-denied) | deny | |
| 10 | `Read` | `docs/rebuild/brief/../../ARCHITECTURE.md` (traversal through an allowed root) | deny | |
| 11 | `Read` | `docs/rebuild/briefing/x.md` (prefix lookalike, directory) | deny | |
| 12 | `Read` | `docs/rebuild/brief-old.md` (prefix lookalike, file) | deny | |
| 13 | `Read` | `docs/rebuild/brief/notes.txt` (allowed dir, non-`.md`) | deny | |
| 14 | `Read` | a symlink at `docs/rebuild/brief/x.md` → `/home/user/scio/docs/next/README.md` | deny — basename is realpath'd | |
| 15 | `Write` | `docs/ROADMAP.md` | deny | |
| 16 | `Write` | `.claude/agents/rebuild-prospector.md` (its own definition) | deny | |
| 17 | `Write` | `.claude/hooks/rebuild-prospector-diet.sh` (the hook itself) | deny | |
| 18 | `Write` | `/etc/passwd` | deny — outside the repository | |
| 19 | `Read` | payload with `tool_input: {}` (no path) | deny | |
| 20 | `Read` | `{` (malformed JSON) | deny | |
| 21 | `Read` | `tool_input: {"file_path": null}` | deny | |
| 22 | `Bash` | any (matcher should never route it here; if it does) | deny — unexpected tool | |

Row 9 is the one worth pausing on: the prospector may **write** its candidate
file and may not **read** it back. That is deliberate. Re-reading its own output
and revising it is self-critique with no external signal, which measured worse on
every model and every benchmark tested — GPT-4 GSM8K 95.5 → 91.5 → 89.0, GPT-3.5
CommonSenseQA 75.8 → **38.1**. The external signal is the adjudicator.

---

## Installation

1. Write the script to `.claude/hooks/rebuild-prospector-diet.sh` and `chmod +x`.
2. Run the 22 controls above and fill the Result column.
3. The frontmatter block is **already present** in
   `.claude/agents/rebuild-prospector.md` and needs no edit:

```yaml
hooks:
  PreToolUse:
    - matcher: "^(Read|Write)$"
      hooks:
        - type: command
          command: "${CLAUDE_PROJECT_DIR}/.claude/hooks/rebuild-prospector-diet.sh"
```

**Until step 1 is done, the agent is shipped unwalled and looks walled.** A
`command` hook whose file does not exist exits 127, which is a non-blocking
error — the tool call proceeds. The frontmatter is therefore not evidence that
the gate exists; only control row 1 returning silence and control row 5
returning a deny are. Do not run `rebuild-prospector` before that.
