"""Shared fixtures. The booking app is the running example throughout the docs
(INTAKE-SCHEMA, LAYER-B, the prototype), so the tests use it too."""

import os

# Before ANY scio_engine import: the suite must not pick up an operator's
# apps/engine/.env. When it did, the relay's ordering tests asserted against
# whatever model that file named, and test_api.py made REAL model calls — a
# test run that took 100 seconds and spent the operator's money. Tests are
# hermetic; a local configuration file is not part of the code under test.
os.environ["SCIO_SKIP_ENV_FILE"] = "1"
for _name in (
    "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
    "GOOGLE_API_KEY",
    "SCIO_MODEL",
    "SCIO_MODEL_PASSES",
    "SCIO_ONLY_PROVIDER",
):
    os.environ.pop(_name, None)

import pytest  # noqa: E402

from scio_engine.intake.schema import AppSpec, DataSensitivity, FieldMeta  # noqa: E402


def make_booking_spec(**overrides) -> AppSpec:
    base = dict(
        purpose=FieldMeta(value="Guests book a table and get a confirmation."),
        users_and_roles=FieldMeta(value=["guests"]),
        entities=FieldMeta(value=["bookings", "tables", "guests"]),
        key_actions=FieldMeta(value=["book a table", "cancel a booking"]),
        sign_in=FieldMeta(value="no account — name and phone"),
        data_ownership_sensitivity=FieldMeta(value=DataSensitivity(owner="you", sensitive=False)),
        non_goals=FieldMeta(value=["no payments for now"]),
    )
    base.update(overrides)
    return AppSpec(**base)


@pytest.fixture
def booking_spec_factory():
    return make_booking_spec


@pytest.fixture(autouse=True)
def isolated_library_store():
    """Every test gets its own library. Nothing one test learns reaches another.

    The build pipeline contributes what it produced back to `default_store()`,
    which is a process-wide singleton — correct in production (one library per
    engine) and poison in a test suite: a full-build test would leave a
    `booking` entry behind, and the next test to ask the matcher about bookings
    would assemble it instead of generating, failing for a reason nowhere near
    the assertion. That is exactly what happened when the contribute gate
    stopped rejecting real packages (B074).

    Pinned to the seed directory rather than reset to the default, so a test run
    with `SCIO_CATALOG_DB` set — which is how the Postgres tests run — cannot
    write into a real database either.
    """
    from scio_engine.library.catalog import SEED_DIR
    from scio_engine.library.store import FileCatalogStore, set_store

    set_store(FileCatalogStore(seed_dir=SEED_DIR))
    yield
    set_store(None)


def complete_reply(package, code: str) -> str:
    """`code`, padded with a minimal stub for every other file in the plan.

    A feature package plans eight files. A test about ONE of them used to write
    just that one, which the builder accepted — and B076 is precisely the rule
    that it should not: a package missing three files is an app missing a form.

    So focused tests stay focused (the interesting file is written out in full,
    right there in the test) and the package is still complete. The stubs are
    deliberately boring: an instrumented element for markup, a named export for
    everything else, so nothing here trips a guardrail the test is not about.
    """
    from scio_engine.builder.file_plan import planned_files

    present = {
        line.split("FILE:", 1)[1].strip()
        for line in code.splitlines()
        if line.startswith("FILE:")
    }
    blocks = [code.rstrip("\n")]
    for path in planned_files(package):
        if path in present:
            continue
        slug = path.replace("/", "-").replace(".", "-")
        name = "".join(part.title() for part in slug.split("-") if part.isalnum())
        if path.endswith((".tsx", ".jsx")):
            blocks.append(
                f'FILE: {path}\n```tsx\nexport default function {name}() {{\n'
                f'  return <section data-scio-id="{slug}">{name}</section>;\n}}\n```'
            )
        elif path.endswith(".sql"):
            blocks.append(f"FILE: {path}\n```sql\ncreate table if not exists stub (id uuid);\n```")
        elif "test" in path:
            blocks.append(
                f'FILE: {path}\n```ts\ntest("{slug}", () => {{ expect(true).toBe(true); }});\n```'
            )
        else:
            name = slug.replace("-", "_")
            blocks.append(f"FILE: {path}\n```ts\nexport const {name} = {{}};\n```")
    return "\n\n".join(blocks) + "\n"


def scripted_codegen(package, replies: list[str]) -> list[str]:
    """Scripted replies, adjusted for a package that is generated in chunks.

    A package too big for one reply is emitted in bounded chunks (B076), so one
    "generate this package" step is now several calls. Each chunk call filters
    the reply down to the files it asked for, so handing the same complete reply
    to each chunk is both correct and the least surprising thing for a test to
    say: the script still reads as one reply per step.
    """
    from scio_engine.builder.loop import file_chunks

    chunks = max(1, len(file_chunks(package)))
    out: list[str] = []
    first_codegen = True
    for reply in replies:
        if not reply.lstrip().startswith("FILE:"):
            out.append(reply)
            continue
        # Only the FIRST generation is chunked. Every later codegen reply is a
        # REPAIR, and a repair is one call with the code already in hand — the
        # loop does not chunk it, so neither does the script.
        out.extend([complete_reply(package, reply)] * (chunks if first_codegen else 1))
        first_codegen = False
    return out
