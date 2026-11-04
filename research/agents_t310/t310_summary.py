"""T-310 r4: research/agents_t310/summary_t310.json from a finished v3052_run.py directory (<out>/v3052). Item codes,
units, states, quantities and engine ids only (no coordinates, no names). With --previous it asserts that the ledger
rows, the totals moved by code and the wet_area_wp identity equal the previous summary's (a rebase moves no quantity
of this package).

    python3 -I research/agents_t310/t310_summary.py --run <out>/v3052 --out research/agents_t310/summary_t310.json \
        [--previous <summary of the earlier round>]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v302 as A302  # noqa: E402

BASE, NEW = "V3_0_51_BOQ_LINES.json", "V3_0_52_BOQ_LINES.json"
DRAWINGS = ("Drive 'Alsenan chalet project': P7757.dxf (P7757_DXF_COMPRESSED.zip), 'ST7757 dxf.dxf' 9f9d1179; run "
            "research/agents_t310/v3052_run.py --t167 (own T-167 run this session); r4: V3_0_48 33a81c53 -> V3_0_50 "
            "d40c4ec5 (T-497) -> V3_0_51 (T-483) base")


def _q(q):
    return A302._q(q) if q else ""


def build(d):
    d = Path(d)
    run = json.loads((d / "V3_0_52_RUN.json").read_text(encoding="utf-8"))
    led = json.loads((d / "V3_0_52_INTEGRATION_LEDGER.json").read_text(encoding="utf-8"))

    def cand(fn):
        raw = (d / fn).read_bytes()
        return {"file": fn, "sha256_8": hashlib.sha256(raw).hexdigest()[:8], "lines": len(json.loads(raw))}
    ident = run["identity"]
    return {"task": "T-310", "method": "ARCH_TAKEOFF_V3.0.52", "base_candidate": cand(BASE),
            "new_candidate": cand(NEW),
            "identity": {k: ident[k] for k in ("replaced", "added", "outside_rows", "outside_rows_identical_to_base",
                                               "outside_rows_sha256", "wet_area_wp", "diff")},
            "rows": [{"action": r["action"], "line_id": r["line_id"], "item_code": r["item_code"], "floor": r["floor"],
                      "room_id": r["room_id"], "element_id": r["element_id"], "unit": r["unit"],
                      "base": _q(r["before_base"]), "v3_0_52": _q(r["after_v3_0_52"]),
                      "evidence_status": r["evidence_status"]} for r in led["rows"]],
            "totals_moved_by_code": run["totals_moved_by_code"], "drawings": DRAWINGS}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--previous")
    a = ap.parse_args(argv)
    doc = build(a.run)
    if a.previous:
        old = json.loads(Path(a.previous).read_text(encoding="utf-8"))
        for k in ("rows", "totals_moved_by_code"):
            if doc[k] != old[k]:
                raise SystemExit(f"{k} differ from the previous summary")
        if doc["identity"]["wet_area_wp"] != old["identity"]["wet_area_wp"]:
            raise SystemExit("wet_area_wp identity differs from the previous summary")
        print("rows, totals moved by code and wet_area_wp identity equal the previous summary")
    Path(a.out).write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(doc["base_candidate"], "->", doc["new_candidate"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
