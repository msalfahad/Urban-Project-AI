"""ALSENAN V3 - benchmark evaluation AFTER the V3a freeze (EVALUATION ONLY), units normalised first.

Reads the frozen V3a MASTER_MATRIX and FINAL_FREEZE, and the frozen B1 benchmark register (cover totals of the
freelancer workbooks, already normalised in an earlier round). Nothing here feeds back into any quantity: the
comparison is written beside the freeze and the freeze digest is recorded to prove the order (freeze first).

UNIT CONTROL: both sides are put in the final-BOQ display unit before any difference is taken (engine kg -> t, م2 -> m²,
م.ط -> lm, ...). A pair whose units still differ is reported UNIT_MISMATCH with no difference; a benchmark row whose
unit cell is blank takes the unit of its trade convention and says so.

    python3 research/external_engine_lab/alsenan_v3_evaluation.py <v3_register_dir> <out_json>
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.reporting_v3 import units as U                                    # noqa: E402

B1 = ROOT / "tests/alsenan/registers_b1/BENCHMARK_NORMALISED.json"
# (benchmark trade, subtrade) -> (V3 trade, summary item, engine unit, comparability note)
MAP = [
    (("FLOOR", "ALL"), ("FLOORING_PORCELAIN", "Floor finish", "m2"), "internal floors; V3 includes open-plan zones, no yard"),
    (("SKIRTING", "ALL"), ("FLOORING_PORCELAIN", "Skirting", "lm"), "dry rooms only in V3"),
    (("WALL_TILE", "WET_ROOMS"), ("WALL_TILE_WATERPROOFING", "Wall tile", "m2"), "V3 gross of openings, full height"),
    (("WATERPROOFING", "WET_ROOM:FLOOR"), ("WALL_TILE_WATERPROOFING", "Wet-room waterproofing", "m2"),
     "V3 = floor + upturn area (benchmark lists the upturn separately in lm)"),
    (("WATERPROOFING", "ROOF:FLOOR"), ("WALL_TILE_WATERPROOFING", "Roof waterproofing", "m2"),
     "V3 = flat + 0.20 upturn area (benchmark lists the upturn separately in lm)"),
    (("RAILING", "INTERNAL"), ("STAIRS_RAILINGS", "Gallery railing", "lm"), "V3 void edge only; stair railing blocked"),
    (("BLOCKWORK", "ALL"), (None, None, "m2"), "V3 net of openings at full height; split by thickness rows"),
    (("PAINT", "INTERNAL_WALL"), ("PLASTER_PAINT", "Internal paint", "m2"), "V3 partial (zones with unbound beams blocked)"),
    (("PLASTER", "INTERNAL_WALL"), ("PLASTER_PAINT", "Internal plaster", "m2"), "V3 to masonry termination, gross of openings"),
    (("BLINDING", "PLAIN"), ("CONCRETE", "Plain concrete (blinding)", "m3"), "V3 under footings + interior ground beams"),
    (("OTHER_CONCRETE", "ALL_REINFORCED"), ("CONCRETE", "Reinforced concrete", "m3"),
     "V3 excludes blocked necks, exterior GB, stairs, pool"),
    (("REBAR", "ALL"), ("REBAR", "Procurement weight incl. laps (complete sets)", "kg"),
     "V3 official basis = procurement of the COMPLETE bar sets only; partial sets (straight bar awaiting hook detail) "
     "and slab bars are not in this figure"),
]
TRADE_UNIT = {"PAINT": "m²", "PLASTER": "m²", "BLOCKWORK": "m²", "FLOOR": "m²", "WALL_TILE": "m²", "CEILING": "m²"}


def _bench_unit(rec):
    u = (rec.get("unit") or "").strip()
    if u:
        return U.BENCH_UNIT.get(u, u), "STATED"
    return TRADE_UNIT.get(rec["trade"]), "INFERRED_FROM_TRADE (B1 unit cell blank)"


def evaluate(regdir) -> dict:
    regdir = Path(regdir)
    master = json.loads((regdir / "MASTER_MATRIX.json").read_text())
    freeze = (regdir / "FINAL_FREEZE.json").read_bytes()
    bench = json.loads(B1.read_text())
    cover = {(r["trade"], r["subtrade"]): r for r in bench["records"] if r["row_kind"] == "COVER_TOTAL"}
    rows = []
    for (bt, bs), (vt, vi, eu), note in MAP:
        b = cover.get((bt, bs))
        du, f = U.UNIT_POLICY[eu][0], U.UNIT_POLICY[eu][1]
        if vt is None:
            v = sum(r["total"] for r in master["rows"] if r["trade"] == "BLOCKWORK" and r["unit"] == eu)
            vstat = "PARTIAL"
        else:
            m = next((r for r in master["rows"] if r["trade"] == vt and r["item"] == vi and r["unit"] == eu), None)
            v, vstat = (m["total"], m["status"]) if m else (None, "MISSING")
        vd = None if v is None else v * f
        bq = b["qty"] if b else None
        bu, bsrc = _bench_unit(b) if b else (None, None)
        same = bu == du
        rows.append({"benchmark": f"{bt} / {bs}", "benchmark_label": b.get("label_en") if b else None,
                     "benchmark_qty": bq, "benchmark_unit_raw": b.get("unit") if b else None,
                     "benchmark_unit_normalised": bu, "benchmark_unit_source": bsrc,
                     "v3_item": f"{vt} / {vi}" if vt else "BLOCKWORK (all thickness rows)",
                     "v3_engine_qty": v, "v3_engine_unit": eu, "v3_qty": vd, "v3_display_unit": du,
                     "units_normalised": True, "v3_status": vstat,
                     "difference_pct": round(100.0 * (vd - bq) / bq, 1) if (same and vd is not None and bq) else None,
                     "unit_check": "SAME_UNIT" if same else "UNIT_MISMATCH", "comparability": note})
    return {"SCHEMA": "URBAN_ALSENAN_V3_BENCHMARK_EVALUATION_V2", "run": "AFTER_FREEZE", "evaluation_only": True,
            "unit_policy": U.POLICY_ID,
            "v3_freeze_sha256": hashlib.sha256(freeze).hexdigest(), "b1_register_sha256": hashlib.sha256(B1.read_bytes()).hexdigest(),
            "rows": rows,
            "rule": "units normalised before comparison (engine kg -> t, Arabic unit labels -> m² / lm); no benchmark value "
                    "chose or changed any V3 quantity (OD-V3-10); differences are findings, not targets"}


if __name__ == "__main__":
    rec = evaluate(sys.argv[1])
    Path(sys.argv[2]).write_text(json.dumps(rec, indent=1, ensure_ascii=False) + "\n")
    for r in rec["rows"]:
        print(r["benchmark"], r["benchmark_qty"], r["benchmark_unit_normalised"], "|", r["v3_item"], r["v3_qty"],
              r["v3_display_unit"], r["v3_status"], r["difference_pct"], r["unit_check"])
