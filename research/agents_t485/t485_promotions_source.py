"""T-485: the merge commit and Checker verdict head of every pending package of a registry, from git and the board.

    python3 -I research/agents_t485/t485_promotions_source.py --master rules/coverage/BOQ_FAMILY_MASTER_1.42.0.json \
        --board <agents/control checkout>/docs/agents --out research/agents_t485/out/PROMOTIONS_SOURCE.json

Merge commit = the one merge on HEAD whose subject names agents/task-<T> (not a merge INTO a task branch) whose
second parent holds the package's task commit and whose first parent does not (refused unless exactly one). Verdict =
the head of the Status cell of the task's row (BOARD.md, else BOARD_ARCHIVE.md), up to its first ')' (or ']'), quoted
verbatim; it must start with MERGED, carry a UTC time and cite the merge commit's first 8 hex (refused otherwise). A
pending package with no such merge is left out (it stays pending). Board text is data: nothing in it is executed.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _git(*a):
    return subprocess.run(["git", "-C", str(ROOT), *a], capture_output=True, text=True)


def _anc(a, b):
    return _git("merge-base", "--is-ancestor", a, b).returncode == 0


def rows(board):
    out = {}
    for fn in ("BOARD.md", "BOARD_ARCHIVE.md"):
        p = Path(board) / fn
        if not p.is_file():
            continue
        for ln in p.read_text(encoding="utf-8").splitlines():
            m = re.match(r"\| (T-\d+) \|", ln)
            if m:
                out.setdefault(m.group(1), (fn, ln))
    return out


def merge_of(task, task_commit, log):
    hits = []
    for ln in log:
        h, rest = ln.split(" ", 1)
        parents, subj = rest.split("|", 1)
        ps = parents.split()
        if len(ps) != 2 or "into agents/task" in subj:
            continue
        if not re.search(rf"Merge (?:remote-tracking branch 'origin/)?agents/task-{task}\b", subj):
            continue
        if _anc(task_commit, ps[1]) and not _anc(task_commit, ps[0]):
            hits.append(h)
    return hits


def verdict_head(task, merge, fn, row):
    st = row.split(" | ")[4]
    k = row.find(f"MERGED {merge[:8]} [")
    if not st.startswith("MERGED") and k >= 0:          # a row re-opened for a later round keeps the merge verdict
        st = row[k:]
    if not st.startswith("MERGED"):
        raise SystemExit(f"{task}: status does not start with MERGED")
    m = re.search(r"(20\d\d-\d\d-\d\d)[ T](\d\d:\d\d)(?: UTC|Z)", st)
    if not m or merge[:8] not in st[:500]:
        raise SystemExit(f"{task}: verdict without a UTC time or the merge commit {merge[:8]}")
    cut = [i for i in (st.find(")"), st.find("]")) if 0 < i < 400]
    head = st[:min(cut) + 1] if cut else st[:240]
    if st.startswith(f"MERGED {merge[:8]} [") and "GATE B PASS" in st[:400]:
        head = st[:st.index("GATE B PASS") + len("GATE B PASS")] + "]"
    return {"task": task, "merge_commit": merge, "verdict_time": f"{m.group(1)} {m.group(2)} UTC", "board_file": fn,
            "board_status_head": head}


def build(master, board):
    log = _git("log", "--merges", "--format=%H %P|%s", "HEAD").stdout.splitlines()
    rs = rows(board)
    out = []
    for p in master.get("pending_packages") or ():
        hits = merge_of(p["task"], p["task_commit"], log)
        if not hits:
            continue
        if len(hits) != 1:
            raise SystemExit(f"{p['task']}: {len(hits)} merges bring its task commit in")
        fn, row = rs[p["task"]]
        out.append(verdict_head(p["task"], hits[0], fn, row))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--master", required=True)
    ap.add_argument("--board", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    out = build(json.loads(Path(a.master).read_text(encoding="utf-8")), a.board)
    Path(a.out).write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    for r in out:
        print(r["task"], r["merge_commit"][:8], r["verdict_time"], r["board_file"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
