"""Gate 2's backend: a batch of markings in, a changed preview out.

Level 2 is "show me before you build it". The user gets a running preview,
marks things in it, writes what they want, and presses go — and only the parts
they touched are rebuilt.

The pieces:

- `markings` — what a batch is, and how it groups by package.
- `conflicts` — the markings that argue with the approved spec. Returned as a
  question, never quietly built.
- `restore` — going back to an earlier version, through the same guardrail.
- `change` — the guarded round trip: resolve strictly, detect conflicts, ask the
  model for new code for the affected packages only, then put it through the
  core's isolation and instrumentation guardrails before accepting it.

Everything that decides anything is already-built core code. This layer's job is
to take several markings at once and to refuse the ones it should not act on.
"""

from .change import (
    DesignChange,
    DesignChangeResult,
    PackageChange,
    apply_change,
    commit_change,
)
from .conflicts import Conflict, detect_conflicts
from .markings import ChangeBatch, Marking, MarkingOutcome, ResolvedBatch, resolve_batch
from .restore import RestoreResult, restore_version

__all__ = [
    "ChangeBatch",
    "Conflict",
    "DesignChange",
    "DesignChangeResult",
    "Marking",
    "MarkingOutcome",
    "PackageChange",
    "ResolvedBatch",
    "RestoreResult",
    "apply_change",
    "commit_change",
    "detect_conflicts",
    "resolve_batch",
    "restore_version",
]
