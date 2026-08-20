"""Deterministic decomposition: architecture graph -> build packages (docs/LAYER-C.md).

Rules group the nodes — foundation, schema, auth, one package per feature,
connectors, design tokens — and a topological sort turns the dependency edges
into the build sequence. No model call happens here; the LLM is reserved for
genuinely ambiguous grouping (see judgment.py).

Granularity is per feature: an entity's operations plus its screens. Per file
would be too fine to stay coherent; per app would be the huge-context failure
mode Scio exists to fix.
"""

from __future__ import annotations

from ..layerb.architecture import Architecture, AuthMode, Operation, Screen
from .criteria import Criterion, checked, interacts, renders, unobservable
from .plan import BuildPackage, BuildPlan, NodeRef, PackageInterface, PackageKind
from .scripts import is_create, isolation_script, persistence_script

FOUNDATION_ID = "pkg_foundation"
SCHEMA_ID = "pkg_schema"
AUTH_ID = "pkg_auth"
TOKENS_ID = "pkg_design_tokens"


class CyclicPlanError(ValueError):
    """Raised when the dependency graph cannot be ordered."""


def architecture_nodes(arch: Architecture) -> list[NodeRef]:
    """Every node a package must cover. Coverage is checked against this list,
    so anything addable to the architecture must be addable here too."""
    nodes = [NodeRef(kind="table", name=t.name) for t in arch.data_model.tables]
    nodes += [NodeRef(kind="operation", name=op.name) for op in arch.operations]
    nodes += [NodeRef(kind="screen", name=s.route) for s in arch.screens_routing.screens]
    nodes += [NodeRef(kind="connector", name=c.name) for c in arch.connectors]
    nodes.append(NodeRef(kind="auth", name="auth_access"))
    nodes.append(NodeRef(kind="tokens", name="design_tokens"))
    nodes.append(NodeRef(kind="security", name="security_posture"))
    return nodes


def _shell_screens(arch: Architecture) -> list:
    """Screens that carry no operations — home, orientation, navigation. They
    belong to the shell; without this they'd belong to no feature and quietly
    vanish from the built app."""
    return [s for s in arch.screens_routing.screens if not s.operations]


def _foundation_package(arch: Architecture) -> BuildPackage:
    shell_screens = _shell_screens(arch)
    routes = [s.route for s in shell_screens]
    return BuildPackage(
        id=FOUNDATION_ID,
        kind=PackageKind.foundation,
        # The goal names only what this package's files can deliver. It used to
        # promise linting and a test runner as well — neither of which is in its
        # file plan, and the stack itself is scaffolded by the workspace before a
        # package runs (builder/workspace.py). Asking for them here only invited
        # code with nowhere to live.
        goal=(
            "Build the app shell on the locked stack (Next.js + TypeScript + Tailwind): the "
            "root layout, the navigation, and the Supabase client the rest of the app uses"
            + (f", plus the shell screens ({', '.join(routes)})." if routes else ".")
        ),
        architecture_slice=[
            NodeRef(kind="security", name="security_posture"),
            *[NodeRef(kind="screen", name=route) for route in routes],
        ],
        dependencies=[],
        interface=PackageInterface(
            routes=routes,
            exports=["app shell", "navigation", "supabase client", "test runner", "lint config"],
        ),
        acceptance_criteria=[
            # The shell's job, and only the shell's job. The first real run failed
            # this package for not proving a test runner and security headers it
            # does not own and nobody could observe — see criteria.py.
            renders(
                "The app shell renders: the page loads with its header and navigation.",
                "app/layout.tsx",
                "components/",
            ),
            renders("The page loads with no console errors caused by the app itself."),
            *(
                [
                    renders(
                        "The shell screens render and navigation reaches them: "
                        f"{', '.join(routes)}.",
                        "page.tsx",
                    )
                ]
                if routes
                else []
            ),
            checked(
                "Secrets are read from environment variables only.",
                "lib/supabase.ts",
            ),
            unobservable(
                "The test runner executes and passes on an empty suite.",
            ),
            unobservable(
                "Secure defaults from the playbook are configured "
                "(headers, input validation helper).",
            ),
        ],
    )


def _schema_package(arch: Architecture) -> BuildPackage:
    tables = [t.name for t in arch.data_model.tables]
    # A migration renders nothing, so none of this is the critique's to judge.
    criteria = [
        checked(
            "Every table exists with its columns, keys and timestamps.",
            "supabase/migrations/",
        ),
        checked(
            "Row-level security is enabled on every table with explicit policies.",
            "supabase/migrations/",
        ),
        unobservable("Foreign keys resolve and migrations run cleanly from empty."),
    ]
    if not tables:
        criteria = [checked("No tables are required by the architecture.")]
    return BuildPackage(
        id=SCHEMA_ID,
        kind=PackageKind.schema,
        goal=(
            "Create the Supabase schema: "
            + (", ".join(tables) if tables else "no tables required")
            + " — as SQL migrations, with row-level security on."
        ),
        architecture_slice=[NodeRef(kind="table", name=name) for name in tables],
        dependencies=[FOUNDATION_ID],
        interface=PackageInterface(tables=tables, exports=["generated database types"]),
        acceptance_criteria=criteria,
    )


def _auth_package(arch: Architecture) -> BuildPackage:
    auth = arch.auth_access
    if auth.mode is AuthMode.none:
        goal = (
            "Set up identification without accounts: guests are identified by "
            f"{', '.join(auth.identity_fields) or 'contact details'}. Deliberately no auth "
            "tables, no sessions, no login UI."
        )
        criteria = [
            checked("No authentication tables, providers or login screens exist.", "lib/auth.ts"),
            checked(
                f"Records capture {', '.join(auth.identity_fields) or 'contact details'} instead.",
                "lib/auth.ts",
            ),
        ]
        exports = ["guest identification helper"]
    else:
        roles = ", ".join(r.name for r in auth.roles) or "a single role"
        goal = (
            f"Set up {auth.mode.value} sign-in via {auth.provider}, with sessions and the "
            f"access rules for {roles}."
        )
        criteria = [
            # The auth package writes helpers, not screens, and the vision loop
            # loads one page — it cannot sign in, sign out and reload.
            unobservable("A user can sign in and out; sessions persist across reloads."),
            checked(
                "Server-side authorization is enforced per operation, not only in the UI.",
                "lib/auth.ts",
            ),
            unobservable("A user cannot read or change another user's rows (covered by a test)."),
        ]
        exports = ["session helper", "authorization guard"]

    return BuildPackage(
        id=AUTH_ID,
        kind=PackageKind.auth,
        goal=goal,
        architecture_slice=[NodeRef(kind="auth", name="auth_access")],
        dependencies=[FOUNDATION_ID, SCHEMA_ID],
        interface=PackageInterface(exports=exports),
        acceptance_criteria=criteria,
    )


def _it_actually_works(
    arch: Architecture, entity: str, ops: list[Operation], screens: list[Screen]
) -> list[Criterion]:
    """The criteria that say the feature WORKS, not merely that it rendered.

    B054 had to scope these out: the evidence was one page load, so "the booking
    persists" and "a guest cannot read another guest's booking" were recorded as
    regrets and judged by nobody. With the interaction channel (B060b) they are
    scripts — filled in, submitted, reloaded, and looked for in the database —
    and they gate the build like every other criterion.

    Where a script cannot be derived honestly (an operation with no screen to
    drive, an app with no identity to isolate by) the criterion stays exactly
    what it was. An interaction criterion nobody can run would fail every build
    for a channel that never looked.
    """
    criteria: list[Criterion] = []

    for op in ops:
        label = op.description or op.name
        script = persistence_script(arch, entity, op, screens) if is_create(op) else None
        if script is None:
            criteria.append(unobservable(f"'{label}' works end to end and persists."))
            continue
        criteria.append(
            interacts(
                f"'{label}' works end to end and persists: filled in through the form, "
                "submitted, and still on the page and in the database after a fresh load.",
                script,
                f"components/{entity}-form.tsx",
                f"app/actions/{entity}.ts",
            )
        )

    isolation = next(
        (
            script
            for op in ops
            if is_create(op)
            and (script := isolation_script(arch, entity, op, screens)) is not None
        ),
        None,
    )
    if isolation is not None:
        criteria.append(
            interacts(
                f"A user cannot read another user's {entity}: "
                f"each of two users sees their own row and not the other's.",
                isolation,
                f"components/{entity}-list.tsx",
                f"lib/db/{entity}.ts",
            )
        )

    return criteria


def _feature_packages(arch: Architecture) -> list[BuildPackage]:
    """One package per feature: an entity's operations plus the screens that use
    them. Operations with no entity are grouped under a "general" feature so
    nothing is silently dropped — validation then reports them if they are
    genuinely unattached."""
    by_entity: dict[str, list] = {}
    for op in arch.operations:
        by_entity.setdefault(op.entity or "general", []).append(op)

    packages: list[BuildPackage] = []
    for entity, ops in by_entity.items():
        op_names = {op.name for op in ops}
        screens = [
            s
            for s in arch.screens_routing.screens
            if s.operations and set(s.operations) & op_names
        ]
        protected = any(s.requires_role for s in screens) or bool(arch.auth_access.permissions)

        slice_nodes = [NodeRef(kind="operation", name=op.name) for op in ops]
        slice_nodes += [NodeRef(kind="screen", name=s.route) for s in screens]

        dependencies = [FOUNDATION_ID, SCHEMA_ID, TOKENS_ID]
        if protected or arch.auth_access.mode is not AuthMode.none:
            dependencies.append(AUTH_ID)

        packages.append(
            BuildPackage(
                id=f"pkg_feature_{entity}",
                kind=PackageKind.feature,
                goal=(
                    f"Build the {entity} feature: "
                    + ", ".join(op.description or op.name for op in ops)
                    + (
                        f" — with the screens {', '.join(s.route for s in screens)}."
                        if screens
                        else " (no dedicated screen)."
                    )
                ),
                architecture_slice=slice_nodes,
                dependencies=dependencies,
                interface=PackageInterface(
                    operations=sorted(op_names),
                    routes=sorted(s.route for s in screens),
                ),
                acceptance_criteria=[
                    # What one page load settles: the screen rendered and the
                    # controls for each operation are on it. Whether a booking
                    # survives a round trip is a different question, asked by a
                    # different channel — see _it_actually_works below.
                    *(
                        renders(
                            f"The interface for '{op.description or op.name}' is on the "
                            "screen and reachable.",
                            "components/",
                        )
                        if screens
                        else checked(
                            f"'{op.description or op.name}' is implemented against the schema.",
                            "lib/db/",
                        )
                        for op in ops
                    ),
                    *(
                        [
                            renders(
                                "The screens render without console errors.",
                                "page.tsx",
                            )
                        ]
                        if screens
                        else []
                    ),
                    *_it_actually_works(arch, entity, ops, screens),
                    checked(
                        "The feature's data access is implemented.",
                        "lib/db/",
                    ),
                    checked(
                        "Inputs are validated server-side and invalid input is rejected clearly.",
                        "lib/validation/",
                    ),
                    checked(
                        "Each operation has a test for its happy path and its main failure.",
                        "tests/",
                    ),
                ],
            )
        )
    return packages


def _connector_packages(arch: Architecture) -> list[BuildPackage]:
    return [
        BuildPackage(
            id=f"pkg_connector_{connector.name}",
            kind=PackageKind.connector,
            goal=f"Wire up the {connector.kind} connector: {connector.detail}",
            architecture_slice=[NodeRef(kind="connector", name=connector.name)],
            dependencies=[FOUNDATION_ID, SCHEMA_ID],
            interface=PackageInterface(exports=[f"{connector.name} client"]),
            acceptance_criteria=[
                unobservable(
                    f"The {connector.kind} integration works against its sandbox/test mode."
                ),
                checked(
                    "Credentials come from environment variables; none appear in code or logs.",
                    "lib/connectors/",
                ),
                checked(
                    "Failures degrade gracefully with a clear message rather than crashing.",
                    "lib/connectors/",
                ),
            ],
        )
        for connector in arch.connectors
    ]


def _tokens_package(arch: Architecture) -> BuildPackage:
    return BuildPackage(
        id=TOKENS_ID,
        kind=PackageKind.design_tokens,
        goal=(
            "Encode the design tokens (palette, typography, radius) as CSS variables and a "
            "Tailwind theme, so every screen styles from tokens rather than ad-hoc values. "
            "Load typefaces with next/font so they are served from this app, never with an "
            "@import or <link> to a font CDN."
        ),
        architecture_slice=[NodeRef(kind="tokens", name="design_tokens")],
        dependencies=[FOUNDATION_ID],
        interface=PackageInterface(exports=["design tokens", "tailwind theme"]),
        # This package writes a stylesheet and a Tailwind config. Nothing it
        # produces is markup, so nothing it does can be judged from a rendered
        # page — the second real run failed it for exactly that, asking for
        # "computed CSS variable values" the evidence never carries.
        acceptance_criteria=[
            checked(
                "Tokens are defined once and consumed by the Tailwind config.",
                "tailwind.config.ts",
            ),
            checked(
                "The palette and typography are defined as CSS variables.",
                "app/globals.css",
            ),
            checked(
                "No hard-coded colours or font families outside the token definitions.",
                "app/globals.css",
            ),
            # Measured, not theoretical: a real build shipped
            # `@import url('https://fonts.googleapis.com/…')` here, and the app
            # then waited 12.7s on a host the network would not reach.
            checked(
                "Typefaces load via next/font, not an @import or <link> to a font CDN — "
                "a third-party font request blocks the first paint.",
                "app/globals.css",
            ),
        ],
    )


def decompose(arch: Architecture) -> list[BuildPackage]:
    """Group the architecture graph into packages. Deterministic."""
    packages = [
        _foundation_package(arch),
        _schema_package(arch),
        _tokens_package(arch),
        _auth_package(arch),
        *_feature_packages(arch),
        *_connector_packages(arch),
    ]
    return packages


def topological_order(packages: list[BuildPackage]) -> list[str]:
    """Build sequence from the dependency edges (Kahn's algorithm).

    Ties are broken by package id so the order is reproducible — a plan that
    shuffles between runs would make diffing builds impossible.
    """
    ids = {p.id for p in packages}
    remaining = {p.id: {d for d in p.dependencies if d in ids} for p in packages}
    order: list[str] = []

    while remaining:
        ready = sorted(pid for pid, deps in remaining.items() if not deps)
        if not ready:
            raise CyclicPlanError(
                "Dependency cycle among packages: " + ", ".join(sorted(remaining))
            )
        for pid in ready:
            order.append(pid)
            del remaining[pid]
        for deps in remaining.values():
            deps.difference_update(ready)
    return order


def mark_parallelizable(packages: list[BuildPackage]) -> None:
    """Flag packages that share no dependency path with a sibling of the same
    kind. MVP builds sequentially; this is the information a later scheduler
    needs, recorded now while the graph is in hand."""
    features = [p for p in packages if p.kind is PackageKind.feature]
    connectors = [p for p in packages if p.kind is PackageKind.connector]
    for group in (features, connectors):
        if len(group) > 1:
            for package in group:
                package.parallelizable = True


def build_plan(arch: Architecture) -> BuildPlan:
    """The deterministic plan: packages, dependency graph, build order."""
    packages = decompose(arch)
    mark_parallelizable(packages)
    order = topological_order(packages)
    return BuildPlan(
        packages=packages,
        order=order,
        graph={p.id: list(p.dependencies) for p in packages},
    )
