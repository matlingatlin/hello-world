"""The preview's senses: screenshot, classified console, and click resolution.

Playwright drives a headless browser against the running sandbox. This is what
the vision loop sees and what the design window points at.

Playwright is an optional extra so the rest of the core (and its tests) run
without a browser; `is_available()` says whether it can be used here.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from .console import ConsoleEntry, ConsoleReport, classify_console
from .resolver import RESOLVE_AT_POINT_JS, ElementHit


def playwright_available() -> bool:
    try:
        import playwright.sync_api  # noqa: F401
    except ImportError:
        return False
    return True


def chromium_executable() -> str | None:
    """The pre-installed Chromium, when the SDK's pinned build differs.

    Environments that ship browsers under PLAYWRIGHT_BROWSERS_PATH and block
    `playwright install` need this; returning None lets Playwright resolve its
    own when the versions match.
    """
    root = Path(os.getenv("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers"))
    if not root.exists():
        return None
    candidates = sorted(root.glob("chromium-*/chrome-linux/chrome"))
    return str(candidates[-1]) if candidates else None


@dataclass
class Observation:
    """One look at the running app."""

    screenshot_path: Path | None
    console: ConsoleReport
    title: str = ""
    hits: list[ElementHit] = field(default_factory=list)
    observed: bool = True
    """False when nobody looked. An empty console then means "unknown", not
    "clean", and whatever reads this has to say so rather than pass a gate on
    evidence it never gathered."""

    @property
    def clean(self) -> bool:
        return self.console.clean

    @classmethod
    def blind(cls) -> Observation:
        """What we know about a page nobody could open."""
        return cls(screenshot_path=None, console=classify_console([], []), observed=False)


class PreviewInspector:
    """Opens the preview and answers questions about it."""

    def __init__(self, url: str, *, viewport: tuple[int, int] = (1024, 900)) -> None:
        self.url = url
        self.viewport = viewport

    @staticmethod
    def is_available() -> bool:
        return playwright_available()

    def _launch(self, playwright):
        return playwright.chromium.launch(executable_path=chromium_executable())

    def observe(
        self,
        screenshot_path: Path | None = None,
        *,
        points: list[tuple[int, int]] | None = None,
        selectors: list[str] | None = None,
    ) -> Observation:
        """Load the page; return what it looks like, what it logged (classified),
        and what the given points/selectors resolve to."""
        from playwright.sync_api import sync_playwright

        entries: list[ConsoleEntry] = []
        page_errors: list[str] = []
        hits: list[ElementHit] = []

        with sync_playwright() as playwright:
            browser = self._launch(playwright)
            page = browser.new_page(
                viewport={"width": self.viewport[0], "height": self.viewport[1]}
            )
            page.on(
                "console",
                lambda m: entries.append(
                    ConsoleEntry(type=m.type, text=m.text, url=(m.location or {}).get("url", ""))
                ),
            )
            page.on("pageerror", lambda e: page_errors.append(str(e)))

            page.goto(self.url, wait_until="networkidle")
            title = page.title()

            for x, y in points or []:
                raw = page.evaluate(RESOLVE_AT_POINT_JS, [x, y])
                hits.append(ElementHit(**raw) if raw else ElementHit(None, None))

            for selector in selectors or []:
                element = page.query_selector(selector)
                if element is None:
                    hits.append(ElementHit(None, None))
                    continue
                hits.append(
                    ElementHit(
                        scio_id=element.get_attribute("data-scio-id"),
                        scio_package=element.get_attribute("data-scio-package"),
                        tag=element.evaluate("e => e.tagName.toLowerCase()"),
                        text=(element.inner_text() or "").strip()[:80],
                    )
                )

            if screenshot_path:
                screenshot_path.parent.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(screenshot_path), full_page=True)

            browser.close()

        return Observation(
            screenshot_path=screenshot_path,
            console=classify_console(entries, page_errors),
            title=title,
            hits=hits,
        )

    def center_of(self, selector: str) -> tuple[int, int] | None:
        """Viewport coordinates of an element — for turning a selector into the
        point a user would actually click."""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as playwright:
            browser = self._launch(playwright)
            page = browser.new_page(
                viewport={"width": self.viewport[0], "height": self.viewport[1]}
            )
            page.goto(self.url, wait_until="networkidle")
            element = page.query_selector(selector)
            box = element.bounding_box() if element else None
            browser.close()
        if not box:
            return None
        return int(box["x"] + box["width"] / 2), int(box["y"] + box["height"] / 2)
