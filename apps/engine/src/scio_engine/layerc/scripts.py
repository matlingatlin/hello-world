"""Turning a feature's architecture into the script that proves it works.

Deterministic, and deliberately so. "Does the booking actually save?" is not a
question of taste, and asking a model to invent the steps would make the one
criterion that gates the build the least reproducible thing in the pipeline.
Everything here is read off the graph: the create operation's inputs become the
fields to fill, the screens become the routes to visit, the entity becomes the
table to look in.

Two scripts come out of a feature:

- **persistence** — fill the create form, submit, load the list route *again*,
  and check both the page and the database. The reload is the point: without it
  the assertion passes on React state that never reached Postgres.
- **isolation** — the same, twice, as two different users, and then check that
  neither sees the other's row. It asserts the user's OWN row is present too,
  because "nobody can see anything" is not isolation, it is a broken list.

Both refuse to be emitted when the architecture cannot support them — no create
operation, no screen to drive, no identity to isolate by. A script that cannot
be derived honestly is left underived, and the criterion stays what B054 made
it: recorded, and judged by nobody.
"""

from __future__ import annotations

from ..core.interaction import (
    Script,
    as_user,
    assert_absent,
    assert_present,
    assert_row,
    click,
    fill,
    reload,
)
from ..layerb.architecture import (
    Architecture,
    AuthMode,
    Column,
    FieldType,
    Operation,
    Screen,
    Table,
)

ALICE = "11111111-1111-1111-1111-111111111111"
BOB = "22222222-2222-2222-2222-222222222222"
"""The two users the isolation script acts as — the claim GUCs B060a reads."""

MARKER = "{{marker}}"
MARKER_A = "{{marker_a}}"
MARKER_B = "{{marker_b}}"
"""Filled in per attempt (core.interaction.resolve). They must differ between
attempts, or attempt 2 would pass on the row attempt 1 left behind."""

CREATE_VERBS = {"create", "add", "book", "submit", "new", "register", "insert"}

# Types a text box can be filled with, and what to put in one. Anything else —
# a checkbox, a select, a generated id — is left to the app's own default: a
# script that guesses at a <select> fails a working form.
_SAMPLE: dict[FieldType, str] = {
    FieldType.text: "",  # the marker goes here
    FieldType.integer: "2",
    FieldType.decimal: "2",
    FieldType.date: "2030-06-01",
    FieldType.timestamp: "2030-06-01T12:00",
}

_SKIP_COLUMNS = {"id", "created_at", "updated_at", "cancelled_at"}


def is_create(op: Operation) -> bool:
    """A create operation, by verb or by name. Both are canonicalised upstream,
    so this stays a lookup rather than a guess."""
    return op.verb.lower() in CREATE_VERBS or op.name.split("_")[0] in CREATE_VERBS


def _owner_column(table: Table | None) -> str:
    """The column that says whose row it is. Without one there is nothing for a
    policy to isolate by, whatever the posture claims."""
    if table is None:
        return ""
    names = {c.name for c in table.columns}
    for candidate in ("user_id", "owner_id", "owner", "created_by", "author_id", "guest_id"):
        if candidate in names:
            return candidate
    for relation in table.relations:
        if relation.to_table in {"user", "users", "profile", "profiles"}:
            return relation.from_column
    return ""


def _fillable(op: Operation, table: Table | None, owner: str) -> list[Column]:
    """The inputs a browser can type into.

    The operation's declared inputs when it has them; otherwise the table's own
    columns, minus the ones the database fills in and the one that records who
    the row belongs to — a form that let the user type their own owner id would
    be the security hole, not the feature.
    """
    columns = list(op.inputs) or [c for c in (table.columns if table else [])]
    return [
        c
        for c in columns
        if c.name not in _SKIP_COLUMNS and c.name != owner and c.type in _SAMPLE
    ]


def _marker_column(columns: list[Column]) -> Column | None:
    """The field that carries the unique value the assertions look for. A text
    field, because it survives a round trip through the page unchanged."""
    return next((c for c in columns if c.type is FieldType.text), None)


def _fills(
    entity: str, columns: list[Column], marker: str, marker_column: Column | None
) -> list:
    return [
        fill(
            f"{entity}-form-{_kebab(column.name)}",
            marker if column is marker_column else _SAMPLE[column.type],
            # The id is the builder's to choose; the field's `name` is the
            # schema's. See core/interaction on why the fallback exists.
            fallback=f'form [name="{column.name}"]',
        )
        for column in columns
    ]


def _kebab(name: str) -> str:
    return name.replace("_", "-")


def _create_route(screens: list[Screen], op: Operation) -> str:
    """The screen that runs the create operation."""
    owning = [s for s in screens if op.name in s.operations]
    if not owning:
        return ""
    # The most specific route: /booking/new over /booking, when both offer it.
    return sorted(owning, key=lambda s: (-len(s.route), s.route))[0].route


def _list_route(screens: list[Screen], create_route: str) -> str:
    """Where the result should show up afterwards.

    The shallowest route the feature owns — `/booking` rather than
    `/booking/new` — which is the list in every layout this stack produces.
    """
    candidates = [s.route for s in screens if s.route != create_route]
    if not candidates:
        return create_route
    return sorted(candidates, key=lambda r: (len(r), r))[0]


def persistence_script(
    arch: Architecture, entity: str, op: Operation, screens: list[Screen]
) -> Script | None:
    """Create it through the UI, load the page again, and look — twice."""
    table = arch.data_model.get(entity)
    owner = _owner_column(table)
    columns = _fillable(op, table, owner)
    create_route = _create_route(screens, op)
    if not columns or not create_route:
        return None

    marker_column = _marker_column(columns)
    list_route = _list_route(screens, create_route)

    steps = []
    if arch.auth_access.mode is not AuthMode.none:
        # An app with accounts inserts as somebody; anonymous would be refused
        # by its own policy, and that is not the failure we are looking for.
        steps.append(as_user(ALICE))
    steps += _fills(entity, columns, MARKER, marker_column)
    steps.append(click(f"{entity}-form-submit", fallback='form button[type="submit"]'))
    # A NEW page load. Everything before this could be React state.
    steps.append(reload(list_route))
    if marker_column is not None:
        steps.append(assert_present(text=MARKER))
        steps.append(assert_row(entity, {marker_column.name: MARKER}))
    else:
        steps.append(assert_present(f"{entity}-row-*"))
        steps.append(assert_row(entity, {}))

    return Script(name=f"{op.name} persists", route=create_route, steps=steps)


def isolation_script(
    arch: Architecture, entity: str, op: Operation, screens: list[Screen]
) -> Script | None:
    """Two users, one table: each sees their own row and only their own."""
    table = arch.data_model.get(entity)
    owner = _owner_column(table)
    if table is None or not owner or not table.row_level_security:
        return None
    if arch.auth_access.mode is AuthMode.none and not arch.auth_access.identifies_users:
        # No identity, nothing to isolate by. Claiming otherwise would fail
        # every guest app for a policy it was right not to have.
        return None

    columns = _fillable(op, table, owner)
    marker_column = _marker_column(columns)
    create_route = _create_route(screens, op)
    if not columns or marker_column is None or not create_route:
        return None

    list_route = _list_route(screens, create_route)

    def creates(actor: str, marker: str) -> list:
        return [
            as_user(actor),
            reload(create_route),
            *_fills(entity, columns, marker, marker_column),
            click(f"{entity}-form-submit", fallback='form button[type="submit"]'),
            reload(list_route),
        ]

    steps = [
        *creates(ALICE, MARKER_A),
        # Alice sees her own — so a later "Bob sees nothing" cannot be the list
        # being broken for everyone.
        assert_present(text=MARKER_A),
        *creates(BOB, MARKER_B),
        assert_present(text=MARKER_B),
        assert_absent(text=MARKER_A),
    ]
    return Script(name=f"{entity} rows are private to their owner", route=create_route, steps=steps)
