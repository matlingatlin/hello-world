"""The vision loop's judgment: does the running package meet its "done when"?

This is where a model earns its keep — the deterministic agents can check that a
test file exists, but only judgment can look at a rendered screen and say whether
"a guest can book a table in a few taps" is true.

Structured in, structured out: the critique gets the acceptance criteria and what
the page actually did, and must answer per criterion. A free-text verdict cannot
be fed back as a fix instruction.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from pydantic import BaseModel, Field

from ..core.console import ConsoleReport
from ..execution.provider import ProviderRegistry
from ..execution.relay import RelayOptions, run_relay
from ..layerc.criteria import Criterion, interacting, judgeable, scoped_out
from ..layerc.plan import BuildPackage
from .file_plan import planned_files

CRITIQUE_SYSTEM = """You are Scio's critique agent. You judge whether a built package \
meets its acceptance criteria, using the evidence you are given.

Answer with JSON only, in exactly this shape:

{"verdict": "pass" | "fail",
 "criteria": [{"criterion": "...", "met": true|false, "why": "..."}],
 "problems": ["a specific, fixable statement of what is wrong", ...]}

Rules:
- Judge only against the criteria listed. Not "is this good code" — "does it do this".
- A criterion you cannot check from the evidence is NOT met; say so in `why`.
- `problems` must be actionable: what is wrong and where, not "improve the UX".
- If every criterion is met, `verdict` is "pass" and `problems` is empty."""


class CriterionVerdict(BaseModel):
    criterion: str
    met: bool
    why: str = ""


class Critique(BaseModel):
    verdict: str  # "pass" | "fail"
    criteria: list[CriterionVerdict] = Field(default_factory=list)
    problems: list[str] = Field(default_factory=list)
    parsed: bool = True
    raw: str = ""
    unjudged: list[str] = Field(
        default_factory=list,
        description="Criteria no evidence channel could settle — recorded, never a failure",
    )

    @property
    def passed(self) -> bool:
        return self.verdict == "pass" and not self.problems

    @property
    def unmet(self) -> list[str]:
        return [c.criterion for c in self.criteria if not c.met]


@dataclass
class Evidence:
    """What the critique gets to look at."""

    console: ConsoleReport
    rendered_text: str = ""
    screenshot_path: str = ""
    element_ids: list[str] = field(default_factory=list)
    extra: list[str] = field(default_factory=list)

    def as_prompt_section(self) -> str:
        lines = ["## Evidence from the running package", ""]
        lines.append(f"Console failures: {self.console.failures or 'none'}")
        if self.console.suppressed:
            lines.append(f"(benign console noise, ignored: {self.console.suppressed})")
        if self.element_ids:
            lines.append(f"Elements present: {', '.join(sorted(self.element_ids))}")
        if self.rendered_text:
            lines += ["", "Rendered text:", self.rendered_text[:2000]]
        if self.screenshot_path:
            lines.append(f"Screenshot: {self.screenshot_path}")
        lines += self.extra
        return "\n".join(lines)


def _extract_json(text: str) -> dict | None:
    """Find the JSON object in a reply that may be wrapped in prose or fences."""
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    candidate = fenced.group(1) if fenced else None
    if candidate is None:
        start = text.find("{")
        end = text.rfind("}")
        candidate = text[start : end + 1] if start != -1 and end > start else None
    if candidate is None:
        return None
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def parse_critique(text: str) -> Critique:
    """Parse a critique reply. An unparseable reply is a FAIL, never a pass.

    Treating "I couldn't read the verdict" as success is how a broken package
    ships; the loop must see it as something to fix or report honestly.
    """
    data = _extract_json(text)
    if data is None:
        return Critique(
            verdict="fail",
            problems=["The critique could not be parsed, so the package is not confirmed."],
            parsed=False,
            raw=text[:2000],
        )

    criteria = [
        CriterionVerdict(
            criterion=str(item.get("criterion", "")),
            met=bool(item.get("met", False)),
            why=str(item.get("why", "")),
        )
        for item in data.get("criteria", [])
        if isinstance(item, dict)
    ]
    problems = [str(p) for p in data.get("problems", []) if str(p).strip()]
    verdict = str(data.get("verdict", "fail")).lower()

    # A "pass" that leaves criteria unmet is a contradiction; trust the criteria.
    if verdict == "pass" and any(not c.met for c in criteria):
        verdict = "fail"
        problems = problems or [
            f"Criterion not met: {c.criterion} — {c.why}" for c in criteria if not c.met
        ]

    return Critique(
        verdict=verdict, criteria=criteria, problems=problems, parsed=True, raw=text[:2000]
    )


def build_critique_prompt(package: BuildPackage, evidence: Evidence) -> str:
    """Only the criteria this evidence can actually settle.

    Sending the rest produced exactly one thing on the first real run: three
    "no evidence was provided" failures on a package that was, in fact, correct.
    """
    criteria = "\n".join(f"- {c}" for c in judgeable_criteria(package))
    return (
        f"## Package\n{package.id} — {package.goal}\n\n"
        f"## Acceptance criteria (judge against exactly these)\n{criteria}\n\n"
        f"{evidence.as_prompt_section()}\n"
    )


def judgeable_criteria(package: BuildPackage) -> list[Criterion]:
    """The package's criteria that the vision loop's evidence can settle."""
    return judgeable(package.acceptance_criteria, planned_files(package))


def interaction_criteria(package: BuildPackage) -> list[Criterion]:
    """The package's criteria settled by driving the app, not by judgment.

    They never reach the critique prompt: a model looking at a screenshot cannot
    tell whether the row reached Postgres, and asking it to would manufacture
    exactly the failure B054 exists to prevent. A script can tell, so a script
    is what asks.
    """
    return interacting(package.acceptance_criteria, planned_files(package))


def unjudged_criteria(package: BuildPackage) -> list[str]:
    """What nobody judged, and why — the trust receipt's raw material."""
    return scoped_out(package.acceptance_criteria, planned_files(package))


async def critique_package(
    package: BuildPackage,
    evidence: Evidence,
    *,
    registry: ProviderRegistry,
    passes: int = 1,
) -> Critique:
    """Ask the relay to judge the package.

    One pass by default: a critique is a short judgment, and the four-pass relay
    would multiply cost on every loop iteration for little gain. Hard packages
    can raise it.

    A package whose criteria the evidence cannot settle (a migration renders
    nothing) is not sent at all: there is no question to ask, and asking one
    anyway only manufactures a failure.
    """
    if not judgeable_criteria(package):
        return Critique(
            verdict="pass",
            criteria=[],
            problems=[],
            unjudged=unjudged_criteria(package),
        )

    prompt = build_critique_prompt(package, evidence)
    try:
        result = await run_relay(
            "review",
            prompt,
            registry=registry,
            options=RelayOptions(
                passes=passes,
                system=CRITIQUE_SYSTEM,
                temperature=0.0,
                # It reads a whole package before answering; the relay's default
                # is sized for a one-line reply.
                timeout_s=300.0,
            ),
        )
    except Exception as exc:
        return Critique(
            verdict="fail",
            problems=[f"The critique could not run: {exc}"],
            parsed=False,
        )
    critique = parse_critique(result.final_text)
    # What nobody could judge travels with the verdict, so a "pass" is never
    # mistaken for "everything was checked".
    critique.unjudged = unjudged_criteria(package)
    return critique
