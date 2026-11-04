"""T-483 r2: PACKAGE -> FAMILY attribution by line diff along the merged candidate CHAIN V3.0.46 -> V3.0.47 ->
V3.0.48 -> V3.0.50 (V3.0.49 was never merged: T-497 V3.0.50 extends V3.0.48), with the T-485 diff and family rules
unchanged (research/agents_t485/t485_package_families.py diff_versions / families_changed). Item codes, counts and
hashes only.

    python3 -I research/agents_t483/t483_package_families.py --run <dir with V3_0_46/47/48/50_BOQ_LINES.json> \
        --master rules/coverage/BOQ_FAMILY_MASTER_1.47.0.json --out research/agents_t483/out/T483_PACKAGE_FAMILIES.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t485"))
import t485_package_families as PF  # noqa: E402

CHAIN = (46, 47, 48, 50)


def attribute(run, master, chain=CHAIN):
    out = {"schema": PF.SCHEMA, "registry": master.get("version"), "chain": [f"ARCH_TAKEOFF_V3.0.{n}" for n in chain],
           "versions": {}}
    prev = None
    for n in chain:
        raw = PF.version_file(run, n).read_bytes()
        lines = PF._lines(json.loads(raw))
        rec = {"lines": len(lines), "lines_sha256": hashlib.sha256(raw).hexdigest()}
        if prev is not None:
            d = PF.diff_versions(prev[1], lines)
            fams, apart = PF.families_changed(d, master)
            rfams, rapart = PF.families_changed(d, master, record=True)
            rec.update(previous=f"ARCH_TAKEOFF_V3.0.{prev[0]}", item_codes=d, families=fams, apart=apart,
                       record_families=sorted(rfams), record_apart=rapart,
                       touched=sum(v["added"] + v["removed"] + v["changed"] for v in d.values()),
                       record_only=sum(v["record"] for v in d.values()))
        out["versions"][f"ARCH_TAKEOFF_V3.0.{n}"] = rec
        prev = (n, lines)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--master", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    doc = attribute(a.run, json.loads(Path(a.master).read_text(encoding="utf-8")))
    Path(a.out).write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    for k, v in doc["versions"].items():
        print(k, v["lines"], v["lines_sha256"][:8], v.get("families"), "record:", v.get("record_families"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
