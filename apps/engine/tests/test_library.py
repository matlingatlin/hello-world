"""The component library, first slice: match -> fetch -> adapt -> assemble.

What has to be true for the library to be worth having:

- a feature the catalog covers is ASSEMBLED — no relay call for that package at
  all, which is the whole economic argument;
- what lands is adapted to THIS project (its entity name, its tokens) and is
  fully instrumented, so the design window works on assembled parts exactly as
  on generated ones;
- a feature the catalog does not cover still generates, unchanged;
- matching is deterministic and goes through canonical vocabulary, so a user who
  says "reservations" gets the booking blueprint without anyone teaching the
  matcher about restaurants;
- nothing gets INTO the library without clearing the gate.
"""


import pytest

from conftest import make_booking_spec
from scio_engine.builder.file_plan import planned_files
from scio_engine.builder.loop import ScriptedPreview
from scio_engine.builder.orchestrate import AppBuildOptions, stream_build_plan
from scio_engine.builder.result import PackageStatus
from scio_engine.core.console import classify_console
from scio_engine.core.manifest_builder import build_manifest
from scio_engine.core.preview import Observation
from scio_engine.core.stamping import ids_missing_package
from scio_engine.core.verifier import verify_instrumentation
from scio_engine.execution.provider import (
    Completion,
    ModelProvider,
    ProviderRegistry,
    Vendor,
)
from scio_engine.intake.schema import FieldMeta
from scio_engine.layerb.architecture import DesignTokens
from scio_engine.layerb.derive import derive_architecture
from scio_engine.layerc.decompose import build_plan
from scio_engine.layerc.plan import BuildPackage
from scio_engine.layerc.service import run_layer_c
from scio_engine.library.assembler import AssemblyError, assemble_package
from scio_engine.library.catalog import Catalog, default_catalog, load_catalog
from scio_engine.library.entry import ENTITY, CatalogEntry, Layer, Quality
from scio_engine.library.gate import Candidate, review
from scio_engine.library.matcher import Decision, candidates, match_plan

BOOKING_PKG = "pkg_feature_booking"


def booking_architecture(**overrides):
    return derive_architecture(make_booking_spec(**overrides))


def booking_package() -> BuildPackage:
    return next(p for p in build_plan(booking_architecture()).packages if p.id == BOOKING_PKG)


def clean() -> Observation:
    return Observation(screenshot_path=None, console=classify_console([]), title="Book")


# --------------------------------------------------------------------------
# The catalog
# --------------------------------------------------------------------------


class TestCatalog:
    def test_the_seed_catalog_loads_from_the_repo(self):
        catalog = default_catalog()
        assert len(catalog) >= 4
        assert catalog.get("feature-booking") is not None

    def test_the_booking_blueprint_carries_a_full_contract(self):
        entry = default_catalog().get("feature-booking")

        assert entry.layer is Layer.feature
        assert "booking" in entry.provides.canonical_entities()
        assert {"create_booking", "cancel_booking"} <= set(entry.provides.operations)
        assert entry.quality.usable
        assert entry.element_ids
        assert entry.npm_dependencies

    def test_ui_entries_seed_the_other_layer(self):
        ui = default_catalog().by_layer(Layer.ui)
        assert {e.id for e in ui} == {"ui-button", "ui-field", "ui-empty-state"}
        assert all(e.offerable for e in ui)

    def test_an_unvetted_entry_is_never_offered(self):
        """An entry nobody reviewed carries authority it has not earned."""
        entry = CatalogEntry(
            id="sketchy",
            name="Sketchy",
            layer=Layer.feature,
            description="untested",
            files={"a.tsx": "x"},
            quality=Quality(tested=False, security_reviewed=False),
        )
        assert entry.offerable is False
        assert Catalog([entry]).offerable() == []

    def test_an_operator_can_point_at_another_catalog(self, tmp_path, monkeypatch):
        monkeypatch.setenv("SCIO_CATALOG_DIR", str(tmp_path))
        assert len(load_catalog(tmp_path)) == 0


# --------------------------------------------------------------------------
# Adaptation
# --------------------------------------------------------------------------


class TestAdaptation:
    def test_the_entry_becomes_this_projects_files(self):
        entry = default_catalog().get("feature-booking")
        files = entry.adapt("booking", {"accent": "#ff0000", "md": "12px"})

        assert "components/booking-form.tsx" in files
        assert ENTITY not in "".join(files)
        assert ENTITY not in "".join(files.keys())

    def test_tokens_are_applied_from_the_project(self):
        entry = default_catalog().get("feature-booking")
        files = entry.adapt("booking", {"accent": "#ff0000", "md": "12px"})
        form = files["components/booking-form.tsx"]

        assert "#ff0000" in form
        assert "12px" in form

    def test_a_missing_token_falls_back_instead_of_shipping_a_placeholder(self):
        """Shipping `__TOKEN_ACCENT__` would render the placeholder text."""
        files = default_catalog().get("feature-booking").adapt("booking", {})
        joined = "".join(files.values())

        assert "__TOKEN_" not in joined
        assert "#0f766e" in joined  # the neutral fallback

    def test_the_projects_own_word_reaches_identifiers_and_ids(self):
        files = default_catalog().get("feature-booking").adapt("booking", {})
        actions = files["app/actions/booking.ts"]

        assert "createBookingAction" in actions
        assert 'data-scio-id="booking-form"' in files["components/booking-form.tsx"]

    def test_a_different_entity_name_adapts_the_whole_blueprint(self):
        """The blueprint is not about restaurants — prove it by renaming.

        ("appointment" would be a poor test: the vocabulary treats it as a
        synonym of booking, so it canonicalises straight back.)
        """
        files = default_catalog().get("feature-booking").adapt("delivery", {})

        assert "components/delivery-form.tsx" in files
        assert "createDeliveryAction" in files["app/actions/delivery.ts"]
        assert "deliveries" in files["lib/db/delivery.ts"]  # pluralised table

    def test_a_synonym_canonicalises_before_it_adapts(self):
        files = default_catalog().get("feature-booking").adapt("reservations", {})
        assert "components/booking-form.tsx" in files


# --------------------------------------------------------------------------
# Matching
# --------------------------------------------------------------------------


class TestMatching:
    async def test_the_booking_feature_matches_the_blueprint(self):
        plan = build_plan(booking_architecture())
        report = await match_plan(plan, registry=ProviderRegistry.fake(), use_judgment=False)

        match = report.for_package(BOOKING_PKG)
        assert match.decision is Decision.assemble
        assert match.entry_id == "feature-booking"

    async def test_reservations_finds_it_through_canonical_vocabulary(self):
        """The user said "reservations"; the catalog says "booking"."""
        arch = booking_architecture(entities=FieldMeta(value=["reservations", "tables"]))
        plan = build_plan(arch)
        report = await match_plan(plan, registry=ProviderRegistry.fake(), use_judgment=False)

        assembled = [m for m in report.matches if m.assembles]
        assert [m.entry_id for m in assembled] == ["feature-booking"]
        assert assembled[0].entity == "booking"

    async def test_a_novel_feature_generates(self):
        arch = booking_architecture(
            entities=FieldMeta(value=["invoices"]),
            key_actions=FieldMeta(value=["send an invoice", "void an invoice"]),
        )
        report = await match_plan(
            build_plan(arch), registry=ProviderRegistry.fake(), use_judgment=False
        )

        assert report.assembled == []
        assert all("nothing in the library" in m.reason for m in report.matches)

    async def test_the_shell_and_schema_are_never_assembled_in_this_slice(self):
        report = await match_plan(
            build_plan(booking_architecture()),
            registry=ProviderRegistry.fake(),
            use_judgment=False,
        )
        for package_id in ("pkg_foundation", "pkg_schema", "pkg_auth", "pkg_design_tokens"):
            assert report.for_package(package_id).decision is Decision.generate

    def test_an_entry_that_would_write_the_wrong_files_is_not_a_match(self):
        """The manifest's package→file map must not disagree with the disk."""
        entry = default_catalog().get("feature-booking").model_copy(deep=True)
        entry.files["components/__ENTITY__-extra.tsx"] = "export const Extra = () => null;\n"

        assert candidates(booking_package(), Catalog([entry])) == []

    def test_an_entry_missing_an_operation_is_not_a_match(self):
        """Four of five operations is not a match — the fifth would vanish."""
        entry = default_catalog().get("feature-booking").model_copy(deep=True)
        entry.provides.operations = ["create_booking"]

        assert candidates(booking_package(), Catalog([entry])) == []

    async def test_the_report_says_how_much_came_from_the_library(self):
        report = await match_plan(
            build_plan(booking_architecture()),
            registry=ProviderRegistry.fake(),
            use_judgment=False,
        )
        assert report.describe() == "1 of 5 parts from the library, 4 generated"

    async def test_two_equal_entries_with_no_judgment_generate_rather_than_guess(self):
        twin = default_catalog().get("feature-booking").model_copy(deep=True)
        twin.id = "feature-booking-twin"
        catalog = Catalog([default_catalog().get("feature-booking"), twin])

        report = await match_plan(
            build_plan(booking_architecture()), catalog=catalog, use_judgment=False
        )
        match = report.for_package(BOOKING_PKG)

        assert match.decision is Decision.generate
        assert "none was clearly better" in match.reason
        assert sorted(match.considered) == ["feature-booking", "feature-booking-twin"]

    async def test_a_model_settles_a_genuine_tie(self):
        twin = default_catalog().get("feature-booking").model_copy(deep=True)
        twin.id = "feature-booking-twin"
        catalog = Catalog([default_catalog().get("feature-booking"), twin])
        registry = ProviderRegistry.scripted(["feature-booking-twin"])

        report = await match_plan(
            build_plan(booking_architecture()),
            catalog=catalog,
            registry=registry,
            use_judgment=True,
        )

        assert report.for_package(BOOKING_PKG).entry_id == "feature-booking-twin"


# --------------------------------------------------------------------------
# Assembly
# --------------------------------------------------------------------------


class TestAssembly:
    def test_assembling_writes_the_plans_files_and_nothing_else(self, tmp_path):
        package = booking_package()
        package.source = "assemble"
        package.catalog_entry = "feature-booking"

        result = assemble_package(package, tmp_path, entity="booking")

        assert result.status is PackageStatus.passed
        assert result.files == sorted(planned_files(package))
        assert result.total_cost_usd == 0.0
        assert result.attempts[0].action == "assemble"

    def test_every_assembled_element_carries_both_attributes(self, tmp_path):
        package = booking_package()
        package.catalog_entry = "feature-booking"
        assemble_package(package, tmp_path, entity="booking")

        for path in planned_files(package):
            if path.endswith(".tsx"):
                assert ids_missing_package((tmp_path / path).read_text()) == []

        manifest = build_manifest(tmp_path, {package.id: planned_files(package)})
        report = verify_instrumentation(tmp_path, manifest)
        assert report.valid, [i.message for i in report.errors]
        assert all(loc.package == package.id for loc in manifest.elements.values())

    def test_the_assembled_code_imports_only_what_exists(self, tmp_path):
        """The blueprint carries its own imports — nothing invented, nothing dangling."""
        from scio_engine.builder.validation import Agent, validate_package

        package = booking_package()
        package.catalog_entry = "feature-booking"
        assemble_package(package, tmp_path, entity="booking")

        files = {p: (tmp_path / p).read_text() for p in planned_files(package)}
        plan_files = {
            package.id: planned_files(package),
            "pkg_foundation": ["lib/supabase.ts", "app/layout.tsx"],
            "pkg_schema": ["types/database.ts"],
            "pkg_design_tokens": ["app/globals.css", "tailwind.config.ts"],
        }
        findings = validate_package(package, files, package_files=plan_files).findings

        assert [f for f in findings if f.agent is Agent.import_boundary] == []

    def test_the_project_tokens_reach_the_assembled_files(self, tmp_path):
        package = booking_package()
        package.catalog_entry = "feature-booking"
        tokens = DesignTokens(palette={"accent": "#123456"}, radius={"md": "14px"})

        assemble_package(package, tmp_path, entity="booking", tokens=tokens)
        form = (tmp_path / "components/booking-form.tsx").read_text()

        assert "#123456" in form and "14px" in form

    def test_an_unknown_entry_fails_loudly(self, tmp_path):
        package = booking_package()
        package.catalog_entry = "does-not-exist"

        with pytest.raises(AssemblyError, match="not in the catalog"):
            assemble_package(package, tmp_path, entity="booking")

    def test_an_entry_that_drifted_from_the_file_plan_fails_loudly(self, tmp_path):
        entry = default_catalog().get("feature-booking").model_copy(deep=True)
        del entry.files["tests/__ENTITY__.test.ts"]
        package = booking_package()

        with pytest.raises(AssemblyError, match="miss"):
            assemble_package(package, tmp_path, entity="booking", entry=entry)


# --------------------------------------------------------------------------
# The whole build
# --------------------------------------------------------------------------

SHELL_CODE = """FILE: app/layout.tsx
```tsx
import "./globals.css";
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body data-scio-id="app-shell" data-scio-package="pkg_foundation">{children}</body>
    </html>
  );
}
```

FILE: components/site-header.tsx
```tsx
export function SiteHeader() {
  return <header data-scio-id="site-header" data-scio-package="pkg_foundation">Scio</header>;
}
```

FILE: lib/supabase.ts
```ts
import { createClient } from '@supabase/supabase-js';
export const getSupabaseClient = () => createClient(process.env.URL!, process.env.KEY!);
```

FILE: app/page.tsx
```tsx
export default function HomePage() {
  return <main data-scio-id="home" data-scio-package="pkg_foundation">Book a table</main>;
}
```
"""

ANY_CODE = """FILE: {path}
```ts
export const ready = true;
```
"""

CRITIQUE_PASS = '{"verdict": "pass", "criteria": [], "problems": []}'


PACKAGE_CODE = {
    "pkg_foundation": SHELL_CODE,
    "pkg_design_tokens": """FILE: app/globals.css
```css
@tailwind base;
:root { --ink: #101319; }
```

FILE: tailwind.config.ts
```ts
import type { Config } from "tailwindcss";
const config: Config = { content: ["./app/**/*.tsx"], theme: {}, plugins: [] };
export default config;
```
""",
    "pkg_schema": """FILE: supabase/migrations/0001_init.sql
```sql
create table bookings (id uuid primary key);
alter table bookings enable row level security;
```

FILE: types/database.ts
```ts
export type Booking = { id: string };
```
""",
    "pkg_auth": """FILE: lib/auth.ts
```ts
export const identify = (name: string, phone: string) => ({ name, phone });
```

FILE: tests/auth.test.ts
```ts
it("identifies a guest", () => expect(true).toBe(true));
```
""",
}


def _package_under_build(prompt: str) -> str:
    """The package a contract prompt is FOR — its header, not its dependencies."""
    for line in prompt.splitlines():
        if line.startswith("# Build package:"):
            return line.split(":", 1)[1].strip().split(" ")[0]
    return ""


class PerPackageProvider(ModelProvider):
    """Answers with the right code for whichever package is being generated.

    The point is what it does NOT get asked: if the assembled package ever
    reaches a model, `asked_about` will say so.
    """

    vendor = Vendor.anthropic

    def __init__(self) -> None:
        self.prompts: list[str] = []

    async def complete(self, model, messages, **kwargs) -> Completion:
        prompt = messages[-1].content
        self.prompts.append(prompt)
        code = PACKAGE_CODE.get(_package_under_build(prompt))
        return Completion(
            text=code if code else CRITIQUE_PASS, model=model, vendor=Vendor.anthropic
        )

    def asked_about(self, package_id: str) -> bool:
        """Was this package the SUBJECT of a call? Every contract names its
        dependencies, so a bare substring search would answer yes for all of them."""
        return any(_package_under_build(p) == package_id for p in self.prompts)


def registry_for(provider: ModelProvider) -> ProviderRegistry:
    return ProviderRegistry(providers=dict.fromkeys(Vendor, provider))


class TestTheWholeBuild:
    async def test_the_blueprint_is_assembled_with_no_model_call_for_it(self, tmp_path):
        """The economic claim, tested: the assembled package costs nothing."""
        arch = booking_architecture()
        result = await run_layer_c(arch, registry=ProviderRegistry.fake(), use_judgment=False)
        plan = result.plan

        assert plan.get(BOOKING_PKG).assembled

        provider = PerPackageProvider()
        app_result = None
        async for event, payload in stream_build_plan(
            plan,
            tmp_path,
            contracts=result.prompts,
            registry=registry_for(provider),
            preview=ScriptedPreview([clean()]),
            options=AppBuildOptions(persist=False, tokens=arch.design_tokens),
        ):
            if event == "result":
                app_result = payload

        booking = app_result.get(BOOKING_PKG)
        assert booking.status is PackageStatus.passed
        assert booking.total_cost_usd == 0.0
        assert booking.attempts[0].action == "assemble"
        # THE assertion: no model was ever asked anything about this package.
        assert not provider.asked_about(BOOKING_PKG)
        # ...while the packages the library does not cover DID go to a model.
        assert provider.asked_about("pkg_foundation")

    async def test_the_assembled_part_lands_beside_the_generated_ones(self, tmp_path):
        arch = booking_architecture()
        result = await run_layer_c(arch, registry=ProviderRegistry.fake(), use_judgment=False)

        app_result = None
        async for event, payload in stream_build_plan(
            result.plan,
            tmp_path,
            contracts=result.prompts,
            registry=registry_for(PerPackageProvider()),
            preview=ScriptedPreview([clean()]),
            options=AppBuildOptions(persist=False, tokens=arch.design_tokens),
        ):
            if event == "result":
                app_result = payload

        assert BOOKING_PKG in app_result.working
        assert (tmp_path / "components/booking-form.tsx").exists()
        assert (tmp_path / "app/actions/booking.ts").exists()
        # One app: the assembled part and the generated shell share a manifest.
        assert app_result.element_count > 0

    async def test_a_novel_feature_still_goes_through_the_builder(self, tmp_path):
        arch = booking_architecture(
            entities=FieldMeta(value=["invoices"]),
            key_actions=FieldMeta(value=["send an invoice"]),
        )
        result = await run_layer_c(arch, registry=ProviderRegistry.fake(), use_judgment=False)

        assert not any(p.assembled for p in result.plan.packages)
        assert result.library.assembled == []


# --------------------------------------------------------------------------
# The contribute-back gate
# --------------------------------------------------------------------------


def clean_candidate() -> Candidate:
    entry = CatalogEntry(
        id="feature-checkin",
        name="Check-in",
        layer=Layer.feature,
        description="A guest checks in.",
        files={
            "components/__ENTITY__-form.tsx": (
                '<form data-scio-id="__ENTITY__-form">'
                "<button data-scio-id=\"__ENTITY__-submit\">Go</button></form>"
            ),
            "tests/__ENTITY__.test.ts": 'it("works", () => expect(true).toBe(true));',
        },
        element_ids=["__ENTITY__-form", "__ENTITY__-submit"],
        quality=Quality(
            tested=True, security_reviewed=True, accessibility_score=95, lighthouse_score=95
        ),
    )
    return Candidate(entry=entry, project_terms=["Bella Vista", "restaurant"])


class TestContributeBackGate:
    def test_a_clean_generalized_tested_candidate_is_accepted(self):
        result = review(clean_candidate())
        assert result.accepted, result.explain()

    def test_a_candidate_with_no_tests_is_rejected(self):
        candidate = clean_candidate()
        del candidate.entry.files["tests/__ENTITY__.test.ts"]

        result = review(candidate)
        assert not result.accepted
        assert any(f.rule == "tested" for f in result.findings)

    def test_an_unreviewed_candidate_is_rejected(self):
        candidate = clean_candidate()
        candidate.entry.quality.security_reviewed = False

        assert any(f.rule == "security_reviewed" for f in review(candidate).findings)

    def test_low_scores_are_rejected(self):
        candidate = clean_candidate()
        candidate.entry.quality.accessibility_score = 40

        assert any(f.rule == "scores" for f in review(candidate).findings)

    def test_a_candidate_carrying_the_projects_own_words_is_rejected(self):
        """The leak that matters most: one customer's copy in everyone's app."""
        candidate = clean_candidate()
        candidate.entry.files["components/__ENTITY__-form.tsx"] += (
            "\n// Welcome to Bella Vista\n"
        )

        result = review(candidate)
        assert not result.accepted
        assert any("Bella Vista" in f.message for f in result.findings)

    def test_a_candidate_with_a_hardcoded_url_or_key_is_rejected(self):
        candidate = clean_candidate()
        candidate.entry.files["components/__ENTITY__-form.tsx"] += (
            "\nconst api = 'https://bella-vista.se/api';\n"
        )

        assert any("external URL" in f.message for f in review(candidate).findings)

    def test_a_real_api_key_is_caught_whatever_shape_it_comes_in(self):
        """The rule used to stop at the first hyphen, so a real `sk-ant-api03-…`
        key — the one this product is actually handed — sailed through the one
        check meant to stop exactly that."""
        for key in (
            "sk-ant-api03-AbCdEfGhIjKlMnOpQrStUvWxYz0123456789-AbCdEfGh",
            "sk-proj-AbCdEfGhIjKlMnOpQrStUvWx",
            "AIzaSyAbCdEfGhIjKlMnOpQrStUvWxYz0123456",
        ):
            candidate = clean_candidate()
            candidate.entry.files["components/__ENTITY__-form.tsx"] += f"\nconst k = '{key}';\n"

            findings = review(candidate).findings
            assert any("API key" in f.message for f in findings), key

    def test_names_reserved_for_examples_are_not_leaks(self):
        """RFC 2606 / RFC 6761 reserve these precisely so a test can use them.

        This is why `pkg_auth` was refused in the first real run despite passing
        all five build gates: a model writes `guest@example.com` in a test, and a
        gate that reads that as a customer's address refuses everything real.
        """
        candidate = clean_candidate()
        candidate.entry.files["tests/__ENTITY__.test.ts"] += (
            "\nconst who = 'guest@example.com';\n"
            "const callback = 'https://app.example.com/auth/callback';\n"
            "const local = 'http://localhost:3000/';\n"
        )

        findings = review(candidate).findings
        assert not any(f.rule == "no_leakage" for f in findings), [f.message for f in findings]

    def test_an_ungeneralized_feature_is_rejected(self):
        candidate = clean_candidate()
        candidate.entry.files = {
            "components/booking-form.tsx": '<form data-scio-id="booking-form"></form>',
            "tests/booking.test.ts": 'it("works", () => {});',
        }

        result = review(candidate)
        assert any(f.rule == "generalized" for f in result.findings)

    def test_ui_without_instrumentation_is_rejected(self):
        candidate = clean_candidate()
        candidate.entry.element_ids = []

        assert any(f.rule == "instrumented" for f in review(candidate).findings)

    def test_the_shipped_seed_entries_would_all_pass_their_own_gate(self):
        """The library must meet the bar it sets."""
        for entry in default_catalog().entries:
            if entry.layer is not Layer.feature:
                continue
            result = review(Candidate(entry=entry, project_terms=[]))
            assert result.accepted, f"{entry.id}: {result.explain()}"

    def test_the_rejection_explains_itself(self):
        candidate = clean_candidate()
        candidate.entry.quality.tested = False

        explanation = review(candidate).explain()
        assert "Not added" in explanation and "[tested]" in explanation
