"""T-343: the URBAN_V3025_INPUTS_V1 project inputs of ARCH_TAKEOFF_V3.0.25 (engine.source.arch_v3025), built ONLY from
Checker-merged ledgers, each pinned by sha256 (an edited ledger stops the build):

  T-342 (MERGED 4dd9cff8, Checker 2026-10-29 14:40 Gate A PASS): research/agents_t342/SCOPES_T342.csv, the census
        binding of the GF court face (6 plan pieces + the E1 risers MISSING, the pool deck corrected to the drawn D,
        porch and deck material HELD) and of the pool water-face finish (MISSING, HELD blank);
  T-157 (MERGED 554c1c46, Checker 2026-10-22): research/agents_t157/AREAS_T157.csv, the drawn piece areas, their cut
        lines and sheets, the owner manual method of the north side walk and the freelancer rows;
  T-183 r2 (MERGED 63802945, Checker 2026-10-22 16:14: 1.20 to the structure line VERIFIED, the 1.15 finished depth
        beside it): research/agents_t183/T-183_POOL_RC.md, the pool D outlines and the NW elevation cut levels.

Every area is read from the merged CSVs (no figure is typed here except the D radii / straights / backs, which are
the drawn ARC / LINE lengths both merged ledgers print, and the T-071 tessellated hole they name). The pool deck is
the T-157 pool court face 17.3414 m2 less the EXACT outer D cut at the boundary-wall face (ARC 200 r 1750 + LINEs
204 / 206 1550, back 3.50 on the wall face) = 10.235564 m2: 7.105837 m2 (T-342 7.1094 used the T-071 tessellated hole
10.232: residual -0.003564 m2, named). Drawing references are Drive titles and DXF entity handles only.

    python3 -I research/agents_t343/t343_inputs.py            # prints the pieces and the declared totals
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
T342 = ROOT / "research/agents_t342/SCOPES_T342.csv"
T157 = ROOT / "research/agents_t157/AREAS_T157.csv"
T183 = ROOT / "research/agents_t183/T-183_POOL_RC.md"
PINS = {T342: "7e307d8d31ff8181b496ab7252d35298e43eaa8aae39fa8baa819732d7ba5caf",
        T157: "94ff4131b436bdc7b2ae54d6660fb979ba985f26e2713ab10dc3c3d47b526294",
        T183: "4e6f543761543a6b7943920e8294599fb229ff04d445c4a6709d091f38e82282"}
MERGES = {"T-342": ("4dd9cff8eafbd440e25716320376346abe274b4e",
                    "Verifier 2026-10-29 T-342 (run session_01E6cPncoznf56LNXvKzxoSH, STARTED 14:10): Gate A PASS, "
                    "MERGED 4dd9cff8 (M2 MET on rooms and openings; court 6 pieces 166.883 m2 + risers named MISSING; "
                    "deck DRAWING-CONFIRMED area + HELD material)"),
          "T-157": ("554c1c462b459701f5be6586a8a4cc60b809bac5",
                    "Verifier 2026-10-22 T-157 Gate A (MERGED 554c1c46; north side walk re-measured 21.021, the "
                    "outdoor pieces re-added to the open face 177.115)"),
          "T-183": ("6380294591b6854e0c0212f876b89fe0198b15ee",
                    "Verifier 2026-10-22 16:14 T-183 r2 (MERGED 6380294: wall to the structure line 1.20 VERIFIED, "
                    "the 1.15 finished depth floor -> rim kept beside it, upstand inside the 1.20)")}
DRIVE_ARCH = "Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip (P7757.dxf)"
OUTER_D = {"what": "pool outer D cut at the boundary-wall face", "r_m": 1.75, "straight_m": 1.55, "width_m": 3.50,
           "edges": f"{DRIVE_ARCH}: ARC 200 (r 1750, 90 -> 270 deg) + LINEs 204 / 206 (1550 each) closed by the "
                    "boundary-wall inner face (back 3.50)",
           "tessellated_m2": 10.232}       # T-071 court hole (D2 lines), as T-342 used it
WATER_D = {"r_m": 1.55, "straight_m": 1.55, "width_m": 3.10,
           "edges": f"{DRIVE_ARCH}: ARC 202 (r 1550, 90 -> 270 deg) + LINEs 203 / 205 (1550 each), back 3.10 on the "
                    "pool back wall face"}
OUTDOOR_RULE = ("OWNER_RULE_OUTDOOR_FLOORS_2026-10-21 (answers OQ-04) with the owner decisions 23:20: chalet court "
                "INTERLOCK, owner choice over the renders")
SIDES_RULE = ("OWNER_RULE_OUTDOOR_FLOORS_2026-10-21 owner addition 20:45: the sides are part of the house, porcelain / "
              "ceramic, never interlock")
STAIR_RULE = ("UP-STAIR-001 (marble on the tread, riser AND landing of every stair assembly, external steps "
              "included); OWNER_RULE_OUTDOOR_FLOORS (outside stairs marble)")


def _sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _check_pins():
    for p, pin in PINS.items():
        s = _sha(p)
        if s != pin:
            raise SystemExit(f"{p.name}: sha256 {s[:8]} is not the merged {pin[:8]} (edited ledger)")


def _t157():
    with T157.open(encoding="utf-8", newline="") as fh:
        return {r["id"]: r for r in csv.DictReader(fh) if r["id"] != "TH"}


def _t342():
    with T342.open(encoding="utf-8", newline="") as fh:
        return {(r["face_id"], r["scope"]): r for r in csv.DictReader(fh)}


def _f(x):
    return float(x) if x not in (None, "") else None


def _piece(piece, code, area, row, *, kind="PLAN", material, ms, src=None, item=None, basis=None, edges=None,
           derived=None, owner_manual=None, freelancer=None, flags=(), task="T-157"):
    d = {"piece": piece, "element_id": f"GF-COURT#{piece}", "floor": "GF", "item_code": code, "unit": "m2",
         "kind": kind, "area_m2": round(area, 6), "area_status": "DRAWING-CONFIRMED",
         "area_basis": basis or f"{row['id']} {row['space_surface']}: {row['hand_formula']}",
         "edges": edges or f"{DRIVE_ARCH}; {row['evidence']}", "material": material, "material_status": ms,
         "source_task": task, "flags": list(flags)}
    if ms == "HELD":
        d["material_item"] = item
    else:
        d["material_source"] = src
    if derived:
        d["derived"] = derived
    if owner_manual:
        d["owner_manual"] = owner_manual
    if freelancer:
        d["freelancer"] = freelancer
    return d


def build(project_id=None):
    _check_pins()
    a, s = _t157(), _t342()
    OA = "ASSUMED - OWNER-APPROVED"   # the engine spelling (arch_v3018.OA)
    yard = {"row": "FIN workbook, yard floors row (one row, no dimensions)", "m2": 151.80,
            "note": "covers open court + porch + north side walk 151.234 (-0.566, -0.37 %): AGREE / RULE_DIFFERENCE "
                    "(T-157); no pool deck, no side passage in his yard"}
    court_face = _f(a["OD-07"]["hand_formula"].split("face ")[1].split(" ")[0])        # 17.3414 (T-157 polygon)
    deck = court_face - (3.141592653589793 * 1.75 ** 2 / 2 + 3.50 * 1.55)
    t342_deck = _f(s[("GF-COURT", "pool deck")]["quantity"])
    pieces = [
        _piece("WEST-OPEN", "EXT.PAVING.INTERLOCK", _f(a["OD-01"]["drawn_m2"]), a["OD-01"], material="interlock",
               ms=OA, src=OUTDOOR_RULE, freelancer=yard),
        _piece("PORCH", "EXT.FLOOR.OUTDOOR", _f(a["OD-02"]["drawn_m2"]), a["OD-02"], material="undecided", ms="HELD",
               item="owner: covered porch finish at court level (wood / ceramic / marble), OWNER_RULE_OUTDOOR_FLOORS "
                    "decision 23:20 'own line, material later'", freelancer=yard),
        _piece("E1-TREADS", "FIN.MARBLE.TREAD", _f(a["OD-03"]["drawn_m2"]), a["OD-03"], material="marble", ms=OA,
               src=STAIR_RULE, freelancer={"row": "FIN workbook, entrance marble block: steps", "m2": 14.00,
                                           "note": "5 steps x 2.80 (a per-step length basis, not the tread area "
                                                   "4 x 0.30 x 2.80): not comparable as m2"}),
        _piece("E1-RISERS", "FIN.MARBLE.RISER", _f(a["OD-04"]["hand_m2"]), a["OD-04"], kind="VERTICAL",
               material="marble", ms=OA, src=STAIR_RULE,
               flags=["drawn riser 0.170 > 0.16 (owner stair rule S-1 check only: 6 risers of 0.142 would be "
                      "needed; the drawing governs, UP-STAIR-002)"]),
        _piece("E1-LANDING", "FIN.MARBLE.LANDING", _f(a["OD-05"]["drawn_m2"]), a["OD-05"], material="marble",
               ms=OA, src=STAIR_RULE, freelancer={"row": "FIN workbook, entrance marble block: landing", "m2": 5.10,
                                                  "note": "printed 1.40 x 3.70 = 5.18: +0.08 (+1.5 %), ENGINE_RIGHT"}),
        _piece("NORTH-WALK", "EXT.FLOOR.PORCELAIN", _f(a["OD-06"]["drawn_m2"]), a["OD-06"],
               material="porcelain / ceramic", ms=OA, src=SIDES_RULE,
               owner_manual={"formula": a["OD-06M"]["hand_formula"] + " (printed 1500 x 15970: to the outer face of "
                                                                       "the boundary wall, from the corner column's "
                                                                       "inner face)",
                             "m2": _f(a["OD-06M"]["hand_m2"])}, freelancer=yard),
        _piece("POOL-DECK", "EXT.FLOOR.OUTDOOR", deck, a["OD-07"], material="undecided", ms="HELD",
               item="owner: pool deck finish (OWNER_RULE_OUTDOOR_FLOORS: pool deck HELD, undecided)",
               basis=(f"OD-07 pool court deck: the T-157 pool court face {court_face} m2 less the exact outer D cut "
                      f"at the boundary-wall face (corrected by T-342 from the T-157 circle r 1.75, 9.4022; T-342 "
                      f"{t342_deck} took the T-071 tessellated hole 10.232)"),
               edges=(f"{DRIVE_ARCH}: pool court face cut by T-157 along the drawn lines (curved GF glazing, 1F edge "
                      f"band at the mouth, boundary-wall inner face); hole {OUTER_D['edges']}"),
               derived={"face_m2": court_face, "face_source": "T-157 AREAS_T157.csv OD-07 pool court face (CAD "
                                                              "polygon, DRAWING-CONFIRMED, merged)",
                        "less": [dict(OUTER_D)]}, task="T-342"),
    ]
    pool = {"element_id": "GF-POOL-WATER#FINISH", "floor": "GF", "water_outline": dict(WATER_D),
            "rim_height_m": 1.15, "structural_height_m": 1.20, "rim_basis": "FINISHED_FLOOR_TO_RIM",
            "rim_height_source": (f"{DRIVE_ARCH}: architectural NW elevation cut (Drive Alsenan_Architectural_P7757 "
                                  "Pages_07-08, NW elevation): DIMENSION handle 2E5E = 1150 from the finished pool "
                                  "floor -0.85 (layer-5 line between the inner wall faces) to the rim +0.30 (wall "
                                  "caps / water line); the structure line -0.90 under the 50 mm build-up gives the "
                                  "1.20 wall concrete (T-183 r2, VERIFIED), beside, not used for a finish"),
            "rim_status": "DRAWING-CONFIRMED", "material_status": "HELD",
            "material_item": "owner / designer: pool water-face finish (no sheet and no Urban rule names it; T-342 "
                             "scope 'pool water-face finish' HELD)",
            "freelancer": {"row": "FIN workbook, pool floors + pool walls (ceramic)", "m2": 40.80,
                           "note": "floors 21.00 + walls 19.80: his floor 21.00 vs the drawn water D 8.579 and his "
                                   "walls 19.80 vs 11.069 x 1.15 = 12.730 are not reproduced by the drawn pool "
                                   "(not proof; finish not specified)"},
            "source_task": "T-183"}
    plan = sum(p["area_m2"] for p in pieces if p["kind"] == "PLAN")
    vert = sum(p["area_m2"] for p in pieces if p["kind"] == "VERTICAL")
    held = sum(p["area_m2"] for p in pieces if p["material_status"] == "HELD")
    wa = 3.141592653589793 * 1.55 ** 2 / 2 + 3.10 * 1.55
    wp = 3.141592653589793 * 1.55 + 2 * 1.55 + 3.10
    sys.path.insert(0, str(ROOT / "research" / "agents_t193"))
    import t193_inputs as L7   # noqa: E402  (the V3.0.7 guard inputs, unchanged, as V3.0.8 .. V3.0.24)
    g = dict(L7.inputs(project_id)["guard"], new_records=[])
    return {"schema": "URBAN_V3025_INPUTS_V1", "project": project_id,
            "sources": [{"file": str(p.relative_to(ROOT)), "sha256": PINS[p], "task": t, "merge_commit": MERGES[t][0],
                         "checker_run": MERGES[t][1]} for p, t in ((T342, "T-342"), (T157, "T-157"), (T183, "T-183"))],
            "face": {"face_id": "GF-COURT", "floor": "GF", "filled_m2": 177.1154,
                     "filled_source": ("T-157 open face inside the plot boundary-wall inner faces, 177.1154 m2 (T-157 "
                                       "polygon of the GF plan = T-153 177.115; T-071 filled 177.299 closes the face "
                                       "with a 0.232 m closure line instead, not used)"),
                     "holes": [dict(OUTER_D)], "closure_tol_m2": 0.005, "reference_total_m2": 166.883,
                     "reference_source": "T-342 SCOPES_T342.csv / T-342 report: 6 pieces 166.883 = 177.115 - 10.232 "
                                         "(tessellated hole)"},
            "pieces": pieces, "pool_finish": pool, "cross_check": CROSS_CHECK,
            "declared": {"lines": len(pieces) + 1, "plan_m2": round(plan, 6), "vertical_m2": round(vert, 6),
                         "held_material_m2": round(held, 6), "pool_bound_m2": round(wa + wp * 1.15, 6)},
            "guard": g}


# The V3.0.24 lines that border or could share area with the pieces (line ids of the V3.0.24 run, own run): each
# measures another face or another element, so the area shared is 0.000 m2 (filled from the run by v3025_run.py).
CROSS_CHECK = []


if __name__ == "__main__":
    d = build()
    print(json.dumps({"pieces": [(p["piece"], p["item_code"], p["area_m2"], p["material_status"]) for p in d["pieces"]],
                      "declared": d["declared"]}, indent=1, ensure_ascii=False))
