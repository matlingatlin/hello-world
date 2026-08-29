#!/usr/bin/env python3
"""Mechanical conformance check for agents, skills and their roster.

This file is the SINGLE HOME of the construction rules. A change-matrix pass
showed why: if the rules are also restated in prose inside each skill, one spec
change opens four parts; if they live only here, it opens one. So skills should
describe the PROCEDURE and point here for the RULES, never restate them.

Everything below runs. Nothing is interpreted. That distinction is the point —
Anthropic's own guide puts it as "Code is deterministic; language interpretation
isn't."

Rule provenance, so a future reader can re-verify rather than trust this file:
  A = The Complete Guide to Building Skills for Claude (Anthropic, 33pp)
  B = code.claude.com/docs/en/sub-agents
  C = code.claude.com/docs/en/skills
  M = measured in this project, see /home/user/skills-repo/knowledge/notes/

Usage:  python3 .claude/validate/agents.py [repo-root]
Exit 0 = clean, 1 = failures. Warnings never fail the run.
"""
import sys, os, re, glob, json

DESC_MAX      = 1024      # A: description under 1024 characters
COMPAT_MAX    = 500       # A: compatibility 1-500 characters
BODY_MAX_W    = 5000      # A: "Keep SKILL.md under 5,000 words"
ROSTER_MAX_T  = 15000     # B: combined non-built-in agent descriptions
PRELOAD_MAX   = 3         # M: 1-3 modules +19.0pp vs 4+ +10.1pp
RESERVED      = ("claude", "anthropic")   # A: reserved in skill names

fails, warns = [], []
def fail(where, msg): fails.append((where, msg))
def warn(where, msg): warns.append((where, msg))

def frontmatter(path):
    """Line-anchored parse. Splitting on '---' reports green on an unterminated
    file — three talents shipped unloadable in one day that way."""
    lines = open(path, encoding="utf-8").read().split("\n")
    if not lines or lines[0] != "---":
        return None, None, "line 1 is not exactly `---`"
    end = next((i for i, l in enumerate(lines[1:], 1) if l == "---"), None)
    if end is None:
        return None, None, "frontmatter is never closed by a line that is exactly `---`"
    return "\n".join(lines[1:end]), "\n".join(lines[end + 1:]), None

def scalar(fm, key):
    m = re.search(rf"^{key}: *(.*)$", fm, re.M)
    return m.group(1).strip().strip('"').strip("'") if m else None

def has_key(fm, key):
    return re.search(rf"^{key}:", fm, re.M) is not None

def block_list(fm, key):
    """Values of a YAML block list, e.g. skills:\n  - a\n  - b"""
    m = re.search(rf"^{key}: *$\n((?:^[ \t]+-.*$\n?)+)", fm, re.M)
    if not m: return []
    return [re.sub(r"^[ \t]*-\s*", "", l).strip() for l in m.group(1).split("\n") if l.strip()]

def check_description(where, d, what):
    if d is None:  return fail(where, f"{what}: no `description:`")
    if len(d) > DESC_MAX:
        fail(where, f"description is {len(d)} chars, over the {DESC_MAX} limit [A]")
    if "<" in d or ">" in d:
        fail(where, "description contains `<` or `>` — forbidden in frontmatter; "
                    "frontmatter enters the system prompt and could carry injected "
                    "instructions [A]")

def main(root):
    root = os.path.abspath(root)
    # Two layouts in the wild: .claude/agents (Claude Code project) and a
    # bare agents/ at the repo root (ECC and others). Scan both.
    agents = sorted(set(glob.glob(os.path.join(root, ".claude/agents/*.md")) +
                        glob.glob(os.path.join(root, "agents/*.md"))))
    skills = sorted(set(glob.glob(os.path.join(root, ".claude/skills/*/SKILL.md")) +
                        glob.glob(os.path.join(root, "skills/*/SKILL.md"))))
    if not agents and not skills:
        # Reporting CLEAN on an empty scan is the silent-defect class this whole
        # file exists to prevent: absence of a result read as a correct negative.
        fail("<scan>", f"found no agents and no skills under {root} — checked "
                       f".claude/agents, agents/, .claude/skills/*/SKILL.md and "
                       f"skills/*/SKILL.md. Either the path is wrong or the layout "
                       f"is one this checker does not know. NOT a clean result")
    skill_names = {os.path.basename(os.path.dirname(p)) for p in skills}
    roster_chars = 0

    # ---- agents ------------------------------------------------------------
    for p in agents:
        rel = os.path.relpath(p, root)
        fm, body, err = frontmatter(p)
        if err: fail(rel, err); continue
        name = scalar(fm, "name")
        if not name: fail(rel, "no `name:`")
        elif not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name):
            fail(rel, f"name `{name}` is not kebab-case [A]")
        d = scalar(fm, "description")
        check_description(rel, d, "agent")
        if d: roster_chars += len(d)

        if not has_key(fm, "tools"):
            fail(rel, "`tools:` is omitted — this INHERITS EVERY TOOL, not none. "
                      "The most dangerous line you can fail to write [B]. "
                      "68/68 agents in the ECC library set it explicitly")
        pre = block_list(fm, "skills")
        if len(pre) > PRELOAD_MAX:
            fail(rel, f"{len(pre)} preloaded skills, over the cap of {PRELOAD_MAX} "
                      f"— a fourth function is the signal you have two agents [M]")
        for s in pre:
            if s not in skill_names:
                fail(rel, f"preloads `{s}`, which does not exist in this repo")
        for m in re.finditer(r'command: *"?([^"\n]+)"?', fm):
            hp = m.group(1).replace("${CLAUDE_PROJECT_DIR}", root).strip()
            if not os.path.exists(hp): fail(rel, f"hook command not found: {m.group(1)}")
            elif not os.access(hp, os.X_OK): fail(rel, f"hook is not executable: {m.group(1)}")
        for m in re.finditer(r'matcher: *"([^"]+)"', fm):
            pat = m.group(1)
            if pat.strip() in ("*", ""): continue
            if not (pat.startswith("^") and pat.endswith("$")):
                fail(rel, f'matcher "{pat}" is unanchored — a matcher is a substring '
                          f'search, so "Write" also matches TodoWrite and "Edit" also '
                          f'matches NotebookEdit. Anchor it: ^(...)$ [M]')

    # ---- skills ------------------------------------------------------------
    for p in skills:
        d_ = os.path.dirname(p); rel = os.path.relpath(p, root)
        folder = os.path.basename(d_)
        if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", folder):
            fail(rel, f"folder `{folder}` is not kebab-case [A]")
        if any(r in folder for r in RESERVED):
            fail(rel, f"folder `{folder}` contains a reserved word {RESERVED} [A]")
        if os.path.exists(os.path.join(d_, "README.md")):
            fail(rel, "README.md inside a skill folder is forbidden — "
                      "documentation goes in SKILL.md or references/ [A]")
        for wrong in ("skill.md", "Skill.md", "SKILL.MD"):
            if os.path.exists(os.path.join(d_, wrong)) and wrong != "SKILL.md":
                fail(rel, f"`{wrong}` present — the filename must be exactly SKILL.md [A]")
        fm, body, err = frontmatter(p)
        if err: fail(rel, err); continue
        check_description(rel, scalar(fm, "description"), "skill")
        c = scalar(fm, "compatibility")
        if c and len(c) > COMPAT_MAX: fail(rel, f"compatibility is {len(c)} chars, over {COMPAT_MAX} [A]")
        w = len(body.split())
        if w > BODY_MAX_W: fail(rel, f"body is {w} words, over the {BODY_MAX_W} guidance [A]")
        for m in re.finditer(r"`((?:references|assets|scripts)/[\w./-]+)`", body):
            if not os.path.exists(os.path.join(d_, m.group(1))):
                fail(rel, f"dead reference: `{m.group(1)}` does not exist")
        if not re.search(r"^## When (this|these|it)\b.*(not apply|does not|NOT)", body, re.M|re.I):
            warn(rel, "no decline section — a procedure that never declines cannot discriminate")

    # ---- roster ------------------------------------------------------------
    tok = roster_chars // 4
    if tok > ROSTER_MAX_T:
        fail("<roster>", f"agent descriptions total ~{tok} tokens, over the shared "
                         f"{ROSTER_MAX_T} budget — Claude Code warns at startup [B]")
    # NOT-clauses must name something real
    for p in skills + agents:
        rel = os.path.relpath(p, root); txt = open(p, encoding="utf-8").read()
        for m in re.finditer(r"\(use ([a-z0-9-]+)\)", txt):
            t = m.group(1)
            if t not in skill_names and not os.path.exists(os.path.join(root, ".claude/agents", t + ".md")):
                warn(rel, f"routes to `{t}`, which exists neither as a skill nor an "
                          f"agent here — fine if it is a bundled command or a plugin "
                          f"skill this checker cannot see, dead otherwise")

    # ---- report ------------------------------------------------------------
    print(f"agents {len(agents)} · skills {len(skills)} · "
          f"roster ~{tok}/{ROSTER_MAX_T} tokens ({tok*100//ROSTER_MAX_T}%)\n")
    for w, m in warns: print(f"  WARN  {w}: {m}")
    if warns: print()
    for w, m in fails: print(f"  FAIL  {w}: {m}")
    print(f"\n{'CLEAN' if not fails else str(len(fails)) + ' FAILURES'}"
          f"{', ' + str(len(warns)) + ' warnings' if warns else ''}")
    return 1 if fails else 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
