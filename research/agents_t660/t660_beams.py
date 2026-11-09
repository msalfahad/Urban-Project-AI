"""T-660 per-beam ledger: the 27 HELD B10-07 STR.CONC.BEAM lines of the 10 Nov trial BOQ r4 (T-654) restated member by
member from the structural drawings (R-T660-1 .. 6). Research only: nothing wired, nothing released.

Committed inputs (no drawing is opened here; each printed fact is cited with its DXF handle / sheet):
  trial r4 lines  research/agents_t654/out/TRIAL_BOQ_R4_T654.json (per_line, item STR.CONC.BEAM, class HELD)
  T-402 r2 rows   research/agents_t402/HELD_LINES_T402.csv (edge handles, drawn widths, face-to-face lengths, plan
                  areas, slab pairing; merged 1b4c18fc, Checker Gate A PASS)
Printed facts re-read by T-660 this run (ST7757 DXF + PDF, Drive 'Alsenan chalet project', read-only, private copy):
  plan edges (layer 1): B29 463 / 2CE 0.200; CB2 274 / 278 0.250; B21 433 / 434 0.400 (inclined); B6 span 5CC / 5CD
    0.200; CB10 5E7 / 5E8 0.300 (outer strip edge 5E5 0.20 further out); GF piece past column 335: 274 / 277 0.500,
    column 335 x 71.4634 .. 71.9634, end line 2A8 x 73.4634 -> 1.500 m; strips: GF 2C6 / 2C7 0.20 outside B20 458 / 2C6
    0.40; 1F 5E1 / 5E6 0.20 outside B23 5E4 / 5E1 0.45; upstand lines 55F / 7BC 0.20 inside the beams' outer faces.
  sections (DIMLFAC 0.025): A-A 59A '40' 5A8 '75', upstand 58C / 561 '20' + 572 '20' (B20 only, outline ends at its
    outer face); B-B 16EA '45' 16F8 '75', 16C0 '25' + 16DC '20', 16CE '20' (B23 only, same); D-D 1785 '55' + 1777 '20'
    = 0.75, round 1777 '20' (V) + 17A3 '20' (H); width not dimensioned.
  simple-beam schedule (ST p.10, block text): breadth 0.20 rows have depths 0.40 (B1-B3), 0.50 (B4, B5), 0.60 (B.W),
    0.75 (B7-B11, B14), 1.20 (B15); B20 40x75 11T18 / 11T18; B23 45x75 11T18 / 11T18 (= sections A-A / B-B).
  CB3 (p.11 three-span schedule) printed spans 3.4 / 3.3 / 3.8; drawn supports: carrier edges 1 x 60.593 / 61.093,
    columns 37F 64.113-64.913, 373 67.563-68.163, 385 71.463-71.963 -> c/c 3.670 / 3.350 / 3.850.
  roof-slab plans GF / 1F / 2F: note 'CHECK ARCHITECTURAL DETAIL OF PARAPET, BEFORE CASTING' (layer S-TITLE TEXT).

    python3 -I research/agents_t660/t660_beams.py [--write]
"""
from __future__ import annotations

import csv
import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
RES = HERE.parent
sys.path.insert(0, str(HERE))
import t660_rules as R  # noqa: E402

R4 = RES / "agents_t654" / "out" / "TRIAL_BOQ_R4_T654.json"
T402 = RES / "agents_t402" / "HELD_LINES_T402.csv"
OUT = HERE / "out" / "T660_BEAM_LEDGER.json"
D = Decimal

SCHEDULE_W020 = [("0.20", d) for d in ("0.40", "0.50", "0.60", "0.75", "1.20")]   # ST p.10 rows of breadth 0.20
GF059 = {"line_id": "L-8ea71184fff91b4357b7", "width": "0.500", "chain": ("0.55", "0.20"), "length": "1.500",
         "round": ("0.20", "0.20"),
         "basis": "section D-D (cut 181D crosses the piece) prints 1785 '55' + 1777 '20' = 0.75 closing the outline, "
                  "round 1777 / 17A3 '20' x '20'; width from plan edges 274 / 277 = 0.500 (D-D width undimensioned); "
                  "length column 335 east face x 71.9634 .. end line 2A8 x 73.4634 = 1.500 (R-T660-1)"}
CB3_SPANS = {"printed": ("3.4", "3.3", "3.8"), "drawn_cc": ("3.670", "3.350", "3.850")}
COMPANION = "NEW:STR.CONC.BEAM:U-C:BEAMS:GF:BAND0030.2~T642_DEPTH_B4_B7"
PARAPET_NOTE = ("roof-slab plans GF / 1F / 2F: 'CHECK ARCHITECTURAL DETAIL OF PARAPET, BEFORE CASTING'; candidate "
                "PARAPET_FOOTPRINT reading beside the parapet family (T-311 / T-659): value in ONE family only")
SECTION_CROSS = {"L-634cefe5e8a7fb458e16": "A-A (cut 55A) crosses it; outline 0.40 ends at B20's outer face 2C6",
                 "L-67f3d325019e618328eb": "B-B (cut 76E) crosses it; outline 0.45 ends at B23's outer face 5E1"}


def _r4():
    d = json.loads(R4.read_text(encoding="utf-8"))
    return {x["line_id"]: x for x in d["per_line"]
            if x.get("item_code") == "STR.CONC.BEAM" and x.get("class") == "HELD"}


def _t402():
    with T402.open(encoding="utf-8") as f:
        return {r["line_id"]: r for r in csv.DictReader(f)}


def _q(x):
    return None if x is None else str(D(str(x)).quantize(R.Q6))


def ledger():
    r4, t402 = _r4(), _t402()
    assert len(r4) == 27, len(r4)
    rows = []
    for lid in sorted(r4):
        t = r4[lid]
        before = {"low": _q(t["held_low"]), "high": _q(t["held_high"])}
        row = {"line_id": lid, "before_r4": before, "m3_value": None, "m3_low": None, "m3_high": None}
        if lid == COMPANION:
            row.update(cls="DEPTH_COMPANION", floor="GF", mark="B4|B7", designer_item="-",
                       status="HELD_BOUNDED_AS_DRAWN", m3_low=before["low"], m3_high=before["high"],
                       basis="T-642 FR-T642-2: 0.050 released at B4 0.50; companion 0 .. 0.025 = B7 0.75 alternative "
                             "(faces 2B2 / 2B3, R-T619-1); unchanged")
            rows.append(row)
            continue
        p = t402[lid]
        row.update(floor=p["floor"], mark=p["mark"], designer_item=p["designer_item"], cls=p["cls"],
                   element_id=p["element_id"], drawn_width_m=p["drawn_width_m"] or None,
                   f2f_length_m=p["f2f_length_m"] or None, edge_handles=p["edge_handles"] or None)
        c = p["cls"]
        if lid == GF059["line_id"]:
            v = R.value_from_section(width_plan=GF059["width"], depth_chain=GF059["chain"], length_f2f=GF059["length"],
                                     round_extents=GF059["round"])
            row.update(status="VALUED_AS_DRAWN", m3_value=str(v), basis=GF059["basis"],
                       beside={"T402_r2_value": p["value_m3"], "without_round": str(
                           (D(GF059["width"]) * D("0.75") * D(GF059["length"])).quantize(R.Q6))})
        elif c == "WIDTH":
            sch_wider = p["mark"] in ("B29", "B21", "B6")
            row.update(status="HELD_BOUNDED_AS_DRAWN", m3_low=before["low"], m3_high=before["high"],
                       basis=f"{p['why_held']} (Q-61 C(1) CONFLICT: pair of readings, R-T660-5)",
                       beside={"T402_own_low": p["low_m3"], "T402_own_high": p["high_m3"],
                               "slab_pairing": p["slab_pairing"],
                               "net_concrete_shift_schedule_minus_drawn_m3": p["total_shift_schedule_minus_drawn_m3"],
                               "schedule_reading_is_wider": sch_wider})
        elif c == "TWO_MARKS":
            lo, hi = R.two_marks("0.212", "0.3975")
            assert (str(lo), str(hi)) == (before["low"], before["high"])
            row.update(status="HELD_BOUNDED_AS_DRAWN", m3_low=str(lo), m3_high=str(hi),
                       basis="B3 20x40 (p.10, label 'B3 (With Stair)' 0.15 m north of span 2) vs CB3 20x75 (p.11 "
                             "three-span row, CB3 printed under all three spans); never both (Q-61 C(2), R-T660-4)",
                       evidence=dict(R.span_crosscheck(CB3_SPANS["printed"], CB3_SPANS["drawn_cc"]),
                                     printed=list(CB3_SPANS["printed"]), drawn_cc=list(CB3_SPANS["drawn_cc"]),
                                     note="3 printed spans = 3 drawn spans; span 2 within 0.05, span 3 within 0.05, "
                                          "span 1 +0.27: evidence for the Checker (B-S18 schedule over plan "
                                          "annotation), never a selection here"))
        elif c == "UNLABELLED":
            env = R.schedule_envelope(p["drawn_width_m"], p["f2f_length_m"], SCHEDULE_W020)
            row.update(status="HELD_BOUNDED_AS_DRAWN", m3_low=str(env[0]), m3_high=str(env[1]),
                       basis=f"no mark, no section crosses it; drawn width {p['drawn_width_m']} x f2f "
                             f"{p['f2f_length_m']} x scheduled depths of breadth-0.20 rows 0.40 .. 1.20 (R-T660-2, "
                             f"Q-61 C(4))")
        elif c in ("PROJECTION", "RING"):
            pr = R.projection_strip(p["plan_area_m2"])
            row.update(status=pr["status"], plan_area_m2=pr["plan_area_m2"],
                       basis=(SECTION_CROSS.get(lid, "no section crosses it") + "; no mark, no bars, depth not printed"
                              + ("; dome detail ring depth 'AS PER ARCH', no B4 mark on the east ring (Q-61 C(3))"
                                 if c == "RING" else "") + " (R-T660-3)"),
                       guard=pr["guard"] if c == "PROJECTION" else None,
                       parapet_note=PARAPET_NOTE if c == "PROJECTION" else None,
                       trial_range_beside_not_drawn=before if before["low"] is not None else None)
        else:
            raise R.Refused(f"unknown class {c}")
        rows.append(row)
    R.check_once(rows)
    return rows


def _sum(rows, key):
    return sum((D(r[key]) for r in rows if r.get(key) is not None), D(0)).quantize(R.Q6)


def totals(rows):
    b4 = [r for r in rows if r["before_r4"]["low"] is not None]
    bd = [r for r in rows if r["status"] == "HELD_BOUNDED_AS_DRAWN"]
    nd = [r for r in rows if r["status"] == "HELD_NO_DRAWN_DEPTH"]
    val = [r for r in rows if r["status"] == "VALUED_AS_DRAWN"]
    return {
        "lines": len(rows),
        "before_r4": {"bounded": len(b4), "blank": len(rows) - len(b4),
                      "low_m3": str(sum((D(r["before_r4"]["low"]) for r in b4), D(0))),
                      "high_m3": str(sum((D(r["before_r4"]["high"]) for r in b4), D(0)))},
        "after": {"valued": len(val), "valued_m3": str(_sum(val, "m3_value")),
                  "bounded_as_drawn": len(bd), "bounded_low_m3": str(_sum(bd, "m3_low")),
                  "bounded_high_m3": str(_sum(bd, "m3_high")),
                  "held_no_drawn_depth": len(nd),
                  "held_no_drawn_depth_plan_m2": str(sum((D(r["plan_area_m2"]) for r in nd), D(0))),
                  "trial_range_beside_not_drawn_low_m3": str(sum((D(r["trial_range_beside_not_drawn"]["low"])
                                                                   for r in nd if r["trial_range_beside_not_drawn"]),
                                                                  D(0))),
                  "trial_range_beside_not_drawn_high_m3": str(sum((D(r["trial_range_beside_not_drawn"]["high"])
                                                                    for r in nd if r["trial_range_beside_not_drawn"]),
                                                                   D(0)))},
        "by_class": {c: sum(1 for r in rows if r["cls"] == c) for c in sorted({r["cls"] for r in rows})},
        "reconciliation": _reconcile(rows)}


def _reconcile(rows):
    """before r4 bound = after bounded + (valued line's old bound) + (projection ranges set aside) + length terms."""
    out = {}
    for end in ("low", "high"):
        before = sum((D(r["before_r4"][end]) for r in rows if r["before_r4"][end] is not None), D(0))
        bounded = sum((D(r[f"m3_{end}"]) for r in rows if r["status"] == "HELD_BOUNDED_AS_DRAWN"), D(0))
        valued_old = sum((D(r["before_r4"][end]) for r in rows if r["status"] == "VALUED_AS_DRAWN"), D(0))
        set_aside = sum((D(r["before_r4"][end]) for r in rows
                         if r["status"] == "HELD_NO_DRAWN_DEPTH" and r["before_r4"][end] is not None), D(0))
        f2f = sum((D(r[f"m3_{end}"]) - D(r["before_r4"][end]) for r in rows if r["cls"] == "UNLABELLED"), D(0))
        assert bounded - f2f + valued_old + set_aside == before, end
        out[end] = {"before": str(before), "after_bounded": str(bounded), "valued_line_old_bound": str(valued_old),
                    "projection_ranges_set_aside": str(set_aside), "unlabelled_face_to_face_length_term": str(f2f)}
    return out


def build():
    rows = ledger()
    return {"schema": "T660_BEAM_LEDGER_V1",
            "candidate": "trial BOQ r4 T-654 per_line (STR.CONC.BEAM HELD); NOT RELEASED, nothing wired",
            "note": "engine figures, bounds, plan areas and drawing bases only; no freelancer row or count",
            "totals": totals(rows), "beams": rows}


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    doc = build()
    if a.write:
        OUT.parent.mkdir(exist_ok=True)
        OUT.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(doc["totals"], indent=1))


if __name__ == "__main__":
    main()
