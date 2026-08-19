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
