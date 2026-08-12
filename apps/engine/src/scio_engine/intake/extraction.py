"""Conversation -> typed AppSpec. Gate 1's first half.

The model reads the conversation and proposes field values. It does not get to
decide whether they are kept: every proposal is checked here, against rules a
prompt cannot enforce.

The rule that matters most is grounding. An extractor that invents a plausible
answer is worse than one that leaves a slot empty, because an empty slot becomes
a question and an invented one becomes an app the user never asked for. So a
value claimed as *stated* must cite a real user message; if it cannot, it is
dropped. An inference is allowed, but only as `derived`, only into an empty slot,
and never over something the user actually said.
"""

from __future__ import annotations

import json
import re
from typing import Any

from pydantic import BaseModel, Field

from ..execution.provider import ProviderRegistry
from ..execution.relay import RelayOptions, run_relay
from ..layerb.vocabulary import canonical_name
from .conversation import Conversation
from .fields import EXTRACTABLE_FIELDS, field_catalogue, guide_for, signal_catalogue
from .schema import AppSpec, Confidence, DataSensitivity, FieldMeta, Source

EXTRACTION_SYSTEM = f"""You are Scio's intake extractor. You turn what a person said \
about the app they want into typed fields. You do not design anything and you do not \
ask anything — you only record what is there.

Answer with JSON only, in exactly this shape:

{{"fields": {{"<field>": {{"value": <value>,
                         "source": "stated" | "derived",
                         "confidence": "low" | "medium" | "high",
                         "provenance": ["<message id>", ...]}}}},
 "signals": {{"<signal>": true|false}}}}

The fields you may fill:
{field_catalogue()}

The signals (set one true when the conversation implies it):
{signal_catalogue()}

Rules — these decide whether your answer is kept:
- NEVER invent. If the person has not said something, leave the field out entirely. \
An empty field becomes a question; a wrong field becomes the wrong app.
- "stated" means the person said it. Cite the message id(s) it came from in `provenance`. \
A stated field without real provenance is discarded.
- "derived" means you concluded it from what they said. Use it sparingly, and cite the \
messages it follows from.
- Only include a field when this conversation adds or changes something. Do not repeat \
fields that are already filled and unchanged.
- Use the person's own words. Do not translate, tidy or rename their terms.
- Answer with the JSON object and nothing else."""


class Rejection(BaseModel):
    """A proposed value that did not survive the checks, and why.

    Kept and returned rather than swallowed: a silent drop looks identical to a
    model that said nothing, and the two need different fixes.
    """

    field: str
    reason: str


class ExtractionReport(BaseModel):
    updated: list[str] = Field(default_factory=list)
    rejected: list[Rejection] = Field(default_factory=list)
    signals_set: list[str] = Field(default_factory=list)
    parsed: bool = True
    raw: str = ""


def _extract_json(text: str) -> dict | None:
    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    candidate = fenced.group(1) if fenced else None
    if candidate is None:
        start, end = text.find("{"), text.rfind("}")
        candidate = text[start : end + 1] if start != -1 and end > start else None
    if candidate is None:
        return None
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


_PLACEHOLDERS = {"", "unknown", "n/a", "na", "none", "tbd", "not stated", "null"}


def _clean_text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return None if text.lower() in _PLACEHOLDERS else text


def _clean_list(value: Any) -> list[str] | None:
    """A list of short, non-empty strings. A bare string is accepted as one item —
    models do that constantly, and refusing it would lose real answers."""
    if isinstance(value, str):
        cleaned = _clean_text(value)
        return [cleaned] if cleaned else None
    if not isinstance(value, list):
        return None
    items = [t for t in (_clean_text(v) for v in value) if t]
    return items or None


def _clean_sensitivity(value: Any) -> DataSensitivity | None:
    if isinstance(value, dict):
        try:
            return DataSensitivity.model_validate(value)
        except ValueError:
            return None
    return None


def _coerce(field: str, value: Any) -> Any | None:
    kind = guide_for(field).kind
    if kind == "text":
        return _clean_text(value)
    if kind == "list":
        return _clean_list(value)
    return _clean_sensitivity(value)


def _merge_list(existing: list[str], incoming: list[str]) -> list[str]:
    """Add what is new, keeping the user's own wording.

    De-duplication goes through Layer B's canonical vocabulary, so "reservations"
    is recognised as the "bookings" already in the spec instead of being added
    beside it. The stored term stays the one the user actually used — Layer A
    records what was said; Layer B is where naming is decided.
    """
    merged = list(existing)
    seen = {canonical_name(term) for term in existing}
    for term in incoming:
        key = canonical_name(term)
        if key and key not in seen:
            merged.append(term)
            seen.add(key)
    return merged


def apply_extraction(
    spec: AppSpec, data: dict, *, evidence_ids: set[str]
) -> tuple[AppSpec, ExtractionReport]:
    """Fold a proposal into the spec, keeping only what survives the rules."""
    report = ExtractionReport(raw=json.dumps(data)[:2000])
    fields = data.get("fields")
    if not isinstance(fields, dict):
        fields = {}

    for name, proposal in fields.items():
        if name not in EXTRACTABLE_FIELDS:
            report.rejected.append(Rejection(field=str(name), reason="not an intake field"))
            continue
        if not isinstance(proposal, dict):
            report.rejected.append(Rejection(field=name, reason="not a field object"))
            continue

        value = _coerce(name, proposal.get("value"))
        if value is None:
            report.rejected.append(
                Rejection(field=name, reason="no usable value — left empty so it gets asked")
            )
            continue

        source = _source_of(proposal)
        provenance = [
            str(m) for m in proposal.get("provenance", []) if str(m) in evidence_ids
        ]

        if source is Source.stated and not provenance:
            # THE grounding rule: claimed as said, but traceable to nothing said.
            report.rejected.append(
                Rejection(
                    field=name,
                    reason="claimed as stated but cites no message the user actually sent",
                )
            )
            continue

        current = getattr(spec, name)
        if source is Source.derived and current is not None and current.source is Source.stated:
            report.rejected.append(
                Rejection(
                    field=name,
                    reason="an inference may not overwrite what the user stated",
                )
            )
            continue

        if guide_for(name).kind == "list" and current is not None:
            value = _merge_list(current.value, value)

        setattr(
            spec,
            name,
            FieldMeta(
                value=value,
                source=source,
                confidence=_confidence_of(proposal, source),
                provenance=provenance,
            ),
        )
        report.updated.append(name)

    _apply_signals(spec, data.get("signals"), report)
    # Round-trip: the field checks above are per-value; this proves the whole
    # spec is still the shape the rest of the engine expects.
    return AppSpec.model_validate(spec.model_dump()), report


def _source_of(proposal: dict) -> Source:
    raw = str(proposal.get("source", "stated")).lower()
    return Source.derived if raw == "derived" else Source.stated


def _confidence_of(proposal: dict, source: Source) -> Confidence:
    raw = str(proposal.get("confidence", "medium")).lower()
    confidence = {
        "low": Confidence.low,
        "medium": Confidence.medium,
        "high": Confidence.high,
    }.get(raw, Confidence.medium)
    if source is Source.derived and confidence is Confidence.high:
        # An inference is never "high": it is our reading, not their words.
        return Confidence.medium
    return confidence


def _apply_signals(spec: AppSpec, signals: Any, report: ExtractionReport) -> None:
    """Signals only ever open a follow-up question.

    So a wrong one costs a question the user can wave away, while a missed one
    costs a whole area of the app. That asymmetry is why they are taken at face
    value and only ever turned on here.
    """
    if not isinstance(signals, dict):
        return
    for name, value in signals.items():
        if not hasattr(spec.signals, str(name)) or value is not True:
            continue
        setattr(spec.signals, str(name), True)
        report.signals_set.append(str(name))


def build_extraction_prompt(conversation: Conversation, spec: AppSpec) -> str:
    filled = _filled_summary(spec)
    return (
        "## The conversation so far\n"
        f"{conversation.as_prompt()}\n\n"
        "## Already recorded (do not repeat unless it changed)\n"
        f"{filled or '(nothing yet)'}\n\n"
        "Record what this conversation says about the app. Leave out anything the "
        "person has not actually told you."
    )


def _filled_summary(spec: AppSpec) -> str:
    lines = []
    for name in EXTRACTABLE_FIELDS:
        field = getattr(spec, name)
        if field is not None:
            lines.append(f"- {name} = {field.value!r} ({field.source})")
    return "\n".join(lines)


async def extract(
    conversation: Conversation,
    spec: AppSpec,
    *,
    registry: ProviderRegistry,
    passes: int = 2,
) -> tuple[AppSpec, ExtractionReport]:
    """Run extraction through the relay and fold the result in.

    Two passes by default: the second is the same best model reviewing its own
    reading of the conversation, which is where over-eager extraction gets caught.
    An unusable reply changes nothing — the spec stands and the wizard asks again.
    """
    prompt = build_extraction_prompt(conversation, spec)
    try:
        result = await run_relay(
            "spec_extraction",
            prompt,
            registry=registry,
            options=RelayOptions(passes=passes, system=EXTRACTION_SYSTEM, temperature=0.0),
        )
    except Exception as exc:  # provider/budget failures must not lose the spec
        return spec, ExtractionReport(
            parsed=False,
            rejected=[Rejection(field="*", reason=f"extraction could not run: {exc}")],
        )

    data = _extract_json(result.final_text)
    if data is None:
        return spec, ExtractionReport(
            parsed=False,
            raw=result.final_text[:2000],
            rejected=[Rejection(field="*", reason="the reply was not usable JSON")],
        )
    return apply_extraction(spec, data, evidence_ids=conversation.evidence_ids)
