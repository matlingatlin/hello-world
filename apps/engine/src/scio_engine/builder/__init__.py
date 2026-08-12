"""The builder — one package, generated and driven to a status you can trust.

B041a: the single-package loop. B041b assembles a whole plan out of it.
"""

from .codegen import (
    CODEGEN_SYSTEM,
    FILE_FORMAT_RULES,
    FIX_SYSTEM,
    CodeExtractionError,
    ExtractedCode,
    build_prompt,
    extract_files,
    fix_prompt,
)
from .critique import (
    CRITIQUE_SYSTEM,
    CriterionVerdict,
    Critique,
    Evidence,
    build_critique_prompt,
    critique_package,
    parse_critique,
)
from .file_plan import file_plan, planned_files
from .loop import (
    GATES,
    BuildOptions,
    BuildPreview,
    SandboxPreview,
    ScriptedPreview,
    build_package,
)
from .persistence import GitError, PersistedBuild, ensure_repo, persist_package_build
from .result import Attempt, PackageBuildResult, PackageStatus, Remainder
from .validation import (
    Agent,
    Finding,
    Severity,
    ValidationReport,
    check_code_quality,
    check_contract_consistency,
    check_security,
    check_tests_present,
    validate_package,
)

__all__ = [
    "CODEGEN_SYSTEM",
    "CRITIQUE_SYSTEM",
    "FILE_FORMAT_RULES",
    "FIX_SYSTEM",
    "GATES",
    "Agent",
    "Attempt",
    "BuildOptions",
    "BuildPreview",
    "CodeExtractionError",
    "CriterionVerdict",
    "Critique",
    "Evidence",
    "ExtractedCode",
    "Finding",
    "GitError",
    "PackageBuildResult",
    "PackageStatus",
    "PersistedBuild",
    "Remainder",
    "SandboxPreview",
    "ScriptedPreview",
    "Severity",
    "ValidationReport",
    "build_critique_prompt",
    "build_package",
    "build_prompt",
    "check_code_quality",
    "check_contract_consistency",
    "check_security",
    "check_tests_present",
    "critique_package",
    "ensure_repo",
    "extract_files",
    "file_plan",
    "fix_prompt",
    "parse_critique",
    "persist_package_build",
    "planned_files",
    "validate_package",
]
