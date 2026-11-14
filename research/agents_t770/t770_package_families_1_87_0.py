"""T-770 r10: PACKAGE -> FAMILY attribution by line diff V3.0.86 -> V3.0.87 (T-770g package; V3.0.86 = the T-770 r9
run of record 7563e411), with the T-485 diff and
family rules unchanged (research/agents_t483/t483_package_families.attribute). Item codes, counts and hashes only.
Run on the Verifier's own Drive chain run (research/agents_t770/v3087_run.py --out <dir>), IN the merge:

    bash scripts/agent_env.sh run --tree <engine> research/agents_t770/t770_package_families_1_87_0.py --run <dir> \
        --master rules/coverage/BOQ_FAMILY_MASTER_1.87.0.json --out research/agents_t770/out/T770_PACKAGE_FAMILIES_1_87_0.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t483"))
import t483_package_families as PF  # noqa: E402

CHAIN = (86, 87)


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
