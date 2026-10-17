"""S6 review, Investigation A: run the engine's own opening census (lintel_measure.openings: the function behind
ARCH_TAKEOFF V1/V2 openings and the M4 / route-G architectural lintel evidence) on each fixture, three ways:
  FROZEN      the code as committed (face_lines drops a segment when L < 100 mm, in drawing units)
  ROBUST      the same code with a tolerance-aware predicate: drop only when L < 100 mm - eps, eps = 1e-6 mm
  CANON_MM    FROZEN after converting the drawing to millimetres first (coordinates x 1/(1000 unit_m))
plus the exact decimal length of the drafted piece (independent of binary floats).
usage: python3 -I eval_fixtures.py SRC FIXTURE_DIR [JSON_OUT]"""
import json, math, sys
from decimal import Decimal, getcontext
getcontext().prec = 50
from pathlib import Path
SRC, FIX = sys.argv[1], Path(sys.argv[2])
sys.path.insert(0, SRC)
from engine.source import opening_census as OC, lintel_measure as LM
from tools import urban_intake as UI
FROZEN = OC.face_lines


def robust(segments, ang_res_deg=0.1, off_tol=2.0, join_tol=1.0, min_len=1.0, _eps=[None]):
    return FROZEN(segments, ang_res_deg=ang_res_deg, off_tol=off_tol, join_tol=join_tol, min_len=min_len - _eps[0])


def census(segs, unit_m, mode):
    if mode == "ROBUST":
        robust.__defaults__[-1][0] = 1e-9 / unit_m              # 1e-6 mm in drawing units
        OC.face_lines = robust
    else:
        OC.face_lines = FROZEN
    try:
        ops, rej = LM.openings(segs, unit_m, ["A-WALL"], (), tol="UNIT_RELATIVE")
    finally:
        OC.face_lines = FROZEN
    return [{"width_mm": round(o["width_m"] * 1000, 6), "jambs": [o["start_jamb"], o["end_jamb"]]} for o in ops], rej


res = {}
for f in sorted(FIX.glob("*.dxf")):
    it = UI.read(str(f))
    u = it["unit_m"]
    segs = [s for s in it["segments"] if s["layer"] == "A-WALL"]
    short = [s for s in segs if math.dist(s["a"], s["b"]) * u < 0.15]
    piece = [{"id": s["id"], "a": s["a"], "b": s["b"], "float_length_mm": repr(math.dist(s["a"], s["b"]) * u * 1000),
              "float_length_drawing_units": repr(math.dist(s["a"], s["b"])), "below_min_len": math.dist(s["a"], s["b"]) < 100.0 * (1e-3 / u),
              # the exact length of the stored binary coordinates (Decimal(float) is exact), to 50 digits:
              # it shows whether the error is in the stored coordinates (the transform) or in the distance formula
              "exact_length_of_stored_coordinates": str(((Decimal(s["a"][0]) - Decimal(s["b"][0])) ** 2 +
                                                         (Decimal(s["a"][1]) - Decimal(s["b"][1])) ** 2).sqrt()),
              "drafted_length": "100 mm (by construction: the block's local coordinates are exact)"}
             for s in short]
    mm = [dict(s, a=(s["a"][0] * u * 1000, s["a"][1] * u * 1000), b=(s["b"][0] * u * 1000, s["b"][1] * u * 1000)) for s in segs]
    r = {"unit_m": u, "short_piece": piece}
    for mode in ("FROZEN", "ROBUST"):
        r[mode] = census(segs, u, mode)
    r["CANON_MM"] = census(mm, 0.001, "FROZEN")
    r["CANON_MM_piece_length_mm"] = [repr(math.dist(s["a"], s["b"])) for s in mm if math.dist(s["a"], s["b"]) < 150]
    res[f.name] = r
    print(f"{f.name:34s} unit_m={u:<6} piece={piece[0]['float_length_drawing_units'] if piece else '-':>22s} "
          f"FROZEN={len(r['FROZEN'][0])} ROBUST={len(r['ROBUST'][0])} CANON_MM={len(r['CANON_MM'][0])} "
          f"canon_piece={r['CANON_MM_piece_length_mm']}")
if len(sys.argv) > 3:
    Path(sys.argv[3]).write_text(json.dumps(res, indent=1, default=str))
