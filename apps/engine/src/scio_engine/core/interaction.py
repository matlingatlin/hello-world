"""Driving the app: fill, submit, reload — and checking what survived.

The vision loop could see that a page rendered. It could not see that pressing
the button did anything, so Layer C had to mark "works end to end and persists"
as unobservable (B054) and nobody checked the one thing the user actually cares
about. With the app running against real data (B060a), that changes: a criterion
can now be a short script, and "it works" becomes something a build passes or
fails on.

The vocabulary is deliberately tiny and declarative:

    fill(booking-form-name, "Ada")      type into the element with that id
    click(booking-form-submit)          press it
    reload(/booking)                    a NEW page load, not a re-render
    assert_present(booking-row-*)       something matching is on the page
    assert_absent(...)                  it is not
    assert_row(bookings, {...})         and it is really in the database

Two properties make it worth having. It targets `data-scio-id`, which every
element is guaranteed to carry (B040), so a script never depends on a class name
or the order of the DOM. And `reload` is a real navigation — the difference
between "React still has it in state" and "it was saved", which is the whole
question.

One concession: every element is guaranteed to *have* an id, but the exact id is
the builder's to choose. The seed catalog's booking form calls the `guest_name`
field `booking-form-name`, and failing a correct app over that would be the
spurious failure B054 exists to prevent. So a step may carry a `fallback`
selector — used only when the id is not on the page — and the derived scripts
fall back to the form field's `name` attribute, which the schema fixes.

`assert_row` goes through the app's own process rather than opening the database
directly: pglite is single-writer, and a second reader would be the corruption
the spike warned about.
"""

from __future__ import annotations

import re
from enum import StrEnum

from pydantic import BaseModel, Field


class Action(StrEnum):
    fill = "fill"
    click = "click"
    reload = "reload"
    assert_present = "assert_present"
    assert_absent = "assert_absent"
    assert_row = "assert_row"
    as_user = "as_user"


class Step(BaseModel):
    """One instruction. `target` is a data-scio-id unless the action says otherwise."""

    action: Action
    target: str = ""
    value: str = ""
    match: dict[str, str] = Field(default_factory=dict)
    text: str = ""
    fallback: str = Field(
        default="",
        description="A raw CSS selector, used only when the data-scio-id is not on the page",
    )

    def describe(self) -> str:
        if self.action is Action.fill:
            return f'fill {self.target} with "{self.value}"'
        if self.action is Action.click:
            return f"click {self.target}"
        if self.action is Action.reload:
            return f"reload {self.target or '/'}"
        if self.action is Action.as_user:
            return f"act as {self.value or 'anonymous'}"
        if self.action is Action.assert_row:
            return f"expect a row in {self.target} matching {self.match}"
        subject = self.text or self.target
        verb = "present" if self.action is Action.assert_present else "absent"
        return f"expect {subject} {verb}"


def fill(target: str, value: str, *, fallback: str = "") -> Step:
    return Step(action=Action.fill, target=target, value=value, fallback=fallback)


def click(target: str, *, fallback: str = "") -> Step:
    return Step(action=Action.click, target=target, fallback=fallback)


def reload(route: str = "/") -> Step:
    return Step(action=Action.reload, target=route)


def assert_present(target: str = "", *, text: str = "") -> Step:
    return Step(action=Action.assert_present, target=target, text=text)


def assert_absent(target: str = "", *, text: str = "") -> Step:
    return Step(action=Action.assert_absent, target=target, text=text)


def assert_row(table: str, match: dict[str, str]) -> Step:
    return Step(action=Action.assert_row, target=table, match=match)


def as_user(user_id: str) -> Step:
    """Act as this user for what follows — the claim the RLS policies read."""
    return Step(action=Action.as_user, value=user_id)


class Script(BaseModel):
    """A named sequence — one criterion's worth of interaction."""

    name: str
    steps: list[Step] = Field(default_factory=list)
    route: str = "/"

    def describe(self) -> str:
        return " → ".join(step.describe() for step in self.steps)


class StepResult(BaseModel):
    step: Step
    ok: bool
    detail: str = ""


class ScriptResult(BaseModel):
    """What running it proved, and where it stopped if it did."""

    name: str
    passed: bool
    steps: list[StepResult] = Field(default_factory=list)
    error: str = ""

    @property
    def failure(self) -> str:
        """One line a repair prompt can act on — what was tried, what happened."""
        if self.passed:
            return ""
        failed = next((s for s in self.steps if not s.ok), None)
        if failed is None:
            return f"{self.name}: {self.error or 'did not complete'}"
        return f"{self.name}: could not {failed.step.describe()} — {failed.detail}"


def selector_for(target: str) -> str:
    """A data-scio-id, as a CSS selector.

    Loop-rendered ids are patterns (`booking-row-*`), so they become a prefix
    match — the id of a row nobody can predict is still addressable.
    """
    if target.endswith("*"):
        return f'[data-scio-id^="{target[:-1]}"]'
    return f'[data-scio-id="{target}"]'


def selectors_for(step: Step) -> list[str]:
    """What to try, in order of authority: the id first, the fallback only if
    the id is not there at all."""
    return [s for s in (selector_for(step.target) if step.target else "", step.fallback) if s]


_TEMPLATE = re.compile(r"\{\{(\w+)\}\}")


def resolve(script: Script, values: dict[str, str]) -> Script:
    """Fill `{{placeholders}}` in a script — the unique name a run invents, say.

    Keeps a criterion's script reusable across runs without it having to carry a
    timestamp that would make two builds of the same app differ.
    """
    def swap(text: str) -> str:
        return _TEMPLATE.sub(lambda m: values.get(m.group(1), m.group(0)), text)

    return Script(
        name=script.name,
        route=swap(script.route),
        steps=[
            step.model_copy(
                update={
                    "target": swap(step.target),
                    "value": swap(step.value),
                    "text": swap(step.text),
                    "match": {k: swap(v) for k, v in step.match.items()},
                }
            )
            for step in script.steps
        ],
    )
