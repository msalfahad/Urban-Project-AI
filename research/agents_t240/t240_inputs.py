"""T-240 WP1 (V3.0.13): the project inputs of ARCH_TAKEOFF_V3.0.13 (URBAN_V3013_INPUTS_V1) for the development villa.
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
Not in WP1 (named for WP2): GF OP-003 is also carried by a porcelain strip AND a blocked threshold twin (Checker 01:12:
'OP-003 has no opening'); the V3.0.13 run lists it as a pre-existing strip duplicate.
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
         "missing": {"m2": 0.24, "why": "the 1.20 x 0.20 band at the B5 beam / 1F wall position inside the drawn "
                                        "passage has no engine line (no line on any layer there; T-223 s.2, cause in "
                                        "the engine not traced)"}},
        {"id": "GF-OP-001-WALLTOP", "kind": "NO_FLOOR", "floor": "GF",
         "evidence": "lines 105 / 106 (86 doubles 105) run the full 1.200 width: a solid boundary wall drawn on layer "
                     "5, read by the engine as a 1.40 m passage",
         "drawing_reference": "P7757.dxf 105 / 106 / 86", "verified_by": "Verifier 2026-10-23 23:13 (the 0.280 strip "
                                                                       "is the boundary-wall top)",
         "line": _ref("GF-STRIP-OP-001:doorway strip", POR, "GF", 0.28,
                      "the top of the solid boundary wall: no opening, no floor"),
         "twin": _ref("GF-STRIP-OP-001:unattributed strip", THR, "GF", None,
                      "the threshold twin of a strip that is no opening (billed the same strip twice)")},
    ]


DECLARED = {"floor_internal_in_m2": 2.97, "floor_internal_out_m2": 1.07, "threshold_m2": 0.55, "outdoor_m2": 5.64,
            "no_floor_m2": 0.28, "floor_internal_delta_m2": 1.9}


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
    import t193_inputs as L7   # noqa: E402  (the V3.0.7 guard inputs, unchanged, as V3.0.8 .. V3.0.12)
    g = dict(L7.inputs(project_id)["guard"], new_records=[])
    return {"schema": "URBAN_V3013_INPUTS_V1", "project": project_id, "pieces": [pc], "guard": g}
