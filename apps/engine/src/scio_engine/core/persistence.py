"""The coupling survives the session.

PRODUCT-OVERVIEW: returning to a project months later drops you back into the
design window with your running app, and a marking still lands in the right
package. That only works if the manifest is saved *with* the project.

Split per DATA-MODEL (ADR-0009): the manifest lives in git beside the code it
describes, so a checked-out version carries its own coupling; the DB row points
at the commit. Storing it only in the DB would let code and manifest drift apart
on a restore — exactly the drift the spike punished.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from .instrumentation import Manifest

MANIFEST_FILENAME = "scio-manifest.json"


class CouplingRecord(BaseModel):
    """The DB side: which manifest belongs to which build version.

    Mirrors build_version in DATA-MODEL — content lives in git, the DB holds
    metadata and pointers.
    """

    project_id: str
    build_version: int
    git_sha: str = ""
    manifest_path: str = MANIFEST_FILENAME
    element_count: int = 0
    package_count: int = 0

    @classmethod
    def for_manifest(
        cls, manifest: Manifest, *, project_id: str, build_version: int, git_sha: str = ""
    ) -> CouplingRecord:
        return cls(
            project_id=project_id,
            build_version=build_version,
            git_sha=git_sha,
            element_count=len(manifest.elements),
            package_count=len(manifest.packages),
        )


class ManifestStore:
    """Reads and writes the manifest in the project's working tree."""

    def __init__(self, app_dir: Path, filename: str = MANIFEST_FILENAME) -> None:
        self.app_dir = Path(app_dir).resolve()
        self.filename = filename

    @property
    def path(self) -> Path:
        return self.app_dir / self.filename

    def save(self, manifest: Manifest) -> Path:
        manifest.save(self.path)
        return self.path

    def load(self) -> Manifest:
        if not self.path.exists():
            raise FileNotFoundError(
                f"No {self.filename} in {self.app_dir}. The manifest is a build artifact — "
                "regenerate it from source rather than writing one by hand."
            )
        return Manifest.load(self.path)

    def exists(self) -> bool:
        return self.path.exists()


class ProjectCoupling(BaseModel):
    """Both halves together — what a session needs to resume a project."""

    record: CouplingRecord
    manifest: Manifest = Field(default_factory=Manifest)

    def save(self, app_dir: Path) -> Path:
        return ManifestStore(app_dir).save(self.manifest)

    @classmethod
    def load(
        cls, app_dir: Path, *, project_id: str, build_version: int, git_sha: str = ""
    ) -> ProjectCoupling:
        manifest = ManifestStore(app_dir).load()
        return cls(
            record=CouplingRecord.for_manifest(
                manifest,
                project_id=project_id,
                build_version=build_version,
                git_sha=git_sha,
            ),
            manifest=manifest,
        )
