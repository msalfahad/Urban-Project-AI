"""T-482: the three blockwork wiring conditions applied to the training villa (DEVELOPMENT-VILLA-T131).

Inputs are only Checker-merged research files (no client file is read): the T-449 round 3 register builder
(research/agents_t449/round3, pinned ledgers), T-215 junction ends (T215_ENDS.csv) and the T-449 parapet entries.
Drawing readings of this run (Drive 'Alsenan chalet project', read in the private folder, cited by handle only) are
recorded as constants with their source; nothing from a drawing file is copied.

    python3 -I research/agents_t482/t482_alsenan.py [out_dir]
"""

from __future__ import annotations

import csv
import io
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in (ROOT, HERE, ROOT / "research/agents_t449/round3"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import blockwork_conditions_v1 as C  # noqa: E402
import t449_blockwork_register as T  # noqa: E402
from engine.source import blockwork_basis_rules_v1 as R  # noqa: E402

T215 = ROOT / "research/agents_t215/T215_ENDS.csv"
F2 = "STOREY_HEIGHT.2F.MAIN"

# ---- plates (merged readings + this run's own read of ST7757 dxf.dxf / ST7757.pdf p.6 and p.14) -----------------
PLATES = {
    "GROUND": C.Plate("GROUND", (C.Zone("GF-MAIN", C.FLOOR, 1.00, 0.05, "T-214 A-A / B-B drawn 0.05"),),
                      "slab on grade, T-214"),
    "GFRS": C.Plate("GFRS", (C.Zone("1F-FLOOR", C.FLOOR, 5.50, 0.05, "T-214 A-A +5.50"),
                             C.Zone("GF-TERRACES", C.ROOF, 5.50, None, "arch plans +5.50 finished roof")),
                    "ST p.4 GROUND FLOOR ROOF SLAB: one 0.16 plate (T-248 / T-220, merged 579e613d)"),
    "FFRS": C.Plate("FFRS", (C.Zone("2F-FLOOR", C.FLOOR, 9.70, 0.05, "T-214 A-A +9.70"),
                             C.Zone("1F-ROOF-TERRACE", C.ROOF, 9.70, None,
                                    "ST dxf LEVEL texts 3F4 / 3F6 '+9.70' on the terrace (T-200)")),
                    "ST p.5 FIRST FLOOR ROOF SLAB: one plate (T-248 / T-220)"),
    "SFRS": C.Plate("SFRS", (C.Zone("MAIN-ROOF", C.ROOF, 13.90, None, "arch sheet10 A-A '+13.90' (finished roof)"),),
                    "ST p.6 SECOND FLOOR ROOF SLAB (block SFRS, insert A8): beams B1 B2 B3 B7 B8 B15, tank T&B "
                    "'T 18'; NO level printed on the plate (the two '+9.70' marks 3F4 / 3F6 and 'ROOF' 3AE sit on "
                    "the 1F-roof terrace outside it); this run, own read"),
    "ANNEX-ROOF": C.Plate("ANNEX-ROOF", (C.Zone("ANNEX-ROOF", C.ROOF, 4.30, None, "arch B-B '+4.30'"),),
                          "annex roof, only the finished +4.30 printed (Q-54 B)"),
}
ROOF_BOUND_NOTE = ("ST p.14 'TYPICAL DETAIL OF PARAPET SECTION' (P1): RC upstand '30' above the slab, note 'MUST BE MORE "
                   "THAN THE HEIGHT OF ROOF FINISHING' -> b_r < 0.30 at a P1 edge; NOT applied: P1 is not keyed to "
                   "the main roof and the point where +13.90 is read (falls) is not printed")
STOREYS = (("GF", "GROUND", "GFRS", 4.50), ("1F", "GFRS", "FFRS", 4.20), ("2F", "FFRS", "SFRS", 4.20))


def datums():
    d = {k: C.plate_top(p, ROOF_BOUND_NOTE if k == "SFRS" else None) for k, p in PLATES.items()}
    basis = []
    for fl, b, t, declared in STOREYS:
        s, upper = C.structural_storey(d[b], d[t])
        try:
            C.refuse_finished_chain(declared, d[b], d[t])
            verdict = "STRUCTURAL (declared storey = plate top - plate top)"
        except C.ConditionError as ex:
            verdict = str(ex).split(":")[0]
        basis.append({"floor": fl, "base_plate": b, "top_plate": t, "declared_storey_m": declared,
                      "structural_storey_m": s, "upper_storey_m": upper, "verdict": verdict,
                      "base_top_m": d[b].top_m, "top_top_m": d[t].top_m, "top_upper_m": d[t].upper_m})
    return d, basis


# ---- finding (1): 2F walls under the roof-only plate -----------------------------------------------------------------
def roof_walls(d):
    cfg = T.load_cfg()
    src = T.sources()
    fill = {r["wall_id"]: r for r in T._rows(T.FILL) if r["wall_id"].startswith("2F-") and r["item_code"] == "MAS.BLOCK"}
    captured = {}
    real = R.wall_net

    def spy(cfg_, wall_id, storey_fact, pieces, openings=(), door_fallback_fact=None, held_notes=()):
        captured[wall_id] = (storey_fact, tuple(pieces), tuple(openings), door_fallback_fact, tuple(held_notes))
        return real(cfg_, wall_id, storey_fact, pieces, openings, door_fallback_fact, held_notes)

    R.wall_net = spy
    try:
        carried = {}
        for w, row in sorted(fill.items()):
            res, geo, notes, bad = T.wall_rule(cfg, w, row, src)
            carried[w] = (row, res, geo)
    finally:
        R.wall_net = real
    out = []
    for w, (row, res41, geo) in sorted(carried.items()):
        sf, pcs, ops, dff, hn = captured[w]
        if sf != F2:
            raise RuntimeError(f"{w}: storey fact {sf}")
        rw = C.wall_under_roof(cfg, w, sf, d["FFRS"], d["SFRS"], pcs, ops, dff, hn, what_if_storey_m=4.20)
        car = float(row["carried"]) if row.get("carried") not in (None, "") else None
        out.append({"wall_id": w, "line_id": row["line_id"], "geometry": geo, "carried_status": row["status"],
                    "carried_m2": car, "v1_state_at_4.20": res41.state, "v1_value_at_4.20": res41.value,
                    "t482_state": rw.state, "upper_m2_at_b0": rw.upper_m2, "datum_length_m": rw.datum_length_m,
                    "part": rw.part, "what_if_b_0.05_m2": rw.v1_at_storey,
                    "check_U_minus_L_x_0.05": None if rw.upper_m2 is None else round(rw.upper_m2 - 0.05 * rw.datum_length_m, 6),
                    "formula": rw.formula, "held": list(rw.held)})
    return out


# ---- finding (2): GF-W22 / GF-W34 CB2 width conflict ----------------------------------------------------------------
def width_conflicts():
    ends = {r["row_id"]: r for r in csv.DictReader(io.StringIO(T215.read_text(encoding="utf-8")))}
    reg = T.build()
    by = {e["element_id"]: e for e in reg["entries"] if e.get("item_code") == "MAS.BLOCK"}
    out = []
    w22 = by["GF-W22"]
    car = w22["patch"]["carried"]
    lo, hi = float(ends["GF-W22"]["d_gross_m2_lo"]), float(ends["GF-W22"]["d_gross_m2_hi"])
    base = round(car - lo, 4)                      # the T-108 run before the junction close (carried = base + lo)
    readings = {"CB2 drawn 0.25 (handles 278 / 274)": round(base + lo, 4),
                "CB2 schedule 0.20 on the drawn outer face": round(base + hi, 4)}
    try:
        C.width_conflict("GF-W22", "D-27 (CB2 BM-GF-055)", readings, car, w22["patch"]["status"])
        refused = None
    except C.ConditionError as ex:
        refused = str(ex)
    rng = C.width_conflict("GF-W22", "D-27 (CB2 BM-GF-055)", readings)
    out.append({"element_id": "GF-W22", "line_id": w22["line_id"], "carried_m2": car,
                "carried_status": w22["patch"]["status"], "carried_refused": refused,
                "range_m2": [rng.low, rng.high], "low_reading": rng.low_reading, "high_reading": rng.high_reading,
                "width_m2": round(rng.high - rng.low, 4), "v1_rule_no_cb2_m2": w22["rule_result"]["value"],
                "v1_vs_high_m2": round(w22["rule_result"]["value"] - rng.high, 5),
                "panel_volume": "ARCH.WALL_PANEL follows the range; ARCH.WALL_VOLUME = range x 0.15 = "
                                f"[{round(rng.low * 0.15, 6)}, {round(rng.high * 0.15, 6)}] m3",
                "status_proposed": "CONFLICT (BOUNDED), D-27; never DRAWING-CONFIRMED at one end"})
    w34 = by["GF-W34"]
    U0 = w34["patch"]["upper_at_d0"]
    lo, hi = float(ends["GF-W34"]["d_gross_m2_lo"]), float(ends["GF-W34"]["d_gross_m2_hi"])
    U, k = C.drop_upper_over_readings("GF-W34", {"CB2 drawn 0.25": U0, "CB2 schedule 0.20": round(U0 - lo + hi, 4)})
    out.append({"element_id": "GF-W34", "line_id": w34["line_id"], "carried_U_m2": U0, "U_m2": U, "U_reading": k,
                "U_change_m2": round(U - U0, 4), "drop_length_carried_m": w34["patch"]["drop_length_m"],
                "drop_length_rule_m": w34["rule_result"]["drop_length_m"],
                "status_proposed": "HELD ON DROP, U = the max over the D-27 readings; the d-coefficient L stays "
                                   "open (1.7231 carried vs 1.7827 rule: T-288 re-clip, not this conflict)"})
    return out


# ---- finding (3) + (4): parapet block alternatives ------------------------------------------------------------------
def parapets():
    cfg = T.load_cfg()
    reg = T.build()
    by = {e["element_id"]: e for e in reg["entries"] if "PARAPET" in str(e.get("element_id"))}
    out = []
    e = by["1F_ROOF#PARAPET_RC:NW-2"]
    old = e["patch"]["block_alt_m2"][1]
    h = e["h_hi_m"]
    try:
        C.parapet_alternative(cfg, C.ParapetRun("NW-2", 3.6107, h, "FLOOR_OUTLINE"), T.F_UPSTAND)
        refused = None
    except C.ConditionError as ex:
        refused = str(ex)
    res, delta = C.parapet_alternative(cfg, C.ParapetRun("NW-2", e["centreline_hi_m"], h, "ROOF_LEVEL"), T.F_UPSTAND,
                                       previous_centreline_m=3.6107)
    out.append({"element_id": e["element_id"], "line_id": e["line_id"], "carried_m2": e["patch"]["block_alt_m2"],
                "carried_centreline_m": 3.6107, "carried_source": "T-311 1F floor-outline bay arc (superseded)",
                "carried_refused": refused, "range_m2": [res.low, res.high], "centreline_m": e["centreline_hi_m"],
                "height_m": h, "delta_hi_m2": delta, "delta_check": round(res.high - old, 6),
                "evidence": "P7757.dxf (ab54dd55) roof plan: inner face 12A7 LINE 11.600 m straight; 0.20 wall line "
                            "12A5 5.6871 + 131C 1.0052 + 131B 4.8077 m, all straight (own read this run) = T-324 C3"})
    e = by["ANNEX_ROOF#PARAPET_RC:NE-6x"]
    res, _ = C.parapet_alternative(cfg, C.ParapetRun("NE-6x", e["centreline_hi_m"], e["h_hi_m"], "ROOF_LEVEL"),
                                   T.F_UPSTAND)
    out.append({"element_id": e["element_id"], "line_id": e["line_id"], "carried_m2": None,
                "range_m2": [res.low, res.high], "centreline_m": e["centreline_hi_m"], "height_m": e["h_hi_m"],
                "evidence": "T-324 C5 new run (B34 11.800 vs B3A -> CEC), merged; no block alternative booked"})
    return out


def build():
    d, basis = datums()
    walls = roof_walls(d)
    vals = [w for w in walls if w["t482_state"] == C.ROOF_DATUM]
    summ = {
        "valued_carried_m2": round(math.fsum(w["carried_m2"] for w in vals if not w["part"]), 4),
        "valued_upper_m2": round(math.fsum(w["upper_m2_at_b0"] for w in vals if not w["part"]), 4),
        "valued_L_m": round(math.fsum(w["datum_length_m"] for w in vals if not w["part"]), 4),
        "part_carried_m2": round(math.fsum(w["carried_m2"] for w in vals if w["part"]), 4),
        "part_upper_m2": round(math.fsum(w["upper_m2_at_b0"] for w in vals if w["part"]), 4),
        "part_L_m": round(math.fsum(w["datum_length_m"] for w in vals if w["part"]), 4),
        "walls": len(walls), "roof_datum": len(vals), "held_whole": len(walls) - len(vals)}
    return {"schema": "T482_BLOCKWORK_CONDITIONS_V1", "rule_version": C.RULE_VERSION,
            "datums": {k: {"state": v.state, "top_m": v.top_m, "upper_m": v.upper_m, "basis": v.basis,
                           "held": list(v.held), "beside": list(v.beside), "source": PLATES[k].source}
                       for k, v in d.items()},
            "storey_basis": basis, "roof_walls_2F": walls, "roof_walls_summary": summ,
            "width_conflicts": width_conflicts(), "parapets": parapets()}


if __name__ == "__main__":
    out_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    reg = build()
    (out_dir / "T482_CONDITIONS.json").write_text(json.dumps(reg, indent=1, ensure_ascii=False) + "\n",
                                                  encoding="utf-8")
    print(json.dumps(reg["roof_walls_summary"]))
