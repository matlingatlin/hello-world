"""The delivery promise, checked against a real Next build.

Gate 2a's load-bearing claim is a negative one: the marking bridge is in the
preview and **absent from the app the user receives**. A negative claim asserted
in prose is worth nothing, and the unit tests can only check that the config
contains a conditional — not that webpack honours it.

So this serves the same app twice, with and without the flag, and follows every
script the page loads. It skips (loudly) when there is no Next to run rather
than passing quietly.
"""

from __future__ import annotations

import os
import re
import shutil
import signal
import socket
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from scio_engine.builder import preview_bridge as PB
from scio_engine.library.verification import next_config

ENGINE_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ENGINE_ROOT.parents[1] / "spikes" / "local-data" / "app"

needs_next = pytest.mark.skipif(
    not (FIXTURE / "node_modules" / "next").exists(),
    reason="no installed Next app to serve (spikes/local-data/app)",
)


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture(scope="module")
def app(tmp_path_factory) -> Path:
    """The booking blueprint, configured the way a real workspace is."""
    target = tmp_path_factory.mktemp("preview") / "app"
    shutil.copytree(
        FIXTURE,
        target,
        symlinks=True,
        ignore=shutil.ignore_patterns("node_modules", ".next", ".env.local", ".scio"),
    )
    (target / "node_modules").symlink_to(FIXTURE / "node_modules", target_is_directory=True)
    # Exactly what builder/workspace writes.
    (target / "next.config.js").write_text(
        next_config(extra_flags=PB.preview_flag_js(), extra_webpack=PB.preview_webpack())
    )
    PB.prepare(target)
    return target


def serve(app: Path, *, preview: bool) -> tuple[str, subprocess.Popen]:
    port = free_port()
    env = {**os.environ, "NEXT_TELEMETRY_DISABLED": "1"}
    if preview:
        env.update(PB.preview_env("http://127.0.0.1:5173"))
    process = subprocess.Popen(
        ["npx", "next", "dev", "--port", str(port), "--hostname", "127.0.0.1"],
        cwd=app,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
        # Its own process group, so `stop` can take the whole tree down. `npx`
        # forks `next`, which forks `next-server` — terminating only the process
        # we started leaves a next-server behind holding ~6 GB, and two of those
        # make the sandbox unusable for anything else. Same lesson as
        # scripts/dev-down.sh.
        start_new_session=True,
    )
    url = f"http://127.0.0.1:{port}"
    deadline = time.time() + 180
    while time.time() < deadline:
        if process.poll() is not None:
            raise AssertionError(f"next died:\n{process.stdout.read()[-2000:]}")
        try:
            urllib.request.urlopen(f"{url}/booking/new", timeout=10)
            return url, process
        except urllib.error.HTTPError:
            return url, process
        except Exception:
            time.sleep(1)
    stop(process)
    raise AssertionError("next never came up")


def stop(process: subprocess.Popen) -> None:
    """Kill the whole tree, not just the wrapper we started."""
    try:
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=30)
    except subprocess.TimeoutExpired:
        os.killpg(os.getpgid(process.pid), signal.SIGKILL)
        process.wait(timeout=30)


def bundles_with_bridge(url: str) -> tuple[int, int]:
    """(bundles carrying the bridge, bundles looked at)."""
    html = urllib.request.urlopen(f"{url}/booking/new", timeout=60).read().decode()
    scripts = re.findall(r'src="(/_next/[^"]+)"', html)
    carrying = 0
    for src in scripts:
        try:
            body = urllib.request.urlopen(url + src, timeout=30).read().decode(errors="ignore")
        except Exception:
            continue
        if PB.bridge_in(body):
            carrying += 1
    return carrying, len(scripts)


@needs_next
class TestTheBridgeIsPreviewOnly:
    def test_a_preview_build_carries_it(self, app: Path):
        url, process = serve(app, preview=True)
        try:
            carrying, total = bundles_with_bridge(url)
        finally:
            stop(process)
            shutil.rmtree(app / ".next", ignore_errors=True)

        assert total > 0, "the page loaded no scripts at all — the check proves nothing"
        assert carrying == 1, f"expected the bridge in exactly one bundle, found {carrying}"

    def test_a_delivery_build_does_not(self, app: Path):
        """The same app, the same files on disk — only the flag differs."""
        url, process = serve(app, preview=False)
        try:
            carrying, total = bundles_with_bridge(url)
            html = urllib.request.urlopen(f"{url}/booking/new", timeout=60).read().decode()
        finally:
            stop(process)
            shutil.rmtree(app / ".next", ignore_errors=True)

        assert total > 0
        assert carrying == 0, "the delivered app must not contain the bridge at all"
        assert PB.bridge_in(html) is False
        # …and the app is otherwise itself: the instrumentation is still there,
        # which is what a delivery build is supposed to have.
        assert "data-scio-id" in html
