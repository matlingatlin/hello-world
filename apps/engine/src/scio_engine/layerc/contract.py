"""Contract assembly — the per-package prompt substrate (docs/LAYER-C.md).

Each package gets exactly what it needs and nothing more: its goal, the slice of
the architecture it owns, the *interfaces* of what it depends on, the relevant
"why", the house rules, the canonical vocabulary, the scope guard, and its
acceptance criteria. Tight context is the whole reason to decompose at all.
"""

from __future__ import annotations

from ..layerb.architecture import Architecture
from ..layerb.playbook import Playbook, default_playbook
from .plan import BuildPackage, BuildPlan, PackageKind


def why_slice(package: BuildPackage, whole: str, arch: Architecture) -> str:
    """The part of the whole this package serves.

    The whole is prose, so we don't try to cut it cleverly — a package gets the
    whole plus a sentence naming its part in it. Wrong-but-confident slicing
    would be worse than carrying two extra paragraphs.
    """
    role = {
        PackageKind.foundation: "This package lays the ground everything else is built on.",
        PackageKind.schema: "This package creates the data the app is about.",
        PackageKind.auth: "This package decides who the users are and what they may reach.",
        PackageKind.feature: "This package builds one of the things the user asked for.",
        PackageKind.connector: "This package connects the app to an outside service.",
        PackageKind.design_tokens: "This package sets how the app looks, consistently.",
    }[package.kind]
    parts = [role]
    if whole:
        parts += ["", "The project as a whole:", whole]
    return "\n".join(parts)


def dependency_interfaces(package: BuildPackage, plan: BuildPlan) -> list[str]:
    """What already exists that this package may lean on — names and shapes only."""
    lines: list[str] = []
    for dep_id in package.dependencies:
        dep = plan.get(dep_id)
        if dep is None:
            continue
        detail = dep.interface.as_lines()
        lines.append(f"- {dep.id} ({dep.kind}): {dep.goal}")
        lines += [f"    {line}" for line in detail]
    return lines


def architecture_slice_text(package: BuildPackage, arch: Architecture) -> str:
    """The architecture nodes this package owns, rendered in full detail."""
    lines: list[str] = []
    for node in package.architecture_slice:
        if node.kind == "table":
            table = arch.data_model.get(node.name)
            if table:
                lines.append(f"table {table.name} (row-level security: {table.row_level_security})")
                lines += [
                    f"    {c.name}: {c.type}{'' if not c.nullable else ' (nullable)'}"
                    f"{' — ' + c.description if c.description else ''}"
                    for c in table.columns
                ]
                lines += [
                    f"    FK {r.from_column} -> {r.to_table}.{r.to_column}"
                    for r in table.relations
                ]
        elif node.kind == "operation":
            op = next((o for o in arch.operations if o.name == node.name), None)
            if op:
                inputs = ", ".join(f"{c.name}: {c.type}" for c in op.inputs) or "none"
                lines.append(
                    f"operation {op.name} — {op.description or op.verb} "
                    f"on {op.entity or '(no entity)'}; inputs: {inputs}; "
                    f"returns: {', '.join(op.outputs) or 'nothing'}"
                )
        elif node.kind == "screen":
            screen = next(
                (s for s in arch.screens_routing.screens if s.route == node.name), None
            )
            if screen:
                lines.append(
                    f"screen {screen.name} at {screen.route} — {screen.purpose}; "
                    f"uses: {', '.join(screen.operations) or 'no operations'}"
                    + (f"; requires role: {screen.requires_role}" if screen.requires_role else "")
                )
        elif node.kind == "connector":
            connector = next((c for c in arch.connectors if c.name == node.name), None)
            if connector:
                lines.append(
                    f"connector {connector.name} ({connector.kind}) — {connector.detail}; "
                    f"secrets: {', '.join(connector.secrets) or 'none'}"
                )
        elif node.kind == "auth":
            auth = arch.auth_access
            lines.append(
                f"auth mode: {auth.mode}"
                + (f" via {auth.provider}" if auth.provider else "")
                + (
                    f"; identity fields: {', '.join(auth.identity_fields)}"
                    if auth.identity_fields
                    else ""
                )
            )
            lines += [f"    role {r.name}: {r.description or r.name}" for r in auth.roles]
            lines += [f"    {p.role} may {p.operation} ({p.scope})" for p in auth.permissions]
        elif node.kind == "tokens":
            tokens = arch.design_tokens
            lines.append(f"design tokens ({tokens.source}): {tokens.notes}")
            lines += [f"    palette {k}: {v}" for k, v in tokens.palette.items()]
            lines += [f"    type {k}: {v}" for k, v in tokens.typography.items()]
        elif node.kind == "security":
            posture = arch.security_posture
            lines.append(
                f"security posture: RLS={posture.row_level_security}, "
                f"input validation={posture.input_validation}, "
                f"secrets in env only={posture.secrets_in_env_only}, "
                f"sensitive={posture.sensitive}"
            )
            lines += [f"    note: {n}" for n in posture.compliance_notes]
    return "\n".join(lines)


def assemble_contract(
    package: BuildPackage,
    plan: BuildPlan,
    arch: Architecture,
    *,
    whole: str = "",
    playbook: Playbook | None = None,
) -> BuildPackage:
    """Fill in the package's contract fields. Returns the same package, completed."""
    book = playbook or default_playbook()
    package.why = why_slice(package, whole, arch)
    package.house_rules = book.as_prompt_section()
    package.canonical_vocabulary = dict(arch.vocabulary)
    package.scope_guard = list(arch.scope_guard)
    return package


def contract_prompt(package: BuildPackage, plan: BuildPlan, arch: Architecture) -> str:
    """The package's contract as the prompt the builder will run."""
    parts = [
        f"# Build package: {package.id} ({package.kind})",
        "",
        "## Goal",
        package.goal,
        "",
        "## The architecture you own (build exactly this)",
        architecture_slice_text(package, arch) or "(nothing)",
    ]

    interfaces = dependency_interfaces(package, plan)
    if interfaces:
        parts += [
            "",
            "## Already built — use these, do not rebuild them",
            *interfaces,
        ]

    # Stated explicitly because a real model does not infer it: on the first real
    # run the foundation package imported `@/lib/env` and `@/types/supabase`,
    # neither of which any package produces. A deterministic guardrail catches it
    # (validation.py), but saying so up front is cheaper than a repair round.
    parts += [
        "",
        "## Import boundary (enforced)",
        "You may import ONLY from:",
        "- files this package writes (listed below), and",
        (
            "- the packages it depends on: "
            + (", ".join(package.dependencies) if package.dependencies else "none")
            + " — through the interfaces above."
        ),
        "- npm dependencies from package.json (next, react, @supabase/supabase-js, …).",
        "Do not import a file no package produces, and never invent a helper module: "
        "if you need it, write it inside one of your own files.",
    ]

    if package.why:
        parts += ["", "## Why this exists", package.why]

    if package.canonical_vocabulary:
        parts += [
            "",
            "## Canonical vocabulary — use exactly these names",
            ", ".join(sorted(package.canonical_vocabulary)),
        ]

    if package.scope_guard:
        parts += ["", "## Out of scope — do not build", *[f"- {s}" for s in package.scope_guard]]

    parts += [
        "",
        "## Done when",
        *[f"- {c}" for c in package.acceptance_criteria],
        "",
        package.house_rules,
    ]
    return "\n".join(parts)
