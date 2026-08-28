---
name: comparable-products-sweep
description: "Use when hunting for what a product is missing, by enumerating comparable existing products from the outside and diffing their capability and actor coverage against a brief — the pass that finds requirements nobody thought to state. Produces a coverage table where every capability is present, absent, or deliberately refused, and every claim carries the vendor source it came from. NOT for reviewing whether an implementation conforms to an external spec (external-domain-audit), NOT for judging or ranking what the sweep turns up (proposal-adjudication, selection-dossier), NOT for competitive positioning or pricing strategy."
---

# What the neighbours have that the brief never mentions

This is the strongest measured lever available for "what is missing", and it
beats every form of thinking harder about the brief.

Measured (30 subjects, requirements elicited by interview and then extended by
searching app stores for comparable existing products): only **30–38%** of the
post-interview content traced to the customer's original ideas at all; up to
**21%** of it was on completely novel topics; the comparable-products pass added
**up to 42% additional feature coverage** and surfaced **8–17% novel roles**.
The authors' own framing is that requirements are *"not elicited in a strict
sense, but actually co-created."* Limits: students, a fictional customer, one
domain — the design maps onto "what is missing here" better than anything else
in the literature, but it is one study.

Expect the yield to be **useful rather than novel**, and do not treat that as
failure. The only study that tracked workshop ideas into a delivered
specification found **2 of 139** fully novel and **106 of 139 (76%)** with real
impact — the effect was *"surfacing requirements known but not documented"*.
That is the legitimate dominant yield of this step.

One warning about your own reaction: structured trigger questions produced
significantly more requirement fragments than free ideation (p ≤ 0.0001, n = 85,
within-subject) and were rated **significantly less useful** by the people who
used them (3/5 against 4/5, p = 0.0003). The same dissociation was measured
independently in security threat identification. **Never use "did that feel
useful?" as the signal.** This step will feel mechanical. Run it anyway.

This procedure opens no files. Its input is your brief and the open web.

## 1 · Enumerate from the outside, before you decide what counts

Search for products that solve the brief's problem for the brief's person —
including ones you would not call competitors. Use `WebSearch`, then `WebFetch`
their own documentation rather than a roundup article: a roundup tells you what
a journalist noticed, and the mechanism you are looking for is usually only in
the vendor's docs.

Include, deliberately, at least one that is:

- **adjacent, not direct** — solves the same problem for a different person, or
  a neighbouring problem for the same person;
- **older than the category** — the way this was done before the current
  technology existed;
- **failed or discontinued** — what it did, and what it was for. A dead product
  is the cheapest available record of a capability someone believed in.

**Artefact:** the product list, each with the URL you actually fetched and one
line saying why it is in the set. A product you named from memory and did not
open is marked `unfetched` and its rows are marked `unverified`.

## 2 · Extract mechanisms, not features

A feature is a name on a marketing page. A mechanism is how it works, and only
the mechanism transfers. *"Visual editing"* is a feature; *"a compile-time id is
attached to every generated element so a style change is applied by a codemod
without a model call"* is a mechanism.

For each product write the mechanisms you can actually establish, with the
source. When a page asserts a capability but describes no mechanism, record it
as `claimed, mechanism not published` — that is honest and it is also
information about what the vendor considers its moat.

**Artefact:** product → mechanism → source URL → `documented | claimed | inferred`.

## 3 · Diff against the brief, both directions

Two tables. The second one is the one people skip.

**Capabilities.** Every mechanism from step 2 against the brief:

| Verdict | Meaning |
|---|---|
| `in the brief` | the brief already implies it |
| `absent` | nobody stated it and it plausibly belongs |
| `deliberately refused` | it conflicts with a position, and you name which |
| `does not apply` | with the reason |

**Actors.** Every *role* these products serve — not just the primary user. The
person who pays, the person who inherits the thing afterwards, the person who
has to approve it, the person who is affected and never touches it, the operator,
the auditor. The measured pass found **8–17% novel roles**, and a role nobody
named has no requirements attached to it at all.

**Artefact:** both tables, complete. A row reading `absent` with nothing after it
is not a finding — say what it would mean here.

## 4 · Say what the whole category does not do

Every product you found shares assumptions. Write the ones you can see: what
none of them offers, what all of them require of the person, what all of them
assume about the problem.

This is the only step in the sweep that can produce something the category has
not already thought of, and it is worth exactly as much as it is worth — do not
inflate it. Mark each line `observed across all N` or `speculation`.

**Artefact:** the category-assumption list, each line marked, each with the
count of products it holds across.

## 5 · Hand over what you could not settle

Some questions this sweep raises can only be answered by someone who can see the
existing system, and you cannot. Write them as questions addressed to the
adjudicator.

**Artefact:** the open-question list. Each is a question that a `file:line`
could answer, phrased so that it can be.

## When this does not apply

- There are no comparable products, and you have searched enough to say so with
  the searches named. Write that; it is a finding about the category.
- You are checking whether an implementation conforms to a published spec. That
  is `external-domain-audit`, which reasons from the contract inward.
- You are being asked which of these products to adopt, or how to position
  against them. Neither is this procedure, and the second is not any agent's
  call to make silently.
