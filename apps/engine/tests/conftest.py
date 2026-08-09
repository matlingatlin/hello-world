"""Shared fixtures. The booking app is the running example throughout the docs
(INTAKE-SCHEMA, LAYER-B, the prototype), so the tests use it too."""

import pytest

from scio_engine.intake.schema import AppSpec, DataSensitivity, FieldMeta


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
