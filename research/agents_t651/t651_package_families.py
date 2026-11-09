"""T-651: PACKAGE -> FAMILY attribution by line diff along the merged candidate chain V3.0.58 -> V3.0.59 (T-498,
merge 4c37ce2c), with the T-485 diff and family rules unchanged (research/agents_t483/t483_package_families.attribute).
Item codes, counts and hashes only.

    python3 -I research/agents_t525/t525_package_families.py --run <dir with V3_0_58/59_BOQ_LINES.json> \
        --master rules/coverage/BOQ_FAMILY_MASTER_1.58.0.json --out research/agents_t651/out/T651_PACKAGE_FAMILIES.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t483"))
import t483_package_families as PF  # noqa: E402

CHAIN = (58, 59)


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
