"""ENGINE ADAPTER - Phase 2B-4: reads the V2.5 engine's own records for the audited rooms (through the Phase 2B-3
adapter tests/m9_p2b3/proof_engine.py, the same engine call the proof library makes). This is the only file of the
audit library that reaches the engine; the expected values and the construction calculator never pass through it.

    engine_record(room_id)    what V2.5 reports for the room: direction, piece lengths, roll segments, laps,
                              junction lap, scrap records, open details, roll sensitivity
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "m9_p2b3"))

import proof_cases as PC                                      # noqa: E402
import proof_engine as PE                                     # noqa: E402

CASES = {"WP-B": PC.WP_B, "WP-E": PC.WP_E, "WP-D": PC.WP_D}


def scenario(room_id):
    return CASES[room_id]["scenario"]


def engine_record(room_id, method=PE.V25):
    a = PE.wp_area(CASES[room_id], method)
    lay = a["layout"]["layout"]
    row = a["row"]
    mm = lambda x: int(round(x * 1000))                      # noqa: E731
    return {
        "direction": lay["direction"],
        "floor_pieces_mm": [mm(x) for x in lay["floor_pieces_m"]],
        "band_pieces_mm": [mm(x) for x in lay["band_pieces_m"]],
        "doorway_pieces_mm": sorted((d["doorway"], mm(d["piece_m"][1]), mm(d["piece_m"][0]))
                                    for d in lay["doorway_pieces"]),
        "rolls": [[(mm(s["length_m"]), s["for"]) for s in r["segments"]] for r in lay["rolls"]],
        "rolls_n": row["rolls_if_installed_alone"], "consumed_m2": row["consumed_m2"], "B_m2": row["B_installed_m2"],
        "waste_m2": row["cutting_waste_m2"], "laps_m2": row["laps_m2"],
        "components": {c["component"]: c["overlap_m2"] for c in a["layout"]["components"]},
        "seams": lay["seams"], "junction_lap_m": lay["seams"]["upturn_to_floor_lap"]["lap_m"],
        "junction_running_m": lay["seams"]["upturn_to_floor_lap"]["running_lm"],
        "scrap": [(mm(s[0]), mm(s[1]), s[2]) for s in lay["scrap"]],
        "not_included": [x["what"] for x in a["v25"]["not_included"]],
        "final_material_state": a["v25"]["final_material_state"],
        "roll_sensitivity": a["v25"]["roll_sensitivity"],
        "segment_keys": sorted({k for r in lay["rolls"] for s in r["segments"] for k in s}),
        "corners": row["corners"], "penetrations": row["penetrations"],
    }
