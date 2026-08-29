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
            fail(rel, f"{len(pre)} preloaded skills, over THIS REPO'S cap of "
                      f"{PRELOAD_MAX} — no documented limit on `skills:` exists; this "
                      f"is a measured quality finding, and a fourth function is the "
                      f"signal you have two agents [M]")
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

    # ---- and the generated copy must actually match ------------------------
    # The check below stops a hand-typed limit. This one stops the other direction:
    # a constant changed here and LIMITS.md never regenerated, so the template quietly
    # tells the writer an old number while the checker enforces a new one.
    for lp in glob.glob(os.path.join(root, ".claude", "skills", "*", "assets",
                                     "template", "LIMITS.md")):
        rel = os.path.relpath(lp, root)
        try:
            on_disk = open(lp, encoding="utf-8").read().strip()
        except OSError as e:
            fail(rel, f"unreadable: {e}"); continue
        if on_disk != emit_limits().strip():
            fail(rel, "is out of date with this checker's constants. Regenerate: "
                      "`python3 .claude/validate/agents.py --limits > " + rel + "` [M]")

    # ---- the template may point at a limit, never restate it ----------------
    # L1 of docs/architecture-agent-factory.md: the numbers live here, the prose lives
    # in the template, and neither imports the other. LIMITS.md is generated from the
    # constants above; a hand-typed copy anywhere else is a second place for a number
    # to rot, and the checker is the copy that actually gets run.
    #
    # Only the two unambiguous constants are scanned. 5000 collides with the
    # compaction budget the template legitimately discusses, and 3 and 500 are too
    # common in prose to test this way — a check with false positives gets disabled,
    # which is worse than a narrower one that holds.
    watched = {str(DESC_MAX): "the description cap",
               str(ROSTER_MAX_T): "the roster budget",
               f"{ROSTER_MAX_T:,}": "the roster budget"}
    for tp in glob.glob(os.path.join(root, ".claude", "skills", "*", "assets",
                                     "template", "*.md")):
        if os.path.basename(tp) == "LIMITS.md": continue
        rel = os.path.relpath(tp, root)
        try:
            body = open(tp, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        for lit, what in watched.items():
            if lit in body:
                fail(rel, f"restates {what} as `{lit}`. The template says HOW to write "
                          f"a part; this checker owns the number, and LIMITS.md is "
                          f"generated from it (`--limits`). Point at LIMITS.md instead "
                          f"— a hand-copied limit is a second place for it to rot [M]")

    # ---- every agent ships with evals ---------------------------------------
    # CLAUDE.md: "Every agent ships with evals carrying a negative control and a
    # containment case." A P5 absence audit found that sentence enforced nowhere — and
    # two of seven agents carrying no eval artefact of any kind, not even a brief saying
    # the test is unmet. A rule that lives only in prose is the thing this repo's own
    # standing rule says a "must never" may not be.
    for p in agents:
        rel = os.path.relpath(p, root)
        name = os.path.basename(p)[:-3]
        found = []
        for cand in (glob.glob(os.path.join(root, "docs", "*.md")) +
                     glob.glob(os.path.join(root, ".claude", "skills", "*", "evals.md")) +
                     glob.glob(os.path.join(root, "docs", "research", "evidence", "*.md"))):
            b = os.path.basename(cand).lower()
            if not any(k in b for k in ("eval", "tester-brief", "test-results", "spec")):
                continue
            # A count of mentions is not a count of things. The first version of this
            # check credited two agents with a spec because a DIFFERENT agent's spec
            # named them once, in a NOT-clause — the exact failure the audit procedure
            # warns about, committed inside the checker meant to catch it. An artefact
            # covers an agent when its FILENAME says so, or when it returns to the agent
            # repeatedly; a single passing reference is a cross-reference.
            try:
                body = open(cand, encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            if name in b or body.count(name) >= 3:
                found.append(os.path.relpath(cand, root))
        if not found:
            fail(rel, f"no eval artefact anywhere names `{name}` — not an evals.md, not a "
                      f"tester brief, not a spec, not a test result. CLAUDE.md: every agent "
                      f"ships with evals carrying a negative control and a containment "
                      f"case. An agent nobody can fail is not tested, it is unexamined [M]")
        # "result", not "test-results". The first version of this line demanded the
        # exact substring `test-results`, so a file literally named
        # `evals-rebuild-pair-results.md` did not count as a result — reported by the
        # tester that wrote it, which pointedly did NOT rename its file or patch this
        # checker to go green, because either would be grading its own work.
        # The limit that remains: this is a filename rule. A file named `-results.md`
        # containing no results passes it. Nothing here reads what a result says.
        elif not any("result" in f or "evidence" in f for f in found):
            warn(rel, f"has eval material ({', '.join(found[:2])}) but no recorded RESULT. "
                      f"A suite nobody ran is a plan [M]")

    # ---- settings.json -----------------------------------------------------
    # A P5 absence audit found `"matcher": "Edit|Write"` sitting in .claude/settings.json —
    # the exact string selftest.sh plants as a defect — while this checker scanned only
    # agent frontmatter. A rule enforced on agents and not on the file that configures the
    # whole session is a blind spot exactly where the blast radius is widest: settings
    # hooks run for every tool call in the session, not for one agent.
    for sp in (os.path.join(root, ".claude", "settings.json"),
               os.path.join(root, ".claude", "settings.local.json")):
        if not os.path.exists(sp): continue
        rel = os.path.relpath(sp, root)
        try:
            cfg = json.load(open(sp, encoding="utf-8"))
        except Exception as e:
            fail(rel, f"does not parse as JSON: {e}")
            continue
        for event, entries in (cfg.get("hooks") or {}).items():
            for entry in entries or []:
                pat = (entry or {}).get("matcher")
                if pat is None or str(pat).strip() in ("*", ""): continue
                if not (str(pat).startswith("^") and str(pat).endswith("$")):
                    fail(rel, f'{event} matcher "{pat}" is unanchored — a matcher is a '
                              f'substring search, so "Write" also matches TodoWrite and '
                              f'"Edit" also matches NotebookEdit. Anchor it: ^(...)$ [M]')
                for h in (entry.get("hooks") or []):
                    cmd = (h or {}).get("command", "")
                    hp = cmd.replace("${CLAUDE_PROJECT_DIR}", root).strip()
                    if h.get("type") == "command" and hp and " " not in hp:
                        if not os.path.exists(hp):
                            fail(rel, f"{event} hook command not found: {cmd}")
                        elif not os.access(hp, os.X_OK):
                            fail(rel, f"{event} hook is not executable: {cmd}")

    # ---- report ------------------------------------------------------------
    print(f"agents {len(agents)} · skills {len(skills)} · "
          f"roster ~{tok}/{ROSTER_MAX_T} tokens ({tok*100//ROSTER_MAX_T}%)\n")
    for w, m in warns: print(f"  WARN  {w}: {m}")
    if warns: print()
    for w, m in fails: print(f"  FAIL  {w}: {m}")
    # Every row carries its provenance tag, and until now the key to those tags lived
    # only in this file's docstring — so a reader of the output saw `[M]` with nothing
    # to read it against. A research run flagged the consequence: an agent reporting a
    # fourth preloaded skill would call it a limit violation, when no documented cap on
    # `skills:` exists at all. The rule is ours, it is a measured quality finding, and
    # the output now says so rather than letting it borrow the authority of a spec.
    if fails or warns:
        print("\n  where each rule comes from:")
        print("    [A] Anthropic, The Complete Guide to Building Skills for Claude")
        print("    [B] code.claude.com/docs/en/sub-agents")
        print("    [C] code.claude.com/docs/en/skills")
        print("    [M] measured in this project — a house rule, not a documented limit")
        print("        (/home/user/skills-repo/knowledge/notes/)")
    print(f"\n{'CLEAN' if not fails else str(len(fails)) + ' FAILURES'}"
          f"{', ' + str(len(warns)) + ' warnings' if warns else ''}")
    return 1 if fails else 0

def emit_limits():
    """The single source for every limit this checker enforces.

    The template describes HOW to write each part; this function says WHAT the
    limits are. A number hand-copied into the template is a second place for it to
    rot, so `template/LIMITS.md` is GENERATED from here and never edited by hand.
    """
    rows = [
        ("description, max characters", DESC_MAX, "A",
         "frontmatter enters a system prompt; the cap is Anthropic's"),
        ("compatibility, max characters", COMPAT_MAX, "A", ""),
        ("SKILL.md body, max words", BODY_MAX_W, "A",
         "guidance for SKILL.md — NOT a limit on an agent body"),
        ("combined agent descriptions, max tokens", ROSTER_MAX_T, "B",
         "shared by every non-built-in agent; Claude Code warns at startup"),
        ("preloaded skills per agent, max", PRELOAD_MAX, "M",
         "1-3 modules ~+19.0pp, 4+ ~+10.1pp — a quality finding, not a documented cap"),
    ]
    out = ["# Limits — GENERATED, do not edit",
           "",
           "Regenerate with `python3 .claude/validate/agents.py --limits`.",
           "",
           "Hand-editing this file reintroduces exactly the drift it exists to prevent:",
           "the checker would keep enforcing its own constants while the template told",
           "the writer something else.",
           "",
           "| Limit | Value | Source | Note |",
           "|---|---|---|---|"]
    src = {"A": "Anthropic, skills guide", "B": "subagents docs",
           "C": "skills docs", "M": "measured here"}
    for name, val, tag, note in rows:
        out.append(f"| {name} | **{val}** | [{tag}] {src[tag]} | {note} |")
    out += ["", f"Reserved words in a skill name: {', '.join(RESERVED)} [A]", ""]
    return "\n".join(out)


if __name__ == "__main__":
    if "--limits" in sys.argv:
        print(emit_limits()); sys.exit(0)
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
