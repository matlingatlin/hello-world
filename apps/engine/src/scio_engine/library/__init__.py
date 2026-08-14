"""The component library — curated parts an app is assembled from (ADR-0014).

Match -> fetch -> adapt -> assemble, with generation as the fallback rather than
the default. See docs/LIBRARY.md.
"""

from .assembler import AssemblyError, assemble_package
from .catalog import Catalog, default_catalog, load_catalog
from .entry import CatalogEntry, Layer, Quality
from .gate import Candidate, GateResult, propose, review
from .matcher import Decision, Match, MatchReport, apply_matches, match_plan

__all__ = [
    "AssemblyError",
    "Candidate",
    "Catalog",
    "CatalogEntry",
    "Decision",
    "GateResult",
    "Layer",
    "Match",
    "MatchReport",
    "Quality",
    "apply_matches",
    "assemble_package",
    "default_catalog",
    "load_catalog",
    "match_plan",
    "propose",
    "review",
]
