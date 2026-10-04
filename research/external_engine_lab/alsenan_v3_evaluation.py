"""ALSENAN V3 - benchmark evaluation AFTER the V3a freeze (EVALUATION ONLY).

Reads the frozen V3a MASTER_MATRIX and FINAL_FREEZE, and the frozen B1 benchmark register (cover totals of the
freelancer workbooks, already normalised in an earlier round). Nothing here feeds back into any quantity: the
comparison is written beside the freeze and the freeze digest is recorded to prove the order (freeze first).

    python3 research/external_engine_lab/alsenan_v3_evaluation.py <v3_register_dir> <out_json>
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
B1 = ROOT / "tests/alsenan/registers_b1/BENCHMARK_NORMALISED.json"
# (benchmark trade, subtrade) -> (V3 trade, summary item, comparability note)
MAP = [
    (("FLOOR", "ALL"), ("FLOORING_PORCELAIN", "Floor finish"), "internal floors; V3 includes open-plan zones, no yard"),
    (("SKIRTING", "ALL"), ("FLOORING_PORCELAIN", "Skirting"), "dry rooms only in V3"),
    (("WALL_TILE", "WET_ROOMS"), ("WALL_TILE_WATERPROOFING", "Wall tile"), "V3 gross of openings, full height"),
    (("WATERPROOFING", "WET_ROOM:FLOOR"), ("WALL_TILE_WATERPROOFING", "Wet-room waterproofing"), "V3 = floor + upturn"),
    (("WATERPROOFING", "ROOF:FLOOR"), ("WALL_TILE_WATERPROOFING", "Roof waterproofing"), "V3 = flat + 0.20 upturn"),
    (("RAILING", "INTERNAL"), ("STAIRS_RAILINGS", "Gallery railing"), "V3 void edge only; stair railing blocked"),
    (("BLOCKWORK", "ALL"), (None, None), "V3 net of openings at full height; split by thickness rows"),
    (("PAINT", "INTERNAL_WALL"), ("PLASTER_PAINT", "Internal paint"), "V3 partial (zones with unbound beams blocked)"),
    (("PLASTER", "INTERNAL_WALL"), ("PLASTER_PAINT", "Internal plaster"), "V3 to masonry termination, gross of openings"),
    (("BLINDING", "PLAIN"), ("CONCRETE", "Plain concrete (blinding)"), "V3 under footings + interior ground beams"),
    (("OTHER_CONCRETE", "ALL_REINFORCED"), ("CONCRETE", "Reinforced concrete"), "V3 excludes blocked necks, exterior GB, stairs, pool"),
]


def evaluate(regdir) -> dict:
    regdir = Path(regdir)
    master = json.loads((regdir / "MASTER_MATRIX.json").read_text())
    freeze = (regdir / "FINAL_FREEZE.json").read_bytes()
    bench = json.loads(B1.read_text())
    cover = {(r["trade"], r["subtrade"]): r for r in bench["records"] if r["row_kind"] == "COVER_TOTAL"}
    rows = []
    for (bt, bs), (vt, vi), note in MAP:
        b = cover.get((bt, bs))
        if vt is None:
            v = sum(r["total"] for r in master["rows"] if r["trade"] == "BLOCKWORK" and r["unit"] == "m2")
            vstat = "PARTIAL"
        else:
            m = next((r for r in master["rows"] if r["trade"] == vt and r["item"] == vi), None)
            v, vstat = (m["total"], m["status"]) if m else (None, "MISSING")
        bq = b["qty"] if b else None
        rows.append({"benchmark": f"{bt} / {bs}", "benchmark_label": b.get("label_en") if b else None, "benchmark_qty": bq,
                     "v3_item": f"{vt} / {vi}" if vt else "BLOCKWORK (all thickness rows)", "v3_qty": v, "v3_status": vstat,
                     "difference_pct": round(100.0 * (v - bq) / bq, 1) if (v is not None and bq) else None,
                     "comparability": note})
    return {"SCHEMA": "URBAN_ALSENAN_V3_BENCHMARK_EVALUATION_V1", "run": "AFTER_FREEZE", "evaluation_only": True,
            "v3_freeze_sha256": hashlib.sha256(freeze).hexdigest(), "b1_register_sha256": hashlib.sha256(B1.read_bytes()).hexdigest(),
            "rows": rows,
            "rule": "no benchmark value chose or changed any V3 quantity (OD-V3-10); differences are findings, not targets"}


if __name__ == "__main__":
    rec = evaluate(sys.argv[1])
    Path(sys.argv[2]).write_text(json.dumps(rec, indent=1, ensure_ascii=False) + "\n")
    for r in rec["rows"]:
        print(r["benchmark"], r["benchmark_qty"], "|", r["v3_item"], r["v3_qty"], r["v3_status"], r["difference_pct"])
