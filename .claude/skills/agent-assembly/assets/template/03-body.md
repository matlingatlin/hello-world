# The body — five sections, and what belongs in each

The body is a **system prompt**. It is paid on every invocation, and it loads
alongside the full text of every preloaded skill. So the discipline is
subtractive: **anything the skills already say does not belong here.**

Five sections. Each answers one question the agent needs settled before it can
start.

| § | Question it answers |
|---|---|
| 1 | What do I produce? |
| 2 | What can I not do, and by what mechanism? |
| 3 | What are my functions, and where do their steps live? |
| 4 | Where do I look things up? |
| 5 | When am I finished, and when do I stop short? |

**Order matters, and §2 is second on purpose.** The agent should know its
boundary before it knows its procedure — an agent that has already planned is
looking for a way to finish the plan.

---

## Two rules that cut across every section

**No persona.** **[MEASURED]** Personas are negative for correctness work: 162
personas across 2,410 questions, effects "largely random", accuracy lower in the
tested range. What a persona seems to promise is content — and content belongs in
the failure tables, where it can be checked.

**Nothing here that a skill already says.** Duplication is not emphasis. It is a
second place for the same rule to rot, and when the two copies disagree the agent
has no way to tell which is current.

---

## §1 · What you produce

One paragraph. The artefact, by path and shape.

> Emits `docs/reviews/migration-NNNN.md`: one row per statement, each carrying
> the ruling, the engine behaviour behind it, and the line in the migration file.

**Good:** names a path, names the shape, names what one row contains.
**Bad:** *"Produces high-quality analysis of migrations."* — no path, no shape,
and "high-quality" is not checkable.

**The test:** could a caller write the acceptance criteria for this agent's output
from this paragraph alone? If not, the agent is not specified yet.

---

## §2 · What you may not do, and by what mechanism

One row per impossibility. **Every row names the mechanism.**

> - You hold no `Bash`. Nothing here executes.
> - You hold no `WebSearch`. You can open a URL the document names; you cannot
>   go and find a source that agrees.
> - `.claude/hooks/migration-review-scope.sh` denies every write outside
>   `docs/reviews/`, and denies overwriting a review that already exists.

**[MEASURED]** A prose warning is not a mechanism. Warnings against a known bias
failed in three studies and **backfired in a fourth**; eight anchoring-warning
variants differing in content and timing were all indistinguishable from no
warning at all. So: **an absent tool, or a hook. Never a sentence.**

**[MEASURED]** And a hook is conditional in a way an absent tool is not — hooks do
not load in a non-interactive session. Where the same protection is available
either way, take the tool.

### Then say what the mechanisms do not cover

This is the part almost every agent file skips, and skipping it is what turns a
list of three protections into an implied claim of completeness.

> **What none of this stops.** The gate enforces *where* you write, never *what*.
> A finding you invented rather than read is indistinguishable from one you
> verified, and nothing downstream will catch it.

**[MEASURED]** People allocate almost no probability to what a description leaves
out — given a pruned fault tree, subjects assigned **.140** where the normative
answer was **.468**, recovering about 30%, and **1 subject of 55** assigned
enough. Naming the gap explicitly recovers some of it; leaving it unnamed
recovers none.

---

## §3 · Your functions

The **map only**. One line per preloaded skill: what it decides, what it emits.

| Skill | Decides | Emits |
|---|---|---|
| `migration-rule-check` | is each statement safe on the declared engine | the ruling table |
| `migration-abstention` | which statements cannot be ruled from the file alone | the abstention list |

**The steps are in the skills.** They are already loaded in full. Restating them
here doubles the cost and creates a second copy to drift.

At most three rows. **A fourth function means two agents** — go back to shaping
rather than growing this one.

---

## §4 · Where your knowledge lives

Pointers, never copies.

> `/home/user/skills-repo/knowledge/notes/postgres-ddl-locking.md` — which
> statements take which lock, per engine and version. Read it at the ruling
> step; do not carry it in your head.

**Copies drift; the base does not.** A number transcribed into an agent file is
correct on the day it is written and unverifiable thereafter. A pointer is
correct whenever it is read.

**A value that changes on its own is fetched, never written down.** Anything with
a version number attached is in this category.

---

### Carrying `unevidenced`

`agent-shape` §1b rules the knowledge base `covered`, `thin` or `absent` for the
agent's domain. **`thin` produces a fourth provenance state** beyond
`[DOC]`/`[MEASURED]`/`[HOUSE]`: a step that had to be written anyway, resting on
material nobody has verified.

It has a home, and it is not the body. **Mark the step in the reference file the
step opens**, and close every such file with:

```markdown
## What is not evidenced here

| Row | Rests on | State |
|---|---|---|
| ... | the note or the reasoning | `unevidenced` · `unevidenced by transfer` |
```

`unevidenced by transfer` is for a measurement borrowed from an adjacent domain —
real, measured, and measured on something else. It is the more dangerous of the
two, because it arrives carrying a number.

Keeping this out of the body is deliberate: the body is paid every invocation and
this is read at the step that needs it. Keeping it out of the *knowledge note* is
also deliberate — the note records what a source says; this records what **we**
did without one.

## §5 · When you are done, and when you stop short

Two halves, and the second is the one that makes the agent trustworthy.

**Done:** the positive stopping condition. What must exist.

> Finished when every statement in the file carries a ruling or an abstention,
> and the findings document exists at its path.

**Stop short:** the conditions under which producing **nothing** is the right
answer, stated as concretely as the success condition.

> Stop and say so, producing no findings document, when: the file does not
> declare its engine; the schema it targets is not in the repository; or the
> migration has already been deployed, which makes this an incident review and
> not this agent's job.

**An agent with no stated way to fail will always find a way to succeed.** That is
the failure this section exists to prevent, and it shows up as output that looks
complete and is not — a table of hedges instead of a refusal.

---

## Length

Aim for **under 1,000 words**. There is **no measured target** — the 5,000-word
figure in circulation is Anthropic's guidance for `SKILL.md`, a different
artefact, and does not transfer.

The reason to keep it short is structural rather than empirical: this file is
paid every invocation, it loads alongside every preloaded skill in full, and
every sentence in it is a sentence that could have been a checkable row in a
skill instead.

**If the body is growing, the usual cause is that procedure is leaking into it.**
Move the steps to a skill. Move the background to a note. What is left is the
five answers above.
