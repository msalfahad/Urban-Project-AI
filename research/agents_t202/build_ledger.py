"""T-202: build the known-failures ledger (known_failures.json) from one full-suite pytest output on the working head.

    python3 -I research/agents_t202/build_ledger.py RUN.txt HEAD_SHA

RUN.txt is the -q output of `bash scripts/agent_env.sh pytest --tree <tree> tests/` on HEAD_SHA. Every FAILED / ERROR
summary id gets exactly one cause from CAUSES (by test file and, where a file has several causes, test name); an id no
cause covers stops the build (a new failure must be diagnosed, never filed under a guess). The failure text of each id
(first `E` line of its section, when pytest printed one) must match the cause's evidence pattern, else the build stops.
`first_failing` is the bisect result for causes found by bisection, else the first first-parent commit of the working
branch that contains the test file (the input was never in the repository, so the test has failed here since it was
added). Standard library only; writes only known_failures.json beside this file.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SUMMARY = re.compile(r"^(FAILED|ERROR) (\S+?)(?: - .*)?$")
SECTION = re.compile(r"^_{3,} (?:ERROR at setup of )?(.+?) _{3,}$")

# T-466 (owner directive 2026-11-02 D5): the ledger lists REAL known failures only, so a red test always means something is
# wrong. An ENVIRONMENT failure (a private input absent, a worktree / shallow-clone git layout, a network or machine
# limit) is never a ledger cause: since T-462 a test that needs private data SKIPS when it is absent ("private data not
# available: <name>"), T-463 keeps the git-history facts in the repository, T-464 / T-210 stamp a worktree's commit.
# A failure of that kind is therefore a defect of the test or of its private-input declaration and must be fixed, not
# filed. build() refuses a cause whose code is listed here.
ENVIRONMENT_CODES = frozenset({"PRIVATE_INPUT_ABSENT", "WORKTREE_GITDIR", "SHALLOW_CLONE", "NETWORK_UNAVAILABLE",
                               "MACHINE_LIMIT"})

# (file regex, test-name regex, cause code, cause text, evidence regex, first_failing or None, owner)
# T-466: EMPTY on the working head 983b75f4: the full suite left 0 failures. The six causes of the T-202 ledger (head
# d699b650, 396 ids) are history (git log of this file and research/agents_t202/KNOWN_FAILURES.md s.0): two were
# environment causes (PRIVATE_INPUT_ABSENT 390 ids -> SKIPPED since T-462; WORKTREE_GITDIR 1 id -> passes since T-210 /
# T-464) and three were code defects fixed by T-465 (DEPENDENCY_NOT_REGISTERED 2, K1_NOT_STDLIB 1, K1_IMPORTS_EZDXF 2).
# A new real failure gets its own diagnosed cause here, with its evidence pattern and owner.
CAUSES = ()


def git(*a):
    return subprocess.run(["git", "-C", str(ROOT), *a], check=True, capture_output=True, text=True).stdout


def first_parent_add(path, head):
    shas = git("log", "--first-parent", "--reverse", "--format=%h", head, "--", path).split()
    return shas[0] if shas else "UNKNOWN"


def sections(text):
    """{(file, test name): [E lines]} from the failure / error sections."""
    out, cur, lines = {}, None, []
    for ln in text.splitlines():
        m = SECTION.match(ln)
        if m:
            cur, lines = m.group(1), []
            continue
        if cur is None:
            continue
        if ln.startswith("E "):
            lines.append(ln)
        f = re.match(r"^(tests/\S+?\.py):\d+:", ln)
        if f:
            out.setdefault((f.group(1), cur), lines)
    return out


def build(text, head):
    ids = {}
    for ln in text.splitlines():
        m = SUMMARY.match(ln.strip())
        if m:
            ids[m.group(2)] = m.group(1)
    secs = sections(text)
    entries, problems = [], []
    for nid, kind in sorted(ids.items()):
        path, _, name = nid.partition("::")
        hit = [c for c in CAUSES if re.search(c[0], path) and re.fullmatch(c[1], name)]
        if not hit:
            problems.append(f"no cause covers {nid}")
            continue
        _, _, code, text_, ev, ff, owner = hit[0]
        if code in ENVIRONMENT_CODES:
            problems.append(f"{nid}: cause {code} is an environment cause, never a known failure (fix the test)")
            continue
        e = secs.get((path, name), [])
        evidence = next((x[1:].strip() for x in e if re.search(ev, x)), None)
        if e and evidence is None:
            problems.append(f"{nid}: failure text does not match the cause {code}: {e[0][:120]}")
            continue
        entries.append({"id": nid, "kind": kind, "cause_code": code, "cause": text_,
                        "evidence": (evidence or "no section printed; covered by the file rule")[:300],
                        "first_failing": ff or first_parent_add(path, head),
                        "first_failing_basis": "bisect (first-parent, research/agents_t202/KNOWN_FAILURES.md s.2)"
                        if ff else "first first-parent commit containing the test file", "owner": owner})
    return entries, problems


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 2:
        print(__doc__)
        return 2
    text = Path(argv[0]).read_text(encoding="utf-8", errors="replace")
    head = argv[1]
    entries, problems = build(text, head)
    for p in problems:
        print("PROBLEM:", p)
    if problems:
        return 1
    doc = {"schema": "URBAN_KNOWN_FAILURES_V1", "head": head, "built_by": "research/agents_t202/build_ledger.py",
           "failures": entries}
    (HERE / "known_failures.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    by = {}
    for e in entries:
        by[e["cause_code"]] = by.get(e["cause_code"], 0) + 1
    print(f"ledger: {len(entries)} ids; by cause {dict(sorted(by.items()))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
