"""SPIKE — the SandboxProvider interface (ADR-0005).

The real implementation will be Azure Container Apps dynamic sessions. The point
of pinning the interface now is that everything above it — the preview, the
vision loop, directed change — is written against this shape, so swapping the
local process for ACA is a binding change, not a rewrite.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class SandboxHandle:
    """A running app: where to reach it, and what it took to get there."""

    url: str
    workdir: Path
    started_at: float = field(default_factory=time.time)
    kind: str = "unknown"

    @property
    def uptime_s(self) -> float:
        return time.time() - self.started_at


class SandboxError(RuntimeError):
    """The sandbox failed to start, apply a change, or stop cleanly."""


class SandboxProvider(ABC):
    """One project's isolated runtime. Start it, look at it, change it, stop it."""

    name: str

    @abstractmethod
    def start(self, app_dir: Path, *, port: int) -> SandboxHandle:
        """Boot the app and return a URL that serves it. Blocks until ready."""

    @abstractmethod
    def apply_change(self, handle: SandboxHandle, files: dict[str, str]) -> None:
        """Write changed file contents (path -> new text) into the running app.

        `files` is deliberately a whole-file map: the caller (the directed-change
        step) has already decided the exact, minimal set of files to touch.
        """

    @abstractmethod
    def stop(self, handle: SandboxHandle) -> None:
        """Tear the sandbox down. Must be safe to call twice."""

    def is_available(self) -> bool:
        """Whether this provider can run here at all — lets the spike (and later
        the engine) fall back rather than fail."""
        return True
