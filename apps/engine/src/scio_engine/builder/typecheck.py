"""Does the app the user is being handed actually compile?

Nothing asked that until now, and the first real answer was no. A build that had
just reported **"5 of 5 parts work"** shipped a `lib/db/booking.ts` importing
`getSupabaseClient` from a `lib/supabase.ts` that exports one boolean. Every
existing gate passed it honestly:

- instrumentation checks that this app's ids resolve, and they did;
- the validation agents read one package's own files, and the import was fine
  *there* — it is the other end that is missing;
- the console classifier only sees a route somebody opened;
- the critique judged the package against its acceptance criteria, not against
  the app it was joining.

Every one of those is per-package. The failure is *between* packages, which is
exactly the seam assembly creates — a library component written against an
interface this app's foundation does not provide. So this gate is app-wide and
runs once, after everything is in place.

It never passes on absence: no compiler means "nobody checked", recorded as
unjudged, the same rule the browser checks follow.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

TSC_TIMEOUT_S = 300
"""A cold `tsc` on a Next app is tens of seconds; this is a ceiling, not a target."""

MAX_REPORTED = 20
"""Enough to act on. A thousand errors from one missing type is noise, and the
first few say the same thing as the rest."""

# tsc's default format: `path/to/file.ts(12,7): error TS2305: message`
_ERROR = re.compile(
    r"^(?P<file>[^(]+)\((?P<line>\d+),\d+\): error (?P<code>TS\d+): (?P<message>.+)$"
)


@dataclass
class TypeProblem:
    file: str
    line: int
    code: str
    message: str

    def as_line(self) -> str:
        return f"{self.file}:{self.line} — {self.message}"


@dataclass
class TypecheckReport:
    """What the compiler said, or why nobody asked it."""

    ran: bool = False
    problems: list[TypeProblem] = field(default_factory=list)
    unjudged: str = ""
    truncated: int = 0

    @property
    def passed(self) -> bool:
        """True only when a compiler ran and found nothing.

        A report that could not run is not a pass — it is an unanswered
        question, and it is recorded as one.
        """
        return self.ran and not self.problems


def _compiler(app_dir: Path) -> Path | None:
    local = app_dir / "node_modules" / ".bin" / "tsc"
    return local if local.exists() else None


def typecheck(app_dir: Path) -> TypecheckReport:
    """Run the app's own TypeScript compiler over the app, and report.

    The app's own, deliberately: the generated app pins its TypeScript version,
    and checking it with a different one would report errors its `next build`
    never would.
    """
    app_dir = Path(app_dir)
    tsc = _compiler(app_dir)
    if tsc is None:
        return TypecheckReport(
            unjudged=(
                "whether the app compiles — there is no TypeScript in this workspace, "
                "so nobody asked the compiler"
            )
        )
    if not (app_dir / "tsconfig.json").exists():
        return TypecheckReport(
            unjudged="whether the app compiles — the workspace has no tsconfig.json"
        )

    try:
        finished = subprocess.run(
            [str(tsc), "--noEmit", "-p", "tsconfig.json"],
            cwd=app_dir,
            capture_output=True,
            text=True,
            timeout=TSC_TIMEOUT_S,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return TypecheckReport(unjudged=f"whether the app compiles — tsc did not finish ({exc})")

    problems: list[TypeProblem] = []
    for raw in (finished.stdout + finished.stderr).splitlines():
        match = _ERROR.match(raw.strip())
        if match:
            problems.append(
                TypeProblem(
                    file=match["file"].strip(),
                    line=int(match["line"]),
                    code=match["code"],
                    message=match["message"].strip(),
                )
            )

    if finished.returncode != 0 and not problems:
        # It failed in a way we cannot read. Reporting "compiles" here would be
        # the worst of both: a claim, on evidence nobody understood.
        return TypecheckReport(
            unjudged=(
                "whether the app compiles — tsc failed without a readable error: "
                f"{(finished.stderr or finished.stdout).strip()[:200]}"
            )
        )

    truncated = max(0, len(problems) - MAX_REPORTED)
    return TypecheckReport(ran=True, problems=problems[:MAX_REPORTED], truncated=truncated)


def blame(
    problems: list[TypeProblem], package_files: dict[str, list[str]]
) -> dict[str, list[TypeProblem]]:
    """Which package owns each broken file.

    A file nobody owns — the scaffold's own, or one a package wrote outside its
    plan — is blamed on "" so the caller can report it against the app rather
    than silently dropping it.
    """
    owner = {path: package for package, paths in package_files.items() for path in paths}
    by_package: dict[str, list[TypeProblem]] = {}
    for problem in problems:
        by_package.setdefault(owner.get(problem.file, ""), []).append(problem)
    return by_package
