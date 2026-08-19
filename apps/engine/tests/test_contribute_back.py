"""B061: the library grows from real builds — both directions.

The acceptance story, as a test, because prose about organic growth is worth
nothing:

1. **"a booking page"** — nothing in the library covers it, so it is generated,
   passes every build gate, is generalized, re-verified, and lands as
   `booking.1.1`, provisional.
2. **"a booking page and a login page"** — the matcher finds `booking.1.x` by
   category and contract and ASSEMBLES it, with no model involved; login has no
   match, is generated, and lands as `auth.1.1`.
3. The assembled booking package is **skipped** by contribute, because it
   carries the entry id it came from. Without that, the library would contribute
   its own entries back to itself forever.
4. A later build that produces an objectively better booking **bumps
   `booking.1.2`**, replacing the version it improves — not a second entry.

Everything that decides anything here is deterministic. The relay is only ever
asked to rewrite copy, and these tests run with no model at all — which is the
point: the mechanism has to work on the free path too.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from conftest import make_booking_spec
from scio_engine.builder.file_plan import planned_files
from scio_engine.builder.result import PackageBuildResult, PackageStatus
from scio_engine.execution.provider import ProviderRegistry
from scio_engine.intake.schema import FieldMeta
from scio_engine.layerb.derive import derive_architecture
from scio_engine.layerc.decompose import build_plan
from scio_engine.layerc.plan import BuildPackage
from scio_engine.library.categories import default_registry
from scio_engine.library.contribute import contribute_build, eligible
from scio_engine.library.entry import CatalogEntry, Layer, Quality
from scio_engine.library.identity import Contract, EntryId, Status
from scio_engine.library.matcher import Decision, match_plan, package_contract
from scio_engine.library.store import FileCatalogStore

pytestmark = pytest.mark.anyio

BOOKING_PKG = "pkg_feature_booking"
AUTH_PKG = "pkg_auth"


def plan_for(**overrides):
    """A plan with an auth package as well as the booking feature."""
    spec = make_booking_spec(sign_in=FieldMeta(value="an email link"), **overrides)
    architecture = derive_architecture(spec)
    return build_plan(architecture), architecture


def source_for(package: BuildPackage) -> dict[str, str]:
    """Plausible generated output: instrumented, tested, no second entity in it."""
    files: dict[str, str] = {}
    for relative in planned_files(package):
        slug = relative.replace("/", "-").replace(".", "-")
        entity = "booking" if "booking" in package.id else "session"
        if relative.endswith(".tsx"):
            files[relative] = (
                f"export function View_{slug.replace('-', '_')}() {{\n"
                f'  return (\n    <section data-scio-id="{entity}-{slug}" '
                f'data-scio-package="{package.id}">\n'
                f'      <h2 data-scio-id="{entity}-{slug}-heading" '
                f'data-scio-package="{package.id}">Bookings</h2>\n'
                f"    </section>\n  );\n}}\n"
            )
        elif "test" in relative:
            files[relative] = (
                'import { describe, expect, it } from "vitest";\n'
                f'describe("{entity}", () => {{ it("works", () => {{ expect(1).toBe(1); }}); }});\n'
            )
        elif relative.endswith(".sql"):
            files[relative] = f"create table {entity} (id uuid primary key);\n"
        else:
            files[relative] = f'export const {entity}_{slug.replace("-", "_")} = {{}};\n'
    return files


def write(app_dir: Path, files: dict[str, str]) -> None:
    for relative, body in files.items():
        target = app_dir / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body)


def passed(package: BuildPackage, files: dict[str, str], **overrides) -> PackageBuildResult:
    """What a package that cleared every build gate looks like."""
    base = dict(
        package_id=package.id,
        status=PackageStatus.passed,
        files=sorted(files),
        checks_passed=5,
        checks_total=5,
    )
    base.update(overrides)
    return PackageBuildResult(**base)


def empty_store() -> FileCatalogStore:
    """A library with nothing in it — so what appears got there by growing."""
    return FileCatalogStore(seed_dir=None)


async def build_and_contribute(
    store: FileCatalogStore,
    app_dir: Path,
    *,
    package_ids: tuple[str, ...] = (BOOKING_PKG,),
    project_id: str = "p1",
    **result_overrides,
):
    plan, architecture = plan_for()
    packages = [p for p in plan.packages if p.id in package_ids]
    results = []
    for package in packages:
        files = source_for(package)
        write(app_dir, files)
        results.append(passed(package, files, **result_overrides))
    return await contribute_build(
        packages,
        results,
        app_dir,
        registry=ProviderRegistry.fake(),
        store=store,
        architecture=architecture,
        project_id=project_id,
    )


# --------------------------------------------------------------------------
# 1. Prompt one: nothing to reuse, so it is learned
# --------------------------------------------------------------------------


class TestTheFirstBuildTeachesTheLibrary:
    async def test_a_booking_package_becomes_booking_1_1(self, tmp_path: Path):
        store = empty_store()

        report = await build_and_contribute(store, tmp_path)

        assert [o.action for o in report.outcomes] == ["added"]
        assert report.added == ["booking.1.1"]
        entry = store.catalog().get("booking.1.1")
        assert entry is not None
        assert entry.category == "booking"
        assert entry.layer is Layer.feature

    async def test_what_it_learned_is_provisional_and_says_where_it_came_from(
        self, tmp_path: Path
    ):
        """A machine's extraction never silently equals something a person wrote."""
        store = empty_store()
        await build_and_contribute(store, tmp_path, project_id="bistro-nord")

        entry = store.catalog().get("booking.1.1")
        assert entry.status is Status.provisional
        assert entry.source_project == "bistro-nord"
        assert entry.provenance == "contributed:bistro-nord"
        # Provisional is not "unusable": it cleared every gate a seed clears.
        assert entry.offerable

    async def test_the_project_s_own_word_is_gone(self, tmp_path: Path):
        store = empty_store()
        await build_and_contribute(store, tmp_path)

        entry = store.catalog().get("booking.1.1")
        blob = "\n".join([*entry.files, *entry.files.values()])
        assert "booking" not in blob.lower()
        assert "__ENTITY__" in blob
        # …and the package tag, which belongs to one app, went with it.
        assert "data-scio-package" not in blob
        # The ids did NOT: they are how any project's user points at this code.
        assert "data-scio-id" in blob

    async def test_the_id_is_assigned_by_the_store_not_by_the_candidate(
        self, tmp_path: Path
    ):
        store = empty_store()
        store.put(
            CatalogEntry(
                id="booking.7.1",
                name="something else in booking",
                layer=Layer.feature,
                description="x",
                category="booking",
                contract=Contract(operations=["unrelated"], files=["a.ts"]),
            )
        )

        await build_and_contribute(store, tmp_path)

        assert store.catalog().get("booking.8.1") is not None


# --------------------------------------------------------------------------
# 2. Prompt two: the library is used, and the rest is learned
# --------------------------------------------------------------------------


class TestTheSecondBuildUsesWhatTheFirstTaught:
    async def test_the_matcher_assembles_the_contributed_booking_entry(
        self, tmp_path: Path
    ):
        """No model is involved: the decision is category + contract."""
        store = empty_store()
        await build_and_contribute(store, tmp_path)

        plan, _ = plan_for()
        report = await match_plan(plan, catalog=store.catalog(), use_judgment=False)

        match = report.for_package(BOOKING_PKG)
        assert match.decision is Decision.assemble
        assert match.entry_id == "booking.1.1"
        assert match.category == "booking"

    async def test_a_different_project_s_word_still_finds_it(self, tmp_path: Path):
        """The contract is entity-free, so "reservations" matches what
        "bookings" taught — which is the entire point of generalizing."""
        store = empty_store()
        await build_and_contribute(store, tmp_path)

        spec = make_booking_spec(
            sign_in=FieldMeta(value="an email link"),
            entities=FieldMeta(value=["reservations", "tables", "guests"]),
            key_actions=FieldMeta(value=["book a reservation", "cancel a reservation"]),
        )
        other = build_plan(derive_architecture(spec))

        report = await match_plan(other, catalog=store.catalog(), use_judgment=False)
        match = report.for_package(BOOKING_PKG)

        assert match.decision is Decision.assemble
        assert match.entry_id == "booking.1.1"

    async def test_the_login_package_has_no_match_and_is_learned_as_auth(
        self, tmp_path: Path
    ):
        store = empty_store()
        await build_and_contribute(store, tmp_path)

        plan, _ = plan_for()
        report = await match_plan(plan, catalog=store.catalog(), use_judgment=False)
        assert report.for_package(AUTH_PKG).decision is Decision.generate

        learned = await build_and_contribute(store, tmp_path, package_ids=(AUTH_PKG,))

        assert learned.added == ["auth.1.1"]
        assert store.catalog().get("auth.1.1").category == "auth"

    async def test_the_assembled_package_is_skipped_by_contribute(self, tmp_path: Path):
        """It came FROM the library. Offering it back would fill `booking` with
        copies of itself, each matching all the others."""
        store = empty_store()
        await build_and_contribute(store, tmp_path)

        plan, architecture = plan_for()
        package = plan.get(BOOKING_PKG)
        files = source_for(package)
        write(tmp_path, files)
        assembled = passed(package, files, entry_id="booking.1.1")

        report = await contribute_build(
            [package],
            [assembled],
            tmp_path,
            registry=ProviderRegistry.fake(),
            store=store,
            architecture=architecture,
        )

        assert [o.action for o in report.outcomes] == ["skipped"]
        assert report.added == []
        assert [e.id for e in store.catalog().entries] == ["booking.1.1"]


# --------------------------------------------------------------------------
# 3. Version vs new: the library improves rather than accumulating
# --------------------------------------------------------------------------


class TestVersionVersusNew:
    async def test_an_objectively_better_booking_bumps_the_version(self, tmp_path: Path):
        store = empty_store()
        await build_and_contribute(store, tmp_path)
        before = store.catalog().get("booking.1.1")

        # The same contract — the file plan is deterministic, so a second build
        # of this package writes exactly the same paths. What improves is the
        # code inside: more of it is instrumented, so more of it is markable.
        plan, architecture = plan_for()
        package = plan.get(BOOKING_PKG)
        files = source_for(package)
        for relative in [f for f in files if f.endswith(".tsx")]:
            files[relative] = files[relative].replace(
                "</section>",
                f'  <p data-scio-id="booking-{relative.replace("/", "-")}-note" '
                f'data-scio-package="{package.id}">note</p>\n    </section>',
            )
        write(tmp_path, files)
        result = passed(package, files)

        report = await contribute_build(
            [package], [result], tmp_path,
            registry=ProviderRegistry.fake(), store=store, architecture=architecture,
        )

        outcome = report.outcomes[0]
        assert outcome.action == "improved", outcome.reason
        assert outcome.entry_id == "booking.1.2"
        assert outcome.replaced == "booking.1.1"
        # Replaced, not added beside: two entries with one contract would make
        # the matcher choose between things that claim to be the same.
        assert [e.id for e in store.catalog().entries] == ["booking.1.2"]
        assert before.quality.evidence() < store.catalog().get("booking.1.2").quality.evidence()

    async def test_a_duplicate_that_is_no_better_is_discarded(self, tmp_path: Path):
        store = empty_store()
        await build_and_contribute(store, tmp_path)

        again = await build_and_contribute(store, tmp_path, project_id="p2")

        assert [o.action for o in again.outcomes] == ["discarded"]
        assert "not worse" in again.outcomes[0].reason
        assert [e.id for e in store.catalog().entries] == ["booking.1.1"]

    async def test_a_build_never_replaces_a_seed(self, tmp_path: Path):
        """Seeds were written and reviewed by a person. A pipeline does not get
        to overwrite one on the strength of counting its own tests."""
        store = FileCatalogStore(seed_dir=None)
        plan, architecture = plan_for()
        package = plan.get(BOOKING_PKG)
        files = source_for(package)
        write(tmp_path, files)
        seed = CatalogEntry(
            id="feature-booking-seed",
            name="a seed",
            layer=Layer.feature,
            description="written by hand",
            category="booking",
            contract=package_contract(package),
            files={"a.tsx": "x"},
            quality=Quality(tested=True, security_reviewed=True),
        )
        store._contributed.append(seed)  # a seed, in the pool the store reads

        report = await contribute_build(
            [package], [passed(package, files)], tmp_path,
            registry=ProviderRegistry.fake(), store=store, architecture=architecture,
        )

        assert report.outcomes[0].action == "discarded"
        assert "seed" in report.outcomes[0].reason

    async def test_a_different_function_in_the_same_category_gets_a_new_seqno(
        self, tmp_path: Path
    ):
        store = empty_store()
        await build_and_contribute(store, tmp_path)

        # Same category, different contract: a genuinely different thing.
        plan, architecture = plan_for()
        package = plan.get(BOOKING_PKG).model_copy(deep=True)
        package.architecture_slice = [
            node for node in package.architecture_slice if "cancel" not in node.name
        ]
        files = source_for(package)
        write(tmp_path, files)

        report = await contribute_build(
            [package], [passed(package, files)], tmp_path,
            registry=ProviderRegistry.fake(), store=store, architecture=architecture,
        )

        assert report.outcomes[0].action == "added"
        assert report.outcomes[0].entry_id == "booking.2.1"
        assert sorted(e.id for e in store.catalog().entries) == ["booking.1.1", "booking.2.1"]


# --------------------------------------------------------------------------
# 4. The refusals
# --------------------------------------------------------------------------


class TestWhatIsNeverLearned:
    def test_a_package_that_did_not_pass_every_gate_is_not_a_candidate(self):
        plan, _ = plan_for()
        package = plan.get(BOOKING_PKG)

        allowed, why = eligible(
            package,
            PackageBuildResult(
                package_id=package.id,
                status=PackageStatus.passed,
                checks_passed=4,
                checks_total=5,
            ),
        )

        assert allowed is False
        assert "4 of 5" in why

    def test_a_package_that_needs_a_look_is_not_a_candidate(self):
        plan, _ = plan_for()
        package = plan.get(BOOKING_PKG)

        allowed, why = eligible(
            package,
            PackageBuildResult(package_id=package.id, status=PackageStatus.needs_look),
        )

        assert allowed is False
        assert "needs_look" in why

    def test_the_project_s_own_shape_is_not_offered(self):
        """A foundation or a schema is derived from ONE architecture."""
        plan, _ = plan_for()

        for package_id in ("pkg_foundation", "pkg_schema", "pkg_design_tokens"):
            allowed, why = eligible(
                plan.get(package_id),
                PackageBuildResult(
                    package_id=package_id,
                    status=PackageStatus.passed,
                    checks_passed=5,
                    checks_total=5,
                ),
            )
            assert allowed is False, package_id
            assert "own shape" in why

    async def test_an_entry_that_does_not_re_verify_is_not_added(self, tmp_path: Path):
        """Generalization can break code. It must be proved not to have."""
        store = empty_store()
        plan, architecture = plan_for()
        package = plan.get(BOOKING_PKG)

        files = source_for(package)
        # The same id twice: after adaptation two elements claim one identity,
        # so a marking could not say which it meant.
        files["components/booking-list.tsx"] = files["components/booking-form.tsx"]
        write(tmp_path, files)

        report = await contribute_build(
            [package], [passed(package, files)], tmp_path,
            registry=ProviderRegistry.fake(), store=store, architecture=architecture,
        )

        assert report.outcomes[0].action == "refused"
        assert "instrumentation" in report.outcomes[0].reason
        assert len(store.catalog()) == 0

    async def test_a_leak_of_the_project_s_other_words_is_refused(self, tmp_path: Path):
        store = empty_store()
        plan, architecture = plan_for()
        package = plan.get(BOOKING_PKG)

        files = source_for(package)
        files["components/booking-form.tsx"] = files["components/booking-form.tsx"].replace(
            "Bookings", "Book a guest at Bistro Nord"
        )
        write(tmp_path, files)

        report = await contribute_build(
            [package], [passed(package, files)], tmp_path,
            registry=ProviderRegistry.fake(), store=store, architecture=architecture,
        )

        assert report.outcomes[0].action == "refused"
        assert "guest" in report.outcomes[0].reason
        assert len(store.catalog()) == 0

    async def test_one_package_s_refusal_never_stops_the_others(self, tmp_path: Path):
        store = empty_store()
        plan, architecture = plan_for()
        good, bad = plan.get(BOOKING_PKG), plan.get(AUTH_PKG)

        good_files, bad_files = source_for(good), source_for(bad)
        write(tmp_path, good_files)
        write(tmp_path, bad_files)

        report = await contribute_build(
            [good, bad],
            [passed(good, good_files), passed(bad, bad_files, status=PackageStatus.failed)],
            tmp_path,
            registry=ProviderRegistry.fake(),
            store=store,
            architecture=architecture,
        )

        assert sorted(o.action for o in report.outcomes) == ["added", "refused"]
        assert report.added == ["booking.1.1"]


# --------------------------------------------------------------------------
# 5. Categories stay canonical
# --------------------------------------------------------------------------


class TestCategoriesStayCanonical:
    def test_a_login_variant_maps_to_auth_rather_than_splitting(self):
        registry = default_registry()

        for word in ("login", "sign_in", "signin", "user_account", "authentication", "session"):
            assert registry.resolve(word) == "auth", word

    def test_bookings_reservations_and_appointments_are_one_category(self):
        registry = default_registry()

        assert {registry.resolve(w) for w in ("booking", "reservations", "appointment")} == {
            "booking"
        }

    def test_an_unknown_area_is_proposed_not_invented(self, tmp_path: Path):
        registry = default_registry()
        assert registry.resolve("widget_factory") == ""

        proposed = registry.propose("widget_factory", "makes widgets")

        assert proposed.confirmed is False
        # Unconfirmed, so nothing matches on it until a person says so.
        assert registry.resolve("widget_factory") == ""
        assert registry.confirm("widget_factory") is not None
        assert registry.resolve("widget_factory") == "widget_factory"

    async def test_a_package_in_no_known_category_proposes_one(self, tmp_path: Path):
        store = empty_store()
        spec = make_booking_spec(
            sign_in=FieldMeta(value="an email link"),
            entities=FieldMeta(value=["sprockets"]),
            key_actions=FieldMeta(value=["calibrate a sprocket", "retire a sprocket"]),
        )
        architecture = derive_architecture(spec)
        plan = build_plan(architecture)
        package = next(p for p in plan.packages if p.id == "pkg_feature_sprocket")
        files = source_for(package)
        write(tmp_path, files)

        report = await contribute_build(
            [package], [passed(package, files)], tmp_path,
            registry=ProviderRegistry.fake(), store=store, architecture=architecture,
        )

        assert report.outcomes[0].action == "added", report.outcomes[0].reason
        assert report.outcomes[0].entry_id.startswith("sprocket.")
        # Proposed, not invented: nothing matches on it until a person confirms.
        assert "sprocket" in report.proposed_categories


# --------------------------------------------------------------------------
# 6. What the library learns, the library can actually use
# --------------------------------------------------------------------------


class TestTheStoreIsWhatEverythingReads:
    """Both halves of this were wrong until a second build was run for real.

    Layer C matched against the seed directory, so a contributed entry could
    never be chosen; and once that was fixed the ASSEMBLER still read the seed
    directory, so the build aborted with "marked assemble but entry
    'auth.1.1' is not in the catalog". A library that can learn and not use what
    it learned is not a library.
    """

    async def test_layer_c_matches_against_contributions_not_only_seeds(
        self, tmp_path: Path, monkeypatch
    ):
        from scio_engine.layerb.derive import derive_architecture as derive
        from scio_engine.layerc import service as layerc_service
        from scio_engine.library import store as store_module

        book = empty_store()
        await build_and_contribute(book, tmp_path)
        assert book.catalog().get("booking.1.1") is not None

        monkeypatch.setattr(store_module, "_STORE", book)
        monkeypatch.setattr(layerc_service, "default_store", lambda: book)

        spec = make_booking_spec(sign_in=FieldMeta(value="an email link"))
        result = await layerc_service.run_layer_c(
            derive(spec), registry=ProviderRegistry.fake(), use_judgment=False
        )

        package = result.plan.get(BOOKING_PKG)
        assert package.source == "assemble"
        assert package.catalog_entry == "booking.1.1"

    async def test_the_assembler_can_find_a_contributed_entry(
        self, tmp_path: Path, monkeypatch
    ):
        from scio_engine.library import assembler as assembler_module
        from scio_engine.library import store as store_module

        book = empty_store()
        await build_and_contribute(book, tmp_path)

        monkeypatch.setattr(store_module, "_STORE", book)
        monkeypatch.setattr(assembler_module, "default_store", lambda: book)

        plan, _ = plan_for()
        package = plan.get(BOOKING_PKG)
        package.source = "assemble"
        package.catalog_entry = "booking.1.1"

        target = tmp_path / "app"
        result = assembler_module.assemble_package(
            package, target, entity="booking", package_files={package.id: planned_files(package)}
        )

        assert result.status is PackageStatus.passed
        # …and it says where it came from, which is what makes contribute skip it.
        assert result.entry_id == "booking.1.1"


# --------------------------------------------------------------------------
# 7. The ids themselves
# --------------------------------------------------------------------------


class TestEntryIds:
    def test_the_shape_is_category_seqno_version(self):
        parsed = EntryId.parse("booking.12.3")

        assert (parsed.category, parsed.seqno, parsed.version) == ("booking", 12, 3)
        assert parsed.line == "booking.12"
        assert str(parsed.bumped()) == "booking.12.4"

    def test_a_seed_id_is_not_pretended_to_be_one(self):
        assert EntryId.parse("feature-booking") is None
        assert EntryId.parse("booking.1") is None

    def test_the_store_hands_out_the_next_number_per_category(self):
        store = empty_store()
        assert store.next_seqno("booking") == 1

        store.put(
            CatalogEntry(
                id="booking.1.1", name="a", layer=Layer.feature, description="a",
                category="booking", files={"a.ts": "x"},
            )
        )

        assert store.next_seqno("booking") == 2
        assert store.next_seqno("auth") == 1
