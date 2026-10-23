"""T-204 on the development villa: lift pit and roof water tank component ledger + ELEMENT_CONTINUITY_V1 re-run.

    python3 -I research/agents_t204/alsenan_t204.py [--write]   (prints the summary; --write rewrites LEDGER_T204.csv,
                                                                 FINDINGS_T204.csv and summary.json beside this file)

Readings (this run's own, private copies in .work/private only, never committed; cited by handle / sheet title):
  "ST7757 dxf.dxf" (Drive "Alsenan chalet project", sha256 9f9d1179...):
    FOUNDATION PLAN frame (title block FP, insert 90): pit outlines S-BW 10EB (outer 2200 x 2200) and 10EA (inner
    1800 x 1800), cross-hatched S-HAT.BAT 10E9 (ANSI37, the RC hatch of the plot-boundary wall); lift columns S-COL.BON
    1099 C1 200 x 500 (NW), 1093 C2 200 x 500 (NE), 1096 C2 200 x 500 (SW), 1090 C9 250 x 1000 (SE) with marks
    109D / 109C / 109B / 109A; footing outline S-FOOTINGS 1B2B 4600 x 4500 under mark FF (text 1676).
    GROUND BEAMS PLAN frame (title block GBP, insert B9): the same ring 7C2 / 7BE + hatch 7BD and the same four
    columns 1EC / 1EF / 1F2 / 1F5; ground-beam edge lines (layer 1: 15C / 7CC, 7E3 / 17C, 177 / 7CD, 15E / 15F, 15D /
    7C8, 17E / 17F) stop on the ring's outer face: no beam runs over the ring.
    Footing schedule row INSERT 2B1E (FTB): FF W 460, H 450, DEPHT 55, top 6 d14/m both ways, bottom 9 d14/m both ways.
    Text search (model space + every block, EN + AR): 'TANK' only 1A85 'WATER TANK PLACE'; no LIFT / PIT / ELEV text.
  "ST7757.pdf" (sha256 74da1523...), p.14 DETAILS (2) (a sheet the DXF does not carry: its only paper layout is
    'DETAILS'): "DETAIL OF LIFT WITH ISOLATED FOOTING (WITHOUT BASEMENT)", Arabic subtitle 'typical detail of the lift
    base in plots without basement': RC pit walls 20 cm on the footing, vertical 6 d16/m and horizontal 6 d12/m on both
    faces, 2 d12 at the wall top, 2 d16 + 2 d16 in the footing under each wall; pit depth 'As Per Lift Manufactures
    recommendations'; pit width 'AS ARCH.'; footing depth / projection 'AS PER SCHEDULE'; above the F.F.L. the shaft
    walls 'AS PER PLAN'; layers: waterproofing membrane round the footing and up the outer wall faces, protection board,
    '5cm Screed' under the footing over the membrane, '10cm Plain con.' below; 'Well graded clean compacted fill from
    excavation material' outside. p.8 notes 19 (beams tie the lift columns at 3.00 m where the storey is taller than
    4.30 m, round the lift shaft) and 20 (walls containing columns are built to the column thickness).
  "P7757.dxf" (from P7757_DXF_COMPRESSED.zip, sha256 ab54dd55...): text search model space + every block (EN + AR
    'lift / elevator / tank / pit'): none; the shaft is drawn unlabelled (T-063 s.5).
Merged evidence reused with citation (WORKFLOW_CONTROLS s.10 rule 5): T-065 FF 4.60 x 4.50 x 0.55 (footing line),
S8.1A ring regions 0.36 + 0.36 + 0.24 + 0.14 m2, T-184 s.2 lift box B14 / B7 / B1 and the storey levels, S8.4 / T-166
tank panels, T-152 tank T&B slab steel, T-188 inventory, D-43 / D-44 / D-52, freelancer row RC:S13:11 (T-196 id).
"""

from __future__ import annotations

import csv
import importlib.util
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


LT = _load("t204_lift_tank_v1", HERE / "lift_tank_v1.py")
T188 = _load("t204_alsenan_t188", ROOT / "research/agents_t188/alsenan_t188.py")

FP = "ST7757 dxf.dxf FOUNDATION PLAN"
P14 = "ST7757.pdf p.14 DETAIL OF LIFT WITH ISOLATED FOOTING (WITHOUT BASEMENT), typical"
# plan frame: origin at the pit ring's outer south-west corner (FOUNDATION PLAN 10EB min corner), millimetres
LIFT = {
    "id": "LIFT-01", "unit": "mm",
    "pit_inner": [200, 200, 2000, 2000], "pit_inner_ref": f"{FP} S-BW 10EA 1800 x 1800 (= p.14 'AS ARCH.')",
    "wall_t": 200, "wall_ref": f"{FP} S-BW 10EB / 10EA + RC hatch 10E9; GROUND BEAMS PLAN 7C2 / 7BE / 7BD; p.14 '20'",
    "columns": [
        {"id": "C1", "rect": [0, 1700, 200, 2200], "ref": f"{FP} S-COL.BON 1099, mark 109D"},
        {"id": "C2-NE", "rect": [2000, 1700, 2200, 2200], "ref": f"{FP} S-COL.BON 1093, mark 109C"},
        {"id": "C2-SW", "rect": [0, 0, 200, 500], "ref": f"{FP} S-COL.BON 1096, mark 109B"},
        {"id": "C9", "rect": [2000, 0, 2250, 1000], "ref": f"{FP} S-COL.BON 1090, mark 109A"}],
    "base": {"id": "FF", "L": 4600, "B": 4500, "D": 550, "owner_line": "CONC.FOOTING FF (T-065: 11.385 m3)",
             "ref": f"{FP} S-FOOTINGS 1B2B 4600 x 4500; schedule INSERT 2B1E FF 460 / 450 / 55"},
    "pit_height": None, "pit_height_ref": "p.14: 'As Per Lift Manufactures recommendations' (not printed); the "
                                          "foundation level chain is HELD too (T-200: the structural set prints FFL "
                                          "only)",
    "detail": {"ref": P14, "state": "TYPICAL",
               "vertical": {"n_per_m": 6, "d": 16, "faces": 2}, "horizontal": {"n_per_m": 6, "d": 12, "faces": 2},
               "membrane": True, "protection_board": True, "screed_t": 50, "blinding_t": 100,
               "extra_bars": [{"label": "2d12_TOP", "count": 2, "d": 12, "run": "NET_CENTRELINE"},
                              {"label": "2+2d16_IN_BASE", "count": 4, "d": 16, "run": "GROSS_CENTRELINE"}]},
    "tie_beams": {"rule_ref": "ST p.8 note 19 (3.00 m, storey > 4.30 m, round the lift shaft); D-43 section not "
                              "printed", "threshold": 4300, "at": 3000, "section": None, "section_ref": None,
                  "storeys": [
                      {"storey": "GF", "height": 4500, "ref": "FFL +1.00 -> +5.50 (T-184 s.2 / T-063 levels; an FFL "
                                                              "interval, T-200 caveat)"},
                      {"storey": "1F", "height": 4200, "ref": "FFL +5.50 -> +9.70 (T-184 s.2)"},
                      {"storey": "2F", "height": 4200, "ref": "FFL +9.70 -> +13.90 (T-184 s.2)"}]},
}
TANK = {
    "id": "TANK-01", "unit": "m",
    "place_ref": "ST7757 dxf.dxf SECOND FLOOR ROOF SLAB 'WATER TANK PLACE' text 1A85 + cloud over panels 2F-011 / "
                 "2F-013 (T 18, T&B; S8.4)",
    "searched": "ST7757.pdf p.1-16 (T-166 s.4: p.7, p.14, p.15, p.16; this run p.14 / p.15 / p.16 re-looked); "
                "ST7757 dxf.dxf all text; P7757.dxf all text EN + AR: no tank wall, base, cover or member",
    "supporting_slab_lines": ["SLAB 2F-011 (T 18, T&B; T-152 / S8.4 1.4823 m3)",
                              "SLAB 2F-013 (T 18, T&B; T-152 / S8.4 0.972 m3)"],
    "walls": None, "base": None, "cover": None,
    "designer_item": "tank type (cast or prefabricated), capacity, footprint, walls / base / cover and support points "
                     "(S8.4 Q-S8.4-01 / Q-S8.4-07; D-44 B15 upstand or downstand; D-52 note 2 on the T&B panels)",
}

FREELANCER = {"row": "RC:S13:11", "text_basis": "lift walls 20 cm under the 'basement RC walls' heading",
              "L_m": 8.0, "t_m": 0.20, "h_m": 1.50, "m3": 2.40,
              "neck_rows": "RC:S13:16 C1 x1, RC:S13:17 C2 x4, RC:S13:24 C9 x2, all at 1.50 m (his neck height)"}


def reconcile(res):
    """Freelancer 2.40 m3 vs the drawing-derived pit wall, in units, cause by cause (ERS s.2 step 4)."""
    s = res["summary"]
    fl = FREELANCER
    his_plan = fl["L_m"] * fl["t_m"]
    out = {"freelancer_m3": fl["m3"], "his_plan_m2": round(his_plan, 6),
           "drawn_gross_ring_m2": s["ring_gross_m2"], "plan_difference_m2": round(his_plan - s["ring_gross_m2"], 6),
           "column_sections_in_ring_m2": s["column_in_ring_m2"], "drawn_net_ring_m2": s["ring_net_m2"],
           "his_height_m": fl["h_m"], "drawn_height": "HELD (not printed: lift manufacturer)"}
    # at HIS height, for comparison only (never a released value)
    out["at_his_height_net_m3"] = round(s["ring_net_m2"] * fl["h_m"], 6)
    out["at_his_height_column_part_m3"] = round(s["column_in_ring_m2"] * fl["h_m"], 6)
    out["closes"] = round(out["at_his_height_net_m3"] + out["at_his_height_column_part_m3"] - fl["m3"], 9) == 0
    out["verdict"] = ("plan scope: AGREE (8.00 m centreline x 0.20 = the drawn ring 1.60 m2); ownership: ENGINE "
                      "RIGHT on 0.50 m2 x h (the four lift columns stand in the ring band and his neck rows also bill "
                      "C1 x1, C2 x4 (2 of them the lift's), C9 x2 (1 the lift's) at 1.50 m: at his height 0.750 m3 "
                      "counted twice, R-CONC-OWN-1); height: UNRESOLVED (his 1.50 m is his neck height, not printed; "
                      "p.14 leaves the pit depth to the lift manufacturer)")
    return out


def proposed_lines():
    """BOQ line proposals bound to LIFT-01 / TANK-01 (all HELD placeholders: never a number until printed)."""
    ln = []
    for item, trade in (("CONC.LIFT_PIT_WALL", "STRUCTURE"), ("FORMWORK.LIFT_PIT_WALL", "FORMWORK"),
                        ("BAR_STEEL.LIFT_PIT_WALL", "BAR_STEEL"), ("WP.LIFT_PIT", "WATERPROOFING")):
        ln.append({"line_id": f"T204:{item}", "item": item, "kind": "LIFT", "storey": "FDN", "trade": trade,
                   "state": "HELD", "element": "LIFT-01", "ref": "T-204 ledger (pit height not printed)"})
    ln.append({"line_id": "T204:CONC.LIFT_TIE_BEAM:GF", "item": "CONC.LIFT_TIE_BEAM", "kind": "LIFT",
               "storey": "GF", "trade": "STRUCTURE", "state": "HELD", "element": "LIFT-01",
               "ref": "note 19 applies on GF (4.50 > 4.30); section D-43"})
    for item, trade in (("CONC.ROOF_TANK", "STRUCTURE"), ("BAR_STEEL.ROOF_TANK", "BAR_STEEL"),
                        ("WP.ROOF_TANK", "WATERPROOFING")):
        ln.append({"line_id": f"T204:{item}", "item": item, "kind": "TANK", "storey": "ROOF", "trade": trade,
                   "state": "HELD", "element": "TANK-01", "ref": "T-204 ledger (tank not drawn: designer item)"})
    return ln


def continuity():
    """ELEMENT_CONTINUITY_V1 on V3.0.6 (as T-188) and on V3.0.6 + the T-204 proposals, with LIFT-01's detail now
    recorded (p.14 typical) and the pit walls DRAWN in plan (depth still HELD)."""
    out = {}
    base = T188.project("V306")
    out["V306"] = T188.M.check(base)
    prop = T188.project("V306")
    for e in prop["elements"]:
        if e["id"] == "LIFT-01":
            e["detail"] = {"state": "TYPICAL", "ref": P14}
            e["components"] = [{"name": "PIT", "state": "HELD",
                                "ref": f"{FP} ring 10EB / 10EA + hatch 10E9 (walls 0.20 drawn) on FF; {P14}",
                                "note": "pit walls DRAWN in plan (net ring 1.10 m2); pit depth not printed "
                                        "('as per lift manufacturer')"}]
            e["presence"].append({"storey": "FDN", "discipline": "STRUCT", "ref": f"{P14}", "what": "DRAWN"})
            e["presence"].append({"storey": "2F", "discipline": "STRUCT", "what": "DRAWN",
                                  "ref": "ST7757 dxf.dxf FIRST FLOOR ROOF SLAB: shaft opening S-OPENING 73F / 740 "
                                         "over the box (beams B7 / B7 / B1 / B1)"})
            e["ends"] = {"ref": "ST7757 dxf.dxf SECOND FLOOR ROOF SLAB (+13.90): no S-OPENING over the lift box "
                                "(GF / FIRST FLOOR ROOF SLAB carry 54F / 550 and 73F / 740); slab bars S-REIN-SLAB "
                                "792 / 794 / 795 and callouts 791 / 793 '5d10/m' run inside the box: the roof slab "
                                "closes the shaft (own read, frame offset by the four lift columns 41E / 421 / 41B / "
                                "418)"}
    prop["lines"] += proposed_lines()
    out["V306+T204"] = T188.M.check(prop)
    return out


def run():
    return {"lift": LT.lift_pit(LIFT), "tank": LT.tank(TANK)}


def ledger_csv(res):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["element", "component", "owner_line", "basis", "unit", "value", "status", "ref", "missing"])
    for key in ("lift", "tank"):
        for r in res[key]["rows"]:
            w.writerow([r["element"], r["component"], r["owner_line"], r["basis"], r["unit"],
                        "" if r["value"] is None else f"{r['value']:.6f}", r["status"], r["ref"], r["missing"] or ""])
    return buf.getvalue()


def findings_csv(cont):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["state", "review", "code", "status", "element", "storey", "lines", "why"])
    for s, r in cont.items():
        for f in r["findings"]:
            if f["element"] in ("LIFT-01", "TANK-01"):
                w.writerow([s, f["review"], f["code"], f["status"], f["element"], f["storey"] or "",
                            " ".join(f["lines"]), f["why"]])
    return buf.getvalue()


def summary():
    res = run()
    cont = continuity()
    lt = {s: sorted(f"{f['element']}:{f['code']}:{f['status']}" for f in r["findings"]
                    if f["element"] in ("LIFT-01", "TANK-01")) for s, r in cont.items()}
    return res, cont, {"lift": res["lift"]["summary"], "lift_findings": res["lift"]["findings"],
                       "tank": res["tank"]["summary"], "tank_missing": res["tank"]["missing"],
                       "freelancer_reconciliation": reconcile(res["lift"]),
                       "continuity_lift_tank": lt,
                       "continuity_counts": {s: r["summary"] for s, r in cont.items()}}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    res, cont, summ = summary()
    if "--write" in argv:
        (HERE / "LEDGER_T204.csv").write_text(ledger_csv(res), encoding="utf-8")
        (HERE / "FINDINGS_T204.csv").write_text(findings_csv(cont), encoding="utf-8")
        (HERE / "summary.json").write_text(json.dumps(summ, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summ, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
