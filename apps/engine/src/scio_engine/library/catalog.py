"""The catalog — every entry the library currently knows.

Seed entries live in the repo (`library/catalog/<id>/`) so they are reviewed like
code and versioned with it. A database-backed catalog is the later step; nothing
above this module needs to know which it is talking to, which is the point of
keeping the lookup behind these functions.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from .entry import CatalogEntry, Layer

CATALOG_DIR_ENV = "SCIO_CATALOG_DIR"
SEED_DIR = Path(__file__).resolve().parent / "catalog"


class Catalog:
    """A set of entries, indexed the way the matcher asks for them."""

    def __init__(self, entries: list[CatalogEntry]) -> None:
        self.entries = entries

    def __len__(self) -> int:
        return len(self.entries)

    def get(self, entry_id: str) -> CatalogEntry | None:
        return next((e for e in self.entries if e.id == entry_id), None)

    def by_layer(self, layer: Layer) -> list[CatalogEntry]:
        return [e for e in self.entries if e.layer is layer]

    def offerable(self, layer: Layer | None = None) -> list[CatalogEntry]:
        """Entries the matcher may propose: vetted, and carrying files.

        An unvetted entry is deliberately invisible rather than merely
        deprioritised — reaching for it would spend the library's whole promise
        (curated, tested, secure) to save one generation.
        """
        pool = self.by_layer(layer) if layer else self.entries
        return [e for e in pool if e.offerable]


def load_catalog(directory: Path | None = None) -> Catalog:
    root = Path(directory) if directory else catalog_dir()
    if not root.exists():
        return Catalog([])
    entries = [
        CatalogEntry.load(child)
        for child in sorted(root.iterdir())
        if child.is_dir() and (child / "entry.json").exists()
    ]
    return Catalog(entries)


def catalog_dir() -> Path:
    configured = os.getenv(CATALOG_DIR_ENV, "")
    return Path(configured).expanduser().resolve() if configured else SEED_DIR


@lru_cache(maxsize=1)
def _cached_seed() -> Catalog:
    return load_catalog(SEED_DIR)


def default_catalog() -> Catalog:
    """The shipped catalog, cached — unless an operator points elsewhere.

    Cached because the seed entries are read-only files that cannot change while
    the process runs; an operator-supplied directory is read fresh, since that
    one is being edited.
    """
    if os.getenv(CATALOG_DIR_ENV, ""):
        return load_catalog(catalog_dir())
    return _cached_seed()
