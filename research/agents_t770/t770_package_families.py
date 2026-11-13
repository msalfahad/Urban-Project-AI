"""T-770 r3: PACKAGE -> FAMILY attribution by line diff V3.0.79 -> V3.0.81 (T-770 package; V3.0.79 = T-314 run of
record aa0ec38a; V3.0.80 was never merged: its reservation lapsed, T-750 folded into T-770 r3), with the T-485 diff and
family rules unchanged (research/agents_t483/t483_package_families.attribute). Item codes, counts and hashes only.
Run on the Verifier's own Drive chain run (research/agents_t770/v3081_run.py --out <dir>), IN the merge:

    bash scripts/agent_env.sh run --tree <engine> research/agents_t770/t770_package_families.py --run <dir> \
        --master rules/coverage/BOQ_FAMILY_MASTER_1.81.0.json --out research/agents_t770/out/T770_PACKAGE_FAMILIES.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t483"))
import t483_package_families as PF  # noqa: E402

CHAIN = (79, 81)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--master", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    doc = PF.attribute(a.run, json.loads(Path(a.master).read_text(encoding="utf-8")), chain=CHAIN)
    Path(a.out).write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    for k, v in doc["versions"].items():
        print(k, v["lines"], v["lines_sha256"][:8], v.get("families"), "record:", v.get("record_families"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
