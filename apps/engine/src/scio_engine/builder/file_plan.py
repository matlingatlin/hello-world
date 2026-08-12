"""Which files each package owns.

Layer C says a package owns architecture *nodes*; somebody has to decide which
paths those become. That decision is deterministic and lives here, following the
playbook's folder structure — not left to the model, because the manifest's
package→file map depends on it and a model that renames a folder would silently
break the marking→code coupling.
"""

from __future__ import annotations

from ..layerc.plan import BuildPackage, PackageKind


def entity_of(package: BuildPackage) -> str:
    """The entity a feature package is about, from its id."""
    prefix = "pkg_feature_"
    return package.id[len(prefix) :] if package.id.startswith(prefix) else ""


def connector_of(package: BuildPackage) -> str:
    prefix = "pkg_connector_"
    return package.id[len(prefix) :] if package.id.startswith(prefix) else "connector"


def planned_files(package: BuildPackage) -> list[str]:
    """The paths this package may write. Anything else the model returns is dropped."""
    if package.kind is PackageKind.foundation:
        files = ["app/layout.tsx", "components/site-header.tsx", "lib/supabase.ts"]
        files += [
            _route_to_page(node.name)
            for node in package.architecture_slice
            if node.kind == "screen"
        ]
        return sorted(set(files))

    if package.kind is PackageKind.schema:
        return ["supabase/migrations/0001_init.sql", "types/database.ts"]

    if package.kind is PackageKind.auth:
        return ["lib/auth.ts", "tests/auth.test.ts"]

    if package.kind is PackageKind.design_tokens:
        return ["app/globals.css", "tailwind.config.ts"]

    if package.kind is PackageKind.connector:
        name = connector_of(package)
        return [f"lib/connectors/{name}.ts", f"tests/{name}.test.ts"]

    # feature
    entity = entity_of(package) or "feature"
    files = [
        f"components/{entity}-form.tsx",
        f"components/{entity}-list.tsx",
        f"lib/db/{entity}.ts",
        f"tests/{entity}.test.ts",
    ]
    files += [
        _route_to_page(node.name)
        for node in package.architecture_slice
        if node.kind == "screen"
    ]
    return sorted(set(files))


def _route_to_page(route: str) -> str:
    """`/booking/new` -> `app/booking/new/page.tsx`; `/` -> `app/page.tsx`."""
    segments = [segment for segment in route.strip("/").split("/") if segment]
    return "app/" + "/".join([*segments, "page.tsx"]) if segments else "app/page.tsx"


def file_plan(packages: list[BuildPackage]) -> dict[str, list[str]]:
    """package id -> files, for the whole plan. This is the manifest's spine."""
    return {package.id: planned_files(package) for package in packages}
