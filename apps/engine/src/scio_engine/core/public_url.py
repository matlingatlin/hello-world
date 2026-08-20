"""Where a preview can be *opened* from, which is not always where it runs.

The sandbox serves a generated app on loopback, on a port picked at random, and
that URL is handed straight to a browser: the design window embeds it in an
iframe, the reveal links it. Loopback is the right answer whenever the browser
is on the same machine, and the wrong one the moment it is not — in a Codespace
the browser is on a phone, and every port is reached through its own forwarded
`https` origin instead.

So the rewrite is one substitution, driven by config and **off by default**:

    SCIO_PUBLIC_URL_TEMPLATE=https://<codespace>-{port}.app.github.dev

Nothing about the sandbox changes. The engine still starts, polls and stops the
preview over loopback — only the URL it *publishes* is translated, and only when
somebody has said what the translation is.
"""

from __future__ import annotations

import os
import re

PUBLIC_URL_TEMPLATE = "SCIO_PUBLIC_URL_TEMPLATE"
"""The shape of a forwarded URL, with `{port}` where the port goes."""

_LOOPBACK = re.compile(
    r"^(?P<scheme>https?)://(?:127\.0\.0\.1|localhost|0\.0\.0\.0)"
    r"(?::(?P<port>\d+))?(?P<path>/.*)?$"
)


def public_url(url: str, template: str | None = None) -> str:
    """Translate a loopback URL into one a browser elsewhere can open.

    Returns `url` untouched when there is no template (the local case, and the
    default), when it is empty, and — deliberately — when it is not loopback:
    a URL that is already public must never be rewritten into a second one.
    """
    pattern = os.getenv(PUBLIC_URL_TEMPLATE, "") if template is None else template
    if not pattern or not url:
        return url

    match = _LOOPBACK.match(url.strip())
    if not match:
        return url

    port = match.group("port") or ("443" if match.group("scheme") == "https" else "80")
    return pattern.replace("{port}", port).rstrip("/") + (match.group("path") or "")
