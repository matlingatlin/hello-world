"""The contribute-back gate: what earns a place in the library.

A part that ships from the catalog carries authority — it is offered *instead of*
generating, and nobody reviews it again per project. So the bar to get in is the
bar the library's whole promise rests on, and it is deliberately hard to clear:

- **generalized**, not this project's code with the names left in. A candidate
  that says `booking` where it means "the entity" would rename a future
  project's concept to ours;
- **no leakage** — no project names, no URLs, no keys, no copy written for one
  customer;
- **tested and security-reviewed**, with scores above a bar;
- **instrumented**, because an entry that lands without ids breaks the marking
  coupling for every project that assembles it.

The contribution itself (writing the entry into the catalog) is stubbed in this
slice — `propose` returns the reviewed candidate rather than persisting it. The
gate is not stubbed: it is the part that has to exist before anything is ever
added, and adding entries without it would be worse than having no library.
"""

from __future__ import annotations

import re
from enum import StrEnum

from pydantic import BaseModel, Field

from ..core.instrumentation import ID_ATTRIBUTE
from .entry import CatalogEntry
from .placeholders import ENTITY

MIN_ACCESSIBILITY = 85
MIN_LIGHTHOUSE = 85

_UI_SUFFIXES = (".tsx", ".jsx")
_TEST_MARKERS = ("test", "spec")

# Names the standards reserve for documentation and testing, and which therefore
# say nothing about anybody's project (RFC 2606, RFC 6761).
#
# This exists because the rule below refused real work: `pkg_auth` cleared all
# five build gates in the first real run and was rejected for containing
# `guest@example.com` and `https://app.example.com/auth/callback` — which is
# what a model writes in a test, and exactly what these names are FOR. A gate
# that cannot tell a fixture from a customer's address refuses everything, and a
# rule that refuses everything is not enforcement, it is a switch left off.
#
# The rule itself is unchanged for everything else: a real domain still fails.
_RESERVED_HOSTS = (
    r"(?:localhost|127\.0\.0\.1|\[::1\]"
    r"|(?:[\w-]+\.)*example\.(?:com|org|net)"
    r"|[\w-]+\.(?:test|example|invalid|localhost))"
)

# Things that are always somebody's, never the library's.
_LEAK_PATTERNS: tuple[tuple[str, str], ...] = (
    (rf"https?://(?!{_RESERVED_HOSTS}\b)[\w.-]+", "a hard-coded external URL"),
    # The key body may contain hyphens and underscores. It did not used to, and
    # the consequence was that this rule caught only the legacy `sk-<alnum>`
    # shape: a real `sk-ant-api03-…` or `sk-proj-…` key stopped the match at the
    # first hyphen and sailed through the one check meant to stop exactly that.
    # The three prefixes are the three providers this engine can be given keys
    # for (execution/provider.py).
    (r"\b(?:sk-[A-Za-z0-9_-]{20,}|AIza[A-Za-z0-9_-]{30,})", "what looks like an API key"),
    (r"(?i)(api[_-]?key|secret|password)\s*[:=]\s*[\"'][^\"']{8,}[\"']", "a hard-coded credential"),
    (rf"(?i)\b[\w.+-]+@(?!{_RESERVED_HOSTS}\b)[\w-]+\.[\w.]+\b", "an email address"),
)


class Verdict(StrEnum):
    accepted = "accepted"
    rejected = "rejected"


class GateFinding(BaseModel):
    rule: str
    message: str
    file: str = ""


class GateResult(BaseModel):
    verdict: Verdict
    findings: list[GateFinding] = Field(default_factory=list)

    @property
    def accepted(self) -> bool:
        return self.verdict is Verdict.accepted

    def explain(self) -> str:
        if self.accepted:
            return "Accepted into the library."
        return "Not added:\n" + "\n".join(
            f"  - [{f.rule}] {f.message}" + (f" ({f.file})" if f.file else "")
            for f in self.findings
        )


class Candidate(BaseModel):
    """A part of a built app being offered to the library.

    `project_terms` is what makes leakage checkable: the words this project used
    for its own concepts. A candidate still carrying them has not been
    generalized, it has only been copied.
    """

    entry: CatalogEntry
    project_terms: list[str] = Field(default_factory=list)


def _has_tests(entry: CatalogEntry) -> bool:
    return any(
        any(marker in path.lower() for marker in _TEST_MARKERS) and body.strip()
        for path, body in entry.files.items()
    )


def _renders_ui(entry: CatalogEntry) -> bool:
    return any(path.endswith(_UI_SUFFIXES) for path in entry.files)


def review(candidate: Candidate) -> GateResult:
    """Judge a candidate against every rule. Deterministic — no model."""
    entry = candidate.entry
    findings: list[GateFinding] = []

    if not entry.files:
        findings.append(GateFinding(rule="has_files", message="the candidate contributes no files"))

    if not entry.quality.tested or not _has_tests(entry):
        findings.append(
            GateFinding(
                rule="tested",
                message="no test file ships with it, so nothing keeps it working",
            )
        )
    if not entry.quality.security_reviewed:
        findings.append(
            GateFinding(rule="security_reviewed", message="it has not been security-reviewed")
        )
    findings += _score_findings(entry)

    findings += _generalization_findings(entry)
    findings += _leakage_findings(entry, candidate.project_terms)

    if _renders_ui(entry) and not entry.element_ids:
        findings.append(
            GateFinding(
                rule="instrumented",
                message=(
                    f"it renders UI but declares no {ID_ATTRIBUTE} — every project that "
                    "assembled it would have unmarkable elements"
                ),
            )
        )

    return GateResult(
        verdict=Verdict.rejected if findings else Verdict.accepted, findings=findings
    )


def _score_findings(entry: CatalogEntry) -> list[GateFinding]:
    """Quality, judged on evidence that exists.

    A seed carries Lighthouse and accessibility numbers a person measured, and
    those must clear the bar. An entry learned from a build has no such numbers —
    the build does not run Lighthouse yet (B048) — so what it is held to is what
    the build DID check: every gate it was put through passed. That is a real
    standard, not a waived one; treating unmeasured scores as zeros would refuse
    every contribution, and treating them as 85 would be a lie.
    """
    quality = entry.quality
    if not quality.scores_measured:
        if quality.all_build_gates_passed:
            return []
        return [
            GateFinding(
                rule="scores",
                message=(
                    "nothing measured this: no accessibility or Lighthouse score, and it did "
                    f"not pass every build gate ({quality.build_gates_passed}/"
                    f"{quality.build_gates_total})"
                ),
            )
        ]

    findings: list[GateFinding] = []
    if quality.accessibility_score < MIN_ACCESSIBILITY:
        findings.append(
            GateFinding(
                rule="scores",
                message=(
                    f"accessibility {quality.accessibility_score} is below the bar of "
                    f"{MIN_ACCESSIBILITY}"
                ),
            )
        )
    if quality.lighthouse_score < MIN_LIGHTHOUSE:
        findings.append(
            GateFinding(
                rule="scores",
                message=(
                    f"lighthouse {quality.lighthouse_score} is below the bar of {MIN_LIGHTHOUSE}"
                ),
            )
        )
    return findings


def _generalization_findings(entry: CatalogEntry) -> list[GateFinding]:
    """A feature entry must be written against the placeholder, not a name."""
    if entry.layer.value != "feature":
        return []
    if any(ENTITY in path or ENTITY in body for path, body in entry.files.items()):
        return []
    return [
        GateFinding(
            rule="generalized",
            message=(
                f"a feature entry must use the {ENTITY} placeholder so it can be adapted; "
                "this one is written against one project's own concept"
            ),
        )
    ]


def _leakage_findings(entry: CatalogEntry, project_terms: list[str]) -> list[GateFinding]:
    findings: list[GateFinding] = []
    terms = [t.strip() for t in project_terms if t.strip()]

    for path, body in sorted(entry.files.items()):
        haystack = f"{path}\n{body}"
        for pattern, what in _LEAK_PATTERNS:
            if re.search(pattern, haystack):
                findings.append(
                    GateFinding(
                        rule="no_leakage",
                        message=f"{what} would ship to every project that assembles this",
                        file=path,
                    )
                )
        for term in terms:
            if re.search(rf"\b{re.escape(term)}\b", haystack, re.IGNORECASE):
                findings.append(
                    GateFinding(
                        rule="no_leakage",
                        message=(
                            f"'{term}' is this project's own word and would be written into "
                            "every project that assembles this"
                        ),
                        file=path,
                    )
                )
    return findings


def propose(candidate: Candidate) -> GateResult:
    """Offer a candidate to the library.

    STUB for this slice: a candidate that clears the gate is reported as
    accepted, not written to the catalog. Curation is a human step by design
    (docs/LIBRARY.md) — automatic contribution is how a library fills up with
    things nobody chose.
    """
    return review(candidate)
