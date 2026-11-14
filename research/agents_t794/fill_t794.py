"""T-794 F-26 ROOF UPTURN vs FREELANCER: 233.0 vs 194 lm, split by run and cause; fix rows on V3.0.85 where the engine
is wrong.

Physical element: the 0.20 m membrane upturn on every SOLID vertical face that bounds a waterproofed roof surface
(parapet inner face, building wall foot, divider, dome ring base, wall under a window sill). Owner Q-24 (2026-10-19):
roofs "calculated as the bathrooms same way (membrane + 20cm walls upturn)", a dome higher than the slab gets "20cm
upturn around circle". Owner Q-35 (option C, 2026-10-19 16:40): the BOQ upturn line is WALLS ONLY; a doorway is its
own transition line (one per door), built to the detail (UP-WP-DOOR-001). A floor-level frame is a transition, never an
upturn (R-T522-1..4, T-529, merged research).

Inputs: research/agents_t770/out/LINE_INDEX_V3_0_85.json (the newest merged candidate), research/agents_t321/
ALSENAN_ROOF_LAYERS_INPUT.json (roof face polygons by handle), the T-522 / T-529 ledge split, and handles re-read this
run on Drive "Alsenan chalet project" P7757_DXF_COMPRESSED.zip (dimensions only, no coordinate stored here).
Freelancer: Drive same folder, floors / waterproofing / decor / marble workbook, waterproofing sheet, re-read this run
with the text reader: ONE typed row "roofs and annexes" length 194.00 lm, area 285.00 m2, multiplier 1.00, no sub-rows
(same as T-541).

Run: python3 -I research/agents_t794/fill_t794.py [--write]
"""
from __future__ import annotations

import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
IDX = os.path.join(ROOT, "research/agents_t770/out/LINE_INDEX_V3_0_85.json")
ROOFS = os.path.join(ROOT, "research/agents_t321/ALSENAN_ROOF_LAYERS_INPUT.json")
OUT = os.path.join(HERE, "out")

FREELANCER_UPTURN_LM = 194.00
UPTURN_H = 0.20                       # owner Q-24 / Q-30 / Q-35

# ---- drawing values re-read this run (P7757.dxf, mm -> m) -------------------------------------------------------------
# +9.70 roof (ROOF-970 = 2F-ROOF-AT379): its boundary on the 2F block south face y = 5.0 runs 4.2 .. 12.3 (8.10 m):
# wall 1280 (0.616) + GAP 1.000 + wall 1281 (6.484); the gap holds door block D115 (INSERT 12BA, layer 4: 12 lines +
# one swing arc r 0.890, layer D): a hinged DOOR from the 2F block onto the terrace, not a wall.
DOOR_970 = {"handle": "12BA", "block": "D115", "gap_m": 1.000, "pieces": {"1280": 0.616, "1281": 6.484}}
# +5.50 strips (TERRACE-550 = 1F-ROOF-AT216): north end of the east strip y = 7.5, x 17.67 .. 18.97 (1.30 m) =
# stub BDB / BDC 0.895 (layer 5, 0.20 thick) + an opening 0.406 between wall B60 and the stub end (C9E line + arcs CA0
# r 0.305 / CA3 r 0.100, layer D). Not a solid face; nature (gate / service opening) not printed: NAMED, not fixed
# (0.17 % of the trade, below the owner 1 % materiality).
GATE_550_LM = 0.406
# every other run of the four roof faces is a wall, parapet, divider or a window opening on layer W with a layer-5 sill
# line (terrace 0.600 / 1.553 / 1.552 / 1.552, annex 0.600): solid wall below a sill = upturn (T-522: the sill of the
# pool-court bath window is printed '84' cm).
WINDOWS_ON_ROOF_EDGES_LM = 0.600 + 1.553 + 1.552 + 1.552 + 0.600

# pool-court ledge (T-522 / T-529, merged research): bay face 3.528277 = BCD wall 0.250804 + BCE floor-level glazing
# 2.976663 + BD0 wall 0.300810 (residual 0).
LEDGE = {"BCD": 0.250804, "BCE_glazing": 2.976663, "BD0": 0.300810}

LINES = {
    "AT216": "L-994b88140f2ea50f1b31", "AT220": "L-d4c73babd2a275c28929", "AT379": "L-5ce5ba49792e8f9d1f6f",
    "TOP": "L-aac1f35e08f85b643692", "POOL": "L-cf8d5ed40b0d546427d6", "POOL_WIN": "L-1954878bb02c91139e1b",
    "LEDGE": "L-d7d1bf8c5991ccf69ea2",
}
DOME_970_RINGS_LM = 92.922 - 65.14     # engine chords 27.782 (circles 27.785396, T-541)
DOME3_RING_LM = 42.15454 - 28.30       # 13.85454 (T-780)


def r6(x):
    return round(x, 6)


def perimeter(poly):
    """perimeter of a T-321 face polygon (vertices and ["ARC", centre, r, a0, a1, handle] items)."""
    pts, total, prev = [], 0.0, None
    seq = []
    for v in poly:
        if isinstance(v, list) and v and v[0] == "ARC":
            _, c, r, a0, a1, _h = v
            seq.append(("ARC", c, r, a0, a1))
        else:
            seq.append(("P", v))
    first = None
    for i, it in enumerate(seq):
        if it[0] == "P":
            p = it[1]
            if prev is not None:
                total += math.dist(prev, p)
            prev = p
            first = first or p
        else:
            _, c, r, a0, a1 = it
            s = (c[0] + r * math.cos(math.radians(a0)), c[1] + r * math.sin(math.radians(a0)))
            e = (c[0] + r * math.cos(math.radians(a1)), c[1] + r * math.sin(math.radians(a1)))
            # the arc is walked from the end nearer the previous vertex
            if math.dist(prev, e) < math.dist(prev, s):
                s, e = e, s
            total += math.dist(prev, s) + r * math.radians(abs(a1 - a0))
            prev = e
    return total + math.dist(prev, first)


def upturn_walls_only(boundary_lm, door_gaps_lm, rings_lm=0.0):
    """R (Q-24 + Q-35 C, every villa): upturn lm = solid boundary faces + dome rings; a doorway is never upturn.
    Refuses missing data (never 0) and a door wider than the boundary."""
    if boundary_lm is None or door_gaps_lm is None:
        raise ValueError("boundary or door gaps missing: HELD, never 0")
    if any(g < 0 for g in door_gaps_lm) or sum(door_gaps_lm) > boundary_lm:
        raise ValueError("door gaps exceed the boundary")
    return boundary_lm - sum(door_gaps_lm) + rings_lm


def self_test():
    # normal (hand, non-Alsenan): 6 x 4 roof inside the parapet, one 0.90 door to a stair room, one dome r 1.0
    assert abs(upturn_walls_only(20.0, [0.90], 2 * math.pi * 1.0) - (19.10 + 6.283185)) < 1e-6
    # adverse: missing gaps refused (never 0); a door wider than the boundary refused
    for bad in ((None, [0.9]), (20.0, None), (1.0, [2.0])):
        try:
            upturn_walls_only(*bad)
        except ValueError:
            continue
        raise AssertionError(bad)
    # adverse: a floor-level frame carried as upturn must not equal the split
    assert abs(sum(LEDGE.values()) - 3.528277) < 1e-6
    assert abs((LEDGE["BCD"] + LEDGE["BD0"]) - 0.551614) < 1e-6


def main(write=False):
    self_test()
    idx = json.load(open(IDX))
    byid = {l["line_id"]: l for l in idx["lines"]}
    roofs = json.load(open(ROOFS))["roofs"]

    # ---- hand perimeters of the four faces (reproduce the engine lines) ----------------------------------------------
    per = {z: perimeter(roofs[z]["face_wall"]) for z in ("ROOF-430", "TERRACE-550", "ROOF-970", "ROOF-1390")}
    assert abs(per["TERRACE-550"] - byid[LINES["AT216"]]["measured_net"]) < 1e-3, per
    assert abs(per["ROOF-430"] - byid[LINES["AT220"]]["measured_net"]) < 2e-3, per
    assert abs(per["ROOF-970"] + DOME_970_RINGS_LM - byid[LINES["AT379"]]["measured_net"]) < 1e-3, per
    assert abs(per["ROOF-1390"] + DOME3_RING_LM - byid[LINES["TOP"]]["measured_net"]) < 1e-3, per
    assert abs(DOOR_970["pieces"]["1280"] + DOOR_970["gap_m"] + DOOR_970["pieces"]["1281"] - 8.10) < 1e-3

    ours = {k: byid[v]["measured_net"] for k, v in LINES.items()}
    for k, v in LINES.items():
        assert byid[v]["item_code"] == "FIN.WP.ROOF_UPTURN" and byid[v]["unit"] == "lm" and byid[v]["class"] == "RELEASED"
    total_before = sum(l["measured_net"] for l in idx["lines"]
                       if l["item_code"] == "FIN.WP.ROOF_UPTURN" and l["class"] != "EXCLUDED")
    assert abs(total_before - sum(ours.values())) < 1e-6

    rows, new = [], []

    def row(key, after, label, basis):
        l = byid[LINES[key]]
        rows.append({"line_id": l["line_id"], "item_code": l["item_code"], "unit": l["unit"],
                     "element_id": l["element_id"],
                     "before": {"class": l["class"], "net": l["measured_net"], "label": "ESTIMATE"},
                     "after": {"class": "RELEASED", "net": r6(after)}, "label": label, "basis": basis})

    at379_after = upturn_walls_only(per["ROOF-970"], [DOOR_970["gap_m"]], DOME_970_RINGS_LM)
    row("AT379", at379_after, "DRAWING-READ",
        f"+9.70 roof inner boundary {per['ROOF-970']:.3f} lm (T-321 face, parapets 1285 / 12A7 / 1278 / 12B9 / 12C9 + "
        f"2F block walls 1288 / 1281 / 1291) less the door gap 1.000 between walls 1280 and 1281 (door block D115, "
        f"swing r 0.89: a doorway is a transition, owner Q-24 'as the bathrooms' + Q-35 C walls only) + two dome "
        f"rings 27.782 (owner Q-24: 20 cm upturn round a dome) = {at379_after:.3f} lm")
    ledge_after = upturn_walls_only(sum(LEDGE.values()), [LEDGE["BCE_glazing"]])
    row("LEDGE", ledge_after, "DRAWING-READ",
        f"pool-court ledge bay face 3.528277 = wall BCD 0.250804 + floor-level glazing BCE 2.976663 + wall BD0 "
        f"0.300810 (T-522 / T-529 split, residual 0): upturn on the two wall pieces only = {ledge_after:.6f} lm; "
        f"the glazing frame stands on the slab = a transition by detail (R-T522-1, UP-WP-DOOR-001), its own line; "
        f"T-767 had carried the whole bay face (engine high bound) as upturn")
    new.append({"family": "B8-06", "line_id": "NEW:2F-ROOF-AT379:doorway transition D115",
                "item_code": "FIN.WP.DOORWAY_TRANSITION", "unit": "m2",
                "element_id": "2F-ROOF-AT379:doorway transition D115", "label": "DRAWING-READ",
                "basis": "2F block door onto the +9.70 roof (block D115 in the 1.000 gap between walls 1280 / 1281): "
                         "1.00 x 0.20 = 0.20 m2 (wet-room transition method, owner Q-35 C); moved out of the upturn",
                "net": r6(DOOR_970["gap_m"] * UPTURN_H)})
    new.append({"family": "B8-06", "line_id": "NEW:2F-ROOF-AT379:wp_door_transition:D115",
                "item_code": "FIN.WP.DOORWAY_TRANSITION_NR", "unit": "pcs",
                "element_id": "2F-ROOF-AT379:wp_door_transition:D115", "label": "DRAWING-READ",
                "basis": "one doorway transition per door (owner Q-35 C reading): the +9.70 roof door D115", "net": 1.0})
    new.append({"family": "B8-06", "line_id": "NEW:1F-POOLCOURT-550-LEDGE:termination glazing BCE",
                "item_code": "FIN.WP.TERMINATION", "unit": "lm",
                "element_id": "1F-POOLCOURT-550-LEDGE:termination glazing BCE", "label": "ESTIMATE",
                "basis": "floor-level bay glazing BCE on the +5.50 ledge: membrane terminated under the frame by detail "
                         "(UP-WP-DOOR-001, T-522 F-T522-3) over its run 2.976663 lm; moved out of the roof upturn",
                "net": r6(LEDGE["BCE_glazing"])})

    after = dict(ours)
    after["AT379"], after["LEDGE"] = at379_after, ledge_after
    total_after = sum(after.values())

    # ---- ours vs his by cause (his lump has no sub-rows: H1 of T-541 = his outlines = the four inner boundaries) ----
    inner4 = per["TERRACE-550"] + per["ROOF-430"] + per["ROOF-970"] + per["ROOF-1390"]
    his_residual = FREELANCER_UPTURN_LM - inner4
    pool = ours["POOL"] + ours["POOL_WIN"] + ledge_after
    causes = {   # ours - his, lm; sums exactly to the gap
        "RULE_DIFFERENCE two +9.70 dome rings (owner Q-24: 20 cm upturn round a dome; his lump keeps domes flat)":
            DOME_970_RINGS_LM,
        "RULE_DIFFERENCE DOME-3 ring on the +13.90 top roof (same rule)": DOME3_RING_LM,
        "ENGINE_RIGHT pool-court open-sky slab 5.193544 + bath-window wall under the '84' sill 0.500002 + ledge walls "
        "0.551614 (not in his lump under H1)": pool,
        "ENGINE_RIGHT doorway out of the upturn: +9.70 door D115 (his outline counts it)": -DOOR_970["gap_m"],
        "UNRESOLVED residual of his typed lump over the four inner boundaries (no sub-rows, formulas not visible)":
            -his_residual,
        "TOLERANCE annex arc: engine line 35.727 vs exact quarter-arc perimeter":
            ours["AT220"] - per["ROOF-430"],
    }
    gap = total_after - FREELANCER_UPTURN_LM
    assert abs(gap - sum(causes.values())) < 1e-6, (gap, sum(causes.values()))
    before_split = {"FIXED this row: bay glazing BCE carried as upturn (a transition; line 3.528 rounded)":
                    ours["LEDGE"] - ledge_after,
                    "FIXED this row: +9.70 door D115 carried as upturn (a transition)": DOOR_970["gap_m"]}
    assert abs((total_before - FREELANCER_UPTURN_LM) - (gap + sum(before_split.values()))) < 1e-6

    per_run = {
        "TERRACE-550 (+5.50 strips, AT216)": {"ours": ours["AT216"], "after": ours["AT216"],
                                              "note": f"52.940 = 18.97 + 7.50 + 1.30 + 6.20 + 17.67 + 1.30; walls / "
                                                      f"parapets / divider CED, windows with sills; opening {GATE_550_LM} "
                                                      f"at the east strip end named, not fixed (<1 %)"},
        "ROOF-430 (+4.30 annex, AT220)": {"ours": ours["AT220"], "after": ours["AT220"],
                                          "note": "35.728 = 11.8 + 1.3 + 1.4 + 3.2 + 6.4 + 0.7 + arc 1.728 + 2.9 + 6.3; "
                                                  "every run solid (window CFD with sill)"},
        "ROOF-970 (+9.70 roof, AT379)": {"ours": ours["AT379"], "after": r6(at379_after),
                                         "note": "65.14 = 18.87 + 11.6 + 6.57 + 6.6 + 8.1 + 2.1 + 4.2 + 7.1; + rings 27.782; "
                                                 "- door D115 1.000"},
        "ROOF-1390 (+13.90 top roof)": {"ours": ours["TOP"], "after": ours["TOP"],
                                        "note": "28.30 inner parapet + DOME-3 ring 13.855 (ESTIMATE, no roof plan, Q-34)"},
        "POOL-COURT +5.50 (open sky, window wall, ledge)": {"ours": r6(ours["POOL"] + ours["POOL_WIN"] + ours["LEDGE"]),
                                                            "after": r6(pool),
                                                            "note": "ledge 3.528 -> 0.552 (glazing 2.977 = transition)"},
    }
    summary = {
        "freelancer": {"row": "waterproofing sheet, 'roofs and annexes': 194.00 lm, 285.00 m2, x1.00, no sub-rows (re-read "
                              "this run with the Drive text reader)", "lm": FREELANCER_UPTURN_LM},
        "ours_before_lm": r6(total_before), "ours_after_lm": r6(total_after),
        "before_vs_freelancer_pct": round(100 * (total_before - FREELANCER_UPTURN_LM) / FREELANCER_UPTURN_LM, 1),
        "after_vs_freelancer_pct": round(100 * gap / FREELANCER_UPTURN_LM, 1),
        "fixed_before_to_after_lm": {k: r6(v) for k, v in before_split.items()},
        "causes_ours_minus_his_lm": {k: r6(v) for k, v in causes.items()},
        "like_for_like_lm": {"ours_walls_only_four_roofs": r6(inner4 - DOOR_970["gap_m"]), "his_H1": FREELANCER_UPTURN_LM,
                             "pct": round(100 * (inner4 - DOOR_970["gap_m"] - FREELANCER_UPTURN_LM) / FREELANCER_UPTURN_LM, 1)},
        "per_run": per_run,
        "named_not_fixed": {"terrace east-strip end opening (C9E / CA0 / CA3)": GATE_550_LM,
                            "window openings on roof edges taken as solid wall below a sill (sills not printed per "
                            "window; T-522 printed '84' on the one checked)": r6(WINDOWS_ON_ROOF_EDGES_LM)},
        "blank_lines": {"roof upturn family before": 0, "after": 0},
        "transition_lines_added": 3,
        "largest_run_for_the_checker": "ROOF-970 boundary 65.14 lm by hand (18.87 + 11.6 + 6.57 + 6.6 + 8.1 + 2.1 + 4.2 + "
                                       "7.1), door gap 1280 end to 1281 start = 1.000",
    }
    out = {"schema": "DELIVERY_FIX_ROWS_V1", "task": "T-794", "candidate_version": "ARCH_TAKEOFF_V3.0.85",
           "rule": "ROOF_UPTURN_WALLS_ONLY (owner Q-24 'as the bathrooms' + Q-35 C walls only; R-T522-1 frame = "
                   "transition); no new rule version",
           "inputs": {"index": "LINE_INDEX_V3_0_85.json", "roof_faces": "research/agents_t321/ALSENAN_ROOF_LAYERS_INPUT.json",
                      "ledge_split": "research/agents_t522 / agents_t529 (merged)",
                      "dxf_reread": "Drive 'Alsenan chalet project' P7757_DXF_COMPRESSED.zip handles 1280 1281 12BA "
                                    "(D115) 1288 1291 1285 12A7 1278 12B9 12C9 AE1 AE2 AE3 CF0 D0A B5D BC2 B5F C92 B60 "
                                    "BDB BDC C9E CA0 CA3 ADF CFD B3A CEC CED B25 B33 (dimensions only)"},
           "summary": summary, "rows": rows, "new_lines": new}
    print(json.dumps(summary, indent=1))
    if write:
        os.makedirs(OUT, exist_ok=True)
        with open(os.path.join(OUT, "FIX_ROWS.json"), "w") as f:
            json.dump(out, f, indent=1)
            f.write("\n")
    return out


if __name__ == "__main__":
    main(write="--write" in sys.argv)
