"""The intake agent (4.3 / B024) — extraction + next-question.

The two things worth proving are the two that decide whether gate 1 is honest:
extraction records what was said and *only* what was said, and the question that
comes back is the one the gate actually needs answered next.
"""

import json

import pytest

from scio_engine.execution.provider import ProviderRegistry
from scio_engine.intake.contradictions import detect
from scio_engine.intake.conversation import Conversation, IntakeMessage
from scio_engine.intake.extraction import apply_extraction
from scio_engine.intake.gate import is_buildable
from scio_engine.intake.questions import next_target
from scio_engine.intake.schema import AppSpec, Confidence, DataSensitivity, FieldMeta, Source
from scio_engine.intake.service import run_intake_step


def messages(*texts: str) -> list[IntakeMessage]:
    """A conversation that alternates Scio/user, ending on the user."""
    out: list[IntakeMessage] = []
    for index, text in enumerate(texts):
        out.append(IntakeMessage(role="assistant" if index % 2 else "user", text=text))
    return out


def user_says(*texts: str) -> list[IntakeMessage]:
    return [IntakeMessage(role="user", text=text) for text in texts]


def extraction_reply(fields: dict, signals: dict | None = None) -> str:
    return json.dumps({"fields": fields, "signals": signals or {}})


def question_reply(question: str, example: str) -> str:
    return json.dumps({"question": question, "example": example})


BOOKING_ANSWER = "Guests book a table at my restaurant and get a confirmation."

FULL_EXTRACTION = {
    "purpose": {
        "value": "Guests book a table and get a confirmation.",
        "source": "stated",
        "confidence": "high",
        "provenance": ["m1"],
    },
    "users_and_roles": {
        "value": ["guests"],
        "source": "stated",
        "confidence": "high",
        "provenance": ["m1"],
    },
    "entities": {
        "value": ["bookings", "tables", "guests"],
        "source": "derived",
        "confidence": "medium",
        "provenance": ["m1"],
    },
    "key_actions": {
        "value": ["book a table", "cancel a booking"],
        "source": "stated",
        "confidence": "high",
        "provenance": ["m1"],
    },
    "sign_in": {
        "value": "No account — name and phone.",
        "source": "stated",
        "confidence": "high",
        "provenance": ["m1"],
    },
    "data_ownership_sensitivity": {
        "value": {"owner": "you", "sensitive": False, "kinds": []},
        "source": "stated",
        "confidence": "medium",
        "provenance": ["m1"],
    },
    "non_goals": {
        "value": ["no payments for now"],
        "source": "stated",
        "confidence": "high",
        "provenance": ["m1"],
    },
}


class TestExtraction:
    """apply_extraction is the part that decides what is kept, so it is tested
    directly — the relay around it is proven separately."""

    def test_a_stated_answer_fills_the_field_with_its_provenance(self):
        spec, report = apply_extraction(
            AppSpec(),
            {"fields": {"purpose": FULL_EXTRACTION["purpose"]}},
            evidence_ids={"m1"},
        )

        assert spec.purpose.value == "Guests book a table and get a confirmation."
        assert spec.purpose.source is Source.stated
        assert spec.purpose.confidence is Confidence.high
        assert spec.purpose.provenance == ["m1"]
        assert report.updated == ["purpose"]

    def test_an_unstated_value_is_not_invented(self):
        # The model claims the user said something, but cites nothing they sent.
        spec, report = apply_extraction(
            AppSpec(),
            {
                "fields": {
                    "sign_in": {
                        "value": "Sign in with Google",
                        "source": "stated",
                        "confidence": "high",
                        "provenance": [],
                    }
                }
            },
            evidence_ids={"m1"},
        )

        assert spec.sign_in is None  # left empty, so it becomes a question
        assert report.rejected[0].field == "sign_in"
        assert "cites no message" in report.rejected[0].reason

    def test_provenance_must_name_a_real_user_message(self):
        spec, report = apply_extraction(
            AppSpec(),
            {
                "fields": {
                    "purpose": {
                        "value": "A CRM for dentists",
                        "source": "stated",
                        "confidence": "high",
                        "provenance": ["m99"],  # never sent
                    }
                }
            },
            evidence_ids={"m1"},
        )

        assert spec.purpose is None
        assert report.rejected[0].reason.startswith("claimed as stated")

    def test_an_inference_is_recorded_as_derived(self):
        spec, _ = apply_extraction(
            AppSpec(), {"fields": {"entities": FULL_EXTRACTION["entities"]}}, evidence_ids={"m1"}
        )

        assert spec.entities.source is Source.derived
        assert spec.entities.value == ["bookings", "tables", "guests"]

    def test_an_inference_is_never_high_confidence(self):
        spec, _ = apply_extraction(
            AppSpec(),
            {
                "fields": {
                    "sign_in": {
                        "value": "probably email",
                        "source": "derived",
                        "confidence": "high",
                        "provenance": ["m1"],
                    }
                }
            },
            evidence_ids={"m1"},
        )

        assert spec.sign_in.confidence is Confidence.medium

    def test_an_inference_may_not_overwrite_what_the_user_stated(self):
        spec = AppSpec(sign_in=FieldMeta(value="No account — name and phone."))
        spec, report = apply_extraction(
            spec,
            {
                "fields": {
                    "sign_in": {
                        "value": "Google sign-in",
                        "source": "derived",
                        "confidence": "medium",
                        "provenance": ["m1"],
                    }
                }
            },
            evidence_ids={"m1"},
        )

        assert spec.sign_in.value == "No account — name and phone."
        assert "may not overwrite" in report.rejected[0].reason

    def test_a_later_stated_answer_does_correct_an_earlier_one(self):
        spec = AppSpec(sign_in=FieldMeta(value="No account."))
        spec, _ = apply_extraction(
            spec,
            {
                "fields": {
                    "sign_in": {
                        "value": "Actually, an email link.",
                        "source": "stated",
                        "confidence": "high",
                        "provenance": ["m3"],
                    }
                }
            },
            evidence_ids={"m1", "m3"},
        )

        assert spec.sign_in.value == "Actually, an email link."

    def test_list_answers_merge_without_duplicating_the_same_concept(self):
        spec = AppSpec(entities=FieldMeta(value=["bookings", "tables"]))
        spec, _ = apply_extraction(
            spec,
            {
                "fields": {
                    "entities": {
                        "value": ["reservations", "guests"],
                        "source": "stated",
                        "confidence": "high",
                        "provenance": ["m3"],
                    }
                }
            },
            evidence_ids={"m3"},
        )

        # "reservations" is the canonical "booking" the spec already holds; the
        # user's own wording is kept for what is genuinely new.
        assert spec.entities.value == ["bookings", "tables", "guests"]

    def test_a_placeholder_value_is_treated_as_no_answer(self):
        spec, report = apply_extraction(
            AppSpec(),
            {
                "fields": {
                    "purpose": {
                        "value": "unknown",
                        "source": "stated",
                        "confidence": "low",
                        "provenance": ["m1"],
                    }
                }
            },
            evidence_ids={"m1"},
        )

        assert spec.purpose is None
        assert "no usable value" in report.rejected[0].reason

    def test_fields_outside_the_schema_are_dropped(self):
        spec, report = apply_extraction(
            AppSpec(),
            {"fields": {"deployment_region": {"value": "eu-north", "source": "stated"}}},
            evidence_ids={"m1"},
        )

        assert report.rejected[0].reason == "not an intake field"
        assert not hasattr(spec, "deployment_region")

    def test_defaulted_fields_cannot_be_silently_overwritten(self):
        # `look` is assumed-and-flagged; extraction must not erase the flag.
        spec, report = apply_extraction(
            AppSpec(),
            {"fields": {"look": {"value": "dark and brutalist", "source": "stated"}}},
            evidence_ids={"m1"},
        )

        assert spec.look.source is Source.default
        assert report.rejected[0].field == "look"

    def test_signals_open_follow_ups(self):
        spec, report = apply_extraction(
            AppSpec(), {"fields": {}, "signals": {"charges_money": True}}, evidence_ids={"m1"}
        )

        assert spec.signals.charges_money is True
        assert report.signals_set == ["charges_money"]


class TestNextTarget:
    def test_the_gate_picks_the_first_missing_core_field(self):
        spec = AppSpec()
        assert next_target(spec, is_buildable(spec)) == "purpose"

    def test_it_moves_on_once_that_field_is_answered(self):
        spec = AppSpec(purpose=FieldMeta(value="Guests book a table."))
        assert next_target(spec, is_buildable(spec)) == "users_and_roles"

    def test_non_goals_is_asked_after_the_core_and_before_the_conditionals(self):
        spec, _ = apply_extraction(
            AppSpec(),
            {"fields": {k: v for k, v in FULL_EXTRACTION.items() if k != "non_goals"}},
            evidence_ids={"m1"},
        )
        spec.signals.charges_money = True  # something still outstanding

        assert next_target(spec, is_buildable(spec)) == "non_goals"

    def test_a_triggered_conditional_becomes_the_target(self):
        spec, _ = apply_extraction(AppSpec(), {"fields": FULL_EXTRACTION}, evidence_ids={"m1"})
        spec.signals.charges_money = True

        assert next_target(spec, is_buildable(spec)) == "payment"

    def test_nothing_is_asked_once_the_spec_is_buildable(self):
        spec, _ = apply_extraction(AppSpec(), {"fields": FULL_EXTRACTION}, evidence_ids={"m1"})

        assert is_buildable(spec).buildable is True
        assert next_target(spec, is_buildable(spec)) is None


class TestContradictions:
    def test_no_sign_in_with_several_roles_is_a_contradiction(self):
        spec = AppSpec(
            sign_in=FieldMeta(value="No account needed."),
            users_and_roles=FieldMeta(value=["guests", "staff"]),
        )
        found = detect(spec)

        assert found and set(found[0].fields) == {"sign_in", "users_and_roles"}

    def test_no_sign_in_with_per_user_data_is_a_contradiction(self):
        spec = AppSpec(
            sign_in=FieldMeta(value="No login."),
            key_actions=FieldMeta(value=["each guest sees their own bookings"]),
        )
        assert any("identify them" in c.description for c in detect(spec))

    def test_not_sensitive_but_payment_data_is_a_contradiction(self):
        spec = AppSpec(
            data_ownership_sensitivity=FieldMeta(
                value=DataSensitivity(owner="you", sensitive=False, kinds=["payment"])
            )
        )
        assert any("usually" in c.description for c in detect(spec))

    def test_a_consistent_spec_has_none(self):
        spec = AppSpec(
            sign_in=FieldMeta(value="No account — name and phone."),
            users_and_roles=FieldMeta(value=["guests"]),
            key_actions=FieldMeta(value=["book a table"]),
        )
        assert detect(spec) == []


class TestStepEndToEnd:
    """The whole turn, driven through the relay with scripted replies."""

    async def test_a_first_answer_is_extracted_and_the_next_gap_is_asked(self):
        registry = ProviderRegistry.scripted(
            [
                extraction_reply({"purpose": FULL_EXTRACTION["purpose"]}),
                extraction_reply({"purpose": FULL_EXTRACTION["purpose"]}),  # review pass
                question_reply("Who will be using it?", "Guests, and staff who see the list."),
            ],
            loop_last=False,
        )

        step = await run_intake_step(user_says(BOOKING_ANSWER), registry=registry)

        assert step.updated_spec.purpose.value.startswith("Guests book a table")
        assert step.buildable is False
        assert step.next_question.field == "users_and_roles"
        assert step.next_question.text == "Who will be using it?"
        assert step.next_question.example  # a question always carries an example
        assert "For example:" in step.next_question.as_text()

    async def test_a_complete_answer_opens_the_gate_with_no_question_left(self):
        registry = ProviderRegistry.scripted(
            [extraction_reply(FULL_EXTRACTION), extraction_reply(FULL_EXTRACTION)],
            loop_last=False,
        )

        step = await run_intake_step(user_says(BOOKING_ANSWER), registry=registry)

        assert step.buildable is True
        assert step.next_question is None
        assert step.done is True

    async def test_unanswered_non_goals_becomes_a_flagged_assumption_not_a_blocker(self):
        # docs/INTAKE-SCHEMA.md asks for non-goals always; the gate does not block
        # on them. Rather than hold a finished wizard open, "nothing excluded" is
        # recorded as an assumption the review screen shows and can correct.
        without = {k: v for k, v in FULL_EXTRACTION.items() if k != "non_goals"}
        registry = ProviderRegistry.scripted(
            [extraction_reply(without), extraction_reply(without)], loop_last=False
        )

        step = await run_intake_step(user_says(BOOKING_ANSWER), registry=registry)

        assert step.buildable is True
        assert step.next_question is None
        assert step.updated_spec.non_goals.value == []
        assert step.updated_spec.non_goals.is_assumed is True

    async def test_the_question_always_has_an_example_even_if_the_model_rambles(self):
        registry = ProviderRegistry.scripted(
            [
                extraction_reply({}),
                extraction_reply({}),
                "Well, it depends on what you mean by an app, really.",
            ],
            loop_last=False,
        )

        step = await run_intake_step(user_says("hi"), registry=registry)

        assert step.next_question.written_by == "guide"
        assert step.next_question.field == "purpose"
        assert step.next_question.example  # from INTAKE-SCHEMA.md, never empty

    async def test_a_contradiction_is_asked_about_rather_than_resolved(self):
        conflicting = {
            "sign_in": {
                "value": "No account at all.",
                "source": "stated",
                "confidence": "high",
                "provenance": ["m1"],
            },
            "users_and_roles": {
                "value": ["guests", "staff"],
                "source": "stated",
                "confidence": "high",
                "provenance": ["m1"],
            },
        }
        registry = ProviderRegistry.scripted(
            [
                extraction_reply(conflicting),
                extraction_reply(conflicting),
                question_reply(
                    "Should staff sign in, even if guests don't?",
                    "Staff sign in with an email link; guests don't.",
                ),
            ],
            loop_last=False,
        )

        step = await run_intake_step(user_says(BOOKING_ANSWER), registry=registry)

        assert step.contradictions  # surfaced
        assert step.next_question.about == "contradiction"
        assert step.buildable is False
        # Neither answer was quietly picked for the user.
        assert step.updated_spec.sign_in.value == "No account at all."
        assert step.updated_spec.users_and_roles.value == ["guests", "staff"]

    async def test_an_unusable_extraction_reply_changes_nothing(self):
        registry = ProviderRegistry.scripted(
            ["I'd love to help!", "Still not JSON.", question_reply("What does it do?", "...")],
            loop_last=False,
        )
        before = AppSpec(purpose=FieldMeta(value="Guests book a table."))

        step = await run_intake_step(user_says("go on then"), before, registry=registry)

        assert step.extraction.parsed is False
        assert step.updated_spec.purpose.value == "Guests book a table."
        assert step.next_question is not None  # the wizard keeps going

    async def test_the_caller_keeps_its_own_spec_object(self):
        registry = ProviderRegistry.scripted(
            [extraction_reply(FULL_EXTRACTION), extraction_reply(FULL_EXTRACTION)],
            loop_last=False,
        )
        original = AppSpec()

        await run_intake_step(user_says(BOOKING_ANSWER), original, registry=registry)

        assert original.purpose is None  # mutated a copy, not the caller's spec

    async def test_provenance_survives_a_multi_turn_conversation(self):
        later = {
            "sign_in": {
                "value": "An email link.",
                "source": "stated",
                "confidence": "high",
                "provenance": ["m3"],
            }
        }
        registry = ProviderRegistry.scripted(
            [
                extraction_reply(later),
                extraction_reply(later),
                question_reply("What are the core things it manages?", "Bookings, tables."),
            ],
            loop_last=False,
        )
        conversation = messages(
            BOOKING_ANSWER,  # m1, user
            "Who uses it?",  # m2, assistant
            "Guests sign in with an email link.",  # m3, user
        )

        step = await run_intake_step(conversation, registry=registry)

        assert step.updated_spec.sign_in.provenance == ["m3"]


class TestTheLoopConverges:
    """Per-turn correctness is not the same as terminating. A wizard that asks a
    good question forever is still a wizard nobody finishes."""

    async def test_three_turns_reach_a_buildable_spec_asking_something_new_each_time(self):
        turn_one = {
            "purpose": FULL_EXTRACTION["purpose"],
            "users_and_roles": FULL_EXTRACTION["users_and_roles"],
            "entities": FULL_EXTRACTION["entities"],
        }
        turn_two = {
            "key_actions": FULL_EXTRACTION["key_actions"],
            "sign_in": FULL_EXTRACTION["sign_in"],
        }
        turn_three = {
            "data_ownership_sensitivity": FULL_EXTRACTION["data_ownership_sensitivity"],
            "non_goals": FULL_EXTRACTION["non_goals"],
        }
        registry = ProviderRegistry.scripted(
            [
                extraction_reply(turn_one), extraction_reply(turn_one),
                question_reply("What should people be able to do?", "Book, cancel."),
                extraction_reply(turn_two), extraction_reply(turn_two),
                question_reply("Who owns the data?", "I do; nothing sensitive."),
                extraction_reply(turn_three), extraction_reply(turn_three),
            ],
            loop_last=False,
        )

        conversation = user_says(BOOKING_ANSWER)
        spec = None
        asked = []
        for answer in ("Book and cancel. No account.", "I own it; nothing sensitive."):
            step = await run_intake_step(conversation, spec, registry=registry)
            spec = step.updated_spec
            asked.append(step.next_question.field)
            conversation = [
                *conversation,
                IntakeMessage(role="assistant", text=step.next_question.as_text()),
                IntakeMessage(role="user", text=answer),
            ]

        final = await run_intake_step(conversation, spec, registry=registry)

        assert asked == ["key_actions", "data_ownership_sensitivity"]
        assert len(set(asked)) == len(asked)  # never asked the same thing twice
        assert final.buildable is True
        assert final.next_question is None
        assert final.updated_spec.purpose.provenance == ["m1"]


class TestConversation:
    def test_messages_get_stable_ids(self):
        conversation = Conversation.of(messages("a", "b", "c"))
        assert [m.id for m in conversation.messages] == ["m1", "m2", "m3"]

    def test_only_the_users_own_messages_count_as_evidence(self):
        conversation = Conversation.of(messages("mine", "Scio's question", "mine again"))
        assert conversation.evidence_ids == {"m1", "m3"}

    def test_a_supplied_id_is_kept(self):
        conversation = Conversation.of([IntakeMessage(id="turn-7", role="user", text="hi")])
        assert conversation.messages[0].id == "turn-7"


@pytest.mark.parametrize("field", ["purpose", "sign_in", "payment", "non_goals"])
def test_every_askable_field_has_a_question_and_an_example(field):
    from scio_engine.intake.questions import fallback_question

    question = fallback_question(field)
    assert question.text.endswith("?")
    assert question.example
