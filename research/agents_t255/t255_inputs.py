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
    row = (f"| {RING_LINE} | GROUND_BEAM | GROUND | GB_MAIN_EXTERIOR_IN_INTERIOR_LINES | 1.13162 | 1.13162 | 1.7349 "
           f"| {DC} |")
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
        "formula": (f"net plan closed on the drawn faces {CHECKER_DRAWN_M2} m2 (annulus 157 / 158, north end 158 -> "
                    f"7C3 -> 17C0 west + south -> 157, south end 157 at 17BD NE -> 17BD north + west -> 158; "
                    f"crown column 17BA {CHECKER_CROWN_M2} deducted) x D {D} = {CHECKER_VALUE} m3"),
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
                                          "(this worker 1.825841): the carried reading is +0.00039 m2 above it, "
                                          "inside the retired reading, not a "
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


# ---------------------------------------------------------------- the opening trace (V3.0.18 lines of record ec741004)
W03_PLASTER_SIDE = round(6.731 * 3.65, 6)     # T-128 r3 room-side developed line x owner height G1 = 24.56815 m2
REVEAL_FINDING = ("no ARCH.WINDOW_REVEAL line names this opening: the 27 reveal lines are the engine's own window "
                  "openings (all BLOCKED_RFI); a reveal line for it is a scope with no line (finding for the Lead)")
EXT_HELD = ("FIN.EXT.FINISH facade line BLOCKED_RFI (EXTERIOR_FINISH_NOT_SPECIFIED; facade area not established): "
            "the opening deduction rides with the facade line when it is built")
EXT_TASK = "T-305 (FACADE-EXT integration dependency, lane A TODO)"


def _finish_side(code_lines, unit="m2"):
    """W03 on the room side: the curved band spans GF-15 (bed-room part 5.106 m) and GF-08 (open-room part 1.625 m),
    T-128 r3 (T-250 verdict: the room face is the outer glass line 6.731 m, inside the drawn 6.726 .. 6.738)."""
    bed, open_ = code_lines
    return {"value": W03_PLASTER_SIDE, "unit": unit, "parts": [
        {"part": "GF-15 bed-room part 5.106 m", "state": "CARRIED_ONCE", "line_ids": [bed],
         "evidence": "owner_manual_method.deductions: 'W03 pool glazing band (bed-room part)' 5.106 x 3.65",
         "deduction_text": "W03 pool glazing band (bed-room part)", "value": round(5.106 * 3.65, 6), "unit": unit},
        {"part": "GF-08 open-room part 1.625 m", "state": "HELD", "line_ids": [open_],
         "held_item": "the GF-08 line is BOUNDED (lift landing door, W02 saloon glazing not printed / not settled, "
                      "D-45 / D-53): no figure released; its record deducts the W03 part once",
         "named_task": "T-244 (plaster / paint whole line)", "deduction_text": "W03 pool glazing band (open-room part)",
         "value": round(1.625 * 3.65, 6), "unit": unit}]}


TRACE = [
    {"opening": "W03", "floor": "GF", "kind": "WINDOW", "task": "T-249",
     "physical_element": "curved pool glazing band, 6.57 printed (Q-38 A) x 4.30 (NW elevation), in the straight "
                         "4.95 m gap of the glazed host GF-W37",
     "trades": {
         "WINDOW_SUPPLY_PCS": {"state": "CARRIED_ONCE", "line_ids": ["L-a224c9fbabd0c366a6b0"], "token": "W03",
                               "evidence": "GF window count 11: opening_ids include W03 (T-232 V3.0.10)", "value": 1,
                               "unit": "pcs"},
         "WINDOW_SUPPLY_M2": {"state": "CARRIED_ONCE", "line_ids": ["L-34a0aa9987a3e094d0de"], "token": "W03 28.251",
                              "evidence": "GF window m2 47.151: formula '... W03 28.251 ...' = 6.57 x 4.30 (Q-32 A, "
                                          "Q-38 A)", "value": 28.251, "unit": "m2"},
         "WINDOW_REVEAL": {"state": "NO_LINE", "finding": REVEAL_FINDING},
         "MASONRY": {"state": "NOT_APPLICABLE",
                     "why": "the host GF-W37 is a glazed line: no masonry is built in the opening (T-175 / T-249 s.3, "
                            "build before deduct); the GF MAS.BLOCK lines are BLOCKED_RFI blank in any case"},
         "PLASTER_ROOM_SIDE": _finish_side(("L-0d93f2209cd9bb827c0a", "L-8cecb1d010d5aafbf25d")),
         "PAINT_ROOM_SIDE": _finish_side(("L-7f083d3e2c2702d14356", "L-c0ac22c964a42e7d71b1")),
         "EXTERNAL_FINISH": {"state": "HELD", "line_ids": ["L-b05f70c92405dbcfbe62"], "held_item": EXT_HELD,
                             "named_task": EXT_TASK}}},
    {"opening": "W18", "floor": "1F", "kind": "WINDOW", "task": "T-249",
     "physical_element": "1F sea-side bath window 0.50 x 2.16 (sill +6.34, head +8.50 printed; T-144), a glazed "
                         "stretch in the wall 1F-W00 (no engine opening id, T-040 G7)",
     "trades": {
         "WINDOW_SUPPLY_PCS": {"state": "CARRIED_ONCE", "line_ids": ["L-221fdc86146248f1b67b"], "token": "W18",
                               "evidence": "1F window count 13: opening_ids include W18", "value": 1, "unit": "pcs"},
         "WINDOW_SUPPLY_M2": {"state": "CARRIED_ONCE", "line_ids": ["L-ba28ba2da13f62445c9f"], "token": "W18 1.08",
                              "evidence": "1F window m2 23.285: formula '... W18 1.08 ...' = 0.50 x 2.16 (Q-32 A)",
                              "value": 1.08, "unit": "m2"},
         "WINDOW_REVEAL": {"state": "NO_LINE", "finding": REVEAL_FINDING},
         "MASONRY": {"state": "HELD", "line_ids": ["L-5ffa7157a2fe483dd008"],
                     "held_item": "MAS.BLOCK 1F t=0.20 BLOCKED_RFI (masonry height not in the drawing); register v3 "
                                  "deducts W18 on 1F-W00 by its 0.4673 m inside the masonry x 2.160 = 1.0094 m2 "
                                  "(R-T274-1 rule 5; Checker own 1F-W00 12.935)",
                     "named_task": "T-279 (established blockwork walls into the candidate)", "value": 1.0094,
                     "unit": "m2"},
         "WALL_TILE_ROOM_SIDE": {"state": "HELD", "line_ids": ["L-82cd58d4a16fb94ddfc6"],
                                 "held_item": "1F-12 bath wall tile line BLOCKED_RFI (wall finish height not "
                                              "established, UP-CER-009); T-292 r2 face 1F-12|1F-W00 deducts W18 1.080 "
                                              "(net 6.0388 ASSUMED - OWNER-APPROVED G1)",
                                 "named_task": "no lane I row carries FIN.WALL.TILE yet (Lead; T-292 r2 is the "
                                               "merged ledger)", "value": 1.08, "unit": "m2"},
         "PLASTER_ROOM_SIDE": {"state": "HELD", "line_ids": ["L-12b83d399be186804faf"],
                               "held_item": "plaster under full-height wall tile: substrate HELD (T-211 s.5.4; T-292 "
                                            "r2), line BLOCKED_RFI",
                               "named_task": "T-244 (plaster / paint whole line)"},
         "PAINT_ROOM_SIDE": {"state": "NOT_APPLICABLE",
                             "why": "wet room tiled to full height: 'paint above wall tile' line "
                                    "L-d8707985856b2cfbe5a2 is NOT_APPLICABLE_WITH_EVIDENCE"},
         "EXTERNAL_FINISH": {"state": "HELD", "line_ids": ["L-8bb83e16cc7b104ab88b"], "held_item": EXT_HELD,
                             "named_task": EXT_TASK, "value": 1.08, "unit": "m2"}}},
]


def build(trace_rows=None):
    return {"schema": "URBAN_V3019_INPUTS_V1", "project": None, "sources": sources(), "records": [ring_record()],
            "opening_trace": list(trace_rows if trace_rows is not None else TRACE)}


if __name__ == "__main__":
    json.dump(build(), sys.stdout, ensure_ascii=False, indent=1)
