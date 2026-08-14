"""The three defects the first real build against Claude exposed (B054).

Each of these passed every test we had. They only appeared when a real model
wrote real code into a real sandbox — so each one gets a test here that first
reproduces the defect and then pins the fix, with the fake provider, so the next
regression is caught for free.

1. `pkg_foundation` FAILED on criteria its own file plan could never satisfy.
2. The model imported `@/lib/env` — a file no package produces.
3. Elements arrived with `data-scio-id` and no `data-scio-package`.
"""

import json
from pathlib import Path

import pytest

from conftest import make_booking_spec
from scio_engine.builder.critique import (
    Evidence,
    build_critique_prompt,
    critique_package,
    judgeable_criteria,
    unjudged_criteria,
)
from scio_engine.builder.file_plan import planned_files
from scio_engine.builder.loop import BuildOptions, ScriptedPreview, build_package
from scio_engine.builder.result import PackageStatus
from scio_engine.builder.validation import Agent, validate_package
from scio_engine.core.console import classify_console
from scio_engine.core.instrumentation import Manifest
from scio_engine.core.manifest_builder import build_manifest
from scio_engine.core.preview import Observation
from scio_engine.core.stamping import ids_missing_package, stamp_files, stamp_package
from scio_engine.core.verifier import verify_instrumentation
from scio_engine.execution.provider import (
    Completion,
    ModelProvider,
    ProviderRegistry,
    Vendor,
)
from scio_engine.layerb.derive import derive_architecture
from scio_engine.layerc.criteria import (
    Observability,
    coerce,
    cover,
    renders,
    unobservable,
)
from scio_engine.layerc.decompose import FOUNDATION_ID, decompose
from scio_engine.layerc.plan import BuildPackage, NodeRef, PackageKind
from scio_engine.layerc.service import run_layer_c
from scio_engine.layerc.validate import validate_plan


def booking_architecture():
    return derive_architecture(make_booking_spec())


def foundation_of(arch) -> BuildPackage:
    return next(p for p in decompose(arch) if p.id == FOUNDATION_ID)


# --------------------------------------------------------------------------
# 1. The spurious pkg_foundation failure
# --------------------------------------------------------------------------


class TestCriteriaMatchTheContract:
    """The real run's headline: the critique was right and the contract was wrong.

    It asked for a test-runner execution, an env-var audit and secure headers
    from a package whose file plan is a layout, a header and a supabase client,
    judged from a screenshot and a console log.
    """

    def test_the_criteria_that_failed_the_real_run_are_no_longer_judged(self):
        foundation = foundation_of(booking_architecture())
        judged = [c.text for c in judgeable_criteria(foundation)]

        # The three the real critique answered "no evidence was provided" to.
        assert not any("test runner" in text for text in judged)
        assert not any("Secrets are read" in text for text in judged)
        assert not any("Secure defaults" in text for text in judged)

    def test_what_the_shell_is_actually_judged_on_is_the_shell(self):
        judged = [c.text for c in judgeable_criteria(foundation_of(booking_architecture()))]
        assert judged, "the shell must still be judged on something"
        assert any("renders" in text for text in judged)

    def test_nothing_is_deleted_it_is_recorded_as_unjudged(self):
        unjudged = unjudged_criteria(foundation_of(booking_architecture()))
        assert any("test runner" in item for item in unjudged)
        # ...and each one says WHY nobody checked it.
        assert all("—" in item for item in unjudged)

    def test_the_critique_prompt_only_carries_answerable_criteria(self):
        foundation = foundation_of(booking_architecture())
        prompt = build_critique_prompt(
            foundation, Evidence(console=classify_console([]), rendered_text="Book your table")
        )
        assert "test runner" not in prompt
        assert "renders" in prompt

    @pytest.mark.asyncio
    async def test_a_package_nothing_can_judge_is_not_sent_to_the_model(self):
        """A migration renders nothing. Asking for a verdict on it invents one."""
        package = BuildPackage(
            id="pkg_schema",
            kind=PackageKind.schema,
            goal="Create the schema.",
            architecture_slice=[NodeRef(kind="table", name="booking")],
            acceptance_criteria=[unobservable("Migrations run cleanly from empty.")],
        )
        registry = ProviderRegistry.scripted(["THIS SHOULD NEVER BE ASKED"])

        critique = await critique_package(
            package, Evidence(console=classify_console([])), registry=registry
        )

        assert critique.passed
        assert registry.get("anthropic").calls == []
        assert critique.unjudged  # but it is on the record


SHELL_CODE = """FILE: app/layout.tsx
```tsx
import "./globals.css";
import { SiteHeader } from '@/components/site-header';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body data-scio-id="app-shell" data-scio-package="pkg_foundation">
        <SiteHeader />
        <main data-scio-id="app-main" data-scio-package="pkg_foundation">{children}</main>
      </body>
    </html>
  );
}
```

FILE: components/site-header.tsx
```tsx
export function SiteHeader() {
  return (
    <header data-scio-id="site-header" data-scio-package="pkg_foundation">
      <a data-scio-id="site-header-home-link" data-scio-package="pkg_foundation" href="/">
        The Guest Table
      </a>
    </header>
  );
}
```

FILE: lib/supabase.ts
```ts
import { createClient } from '@supabase/supabase-js';

export const getClient = () =>
  createClient(process.env.NEXT_PUBLIC_SUPABASE_URL!, process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!);
```

FILE: app/page.tsx
```tsx
export default function HomePage() {
  return (
    <section data-scio-id="home-screen" data-scio-package="pkg_foundation">
      <h1 data-scio-id="home-heading" data-scio-package="pkg_foundation">Book your table</h1>
    </section>
  );
}
```
"""


class LikeTheRealCritic(ModelProvider):
    """Answers the way Claude Sonnet 5 actually answered on the first real run:
    per criterion, and "not met" for anything the evidence cannot show.

    That behaviour is correct — it is what the critique system prompt asks for.
    The point of the fix is that such criteria never reach it.
    """

    vendor = Vendor.anthropic
    UNSHOWABLE = ("test runner", "Secrets are read", "Secure defaults", "migrations run")

    def __init__(self) -> None:
        self.prompts: list[str] = []

    async def complete(self, model, messages, **kwargs) -> Completion:
        prompt = messages[-1].content
        self.prompts.append(prompt)
        criteria = [
            line[2:].strip()
            for line in prompt.splitlines()
            if line.startswith("- ") and "Acceptance criteria" not in line
        ]
        verdicts = [
            {
                "criterion": c,
                "met": not any(u in c for u in self.UNSHOWABLE),
                "why": "no evidence of this was provided"
                if any(u in c for u in self.UNSHOWABLE)
                else "visible in the rendered page",
            }
            for c in criteria
        ]
        unmet = [v for v in verdicts if not v["met"]]
        body = json.dumps(
            {
                "verdict": "fail" if unmet else "pass",
                "criteria": verdicts,
                "problems": [f"No evidence: {v['criterion']}" for v in unmet],
            }
        )
        return Completion(text=body, model=model, vendor=Vendor.anthropic, output_tokens=200)


async def build_the_shell(package: BuildPackage, tmp_path: Path, critic: LikeTheRealCritic):
    return await build_package(
        package,
        "## Goal\nThe app shell.\n",
        tmp_path,
        # Every vendor answers from the same stand-in: the review task's matrix
        # ranking is not what this test is about.
        registry=ProviderRegistry(providers=dict.fromkeys(Vendor, critic)),
        preview=ScriptedPreview([clean()]),
        options=BuildOptions(
            max_attempts=1,
            codegen_passes=1,
            critique_passes=1,
            persist=False,
            package_files={FOUNDATION_ID: planned_files(package)},
        ),
    )


class TestTheRealRunFailureIsGone:
    """The whole point of B054, end to end: the same critic, the same code."""

    async def test_the_old_contract_reproduces_the_failure(self, tmp_path):
        package = foundation_of(booking_architecture())
        # The criteria exactly as they were when the real build failed.
        package.acceptance_criteria = [
            coerce("The project builds and starts with no errors."),
            coerce("The test runner executes and passes on an empty suite."),
            coerce("Secrets are read from environment variables only."),
            coerce("Secure defaults from the playbook are configured (headers)."),
        ]
        critic = LikeTheRealCritic()

        result = await build_the_shell(package, tmp_path, ScriptedShell(critic))

        assert result.status is PackageStatus.needs_look
        assert any("No evidence" in r.what for r in result.remainders)

    async def test_the_shipped_contract_passes_the_same_shell(self, tmp_path):
        package = foundation_of(booking_architecture())
        critic = LikeTheRealCritic()

        result = await build_the_shell(package, tmp_path, ScriptedShell(critic))

        assert result.status is PackageStatus.passed, [r.what for r in result.remainders]
        assert result.checks_passed == result.checks_total == 4
        # It was judged — on the things the evidence can actually settle.
        assert critic.prompts and "renders" in critic.prompts[-1]
        # And what nobody could check is still on the record, not swallowed.
        assert any("Not verified" in r.what for r in result.remainders)


class ScriptedShell(ModelProvider):
    """Writes the shell on the codegen call, then defers to the critic."""

    vendor = Vendor.anthropic

    def __init__(self, critic: LikeTheRealCritic) -> None:
        self.critic = critic
        self.calls = 0

    @property
    def prompts(self) -> list[str]:
        return self.critic.prompts

    async def complete(self, model, messages, **kwargs) -> Completion:
        self.calls += 1
        if self.calls == 1:
            return Completion(
                text=SHELL_CODE, model=model, vendor=Vendor.anthropic, output_tokens=800
            )
        return await self.critic.complete(model, messages, **kwargs)


class TestCoverageIsValidatedBeforeGeneration:
    """A criterion the file plan cannot produce is a contract bug, and it costs a
    relay run and a sandbox to find during a build. It is caught here instead."""

    @pytest.mark.asyncio
    async def test_the_shipped_plan_has_no_unproducible_criteria(self):
        arch = booking_architecture()
        result = await run_layer_c(arch, registry=ProviderRegistry.fake(), use_judgment=False)
        offenders = [
            v for v in result.validation.violations if v.rule == "criterion_producible"
        ]
        assert offenders == []

    def test_a_criterion_no_file_would_produce_is_an_error(self):
        arch = booking_architecture()
        packages = decompose(arch)
        foundation = next(p for p in packages if p.id == FOUNDATION_ID)
        foundation.acceptance_criteria.append(
            renders("The billing dashboard totals last month.", "app/billing/")
        )

        from scio_engine.layerc.decompose import topological_order
        from scio_engine.layerc.plan import BuildPlan

        plan = BuildPlan(packages=packages, order=topological_order(packages))
        violations = [
            v for v in validate_plan(plan, arch).violations if v.rule == "criterion_producible"
        ]

        assert violations, "an unproducible criterion must be caught before generation"
        assert "billing dashboard" in violations[0].message
        assert violations[0].severity == "error"

    def test_an_unobservable_criterion_warns_but_never_fails_the_build(self):
        arch = booking_architecture()
        packages = decompose(arch)

        from scio_engine.layerc.decompose import topological_order
        from scio_engine.layerc.plan import BuildPlan

        plan = BuildPlan(packages=packages, order=topological_order(packages))
        validation = validate_plan(plan, arch)
        warnings = [v for v in validation.violations if v.rule == "criterion_observable"]

        assert warnings, "the shipped plan does carry criteria nobody can observe"
        assert all(v.severity == "warning" for v in warnings)
        assert validation.valid

    def test_coverage_reports_both_halves_of_the_contract(self):
        criteria = [
            renders("The header renders.", "app/layout.tsx"),
            renders("The billing page totals.", "app/billing/"),
            unobservable("Headers are configured."),
        ]
        report = cover(criteria, ["app/layout.tsx"])

        assert [c.judgeable for c in report] == [True, False, False]
        assert "file plan" in report[1].reason
        assert report[2].observed_by is Observability.unsupported


# --------------------------------------------------------------------------
# 2. Invented cross-package imports
# --------------------------------------------------------------------------

REAL_RUN_SUPABASE = """import { createClient } from '@supabase/supabase-js';
import type { Database } from '@/types/supabase';
import { env } from '@/lib/env';

export const client = createClient(env.url(), env.key());
"""

PLAN_FILES = {
    "pkg_foundation": ["app/layout.tsx", "components/site-header.tsx", "lib/supabase.ts"],
    "pkg_schema": ["supabase/migrations/0001_init.sql", "types/database.ts"],
    "pkg_feature_booking": ["components/booking-form.tsx", "lib/db/booking.ts"],
}


def foundation_package() -> BuildPackage:
    return BuildPackage(
        id="pkg_foundation",
        kind=PackageKind.foundation,
        goal="The app shell.",
        architecture_slice=[NodeRef(kind="security", name="security_posture")],
        dependencies=[],
        acceptance_criteria=[renders("The shell renders.", "app/layout.tsx")],
    )


class TestImportBoundary:
    def test_the_exact_imports_the_real_run_invented_are_caught(self):
        findings = validate_package(
            foundation_package(),
            {"lib/supabase.ts": REAL_RUN_SUPABASE},
            package_files=PLAN_FILES,
        ).findings
        out_of_bounds = [f for f in findings if f.agent is Agent.import_boundary]

        assert len(out_of_bounds) == 2
        messages = " ".join(f.message for f in out_of_bounds)
        assert "@/lib/env" in messages and "@/types/supabase" in messages
        assert "no package in the build plan produces that file" in messages

    def test_it_names_the_package_when_the_file_belongs_to_one(self):
        """Reaching into a real package you don't depend on is a different
        mistake from importing a file that does not exist — say which."""
        finding = validate_package(
            foundation_package(),
            {"lib/supabase.ts": "import { booking } from '@/lib/db/booking';\n"},
            package_files=PLAN_FILES,
        ).errors[0]

        assert "pkg_feature_booking" in finding.message
        assert "not one of this package's dependencies" in finding.message

    def test_an_in_bounds_build_is_untouched(self):
        package = foundation_package()
        package.dependencies = ["pkg_schema"]
        code = (
            "import { createClient } from '@supabase/supabase-js';\n"
            "import type { Database } from '@/types/database';\n"
            "import { SiteHeader } from './site-header';\n"
            "import '@/app/globals.css';\n"
        )
        findings = validate_package(
            package, {"components/site-header.tsx": code}, package_files=PLAN_FILES
        ).findings

        assert [f for f in findings if f.agent is Agent.import_boundary] == []

    def test_relative_imports_that_climb_out_are_still_resolved(self):
        findings = validate_package(
            foundation_package(),
            {"app/layout.tsx": "import { env } from '../lib/env';\n"},
            package_files=PLAN_FILES,
        ).errors

        assert any("../lib/env" in f.message for f in findings)

    def test_the_boundary_is_fed_back_as_a_fix_instruction(self):
        report = validate_package(
            foundation_package(),
            {"lib/supabase.ts": REAL_RUN_SUPABASE},
            package_files=PLAN_FILES,
        )
        assert any("[import_boundary]" in line for line in report.instructions())


OUT_OF_BOUNDS_CODE = """FILE: app/booking/page.tsx
```tsx
import { env } from '@/lib/env';

export default function BookingPage() {
  return (
    <main data-scio-id="booking-page" data-scio-package="pkg_feature_booking">
      <BookingForm />
    </main>
  );
}
```

FILE: components/booking-form.tsx
```tsx
export function BookingForm() {
  return (
    <form data-scio-id="booking-form" data-scio-package="pkg_feature_booking">
      <button data-scio-id="booking-submit" data-scio-package="pkg_feature_booking">Book</button>
    </form>
  );
}
```

FILE: lib/db/booking.ts
```ts
export async function create_booking() { return { id: "1" }; }
```

FILE: tests/booking.test.ts
```ts
test("create_booking", () => { expect(true).toBe(true); });
```
"""

IN_BOUNDS_CODE = OUT_OF_BOUNDS_CODE.replace("import { env } from '@/lib/env';\n\n", "")

CRITIQUE_PASS = '{"verdict": "pass", "criteria": [], "problems": []}'


def booking_package() -> BuildPackage:
    return BuildPackage(
        id="pkg_feature_booking",
        kind=PackageKind.feature,
        goal="A guest can book a table.",
        architecture_slice=[
            NodeRef(kind="operation", name="create_booking"),
            NodeRef(kind="screen", name="/booking"),
        ],
        dependencies=["pkg_foundation"],
        acceptance_criteria=[renders("A guest can book a table.", "components/")],
    )


def clean() -> Observation:
    return Observation(screenshot_path=None, console=classify_console([]), title="Book")


class TestImportBoundaryInTheLoop:
    """The guardrail has to reach the build, not just the agent."""

    async def test_an_out_of_bounds_import_is_caught_and_then_fixed(self, tmp_path):
        package = booking_package()
        result = await build_package(
            package,
            "## Goal\nA guest can book a table.\n",
            tmp_path,
            registry=ProviderRegistry.scripted(
                [OUT_OF_BOUNDS_CODE, IN_BOUNDS_CODE, CRITIQUE_PASS], loop_last=True
            ),
            preview=ScriptedPreview([clean()]),
            options=BuildOptions(
                max_attempts=2,
                codegen_passes=1,
                critique_passes=1,
                persist=False,
                package_files={
                    **PLAN_FILES,
                    "pkg_feature_booking": planned_files(package),
                },
            ),
        )

        first = result.attempts[0]
        assert not first.validation_ok
        assert any("import_boundary" in p for p in first.problems)
        assert "@/lib/env" not in (tmp_path / "app/booking/page.tsx").read_text()
        assert result.status is PackageStatus.passed


# --------------------------------------------------------------------------
# 3. data-scio-package coverage
# --------------------------------------------------------------------------

REAL_RUN_PAGE = """export default function HomePage() {
  return (
    <section data-scio-id="home-screen" data-scio-package="pkg_foundation">
      <ol data-scio-id="home-steps" data-scio-package="pkg_foundation">
        <li data-scio-id="home-step-choose">1. Choose a table that&apos;s free.</li>
        <li data-scio-id="home-step-details">2. Add your name and phone number.</li>
      </ol>
    </section>
  );
}
"""


class TestPackageStamping:
    def test_the_real_runs_missing_tags_are_seen(self):
        assert ids_missing_package(REAL_RUN_PAGE) == [
            "home-step-choose",
            "home-step-details",
        ]

    def test_stamping_fills_them_and_leaves_the_rest_alone(self):
        stamped = stamp_package(REAL_RUN_PAGE, "pkg_foundation")

        assert ids_missing_package(stamped) == []
        assert stamped.count('data-scio-package="pkg_foundation"') == 4
        assert "1. Choose a table that&apos;s free." in stamped

    def test_an_element_that_names_a_package_is_never_rewritten(self):
        source = '<b data-scio-id="x" data-scio-package="pkg_other">hi</b>'
        assert stamp_package(source, "pkg_foundation") == source

    def test_loop_rendered_ids_are_stamped_too(self):
        source = "<li data-scio-id={`booking-row-${b.id}`}>{b.name}</li>"
        stamped = stamp_package(source, "pkg_feature_booking")

        assert 'data-scio-package="pkg_feature_booking"' in stamped
        assert ids_missing_package(stamped) == []

    def test_only_markup_files_are_touched(self):
        files = {"lib/db.ts": 'const q = \'data-scio-id="not-markup"\';\n'}
        assert stamp_files(files, "pkg_x") == files


class TestVerifierRequiresBothAttributes:
    def _manifest(self, tmp_path: Path, source: str) -> Manifest:
        (tmp_path / "app").mkdir(exist_ok=True)
        (tmp_path / "app/page.tsx").write_text(source)
        return build_manifest(tmp_path, {"pkg_foundation": ["app/page.tsx"]})

    def test_an_element_without_a_package_fails_the_verifier(self, tmp_path):
        manifest = self._manifest(tmp_path, REAL_RUN_PAGE)
        report = verify_instrumentation(tmp_path, manifest)

        assert not report.valid
        broken = [i for i in report.errors if i.rule == "element_has_package_attribute"]
        assert {i.subject for i in broken} == {"home-step-choose", "home-step-details"}
        assert "resolve to whichever package was written above it" in broken[0].message

    def test_the_stamped_source_passes(self, tmp_path):
        manifest = self._manifest(tmp_path, stamp_package(REAL_RUN_PAGE, "pkg_foundation"))
        report = verify_instrumentation(tmp_path, manifest)

        assert report.valid, [i.message for i in report.errors]
        assert report.element_count == 4

    async def test_a_real_build_is_fully_resolvable_without_the_model_helping(self, tmp_path):
        """The end of the chain: the model writes ids only, and every element in
        the built app still resolves to exactly one package."""
        unmarked = OUT_OF_BOUNDS_CODE.replace(' data-scio-package="pkg_feature_booking"', "")
        unmarked = unmarked.replace("import { env } from '@/lib/env';\n\n", "")
        package = booking_package()

        result = await build_package(
            package,
            "## Goal\nA guest can book a table.\n",
            tmp_path,
            registry=ProviderRegistry.scripted([unmarked, CRITIQUE_PASS], loop_last=True),
            preview=ScriptedPreview([clean()]),
            options=BuildOptions(
                max_attempts=1,
                codegen_passes=1,
                critique_passes=1,
                persist=False,
                package_files={"pkg_feature_booking": planned_files(package)},
            ),
        )

        assert result.status is PackageStatus.passed
        page = (tmp_path / "app/booking/page.tsx").read_text()
        assert 'data-scio-package="pkg_feature_booking"' in page

        manifest = build_manifest(tmp_path, {"pkg_feature_booking": planned_files(package)})
        assert manifest.elements
        assert all(loc.package == "pkg_feature_booking" for loc in manifest.elements.values())
        assert verify_instrumentation(tmp_path, manifest).valid


# --------------------------------------------------------------------------
# 4. What the SECOND real run surfaced
# --------------------------------------------------------------------------


class TestServerActionsHaveAHome:
    """The second run's one remaining failure.

    `components/booking-form.tsx` did:

        import { createBookingAction } from '@/app/actions/booking';

    which is the App Router idiom for a form that mutates data — and a file the
    plan gave it nowhere to write. The import boundary caught it (correctly) and
    the app broke on a dangling module. The model was not being careless; the
    contract was incomplete.
    """

    def test_a_feature_package_owns_its_server_actions_and_validation(self):
        """Both files the second run invented now have a legal home."""
        planned = planned_files(booking_package())
        assert "app/actions/booking.ts" in planned
        assert "lib/validation/booking.ts" in planned

    def test_the_import_that_broke_the_second_run_is_now_in_bounds(self):
        package = booking_package()
        files = {
            "components/booking-form.tsx": (
                "import { createBookingAction } from '@/app/actions/booking';\n"
                "export function BookingForm() { return null; }\n"
            ),
            "lib/db/booking.ts": (
                "import { bookingSchema } from '@/lib/validation/booking';\n"
                "export const create = (i: unknown) => bookingSchema;\n"
            ),
        }
        findings = validate_package(
            package,
            files,
            package_files={package.id: planned_files(package)},
        ).findings

        assert [f for f in findings if f.agent is Agent.import_boundary] == []

    def test_another_packages_actions_are_still_out_of_bounds(self):
        """Owning your own actions is not permission to reach into someone else's."""
        package = booking_package()
        findings = validate_package(
            package,
            {"components/booking-form.tsx": "import { x } from '@/app/actions/payment';\n"},
            package_files={
                package.id: planned_files(package),
                "pkg_feature_payment": ["app/actions/payment.ts"],
            },
        ).errors

        assert any("pkg_feature_payment" in f.message for f in findings)

    def test_the_actions_file_is_not_claimed_by_two_packages(self):
        """Every feature gets its own entity-named file — the manifest's package
        map cannot have two owners for one path."""
        booking = planned_files(booking_package())
        menu_package = BuildPackage(
            id="pkg_feature_menu",
            kind=PackageKind.feature,
            goal="Read the menu.",
            architecture_slice=[NodeRef(kind="operation", name="list_menu")],
        )
        assert set(booking) & set(planned_files(menu_package)) == set()
