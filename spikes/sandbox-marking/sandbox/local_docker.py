"""SPIKE — the container implementation, written but NOT exercised here.

Docker's CLI is installed in this environment but no daemon is reachable, so
`is_available()` returns False and the spike falls back to LocalProcessSandbox.
It is kept because it is the honest halfway house between "a process on my
machine" and the real ACA sandbox: same interface, real container boundary.

Nothing below has been run. Treat it as a sketch to validate when a daemon is
available, not as working code.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from .local_process import free_port
from .provider import SandboxError, SandboxHandle, SandboxProvider

DOCKERFILE = """FROM node:22-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
EXPOSE 3000
CMD ["npm", "run", "dev", "--", "--hostname", "0.0.0.0"]
"""


class LocalDockerSandbox(SandboxProvider):
    name = "local-docker"

    def __init__(self, image: str = "scio-spike-app") -> None:
        self.image = image
        self._containers: dict[str, str] = {}

    def is_available(self) -> bool:
        if shutil.which("docker") is None:
            return False
        probe = subprocess.run(
            ["docker", "info"], capture_output=True, text=True, timeout=20, check=False
        )
        return probe.returncode == 0

    def start(self, app_dir: Path, *, port: int = 0) -> SandboxHandle:
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
        return SandboxHandle(url=url, workdir=app_dir, kind=self.name)

    def apply_change(self, handle: SandboxHandle, files: dict[str, str]) -> None:
        container = self._containers.get(handle.url)
        if container is None:
            raise SandboxError("no container for this handle")
        for relative, content in files.items():
            (handle.workdir / relative).write_text(content)
            copy = subprocess.run(
                ["docker", "cp", str(handle.workdir / relative), f"{container}:/app/{relative}"],
                capture_output=True,
                text=True,
                check=False,
            )
            if copy.returncode != 0:
                raise SandboxError(f"docker cp failed:\n{copy.stderr}")

    def stop(self, handle: SandboxHandle) -> None:
        container = self._containers.pop(handle.url, None)
        if container:
            subprocess.run(["docker", "rm", "-f", container], capture_output=True, check=False)
