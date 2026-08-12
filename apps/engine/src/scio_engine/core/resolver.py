"""GUARDRAIL 2 — marking -> package, or a loud error. Never a guess.

The spike's exact bug: an element lost its id, the click walked up to the nearest
instrumented ancestor, and the resolver returned `pkg_foundation` with full
confidence. The user had marked a button; a directed change would have rewritten
the app shell.

So this resolver is strict. The element under the pointer must carry its own id.
If it does not, we raise — and the error names the ancestor we *could* have
resolved to, because that ancestor is the evidence that instrumentation is
missing exactly there.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .instrumentation import ID_ATTRIBUTE, Manifest, SourceLocation


@dataclass
class ElementHit:
    """What the browser found under the pointer.

    `ancestor_id` is diagnostic only: it is what a permissive resolver would have
    (wrongly) used, and naming it makes the failure actionable instead of blank.
    """

    scio_id: str | None
    scio_package: str | None
    tag: str = ""
    text: str = ""
    ancestor_id: str | None = None
    ancestor_package: str | None = None
    ancestor_distance: int = 0


class MarkingResolutionError(RuntimeError):
    """A marking could not be resolved safely. Never downgrade this to a guess."""


@dataclass
class ResolvedMarking:
    """A marking tied to exactly one package and source location."""

    scio_id: str
    location: SourceLocation
    hit: ElementHit = field(default_factory=lambda: ElementHit(None, None))

    @property
    def package(self) -> str:
        return self.location.package


def resolve_marking(hit: ElementHit, manifest: Manifest) -> ResolvedMarking:
    """Turn a click into a package + source location, or raise.

    Three failure modes, three distinct messages — the design window shows these
    to a human, and "something went wrong" would waste their time.
    """
    if hit.scio_id is None:
        if hit.ancestor_id is not None:
            raise MarkingResolutionError(
                f"The element you marked (<{hit.tag or '?'}>) has no {ID_ATTRIBUTE}. "
                f"Its ancestor '{hit.ancestor_id}' does "
                f"(package {hit.ancestor_package or 'unknown'}), but resolving to an ancestor "
                "would target the wrong part of the app — the spike proved this rewrites the "
                "shell instead of the marked element. This element needs instrumentation."
            )
        raise MarkingResolutionError(
            f"The element you marked (<{hit.tag or '?'}>) has no {ID_ATTRIBUTE}, and neither "
            "does anything above it. This part of the app was generated without "
            "instrumentation and cannot be addressed."
        )

    location = manifest.resolve(hit.scio_id)
    if location is None:
        raise MarkingResolutionError(
            f"'{hit.scio_id}' is not in the manifest. The code and the manifest have drifted — "
            "regenerate the manifest from source before marking anything here."
        )

    # The DOM and the manifest must agree about ownership. Disagreement means one
    # of them is stale, and acting on either would be a coin flip.
    if hit.scio_package and hit.scio_package != location.package:
        raise MarkingResolutionError(
            f"'{hit.scio_id}' claims package '{hit.scio_package}' in the running app but "
            f"'{location.package}' in the manifest. Refusing to guess which is current."
        )

    return ResolvedMarking(scio_id=hit.scio_id, location=location, hit=hit)


# Returns the element under the point AND, separately, the nearest instrumented
# ancestor. Keeping them apart in the browser is what lets Python be strict:
# the ancestor is evidence for the error message, never a fallback answer.
RESOLVE_AT_POINT_JS = f"""
([x, y]) => {{
  const node = document.elementFromPoint(x, y);
  if (!node) return null;

  let ancestor = node.parentElement;
  let distance = 1;
  while (ancestor && !ancestor.getAttribute('{ID_ATTRIBUTE}')) {{
    ancestor = ancestor.parentElement;
    distance += 1;
  }}

  return {{
    scio_id: node.getAttribute('{ID_ATTRIBUTE}'),
    scio_package: node.getAttribute('data-scio-package'),
    tag: node.tagName.toLowerCase(),
    text: (node.innerText || '').trim().slice(0, 80),
    ancestor_id: ancestor ? ancestor.getAttribute('{ID_ATTRIBUTE}') : null,
    ancestor_package: ancestor ? ancestor.getAttribute('data-scio-package') : null,
    ancestor_distance: ancestor ? distance : 0,
  }};
}}
"""
