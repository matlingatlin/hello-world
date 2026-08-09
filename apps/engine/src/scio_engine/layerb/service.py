"""Layer B end to end: AppSpec -> { whole, architecture, playbook, validation }.

Order matters. The deterministic backbone is derived first and validated before
the LLM is asked for anything, so a design error costs a function call rather
than a relay run (docs/LAYER-B.md, "Validate the architecture before generating").
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from ..execution.provider import ProviderRegistry
from ..intake.gate import BuildableResult, is_buildable
from ..intake.schema import AppSpec
from .architecture import Architecture
from .derive import derive_architecture
from .playbook import BuildContext, Playbook, assemble_build_context, default_playbook
from .validate import ValidationResult, validate_architecture
from .whole import Whole, generate_whole


class NotBuildableError(ValueError):
    """Raised when Layer B is asked to run on a spec that hasn't passed the gate."""

    def __init__(self, result: BuildableResult) -> None:
        self.result = result
        super().__init__("Spec is not buildable yet")


class LayerBResult(BaseModel):
    whole: Whole
    architecture: Architecture
    playbook: Playbook
    validation: ValidationResult
    build_context: BuildContext
    revisit_fields: list[str] = Field(
        default_factory=list,
        description="Spec fields to reopen in the wizard, surgically, when validation fails",
    )


async def run_layer_b(
    spec: AppSpec,
    *,
    registry: ProviderRegistry,
    whole_passes: int = 2,
    playbook: Playbook | None = None,
) -> LayerBResult:
    """Run Layer B. Raises NotBuildableError if Layer A's gate hasn't opened."""
    gate = is_buildable(spec)
    if not gate.buildable:
        raise NotBuildableError(gate)

    architecture = derive_architecture(spec)
    validation = validate_architecture(architecture)

    whole = await generate_whole(spec, registry=registry, passes=whole_passes)
    book = playbook or default_playbook()
    context = assemble_build_context(architecture, whole=whole.narrative, playbook=book)

    return LayerBResult(
        whole=whole,
        architecture=architecture,
        playbook=book,
        validation=validation,
        build_context=context,
        revisit_fields=validation.fields_to_revisit,
    )
