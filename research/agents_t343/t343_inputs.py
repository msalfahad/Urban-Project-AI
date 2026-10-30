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
the drawn ARC / LINE lengths both merged ledgers print, and the T-071 tessellated hole they name).

r2 (D-T343-1, Checker Gate B 2026-10-29 23:05, own re-read of the DXF handles 2026-10-30): the pool deck face stops at
the COURT face of the 0.20 curved glazed band (ARC 201, r 2.25, the printed 657 line, owner Q-38 A), not at the
window-frame line W 280 (r 2.33, its straights 0.08 inside the house face) that the T-157 polygon walked (rule
R-T343-1). Its face is built from the drawn terms: rectangle 1.80 x 5.60 (house east face LINEs 94 / 95 / 96 on the
chord, boundary-wall inner face LINE B7, south face LINE E2, house north-face line 2BC) + the band segment r 2.25
beyond the chord at 0.25 from the pool centre - column LWPOLYLINE 2F87 0.50 x 0.25 = 16.784476 m2; less the EXACT
outer D cut at the boundary-wall face (ARC 200 r 1750 + LINEs 204 / 206 1550, back 3.50 on the wall face, DIMENSION
6A1 3500) 10.235564 = 6.548912 m2. The recess between the band face and the frame line (segment r 2.33 at 0.33 +
0.08 x 4.95 - segment r 2.25 at 0.25 = 0.561577 m2) is the glazing reveal strip SX-02 of the merged T-127 / T-154
ledgers (one surface, one line, HELD there): named in the closure, never deck, never 0, not a line here. The T-157
polygon 17.3414 is the frame-walked face 17.346053 read with a -0.004653 m2 tessellation residual (named). Drawing
references are Drive titles and DXF entity handles only.

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
# the deck face and the SX-02 strip, from the drawn terms (DXF handles of P7757.dxf; lengths in m, as printed / drawn)
DECK_FACE_TERMS = [
    {"what": "court rectangle 1.80 x 5.60", "kind": "RECT", "a_m": 1.80, "b_m": 5.60, "sign": 1, "edge_kind": "DRAWN_LINE",
     "edges": "house east face LINEs 94 / 95 / 96 (chord) to boundary-wall inner face LINE B7; south face LINE E2 to "
              "house north-face line 2BC"},
    {"what": "band segment r 2.25 beyond the chord at 0.25", "kind": "SEGMENT", "r_m": 2.25, "d_m": 0.25, "sign": 1,
     "edge_kind": "BAND_COURT_FACE",
     "edges": "ARC 201 (layer 5, r 2250, 96.38 -> 263.62 deg, concentric with the pool ARCs 200 / 202): the glazed "
              "band's court face, the printed 657 line (owner Q-38 A)"},
    {"what": "column 0.50 x 0.25", "kind": "RECT", "a_m": 0.50, "b_m": 0.25, "sign": -1, "edge_kind": "DRAWN_LINE",
     "edges": "LWPOLYLINE 2F87 (S-COL.BON), inside the rectangle"},
]
SX02_TERMS = [
    {"what": "frame segment r 2.33 beyond its straights at 0.33", "kind": "SEGMENT", "r_m": 2.33, "d_m": 0.33, "sign": 1,
     "edge_kind": "FRAME_LINE", "edges": "LWPOLYLINE W 280 bulge 0.86711 (chord 4.613, r 2330)"},
    {"what": "strip 0.08 x 4.95 between the house face and the frame straights", "kind": "RECT", "a_m": 0.08,
     "b_m": 4.95, "sign": 1, "edge_kind": "FRAME_LINE",
     "edges": "LWPOLYLINE W 280 straights (x 0.08 inside LINEs 94 / 95 / 96; y +2.500 .. -2.450 about the pool centre)"},
    {"what": "band segment r 2.25 beyond the chord at 0.25", "kind": "SEGMENT", "r_m": 2.25, "d_m": 0.25, "sign": -1,
     "edge_kind": "BAND_COURT_FACE", "edges": "ARC 201 (r 2250)"},
]
OUTDOOR_RULE = ("OWNER_RULE_OUTDOOR_FLOORS_2026-10-21 (answers OQ-04) with the owner decisions 23:20: chalet court "
                "INTERLOCK, owner choice over the renders")
SIDES_RULE = ("OWNER_RULE_OUTDOOR_FLOORS_2026-10-21 owner addition 20:45: the sides are part of the house, porcelain / "
              "ceramic, never interlock")
STAIR_RULE = ("UP-STAIR-001 (marble on the tread, riser AND landing of every stair assembly, external steps "
              "included); OWNER_RULE_OUTDOOR_FLOORS (outside stairs marble)")


sys.path.insert(0, str(ROOT))
from engine.source import arch_v3025 as A  # noqa: E402

SX02 = A.terms_area(SX02_TERMS, "SX-02")[0]                                            # 0.561577


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
    deck_face = A.terms_area(DECK_FACE_TERMS, "deck face", floor_face=True)[0]          # 16.784476 (band face)
    deck = deck_face - (3.141592653589793 * 1.75 ** 2 / 2 + 3.50 * 1.55)
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
               basis=(f"OD-07 pool court deck (r2, R-T343-1): the pool court face to the glazed band's court face "
                      f"(ARC 201 r 2.25) {round(deck_face, 6)} m2 less the exact outer D cut at the boundary-wall face "
                      f"(T-157 {court_face} walked the frame line W 280: + SX-02 reveal strip {round(SX02, 6)}, "
                      f"named in the closure; T-342 {t342_deck} took the T-071 tessellated hole 10.232; T-157 first "
                      f"used a circle r 1.75)"),
               edges=(f"{DRIVE_ARCH}: house east face LINEs 94 / 95 / 96, boundary-wall inner face LINE B7, south "
                      f"face LINE E2, house north-face line 2BC, glazed band court face ARC 201 (r 2250), column "
                      f"LWPOLYLINE 2F87; hole {OUTER_D['edges']}"),
               derived={"face_m2": round(deck_face, 6), "face_edge_kind": "BAND_COURT_FACE",
                        "face_source": ("drawn construction from DXF handles (Checker Gate B T-343 2026-10-29 23:05 "
                                        "own construction = T-127 hand 6.8295 for the band segment; re-read from the "
                                        "handles by worker 3 on 2026-10-30)"),
                        "construction": {"terms": DECK_FACE_TERMS},
                        "polygon_reading": {"m2": court_face, "edge_kind": "FRAME_LINE",
                                            "source": "T-157 AREAS_T157.csv OD-07 (CAD polygon along W 280): not "
                                                      "used; = band face + SX-02 - 0.004653 tessellation"},
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
                     "holes": [dict(OUTER_D)],
                     "reveal_strips": [{"what": "SX-02 recess in front of the curved glazing frame (pool court)",
                                        "scope": ("openings / glazing reveal strip (T-127 0.561 / T-154 0.5609 merged: "
                                                  "one surface one line, HELD there with T-123); R-T343-1"),
                                        "held_with": "T-154 glazing reveal strip SX-02 (HELD), not a floor line here",
                                        "edges": (f"{DRIVE_ARCH}: frame LWPOLYLINE W 280 (bulge r 2330, straights "
                                                  "0.08 inside the house face), band court face ARC 201 (r 2250), "
                                                  "house east face LINEs 94 / 95 / 96 (chord)"),
                                        "construction": {"terms": SX02_TERMS}, "m2": round(SX02, 6)}],
                     "reading_residuals": [{"what": "T-157 pool court face polygon along the curved frame line W 280",
                                            "tessellated_m2": court_face, "exact_m2": round(deck_face + SX02, 6),
                                            "basis": ("T-157 OD-07 polygon 17.3414 vs the exact frame-walked face = "
                                                      "band face construction + SX-02 (inside the T-157 filled face "
                                                      "177.1154)")}],
                     "closure_tol_m2": 0.005, "reference_total_m2": 166.883,
                     "reference_source": "T-342 SCOPES_T342.csv / T-342 report: 6 pieces 166.883 = 177.115 - 10.232 "
                                         "(tessellated hole)"},
            "pieces": pieces, "pool_finish": pool, "cross_check": CROSS_CHECK,
            "declared": {"lines": len(pieces) + 1, "plan_m2": round(plan, 6), "vertical_m2": round(vert, 6),
                         "held_material_m2": round(held, 6), "pool_bound_m2": round(wa + wp * 1.15, 6)},
            "guard": g}


# The V3.0.24 lines that border or could share area with the pieces (line ids of the V3.0.24 run, own run of
# v3025_run.py, V3_0_24_BOQ_LINES.json sha256 19394733 = the Checker's candidate of record). The room-face lines come
# from the same polygonization of the GF plan as the court face (T-147 rooms.py, the call T-153 / T-157 used): faces of
# one planar partition are disjoint, so a room-face line shares 0.000 m2 with a court piece by construction; the
# pool lines measure the court's HOLE (the deck is the face less the exact outer D); the soffit is a ceiling surface.
# T-342 (merged): no candidate line binds the court face (its labels AT21 / AT22 / AT39 / AT40 were MISSING).
_FACE = ("a separate face of the same GF polygonization (planar partition, disjoint from the court face); T-342 "
         "merged: no candidate line binds GF-COURT")
CROSS_CHECK = [
    {"line_id": "L-e653ef87a06a97903b0a", "item_code": "ARCH.SPACE", "element_id": "HL:FLOOR_SCOPE:OUTDOOR:GF:GF-SIDE-PASSAGE",
     "why": "side passage 1.20 x 4.70 = 5.64 m2 (Q-67 A), T-157 OD-08: its own face between the annex and the house, "
            "outside the court face (not in the 177.1154 re-add)", "shared_m2": 0.0},
    {"line_id": "L-5431fa278fbb44816a08", "item_code": "ARCH.EXTERIOR", "element_id": "GF-R9A05AA:space",
     "why": "GF garden band part 9.101 m2 (T-157 OD-09: physically inside, HELD_CONFLICT, designer D-48); " + _FACE,
     "shared_m2": 0.0},
    {"line_id": "L-6b6412e885390b434819", "item_code": "ARCH.SPACE", "element_id": "GF-RFD4E1D:space",
     "why": "GF garden band part 4.885 m2 (T-153 / T-157 OD-09 9.101 + 4.885 = 13.986); " + _FACE, "shared_m2": 0.0},
    {"line_id": "L-554a525edce9a9235bee", "item_code": "ARCH.SPACE",
     "element_id": "HL:FLOOR_SCOPE:HELD_WITH:GF:GF-OP-003-NO-OPENING:band",
     "why": "6.82 x 0.20 strip HELD with the garden band (P-2), inside the south facade: not in the court face",
     "shared_m2": 0.0},
    {"line_id": "L-36efa902da4263479e0b", "item_code": "STR.CONC.POOL", "element_id": "pool base",
     "why": "pool base concrete (m3) on the outer D incl. the back wall 10.935564 m2: the court's hole; the deck is the "
            "face less the outer D cut at the wall face 10.235564 (the 0.70 m2 under the back wall is outside the face)",
     "shared_m2": 0.0},
    {"line_id": "L-15a128c38982af899894", "item_code": "STR.CONC.POOL", "element_id": "pool walls",
     "why": "pool wall ring concrete (m3) inside the outer D: the court's hole; its 0.15 upstand top and outer face "
            "are pool faces, not deck floor", "shared_m2": 0.0},
    {"line_id": "L-b62a7065645589011141", "item_code": "STR.CONC.POOL", "element_id": "pool steps",
     "why": "pool steps BLOCKED (not drawn): inside the water D, never a floor", "shared_m2": 0.0},
    {"line_id": "L-23072352a28aeca7b051", "item_code": "FIN.CEILING", "element_id": "SOFFIT:GF:PL-03",
     "why": "pool court soffit 16.525 - 3.690 = 12.834 m2: the ceiling under the 1F over the pool court, another "
            "surface (not a floor)", "shared_m2": 0.0},
    {"line_id": "L-1983e89d8b619eade1db", "item_code": "FIN.MARBLE.LANDING", "element_id": "GF-R31F8AE:landings",
     "why": "landings of the interior stair room GF-R31F8AE (face area 12.475, TS01): " + _FACE + "; E1 and its "
            "landing lie outside the main door in the court face", "shared_m2": 0.0},
    {"line_id": "L-151d92470a81dd1c450b", "item_code": "FIN.MARBLE.TREAD", "element_id": "GF-R31F8AE:flight 1",
     "why": "treads of the interior stair room GF-R31F8AE: " + _FACE, "shared_m2": 0.0},
    {"line_id": "L-fa534ec5f9dc14947899", "item_code": "FIN.MARBLE.TREAD", "element_id": "GF-RC99C2A:flight 1",
     "why": "treads of the main stair room GF-RC99C2A: " + _FACE, "shared_m2": 0.0},
]


if __name__ == "__main__":
    d = build()
    print(json.dumps({"pieces": [(p["piece"], p["item_code"], p["area_m2"], p["material_status"]) for p in d["pieces"]],
                      "declared": d["declared"]}, indent=1, ensure_ascii=False))
