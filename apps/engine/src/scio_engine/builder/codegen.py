"""Turning a package contract into files.

The model writes prose around code no matter how firmly you ask it not to, so
the contract here is a *format*, not a promise: files arrive in fenced blocks
with a path line, and anything outside a block is ignored. Parsing is strict
about paths (they must belong to the package) and forgiving about everything
else.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from ..core.instrumentation import INSTRUMENTATION_RULES
from ..layerc.plan import BuildPackage
from .file_plan import planned_files

FILE_FORMAT_RULES = """## How to return the code

Return every file in a fenced block, preceded by its path on its own line:

FILE: components/booking-form.tsx
```tsx
...the complete file...
```

Rules:
- One block per file; return the COMPLETE file, never a fragment or a diff.
- Only paths that belong to this package. Anything else is discarded.
- No commentary outside the blocks — it will be ignored.
"""

_FILE_BLOCK = re.compile(
    r"^FILE:\s*(?P<path>[^\n`]+?)\s*\n+```[a-zA-Z0-9+.-]*\n(?P<body>.*?)^```",
    re.MULTILINE | re.DOTALL,
)


class CodeExtractionError(RuntimeError):
    """The model's reply contained no usable files."""


@dataclass
class ExtractedCode:
    files: dict[str, str]
    ignored_paths: list[str]

    @property
    def is_empty(self) -> bool:
        return not self.files


def _normalise(raw: str) -> str:
    """Trim a leading `./` — and nothing more.

    Stripping character sets here would quietly rewrite `../../etc/passwd` into a
    path that looks harmless; a traversal attempt must survive intact so it can
    be recognised and refused.
    """
    path = raw.strip()
    while path.startswith("./"):
        path = path[2:]
    return path


def _escapes(path: str) -> bool:
    """Absolute paths and `..` segments never belong to a package, allow list or
    not. Generated code is untrusted input (core/sandbox says the same)."""
    return path.startswith("/") or ".." in Path(path).parts


def extract_files(text: str, allowed: list[str] | None = None) -> ExtractedCode:
    """Pull FILE blocks out of a reply.

    `allowed` is the package's file list: a path outside it is dropped rather
    than written, because a builder that quietly edits another package's files
    is exactly the leak the core's isolation proof exists to catch. Better to
    never write it.
    """
    files: dict[str, str] = {}
    ignored: list[str] = []

    for match in _FILE_BLOCK.finditer(text):
        path = _normalise(match.group("path"))
        body = match.group("body")
        if _escapes(path) or (allowed is not None and path not in allowed):
            ignored.append(path)
            continue
        files[path] = body if body.endswith("\n") else body + "\n"

    if not files:
        raise CodeExtractionError(
            "No FILE blocks in the reply. The model must return complete files in the "
            "documented format; nothing was written."
        )
    return ExtractedCode(files=files, ignored_paths=ignored)


CODEGEN_SYSTEM = f"""You are Scio's builder. You write one build package at a time: \
complete, working, professional code that satisfies its contract exactly.

You are given a contract — the goal, the architecture slice you own, the interfaces \
of what already exists, why it exists, the house rules, and the acceptance criteria \
you will be judged against. Build exactly that. Do not build what other packages own, \
and do not build what the scope guard excludes.

{INSTRUMENTATION_RULES}

{FILE_FORMAT_RULES}"""


FIX_SYSTEM = f"""You are Scio's builder, fixing a package that did not yet meet its \
contract.

You are given the contract, the current code, and exactly what went wrong. Fix those \
problems and nothing else: keep every id, keep what already works, and return the \
complete files you changed.

{INSTRUMENTATION_RULES}

{FILE_FORMAT_RULES}"""


def build_prompt(package: BuildPackage, contract: str) -> str:
    """The generation prompt: the contract, plus what to hand back."""
    return (
        f"{contract}\n\n"
        "---\n\n"
        f"Write the complete code for `{package.id}`. Every file you return must be one "
        "this package owns:\n"
        + "\n".join(f"- {path}" for path in planned_files(package))
        + "\n"
    )


def fix_prompt(
    package: BuildPackage,
    contract: str,
    current_files: dict[str, str],
    problems: list[str],
) -> str:
    """The repair prompt: what is there now, and precisely what is wrong with it.

    The current code goes in verbatim. A model asked to fix code it cannot see
    invents a plausible replacement, which is how ids get lost.
    """
    listing = "\n\n".join(
        f"FILE: {path}\n```\n{content}```" for path, content in sorted(current_files.items())
    )
    numbered = "\n".join(f"{i}. {problem}" for i, problem in enumerate(problems, start=1))
    return (
        f"{contract}\n\n"
        "---\n\n"
        f"## The current code for `{package.id}`\n\n{listing}\n\n"
        f"## What is wrong\n\n{numbered}\n\n"
        "Fix exactly these problems and return the complete files you changed."
    )
