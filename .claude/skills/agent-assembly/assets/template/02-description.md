# `description` — the field that decides whether the agent is ever used

Everything else in the file describes an agent that has already been chosen. This
field is what gets it chosen. Write it last, when you know what the agent
actually does, and then rewrite it.

---

## What it is for, and what it is not

**[DOC]** The description **drives delegation** — whether a whole job is handed to
a separate worker with its own context window.

That is a different problem from a **skill** description, which decides whether
some text gets loaded into the current context. Do not carry skill-writing habits
here. A skill competes for attention inside one run; **an agent competes against
the entire roster**, and the caller sees only these few lines when deciding.

**[DOC]** Every non-built-in agent description shares one token budget across the
whole roster, and Claude Code warns at startup when it is exceeded. The figure is
in `LIMITS.md`. Your description is not free and it is not alone.

---

## Hard requirements

| Rule | Source |
|---|---|
| A maximum character count — **see `LIMITS.md`** | **[DOC]** |
| **No `<` or `>`** anywhere | **[DOC]** — the frontmatter enters a system prompt, so angle brackets are a prompt-injection surface |
| Must carry **what** the agent does **and when** to use it | **[DOC]** |

The validator enforces all three, and it is the only place the number lives.
`LIMITS.md` is generated from it. A defect it names is yours.

---

## The four parts, in order

**1 · The trigger — the situation, in the words someone would actually type.**

Not the capability. The *moment*. "When a migration needs reviewing before it
ships", not "reviews migrations". Include the phrases a person would use in
passing: *"is this safe to run"*, *"will this lock the table"*. Those phrases are
what the caller is matching against.

**2 · What it does with that situation** — the verb and the object, concretely.

**3 · The artefact it emits**, by path or shape. This is the part most
descriptions omit and it is the one that tells the caller what they get back. An
agent whose return value is unstated will be invoked and then second-guessed.

**4 · NOT-clauses routing to named neighbours.**

One per plausible confusion. **The neighbour must exist and must be named** — a
NOT-clause pointing nowhere sends the caller in a circle.

**Two forms, and the checker only understands one of them.**

*In this repository:* `NOT for the adjacent job (neighbour-name)`. The checker
resolves the parenthesised name against `.claude/agents/` and `.claude/skills/`
and warns when it finds nothing. Use this form and the routing is verified.

*Outside this repository* — a library talent, another repo's agent: the same form
produces a **warning**, because the checker cannot see the target. Phrasing it
without parentheses makes the warning go away and makes the route invisible.
Neither is good. **Name the job and where it lives, in prose**, and accept that
nothing verifies it:

> NOT for retrieval, chunking or embedding quality — that is a separate job and
> the talent for it lives in the library at `/home/user/skills-repo`, not here.

The template's own rule calls an unverifiable route a defect. It is one; it is
just a defect with no better alternative until the checker can resolve across
repositories. Say so in the spec rather than choosing a phrasing that hides it.

This is **[HOUSE]**, not measured. The argument for it is mechanical rather than
empirical: two descriptions competing on the same vocabulary give the caller no
way to choose, and a NOT-clause is the only place in the file where you can say
"not me, them."

---

## Test it before you keep it

Read your description next to every sibling in `.claude/agents/`. Then answer:

- **Could a caller who wanted the neighbour land here instead?** If yes, the two
  share vocabulary and one of them must change.
- **Does it name a situation, or a subject area?** A subject area collides with
  everything in that area.
- **Would someone know what comes back?** If not, add the artefact.
- **Is every NOT-clause target real?** Check the file exists.

---

## A description that works

> Use when a database migration must be judged safe to run before it ships —
> "will this lock the table", "is this reversible", "can we deploy this at
> midday". Reads the migration file and the schema it targets, rules each
> statement safe, unsafe or dialect-dependent, and emits a findings list at
> `docs/reviews/migration-NNNN.md` with one row per statement and the engine
> behaviour behind each ruling. Abstains where the file does not declare its
> dialect, because the same statement is safe on one engine and not another. NOT
> for writing or repairing a migration, NOT for schema design or index choice
> (those need the query workload, which is not in the file), NOT for judging a
> migration already deployed (that is an incident review).

Why it works: the trigger is in a caller's words; the artefact is named with its
shape; the abstention tells you when it will decline; every NOT-clause names a
real adjacent job and says *why* it is out of scope.

---

## Descriptions that do not work, and what is wrong

> **"You are an expert database engineer with 15 years of experience."**

A persona, and **[MEASURED]** personas are negative for correctness work — 162
personas across 2,410 questions, "largely random" effects, with accuracy dropping
in the tested range. It also says nothing about *when* to call it, which the
documentation requires.

> **"Handles database stuff."**

A subject area, not a situation. It will be matched for anything containing the
word "database", including the jobs it cannot do.

> **"Reviews migrations carefully and thoroughly, applying deep expertise to
> ensure high-quality outcomes."**

Adjectives instead of content. Nothing here distinguishes it from any other
agent, and a caller cannot tell what comes back.

> **"Use when reviewing migrations. NOT for schema work (use the schema agent)."**

The NOT-clause routes to an agent that does not exist. The caller now has a
dead end where they expected a hand-off.

> **"Reviews <migration files> for safety."**

Contains angle brackets. **[DOC]** forbidden — and the validator will reject it.

---

## Length

The cap is in `LIMITS.md`. There is **no measured optimum** below it, and anyone
who tells you otherwise is repeating a habit.

What the four parts imply in practice: a trigger with real phrasing, an artefact,
and two or three NOT-clauses will land somewhere around 600–900 characters. If
you are at 300 you have probably omitted the artefact or the routing. If you are
at 1020 you are describing the procedure, which belongs in the skills.
