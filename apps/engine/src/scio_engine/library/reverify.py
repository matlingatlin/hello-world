"""Does the generalized entry still work?

Generalization rewrites code. A rename that is 99% right leaves an import
pointing at a file that no longer exists, or an id that no longer matches its
label — and because an entry is offered *instead of* generating, that breakage
would be inherited by every project that assembles it, silently, for as long as
the entry lives.

So nothing is added on the strength of having been generalized. The entry is
adapted to a **sample entity it has never seen** — deliberately not the project's
own, because adapting back to `booking` would pass even if the generalization
had done nothing at all — and then put through the checks that a generated
package has to pass:

- every planned file lands, and none of them is empty;
- no placeholder survives into the output (`__ENTITY`, `__TOKEN_`): the app
  would render the placeholder and the build would be a lie;
- the instrumentation verifies, using the same `core/verifier` every build uses;
- the static validation agents pass (security, code quality, imports that
  resolve) — the same ones the vision loop runs;
- the contract of the adapted files still equals the entry's own contract, so a
  rename that quietly moved a file cannot slip through.

What this deliberately does NOT do is install npm and run `next build` per
contribution. That is minutes and hundreds of megabytes for every package of
every build, and it checks something the build has *already* checked: this exact
code, in this exact stack, ran and passed its vision loop moments ago. What
generalization can break is the rename, and the rename is what is checked here.
"""

from __future__ import annotations

import re
import tempfile
from pathlib import Path

from pydantic import BaseModel, Field

from ..builder.validation import Severity, check_code_quality, check_security
from ..core.manifest_builder import build_manifest
from ..core.stamping import stamp_files
from ..core.verifier import verify_instrumentation
from .entry import CatalogEntry
from .identity import Contract
from .placeholders import ENTITY, TOKEN_PREFIX

_UI_SUFFIXES = (".tsx", ".jsx")

SAMPLE_ENTITY = "widget"
"""What a re-verification adapts to.

Not the contributing project's own entity, and not anything in the seed
vocabulary: adapting `booking` code back to `booking` would pass even if
generalization had done nothing, which is precisely the failure being looked
for."""

_LEFTOVER = re.compile(rf"{re.escape(ENTITY[:8])}|{re.escape(TOKEN_PREFIX)}")


class ReverifyResult(BaseModel):
    """Whether the generalized entry survives being used by somebody else."""

    ok: bool = False
    entity: str = SAMPLE_ENTITY
    files: list[str] = Field(default_factory=list)
    problems: list[str] = Field(default_factory=list)

    def explain(self) -> str:
        if self.ok:
            return f"re-verified against '{self.entity}'"
        return "did not re-verify:\n" + "\n".join(f"  - {p}" for p in self.problems)


def reverify(
    entry: CatalogEntry,
    *,
    entity: str = SAMPLE_ENTITY,
    package_id: str = "pkg_library_reverify",
) -> ReverifyResult:
    """Adapt, write, and check. Deterministic — no model, no network."""
    result = ReverifyResult(entity=entity)

    try:
        adapted = entry.adapt(entity)
    except Exception as exc:  # a template that cannot even be substituted
        result.problems.append(f"could not be adapted: {type(exc).__name__}: {exc}")
        return result

    if not adapted:
        result.problems.append("it writes no files")
        return result

    result.files = sorted(adapted)

    for path, body in sorted(adapted.items()):
        if not body.strip():
            result.problems.append(f"{path} is empty after adaptation")
        if _LEFTOVER.search(body) or _LEFTOVER.search(path):
            # A surviving placeholder ships to the user as literal text.
            result.problems.append(f"{path} still contains a placeholder after adaptation")

    # The same contract, still. A rename that moved a file would change it, and
    # the matcher would then assemble something whose files are not its plan.
    before = entry.effective_contract()
    after = Contract.of(
        operations=list(entry.provides.operations),
        routes=list(entry.provides.routes),
        files=list(adapted),
        entity=entity,
    )
    if set(before.files) != set(after.files):
        result.problems.append(
            "adapting moved files: "
            f"{sorted(set(after.files) ^ set(before.files))} — the file plan would not match"
        )

    stamped = stamp_files(adapted, package_id)
    findings = [
        *check_security(stamped),
        *check_code_quality(stamped),
    ]
    for finding in findings:
        if finding.severity is Severity.error:
            result.problems.append(f"[{finding.agent.value}] {finding.message}")

    with tempfile.TemporaryDirectory(prefix="scio-reverify-") as tmp:
        app_dir = Path(tmp)
        for relative, content in stamped.items():
            target = app_dir / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)

        manifest = build_manifest(app_dir, {package_id: sorted(stamped)})
        report = verify_instrumentation(app_dir, manifest)
        renders_ui = any(path.endswith(_UI_SUFFIXES) for path in adapted)
        for issue in report.errors:
            if issue.rule == "has_instrumentation" and not renders_ui:
                # "Nothing here could be marked" is a statement about a whole
                # APP. An entry that is server code — an auth helper, a data
                # module — has no elements by nature, and requiring ids of it
                # would mean the library could only ever learn UI.
                continue
            result.problems.append(f"[instrumentation] {issue.message}")

        if entry.element_ids and not manifest.elements:
            result.problems.append(
                "it declares element ids but none of them are in the adapted source"
            )

    result.ok = not result.problems
    return result
