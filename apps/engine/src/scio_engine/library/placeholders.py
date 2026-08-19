"""The placeholders an entry is written against.

In their own module because both `entry` (which substitutes them) and `identity`
(which generalises code back into them) need them, and importing either from the
other would make a cycle.
"""

from __future__ import annotations

ENTITY = "__ENTITY__"
ENTITY_PASCAL = "__ENTITY_PASCAL__"
ENTITY_TITLE = "__ENTITY_TITLE__"
ENTITY_PLURAL = "__ENTITY_PLURAL__"
ENTITY_PLURAL_TITLE = "__ENTITY_PLURAL_TITLE__"

TOKEN_PREFIX = "__TOKEN_"
