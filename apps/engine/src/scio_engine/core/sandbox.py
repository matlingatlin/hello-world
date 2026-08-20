"""The sandbox interface — one project's isolated runtime (ADR-0005).

Gates 2 and 3 share this: the preview and the finished app run in the same
service. The interface is what lets the Azure implementation replace the local
one without anything above it changing.
"""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
import time
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class SandboxHandle:
    """A running app: where to reach it, and what it took to get there."""

    url: str
    workdir: Path
    kind: str
    started_at: float = field(default_factory=time.time)

    @property
    def uptime_s(self) -> float:
        return time.time() - self.started_at


class SandboxError(RuntimeError):
    """The sandbox failed to start, apply a change, or stop cleanly."""


class SandboxProvider(ABC):
    """Start it, change it, stop it. Looking at it is the preview's job."""

    name: str

    @abstractmethod
    def start(
        self, app_dir: Path, *, port: int = 0, env: dict[str, str] | None = None
    ) -> SandboxHandle:
        """Boot the app and return a URL serving it. Blocks until ready.

        `env` carries per-run configuration the app process needs — the
        verification data layer's database, for instance (library/verification).
        """

    @abstractmethod
    def apply_change(self, handle: SandboxHandle, files: dict[str, str]) -> None:
        """Write changed file contents (relative path -> new text).

        A whole-file map by design: the caller has already decided the exact,
        minimal set of files to touch, and that decision is auditable.
        """

    @abstractmethod
    def stop(self, handle: SandboxHandle) -> None:
        """Tear down. Must be safe to call twice."""

    def is_available(self) -> bool:
        """Whether this provider can run in the current environment."""
        return True


def free_port(preferred: int = 0) -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", preferred))
        return sock.getsockname()[1]


PREVIEW_HOST = "SCIO_PREVIEW_HOST"
"""Which interface a preview binds. Loopback unless told otherwise.

Loopback is the safe default and the right one whenever the browser is on the
same machine. A Codespace forwards a port only if something is listening on
every interface, so there it has to be `0.0.0.0` — a decision for whoever runs
the engine, never a default we ship.
"""


def preview_host() -> str:
    return os.getenv(PREVIEW_HOST, "").strip() or "127.0.0.1"


def _guard_path(workdir: Path, relative: str) -> Path:
    """Refuse writes that escape the sandbox directory.

    Generated code is untrusted input; a change request naming ../../etc/passwd
    must not be honoured just because it arrived through our own API.
    """
    target = (workdir / relative).resolve()
    if workdir.resolve() not in target.parents:
        raise SandboxError(f"refusing to write outside the sandbox: {relative}")
    return target


class LocalProcessSandbox(SandboxProvider):
    """Run the app as a local dev-server process.

    Honest about what it is: this shares the host. It exists so the core is
    runnable and testable without Docker or Azure — it is NOT an isolation
    boundary, and must never be the production provider.
    """

    name = "local-process"

    def __init__(self, *, ready_timeout_s: float = 180.0) -> None:
        self.ready_timeout_s = ready_timeout_s
        self._processes: dict[str, subprocess.Popen] = {}

    def is_available(self) -> bool:
        return shutil.which("npm") is not None

    @property
    def isolated(self) -> bool:
        return False

    def start(
        self, app_dir: Path, *, port: int = 0, env: dict[str, str] | None = None
    ) -> SandboxHandle:
        app_dir = app_dir.resolve()
        if not (app_dir / "node_modules").exists():
            raise SandboxError(
                f"{app_dir} has no node_modules. Dependencies must be installed BEFORE the "
                "sandbox starts — a dev server that installs on first boot can die mid-startup "
                "(seen in the spike)."
            )

        port = port or free_port()
        url = f"http://127.0.0.1:{port}"
        process = subprocess.Popen(
            ["npm", "run", "dev", "--", "--port", str(port), "--hostname", preview_host()],
            cwd=app_dir,
            env={
                **os.environ,
                "PORT": str(port),
                "NEXT_TELEMETRY_DISABLED": "1",
                **(env or {}),
            },
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        handle = SandboxHandle(url=url, workdir=app_dir, kind=self.name)
        self._processes[url] = process
        self._wait_until_ready(handle, process)
        return handle

    def _wait_until_ready(self, handle: SandboxHandle, process: subprocess.Popen) -> None:
        deadline = time.time() + self.ready_timeout_s
        while time.time() < deadline:
            if process.poll() is not None:
                output = process.stdout.read() if process.stdout else ""
                raise SandboxError(f"dev server exited during startup:\n{output[-2000:]}")
            try:
                with urllib.request.urlopen(handle.url, timeout=2) as response:
                    if response.status < 500:
                        return
            except urllib.error.HTTPError:
                # The server ANSWERED — a 404 on `/` just means this app has no
                # root route, which is true of any app whose pages all live under
                # a prefix. HTTPError subclasses URLError, so without this branch
                # it lands in "not up yet" and the sandbox waits out the full
                # timeout on an app that started in two seconds.
                return
            except (urllib.error.URLError, TimeoutError, ConnectionError):
                time.sleep(0.5)
        raise SandboxError(f"dev server not ready within {self.ready_timeout_s}s")

    def apply_change(self, handle: SandboxHandle, files: dict[str, str]) -> None:
        for relative, content in files.items():
            target = _guard_path(handle.workdir, relative)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
        time.sleep(2.0)  # let the dev server recompile

    def stop(self, handle: SandboxHandle) -> None:
        process = self._processes.pop(handle.url, None)
        if process is None or process.poll() is not None:
            return
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()


DOCKERFILE = """FROM node:22-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
EXPOSE 3000
CMD ["npm", "run", "dev", "--", "--hostname", "0.0.0.0"]
"""


class LocalDockerSandbox(SandboxProvider):
    """A real container boundary, locally. Runs when a Docker daemon is reachable."""

    name = "local-docker"

    def __init__(self, image: str = "scio-sandbox") -> None:
        self.image = image
        self._containers: dict[str, str] = {}

    @property
    def isolated(self) -> bool:
        return True

    def is_available(self) -> bool:
        if shutil.which("docker") is None:
            return False
        probe = subprocess.run(
            ["docker", "info"], capture_output=True, text=True, timeout=20, check=False
        )
        return probe.returncode == 0

    def start(
        self, app_dir: Path, *, port: int = 0, env: dict[str, str] | None = None
    ) -> SandboxHandle:
        if not self.is_available():
            raise SandboxError("Docker daemon is not reachable")
        app_dir = app_dir.resolve()

        dockerfile = app_dir / "Dockerfile"
        if not dockerfile.exists():
            dockerfile.write_text(DOCKERFILE)

        build = subprocess.run(
            ["docker", "build", "-t", self.image, "."],
            cwd=app_dir,
            capture_output=True,
            text=True,
            check=False,
        )
        if build.returncode != 0:
            raise SandboxError(f"docker build failed:\n{build.stderr[-2000:]}")

        port = port or free_port()
        run = subprocess.run(
            ["docker", "run", "-d", "-p", f"{port}:3000", self.image],
            capture_output=True,
            text=True,
            check=False,
        )
        if run.returncode != 0:
            raise SandboxError(f"docker run failed:\n{run.stderr[-2000:]}")

        url = f"http://127.0.0.1:{port}"
        self._containers[url] = run.stdout.strip()
        handle = SandboxHandle(url=url, workdir=app_dir, kind=self.name)
        self._wait_until_ready(handle)
        return handle

    def _wait_until_ready(self, handle: SandboxHandle, timeout_s: float = 180.0) -> None:
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            try:
                with urllib.request.urlopen(handle.url, timeout=2) as response:
                    if response.status < 500:
                        return
            except (urllib.error.URLError, TimeoutError, ConnectionError):
                time.sleep(0.5)
        raise SandboxError(f"container not ready within {timeout_s}s")

    def apply_change(self, handle: SandboxHandle, files: dict[str, str]) -> None:
        container = self._containers.get(handle.url)
        if container is None:
            raise SandboxError("no container for this handle")
        for relative, content in files.items():
            target = _guard_path(handle.workdir, relative)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
            copy = subprocess.run(
                ["docker", "cp", str(target), f"{container}:/app/{relative}"],
                capture_output=True,
                text=True,
                check=False,
            )
            if copy.returncode != 0:
                raise SandboxError(f"docker cp failed:\n{copy.stderr}")
        time.sleep(2.0)

    def stop(self, handle: SandboxHandle) -> None:
        container = self._containers.pop(handle.url, None)
        if container:
            subprocess.run(["docker", "rm", "-f", container], capture_output=True, check=False)


def choose_sandbox() -> SandboxProvider:
    """The best sandbox this environment can offer.

    Prefers a real boundary. Falls back to a process so the core stays runnable
    — callers that care about isolation must check `isolated`.
    """
    docker = LocalDockerSandbox()
    if docker.is_available():
        return docker
    return LocalProcessSandbox()
