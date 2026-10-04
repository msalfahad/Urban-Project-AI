"""ALSENAN V3b - benchmark evaluation AFTER the V3b freeze (EVALUATION ONLY) + MISMATCH_REGISTER.

Reads the frozen V3b MASTER_MATRIX_V3B and FINAL_FREEZE_V3B, and the frozen B1 benchmark register (cover totals of the
freelancer workbooks, normalised in an earlier round). Units are normalised first (engine kg -> t). Each comparison
beyond TOL becomes a MISMATCH_CASE whose classification is the cause PRE-DECLARED in MAP (written before the numbers
were read; a candidate, not a proof) with the evidence of each side and what to inspect next. Nothing here feeds
back into any quantity; the freeze digest is recorded to prove the order.

    python3 research/external_engine_lab/alsenan_v3b_evaluation.py <v3b_register_dir> <out_dir>
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
TOL = 0.10
# (benchmark trade, subtrade) -> [(V3b trade, summary item, engine unit)], pre-declared cause, what to inspect next
MAP = [
    (("FLOOR", "ALL"), [("FLOORING", "Floor finish", "m2")], "SCOPE",
     "yard / external paving and stair finish are separate V3b items; compare room lists"),
    (("SKIRTING", "ALL"), [("FLOORING", "Skirting", "lm")], "SCOPE", "wet rooms carry no skirting in V3b (full tile)"),
    (("WALL_TILE", "WET_ROOMS"), [("WALL_TILE_WATERPROOFING", "Wall tile (net)", "m2")], "OPENING DEDUCTION",
     "V3b is NET of openings + reveals; check the benchmark tile height and deduction rule"),
    (("WATERPROOFING", "WET_ROOM:FLOOR"), [("WALL_TILE_WATERPROOFING", "WP floor", "m2")], "SCOPE",
     "V3b floor m2 only (upturn split into lm); check the benchmark room list"),
    (("WATERPROOFING", "ROOF:FLOOR"), [("WALL_TILE_WATERPROOFING", "Roof waterproofing", "m2")], "HEIGHT",
     "V3b includes a 0.20 upturn area; benchmark lists the upturn separately in lm"),
    (("RAILING", "INTERNAL"), [("STAIRS_RAILINGS", "Gallery railing", "lm")], "MISSING POPULATION",
     "stair handrail is in a separate provisional V3b line (S-RAIL)"),
    (("BLOCKWORK", "ALL"), [("BLOCKWORK", "Blockwork 200 mm", "m2"), ("BLOCKWORK", "Blockwork 150 mm", "m2"),
                            ("BLOCKWORK", "Blockwork OVER OPENINGS", "m2"), ("BLOCKWORK", "Parapet blockwork", "m2")],
     "OPENING DEDUCTION", "V3b measures wall pieces between openings + over / below openings; boundary wall separate"),
    (("PAINT", "INTERNAL_WALL"), [("PLASTER_PAINT", "Internal paint (net)", "m2")], "HEIGHT",
     "paint height (build-up fallback 0.10) and the soffit under unbound beams"),
    (("PLASTER", "INTERNAL_WALL"), [("PLASTER_PAINT", "Rough plaster", "m2")], "PAYABLE vs TECHNICAL",
     "V3b dry rooms only (wet faces = spatter + tile prep, OD-V3B-4), NET of openings; plaster to the soffit"),
    (("BLINDING", "PLAIN"), [("CONCRETE", "Plain concrete (blinding)", "m3")], "SCOPE",
     "V3b = owner full-footprint method (OD-V3B-1); local detail alternative published"),
    (("OTHER_CONCRETE", "ALL_REINFORCED"), [("CONCRETE", "Reinforced concrete", "m3")], "MISSING POPULATION",
     "residue / provisional items (necks, exterior GB, stairs) are commercial only"),
    (("REBAR", "ALL"), [("REBAR", "Rebar - net design weight (straight + hooks)", "kg")], "PROCUREMENT vs NET",
     "V3b NET excludes laps and waste; compare with R-BBS purchased; check the benchmark kg/m3 basis"),
]
TRADE_UNIT = {"PAINT": "m²", "PLASTER": "m²", "BLOCKWORK": "m²", "FLOOR": "m²", "WALL_TILE": "m²", "CEILING": "m²"}


def _bench_unit(rec):
    u = (rec.get("unit") or "").strip()
    if u:
        return U.BENCH_UNIT.get(u, u), "STATED"
    return TRADE_UNIT.get(rec["trade"]), "INFERRED_FROM_TRADE (B1 unit cell blank)"


def evaluate(regdir) -> dict:
    regdir = Path(regdir)
    master = json.loads((regdir / "MASTER_MATRIX_V3B.json").read_text())
    freeze = (regdir / "FINAL_FREEZE_V3B.json").read_bytes()
    bench = json.loads(B1.read_text())
    cover = {(r["trade"], r["subtrade"]): r for r in bench["records"] if r["row_kind"] == "COVER_TOTAL"}
    rows, cases = [], []
    for (bt, bs), items, cause, nxt in MAP:
        b = cover.get((bt, bs))
        tech = com = 0.0
        found = []
        eu = items[0][2]
        for vt, vi, u in items:
            m = next((r for r in master["rows"] if r["trade"] == vt and r["item"] == vi and r["unit"] == u), None)
            if m:
                tech += m["technical"]["total"]
                com += m["commercial"]["total"]
                found.append(vi)
        du, f = U.UNIT_POLICY[eu][0], U.UNIT_POLICY[eu][1]
        bq = b["qty"] if b else None
        bu, bsrc = _bench_unit(b) if b else (None, None)
        same = bu == du
        t, c = tech * f, com * f
        dt = round(100.0 * (t - bq) / bq, 1) if (same and bq) else None
        dc = round(100.0 * (c - bq) / bq, 1) if (same and bq) else None
        row = {"benchmark": f"{bt} / {bs}", "benchmark_qty": bq, "benchmark_unit": bu, "benchmark_unit_source": bsrc,
               "v3b_items": found, "v3b_technical": round(t, 3), "v3b_commercial": round(c, 3), "unit": du,
               "diff_technical_pct": dt, "diff_commercial_pct": dc, "unit_check": "SAME_UNIT" if same else "UNIT_MISMATCH"}
        rows.append(row)
        if dc is not None and abs(dc) > 100 * TOL or not same:
            cases.append({"case": f"MM-{len(cases) + 1:02d}", "benchmark": row["benchmark"],
                          "classification": "UNIT" if not same else cause,
                          "classification_basis": "pre-declared candidate cause (written before the comparison), "
                                                  "not proven", "urban_evidence": f"{found} technical {t:.3f} / "
                                                                                  f"commercial {c:.3f} {du}",
                          "benchmark_evidence": f"cover total {bq} {bu} ({bsrc})", "diff_commercial_pct": dc,
                          "inspect_next": nxt, "against": "FREELANCER (B1 cover totals)"})
    return {"evaluation": {"SCHEMA": "URBAN_ALSENAN_V3B_BENCHMARK_EVALUATION_V1", "run": "AFTER_FREEZE",
                           "evaluation_only": True, "unit_policy": U.POLICY_ID,
                           "v3b_freeze_sha256": hashlib.sha256(freeze).hexdigest(),
                           "b1_register_sha256": hashlib.sha256(B1.read_bytes()).hexdigest(), "rows": rows,
                           "rule": "units normalised first; no benchmark value chose or changed any V3b quantity; "
                                   "differences are findings, never targets (44.19 t is not a target)"},
            "mismatch": {"SCHEMA": "URBAN_ALSENAN_V3B_MISMATCH_REGISTER_V1", "tolerance": TOL, "cases": cases,
                         "rule": "one MISMATCH_CASE per comparison beyond tolerance; classification = pre-declared "
                                 "candidate (SCOPE / UNIT / MATERIAL / REVISION / GEOMETRY / OPENING DEDUCTION / HEIGHT / "
                                 "MISSING POPULATION / PROCUREMENT vs NET / PAYABLE vs TECHNICAL / BENCHMARK ERROR / "
                                 "URBAN ENGINE ERROR / UNRESOLVED)"}}


if __name__ == "__main__":
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    rec = evaluate(sys.argv[1])
    (out / "BENCHMARK_EVALUATION_V3B.json").write_text(json.dumps(rec["evaluation"], indent=1, ensure_ascii=False) + "\n")
    (out / "MISMATCH_REGISTER.json").write_text(json.dumps(rec["mismatch"], indent=1, ensure_ascii=False) + "\n")
    for r in rec["evaluation"]["rows"]:
        print(r["benchmark"], r["benchmark_qty"], r["benchmark_unit"], "|", r["v3b_technical"], r["v3b_commercial"], r["unit"],
              r["diff_technical_pct"], r["diff_commercial_pct"], r["unit_check"])
