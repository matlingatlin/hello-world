"""B048: does the app we are handing over actually compile?

Written after a build reported **"5 of 5 parts work"** for an app whose
`lib/db/booking.ts` imported `getSupabaseClient` from a `lib/supabase.ts` that
exports one boolean. Every gate passed it honestly — and every gate was
per-package, while the failure was between two of them.
"""

from __future__ import annotations

import json
from pathlib import Path

from scio_engine.builder.typecheck import TypeProblem, blame, typecheck


def workspace(tmp_path: Path, *, with_compiler: bool = True) -> Path:
    (tmp_path / "tsconfig.json").write_text(json.dumps({"compilerOptions": {"strict": True}}))
    if with_compiler:
        bin_dir = tmp_path / "node_modules" / ".bin"
        bin_dir.mkdir(parents=True)
        return tmp_path
    return tmp_path


def fake_tsc(app_dir: Path, *, output: str = "", code: int = 0) -> None:
    """A `tsc` that prints what we tell it. The real one is exercised by the
    engine's own suite running against real workspaces; what is under test here
    is how its output is read."""
    tsc = app_dir / "node_modules" / ".bin" / "tsc"
    tsc.write_text(f'#!/bin/sh\ncat <<"EOF"\n{output}\nEOF\nexit {code}\n')
    tsc.chmod(0o755)


class TestReadingTheCompiler:
    def test_a_clean_compile_passes(self, tmp_path: Path):
        app = workspace(tmp_path)
        fake_tsc(app)

        report = typecheck(app)

        assert report.ran is True
        assert report.passed is True

    def test_an_error_is_read_with_its_file_and_line(self, tmp_path: Path):
        app = workspace(tmp_path)
        fake_tsc(
            app,
            output=(
                "lib/db/booking.ts(1,10): error TS2305: Module '\"@/lib/supabase\"' has no "
                "exported member 'getSupabaseClient'."
            ),
            code=2,
        )

        report = typecheck(app)

        assert report.passed is False
        problem = report.problems[0]
        assert (problem.file, problem.line, problem.code) == ("lib/db/booking.ts", 1, "TS2305")
        assert "getSupabaseClient" in problem.message

    def test_no_compiler_is_unjudged_and_never_a_pass(self, tmp_path: Path):
        # Same rule as the browser checks: an answer nobody asked for is not a
        # yes. It rides along so "works" keeps meaning "works, and here is what
        # nobody checked".
        report = typecheck(workspace(tmp_path, with_compiler=False))

        assert report.ran is False
        assert report.passed is False
        assert "nobody asked the compiler" in report.unjudged

    def test_an_unreadable_failure_is_unjudged_rather_than_a_pass(self, tmp_path: Path):
        app = workspace(tmp_path)
        fake_tsc(app, output="Segmentation fault", code=139)

        report = typecheck(app)

        assert report.passed is False
        assert "without a readable error" in report.unjudged

    def test_a_thousand_errors_are_capped(self, tmp_path: Path):
        app = workspace(tmp_path)
        lines = "\n".join(
            f"app/page.tsx({i},1): error TS2304: Cannot find name 'x{i}'." for i in range(60)
        )
        fake_tsc(app, output=lines, code=2)

        report = typecheck(app)

        assert len(report.problems) == 20
        assert report.truncated == 40


class TestWhoIsToBlame:
    def test_an_error_lands_on_the_package_that_owns_the_file(self):
        problems = [TypeProblem(file="lib/db/booking.ts", line=1, code="TS2305", message="…")]

        blamed = blame(problems, {"pkg_feature_booking": ["lib/db/booking.ts"]})

        assert list(blamed) == ["pkg_feature_booking"]

    def test_a_file_nobody_owns_is_blamed_on_nobody(self):
        # The scaffold's own files, or one a package wrote outside its plan.
        # Pinning it on whichever part was nearest would be a guess with a name
        # attached.
        problems = [TypeProblem(file="next.config.js", line=3, code="TS1005", message="…")]

        blamed = blame(problems, {"pkg_foundation": ["app/layout.tsx"]})

        assert list(blamed) == [""]
