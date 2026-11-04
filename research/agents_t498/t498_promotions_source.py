"""T-498 r2: the merge commit and Checker verdict head of every merged pending package of BOQ_FAMILY_MASTER_1.54.0
(T-310 V3.0.57, merge 87ef8718), with the T-485 / T-483 r2 rules unchanged (research/agents_t483/t483_promotions_source.py
build / verdict_head: exactly one merge of agents/task-<row> on HEAD whose second parent holds the task commit and whose
first parent does not; the verdict is the head of the row's Status cell, quoted verbatim).

    python3 -I research/agents_t498/t498_promotions_source.py --board <agents/control>/docs/agents \
        --out research/agents_t498/out/PROMOTIONS_SOURCE_1_55_0.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t483"))
import t483_promotions_source as PS  # noqa: E402

MASTER = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.54.0.json"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    out = PS.build(json.loads(MASTER.read_text(encoding="utf-8")), a.board)
    Path(a.out).write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    for r in out:
        print(r["task"], r["merge_commit"][:8], r["verdict_time"], r["board_file"], r["board_status_head"][:160])
    return 0


if __name__ == "__main__":
    sys.exit(main())
