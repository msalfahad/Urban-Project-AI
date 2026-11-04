"""T-483 r2: the merge commit and Checker verdict head of every merged pending package of BOQ_FAMILY_MASTER_1.45.0
(T-443, T-350b), with the T-485 rules (research/agents_t485/t485_promotions_source.py, unchanged): exactly one merge
of agents/task-<row> on HEAD whose second parent holds the task commit and whose first parent does not; the verdict is
the head of the row's Status cell, quoted verbatim. A package id with a round letter (T-350b: the second T-350
package, task ids T-nnn[a-z]) is looked up under its board row and branch T-350.

    python3 -I research/agents_t483/t483_promotions_source.py --board <agents/control>/docs/agents \
        --out research/agents_t483/out/PROMOTIONS_SOURCE_1_46_0.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t485"))
import t485_promotions_source as PS  # noqa: E402

MASTER = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.45.0.json"


def row_id(task):
    return re.sub(r"[a-z]$", "", task)


def build(master, board):
    log = PS._git("log", "--merges", "--format=%H %P|%s", "HEAD").stdout.splitlines()
    rs = PS.rows(board)
    out = []
    for p in master.get("pending_packages") or ():
        rid = row_id(p["task"])
        hits = PS.merge_of(rid, p["task_commit"], log)
        if not hits:
            continue
        if len(hits) != 1:
            raise SystemExit(f"{p['task']}: {len(hits)} merges bring its task commit in")
        fn, row = rs[rid]
        out.append(dict(PS.verdict_head(rid, hits[0], fn, row), task=p["task"]))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    out = build(json.loads(MASTER.read_text(encoding="utf-8")), a.board)
    Path(a.out).write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    for r in out:
        print(r["task"], r["merge_commit"][:8], r["verdict_time"], r["board_file"], r["board_status_head"][:160])
    return 0


if __name__ == "__main__":
    sys.exit(main())
