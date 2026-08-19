"""The component library — curated parts an app is assembled from (ADR-0014).

Two directions, and the library is only worth having with both (B061):

**Search** — before the build, does the library already know how to do this?
The category narrows, the contract decides, and a hit is assembled with no model
involved at all (`matcher`, `assembler`).

**Contribute** — after the build, is any of this worth keeping? What came from
the library is skipped; what passed every build gate is generalized, re-verified
against an entity it has never seen, put through the gate, and either added
under a store-assigned id or discarded as no better than what is already there
(`contribute`, `generalize`, `reverify`, `store`).

Match -> fetch -> adapt -> assemble, with generation as the fallback rather than
the default. See docs/LIBRARY.md.
"""

from .assembler import AssemblyError, assemble_package
from .catalog import Catalog, default_catalog, load_catalog
from .categories import Category, CategoryRegistry, default_registry
from .contribute import ContributionReport, Outcome, contribute_build, contribute_package
from .entry import CatalogEntry, Layer, Quality
from .gate import Candidate, GateResult, propose, review
from .identity import Contract, EntryId, Status
from .matcher import Decision, Match, MatchReport, apply_matches, match_plan
from .reverify import ReverifyResult, reverify
from .store import (
    CatalogStore,
    FileCatalogStore,
    PostgresCatalogStore,
    default_store,
    set_store,
)

__all__ = [
    "AssemblyError",
    "Candidate",
    "Catalog",
    "CatalogEntry",
    "CatalogStore",
    "Category",
    "CategoryRegistry",
    "Contract",
    "ContributionReport",
    "Decision",
    "EntryId",
    "FileCatalogStore",
    "GateResult",
    "Layer",
    "Match",
    "MatchReport",
    "Outcome",
    "PostgresCatalogStore",
    "Quality",
    "ReverifyResult",
    "Status",
    "apply_matches",
    "assemble_package",
    "contribute_build",
    "contribute_package",
    "default_catalog",
    "default_registry",
    "default_store",
    "load_catalog",
    "match_plan",
    "propose",
    "review",
    "reverify",
    "set_store",
]
