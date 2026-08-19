"""Where the library actually lives — and who hands out the numbers.

The first slice read entries from a directory in the repo. That is right for
seeds, which are reviewed like code, and wrong for anything learned from a
build: two builds finishing at the same moment would both decide they were
`booking.2`, and a file tree has no way to stop them.

So there are two stores behind one interface:

- **`FileCatalogStore`** — the seed directory. Read-only in practice, and the
  fallback when no database is configured, so the engine still runs, still
  matches and still assembles with nothing but a checkout.
- **`PostgresCatalogStore`** — where contributions go. It owns a handful of
  `library_*` tables, created idempotently on first use, in the same database
  the product uses but emphatically NOT in Prisma's care: Prisma owns the
  product's schema (ADR-0007/0009), the engine owns the library's, and neither
  migrates the other's tables.

The one genuinely hard requirement is the sequence number. `next_seqno` takes a
row lock on the category before reading its high-water mark, so two builds
contributing to `booking` at the same instant get 2 and 3 rather than 2 and 2.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Protocol

from .catalog import Catalog, load_catalog
from .categories import CategoryRegistry, default_registry
from .entry import CatalogEntry
from .identity import EntryId, Status

CATALOG_DB_ENV = "SCIO_CATALOG_DB"


class CatalogStore(Protocol):
    """What the library needs of wherever its entries are kept."""

    def catalog(self) -> Catalog: ...
    def registry(self) -> CategoryRegistry: ...
    def next_seqno(self, category: str) -> int: ...
    def add(self, entry: CatalogEntry, category: str) -> CatalogEntry: ...
    def put(self, entry: CatalogEntry) -> CatalogEntry: ...
    def set_status(self, entry_id: str, status: Status) -> CatalogEntry | None: ...
    def propose_category(self, name: str, description: str) -> None: ...
    def confirm_category(self, name: str) -> bool: ...
    @property
    def writable(self) -> bool: ...


class FileCatalogStore:
    """The seeds on disk, plus anything contributed into a writable directory.

    Contributions are held in memory when the directory is not writable, which
    is what makes the whole contribute path testable without a database while
    still refusing to pretend it persisted something.
    """

    def __init__(self, seed_dir: Path | None = None, contributed_dir: Path | None = None) -> None:
        self.seed_dir = seed_dir
        self.contributed_dir = Path(contributed_dir) if contributed_dir else None
        self._contributed: list[CatalogEntry] = []
        self._registry = default_registry()
        if self.contributed_dir and self.contributed_dir.exists():
            self._contributed = load_catalog(self.contributed_dir).entries

    @property
    def writable(self) -> bool:
        return self.contributed_dir is not None

    def catalog(self) -> Catalog:
        seeds = load_catalog(self.seed_dir).entries if self.seed_dir else []
        return Catalog([*seeds, *self._contributed])

    def registry(self) -> CategoryRegistry:
        return self._registry

    def next_seqno(self, category: str) -> int:
        used = [
            e.entry_id.seqno
            for e in self.catalog().entries
            if e.entry_id and e.entry_id.category == category
        ]
        return max(used, default=0) + 1

    def add(self, entry: CatalogEntry, category: str) -> CatalogEntry:
        entry.id = str(EntryId(category=category, seqno=self.next_seqno(category), version=1))
        return self.put(entry)

    def put(self, entry: CatalogEntry) -> CatalogEntry:
        self._contributed = [e for e in self._contributed if e.id != entry.id]
        # A new version replaces the line it improves: the old code is in git,
        # and leaving both offerable would make the matcher choose between two
        # entries that claim exactly the same contract.
        if entry.entry_id:
            self._contributed = [
                e for e in self._contributed if not (e.entry_id and e.line == entry.line)
            ]
        self._contributed.append(entry)
        if self.contributed_dir:
            self._write(entry)
        return entry

    def _write(self, entry: CatalogEntry) -> None:
        root = self.contributed_dir / entry.id
        files_root = root / "files"
        files_root.mkdir(parents=True, exist_ok=True)
        for relative, body in entry.files.items():
            target = files_root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(body)
        data = entry.model_dump(mode="json", exclude={"files"})
        (root / "entry.json").write_text(json.dumps(data, indent=2) + "\n")

    def set_status(self, entry_id: str, status: Status) -> CatalogEntry | None:
        for entry in self._contributed:
            if entry.id == entry_id:
                entry.status = status
                if self.contributed_dir:
                    self._write(entry)
                return entry
        return None

    def propose_category(self, name: str, description: str) -> None:
        self._registry.propose(name, description)

    def confirm_category(self, name: str) -> bool:
        return self._registry.confirm(name) is not None


SCHEMA = """
CREATE TABLE IF NOT EXISTS library_category (
    name         text PRIMARY KEY,
    description  text NOT NULL DEFAULT '',
    aliases      jsonb NOT NULL DEFAULT '[]'::jsonb,
    seeded       boolean NOT NULL DEFAULT false,
    confirmed    boolean NOT NULL DEFAULT false,
    created_at   timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS library_entry (
    id           text PRIMARY KEY,
    category     text NOT NULL,
    seqno        integer NOT NULL,
    version      integer NOT NULL,
    status       text NOT NULL,
    contract_key text NOT NULL DEFAULT '',
    payload      jsonb NOT NULL,
    created_at   timestamptz NOT NULL DEFAULT now(),
    UNIQUE (category, seqno, version)
);

CREATE INDEX IF NOT EXISTS library_entry_contract ON library_entry (contract_key);
"""


# Query parameters Prisma understands and libpq does not. The local stack hands
# the engine the SAME `DATABASE_URL` the api uses — which is the point, one
# database — and Prisma's URL carries `?schema=public`. psycopg rejects it
# outright ("invalid URI query parameter"), so the engine could not connect at
# all until this was translated. Found by running it, not by a test.
_PRISMA_ONLY = {"connection_limit", "connect_timeout_ms", "pgbouncer", "pool_timeout",
                "socket_timeout", "sslaccept", "sslcert", "sslidentity", "sslpassword"}


def libpq_dsn(dsn: str) -> str:
    """A Prisma connection URL as something libpq will accept.

    `schema` becomes a `search_path` option rather than being dropped: the
    library's tables are unqualified, and silently ignoring the schema would put
    them somewhere the api's database browser never looks.
    """
    from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

    parts = urlsplit(dsn)
    if not parts.query:
        return dsn

    kept: list[tuple[str, str]] = []
    schema = ""
    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        if key == "schema":
            schema = value
        elif key not in _PRISMA_ONLY:
            kept.append((key, value))
    if schema:
        # `-csearch_path=…`, with NO space. libpq splits `options` on
        # whitespace, and urlencode writes a space as `+`, which libpq then
        # reads literally — it reported an unrecognised parameter called
        # "+search_path". The second thing running it caught.
        kept.append(("options", f"-csearch_path={schema}"))
    return urlunsplit(parts._replace(query=urlencode(kept)))


class PostgresCatalogStore:
    """Contributed entries in Postgres, with the sequence numbers it hands out."""

    def __init__(self, dsn: str, *, seed_dir: Path | None = None) -> None:
        self.dsn = libpq_dsn(dsn)
        self.seed_dir = seed_dir
        self._ready = False

    @property
    def writable(self) -> bool:
        return True

    def _connect(self):
        import psycopg  # imported here: the engine runs without a database

        connection = psycopg.connect(self.dsn, autocommit=True)
        if not self._ready:
            with connection.cursor() as cur:
                cur.execute(SCHEMA)
            self._seed_categories(connection)
            self._ready = True
        return connection

    def _seed_categories(self, connection) -> None:
        """Put the canonical categories in the table once, confirmed.

        They are code, not data — but they have to be rows too, or a proposal
        could collide with a seeded name that the table has never heard of.
        """
        with connection.cursor() as cur:
            for category in default_registry().categories:
                cur.execute(
                    """
                    INSERT INTO library_category (name, description, aliases, seeded, confirmed)
                    VALUES (%s, %s, %s::jsonb, true, true)
                    ON CONFLICT (name) DO NOTHING
                    """,
                    (category.name, category.description, json.dumps(category.aliases)),
                )

    def catalog(self) -> Catalog:
        seeds = load_catalog(self.seed_dir).entries if self.seed_dir else []
        with self._connect() as connection, connection.cursor() as cur:
            cur.execute("SELECT payload FROM library_entry WHERE status <> %s", (Status.rejected,))
            rows = [CatalogEntry.model_validate(r[0]) for r in cur.fetchall()]
        return Catalog([*seeds, *rows])

    def registry(self) -> CategoryRegistry:
        from .categories import Category

        with self._connect() as connection, connection.cursor() as cur:
            cur.execute(
                "SELECT name, description, aliases, seeded, confirmed FROM library_category"
            )
            rows = [
                Category(
                    name=name,
                    description=description,
                    aliases=list(aliases or []),
                    seeded=seeded,
                    confirmed=confirmed,
                )
                for name, description, aliases, seeded, confirmed in cur.fetchall()
            ]
        return CategoryRegistry(categories=rows or list(default_registry().categories))

    def next_seqno(self, category: str) -> int:
        """What the next number WOULD be. Reporting only.

        Deliberately not how a contribution gets its id: reading the high-water
        mark and inserting afterwards is two transactions, and between them
        another build reads the same number. Use `add`, which does both under
        one lock. Running eight concurrent contributions is what proved this —
        four of them were handed `booking.1.1` and three of the four were then
        silently overwritten.
        """
        with self._connect() as connection, connection.cursor() as cur:
            cur.execute(
                "SELECT coalesce(max(seqno), 0) + 1 FROM library_entry WHERE category = %s",
                (category,),
            )
            return max(cur.fetchone()[0], self._seed_seqno(category) + 1)

    def add(self, entry: CatalogEntry, category: str) -> CatalogEntry:
        """Assign the next id in this category and insert the entry — atomically.

        The category row is locked FOR UPDATE and held for the whole
        transaction, so a second build wanting a `booking` id waits here rather
        than reading the same high-water mark. The unique constraint on
        (category, seqno, version) is the backstop: if this were ever wrong, the
        insert fails loudly instead of one contribution quietly replacing
        another.
        """
        with self._connect() as connection, connection.transaction(), connection.cursor() as cur:
            cur.execute(
                """
                INSERT INTO library_category (name, confirmed) VALUES (%s, true)
                ON CONFLICT (name) DO NOTHING
                """,
                (category,),
            )
            cur.execute(
                "SELECT name FROM library_category WHERE name = %s FOR UPDATE",
                (category,),
            )
            cur.execute(
                "SELECT coalesce(max(seqno), 0) + 1 FROM library_entry WHERE category = %s",
                (category,),
            )
            seqno = max(cur.fetchone()[0], self._seed_seqno(category) + 1)
            assigned = EntryId(category=category, seqno=seqno, version=1)
            entry.id = str(assigned)
            self._insert(cur, entry, assigned)
        return entry

    def _seed_seqno(self, category: str) -> int:
        seeds = load_catalog(self.seed_dir).entries if self.seed_dir else []
        return max(
            (e.entry_id.seqno for e in seeds if e.entry_id and e.entry_id.category == category),
            default=0,
        )

    def put(self, entry: CatalogEntry) -> CatalogEntry:
        """Persist an entry that already HAS its id — a version bump.

        Safe without the lock `add` takes, because the line
        (`category.seqno`) already exists: this replaces a known row rather
        than competing for a new number.
        """
        parsed = entry.entry_id
        if parsed is None:
            raise ValueError(f"'{entry.id}' is not a library id (category.seqno.version)")
        with self._connect() as connection, connection.transaction(), connection.cursor() as cur:
            # A new version replaces the line it improves — see FileCatalogStore.put.
            cur.execute(
                "DELETE FROM library_entry WHERE category = %s AND seqno = %s",
                (parsed.category, parsed.seqno),
            )
            self._insert(cur, entry, parsed)
        return entry

    def _insert(self, cur, entry: CatalogEntry, parsed: EntryId) -> None:
        cur.execute(
            """
            INSERT INTO library_entry
                (id, category, seqno, version, status, contract_key, payload)
            VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb)
            """,
            (
                entry.id,
                parsed.category,
                parsed.seqno,
                parsed.version,
                entry.status.value,
                entry.effective_contract().key,
                json.dumps(entry.model_dump(mode="json")),
            ),
        )

    def set_status(self, entry_id: str, status: Status) -> CatalogEntry | None:
        with self._connect() as connection, connection.cursor() as cur:
            cur.execute("SELECT payload FROM library_entry WHERE id = %s", (entry_id,))
            row = cur.fetchone()
            if not row:
                return None
            entry = CatalogEntry.model_validate(row[0])
            entry.status = status
            cur.execute(
                "UPDATE library_entry SET status = %s, payload = %s::jsonb WHERE id = %s",
                (status.value, json.dumps(entry.model_dump(mode="json")), entry_id),
            )
        return entry

    def propose_category(self, name: str, description: str) -> None:
        with self._connect() as connection, connection.cursor() as cur:
            cur.execute(
                """
                INSERT INTO library_category (name, description, seeded, confirmed)
                VALUES (%s, %s, false, false)
                ON CONFLICT (name) DO NOTHING
                """,
                (name, description),
            )

    def confirm_category(self, name: str) -> bool:
        with self._connect() as connection, connection.cursor() as cur:
            cur.execute("UPDATE library_category SET confirmed = true WHERE name = %s", (name,))
            return cur.rowcount > 0


_STORE: CatalogStore | None = None


def default_store() -> CatalogStore:
    """The store this process uses, decided once from the environment.

    Without `SCIO_CATALOG_DB` the engine still works completely: it reads the
    seeds, it matches, it assembles. What it cannot do is *keep* anything, and
    the contribute step says so rather than reporting a phantom success.
    """
    global _STORE
    if _STORE is None:
        from .catalog import SEED_DIR, catalog_dir

        seed_dir = catalog_dir()
        dsn = os.getenv(CATALOG_DB_ENV, "").strip()
        _STORE = (
            PostgresCatalogStore(dsn, seed_dir=seed_dir)
            if dsn
            else FileCatalogStore(seed_dir=seed_dir or SEED_DIR)
        )
    return _STORE


def set_store(store: CatalogStore | None) -> None:
    """Used by tests and by the endpoints' dependency wiring."""
    global _STORE
    _STORE = store


def next_id(store: CatalogStore, category: str) -> EntryId:
    return EntryId(category=category, seqno=store.next_seqno(category), version=1)
