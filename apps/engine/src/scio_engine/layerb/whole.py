"""Output 1 of Layer B — "the whole" (docs/LAYER-B.md).

The coherent human narrative shown at the spec gate: the user's vision retold,
organised, gaps filled and flagged. This is the one part where judgment beats
rules, so it runs through the B031 relay — but grounded: the prompt carries only
what the spec actually says, and the model is told to organise, not invent.

Everything the model may add is flagged "assumed", and the assumed-field list
comes from Layer A's metadata, not from the model's own claim about itself.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from ..execution.provider import ProviderRegistry
from ..execution.relay import RelayOptions, run_relay
from ..intake.gate import assumed_fields
from ..intake.schema import CONDITIONAL_FIELDS, CORE_FIELDS, AppSpec, FieldMeta

WHOLE_SYSTEM = """You are Scio, articulating a user's project back to them.

Rules:
- Ground every sentence in the facts listed below. Do not invent features, \
entities, integrations or constraints that are not there.
- Organise and articulate better than the user did: connect the scattered facts \
into one coherent narrative, and make the unspoken explicit where the facts \
clearly imply it.
- Facts marked [assumed] are defaults we filled in, not things the user said. \
Where you rely on one, say so in plain language.
- Write 2-4 short paragraphs of plain prose, addressed to the user as "you". \
No headings, no bullet lists, no preamble.
- This is what the user will approve as their project's contract, so it must be \
accurate before it is elegant."""


class Whole(BaseModel):
    """The narrative plus the honest bookkeeping around it."""

    narrative: str
    assumptions: list[str] = Field(default_factory=list)
    grounding: dict[str, str] = Field(default_factory=dict)
    models_used: list[str] = Field(default_factory=list)
    generated: bool = True


def _format_value(field: FieldMeta) -> str:
    value = field.value
    if isinstance(value, list):
        return ", ".join(str(v) for v in value) if value else "(none)"
    if isinstance(value, BaseModel):
        return "; ".join(f"{k}={v}" for k, v in value.model_dump().items())
    return str(value)


def grounding_facts(spec: AppSpec) -> dict[str, str]:
    """The exact facts the prompt may use — the grounding set.

    Nothing outside this dict reaches the model, which is what makes "grounded
    only" enforceable rather than merely requested.
    """
    facts: dict[str, str] = {}
    names = [*CORE_FIELDS, *CONDITIONAL_FIELDS, "non_goals", "platform", "look", "publishing"]
    for name in names:
        field = getattr(spec, name, None)
        if isinstance(field, FieldMeta):
            marker = " [assumed]" if field.is_assumed else ""
            facts[name] = f"{_format_value(field)}{marker}"
    return facts


def build_prompt(spec: AppSpec) -> str:
    facts = grounding_facts(spec)
    lines = ["Here are the facts about the project:", ""]
    lines += [f"- {name.replace('_', ' ')}: {value}" for name, value in facts.items()]
    lines += [
        "",
        "Write the whole: tell this project back to the user as one coherent story.",
    ]
    return "\n".join(lines)


def fallback_narrative(spec: AppSpec) -> str:
    """A deterministic, honest narrative for when no model is available.

    Plainer than the generated version, but never wrong — it only restates facts.
    """
    purpose = spec.purpose.value if spec.purpose else "an app"
    users = ", ".join(spec.users_and_roles.value) if spec.users_and_roles else "its users"
    actions = ", ".join(spec.key_actions.value) if spec.key_actions else "its core actions"
    entities = ", ".join(spec.entities.value) if spec.entities else "its data"
    sign_in = spec.sign_in.value if spec.sign_in else "not decided"

    text = (
        f"You're building {purpose} It is for {users}, and the things it manages are "
        f"{entities}. The people using it can {actions}. Signing in works like this: "
        f"{sign_in}."
    )
    if spec.non_goals and spec.non_goals.value:
        text += f" You've deliberately left out: {', '.join(spec.non_goals.value)}."
    return text


async def generate_whole(
    spec: AppSpec,
    *,
    registry: ProviderRegistry,
    passes: int = 2,
) -> Whole:
    """Generate the whole through the relay (B031) — never a direct model call.

    Two passes by default: draft then review. The whole is short and high-stakes
    rather than long and expensive, so the full four-pass relay isn't warranted.
    If every pass fails, we fall back to the deterministic narrative rather than
    leaving the spec gate with nothing to approve.
    """
    facts = grounding_facts(spec)
    prompt = build_prompt(spec)

    try:
        result = await run_relay(
            "architecture",
            prompt,
            registry=registry,
            options=RelayOptions(passes=passes, system=WHOLE_SYSTEM, temperature=0.3),
        )
        return Whole(
            narrative=result.final_text,
            assumptions=assumed_fields(spec),
            grounding=facts,
            models_used=result.models,
            generated=True,
        )
    except Exception:
        return Whole(
            narrative=fallback_narrative(spec),
            assumptions=assumed_fields(spec),
            grounding=facts,
            models_used=[],
            generated=False,
        )
