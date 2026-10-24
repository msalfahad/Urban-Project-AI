"""T-240 WP1 (V3.0.14): the project inputs of ARCH_TAKEOFF_V3.0.14 (URBAN_V3014_INPUTS_V1) for the development villa.
Research code; it reads the checker-merged T-223 / T-218 ledgers as committed and changes none of their quantities. No
coordinates, no names, no drawing content: references are P7757.dxf entity handles (hex) or printed dimensions, as the
merged ledgers give them.

FLOOR_SCOPE, from T-223 (MERGED 48d1d846, Verifier 2026-10-23 23:13 UTC: Gate A PASS; own curved room = engine, 'GF
side passage 5.640 m2 exterior, the 0.280 strip is the boundary-wall top') on T-218 (MERGED 0a622a86, Verifier
2026-10-23 14:30 UTC: the doorway-strip classes UP-DOOR-CLS-005 / UP-THR-001) and the Checker's own floor re-measure
(T-180 floor batches 21:15 / 22:05: the 1F dressing 1.650 x 1.800 = 2.970 m2 re-measured face to face):
  ENTER_FLOOR  1F dressing 1F-RFFE7AF (faces B03 + B04 / B00 / B20 / AD4 + AD5, dim EE9 1650; open passage OP-011,
               door OP-019; inside only the layer-5 joinery box B0A / BE3; no fixture, no drain on the 1F drainage
               plan): INTERIOR, DRY, 2.970 m2, finish material HELD (the DRY class rests on the absence of fixtures
               and T-218's drainage-plan read; never the bedroom's material);
  TO_THRESHOLD 1F OP-007 (1.00 x 0.20, lift landing, jambs B96 / B97), 2F OP-002 (1.00 x 0.20, lift landing),
               2F OP-001 (1.00 x 0.15, exterior sill to the +9.70 roof): 0.550 m2 out of porcelain into ARCH.THRESHOLD,
               HELD with the area kept;
  TO_OUTDOOR   GF side passage 1.200 x 4.700 = 5.640 m2 (west A2 / A3, east 9F / A0 / A1, boundary wall 105 / 106,
               0 lines across the mouth 120 / 15A): EXTERIOR by owner Q-67 A (condition met, Checker 2026-10-20
               21:05); retired: the two untyped spaces 3.600 + 1.560 and the mouth strip GF OP-007 0.240 (porcelain);
               the 1.20 x 0.20 band 0.240 m2 no engine line carries is named (T-223 s.2, cause not traced); finish
               porcelain / ceramic by the owner's sides rule (OWNER_RULE_OUTDOOR_FLOORS_2026-10-21), ASSUMED -
               OWNER-APPROVED;
  NO_FLOOR     GF OP-001 0.280 m2 porcelain strip = the top of the solid boundary wall (lines 105 / 106 run the full
               width; ENGINE DEFECT: the layer-5 wall read as a 1.40 m passage) and its ARCH.THRESHOLD twin (BLOCKED).
WP2 (wp2_records, the Checker's 2026-10-24 01:12 GF batch: own width x wall thickness, geometry = engine 0.0 %):
  TO_THRESHOLD GF OP-011 lift landing 0.200 and the exterior sills OP-005 0.180, OP-008 0.200, OP-009 0.200, OP-013
               0.180, OP-021 0.400 (1.160): 1.360 m2 out of porcelain into ARCH.THRESHOLD, HELD with the area kept;
  NO_OPENING_SPLIT GF OP-003 2.244 (+ its blocked threshold twin): an edge line with no opening, placed along its
               11.22 m: side passage 1.20 (0.240 = the passage's named missing piece, counted once in the outdoor line),
               its east wall 0.20 (0.040 no floor), pantry 3.00 (0.600 wet, Q-37 A), garden band 6.82 (1.364 HELD with
               the band, P-2);
  TO_WET       the pantry pieces by Q-37 A: GF-RC06FED 2.800 whole, and the part of the open face GF-RC99C2A inside the
               printed 4.50 x 3.00 box (8.954867 from the engine face polygon; closure 13.500 - 0.0452 column - 2.800 -
               0.600 - 1.100 doorway zone = 8.9548, residual 0.0001; the Checker's '8.925' leaves -0.030 in its own box).
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
T223 = ROOT / "research/agents_t223"
T218 = ROOT / "research/agents_t218"
POR, SP, THR = "FIN.FLOOR.PORCELAIN", "ARCH.SPACE", "ARCH.THRESHOLD"
CHECKER_FLOOR = "Checker T-180 floor batches 2026-10-23 21:15 / 22:05 (own face-to-face re-measure)"


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _src(f, task, mc, run):
    return {"file": f, "sha256": _sha(ROOT / f), "task": task, "merge_commit": mc, "checker_run": run}


def _ref(eid, item, floor, carried, why):
    return {"item_code": item, "floor": floor, "element_id": eid, "unit": "m2", "carried": carried, "why": why}


def records():
    return [
        {"id": "1F-DRESSING-1F-RFFE7AF", "kind": "ENTER_FLOOR", "floor": "1F", "dims": [[1.65, 1.80]],
         "area_m2": 2.97, "class": "INTERIOR", "wet_dry": "DRY", "area_status": "VERIFIED", "material_status": "HELD",
         "material_why": "no finish printed for the dressing; the DRY class rests on the absence of fixtures and the "
                         "T-218 drainage-plan read (sanitary-7757.pdf p.2), not independently re-read; the bedroom's "
                         "material is never borrowed (D-C3)",
         "evidence": "enclosed; open passage OP-011 1.000 to the 3.80 x 4.30 bedroom, door OP-019 0.800 to its bath; "
                     "inside only the layer-5 box B0A / BE3 (0.50 x 1.80, no wall line: joinery, floor continues); 0 "
                     "inserts; no fixture; no drain on the 1F drainage plan",
         "drawing_reference": "P7757.dxf faces B03 + B04 / B00 / B20 / AD4 + AD5, dim EE9 1650; box B0A / BE3",
         "verified_by": CHECKER_FLOOR + " (2.970 m2) + Verifier 2026-10-23 23:13 (T-223 Gate A)",
         "line": _ref("1F-RFFE7AF:space", SP, "1F", 2.97,
                      "an enclosed interior face typed nothing: ARCH.SPACE PROVISIONAL in no floor line (T-223)")},
        {"id": "1F-OP-007-LIFT", "kind": "TO_THRESHOLD", "floor": "1F", "opening": "OP-007", "class": "LIFT_LANDING",
         "rule": "UP-DOOR-CLS-005 / UP-ELEV-SCHED-001", "dims": [[1.00, 0.20]], "area_m2": 0.2,
         "evidence": "living / lift shaft, jambs B96 / B97 (T-218 strip class, T-223 s.3)",
         "drawing_reference": "P7757.dxf jambs B96 / B97", "verified_by": "T-218 Gate A (class); area DRAWING-CONFIRMED",
         "line": _ref("1F-STRIP-OP-007:doorway strip", POR, "1F", 0.2,
                      "a lift landing sill carried as porcelain floor")},
        {"id": "2F-OP-002-LIFT", "kind": "TO_THRESHOLD", "floor": "2F", "opening": "OP-002", "class": "LIFT_LANDING",
         "rule": "UP-DOOR-CLS-005 / UP-ELEV-SCHED-001", "dims": [[1.00, 0.20]], "area_m2": 0.2,
         "evidence": "stair room / lift shaft (T-218 strip class, T-223 s.3)",
         "drawing_reference": "P7757.dxf 2F lift landing opening OP-002 (T-218 STRIPS_T218.csv)",
         "verified_by": "T-218 Gate A (class); area DRAWING-CONFIRMED",
         "line": _ref("2F-STRIP-OP-002:doorway strip", POR, "2F", 0.2,
                      "a lift landing sill carried as porcelain floor")},
        {"id": "2F-OP-001-SILL", "kind": "TO_THRESHOLD", "floor": "2F", "opening": "OP-001", "class": "EXTERIOR_SILL",
         "rule": "UP-THR-001 (dry doorways between interior spaces only; an exterior sill is by specification)",
         "dims": [[1.00, 0.15]], "area_m2": 0.15, "evidence": "stair room / +9.70 roof (T-218, T-223 s.3)",
         "drawing_reference": "P7757.dxf 2F roof door OP-001 (T-218 STRIPS_T218.csv)",
         "verified_by": "T-218 Gate A (class); area DRAWING-CONFIRMED",
         "line": _ref("2F-STRIP-OP-001:doorway strip", POR, "2F", 0.15,
                      "an exterior sill carried as interior porcelain floor")},
        {"id": "GF-SIDE-PASSAGE", "kind": "TO_OUTDOOR", "floor": "GF", "dims": [[1.20, 4.70]], "area_m2": 5.64,
         "decision": "owner Q-67 A (open-air side passage; condition met, Checker 2026-10-20 21:05; mouth re-read "
                     "T-223: 0 lines on any layer across it)",
         "material_status": "ASSUMED - OWNER-APPROVED",
         "material_source": "OWNER_RULE_OUTDOOR_FLOORS_2026-10-21 (sides: porcelain / ceramic, not split by the rule)",
         "area_status": "VERIFIED",
         "evidence": "1.200 x 4.700 own re-read (T-123, T-223); west A2 / A3 (door 19C), east 9F / A0 / A1 (windows "
                     "3BE / 3CB), boundary wall 105 / 106 closed, mouth between the ends of 120 / 15A open",
         "drawing_reference": "P7757.dxf A2 / A3 / 9F / A0 / A1, 105 / 106, 120 / 15A",
         "verified_by": "Verifier 2026-10-23 23:13 (own: GF side passage 5.640 m2 exterior)",
         "lines": [_ref("GF-RF002DC:space", SP, "GF", 3.6, "a piece of the exterior side passage, untyped space"),
                   _ref("GF-R7B7A5D:space", SP, "GF", 1.56, "a piece of the exterior side passage, untyped space"),
                   _ref("GF-STRIP-OP-007:doorway strip", POR, "GF", 0.24,
                        "the passage mouth carried as interior porcelain")],
         "missing": {"m2": 0.24, "carried_by": "GF-OP-003-NO-OPENING",
                     "why": "the 1.20 x 0.20 band inside the drawn passage between the two space pieces is carried by "
                            "no space line: the engine carried it inside the OP-003 'strip' (an edge line with no "
                            "opening, WP2 record GF-OP-003-NO-OPENING, part 'passage'), which is retired; it is "
                            "counted once, here"}},
        {"id": "GF-OP-001-WALLTOP", "kind": "NO_FLOOR", "floor": "GF",
         "evidence": "lines 105 / 106 (86 doubles 105) run the full 1.200 width: a solid boundary wall drawn on layer "
                     "5, read by the engine as a 1.40 m passage",
         "drawing_reference": "P7757.dxf 105 / 106 / 86", "verified_by": "Verifier 2026-10-23 23:13 (the 0.280 strip "
                                                                       "is the boundary-wall top)",
         "line": _ref("GF-STRIP-OP-001:doorway strip", POR, "GF", 0.28,
                      "the top of the solid boundary wall: no opening, no floor"),
         "twin": _ref("GF-STRIP-OP-001:unattributed strip", THR, "GF", None,
                      "the threshold twin of a strip that is no opening (billed the same strip twice)")},
    ] + wp2_records()


CHECKER_GF_STRIPS = ("Checker 2026-10-24 01:12 UTC (T-180 floor batch 'the 11 GF strips': own width x wall thickness "
                     "from the jamb ends and both wall faces, every geometry = engine 0.0 %; class by the spaces each "
                     "strip joins, the merged T-218 ruling applied to GF)")
Q37A = ("owner Q-37 A (2026-10-19 16:40: the pantry is waterproofed within its printed 4.50 x 3.00 like a kitchen; "
        "pantry on the wet list, drain FD on the GF drainage plan): wet floor")


def _sill(op, w, jambs, joins):
    return {"id": f"GF-{op}-SILL", "kind": "TO_THRESHOLD", "floor": "GF", "opening": op, "class": "EXTERIOR_SILL",
            "rule": "UP-THR-001 (dry doorways between interior spaces only; an exterior sill is by specification)",
            "dims": [[w, 0.20]], "area_m2": round(w * 0.20, 6),
            "evidence": f"{joins}: one side exterior (Checker 01:12, T-218 class)",
            "drawing_reference": f"P7757.dxf jambs {jambs}", "verified_by": CHECKER_GF_STRIPS,
            "line": _ref(f"GF-STRIP-{op}:doorway strip", POR, "GF", round(w * 0.20, 6),
                         "an exterior-door sill carried as interior porcelain floor")}


def wp2_records():
    """T-240 WP2: the T-218 strip class on the GF strips (the Checker's 01:12 batch; GF OP-001 / OP-007 were WP1),
    the strip with no opening (GF OP-003) placed part by part, and the Q-37 A wet class on the pantry pieces."""
    return [
        {"id": "GF-OP-011-LIFT", "kind": "TO_THRESHOLD", "floor": "GF", "opening": "OP-011", "class": "LIFT_LANDING",
         "rule": "UP-DOOR-CLS-005 / UP-ELEV-SCHED-001", "dims": [[1.00, 0.20]], "area_m2": 0.2,
         "evidence": "open room / lift shaft (Checker 01:12: carried as porcelain, not as a threshold line)",
         "drawing_reference": "P7757.dxf jambs BB / 20D", "verified_by": CHECKER_GF_STRIPS,
         "line": _ref("GF-STRIP-OP-011:doorway strip", POR, "GF", 0.2, "a lift landing sill carried as porcelain floor")},
        _sill("OP-005", 0.90, "11E / 11D", "driver room / exterior"),
        _sill("OP-008", 1.00, "158 / 159", "main entrance / exterior"),
        _sill("OP-009", 1.00, "138 / 139", "Majlis / court"),
        _sill("OP-013", 0.90, "26E / 26F", "stair hall / north court"),
        _sill("OP-021", 2.00, "9D / 9E", "D200 / porch"),
        {"id": "GF-OP-003-NO-OPENING", "kind": "NO_OPENING_SPLIT", "floor": "GF",
         "evidence": "the 11.22 m 'passage' is the garden band's north edge line (layer-2 A8 / layer-5 A9 / layer-2 4B4, "
                     "0.20) carried west across the pantry and the side passage: no opening anywhere along it (Checker "
                     "01:12; T-175 P-GF-04 'not a building opening'). Placed along its length, west to east, against "
                     "the engine's own faces: side passage 1.20 (between the two passage space pieces), the passage's "
                     "east wall 0.20, pantry 3.00 (to the layer-5 line B3 / AD), garden band 6.82",
         "drawing_reference": "P7757.dxf A8 / A9 / 4B4; B3 / AD (pantry east edge); passage pieces GF-RF002DC / "
                              "GF-R7B7A5D",
         "verified_by": CHECKER_GF_STRIPS + "; split 1.364 band / 0.600 pantry / 0.280 passage and its wall",
         "line": _ref("GF-STRIP-OP-003:doorway strip", POR, "GF", 2.244,
                      "an edge line across an open zone carried as an 11.22 m doorway strip"),
         "twin": _ref("GF-STRIP-OP-003:unattributed strip", THR, "GF", None,
                      "the threshold twin of a strip that is no opening (billed the same strip twice)"),
         "parts": [
             {"part": "passage", "dims": [[1.20, 0.20]], "area_m2": 0.24, "to": "COUNTED_IN",
              "record": "GF-SIDE-PASSAGE"},
             {"part": "wall", "dims": [[0.20, 0.20]], "area_m2": 0.04, "to": "NO_FLOOR",
              "why": "the body of the passage's east wall (passage face to pantry face): wall, no floor"},
             {"part": "pantry", "dims": [[3.00, 0.20]], "area_m2": 0.6, "to": "TO_WET", "decision": Q37A},
             {"part": "band", "dims": [[6.82, 0.20]], "area_m2": 1.364, "to": "HELD_WITH",
              "held_with": "the GF garden band (P-2: 1.30 x 10.82 = 13.986 m2, HELD outside the internal key)",
              "why": "inside the printed band 150 (the 0.20 edge line is part of it); the band is HELD (P-2)"}]},
        {"id": "GF-PANTRY-RC06FED", "kind": "TO_WET", "floor": "GF", "decision": Q37A, "whole": True,
         "move_m2": 2.800001, "area_status": "DRAWING-CONFIRMED",
         "evidence": "the whole face lies inside the printed pantry box (engine face clipped to the box = its area)",
         "drawing_reference": "P7757.dxf pantry printed 450 / 300; east edge layer-5 B3 / AD",
         "verified_by": "Checker 2026-10-24 01:12 (GF open face partition: geometry agrees +0.002 %; class open)",
         "downstream": ["waterproofing: the pantry membrane (Q-37 A) is its own line, unchanged here"],
         "line": _ref("GF-RC06FED:floor", POR, "GF", 2.800001, "a pantry piece carried as dry porcelain")},
        {"id": "GF-PANTRY-RC99C2A-PART", "kind": "TO_WET", "floor": "GF", "decision": Q37A,
         "move_m2": 8.954867, "area_status": "DRAWING-CONFIRMED",
         "area_basis": "the engine face GF-RC99C2A (its own polygon) clipped to the printed pantry box 3.00 x 4.50 "
                       "(west wall face to the layer-5 line B3 / AD, south wall face + 4.50); no stair flight lies in "
                       "the box, so the drawn-tread deduction is untouched",
         "closure": {"box_m2": 13.5, "basis": "printed 450 x 300; every other piece in it as the Checker measured it",
                     "terms": {"column 2FAC notch (Checker own box 13.4548)": 0.0452,
                               "GF-RC06FED (moved whole, record GF-PANTRY-RC06FED)": 2.800001,
                               "OP-003 strip part 'pantry' 3.00 x 0.20": 0.6,
                               "doorway zone (Checker partition 01:12, RFI, stays as carried)": 1.1}},
         "evidence": "Q-37 A binds the pantry WET within its printed box; the open face's part in the box is wet floor, "
                     "the rest stays dry porcelain. The Checker's '8.925' does not close its own box (8.925 + 2.800 + "
                     "1.100 + 0.600 = 13.425 vs 13.4548, -0.030); the engine geometry does (residual 0.0001)",
         "drawing_reference": "P7757.dxf pantry printed 450 / 300; B3 / AD; column 2FAC",
         "verified_by": "Checker 2026-10-24 01:12 (pieces re-measured; class open; part figure re-measured at WP4)",
         "downstream": ["waterproofing: the pantry membrane (Q-37 A) is its own line, unchanged here"],
         "line": _ref("GF-RC99C2A:floor", POR, "GF", 118.733284,
                      "the pantry part of the open dining / living face carried as dry porcelain")},
    ]


DECLARED = {"floor_internal_in_m2": 3.57, "floor_internal_out_m2": 4.674, "threshold_m2": 1.91, "outdoor_m2": 5.64,
            "no_floor_m2": 0.32, "dry_to_wet_m2": 11.754868, "held_with_m2": 1.364, "counted_in_m2": 0.24,
            "floor_internal_delta_m2": -1.104}


def inputs(project_id):
    pc = {"piece": "FLOOR_SCOPE",
          "source": _src("research/agents_t223/summary.json", "T-223", "48d1d846",
                         "Verifier 2026-10-23 23:13 UTC (Gate A PASS)"),
          "sources": [_src("research/agents_t223/FACE_TYPING_T223.csv", "T-223", "48d1d846",
                           "Verifier 2026-10-23 23:13 UTC"),
                      _src("research/agents_t223/STRIPS_T223.csv", "T-223", "48d1d846",
                           "Verifier 2026-10-23 23:13 UTC"),
                      _src("research/agents_t218/STRIPS_T218.csv", "T-218", "0a622a86",
                           "Verifier 2026-10-23 14:30 UTC (Gate A PASS)")],
          "records": records(), "declared": DECLARED}
    sys.path.insert(0, str(ROOT / "research/agents_t193"))
    import t193_inputs as L7   # noqa: E402  (the V3.0.7 guard inputs, unchanged, as V3.0.8 .. V3.0.13)
    g = dict(L7.inputs(project_id)["guard"], new_records=[])
    return {"schema": "URBAN_V3014_INPUTS_V1", "project": project_id, "pieces": [pc], "guard": g}
