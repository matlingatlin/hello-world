"""Azure Container Apps dynamic sessions (ADR-0005).

⚠️  NOT RUN HERE. No Azure in this environment, so nothing below has ever
executed. It is wired against the documented session-pool API and kept behind
SandboxProvider so the swap is a binding change, not a rewrite — but treat every
line as unverified until it runs against a real pool.

Open questions the spike flagged and this file does not answer: prewarm latency,
concurrency limits, cost per session-hour, and whether Playwright runs inside the
session or beside it.
"""

from __future__ import annotations

import os
from pathlib import Path

from .sandbox import SandboxError, SandboxHandle, SandboxProvider


class AcaSandbox(SandboxProvider):
    """Per-project session from an ACA dynamic-session pool, custom container.

    Each session runs in its own Hyper-V sandbox — the isolation that makes
    running untrusted generated code safe, which no local provider gives us.
    """

    name = "aca"

    def __init__(
        self,
        pool_endpoint: str | None = None,
        *,
        credential=None,
        cooldown_s: int = 300,
    ) -> None:
        self.pool_endpoint = pool_endpoint or os.getenv("AZURE_SESSION_POOL_ENDPOINT", "")
        self.credential = credential
        self.cooldown_s = cooldown_s  # idle timeout: the main sandbox cost lever

    @property
    def isolated(self) -> bool:
        return True

    def is_available(self) -> bool:
        return bool(self.pool_endpoint)

    def _client(self):
        if not self.pool_endpoint:
            raise SandboxError("AZURE_SESSION_POOL_ENDPOINT is not set")
        try:
            from azure.identity import DefaultAzureCredential
            from azure.mgmt.appcontainers import ContainerAppsAPIClient
        except ImportError as exc:  # pragma: no cover - optional extra
            raise SandboxError(
                "Azure SDK not installed (pip install '.[azure]')"
            ) from exc
        return ContainerAppsAPIClient(
            credential=self.credential or DefaultAzureCredential(),
            subscription_id=os.getenv("AZURE_SUBSCRIPTION_ID", ""),
        )

    def start(self, app_dir: Path, *, port: int = 0) -> SandboxHandle:
        # TODO(B04x): allocate a session from the pool, upload app_dir into the
        # session's filesystem, start the dev server, and return the session's
        # ingress URL. Sessions are prewarmed, so this should be milliseconds
        # rather than the ~7s a cold local process takes — unverified.
        raise SandboxError(
            "AcaSandbox.start is not implemented — wired but never run. "
            "Implement and verify against a real session pool before production use."
        )

    def apply_change(self, handle: SandboxHandle, files: dict[str, str]) -> None:
        # TODO(B04x): write files into the running session (file API), then let
        # the dev server hot-reload.
        raise SandboxError("AcaSandbox.apply_change is not implemented")

    def stop(self, handle: SandboxHandle) -> None:
        # TODO(B04x): release the session back to the pool. Releasing promptly
        # is what keeps the sandbox bill sane — do not rely on cooldown alone.
        raise SandboxError("AcaSandbox.stop is not implemented")
