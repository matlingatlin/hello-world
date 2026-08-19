"""B066: correcting a field the wizard filed wrongly.

The defect is mundane and expensive. Extraction puts "guests and staff" in
`entities` instead of `users_and_roles`; the review screen shows it; and until
now the only way to fix it was to start the wizard again. Nobody starts again —
they approve a spec they know is wrong, and every layer below faithfully builds
the wrong thing.

What is under test is not "the value changed". It is the three properties that
make a correction worth trusting: it outranks extraction, it re-opens work it
genuinely opens, and it can settle the contradiction it caused.
"""

from __future__ import annotations

import pytest

from scio_engine.intake.correction import (
    CORRECTION_MARK,
    CorrectionError,
    FieldCorrection,
    correct_field,
)
from scio_engine.intake.extraction import apply_extraction
from scio_engine.intake.schema import (
    AppSpec,
    Confidence,
    Contradiction,
    DataSensitivity,
    FieldMeta,
    Source,
)


def spec(**fields) -> AppSpec:
    base = AppSpec(
        purpose=FieldMeta(value="Guests book a table.", provenance=["m1"]),
        users_and_roles=FieldMeta(value=["guests"], provenance=["m1"]),
        entities=FieldMeta(value=["bookings"], provenance=["m1"]),
        key_actions=FieldMeta(value=["book a table"], provenance=["m1"]),
        sign_in=FieldMeta(value="an email link", provenance=["m1"]),
        data_ownership_sensitivity=FieldMeta(
            value=DataSensitivity(owner="you", sensitive=False), provenance=["m1"]
        ),
    )
    for name, value in fields.items():
        setattr(base, name, value)
    return base


def correct(current: AppSpec, field: str, value, clear: list[str] | None = None):
    return correct_field(current, FieldCorrection(field=field, value=value, clear=clear or []))


class TestTheCorrectionItself:
    def test_a_misfiled_answer_moves_to_the_right_field(self):
        """The actual defect: one action, not a restart."""
        current = spec(entities=FieldMeta(value=["guests", "staff"], provenance=["m2"]))

        result = correct(current, "users_and_roles", ["guests", "staff"], clear=["entities"])

        assert result.updated_spec.users_and_roles is not None
        assert result.updated_spec.users_and_roles.value == ["guests", "staff"]
        assert result.updated_spec.entities is None
        assert result.changed == ["users_and_roles"]
        assert result.cleared == ["entities"]

    def test_a_correction_is_stated_with_a_manual_provenance(self):
        result = correct(spec(), "purpose", "Staff manage today's tables.")
        field = result.updated_spec.purpose

        assert field is not None
        assert field.source is Source.stated
        assert field.confidence is Confidence.high
        # Not a message id: nobody said this, somebody typed it.
        assert field.provenance == [CORRECTION_MARK]

    def test_a_comma_separated_answer_becomes_a_list(self):
        """What a person types into one box, in the shape the schema wants."""
        result = correct(spec(), "entities", "bookings, tables, guests")

        assert result.updated_spec.entities is not None
        assert result.updated_spec.entities.value == ["bookings", "tables", "guests"]

    def test_an_assumption_can_be_replaced_by_hand(self):
        """The defaulted fields exist to be corrected — that is what showing them is for."""
        result = correct(spec(), "look", "dark, dense, no rounded corners")

        assert result.updated_spec.look.value == "dark, dense, no rounded corners"
        assert result.updated_spec.look.source is Source.stated
        assert "look" not in [n for n in result.still_needed]

    def test_the_sensitivity_field_keeps_its_shape(self):
        result = correct(
            spec(),
            "data_ownership_sensitivity",
            {"owner": "the restaurant", "sensitive": True, "kinds": ["personal"]},
        )
        value = result.updated_spec.data_ownership_sensitivity

        assert value is not None
        assert value.value.sensitive is True
        assert value.value.kinds == ["personal"]


class TestWhatACorrectionRefuses:
    def test_an_unknown_field_is_named_not_guessed(self):
        with pytest.raises(CorrectionError, match="not a field on the spec"):
            correct(spec(), "colour_scheme", "blue")

    def test_a_value_of_the_wrong_shape_is_refused(self):
        with pytest.raises(CorrectionError, match="sentence"):
            correct(spec(), "purpose", ["a", "list"])

    def test_a_core_list_cannot_be_emptied_by_accident(self):
        """"No entities" is not an answer — it is a field nobody filled."""
        with pytest.raises(CorrectionError, match="at least one value"):
            correct(spec(), "entities", "   ")

    def test_nothing_excluded_is_a_real_answer_for_non_goals(self):
        result = correct(spec(), "non_goals", "")

        assert result.updated_spec.non_goals is not None
        assert result.updated_spec.non_goals.value == []

    def test_an_assumption_cannot_be_emptied(self):
        with pytest.raises(CorrectionError, match="cannot be emptied"):
            correct(spec(), "purpose", "still fine", clear=["look"])


class TestACorrectionCanOpenWork:
    def test_a_second_role_opens_role_permissions(self):
        """The kickoff's own example: correcting roles triggers RBAC."""
        before = spec()
        assert before.role_permissions is None

        result = correct(before, "users_and_roles", ["guests", "staff"])

        assert "role_permissions" in result.newly_required
        assert result.gate.buildable is False
        assert "role_permissions" in result.gate.unresolved_conditionals

    def test_sensitive_data_opens_compliance(self):
        result = correct(
            spec(),
            "data_ownership_sensitivity",
            {"owner": "you", "sensitive": True, "kinds": ["personal"]},
        )

        assert "compliance" in result.newly_required
        assert result.gate.buildable is False

    def test_answering_what_it_opened_closes_the_gate_again(self):
        opened = correct(spec(), "users_and_roles", ["guests", "staff"])
        assert opened.gate.buildable is False

        filled = correct(
            opened.updated_spec,
            "role_permissions",
            "Staff see today's list; guests see the menu.",
        )

        assert filled.gate.buildable is True
        assert filled.newly_required == []

    def test_clearing_a_core_field_reopens_the_gate(self):
        result = correct(spec(), "users_and_roles", ["guests", "staff"], clear=["entities"])

        assert "entities" in result.gate.missing_core
        assert "entities" in result.newly_required
        assert result.gate.buildable is False

    def test_a_correction_that_opens_nothing_says_so(self):
        result = correct(spec(), "purpose", "Guests book a table and get a text back.")

        assert result.newly_required == []
        assert result.gate.buildable is True


class TestACorrectionCanSettleAContradiction:
    def test_fixing_the_answer_that_caused_it_clears_it(self):
        """Otherwise the gate stays shut on a question already answered."""
        conflicted = spec(
            users_and_roles=FieldMeta(value=["guests", "staff"], provenance=["m2"]),
            sign_in=FieldMeta(value="no sign-in at all", provenance=["m3"]),
            role_permissions=FieldMeta(value="staff see everything", provenance=["m4"]),
        )
        conflicted.contradictions = [
            Contradiction(
                fields=["users_and_roles", "sign_in"],
                description="two kinds of user, but nobody signs in",
            )
        ]
        assert conflicted.contradictions[0].resolved is False

        result = correct(conflicted, "sign_in", "an email link")

        assert result.updated_spec.contradictions == []
        assert result.gate.buildable is True


class TestACorrectionOutranksExtraction:
    def test_extraction_may_not_overwrite_a_hand_correction(self):
        """The conversation still holds the sentence that was misfiled.

        Without this rule the very next wizard turn re-files it and the
        correction evaporates — silently, which is the worst kind.
        """
        corrected = correct(spec(), "users_and_roles", ["guests", "staff"]).updated_spec

        after, report = apply_extraction(
            corrected,
            {
                "fields": {
                    "users_and_roles": {
                        "value": ["guests"],
                        "source": "stated",
                        "provenance": ["m1"],
                    }
                }
            },
            evidence_ids={"m1"},
        )

        assert after.users_and_roles is not None
        assert after.users_and_roles.value == ["guests", "staff"]
        # Refused out loud, and the reason says who wins and why.
        assert [r.field for r in report.rejected] == ["users_and_roles"]
        assert "corrected this by hand" in report.rejected[0].reason

    def test_a_field_nobody_corrected_is_still_extractable(self):
        after, report = apply_extraction(
            spec(),
            {
                "fields": {
                    "purpose": {
                        "value": "Guests book a table online.",
                        "source": "stated",
                        "provenance": ["m1"],
                    }
                }
            },
            evidence_ids={"m1"},
        )

        assert after.purpose is not None
        assert after.purpose.value == "Guests book a table online."
        assert report.rejected == []
