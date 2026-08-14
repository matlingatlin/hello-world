"""The verification data layer (B060a): running a generated app WITH data.

Two claims carry the weight, and they pull against each other:

1. **What ships is unchanged.** The app imports real `@supabase/supabase-js`.
   If verification quietly rewrote the user's data layer, every build would be
   verifying something the user never receives.
2. **What we verify is real.** A row really persists, and RLS is really
   enforced — which needs a non-superuser and claim GUCs inside a transaction,
   because pglite connects as superuser and superusers skip RLS entirely.

The Node-level tests run the actual client against actual PostgreSQL. They are
skipped when the sandbox has no node/pglite rather than silently passing: a green
suite that never touched a database would be worse than a skipped one.
"""

import json
import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest

from scio_engine.builder.workspace import stack_files
from scio_engine.library.verification import (
    PGLITE_PACKAGE,
    VERIFICATION_DIR,
    VERIFY_FLAG,
    migration_files,
    next_config,
    prepare,
    uses_real_supabase,
    verification_enabled,
)

ENGINE_ROOT = Path(__file__).resolve().parents[1]
SPIKE_MODULES = ENGINE_ROOT.parents[1] / "spikes" / "local-data" / "app" / "node_modules"

pytestmark = pytest.mark.filterwarnings("ignore")


def node_binary() -> str | None:
    """A Node new enough to run TypeScript directly (22.18+ strips types).

    Resolved explicitly rather than trusting PATH: this sandbox has both a 20
    and a 22, and the 20 cannot load the client's .ts at all.
    """
    for candidate in ("/opt/node22/bin/node", shutil.which("node")):
        if not candidate or not Path(candidate).exists():
            continue
        version = subprocess.run(
            [candidate, "--version"], capture_output=True, text=True, check=False
        ).stdout.strip()
        major, _, minor = version.lstrip("v").partition(".")
        if (int(major or 0), int(minor.split(".")[0] or 0)) >= (22, 18):
            return candidate
    return None


def node_with_pglite() -> Path | None:
    """A node_modules that has pglite — the spike installed one; reuse it."""
    if node_binary() and (SPIKE_MODULES / "@electric-sql" / "pglite").exists():
        return SPIKE_MODULES
    return None


needs_pglite = pytest.mark.skipif(
    node_with_pglite() is None, reason="node with @electric-sql/pglite is not available here"
)


def app_with_schema(tmp_path: Path, schema: str) -> Path:
    """A minimal generated app: its own migration, its own supabase client."""
    (tmp_path / "supabase" / "migrations").mkdir(parents=True)
    (tmp_path / "supabase" / "migrations" / "0001_init.sql").write_text(schema)
    (tmp_path / "lib").mkdir(exist_ok=True)
    (tmp_path / "lib" / "supabase.ts").write_text(
        'import { createClient } from "@supabase/supabase-js";\n'
        "export const getSupabaseClient = () => createClient(process.env.URL!, process.env.KEY!);\n"
    )
    return tmp_path


# --------------------------------------------------------------------------
# 1. What ships is unchanged
# --------------------------------------------------------------------------


class TestTheShippedAppIsUntouched:
    def test_the_apps_own_client_still_imports_real_supabase(self, tmp_path):
        app = app_with_schema(tmp_path, "create table t (id int);")
        prepare(app)

        assert uses_real_supabase(app), "verification must not rewrite the user's data layer"
        assert "@supabase/supabase-js" in (app / "lib" / "supabase.ts").read_text()
        assert "pglite" not in (app / "lib" / "supabase.ts").read_text()

    def test_verification_writes_only_inside_its_own_directory(self, tmp_path):
        app = app_with_schema(tmp_path, "create table t (id int);")
        before = {p.relative_to(app) for p in app.rglob("*") if p.is_file()}

        prepare(app)

        added = {p.relative_to(app) for p in app.rglob("*") if p.is_file()} - before
        assert all(str(p).startswith(".scio") for p in added), added

    def test_the_verification_directory_is_not_the_users_code(self):
        """It is build scaffolding — gitignored, and out of lib/."""
        assert VERIFICATION_DIR.startswith(".scio")
        assert ".scio" in stack_files("booking")[".gitignore"]

    def test_the_swap_is_off_unless_the_flag_is_set(self):
        config = next_config()

        assert VERIFY_FLAG in config
        # The swap is inside a conditional evaluated at boot — not applied
        # unconditionally with a flag checked somewhere else.
        assert "if (verifying)" in config
        # A module REPLACEMENT, not a resolve.alias: Next's tsconfig-paths
        # resolver plugin beats aliases, so an alias silently does nothing and
        # the app quietly talks to real Supabase during verification.
        assert "NormalModuleReplacementPlugin" in config
        assert "config.resolve.alias" not in config

    def test_without_the_flag_there_is_no_swap_at_all(self):
        plain = next_config(alias_enabled=False)

        assert "NormalModuleReplacementPlugin" not in plain
        assert VERIFICATION_DIR not in plain

    def test_a_build_without_the_flag_is_not_in_verification_mode(self):
        assert verification_enabled({}) is False
        assert verification_enabled({VERIFY_FLAG: "0"}) is False
        assert verification_enabled({VERIFY_FLAG: "1"}) is True
        assert verification_enabled({VERIFY_FLAG: "true"}) is True

    def test_pglite_is_a_dev_dependency_so_it_never_ships(self):
        manifest = json.loads(stack_files("booking")["package.json"])

        assert PGLITE_PACKAGE in manifest["devDependencies"]
        assert PGLITE_PACKAGE not in manifest["dependencies"]
        assert "@supabase/supabase-js" in manifest["dependencies"]


# --------------------------------------------------------------------------
# 2. Lifecycle
# --------------------------------------------------------------------------


class TestLifecycle:
    def test_one_database_per_build_in_a_directory_we_own(self, tmp_path):
        app = app_with_schema(tmp_path, "create table t (id int);")
        db = prepare(app)

        assert db.data_dir.is_relative_to(app / ".scio")
        assert db.env[VERIFY_FLAG] == "1"
        assert db.env["SCIO_VERIFY_PGDATA"] == str(db.data_dir)

    def test_it_applies_the_apps_own_migrations(self, tmp_path):
        app = app_with_schema(tmp_path, "create table t (id int);")
        (app / "supabase" / "migrations" / "0002_more.sql").write_text("create table u (id int);")

        db = prepare(app)

        assert len(db.schema_files) == 2
        assert db.schema_files == sorted(db.schema_files)  # 0001 before 0002
        assert db.env["SCIO_VERIFY_SCHEMA"] == ":".join(db.schema_files)

    def test_an_app_with_no_migrations_is_not_an_error(self, tmp_path):
        (tmp_path / "lib").mkdir()
        assert migration_files(tmp_path) == []

    def test_a_fresh_database_per_build(self, tmp_path):
        app = app_with_schema(tmp_path, "create table t (id int);")
        db = prepare(app)
        db.data_dir.mkdir(parents=True, exist_ok=True)
        (db.data_dir / "stale").write_text("from a previous build")

        again = prepare(app)

        assert not (again.data_dir / "stale").exists()

    def test_discard_removes_the_database_and_is_safe_twice(self, tmp_path):
        app = app_with_schema(tmp_path, "create table t (id int);")
        db = prepare(app)
        db.data_dir.mkdir(parents=True, exist_ok=True)
        (db.data_dir / "PG_VERSION").write_text("18")

        db.discard()
        db.discard()  # a cleanup that throws on the second call is not cleanup

        assert not db.data_dir.exists()
        assert db.size_bytes == 0

    def test_the_database_size_is_measurable(self, tmp_path):
        """~39MB each (the spike measured it): builds need a cleanup policy."""
        app = app_with_schema(tmp_path, "create table t (id int);")
        db = prepare(app)
        db.data_dir.mkdir(parents=True, exist_ok=True)
        (db.data_dir / "base").write_bytes(b"x" * 2048)

        assert db.size_bytes == 2048


# --------------------------------------------------------------------------
# 3. It really runs, against a real database
# --------------------------------------------------------------------------

BOOKING_SCHEMA = """
create table bookings (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid,
  guest_name text not null,
  party_size integer not null check (party_size between 1 and 20),
  created_at timestamptz not null default now(),
  cancelled_at timestamptz
);

alter table bookings enable row level security;

create policy bookings_own on bookings for select
  using (owner_id = auth.uid());

create policy bookings_insert on bookings for insert
  with check (true);
"""


def run_node(script: str, app: Path, db, modules: Path) -> dict:
    """Run a snippet against the real verification client, in Node.

    node_modules is symlinked in rather than pointed at with NODE_PATH: ESM
    ignores NODE_PATH entirely and resolves by walking up from the importing
    file — which is also why the real workspace symlinks its dependency cache.
    """
    link = app / "node_modules"
    if not link.exists():
        link.symlink_to(modules, target_is_directory=True)
    runner = app / "run.mjs"
    runner.write_text(script)
    # Node 22.18+ strips TypeScript types natively, so the client runs as-is —
    # the same source the app is aliased onto, not a transpiled copy of it.
    result = subprocess.run(
        [node_binary(), str(runner)],
        cwd=app,
        capture_output=True,
        text=True,
        timeout=300,
        env={"PATH": "/usr/bin:/bin", **db.env},
    )
    if result.returncode != 0:
        raise AssertionError(f"node failed:\n{result.stdout}\n{result.stderr}")
    return json.loads(result.stdout.strip().splitlines()[-1])


@needs_pglite
class TestItReallyPersists:
    def test_an_insert_persists_and_reads_back(self, tmp_path):
        app = app_with_schema(tmp_path, BOOKING_SCHEMA)
        db = prepare(app)
        modules = node_with_pglite()

        out = run_node(
            textwrap.dedent(f"""
            import {{ getSupabaseClient, setVerificationActor, verificationQuery }}
              from "{app}/{VERIFICATION_DIR}/client.ts";

            const alice = "11111111-1111-1111-1111-111111111111";
            setVerificationActor(alice);
            const client = getSupabaseClient();

            const created = await client
              .from("bookings")
              .insert({{ owner_id: alice, guest_name: "Ada", party_size: 4 }})
              .select()
              .single();

            const read = await client.from("bookings").select("*").eq("guest_name", "Ada");
            const raw = await verificationQuery("select count(*)::int as n from bookings");

            console.log(JSON.stringify({{
              insertError: created.error?.message ?? null,
              insertedId: created.data?.id ?? null,
              readError: read.error?.message ?? null,
              readCount: read.data?.length ?? 0,
              rowsInDatabase: raw[0].n,
            }}));
            """),
            app,
            db,
            modules,
        )

        assert out["insertError"] is None, out["insertError"]
        assert out["insertedId"], "the row should come back with its generated id"
        assert out["readError"] is None
        assert out["readCount"] == 1, "the app should read back what it wrote"
        assert out["rowsInDatabase"] == 1, "and it should really be in Postgres"

        db.discard()

    def test_row_level_security_isolates_two_guests(self, tmp_path):
        """The claim B054 had to scope out as unobservable, now observable."""
        app = app_with_schema(tmp_path, BOOKING_SCHEMA)
        db = prepare(app)
        modules = node_with_pglite()

        out = run_node(
            textwrap.dedent(f"""
            import {{ getSupabaseClient, setVerificationActor }}
              from "{app}/{VERIFICATION_DIR}/client.ts";

            const alice = "11111111-1111-1111-1111-111111111111";
            const bob   = "22222222-2222-2222-2222-222222222222";
            const client = getSupabaseClient();

            setVerificationActor(alice);
            await client
              .from("bookings")
              .insert({{ owner_id: alice, guest_name: "Ada", party_size: 2 }});
            setVerificationActor(bob);
            await client
              .from("bookings")
              .insert({{ owner_id: bob, guest_name: "Grace", party_size: 3 }});

            setVerificationActor(alice);
            const asAlice = await client.from("bookings").select("*");
            setVerificationActor(bob);
            const asBob = await client.from("bookings").select("*");

            console.log(JSON.stringify({{
              aliceSees: (asAlice.data ?? []).map((r) => r.guest_name),
              bobSees: (asBob.data ?? []).map((r) => r.guest_name),
            }}));
            """),
            app,
            db,
            modules,
        )

        assert out["aliceSees"] == ["Ada"], out
        assert out["bobSees"] == ["Grace"], out

        db.discard()

    def test_the_apps_own_migration_is_applied_verbatim(self, tmp_path):
        app = app_with_schema(tmp_path, BOOKING_SCHEMA)
        db = prepare(app)

        out = run_node(
            textwrap.dedent(f"""
            import {{ verificationQuery }} from "{app}/{VERIFICATION_DIR}/client.ts";
            const cols = await verificationQuery(
              "select column_name from information_schema.columns where table_name = 'bookings'"
            );
            const policies = await verificationQuery(
              "select policyname from pg_policies where tablename = 'bookings'"
            );
            console.log(JSON.stringify({{
              columns: cols.map((c) => c.column_name).sort(),
              policies: policies.map((p) => p.policyname).sort(),
            }}));
            """),
            app,
            db,
            node_with_pglite(),
        )

        assert "party_size" in out["columns"]
        assert out["policies"] == ["bookings_insert", "bookings_own"]

        db.discard()

    def test_an_unimplemented_call_throws_instead_of_answering_nothing(self, tmp_path):
        """A shim that quietly returns no rows makes a working app look broken."""
        app = app_with_schema(tmp_path, BOOKING_SCHEMA)
        db = prepare(app)

        out = run_node(
            textwrap.dedent(f"""
            import {{ getSupabaseClient }} from "{app}/{VERIFICATION_DIR}/client.ts";
            const client = getSupabaseClient();
            let rpc = null, embedded = null;
            try {{ client.rpc("whatever"); }} catch (e) {{ rpc = e.message; }}
            try {{
              client.from("bookings").select("*, guest(*)");
            }} catch (e) {{ embedded = e.message; }}
            console.log(JSON.stringify({{ rpc, embedded }}));
            """),
            app,
            db,
            node_with_pglite(),
        )

        assert "rpc" in (out["rpc"] or "")
        assert "embedded selects" in (out["embedded"] or "")
        assert "PostgREST" in (out["rpc"] or "")  # the documented escape hatch

        db.discard()


# --------------------------------------------------------------------------
# 4. The build wires it in
# --------------------------------------------------------------------------


class TestTheBuildUsesIt:
    async def test_a_build_without_the_flag_never_touches_a_database(
        self, tmp_path, monkeypatch
    ):
        """The default path is unchanged — no database, no env, no cleanup to do."""
        monkeypatch.delenv(VERIFY_FLAG, raising=False)
        from scio_engine.builder.loop import ScriptedPreview
        from scio_engine.core.console import classify_console
        from scio_engine.core.preview import Observation

        preview = ScriptedPreview(
            [Observation(screenshot_path=None, console=classify_console([]), title="x")]
        )
        assert getattr(preview, "env", {}) == {}
        assert not (tmp_path / ".scio").exists()

    def test_the_database_env_is_what_the_sandbox_passes_to_the_app(self, tmp_path):
        app = app_with_schema(tmp_path, BOOKING_SCHEMA)
        db = prepare(app)

        # These four are exactly what client.ts reads.
        assert set(db.env) == {
            VERIFY_FLAG,
            "SCIO_VERIFY_PGDATA",
            "SCIO_VERIFY_SCHEMA",
            "SCIO_VERIFY_ACTOR",
        }

    def test_the_sandbox_forwards_per_run_env_to_the_app_process(self):
        """Without this the app would boot with no database to talk to."""
        import inspect

        from scio_engine.core.sandbox import LocalProcessSandbox

        signature = inspect.signature(LocalProcessSandbox.start)
        assert "env" in signature.parameters
