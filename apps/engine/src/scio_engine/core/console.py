"""GUARDRAIL 3 — classify console output before the vision loop judges it.

The spike found that a missing /favicon.ico logs an error on every page load, and
that the message TEXT names nothing:

    "Failed to load resource: the server responded with a status of 404"

Only the source URL identifies it. A critique agent reading raw console errors
would fail every build ever made; one filtering on text alone cannot tell this
from a real 404 on /api/bookings.

The filter is deliberately small. Every entry is a decision to let a class of
failure through unseen, so additions belong in review, not in a hotfix.
"""

from __future__ import annotations

from enum import StrEnum
from urllib.parse import urlparse

from pydantic import BaseModel, Field


class Severity(StrEnum):
    error = "error"
    warning = "warning"
    info = "info"


class Origin(StrEnum):
    app = "app"  # the generated app — the vision loop's business
    framework = "framework"  # Next/React dev-time chatter
    browser = "browser"  # the browser asking for things nobody wrote
    third_party = "third_party"  # a resource on someone else's host
    unknown = "unknown"


class ConsoleEntry(BaseModel):
    """One console message. `url` is not optional in practice — see the module docstring."""

    type: str
    text: str
    url: str = ""

    @property
    def full(self) -> str:
        return f"{self.text} ({self.url})" if self.url else self.text


class Classification(BaseModel):
    entry: ConsoleEntry
    origin: Origin
    severity: Severity
    fails_build: bool
    reason: str


# Benign browser-initiated requests. Nobody wrote them; their absence is not a defect.
BROWSER_NOISE_URLS = ("/favicon.ico", "/apple-touch-icon", "/robots.txt", "/.well-known/")

# Dev-server chatter that appears whether or not the app is correct.
FRAMEWORK_NOISE = (
    "Download the React DevTools",
    "[Fast Refresh]",
    "[HMR]",
    "webpack-hmr",
    "react-devtools",
)


LOCAL_HOSTS = ("127.0.0.1", "localhost", "0.0.0.0", "::1")
"""Where the sandbox serves the generated app. Anything else is someone else's
host, and whether it answers is not a fact about the code we just wrote."""


def _is_third_party(url: str) -> bool:
    """A resource on a host that is not the app's own.

    The second real run failed a package because fonts.googleapis.com was
    unreachable from the sandbox — ERR_CONNECTION_RESET, classified as an error
    from "the app's own code or resources". A build must not turn on whether the
    machine running it can reach a CDN. It stays visible in `suppressed`, like
    every other thing this filter lets past.
    """
    if not url.startswith(("http://", "https://")):
        return False
    host = urlparse(url).hostname or ""
    return host not in LOCAL_HOSTS


def _origin_of(entry: ConsoleEntry) -> Origin:
    haystack = entry.full
    if any(path in haystack for path in BROWSER_NOISE_URLS):
        return Origin.browser
    if any(marker in haystack for marker in FRAMEWORK_NOISE):
        return Origin.framework
    if _is_third_party(entry.url):
        return Origin.third_party
    if entry.url:
        return Origin.app
    return Origin.unknown


def classify(entry: ConsoleEntry) -> Classification:
    """Decide whether this message says anything about the generated app."""
    origin = _origin_of(entry)
    severity = {
        "error": Severity.error,
        "warning": Severity.warning,
        "warn": Severity.warning,
    }.get(entry.type, Severity.info)

    if origin is Origin.browser:
        return Classification(
            entry=entry,
            origin=origin,
            severity=severity,
            fails_build=False,
            reason=(
                "Browser-initiated request for an asset nobody wrote (e.g. favicon). "
                "Absent by default, not a defect."
            ),
        )

    if origin is Origin.framework:
        return Classification(
            entry=entry,
            origin=origin,
            severity=Severity.info,
            fails_build=False,
            reason="Dev-server chatter; appears whether or not the app is correct.",
        )

    if origin is Origin.third_party:
        return Classification(
            entry=entry,
            origin=origin,
            severity=severity,
            fails_build=False,
            reason=(
                "A resource on someone else's host did not load. That is the network "
                "or that host, not the generated code — reported, never a failed build."
            ),
        )

    fails = severity is Severity.error
    return Classification(
        entry=entry,
        origin=origin,
        severity=severity,
        fails_build=fails,
        reason=(
            "Error from the app's own code or resources."
            if fails
            else "Not an error-level message from the app."
        ),
    )


class ConsoleReport(BaseModel):
    """What the vision loop should act on."""

    classifications: list[Classification] = Field(default_factory=list)
    page_errors: list[str] = Field(default_factory=list)

    @property
    def failures(self) -> list[str]:
        """Only the messages that mean the generated app is broken."""
        return [c.entry.full for c in self.classifications if c.fails_build] + self.page_errors

    @property
    def suppressed(self) -> list[str]:
        """Errors deliberately ignored — surfaced so the filter stays auditable
        rather than becoming a place failures go to hide."""
        return [
            c.entry.full
            for c in self.classifications
            if c.severity is Severity.error and not c.fails_build
        ]

    @property
    def clean(self) -> bool:
        return not self.failures


def classify_console(
    entries: list[ConsoleEntry], page_errors: list[str] | None = None
) -> ConsoleReport:
    """Uncaught page errors are always real: nothing but the app throws them."""
    return ConsoleReport(
        classifications=[classify(entry) for entry in entries],
        page_errors=list(page_errors or []),
    )
