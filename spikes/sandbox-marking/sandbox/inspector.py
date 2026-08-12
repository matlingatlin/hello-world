"""SPIKE — the vision loop's senses: screenshot, console, and click resolution.

Playwright drives a headless Chromium against the running preview. Two things
matter here beyond the pixels: console errors are what the critique agent reads,
and a click at (x, y) must resolve to a stable element identity — that is the
first half of marking->code.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from playwright.sync_api import sync_playwright


def chromium_executable() -> str | None:
    """The pre-installed Chromium, if the pinned build differs from ours.

    This environment ships browsers under PLAYWRIGHT_BROWSERS_PATH and blocks
    `playwright install`, so the SDK's expected build number may not match what
    is on disk. Pointing at the installed binary is the supported way through;
    returning None lets Playwright use its own resolution when they do match.
    """
    root = Path(os.getenv("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers"))
    if not root.exists():
        return None
    candidates = sorted(root.glob("chromium-*/chrome-linux/chrome"))
    return str(candidates[-1]) if candidates else None


@dataclass
class ConsoleMessage:
    type: str
    text: str
    url: str = ""  # where the message came from — often the only way to classify it

    @property
    def full(self) -> str:
        return f"{self.text} ({self.url})" if self.url else self.text


# Console noise the browser and dev server generate regardless of whether the
# generated app is correct. Proven in this spike: a missing /favicon.ico makes
# Chromium log a 404 on every page load — and the message TEXT is only
# "Failed to load resource: the server responded with a status of 404", which
# names nothing. Classifying it requires the message's source URL, which is why
# ConsoleMessage carries `url`. A vision loop reading text alone would fail
# every build ever made.
NOISE_PATTERNS = (
    "favicon.ico",
    "Download the React DevTools",
    "[Fast Refresh]",
)


def is_noise(message: ConsoleMessage) -> bool:
    return any(pattern in message.full for pattern in NOISE_PATTERNS)


@dataclass
class Observation:
    """One look at the running app."""

    screenshot_path: Path
    console: list[ConsoleMessage] = field(default_factory=list)
    page_errors: list[str] = field(default_factory=list)
    title: str = ""

    @property
    def errors(self) -> list[str]:
        """Every error, noise included — what a naive critique agent would read."""
        return [m.full for m in self.console if m.type == "error"] + self.page_errors

    @property
    def app_errors(self) -> list[str]:
        """Errors plausibly caused by the generated app. This is the signal the
        critique agent should judge against.

        The favicon case makes the filter necessary; it also makes it dangerous,
        because a filter that grows too broad will one day hide a real failure.
        Keep it short, and keep it justified.
        """
        noise = {m.full for m in self.console if m.type == "error" and is_noise(m)}
        return [text for text in self.errors if text not in noise]

    @property
    def clean(self) -> bool:
        return not self.app_errors


@dataclass
class ElementHit:
    """What sits at a clicked point."""

    scio_id: str | None
    scio_package: str | None
    tag: str
    text: str


# Walk up from the clicked node to the nearest instrumented ancestor: a click
# usually lands on a text node or an inner span, not on the marked element.
_RESOLVE_JS = """
([x, y]) => {
  let node = document.elementFromPoint(x, y);
  while (node && !node.getAttribute?.('data-scio-id')) node = node.parentElement;
  if (!node) return null;
  return {
    scio_id: node.getAttribute('data-scio-id'),
    scio_package: node.getAttribute('data-scio-package'),
    tag: node.tagName.toLowerCase(),
    text: (node.innerText || '').trim().slice(0, 80),
  };
}
"""


class PreviewInspector:
    """Opens the preview once and answers questions about it."""

    def __init__(self, url: str, *, viewport: tuple[int, int] = (1024, 900)) -> None:
        self.url = url
        self.viewport = viewport

    def observe(
        self,
        screenshot_path: Path,
        *,
        clicks: list[tuple[int, int]] | None = None,
        selectors: list[str] | None = None,
    ) -> tuple[Observation, list[ElementHit], list[ElementHit]]:
        """Load the page; return what it looks like, what it logged, and what
        the given points/selectors resolve to."""
        console: list[ConsoleMessage] = []
        page_errors: list[str] = []
        by_point: list[ElementHit] = []
        by_selector: list[ElementHit] = []

        screenshot_path.parent.mkdir(parents=True, exist_ok=True)

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(executable_path=chromium_executable())
            page = browser.new_page(
                viewport={"width": self.viewport[0], "height": self.viewport[1]}
            )
            page.on(
                "console",
                lambda m: console.append(
                    ConsoleMessage(m.type, m.text, (m.location or {}).get("url", ""))
                ),
            )
            page.on("pageerror", lambda e: page_errors.append(str(e)))

            page.goto(self.url, wait_until="networkidle")
            title = page.title()

            for x, y in clicks or []:
                page.mouse.click(x, y)
                raw = page.evaluate(_RESOLVE_JS, [x, y])
                by_point.append(
                    ElementHit(**raw)
                    if raw
                    else ElementHit(scio_id=None, scio_package=None, tag="", text="")
                )

            for selector in selectors or []:
                element = page.query_selector(selector)
                if element is None:
                    by_selector.append(
                        ElementHit(scio_id=None, scio_package=None, tag="", text="")
                    )
                    continue
                by_selector.append(
                    ElementHit(
                        scio_id=element.get_attribute("data-scio-id"),
                        scio_package=element.get_attribute("data-scio-package"),
                        tag=element.evaluate("e => e.tagName.toLowerCase()"),
                        text=(element.inner_text() or "").strip()[:80],
                    )
                )

            page.screenshot(path=str(screenshot_path), full_page=True)
            browser.close()

        observation = Observation(
            screenshot_path=screenshot_path,
            console=console,
            page_errors=page_errors,
            title=title,
        )
        return observation, by_point, by_selector

    def center_of(self, selector: str) -> tuple[int, int] | None:
        """The viewport coordinates of an element — used to prove that a *point*
        (what a user actually clicks on) resolves as well as a selector does."""
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(executable_path=chromium_executable())
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
