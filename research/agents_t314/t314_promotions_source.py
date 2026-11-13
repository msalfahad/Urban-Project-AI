"""T-314 r4: the merge commit and Checker verdict head of every MERGED pending package of a BOQ_FAMILY_MASTER, with the
T-485 / T-483 r2 rules unchanged (research/agents_t483/t483_promotions_source.py build / verdict_head: exactly one merge
of agents/task-<row> on HEAD whose second parent holds the task commit and whose first parent does not; the verdict is
the head of the row's Status cell, quoted verbatim) + the agents/control commit the verdict was read at. A pending
package with no such merge on HEAD is left out (never promoted).

Two sources feed BOQ_FAMILY_MASTER_1.80.0 (research/agents_t314/build_master_1_80_0.py, R-T485-1 multi-promotion as
1.48.0):

  (1) T-738, merged 208c5689 but left PENDING in 1.79.0 (its in-merge --promote did not run); built on the task branch:
    python3 -I research/agents_t314/t314_promotions_source.py --master 1.79.0 --board <agents/control>/docs/agents \
        --out research/agents_t314/out/PROMOTIONS_SOURCE_T738_1_80_0.json
  (2) T-314 itself, run by the Verifier IN the merge, after the merge commit exists:
    python3 -I research/agents_t314/t314_promotions_source.py --master 1.80.0 --board <agents/control>/docs/agents \
        --out research/agents_t314/out/PROMOTIONS_SOURCE_1_80_0.json
    python3 -I research/agents_t314/build_master_1_80_0.py --promote --write      # then commit both in the merge
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

MASTERS = {"1.79.0": ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.79.0.json",
           "1.80.0": ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.80.0.json"}
EXPECT = {"1.79.0": ["T-738"], "1.80.0": ["T-314"]}


def build(version, board):
    master = json.loads(MASTERS[version].read_text(encoding="utf-8"))
    pend = [p["task"] for p in master.get("pending_packages") or ()]
    if pend != EXPECT[version]:
        raise SystemExit(f"{version} pending packages {pend}: expected {EXPECT[version]}")
    return PS.build(master, board)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--master", required=True, choices=sorted(MASTERS))
    ap.add_argument("--board", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    board_commit = subprocess.run(["git", "-C", a.board, "rev-parse", "--short=8", "HEAD"], capture_output=True,
                                  text=True, check=True).stdout.strip()
    out = [dict(r, board_commit=board_commit) for r in build(a.master, a.board)]
    if [r["task"] for r in out] != EXPECT[a.master]:
        raise SystemExit(f"{a.master}: merged pending {[r['task'] for r in out]}, expected {EXPECT[a.master]} "
                         "(an unmerged package is never promoted)")
    Path(a.out).write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    for r in out:
        print(r["task"], r["merge_commit"][:8], r["verdict_time"], r["board_commit"], r["board_status_head"][:160])
    return 0


if __name__ == "__main__":
    sys.exit(main())
