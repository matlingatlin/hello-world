"""Validation agents — the checks that run on every package's output.

Deterministic on purpose. Asking a model whether the code it just wrote is
secure gets you an opinion; grepping for a hardcoded key gets you a fact. The
model's judgment is used where judgment is needed (the critique), not here.

Each agent returns findings; the loop feeds them back as fix instructions.
"""

from __future__ import annotations

import re
from enum import StrEnum

from pydantic import BaseModel, Field

from ..core.instrumentation import ID_ATTRIBUTE
from ..layerc.plan import BuildPackage


class Agent(StrEnum):
    code_quality = "code_quality"
    tests_present = "tests_present"
    security = "security"
    contract_consistency = "contract_consistency"


class Severity(StrEnum):
    error = "error"
    warning = "warning"


class Finding(BaseModel):
    agent: Agent
    severity: Severity = Severity.error
    message: str
    file: str = ""

    def as_instruction(self) -> str:
        where = f" ({self.file})" if self.file else ""
        return f"[{self.agent}]{where} {self.message}"


class ValidationReport(BaseModel):
    findings: list[Finding] = Field(default_factory=list)

    @property
    def errors(self) -> list[Finding]:
        return [f for f in self.findings if f.severity is Severity.error]

    @property
    def passed(self) -> bool:
        return not self.errors

    def instructions(self) -> list[str]:
        return [f.as_instruction() for f in self.errors]


# Things that must never appear in generated code. Each pattern is a rule from
# the playbook's secure-by-default section, made checkable.
_SECRET_PATTERNS: tuple[tuple[str, str], ...] = (
    (r'(?i)(api[_-]?key|secret|password|token)\s*[:=]\s*["\'][A-Za-z0-9_\-]{12,}["\']',
     "a credential appears to be hardcoded — secrets come from environment variables only"),
    (r"(?i)\bsk-[A-Za-z0-9]{16,}", "what looks like a provider API key is embedded in the code"),
    (r"(?i)eyJ[A-Za-z0-9_\-]{20,}\.", "a JWT is embedded in the code"),
)

_UNSAFE_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"dangerouslySetInnerHTML", "dangerouslySetInnerHTML risks XSS; render text instead"),
    (r"\beval\s*\(", "eval() must not appear in generated code"),
    (r"`\s*SELECT .*\$\{", "SQL built by string interpolation — use parameterised queries"),
)

_QUALITY_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"\bTODO\b|\bFIXME\b", "a TODO/FIXME was left behind — finish it or leave it out"),
    (r"@ts-ignore|@ts-nocheck", "type checking was suppressed instead of the type being fixed"),
    (r":\s*any\b", "an `any` type defeats the point of TypeScript here"),
)

_CODE_SUFFIXES = (".ts", ".tsx", ".js", ".jsx")


def _scan(files: dict[str, str], patterns, agent: Agent, severity=Severity.error) -> list[Finding]:
    findings: list[Finding] = []
    for path, content in sorted(files.items()):
        if not path.endswith(_CODE_SUFFIXES):
            continue
        for pattern, message in patterns:
            if re.search(pattern, content):
                findings.append(
                    Finding(agent=agent, severity=severity, message=message, file=path)
                )
    return findings


def check_security(files: dict[str, str]) -> list[Finding]:
    """Secrets and unsafe constructs. The wedge is developer-grade output; a
    leaked key in generated code would end that claim (ADR-0001)."""
    return _scan(files, _SECRET_PATTERNS, Agent.security) + _scan(
        files, _UNSAFE_PATTERNS, Agent.security
    )


def check_code_quality(files: dict[str, str]) -> list[Finding]:
    findings = _scan(files, _QUALITY_PATTERNS, Agent.code_quality, Severity.warning)
    for path, content in sorted(files.items()):
        if path.endswith(_CODE_SUFFIXES) and not content.strip():
            findings.append(
                Finding(
                    agent=Agent.code_quality,
                    message="the file is empty",
                    file=path,
                )
            )
    return findings


def check_tests_present(package: BuildPackage, files: dict[str, str]) -> list[Finding]:
    """The playbook says every operation gets a test. A package that ships no
    test has not met the house rules, whatever the screenshot looks like."""
    expects_tests = any(
        node.kind == "operation" for node in package.architecture_slice
    ) or package.kind.value in {"auth", "connector"}
    if not expects_tests:
        return []

    test_files = [p for p in files if "test" in p.lower() or "spec" in p.lower()]
    if not test_files:
        return [
            Finding(
                agent=Agent.tests_present,
                message=(
                    f"'{package.id}' has operations but no test file. Every operation needs a "
                    "test for its happy path and its main failure."
                ),
            )
        ]
    if not any(files[p].strip() for p in test_files):
        return [
            Finding(
                agent=Agent.tests_present,
                message="the test file is empty",
                file=test_files[0],
            )
        ]
    return []


def check_contract_consistency(package: BuildPackage, files: dict[str, str]) -> list[Finding]:
    """Does the code actually cover the slice it was given?

    Screens and operations the package owns must be findable in what it wrote —
    a build that quietly skips half its contract passes every other check.
    """
    findings: list[Finding] = []
    blob = "\n".join(files.values())

    for node in package.architecture_slice:
        if node.kind == "operation" and node.name not in blob:
            findings.append(
                Finding(
                    agent=Agent.contract_consistency,
                    message=(
                        f"operation '{node.name}' is in this package's slice but appears "
                        "nowhere in the code"
                    ),
                )
            )
        if node.kind == "screen":
            expected = _route_page_path(node.name)
            if expected not in files:
                findings.append(
                    Finding(
                        agent=Agent.contract_consistency,
                        message=f"screen '{node.name}' has no page file ({expected})",
                    )
                )

    if _package_renders_ui(package, files) and ID_ATTRIBUTE not in blob:
        findings.append(
            Finding(
                agent=Agent.contract_consistency,
                message=(
                    f"no {ID_ATTRIBUTE} anywhere in this package's UI — nothing in it could "
                    "be marked in the design window"
                ),
            )
        )
    return findings


def _route_page_path(route: str) -> str:
    from .file_plan import _route_to_page

    return _route_to_page(route)


def _package_renders_ui(package: BuildPackage, files: dict[str, str]) -> bool:
    return any(path.endswith((".tsx", ".jsx")) for path in files)


def validate_package(package: BuildPackage, files: dict[str, str]) -> ValidationReport:
    """Run every agent over a package's generated files."""
    return ValidationReport(
        findings=[
            *check_security(files),
            *check_code_quality(files),
            *check_tests_present(package, files),
            *check_contract_consistency(package, files),
        ]
    )
