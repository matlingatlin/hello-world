"""The catalog store against a real PostgreSQL.

Two claims here cannot be checked without one, and both were WRONG the first
time they were run against a database rather than reasoned about:

1. **The engine can connect at all.** The local stack hands it the same
   `DATABASE_URL` the api uses, and Prisma's URL carries `?schema=public`, which
   psycopg rejects outright. Then the obvious fix encoded the space in
   `-c search_path=…` as `+`, and Postgres reported an unrecognised parameter
   called `+search_path`.

2. **Two builds contributing at once get different numbers.** Reading the
   high-water mark and inserting afterwards is two transactions; eight
   concurrent contributions handed out `booking.1.1` four times, and three of
   those four were then silently overwritten by the fourth.

Skipped, loudly, when there is no database to talk to.
"""

from __future__ import annotations

import concurrent.futures as futures
import os

import pytest

from scio_engine.library.entry import CatalogEntry, Layer, Quality
from scio_engine.library.identity import Contract, EntryId, Status
from scio_engine.library.store import PostgresCatalogStore, libpq_dsn

DSN = os.getenv("SCIO_CATALOG_DB", "")

needs_db = pytest.mark.skipif(not DSN, reason="no SCIO_CATALOG_DB to talk to")


def an_entry(n: int) -> CatalogEntry:
    return CatalogEntry(
        id="pending",
        name=f"entry {n}",
        layer=Layer.feature,
        description="a thing",
        category="booking",
        status=Status.provisional,
        files={f"a{n}.ts": "export const x = 1;\n"},
        contract=Contract(operations=[f"op{n}"], files=[f"a{n}.ts"]),
        quality=Quality(tested=True, security_reviewed=True),
    )


class TestPrismaUrlsAreTranslated:
    """No database needed: this is pure string handling, and it broke twice."""

    def test_prisma_s_schema_becomes_a_search_path_option(self):
        translated = libpq_dsn("postgresql://scio@127.0.0.1:55432/scio?schema=public")

        assert "schema=public" not in translated
        assert "options=-csearch_path%3Dpublic" in translated
        # No space, and therefore no "+": libpq splits `options` on whitespace
        # and reads a urlencoded space literally.
        assert "+search_path" not in translated

    def test_prisma_only_parameters_are_dropped_and_real_ones_kept(self):
        translated = libpq_dsn(
            "postgresql://u:p@h/db?schema=lib&connection_limit=5&pgbouncer=true&sslmode=require"
        )

        assert "connection_limit" not in translated
        assert "pgbouncer" not in translated
        assert "sslmode=require" in translated

    def test_a_url_with_no_query_is_left_alone(self):
        dsn = "postgresql://scio@127.0.0.1:55432/scio"

        assert libpq_dsn(dsn) == dsn


@needs_db
class TestTheStoreAgainstPostgres:
    @pytest.fixture(autouse=True)
    def clean(self):
        store = PostgresCatalogStore(DSN, seed_dir=None)
        with store._connect() as connection, connection.cursor() as cur:
            cur.execute("DELETE FROM library_entry")
        yield store
        with store._connect() as connection, connection.cursor() as cur:
            cur.execute("DELETE FROM library_entry")

    def test_the_tables_are_created_on_first_use(self, clean: PostgresCatalogStore):
        assert clean.registry().names()  # the seeded categories are rows
        assert clean.writable

    def test_an_entry_round_trips(self, clean: PostgresCatalogStore):
        clean.add(an_entry(1), "booking")

        stored = clean.catalog().get("booking.1.1")
        assert stored is not None
        assert stored.status is Status.provisional
        assert stored.files == {"a1.ts": "export const x = 1;\n"}

    def test_eight_concurrent_contributions_get_eight_different_ids(self):
        """The claim the lock exists for. Each thread opens its own connection,
        which is what two builds in two processes actually look like."""

        def contribute(n: int) -> str:
            store = PostgresCatalogStore(DSN, seed_dir=None)
            return store.add(an_entry(n), "booking").id

        with futures.ThreadPoolExecutor(max_workers=8) as pool:
            handed_out = sorted(pool.map(contribute, range(8)))

        assert len(set(handed_out)) == 8, handed_out
        assert [EntryId.parse(i).seqno for i in handed_out] == list(range(1, 9))
        # And every one of them is actually in there — the failure mode was that
        # later inserts deleted earlier rows that shared a number.
        store = PostgresCatalogStore(DSN, seed_dir=None)
        assert sorted(e.id for e in store.catalog().entries) == handed_out

    def test_a_version_bump_replaces_the_line_it_improves(self, clean: PostgresCatalogStore):
        first = clean.add(an_entry(1), "booking")
        better = an_entry(1)
        better.id = str(EntryId.parse(first.id).bumped())

        clean.put(better)

        ids = sorted(e.id for e in clean.catalog().entries)
        assert ids == ["booking.1.2"]

    def test_a_rejected_entry_is_never_listed(self, clean: PostgresCatalogStore):
        clean.add(an_entry(1), "booking")

        clean.set_status("booking.1.1", Status.rejected)

        assert clean.catalog().get("booking.1.1") is None
        assert clean.set_status("booking.1.1", Status.approved) is not None  # still a row

    def test_a_proposed_category_is_unconfirmed_until_someone_says_so(
        self, clean: PostgresCatalogStore
    ):
        clean.propose_category("sprocket", "makes sprockets")

        registry = clean.registry()
        assert "sprocket" not in registry.names()
        assert registry.resolve("sprocket") == ""

        assert clean.confirm_category("sprocket") is True
        assert "sprocket" in clean.registry().names()
        assert clean.confirm_category("nothing-like-this") is False
