# Proposal — close the `architect` × `architect-rebuild` collision

**Status: proposed.** Both target files exist under `.claude/`, and the builder that
wrote this cannot write over a file that already exists. A human applies it.

**The defect.** `docs/review-agent-builder-loop.md:56-71` measured the two agents'
descriptions overlapping at Jaccard **0.195** — the highest of any pair in the
roster — sharing *boundary, carving, choosing, datastore, decision, design, layer,
parts, seams*, **with no NOT-clause in either direction**. It has stood open as eval
case T5, never checked (`docs/architect-rebuild-tester-brief.md:77-80`). The review
that found it declined to fix it, correctly: *"which one survives is a decision, not
a repair."*

**Why now.** A third architect-shaped agent has been added
(`llm-component-architect`). It was built to keep away from all nine shared terms in
the positive half of its description and to carry a NOT-clause to each of the two
existing agents. That is the new agent paying its own way; it does nothing for the
original pair, and the pair is still the roster's worst routing defect.

**What this proposal is not.** It does not decide which of the two agents should
survive. That is a human's call and it is a bigger question than a description edit:
`architect` is scoped to this repository and `architect-rebuild` to
`/home/user/scio/`, and whether that split should exist at all is a scope decision.
This closes the *routing* defect either way, and it is reversible.

---

## The change

### 1 · `.claude/agents/architect.md`, line 3

Append to the end of the existing `description:` value, before the closing of the
line:

> ` NOT for shape questions about the Scio rebuild at /home/user/scio (architect-rebuild), NOT for ruling on the model calls in a system — their cost, latency, failure behaviour, prompt intake or output judgement (llm-component-architect).`

### 2 · `.claude/agents/architect-rebuild.md`, line 3

The existing description already carries four NOT-clauses. Add two more, inside the
closing quote:

> ` NOT for architecture work on the hello-world repo itself rather than the Scio rebuild (architect), NOT for ruling on the model calls in a system — their cost, latency, failure behaviour, prompt intake or output judgement (llm-component-architect).`

### 3 · Re-check the length and the roster

Both descriptions must stay under the cap in
`.claude/skills/agent-assembly/assets/template/LIMITS.md`, and the roster total is
shared. Measure, do not estimate — the worked example in the template records two
numbers that were wrong when first written *"typed from a sense of the length rather
than counted"*:

```
sed -n 's/^description: //p' .claude/agents/architect.md | wc -c
sed -n 's/^description: //p' .claude/agents/architect-rebuild.md | wc -c
python3 .claude/validate/agents.py
```

`architect-rebuild`'s description is the longest in the roster; if the addition puts
it over, shorten one of its four existing NOT-clauses rather than dropping one of
these two.

---

## How to tell whether it worked

Re-run the measurement that found the defect, not a reading of the new text.

| Pair | Before | Requirement after |
|---|---|---|
| `architect` × `architect-rebuild` | 0.195 | lower, **and** a NOT-clause in both directions |
| `llm-component-architect` × `architect` | measure it | below 0.195, NOT-clause present |
| `llm-component-architect` × `architect-rebuild` | measure it | below 0.195, NOT-clause present |

A deliberate split has a NOT-clause in **both** directions; a collision has none
(`docs/proposal-route-into-agent-fitness-review.md:8-10`). After this change all
three pairs are deliberate splits, which is the whole of what a description edit can
buy.

**What it cannot buy, and should not be claimed to.** Adding NOT-clauses lowers term
overlap and gives the caller a place to read "not me, them". It does **not**
establish that the two agents should both exist, and it does not test routing —
that needs the trigger cases in `docs/architect-rebuild-tester-brief.md` §T5 and in
`docs/llm-component-architect-tester-brief.md` §D actually run, by somebody who
authored neither.
