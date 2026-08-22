"""Where a generated app lives while it is being built and previewed.

Two things happen here, in this order, and the order is the whole point:

1. **Scaffold** the locked stack (ADR-0011 — Next.js + TypeScript + Tailwind +
   Supabase). These are stack files, not application files: the build writes the
   app *into* this, and may overwrite any of them (a design-tokens package owns
   `tailwind.config.ts`, for instance).
2. **Install** the dependencies — explicitly, blocking, *before* anything tries
   to serve the app.

Step 2 is the answer to the constraint the spike found: a dev server told to
install on first boot dies mid-startup, so `LocalProcessSandbox.start` refuses a
directory without `node_modules`. Installing is therefore its own step with its
own failure, not a side effect of starting.

Installing per project would mean ~200MB and a minute per build, so the install
goes into a cache keyed by the dependency set and is linked into each workspace.
Same dependencies (the normal case — the stack is locked) means the second build
onwards costs a symlink.

`SCIO_SCAFFOLD_DIR` still short-circuits both steps for an operator who has a
prepared directory (or an offline machine): point it at a folder that already has
`package.json` and `node_modules` and the workspace is built from that instead.
In production this is an ACA session with a prepared image (ADR-0005).
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from ..library.verification import PGLITE_PACKAGE, PGLITE_VERSION, next_config
from .preview_bridge import preview_flag_js, preview_webpack

SCAFFOLD_FILES = ("package.json", "next.config.js", "tsconfig.json", "next-env.d.ts")

ENGINE_ROOT = Path(__file__).resolve().parents[3]

SCAFFOLD_DIR_ENV = "SCIO_SCAFFOLD_DIR"
WORKSPACE_ROOT_ENV = "SCIO_WORKSPACE_ROOT"
DEPS_CACHE_ENV = "SCIO_DEPS_CACHE"
SKIP_INSTALL_ENV = "SCIO_SKIP_INSTALL"
INSTALL_TIMEOUT_ENV = "SCIO_INSTALL_TIMEOUT_S"

# Pinned, not floating: a locked stack is only a reliability multiplier if it is
# the same stack every time. Bump these deliberately, and re-run a real build.
DEPENDENCIES = {
    "next": "14.2.15",
    "react": "18.3.1",
    "react-dom": "18.3.1",
    "@supabase/supabase-js": "2.45.4",
    # Server-side input validation. Part of the stack because both the library's
    # blueprints and real generated code reach for it unprompted — the second
    # real run imported it into lib/auth.ts while it was not installed, which
    # only stayed invisible because no rendered route imported that module.
    "zod": "3.23.8",
}

DEV_DEPENDENCIES = {
    "typescript": "5.6.3",
    "@types/node": "22.9.0",
    "@types/react": "18.3.12",
    "@types/react-dom": "18.3.1",
    # Verification only — the in-process Postgres the data layer runs against
    # (library/verification). A devDependency because it never ships in a build.
    PGLITE_PACKAGE: PGLITE_VERSION,
    "tailwindcss": "3.4.14",
    "postcss": "8.4.47",
    "autoprefixer": "10.4.20",
}


class WorkspaceUnavailable(RuntimeError):
    """No runnable workspace can be prepared here.

    Raised rather than quietly building something that cannot run: a build the
    user cannot see is not a build, and pretending otherwise is the dishonesty
    the whole product is trying to avoid.
    """


@dataclass
class InstallReport:
    """What the install step actually did — for the build log and the runbook."""

    node_modules: Path
    cached: bool
    seconds: float
    packages: int = 0

    def describe(self) -> str:
        source = "cache" if self.cached else "npm install"
        return f"dependencies ready via {source} in {self.seconds:.1f}s"


def package_json(project_id: str) -> str:
    """The generated app's package.json — the locked stack, pinned."""
    return (
        json.dumps(
            {
                "name": _npm_name(project_id),
                "private": True,
                "version": "0.1.0",
                "scripts": {
                    "dev": "next dev",
                    "build": "next build",
                    "start": "next start",
                    "lint": "next lint",
                },
                "dependencies": DEPENDENCIES,
                "devDependencies": DEV_DEPENDENCIES,
            },
            indent=2,
        )
        + "\n"
    )


def _npm_name(project_id: str) -> str:
    """npm names are lowercase and have a small alphabet; project ids are ours."""
    cleaned = "".join(c if c.isalnum() or c in "-_" else "-" for c in project_id.lower())
    return f"scio-{cleaned.strip('-') or 'app'}"


def stack_files(project_id: str) -> dict[str, str]:
    """Every non-application file the app needs to run.

    Written before the build so the very first package already has a compiling
    project underneath it, and overwritable by the build so a package that owns
    `tailwind.config.ts` or `app/globals.css` really owns it.
    """
    return {
        "package.json": package_json(project_id),
        # Carries two preview-time swaps, each behind its own flag and each
        # inert without it: the verification data client (SCIO_VERIFY_DATA) and
        # the design window's marking bridge (SCIO_PREVIEW_MODE).
        "next.config.js": next_config(
            extra_flags=preview_flag_js(), extra_webpack=preview_webpack()
        ),
        "tsconfig.json": json.dumps(
            {
                "compilerOptions": {
                    "target": "ES2022",
                    "lib": ["dom", "dom.iterable", "esnext"],
                    "allowJs": True,
                    "skipLibCheck": True,
                    "strict": True,
                    "noEmit": True,
                    "esModuleInterop": True,
                    "module": "esnext",
                    "moduleResolution": "bundler",
                    "resolveJsonModule": True,
                    "isolatedModules": True,
                    "jsx": "preserve",
                    "incremental": True,
                    "plugins": [{"name": "next"}],
                    "paths": {"@/*": ["./*"]},
                },
                # tests/ is excluded: generated test files are run by the user's
                # own runner, and a missing `test` global must not break the app.
                "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
                "exclude": ["node_modules", "tests"],
            },
            indent=2,
        )
        + "\n",
        "next-env.d.ts": (
            "/// <reference types=\"next\" />\n"
            "/// <reference types=\"next/image-types/global\" />\n"
        ),
        "postcss.config.js": (
            "module.exports = { plugins: { tailwindcss: {}, autoprefixer: {} } };\n"
        ),
        # A working default. The design-tokens package overwrites both of these
        # — until it runs, the app still builds and still has Tailwind.
        "tailwind.config.ts": (
            "import type { Config } from \"tailwindcss\";\n\n"
            "const config: Config = {\n"
            '  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],\n'
            "  theme: { extend: {} },\n"
            "  plugins: [],\n"
            "};\n\nexport default config;\n"
        ),
        "app/globals.css": "@tailwind base;\n@tailwind components;\n@tailwind utilities;\n",
        ".gitignore": "node_modules\n.next\n.env.local\n.scio\n",
    }


def default_scaffold_dir() -> Path | None:
    """A prepared app skeleton, if the operator configured one.

    Only `SCIO_SCAFFOLD_DIR` counts as configuration. The spike app is the
    offline fallback — it exists in this repo, so a machine without npm or
    without a network can still run the whole path.
    """
    configured = os.getenv(SCAFFOLD_DIR_ENV)
    if configured:
        path = Path(configured).expanduser().resolve()
        return path if path.exists() else None
    return None


def fallback_scaffold_dir() -> Path | None:
    # apps/engine -> apps -> the repo root, where spikes/ lives.
    fallback = ENGINE_ROOT.parents[1] / "spikes" / "sandbox-marking" / "example-app"
    return fallback if (fallback / "node_modules").exists() else None


def workspace_root() -> Path:
    return Path(os.getenv(WORKSPACE_ROOT_ENV, str(ENGINE_ROOT / "out" / "projects"))).resolve()


def discard_workspace(project_id: str) -> dict[str, object]:
    """Remove a project's workspace, and say honestly what was removed (B100).

    Deleting a project used to mean setting a timestamp on a row. The code, the
    git history and the screenshots stayed on disk indefinitely — so a user who
    deleted a project still had their app sitting on our machine, which is the
    opposite of what the word means.

    Never raises. A workspace that cannot be removed must not stop the project
    from being deleted; it must be *reported* instead, because the one thing
    this must never do is claim something is gone when it is not.
    """
    root = workspace_root()
    removed: list[str] = []
    problems: list[str] = []
    # The workspace itself and its screenshot directory, which lives beside it.
    for target in (root / project_id, root / f"{project_id}-shots"):
        if not target.exists():
            continue
        # Never step outside the root, whatever the project id says.
        if root not in target.resolve().parents:
            problems.append(f"{target} is not inside the workspace root")
            continue
        try:
            shutil.rmtree(target)
            removed.append(str(target))
        except OSError as exc:
            problems.append(f"{target}: {exc}")
    return {"removed": removed, "problems": problems}


def deps_cache_root() -> Path:
    """Where installed dependency sets live, shared across projects."""
    return Path(os.getenv(DEPS_CACHE_ENV, str(ENGINE_ROOT / "out" / "deps"))).resolve()


def deps_key(manifest: dict[str, dict[str, str]]) -> str:
    """A stable id for a dependency set — the cache is keyed on this."""
    canonical = json.dumps(
        {
            "dependencies": manifest.get("dependencies", {}),
            "devDependencies": manifest.get("devDependencies", {}),
        },
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


def _install_timeout() -> float:
    try:
        return float(os.getenv(INSTALL_TIMEOUT_ENV, "900"))
    except ValueError:
        return 900.0


def install_dependencies(app_dir: Path, *, timeout_s: float | None = None) -> InstallReport:
    """Install this app's dependencies and link them in. Blocks until done.

    Deliberately a separate, explicit step: the sandbox refuses to start without
    `node_modules`, so if this fails the build fails *here*, with npm's own
    error, instead of as a dev server that dies half-way through booting.
    """
    started = time.time()
    modules = app_dir / "node_modules"
    if modules.exists():
        return InstallReport(node_modules=modules, cached=True, seconds=0.0)

    manifest_path = app_dir / "package.json"
    if not manifest_path.exists():
        raise WorkspaceUnavailable(f"{app_dir} has no package.json — nothing to install")
    manifest = json.loads(manifest_path.read_text())

    if shutil.which("npm") is None:
        raise WorkspaceUnavailable(
            "npm is not on PATH, so dependencies cannot be installed. Install Node 20+, "
            f"or set {SCAFFOLD_DIR_ENV} to a directory that already has node_modules."
        )

    cache = deps_cache_root() / deps_key(manifest)
    cached = (cache / "node_modules").exists()
    if not cached:
        _install_into_cache(cache, manifest, timeout_s or _install_timeout())

    # A symlink, not a copy: 200MB per project would be absurd, and a generated
    # app never writes into node_modules.
    modules.symlink_to(cache / "node_modules", target_is_directory=True)
    lockfile = cache / "package-lock.json"
    if lockfile.exists() and not (app_dir / "package-lock.json").exists():
        shutil.copy2(lockfile, app_dir / "package-lock.json")

    return InstallReport(
        node_modules=modules,
        cached=cached,
        seconds=time.time() - started,
        packages=_count_packages(cache / "node_modules"),
    )


def _install_into_cache(cache: Path, manifest: dict, timeout_s: float) -> None:
    """npm install into a scratch directory, then move it into place.

    Built aside and renamed so a crashed or timed-out install never leaves a
    half-populated cache entry that the next build would happily symlink to.
    """
    cache.parent.mkdir(parents=True, exist_ok=True)
    scratch = cache.parent / f".{cache.name}.{os.getpid()}"
    if scratch.exists():
        shutil.rmtree(scratch)
    scratch.mkdir(parents=True)
    (scratch / "package.json").write_text(
        json.dumps(
            {
                "name": "scio-deps",
                "private": True,
                "dependencies": manifest.get("dependencies", {}),
                "devDependencies": manifest.get("devDependencies", {}),
            },
            indent=2,
        )
        + "\n"
    )

    try:
        result = subprocess.run(
            ["npm", "install", "--no-audit", "--no-fund", "--loglevel=error"],
            cwd=scratch,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
            env={**os.environ, "NEXT_TELEMETRY_DISABLED": "1", "CI": "1"},
        )
    except subprocess.TimeoutExpired as exc:
        shutil.rmtree(scratch, ignore_errors=True)
        raise WorkspaceUnavailable(
            f"npm install did not finish within {timeout_s:.0f}s. Raise "
            f"{INSTALL_TIMEOUT_ENV}, or pre-install and set {SCAFFOLD_DIR_ENV}."
        ) from exc

    if result.returncode != 0 or not (scratch / "node_modules").exists():
        detail = (result.stderr or result.stdout or "").strip()[-2000:]
        shutil.rmtree(scratch, ignore_errors=True)
        raise WorkspaceUnavailable(f"npm install failed:\n{detail}")

    try:
        scratch.rename(cache)
    except OSError:
        # Another build won the race and populated the same key first — its
        # install is as good as ours, so keep theirs and drop ours.
        shutil.rmtree(scratch, ignore_errors=True)
        if not (cache / "node_modules").exists():
            raise


def _count_packages(modules: Path) -> int:
    if not modules.exists():
        return 0
    return sum(1 for entry in modules.iterdir() if not entry.name.startswith("."))


def prepare_workspace(project_id: str, *, fresh: bool = True, install: bool = True) -> Path:
    """A directory with the locked stack and its dependencies, ready to serve.

    Generated from `stack_files` and installed with npm, unless the operator
    pointed `SCIO_SCAFFOLD_DIR` at a prepared directory (or npm is unavailable
    and the repo's spike app can stand in).
    """
    target = workspace_root() / project_id
    if fresh and target.exists():
        # This deletes history. It is safe for a first build, and it is exactly
        # what ADR-0017 stopped the delivery build from doing: the design window
        # commits into this directory, and wiping it threw away both the
        # versions the user can return to and the changes they had made. Any new
        # caller that might run against an existing project must promote
        # (`stream_promotion`) rather than come through here.
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)

    scaffold = default_scaffold_dir()
    if scaffold is not None:
        _copy_prepared(scaffold, target)
        return target

    for relative, content in stack_files(project_id).items():
        path = target / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

    if not install:
        return target

    try:
        install_dependencies(target)
    except WorkspaceUnavailable:
        prepared = fallback_scaffold_dir()
        if prepared is None:
            raise
        # No npm, or no network: the repo's spike app has the same framework
        # already installed. Say so in the build rather than failing outright.
        _copy_prepared(prepared, target)
    return target


def _copy_prepared(scaffold: Path, target: Path) -> None:
    """Build the workspace from a directory that already has dependencies."""
    if not (scaffold / "node_modules").exists():
        raise WorkspaceUnavailable(
            f"{scaffold} has no node_modules. Install dependencies there first; a dev "
            "server that installs on first boot dies mid-startup (seen in the spike)."
        )
    for name in SCAFFOLD_FILES:
        source = scaffold / name
        if source.exists():
            shutil.copy2(source, target / name)

    modules = target / "node_modules"
    if not modules.exists():
        modules.symlink_to(scaffold / "node_modules", target_is_directory=True)
