"""T-270 (V3.0.15): the project inputs of ARCH_TAKEOFF_V3.0.15 (URBAN_V3015_INPUTS_V1) for the development villa.
Research code; it reads the checker-merged T-219 / T-263 / T-233 ledgers as committed and changes none of their
quantities. No coordinates, no names, no drawing content: references are 'ST7757 dxf.dxf' entity handles (hex), run ids
and printed dimensions, as the merged ledgers give them.

FOUNDATION_WP, from
  T-219 (MERGED de7c1c4c, Verifier 2026-10-24 10:40 UTC Gate A PASS: own footing schedule sizes x tag count = 109.85 m2
        on 24 outlines, 9 drawn outlines agree, p.13 extent at 300 dpi (membrane / screed end at the footing faces);
        lift fixed parts 47.43 / 26.73 / 1.035 own; F10 / F outline 1B1B HELD (Q-31 C); sides HELD (Q-21 C); walls HELD
        (pit depth); procurement HELD);
  T-263 (MERGED c0ab564d, Verifier 2026-10-24 17:59 UTC Gate A PASS: ground-beam buried faces 35.404365 m2
        DRAWING-CONFIRMED on 21 faces, 2 runs / 3 faces 5.3825 m2 own-checked: line PARTIALLY VERIFIED; footing tops,
        necks, held faces, boundary / straps HELD; plinth outer faces and soffits on blinding EXCLUDED by name);
  T-233 (MERGED 2ecb5bf0, Checker 2026-10-23 20:14 re-measured all 26 outlines): the footing outline and blinding
        outline areas the extent check compares each underlay component with.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
L219 = "research/agents_t219/LEDGER_T219.csv"
L263 = "research/agents_t263/LEDGER_T263.csv"
S263 = "research/agents_t263/summary.json"
I233 = "research/agents_t233/ALSENAN_FOOTING_INPUT.json"
I219 = "research/agents_t219/ALSENAN_T219_INPUT.json"
FLOOR = "FOUNDATION"                      # the floor of the candidate's footing / blinding lines
V219 = "Verifier 2026-10-24 10:40 UTC (Gate A PASS a-h)"
V263 = "Verifier 2026-10-24 17:59 UTC (Gate A PASS)"
V233 = "Checker 2026-10-23 20:14 UTC (all 26 outlines re-measured)"
P13 = "ST7757.pdf p.13 typical isolated-footing details (5 cm screed / membrane '2' / 10 cm plain concrete; membrane " \
      "and screed end at the footing faces, only the blinding projects '10 | L x W | 10')"
P14 = "ST7757.pdf p.14 'DETAIL OF LIFT WITH ISOLATED FOOTING (WITHOUT BASEMENT)' + 'ST7757 dxf.dxf' FF 1B2B 4.600 x " \
      "4.500, ring 10EB 2.200 x 2.200, C9 1090 proud 0.050 x 1.000 (envelope 4.890 m2 / 8.900 m)"
NOTE13 = "ST7757.pdf p.13 note 'Two layers liquid water proofing to be applied to all surface in contact with earth' " \
         "(per face with earth against it in the finished work)"
PRODUCT_HELD = ("PRODUCT_NOT_PRINTED: membrane / liquid product, thickness-to-product, laps and coats not printed: rolls "
                "/ coats only for a printed product (UP-WP-MAT-001; UP-WP-001 / -002 / -005 / UP-WP-LAY-001 for a "
                "printed sheet membrane); designer item")


def _sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def _src(f, task, mc, run):
    return {"file": f, "sha256": _sha(f), "task": task, "merge_commit": mc, "checker_run": run}


def _rows(f):
    with open(ROOT / f, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _outlines():
    d = json.loads((ROOT / I233).read_text(encoding="utf-8"))
    return {o["id"]: o for o in d["outlines"]}


def footing_components(item, unit):
    """the T-219 DRAWING-CONFIRMED rows of one item / unit, each with the T-233 outline and blinding areas."""
    out, ol = [], _outlines()
    for x in _rows(L219):
        if x["item"] != item or x["unit"] != unit or x["status"] != "DRAWING-CONFIRMED":
            continue
        o = ol[x["outline"]]
        out.append({"id": f"FTG:{x['outline']}", "type": x["type"], "value": float(x["qty"]),
                    "extent": "FOOTING_OUTLINE", "outline_m2": float(o["area"]), "blinding_m2": float(o["blind_m2"]),
                    "clipped_by": o.get("clipped_by") or []})
    return out


def _held_219(item, unit, outline):
    x = [r for r in _rows(L219) if r["item"] == item and r["unit"] == unit and r["outline"] == outline]
    assert len(x) == 1 and x[0]["status"] == "HELD", (item, unit, outline)
    return x[0]


def sides_readings():
    lo = hi = 0.0
    n = 0
    for x in _rows(L219):
        if x["item"] == "WP.FOOTING_SIDES" and x["status"] == "HELD" and x["low"]:
            lo += float(x["low"])
            hi += float(x["high"])
            n += 1
    return round(lo, 6), round(hi, 6), n


def buried_components():
    out = []
    for x in _rows(L263):
        if x["status"] == "DRAWING-CONFIRMED" and x["unit"] == "m2":
            out.append({"id": f"{x['element']} {x['face'].split(' (')[0]}", "member": x["member"],
                        "face": x["face"], "value": float(x["qty"]), "basis": x["basis"]})
    return out


def records():
    sl, sh, sn = sides_readings()
    s263 = json.loads((ROOT / S263).read_text(encoding="utf-8"))
    tops = s263["footing_tops"]
    conf = list(tops["single_reading_conflict"].values())[0]
    necks = s263["necks"]
    m1b = _held_219("WP.FOOTING_MEMBRANE", "m2", "1B1B")
    lw = _held_219("WP.LIFT_PIT_MEMBRANE_WALLS", "m2", "1B2B")
    fm = footing_components("WP.FOOTING_MEMBRANE", "m2")
    s2 = footing_components("SCREED.FOOTING_PROTECTION", "m2")
    s3 = footing_components("SCREED.FOOTING_PROTECTION", "m3")
    bc = buried_components()
    held_1b1b = ["F10 / F outline 1B1B carries two schedule tags (F + F10): readings 'outline' 4.55 and 'rows "
                 "separately' 4.64 m2, never one picked (Q-31 C; designer item)"]
    R = []

    def rec(**kw):
        kw.setdefault("floor", FLOOR)
        kw.setdefault("physical_element", "FOUNDATION")
        R.append(kw)

    # ---- T-219: underlay under the footings
    rec(id="FTG-MEMBRANE", item_code="WP.FOUNDATION.FOOTING_MEMBRANE", unit="m2", state="RELEASED", task="T-219",
        element="FOOTING_UNDERLAY_MEMBRANE", value=round(sum(c["value"] for c in fm), 6), components=fm,
        verified_by=V219 + ": own footing schedule sizes x tag count, 9 drawn outlines agree",
        verified_components="ALL", printed=P13, line_status="PARTIALLY VERIFIED (24 / 25 outlines; 1B1B HELD)",
        formula="sum over the 24 measured footing outlines of L x W (FN 180C notch 0.40 x 0.35 deducted once), one "
                "layer installed")
    rec(id="FTG-MEMBRANE-1B1B", item_code="WP.FOUNDATION.FOOTING_MEMBRANE", unit="m2", state="HELD", task="T-219",
        element="FOOTING_UNDERLAY_MEMBRANE_1B1B", reasons=held_1b1b, printed=P13,
        scenario={"readings": json.loads(m1b["readings"]), "basis": m1b["basis"]})
    rec(id="FTG-SCREED-M2", item_code="WP.FOUNDATION.FOOTING_SCREED", unit="m2", state="RELEASED", task="T-219",
        element="FOOTING_PROTECTION_SCREED", value=round(sum(c["value"] for c in s2), 6), components=s2,
        verified_by=V219 + ": screed on the same 24 outlines", verified_components="ALL", printed=P13,
        line_status="PARTIALLY VERIFIED (24 / 25 outlines; 1B1B HELD)", formula="screed plan = the footing outline")
    rec(id="FTG-SCREED-M3", item_code="WP.FOUNDATION.FOOTING_SCREED", unit="m3", state="RELEASED", task="T-219",
        element="FOOTING_PROTECTION_SCREED", value=round(sum(c["value"] for c in s3), 6), components=s3,
        verified_by=V219 + ": 109.85 x 0.05 = 5.4925 m3", verified_components="ALL", printed=P13,
        line_status="PARTIALLY VERIFIED (24 / 25 outlines; 1B1B HELD)",
        formula="footing outline x the printed 0.05 m screed")
    rec(id="FTG-SCREED-M2-1B1B", item_code="WP.FOUNDATION.FOOTING_SCREED", unit="m2", state="HELD", task="T-219",
        element="FOOTING_PROTECTION_SCREED_1B1B", reasons=held_1b1b, printed=P13,
        scenario={"readings": {"outline": 4.55, "rows_separately": 4.64}, "basis": "follows the held outline"})
    rec(id="FTG-SCREED-M3-1B1B", item_code="WP.FOUNDATION.FOOTING_SCREED", unit="m3", state="HELD", task="T-219",
        element="FOOTING_PROTECTION_SCREED_1B1B", reasons=held_1b1b, printed=P13,
        scenario={"readings": {"outline": 0.2275, "rows_separately": 0.232}, "basis": "held outline x 0.05"})
    rec(id="FTG-SIDES", item_code="WP.FOUNDATION.FOOTING_SIDES", unit="m2", state="HELD", task="T-219",
        element="FOOTING_SIDE_FACES",
        reasons=["governing footing detail not selected: p.13 right detail (upper ground beam to footing < 2.5 m) "
                 "'Two layers liquid water proofing' on perimeter x H, left detail (> 2.5 m) sheet membrane down the "
                 "sides to the blinding perimeter x (H + 0.07); the founding level decides (Q-21 C; designer); 1B1B "
                 "depth not established (two tags)"], printed=P13,
        scenario={"readings": {"single_liquid_P_x_H": sl, "double_sheet_P_x_H_plus_0_07": sh},
                  "basis": f"{sn} outlines, net of the FN / F9 clip faces and the strap ends at e = 0 (T-230); 1B1B "
                           "not included"})
    # ---- T-219: lift pit (p.14)
    rec(id="PIT-MEMBRANE", item_code="WP.FOUNDATION.LIFT_PIT_MEMBRANE", unit="m2", state="RELEASED", task="T-219",
        element="LIFT_PIT_MEMBRANE_FIXED", physical_element="LIFT_PIT", value=47.43,
        components=[{"id": "LIFT-01 base soffit", "value": 20.7, "basis": "4.600 x 4.500"},
                    {"id": "LIFT-01 base + screed sides", "value": 10.92, "basis": "18.200 x (0.55 + 0.05)"},
                    {"id": "LIFT-01 base top outside the pit envelope", "value": 15.81, "basis": "20.700 - 4.890"}],
        verified_by=V219 + ": own read p.14 + DXF FF 1B2B / ring 10EB / C9 1090", verified_components="ALL",
        printed=P14, line_status="PARTIALLY VERIFIED (fixed parts VERIFIED; walls HELD)",
        formula="soffit + base and screed sides + base top outside the pit envelope")
    rec(id="PIT-MEMBRANE-WALLS", item_code="WP.FOUNDATION.LIFT_PIT_MEMBRANE", unit="m2", state="HELD", task="T-219",
        element="LIFT_PIT_MEMBRANE_WALLS", physical_element="LIFT_PIT", reasons=[lw["held_why"] + " (D-43)"],
        printed=P14, scenario={"readings": json.loads(lw["readings"]), "basis": lw["basis"]})
    rec(id="PIT-BOARD", item_code="WP.FOUNDATION.LIFT_PIT_BOARD", unit="m2", state="RELEASED", task="T-219",
        element="LIFT_PIT_BOARD_FIXED", physical_element="LIFT_PIT", value=26.73,
        components=[{"id": "LIFT-01 base + screed sides", "value": 10.92, "basis": "18.200 x (0.55 + 0.05)"},
                    {"id": "LIFT-01 base top outside the pit envelope", "value": 15.81, "basis": "20.700 - 4.890"}],
        verified_by=V219 + ": own read p.14 (board on sides, top and walls, not under the base)",
        verified_components="ALL", printed=P14, line_status="PARTIALLY VERIFIED (fixed parts VERIFIED; walls HELD)",
        formula="base and screed sides + base top outside the pit envelope (no board under the base)")
    rec(id="PIT-BOARD-WALLS", item_code="WP.FOUNDATION.LIFT_PIT_BOARD", unit="m2", state="HELD", task="T-219",
        element="LIFT_PIT_BOARD_WALLS", physical_element="LIFT_PIT", reasons=[lw["held_why"] + " (D-43)"],
        printed=P14, scenario={"readings": {"per_m_height": 8.9}, "basis": "envelope 8.900 m x h"})
    rec(id="PIT-SCREED-M2", item_code="WP.FOUNDATION.LIFT_PIT_SCREED", unit="m2", state="RELEASED", task="T-219",
        element="LIFT_PIT_BASE_SCREED", physical_element="LIFT_PIT", value=20.7,
        components=[{"id": "LIFT-01 base", "value": 20.7, "basis": "4.600 x 4.500"}],
        verified_by=V219, verified_components="ALL", printed=P14, line_status="VERIFIED",
        formula="base area under the base")
    rec(id="PIT-SCREED-M3", item_code="WP.FOUNDATION.LIFT_PIT_SCREED", unit="m3", state="RELEASED", task="T-219",
        element="LIFT_PIT_BASE_SCREED", physical_element="LIFT_PIT", value=1.035,
        components=[{"id": "LIFT-01 base", "value": 1.035, "basis": "20.700 x 0.05"}],
        verified_by=V219, verified_components="ALL", printed=P14, line_status="VERIFIED",
        formula="base area x the printed 0.05 m screed")
    # ---- T-263: liquid coating of the buried concrete
    rec(id="BURIED-GB", item_code="WP.FOUNDATION.BURIED_LIQUID", unit="m2", state="RELEASED", task="T-263",
        element="BURIED_GROUND_BEAM_FACES", physical_element="GROUND_BEAM", value=round(sum(c["value"] for c in bc), 6),
        components=bc, verified_by=None,
        partial_check={"m2_or_unit": 5.3825, "run": V263,
                       "what": "runs 7E9+7EA#1 (2 x 0.30 x 4.225 = 2.535) and 7E0+FD#1 inner (0.85 x 3.350 = "
                               "2.8475): 2 runs / 3 faces own-checked, agree"},
        excluded={"plinth_outer_faces": "14 main exterior OUTER faces: soffit at natural ground, 0.95 m plinth above "
                                        "ground (facade item, not buried)",
                  "soffits_on_blinding_m2": 55.002},
        printed=NOTE13, line_status="PARTIALLY VERIFIED (DRAWING-CONFIRMED; 5.3825 of 35.404365 m2 own-checked)",
        formula="interior single-title runs 2 x (D - 0.10 slab) x L + main exterior inner faces on fill 0.85 x L; "
                "21 faces")
    rec(id="BURIED-GB-HELD", item_code="WP.FOUNDATION.BURIED_LIQUID", unit="m2", state="HELD", task="T-263",
        element="BURIED_GROUND_BEAM_FACES_HELD", physical_element="GROUND_BEAM",
        reasons=[f"{s263['gb_faces_held']} ground-beam faces HELD: interior depth (D-33 / D-34 / T-217), panels "
                 "GS-12 / GS-16 / GS-08, annex CONFLICT, court, 2 arcs with two readings; traced faces wait on T-276 "
                 "(REJECTED narrow r2), never estimated"], printed=NOTE13)
    rec(id="BURIED-TOPS", item_code="WP.FOUNDATION.BURIED_LIQUID", unit="m2", state="HELD", task="T-263",
        element="FOOTING_TOPS_OUTSIDE_NECKS",
        reasons=["footing tops outside the necks: the coating is drawn on the right p.13 detail only; the founding "
                 "level selects the detail (Q-21 C); C8 10E0 neck section CONFLICT; 1B1B two tags"], printed=NOTE13,
        scenario={"readings": {"single_detail_low": round(tops["single_reading_m2_exact"] + conf["SINGLE_low"], 6),
                               "single_detail_high": round(tops["single_reading_m2_exact"] + conf["SINGLE_high"], 6)},
                  "basis": f"{tops['outlines_held_detail']} outlines, footing outline less the neck sections"})
    rec(id="BURIED-NECKS", item_code="WP.FOUNDATION.BURIED_LIQUID", unit="m2", state="HELD", task="T-263",
        element="NECK_FACES",
        reasons=[f"{necks['held']} neck faces HELD on the neck height (formation, Q-21 C); 4 lift necks owned by the "
                 "lift pit (T-219); beam-zone faces against concrete to be deducted (T-276 finding)"],
        printed=NOTE13, scenario={"readings": {"per_m_height_low": necks["m2_per_m_height"][0],
                                               "per_m_height_high": necks["m2_per_m_height"][1]},
                                  "basis": "perimeter per metre of neck height (beam-zone deduction not applied)"})
    rec(id="BURIED-BOUNDARY", item_code="WP.FOUNDATION.BURIED_LIQUID", unit="m2", state="HELD", task="T-263",
        element="BOUNDARY_GB_AND_STRAPS",
        reasons=["boundary ground beam, straps and the lower boundary beam: their own details print no coating "
                 "(note scope, designer item; ERS s.3)"], printed=NOTE13)
    rec(id="WP-PROCUREMENT", item_code="WP.FOUNDATION.PROCUREMENT", unit="item", state="HELD", task="T-219",
        element="FOUNDATION_WP_PROCUREMENT", reasons=[PRODUCT_HELD], printed=P13)
    return R


def declared(recs):
    out = {}
    for r in recs:
        t = out.setdefault(f"{r['item_code']} {r['unit']}", {"released": 0.0, "held_lines": 0})
        if r["state"] == "RELEASED":
            t["released"] = round(t["released"] + r["value"], 6)
        else:
            t["held_lines"] += 1
    return out


# the figures the Checker re-measured (Verifier 10:40 / 17:59): the declared totals must equal them to 1e-6
CHECKER_FIGURES = {"WP.FOUNDATION.FOOTING_MEMBRANE m2": 109.85, "WP.FOUNDATION.FOOTING_SCREED m2": 109.85,
                   "WP.FOUNDATION.FOOTING_SCREED m3": 5.4925, "WP.FOUNDATION.LIFT_PIT_MEMBRANE m2": 47.43,
                   "WP.FOUNDATION.LIFT_PIT_BOARD m2": 26.73, "WP.FOUNDATION.LIFT_PIT_SCREED m2": 20.7,
                   "WP.FOUNDATION.LIFT_PIT_SCREED m3": 1.035, "WP.FOUNDATION.BURIED_LIQUID m2": 35.404365}


def inputs(project_id):
    recs = records()
    dec = declared(recs)
    for k, v in CHECKER_FIGURES.items():
        assert abs(dec[k]["released"] - v) <= 1e-6, (k, dec[k], v)
    pc = {"piece": "FOUNDATION_WP",
          "source": _src(L219, "T-219", "de7c1c4c", V219),
          "sources": [_src(L263, "T-263", "c0ab564d", V263), _src(I233, "T-233", "2ecb5bf0", V233)],
          "chain": {"screed_t": 0.05, "membrane_t": 0.02, "membrane_extent": "FOOTING_OUTLINE",
                    "source": "T-219 " + I219},
          "blinding": {"item_codes": ["STR.CONC.BLINDING"], "trade": "CONCRETE"},
          "records": recs, "declared_totals": dec}
    import sys
    sys.path.insert(0, str(ROOT / "research/agents_t193"))
    import t193_inputs as L7   # noqa: E402  (the V3.0.7 guard inputs, unchanged, as V3.0.8 .. V3.0.14)
    g = dict(L7.inputs(project_id)["guard"], new_records=[])
    return {"schema": "URBAN_V3015_INPUTS_V1", "project": project_id, "pieces": [pc], "guard": g}
