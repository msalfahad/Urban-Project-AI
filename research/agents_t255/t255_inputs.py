"""T-255: the URBAN_V3019_INPUTS_V1 of the development villa, line id by line id, from checker readings and merged
ledgers only:

  F-T254-01 (Verifier 2026-10-25 16:00 UTC, board agents/control, closed from the drawing): the ring ground beam
      between ARC 157 (r 2.250) and ARC 158 (r 2.550), D 0.95, closes on its drawn faces: NORTH outer arc 158 -> beam
      face LINE 7C3 -> neck column 17C0 west + south faces -> inner arc 157; SOUTH inner arc 157 at 17BD's north-east
      corner, outer arc 158 through 17BD's west face (17BD north + west faces); crown column 17BA deducted. Own net
      1.83888 m2 x 0.95 = 1.746943 m3; chord-closed reading 1.82582 m2 (13:35 figure 1.8258); drawn - chord = the north
      triangle 0.01306 m2 (in no other line); the neck parts 0.06585 m2 the chord already left out.
  T-254 MERGED 7c49e890 (Verifier 2026-10-25 13:35, Gate B PASS): the ring line L-7076482d75ca42691468 carried 1.7349
      DRAWING-CONFIRMED (T-242 net plan 1.8262 m2 x D 0.95).
  T-232 MERGED a0cd9bbc (Gate B 2026-10-24 02:44), T-249 MERGED 2a2d15af (Gate A 02:48), T-250 MERGED 47390c9b (Gate A
      2026-10-24 10:40), T-285 MERGED e418c5e0 (Gate A 2026-10-25 01:41), T-292 r2 MERGED a9754a67 (Gate A r2 2026-10-25
      15:32): the opening trace of W03 and W18 (which candidate line carries each, or why none does).

This worker's own drawing read (private copy 'ST7757 dxf.dxf' 9f9d1179, shapely, 40 000 points per arc) reproduces the
Checker: drawn net 1.838859 m2 (1.746916 m3), chord net 1.825841 m2, triangle 0.013018 m2, crown column 0.089559 m2;
the 0.000028 m2 (0.000027 m3, 0.0015 %) between the two is the Checker's named 2 mm sliver under 17BD (0.00002 m2) and
rounding. The line carries the Checker's figure (lane I wires what the Checker verified). No coordinate is written here.

The opening trace (W03, W18) is filled by `trace()` from the V3.0.18 lines of the run (research/agents_t255/
T-255_RING_AND_OPENING_TRACE.md section 3 gives the line-by-line reading); `build()` asserts every cited ledger's sha.

    python3 -I research/agents_t255/t255_inputs.py > <scratch>/v3019_inputs.json
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
T254 = ROOT / "research/agents_t254/T-254_BASIS_CORRECTION.md"
T249 = ROOT / "research/agents_t249/OPENINGS_T249.csv"
T250 = ROOT / "research/agents_t250/T-250_FACE_CROSSWALK.md"
T285 = ROOT / "research/agents_t285/T-285_REGISTER_V3.md"
T292 = ROOT / "research/agents_t292/T-292_FACE_TO_LINE_LEDGER.md"
T232 = ROOT / "research/agents_t232/T-232_ARCH_V3010.md"
DC = "DRAWING-CONFIRMED"

RING_LINE = "L-7076482d75ca42691468"
RING_ELEMENT = "P-C:GROUND_BEAMS:GROUND:BAND0043"
D = 0.95
CHECKER_VALUE = 1.746943          # F-T254-01 own (1.83888 m2 x 0.95, incl. the 2 mm sliver)
CHECKER_DRAWN_M2 = 1.838887       # = 1.746943 / 0.95 to 6 dp (Checker printed 1.83888)
CHECKER_CHORD_M2 = 1.82582
CHECKER_TRIANGLE_M2 = 0.01306
CHECKER_NECK_PARTS_M2 = 0.06585   # 17C0 0.01205 + 17BD 0.05380: left out by both readings
CHECKER_CROWN_M2 = 0.08961        # 17BA inside the band: deducted by both readings
CARRIED = 1.7349                  # V3.0.17 / V3.0.18 (T-242 1.8262 m2 x 0.95)
OWN = {"drawn_net_m2": 1.838859, "value_m3": 1.746916, "chord_net_m2": 1.825841, "triangle_m2": 0.013018,
       "crown_column_m2": 0.089559, "neck_parts_m2": 0.065877}
F_T254_01 = "Verifier 2026-10-25 16:00 UTC F-T254-01 (closed from the drawing; own ezdxf read of the handles)"


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def sources():
    return [
        {"file": "docs/agents/BOARD.md (agents/control: Verifier 2026-10-25 16:00 UTC note, F-T254-01)",
         "sha256": "verdict-text", "task": "F-T254-01",
         "merge_commit": "none: a checker reading on the board (the correction belongs to this lane I package)",
         "checker_run": F_T254_01},
        {"file": "research/agents_t254/T-254_BASIS_CORRECTION.md", "sha256": _sha(T254), "task": "T-254",
         "merge_commit": "7c49e890", "checker_run": "Verifier 2026-10-25 13:35 UTC (Gate B PASS)"},
        {"file": "research/agents_t232/T-232_ARCH_V3010.md", "sha256": _sha(T232), "task": "T-232",
         "merge_commit": "a0cd9bbc", "checker_run": "Verifier 2026-10-24 02:44 UTC (Gate B PASS)"},
        {"file": "research/agents_t249/OPENINGS_T249.csv", "sha256": _sha(T249), "task": "T-249",
         "merge_commit": "2a2d15af", "checker_run": "Verifier 2026-10-24 02:48 UTC (Gate A PASS)"},
        {"file": "research/agents_t250/T-250_FACE_CROSSWALK.md", "sha256": _sha(T250), "task": "T-250",
         "merge_commit": "47390c9b", "checker_run": "Verifier 2026-10-24 10:40 UTC (Gate A PASS, own W03 re-walk)"},
        {"file": "research/agents_t285/T-285_REGISTER_V3.md", "sha256": _sha(T285), "task": "T-285",
         "merge_commit": "e418c5e0", "checker_run": "Verifier 2026-10-25 01:41 UTC (Gate A PASS; 1F-W00 own 12.935)"},
        {"file": "research/agents_t292/T-292_FACE_TO_LINE_LEDGER.md", "sha256": _sha(T292), "task": "T-292",
         "merge_commit": "a9754a67", "checker_run": "Verifier 2026-10-25 15:32 UTC (Gate A r2 PASS)"},
    ]


def ring_record():
    t = T254.read_text(encoding="utf-8")
    row = f"| {RING_LINE} | GROUND_BEAM | GROUND | GB_MAIN_EXTERIOR_IN_INTERIOR_LINES | 1.13162 | 1.13162 | 1.7349 | {DC} |"
    if row not in t:
        raise SystemExit("T-254 ledger: the ring line row is not the merged one (stale or edited ledger)")
    assert abs(CHECKER_CHORD_M2 + CHECKER_TRIANGLE_M2 - 1.83888) < 1e-9
    assert abs(round(CHECKER_DRAWN_M2 * D, 6) - CHECKER_VALUE) < 1e-9
    return {
        "kind": "END_CLOSURE", "line_id": RING_LINE, "item_code": "STR.CONC.GROUND_BEAM", "element_id": RING_ELEMENT,
        "task": "F-T254-01", "group": "RING_END_CLOSURE",
        "physical_element": "curved exterior ground beam between inner arc 157 (r 2.250) and outer arc 158 (r 2.550), "
                            "width 0.30, D 0.95 (two printed levels, T-254 Gate B)",
        "before": {"evidence_state": "SOURCE_DERIVED", "measured_net": CARRIED},
        "status": DC, "value": CHECKER_VALUE,
        "pieces": [{"id": "GB-RING-BAND0043-DRAWN", "value": CHECKER_VALUE, "status": DC}],
        "formula": (f"net plan closed on the drawn faces {CHECKER_DRAWN_M2} m2 (annulus 157 / 158, north end 158 -> 7C3 "
                    f"-> 17C0 west + south -> 157, south end 157 at 17BD NE -> 17BD north + west -> 158; crown column "
                    f"17BA {CHECKER_CROWN_M2} deducted) x D {D} = {CHECKER_VALUE} m3"),
        "retired": {"reading": "CHORD (ends closed by a chord between the arc end points; T-242 / T-254)",
                    "value": CARRIED},
        "arc_band": {
            "end_a": {"reading": "DRAWN_FACES", "closing_faces": ["ARC 158 end on LINE 7C3", "LINE 7C3 to 17C0 west",
                                                                  "17C0 west face", "17C0 south face"]},
            "end_b": {"reading": "DRAWN_FACES", "closing_faces": ["17BD north face", "17BD west face"]},
            "drawn_net_m2": CHECKER_DRAWN_M2, "retired_net_m2": CHECKER_CHORD_M2, "depth_m": D,
            "closing_pieces": [{"id": "BAND0043-N-TRIANGLE", "m2": CHECKER_TRIANGLE_M2, "owned_by": RING_LINE,
                                "where": "between the chord, beam face 7C3 and 17C0's west face: not in the 7C3 / 170 "
                                         "band (outside the face), not in 17C0"}],
            "excluded_pieces": [],
            "columns_in_band": [{"id": "17BA", "m2": CHECKER_CROWN_M2, "deducted": True, "trade": "STR.CONC.COLUMN"}],
            "columns_at_ends": [{"id": "17C0", "m2_left_out_by_chord": 0.01205, "deducted": True},
                                {"id": "17BD", "m2_left_out_by_chord": 0.05380, "deducted": True}],
            "retired_residual": {"m2": round(CARRIED / D - CHECKER_CHORD_M2, 7),
                                 "cause": "the carried 1.7349 = T-242 net plan 1.8262 m2 (its own polygon, rounded) x "
                                          "0.95; the chord re-measured by the Checker (13:35, 16:00) is 1.82582 m2 "
                                          "(this worker 1.825841): the carried reading is +0.00039 m2 above it, inside the retired reading, not a "
                                          "drawn piece"},
            "own_reproduction": dict(OWN, residual_vs_checker_m3=round(OWN["value_m3"] - CHECKER_VALUE, 6),
                                     residual_cause="the Checker's 2 mm drawing-gap sliver under 17BD (0.00002 m2) "
                                                    "and rounding; immaterial (0.0015 %)")},
        "verified_by": None,
        "printed": "'ST7757 dxf.dxf' (Drive 'Alsenan chalet project'): ARC 157 / 158, LINE 7C3 / 170, S-COL.BON "
                   "17C0 / 17BD / 17BA; depth D 0.95 as T-254 (two printed levels)",
        "downstream": ["formwork of the ring (T-293 / T-199: the triangle's side faces follow the drawn faces)",
                       "buried waterproofing of the ring (T-276: faces on the drawn closure)",
                       "excavation / backfill around the ring (not in the candidate)"],
    }


def build(trace_rows=None):
    doc = {"schema": "URBAN_V3019_INPUTS_V1", "project": None, "sources": sources(), "records": [ring_record()],
           "opening_trace": list(trace_rows if trace_rows is not None else TRACE)}
    return doc


TRACE = []     # filled below (section 3 of the report), asserted against the V3.0.18 lines by the module


if __name__ == "__main__":
    json.dump(build(), sys.stdout, ensure_ascii=False, indent=1)
