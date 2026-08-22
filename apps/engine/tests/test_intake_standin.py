"""Gate 1 with no model — the path the operator actually clicks through.

The stand-in exists because the free path could not finish at all: the fake
provider returns a digest, extraction cannot parse a digest, nothing is ever
recorded, and the wizard asks the same question forever.

What is held here is the honesty contract, which matters more for a stand-in
than for a model: every value is the person's own words, cited to the message
they typed it in, and nothing is invented to fill a slot.
"""

from __future__ import annotations

import json

from scio_engine.intake.fields import guide_for
from scio_engine.intake.standin import answer_extraction


def prompt(*, question: str, answer: str, recorded: str = "") -> str:
    """An extraction prompt in the shape build_extraction_prompt produces."""
    return (
        "## The conversation so far\n"
        f"[m1] SCIO: {question}\n"
        f"[m2] USER: {answer}\n\n"
        "## Already recorded (do not repeat unless it changed)\n"
        f"{recorded or '(nothing yet)'}\n"
    )


def fields_of(reply: str) -> dict:
    return json.loads(reply)["fields"]


class TestFilingTheAnswer:
    def test_the_answer_goes_under_the_question_that_was_asked(self):
        asked = guide_for("purpose").question
        reply = fields_of(answer_extraction(prompt(question=asked, answer="Guests book a table.")))

        assert reply["purpose"]["value"] == "Guests book a table."
        assert reply["purpose"]["provenance"] == ["m2"]

    def test_a_turn_with_nothing_in_it_records_nothing(self):
        reply = answer_extraction("## The conversation so far\n\n")

        assert json.loads(reply)["fields"] == {}


class TestReadingAParagraph:
    """B065: one field per turn made the free path an interrogation."""

    def test_it_files_what_the_same_paragraph_plainly_said(self):
        asked = guide_for("purpose").question
        answer = "Guests book a table. No payments, and no accounts."

        reply = fields_of(answer_extraction(prompt(question=asked, answer=answer)))

        assert reply["purpose"]["value"] == answer  # the asked field keeps the whole answer
        assert "non_goals" in reply
        assert "No payments" in reply["non_goals"]["value"][0]

    def test_it_recognises_who_the_app_is_for(self):
        asked = guide_for("purpose").question
        answer = "A booking app. Guests book; staff see the day's list."

        reply = fields_of(answer_extraction(prompt(question=asked, answer=answer)))

        assert "users_and_roles" in reply

    def test_what_it_files_is_still_the_users_own_words(self):
        # The whole contract. A stand-in that paraphrased would produce a spec
        # whose provenance is a lie, which is worse than an empty field.
        asked = guide_for("purpose").question
        answer = "Guests book a table. No card payments at all."

        reply = fields_of(answer_extraction(prompt(question=asked, answer=answer)))

        assert reply["non_goals"]["value"] == ["No card payments at all"]
        assert reply["non_goals"]["provenance"] == ["m2"]

    def test_it_does_not_overwrite_a_field_that_is_already_filled(self):
        # A recorded field is the user's earlier answer, or their correction on
        # the review screen. A cue word in a later sentence must not replace it.
        asked = guide_for("purpose").question
        reply = fields_of(
            answer_extraction(
                prompt(
                    question=asked,
                    answer="Guests book a table. No payments.",
                    recorded="- non_goals = ['no deliveries'] (stated)",
                )
            )
        )

        assert "non_goals" not in reply

    def test_an_ordinary_sentence_fills_only_what_was_asked(self):
        # The failure to avoid is the opposite one: a stand-in that files
        # something under every field it can half-match produces a review screen
        # full of corrections, which is the screen that is supposed to be empty.
        asked = guide_for("purpose").question

        reply = fields_of(answer_extraction(prompt(question=asked, answer="A tool for my shop.")))

        assert list(reply) == ["purpose"]

    def test_the_first_clause_stays_where_it_was_asked_for(self):
        # Found by the first click-through: "Guests book a table at my bistro"
        # was filed under users_and_roles because it contains "Guest". The
        # person's own words, under a field they were not answering — exactly
        # the wrong-field correction this is meant to save them.
        asked = guide_for("purpose").question
        answer = "Guests book a table at my bistro. No payments."

        reply = fields_of(answer_extraction(prompt(question=asked, answer=answer)))

        assert "users_and_roles" not in reply
        assert reply["non_goals"]["value"] == ["No payments"]

    def test_a_clause_is_filed_without_the_word_joining_it_on(self):
        # "and no accounts" is not what anyone would write in that box.
        asked = guide_for("purpose").question
        answer = "Guests book a table, and no accounts to sign in with."

        reply = fields_of(answer_extraction(prompt(question=asked, answer=answer)))

        assert reply["sign_in"]["value"] == "no accounts to sign in with"

    def test_a_recognised_clause_is_marked_low_confidence(self):
        # It was recognised, not understood, and the review screen shows the
        # difference.
        asked = guide_for("purpose").question
        answer = "Guests book a table. No payments."

        reply = fields_of(answer_extraction(prompt(question=asked, answer=answer)))

        assert reply["non_goals"]["confidence"] == "low"
        assert reply["purpose"]["confidence"] == "medium"
