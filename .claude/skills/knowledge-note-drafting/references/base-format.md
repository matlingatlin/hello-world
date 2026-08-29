# The format the base already keeps

Opened at step 1 of `knowledge-note-drafting`. Everything here is a description of
`/home/user/skills-repo/knowledge/notes/` as it is, with the `file:line` behind it.
Nothing here is a new rule. If this file and an exemplar note disagree, **the note
wins** and this file is stale — say so.

Exemplars, all added 2026-08-28 for the purpose: `ideation-and-idea-selection.md`,
`design-fixation-and-anchoring.md`, `llm-idea-generation.md`,
`requirements-discovery.md`, `architecture-evidence.md`.

## Frontmatter

```yaml
---
title: Ideation and idea selection — what is measured
sources:
  - url: https://doi.org/10.1037/0022-3514.53.3.497
    note: Diehl & Stroebe 1987, Productivity Loss in Brainstorming Groups, JPSP 53(3) 497-509
    fetched: 2026-08-28
status: verified
tags: [ideation, brainstorming, decision-making, evidence, measured-vs-repeated]
related: ["[[design-fixation-and-anchoring]]", "[[llm-idea-generation]]", "[[requirements-discovery]]"]
---
```
— `ideation-and-idea-selection.md:1-25`, six sources in that shape.

| Key | Contract | How well the base keeps it |
|---|---|---|
| `title` | a sentence, not a label | kept |
| `sources` | one entry per source: `url`, `note` (full citation), `fetched` | 76 URL entries across 26 notes, 75 carrying a fetch date. This is the base's strongest habit — match it, do not re-teach it |
| `status` | `verified` / `unverified` / `outdated`, per `INDEX.md:5-7` | kept, and **self-assigned in all 26** — which is why a draft is `unverified` and only a verifier writes `verified` |
| `tags` | flat list | kept |
| `related` | Obsidian `[[wikilinks]]` | **the weakest element — see below** |

The one **addition** this pipeline makes, and it is additive: a promoted note also
carries `verified_by:` naming its verdict document. Every existing note stays valid
without it. It is not written by the researcher.

## Body

- **A house-rule line, early.** `ideation-and-idea-selection.md:29-31`:
  *"every row carries MEASURED (a study with numbers exists and was read) or
  REPEATED (widely asserted, no measurement found). The distinction is the content;
  the summary is not."*
- **Claim tables where there are numbers.** `ideation-and-idea-selection.md:42-48`:
  `| Claim | Verdict | Number |`, with rows like *"Individuals working alone,
  pooled, beat the same people interacting | MEASURED | d = 1.395, k = 34,
  N = 2,577"*.
- **Contradiction between primary sources stated, not smoothed.**
  `ideation-and-idea-selection.md:51-54`.
- **A finding's weakness carried in the row, not hidden.**
  `ideation-and-idea-selection.md:48`: *"MEASURED, contested — 96% of
  between-condition variance — but from n = 15 units"*.
- **A closing section for what could not be found measured.**
  `ideation-and-idea-selection.md:108-113`, listing the searched-and-empty questions
  by name and ending *"All REPEATED."*
- **Scope limits stated by the measurement itself.** `subagents.md:81-84`:
  *"Scope limit, stated by the probe itself: this tests the subagent path only …
  Do not generalise this to the main session."*
- **A number not dressed as a limit when it is a judgement.**
  `subagents.md:100-104`.

## The two things the base gets wrong, which you are here to not repeat

**1 · Claims not bound to sources.** `subagents.md` cites one URL and asserts on
the order of forty facts. `long-text-comprehension.md:19-41` makes about a dozen
claims across "Verified claims", "Outdated claims" and "Overstated claims" and no
claim names which of its three sources it came from. `long-text-comprehension.md:61`
attributes a heuristic with a stated `±15%` to a source the frontmatter does not
list. Consequence: to check one claim, a reader must re-read everything.

**2 · The link graph is not the graph the index promises.** `INDEX.md:3-5` says
notes link *"to related notes with [[wikilinks]] (Obsidian-compatible)"*. In fact:

| Broken link | Where | Resolves to |
|---|---|---|
| `[[plugins]]` | `claude-code-extension-layer.md:8`, `mcp.md:8` | nothing — the note is `plugins-and-marketplaces` |
| `[[context-budget]]` | `graphify-assessment.md:12` | nothing — it is a talent, not a note |
| `[[unified-memory]]` | `temporal-kg-agent-memory.md:8` | nothing — it is a talent, not a note |

And one-sidedness is common rather than exceptional:
`skill-authoring-eval-methodology.md:10` names three neighbours and none of the
three names it back; `graphify-features.md:12` names `graphify-assessment`, which
does not return it.

`/home/user/skills-repo/CLAUDE.md` already names the cause — *"parallel authoring
produces one-sided links structurally"* — and attaches no mechanism to it. The
mechanism this pipeline adds is the back-link table: you cannot edit a neighbour, so
you emit the exact line a human adds, and the omission is visible instead of silent.

## What a draft is, and is not

A draft under `docs/research/drafts/` is **not a note**. It carries the note body,
and above it the scope contract, and below it the full claim table with the columns
the note's prose compresses. The verifier rules against the claim table; the note
body is what may eventually be promoted. Keep all three in one file so nothing has
to be reassembled from two.
