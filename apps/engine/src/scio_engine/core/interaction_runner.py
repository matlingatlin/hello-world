"""Running an interaction script against the app, in a real browser.

Sync Playwright, like `core/preview` — and for the same reason it must be called
through `asyncio.to_thread`: the sync API refuses to run inside a running event
loop, which is a lesson this codebase learned the hard way once already.

Every failure is caught and reported rather than raised. A script that cannot
complete is a *finding about the build* — "pressing submit did nothing" is
exactly the kind of thing this exists to notice — so it must come back as a
result the loop can feed into a repair, never as an exception that ends the
build.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request

from .interaction import Action, Script, ScriptResult, Step, StepResult, selectors_for
from .preview import chromium_executable

STEP_TIMEOUT_MS = 15_000
"""Long enough for a dev server to compile a route on first visit, short enough
that a hung script does not hold a build open."""


def run_script(
    base_url: str,
    script: Script,
    *,
    verify_url: str = "",
    browser_path: str = "",
) -> ScriptResult:
    """Drive the app through one script. Never raises."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:  # pragma: no cover - playwright is an optional extra
        return ScriptResult(
            name=script.name, passed=False, error="playwright is not installed"
        )

    results: list[StepResult] = []
    executable = browser_path or chromium_executable()

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(executable_path=executable)
            page = browser.new_page()
            try:
                navigated = False
                for step in script.steps:
                    if step.action is Action.as_user:
                        # Before the first page load, so an isolation script's
                        # opening page is rendered as the user it names — not as
                        # whoever the previous script left behind.
                        _set_actor(verify_url, step.value)
                        results.append(StepResult(step=step, ok=True))
                        continue

                    if not navigated:
                        page.goto(base_url.rstrip("/") + script.route, wait_until="networkidle")
                        navigated = True

                    outcome = _run_step(page, base_url, step, verify_url)
                    results.append(outcome)
                    if not outcome.ok:
                        break
            finally:
                browser.close()
    except Exception as exc:  # the browser itself failed — still a finding
        return ScriptResult(
            name=script.name, passed=False, steps=results, error=str(exc)[:400]
        )

    return ScriptResult(
        name=script.name,
        passed=bool(results) and all(r.ok for r in results),
        steps=results,
    )


def _locate(page, step: Step) -> str:
    """The selector that is actually on the page, preferring the data-scio-id.

    The fallback is a concession, not a shortcut: it is consulted only when the
    id is absent, so a build that follows the convention is never judged on
    anything but its ids.
    """
    options = selectors_for(step)
    for selector in options:
        if page.locator(selector).count() > 0:
            return selector
    # Nothing matched: return the primary so the failure names the id we wanted.
    return options[0] if options else ""


def _run_step(page, base_url: str, step: Step, verify_url: str) -> StepResult:
    try:
        if step.action is Action.fill:
            page.fill(_locate(page, step), step.value, timeout=STEP_TIMEOUT_MS)
            return StepResult(step=step, ok=True)

        if step.action is Action.click:
            page.click(_locate(page, step), timeout=STEP_TIMEOUT_MS)
            # Give the server action its round trip before anything is asserted.
            page.wait_for_timeout(1500)
            return StepResult(step=step, ok=True)

        if step.action is Action.reload:
            # A real navigation, not page.reload(): the point is to prove the
            # row came back from the database rather than from React's state.
            page.goto(base_url.rstrip("/") + (step.target or "/"), wait_until="networkidle")
            return StepResult(step=step, ok=True)

        if step.action in (Action.assert_present, Action.assert_absent):
            found = _is_present(page, step)
            want = step.action is Action.assert_present
            if found == want:
                return StepResult(step=step, ok=True)
            subject = step.text or step.target
            return StepResult(
                step=step,
                ok=False,
                detail=f"'{subject}' was {'not ' if want else ''}on the page",
            )

        if step.action is Action.assert_row:
            return _assert_row(step, verify_url)

    except Exception as exc:
        return StepResult(step=step, ok=False, detail=_short(exc))

    return StepResult(step=step, ok=False, detail=f"unknown action {step.action}")


def _is_present(page, step: Step) -> bool:
    if step.text:
        return step.text in (page.content() or "")
    return any(page.locator(selector).count() > 0 for selector in selectors_for(step))


def _assert_row(step: Step, verify_url: str) -> StepResult:
    """Ask the APP whether the row is really there.

    Through the app's own process on purpose: pglite is single-writer, and a
    second reader on the same directory is the corruption the spike hit.
    """
    if not verify_url:
        return StepResult(
            step=step,
            ok=False,
            detail="no verification endpoint — the app is not running with data",
        )
    query = urllib.parse.urlencode({"table": step.target, "match": json.dumps(step.match)})
    try:
        with urllib.request.urlopen(f"{verify_url}?{query}", timeout=30) as response:
            payload = json.loads(response.read().decode())
    except Exception as exc:
        return StepResult(step=step, ok=False, detail=_short(exc))

    if payload.get("error"):
        return StepResult(step=step, ok=False, detail=str(payload["error"])[:200])
    count = int(payload.get("count", 0))
    if count > 0:
        return StepResult(step=step, ok=True, detail=f"{count} row(s)")
    return StepResult(
        step=step,
        ok=False,
        detail=f"no row in {step.target} matching {step.match} — it was not saved",
    )


def _set_actor(verify_url: str, actor: str) -> None:
    if not verify_url:
        return
    query = urllib.parse.urlencode({"actor": actor})
    with urllib.request.urlopen(f"{verify_url}?{query}", timeout=15):
        pass


def _short(exc: Exception) -> str:
    return str(exc).splitlines()[0][:200] if str(exc) else exc.__class__.__name__
