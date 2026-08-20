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

Never load a font, stylesheet or script from a third-party CDN. Typefaces come from \
next/font, which serves them from this app; an external font request blocks the first \
paint on somebody else's server.

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


def build_prompt(
    package: BuildPackage,
    contract: str,
    *,
    only: list[str] | None = None,
    already_written: dict[str, str] | None = None,
) -> str:
    """The generation prompt: the contract, plus what to hand back.

    `only` asks for part of the package. A package whose files will not fit in
    one reply is emitted in bounded chunks (builder/loop.file_chunks), because a
    reply cut off at the output limit cannot be fixed by asking for it again —
    the first real run lost a whole feature that way.

    `already_written` is the code from earlier chunks, verbatim. Without it the
    second chunk invents its own names for what the first one exported, and the
    package does not compile — the same reason the repair prompt hands the model
    its own code back rather than describing it.
    """
    owned = planned_files(package)
    wanted = only or owned
    listing = "\n".join(f"- {path}" for path in wanted)

    context = ""
    if already_written:
        blocks = "\n\n".join(
            f"FILE: {path}\n```\n{body}```" for path, body in sorted(already_written.items())
        )
        context = (
            f"\n## Already written for this package — do not return these again, "
            f"and match their exports and names exactly\n\n{blocks}\n"
        )

    scope = (
        f"Write the complete code for `{package.id}`."
        if only is None
        else (
            f"Write the complete code for these files of `{package.id}`. The rest of the "
            "package is being written separately — return ONLY the files listed here."
        )
    )
    return (
        f"{contract}\n\n"
        "---\n\n"
        f"{context}\n"
        f"{scope} Every file you return must be one this package owns:\n"
        f"{listing}\n"
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
