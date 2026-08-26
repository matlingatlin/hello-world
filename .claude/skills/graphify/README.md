# graphify — vendored skill

`SKILL.md` is upstream's file, copied verbatim so it can be re-fetched and diffed
cleanly. Do not hand-edit it; re-run the fetch below instead.

- **Upstream:** https://github.com/Graphify-Labs/graphify (Apache-2.0 / MIT)
- **Source:** `https://raw.githubusercontent.com/Graphify-Labs/graphify/main/skills/graphify/skill.md`
- **Fetched:** 2026-08-26 — `sha256 f138783724b92036c211d4b3ed1799e8b7d6f071c0c477acd2d1861ccedaa2d3`

To update:

```sh
curl -fsSL https://raw.githubusercontent.com/Graphify-Labs/graphify/main/skills/graphify/skill.md \
  -o .claude/skills/graphify/SKILL.md
```

## Why it is vendored rather than installed

Upstream installs with `uv tool install graphifyy && graphify install`, which writes the
skill to `~/.claude/skills/`. That is per-machine and per-container: web sessions get a
fresh home directory every time, so an installed copy is gone by the next session. Kept
in the repo, every checkout and every fresh session inherits it.

Two naming traps, both checked and both benign: the PyPI package is `graphifyy` with two
y's (plain `graphify` is unregistered, not a squat on it), and upstream docs still link
raw files via the pre-rename owner `safishamsi/graphify`, which redirects to
`Graphify-Labs` and serves a byte-identical file.

## What it does on first run

`SKILL.md` step 1 bootstraps its own dependency:

```sh
python3 -c "import graphify" || pip install graphifyy -q --break-system-packages
```

So the Python package is installed at first `/graphify` invocation, not by this commit.
Run it inside a virtualenv if you would rather that not touch a system Python.

Code parsing is local and deterministic (tree-sitter AST, no LLM). Extraction over docs,
PDFs and images uses the calling assistant's model, so it spends tokens; `--no-viz` and
`--update` keep that down. Output lands in `graphify-out/` and is gitignored.
