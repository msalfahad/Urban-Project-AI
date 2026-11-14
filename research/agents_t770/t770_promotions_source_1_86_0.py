"""T-770 r9 (1.86.0, package T-770f; the r3 tool pointed at 1.86.0): the merge commit and Checker verdict head of the T-770f package pending in BOQ_FAMILY_MASTER_1.86.0, with
the T-485 / T-483 r2 rules unchanged (research/agents_t483/t483_promotions_source.build: exactly one merge of
agents/task-T-770 on HEAD whose second parent holds the task commit and whose first parent does not; the verdict is the
head of the row's Status cell, quoted verbatim) + the agents/control commit the verdict was read at. The T-314 r4 tool
(research/agents_t314/t314_promotions_source.py) pointed at 1.86.0; run by the Verifier IN the merge, after the merge
commit exists and the MERGED verdict is on the board:

    bash scripts/agent_env.sh run --tree <engine> research/agents_t770/t770_promotions_source_1_86_0.py \
        --board <agents/control>/docs/agents --out research/agents_t770/out/PROMOTIONS_SOURCE_1_86_0.json
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t483"))
import t483_promotions_source as PS  # noqa: E402

MASTER = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.86.0.json"
EXPECT = ["T-770f"]


def build(board):
    master = json.loads(MASTER.read_text(encoding="utf-8"))
    pend = [p["task"] for p in master.get("pending_packages") or ()]
    if pend != EXPECT:
        raise SystemExit(f"1.86.0 pending packages {pend}: expected {EXPECT}")
    return PS.build(master, board)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    board_commit = subprocess.run(["git", "-C", a.board, "rev-parse", "--short=8", "HEAD"], capture_output=True,
                                  text=True, check=True).stdout.strip()
    out = [dict(r, board_commit=board_commit) for r in build(a.board)]
    if [r["task"] for r in out] != EXPECT:
        raise SystemExit(f"1.86.0: merged pending {[r['task'] for r in out]}, expected {EXPECT} "
                         "(an unmerged package is never promoted)")
    Path(a.out).write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    for r in out:
        print(r["task"], r["merge_commit"][:8], r["verdict_time"], r["board_commit"], r["board_status_head"][:160])
    return 0


if __name__ == "__main__":
    sys.exit(main())
