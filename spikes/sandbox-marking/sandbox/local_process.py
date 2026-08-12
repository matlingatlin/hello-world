"""SPIKE — run the app as a local `next dev` process.

The fallback the kickoff anticipated: Docker's CLI is present in this
environment but no daemon is reachable, so containers are not an option here.
Behind the SandboxProvider interface the difference is invisible to everything
above — which is exactly the property we wanted to prove.

What this does NOT prove: isolation. A local process shares the host; the real
ACA sandbox is the thing that makes running untrusted generated code safe.
"""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

from .provider import SandboxError, SandboxHandle, SandboxProvider


def free_port(preferred: int = 0) -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", preferred))
        return sock.getsockname()[1]


class LocalProcessSandbox(SandboxProvider):
    name = "local-process"

    def __init__(self, *, ready_timeout_s: float = 180.0) -> None:
        self.ready_timeout_s = ready_timeout_s
        self._processes: dict[str, subprocess.Popen] = {}

    def is_available(self) -> bool:
        return shutil.which("npm") is not None

    def start(self, app_dir: Path, *, port: int = 0) -> SandboxHandle:
        app_dir = app_dir.resolve()
        if not (app_dir / "node_modules").exists():
            raise SandboxError(f"{app_dir} has no node_modules — run npm install first")

        port = port or free_port()
        url = f"http://127.0.0.1:{port}"

        env = {**os.environ, "PORT": str(port), "NEXT_TELEMETRY_DISABLED": "1"}
        process = subprocess.Popen(
            ["npm", "run", "dev", "--", "--port", str(port), "--hostname", "127.0.0.1"],
            cwd=app_dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        handle = SandboxHandle(url=url, workdir=app_dir, kind=self.name)
        self._processes[url] = process

        self._wait_until_ready(handle, process)
        return handle

    def _wait_until_ready(self, handle: SandboxHandle, process: subprocess.Popen) -> None:
        """Poll the URL until the dev server answers. A dev server that dies
        during startup must fail loudly here, not time out silently later."""
        deadline = time.time() + self.ready_timeout_s
        while time.time() < deadline:
            if process.poll() is not None:
                output = process.stdout.read() if process.stdout else ""
                raise SandboxError(f"dev server exited during startup:\n{output[-2000:]}")
            try:
                with urllib.request.urlopen(handle.url, timeout=2) as response:
                    if response.status < 500:
                        return
            except (urllib.error.URLError, TimeoutError, ConnectionError):
                time.sleep(0.5)
        raise SandboxError(f"dev server did not become ready within {self.ready_timeout_s}s")

    def apply_change(self, handle: SandboxHandle, files: dict[str, str]) -> None:
        for relative, content in files.items():
            target = (handle.workdir / relative).resolve()
            if handle.workdir not in target.parents and target != handle.workdir:
                raise SandboxError(f"refusing to write outside the sandbox: {relative}")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
        # Next's dev server hot-reloads on write; give it a moment to recompile.
        time.sleep(2.0)

    def stop(self, handle: SandboxHandle) -> None:
        process = self._processes.pop(handle.url, None)
        if process is None or process.poll() is not None:
            return
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
