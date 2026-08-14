"""Running a generated app WITH DATA, so persistence can be verified (B060a).

Built on the spike's result (spikes/local-data/FINDINGS.md): an in-process
PostgreSQL — pglite, WASM, no Docker, no external project — is enough to make a
generated app really save a row, in this sandbox.

The rule that shapes everything here: **what ships to the user must not change.**
The app keeps importing `@/lib/supabase`, which imports real
`@supabase/supabase-js`. Verification does not rewrite that file. Instead it
writes a second client into `.scio/verification/` and has next.config.js replace
the `@/lib/supabase` module with it — *only* when `SCIO_VERIFY_DATA=1`. Turn the
flag off and the replacement is not even registered, so what runs is what ships.

(A `resolve.alias` does NOT work here: Next installs its own resolver plugin for
tsconfig `paths`, which wins, and the app quietly keeps talking to real Supabase.
It has to be a `NormalModuleReplacementPlugin`.)

What this module owns:

- **the files** — the client and the pglite dependency, written into the app;
- **the database's life** — one per build, in a directory this module creates
  and this module deletes. pglite is single-writer, and the spike showed what
  sharing costs: clearing PGDATA under a running server left it serving stale
  rows while new inserts reported success and vanished;
- **the environment** — the variables the client reads (data dir, the app's own
  migration files, the acting user).

What it does NOT own: the queries. Those are the app's, unchanged.
"""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path

VERIFY_FLAG = "SCIO_VERIFY_DATA"
PGDATA_ENV = "SCIO_VERIFY_PGDATA"
SCHEMA_ENV = "SCIO_VERIFY_SCHEMA"
ACTOR_ENV = "SCIO_VERIFY_ACTOR"

CLIENT_SOURCE = Path(__file__).resolve().parent / "client.ts"

VERIFICATION_DIR = ".scio/verification"
"""Inside the app, but namespaced and gitignored: it is build scaffolding, not
the user's code. A user who opens their repo should not find our test harness in
the middle of their lib/."""

PGLITE_PACKAGE = "@electric-sql/pglite"
PGLITE_VERSION = "0.5.5"
"""Pinned to what the spike proved: PostgreSQL 18.3 as WASM."""


def verification_enabled(env: dict[str, str] | None = None) -> bool:
    """Whether this process should run apps against the verification database."""
    source = env if env is not None else os.environ
    return source.get(VERIFY_FLAG, "").lower() in {"1", "true", "yes"}


def next_config(alias_enabled: bool = True) -> str:
    """The app's next.config.js, with the verification swap behind the flag.

    The condition is evaluated in the app's own config at boot, so the swap
    exists only in a process that was told to verify. There is no build in which
    the user's code silently points somewhere else.
    """
    if not alias_enabled:
        return (
            "/** @type {import('next').NextConfig} */\n"
            "module.exports = { reactStrictMode: true };\n"
        )
    return f"""const path = require("node:path");

/**
 * Scio: in verification mode ONLY, the data client is swapped for one backed by
 * an in-process Postgres, so a build can prove that saving actually saves.
 * Without {VERIFY_FLAG} this block does nothing and the app uses its own
 * lib/supabase.ts — the real @supabase/supabase-js — exactly as delivered.
 */
const verifying = ["1", "true", "yes"].includes(
  String(process.env.{VERIFY_FLAG} ?? "").toLowerCase(),
);

/** @type {{import('next').NextConfig}} */
module.exports = {{
  reactStrictMode: true,
  webpack: (config, {{ isServer, webpack }}) => {{
    if (verifying) {{
      // A module REPLACEMENT rather than a resolve.alias: Next installs its own
      // resolver plugin for tsconfig `paths`, which wins over aliases, so an
      // alias on "@/lib/supabase" silently does nothing and the app talks to
      // real Supabase during verification.
      config.plugins.push(
        new webpack.NormalModuleReplacementPlugin(/^@\\/lib\\/supabase$/, (resource) => {{
          resource.request = path.resolve(__dirname, "{VERIFICATION_DIR}/client.ts");
        }}),
      );
    }}
    if (isServer) {{
      // pglite is a WASM module; bundling it into the server output breaks it.
      config.externals = [...(config.externals ?? []), "{PGLITE_PACKAGE}"];
    }}
    return config;
  }},
}};
"""


@dataclass
class VerificationDatabase:
    """One database, for one build, with an owned lifetime."""

    app_dir: Path
    data_dir: Path
    schema_files: list[str] = field(default_factory=list)
    actor: str = ""

    @property
    def env(self) -> dict[str, str]:
        """What the app's process needs to run against this database."""
        return {
            VERIFY_FLAG: "1",
            PGDATA_ENV: str(self.data_dir),
            SCHEMA_ENV: ":".join(self.schema_files),
            ACTOR_ENV: self.actor,
        }

    @property
    def size_bytes(self) -> int:
        if not self.data_dir.exists():
            return 0
        return sum(f.stat().st_size for f in self.data_dir.rglob("*") if f.is_file())

    def discard(self) -> None:
        """Delete the database. Safe to call twice; never call it while serving.

        Build output, not user data — a fresh one per build is what makes a
        verification result mean something.
        """
        shutil.rmtree(self.data_dir, ignore_errors=True)


def migration_files(app_dir: Path) -> list[str]:
    """The app's OWN schema, in order. Applied verbatim — if the generated
    migration does not apply, that is a finding about the build, not something
    for this layer to paper over."""
    migrations = sorted((app_dir / "supabase" / "migrations").glob("*.sql"))
    return [str(path.resolve()) for path in migrations]


def prepare(app_dir: Path, *, actor: str = "", fresh: bool = True) -> VerificationDatabase:
    """Put the verification client into an app and hand back its database.

    Writes only inside `.scio/verification/` and adds the pglite dependency —
    the app's own files are not touched, which is the property the whole design
    rests on.
    """
    app_dir = Path(app_dir).resolve()
    target = app_dir / VERIFICATION_DIR
    target.mkdir(parents=True, exist_ok=True)
    (target / "client.ts").write_text(CLIENT_SOURCE.read_text())
    (app_dir / ".scio" / ".gitignore").write_text("*\n")

    data_dir = target / "pgdata"
    if fresh:
        shutil.rmtree(data_dir, ignore_errors=True)

    return VerificationDatabase(
        app_dir=app_dir,
        data_dir=data_dir,
        schema_files=migration_files(app_dir),
        actor=actor,
    )


def uses_real_supabase(app_dir: Path) -> bool:
    """Does the app, as it would ship, still import the real client?

    The load-bearing assertion of this whole module, kept as a function so a test
    can make it and a build can too.
    """
    client = Path(app_dir) / "lib" / "supabase.ts"
    if not client.exists():
        return False
    return "@supabase/supabase-js" in client.read_text()
