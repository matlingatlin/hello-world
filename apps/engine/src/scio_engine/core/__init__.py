"""The shared core: sandbox + marking->code coupling.

Gates 2 (preview) and 3 (build) both run on this. Three guardrails, each proven
necessary by spikes/sandbox-marking:

1. `verifier`  — a regeneration that loses an id is a FAILED build.
2. `resolver`  — a marking resolves exactly, or errors. It never climbs to a
                 parent and guesses (that bug would rewrite the app shell).
3. `console`   — console output is classified by source before the vision loop
                 judges it, so a favicon 404 is not read as a broken build.
"""

from .console import ConsoleEntry, ConsoleReport, classify_console
from .instrumentation import INSTRUMENTATION_RULES, Manifest, SourceLocation
from .manifest_builder import build_manifest
from .persistence import CouplingRecord, ManifestStore, ProjectCoupling
from .regenerate import (
    ChangeRequest,
    IsolationViolation,
    MechanicalRegenerator,
    PackageRegenerator,
    directed_regenerate,
    regenerate_or_raise,
    snapshot,
    verify_isolation,
)
from .resolver import ElementHit, MarkingResolutionError, resolve_marking
from .sandbox import (
    LocalDockerSandbox,
    LocalProcessSandbox,
    SandboxError,
    SandboxHandle,
    SandboxProvider,
    choose_sandbox,
)
from .verifier import InstrumentationError, ids_in_source, verify_instrumentation

__all__ = [
    "INSTRUMENTATION_RULES",
    "ChangeRequest",
    "ConsoleEntry",
    "ConsoleReport",
    "CouplingRecord",
    "ElementHit",
    "InstrumentationError",
    "IsolationViolation",
    "LocalDockerSandbox",
    "LocalProcessSandbox",
    "Manifest",
    "ManifestStore",
    "MarkingResolutionError",
    "MechanicalRegenerator",
    "PackageRegenerator",
    "ProjectCoupling",
    "SandboxError",
    "SandboxHandle",
    "SandboxProvider",
    "SourceLocation",
    "build_manifest",
    "choose_sandbox",
    "classify_console",
    "directed_regenerate",
    "ids_in_source",
    "regenerate_or_raise",
    "resolve_marking",
    "snapshot",
    "verify_instrumentation",
    "verify_isolation",
]
