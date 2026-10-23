"""T-193: the project inputs of ARCH_TAKEOFF_V3.0.7 (URBAN_V307_INPUTS_V1) for the development villa, and the guard
evidence version 2. Research code; it reads the merged files as committed and changes none of their quantities. Every
choice cites its source.

POOL_CONCRETE (T-183 r2, MERGED 6380294, Verifier 2026-10-22 16:14 UTC; owner 11:50 conditions (a)-(h)):
  base  C_BASE 10.935564 m2 (outer D 3.50 x 1.75 + pi 1.75^2 / 2) x 0.40 printed (ST p.7 '40', STRUCTURAL) = 4.374226 m3
        VERIFIED (Checker T-180 10:20 re-measured 10.935 m2 x 0.40; T-183 r2 verdict conditions (a) (b) PASS)
  walls D_WALLS 2.356726 m2 (outer D - water D, the curved half on its true arc) x 1.20 (rim +0.30 -> structure line
        -0.90, the NW elevation cut of the architectural DXF; STRUCTURAL) = 2.828071 m3 VERIFIED (verdict 16:14: "RC wall
        height rim -> structural base top = 1.200 m VERIFIED (worker 1.200, 0.0 %); walls 2.3568 m2 x 1.20 = 2.828")
        the printed 1.15 is the FINISHED water depth (owner Q-26 A) and governs the visible finish only, never the RC
  steps E_STEPS NOT DRAWN (GF plan, ST p.7, the sections): owner 2026-10-22 16:45 "record it as STEPS: NOT DRAWN -
        consultant item (access ladder or steps?) open; close it only on a drawing or a consultant answer": HELD line,
        never 0
  line group: PARTIALLY VERIFIED (owner whole-line rule 11:50 / 16:45): concrete VERIFIED, steps NOT DRAWN, bar
        populations R1 / R2 HELD (T-191 re-derived them, a later package), joints / waterstop, membrane termination,
        finishes UNKNOWN
  supersedes: the two route lines of the pool (V3.0.6 held both by the guard): FLOOR 1.51125 (0.25 convention on the
        6.045 m2 footprint) and WALLS 1.984 (1.60 convention on half the ring): 3.49525 m3 -> 7.202297 (+3.707047)

DOME_SHELL (T-185, MERGED 94e39ee6, Verifier 2026-10-22 18:15 UTC, S0 approved design):
  DOME-A (west) and DOME-B (east) shells, each 2.540681 m3 from the printed chord 442, rise 190, thickness 10 (ST p.7
        DETAIL OF DOME), exact solid between concentric spheres; Verifier 18:15 own re-measure "2.5407 m3 per dome =
        worker (0.0 %); 2 terrace domes 5.081 m3 VERIFIED"
  register ids (T-186 evidence mapping): DOME-1 = route finding CC-6e7b8c8d1f (sheet SH02, box x 12.688 .. 17.110 m,
        centre 14.899 m from the sheet edge = the WEST circle) = DOME-A; DOME-2 = CC-a0729cfebc (box x 27.136 .. 31.558,
        centre 29.347 m = the EAST circle) = DOME-B (route G completeness findings, own run of this task)
  supersedes: the two route dome lines (V3.0.6 held both): 2 x 3.685858 (rise = radius 2.211, shell 0.12, outer area)
        = 7.371716 -> 5.081361 (-2.290355)
  retires: P-C:STAIRS:1F:SITE-b845e1e78b1f74a8 (STR.CONC.STAIR, 1F, 4.450745 m3 winder convention, V3.0.6 HELD
        MISREAD): its face on SH04 (the 1F roof slab sheet, frame x 1481 .. 36675) has its point at (32988, 41651) and
        its polygon from x 28617, i.e. round the EAST dome centre (30828, 41651) of that sheet (circle 649 r 2211.1, 20
        radial lines on S-OPENING); the west dome of the same sheet is at (16380, 41651). The same two domes are drawn on
        SH02 (circles 3CD / 3F8 on S-BOUN, 20 radial lines each on S-COL.BON, offset -38724 / -38725 in x): the route
        took them there as the 2F dome lines. So the retired line is DOME-B drawn on its own slab sheet, now carried
        once by HL:DOME_SHELL:DOME-B:SHELL. Own read of ST7757 dxf.dxf (9f9d1179) in this task.
  other element: DG5:DOME-3:SHELL (upper-roof dome, no structural detail; Q-27 A; held placeholder of V3.0.6) stays
  beside (never summed, never a line): the S1 client-requested scenario and S2 (T185_LEDGER.json)

GUARD (T-186 guard, evidence version 2 = dev_villa_guard_evidence_v2.json):
  version 1 (research/agents_t186/dev_villa_guard_evidence.json) unchanged; version 2 adds three printed records:
  EV-POOL-WALL-H-STR  POOL_WALL_HEIGHT_M 1.20 STRUCTURAL (T-183 r2 verdict, G-T187-1)
  EV-BLINDING-T       BLINDING_THICKNESS_M 0.10 STRUCTURAL: ST7757.pdf p.13 '10cm Plain con.' under both typical
                      isolated-footing details, a 10 cm layer dimensioned under every ground-beam section (T-044 r2 row
                      10, re-read in this task). G-T187-2 cited "ST7757 dxf.dxf TEXT 1877" for it: TEXT 1877 '10cm PLAIN
                      CONCRETE.' stands beside TEXT 1876 '5cm INSULATION MEMBRANE.' and TEXT 1874 '5cm SECREED.' in
                      frame FR01, nearest title TEXT 1864 'DETAIL OF SWIMMING POOL.': it is the POOL detail's layer
                      note (T-044 r2 row 10 says the same), recorded below as the pool's own record
  EV-POOL-BLINDING-T  BLINDING_THICKNESS_M 0.10 STRUCTURAL, element POOL-1 (TEXT 1877)
  Convention set: the route ran on URBAN_M8_GENERIC_CONVENTIONS_V6 + the M4 drawing profile (each line's rule_set
  'URBAN_M8_GENERIC_CONVENTIONS_V6+ST7757_M4'); V3.0.6 gave the guard the V6 file only, so profile values (e.g.
  BLINDING_THICKNESS_M 0.10) reached the guard as None. Version 2 passes the set the route ran on: V6 with the 17
  profile conventions overriding by id (both files and shas named).
"""

from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
T183_DIR = ROOT / "research/agents_t183"
T183_IN = "research/agents_t183/ALSENAN_POOL_INPUT.json"
T183_PY = "research/agents_t183/t183_pool_rc.py"
T185 = "research/agents_t185/T185_LEDGER.json"
EV1 = "research/agents_t186/dev_villa_guard_evidence.json"
EV2 = "research/agents_t193/dev_villa_guard_evidence_v2.json"
CONVENTIONS = "engine/profiles/URBAN_M8_GENERIC_CONVENTIONS_V6.json"
PROFILE = "research/urban_engine_m4_correctness/profile_st7757_m4.json"
HOLD = ["DG-1", "DG-3", "DG-4", "DG-5", "DG-6", "DG-7", "DG-8"]   # as V3.0.6 (t187_inputs.py)
RECORD = ["DG-2"]

NEW_RECORDS = [
    {"id": "EV-POOL-WALL-H-STR", "element_kind": "POOL", "element_id": "POOL-1", "param": "POOL_WALL_HEIGHT_M",
     "value": 1.2, "unit": "m", "doc": "P7757_DXF_COMPRESSED.zip",
     "note": "RC wall height rim +0.30 -> structure line (base top) -0.90 = 1.200 in the NW elevation cut through the "
             "pool (layer-1 wall caps and structure line); T-183 r2, Verifier 2026-10-22 16:14 VERIFIED (worker 1.200, "
             "0.0 %); the 1.15 FINISHED depth stays beside it (EV-POOL-DEPTH-FIN). T-193 (G-T187-1)",
     "basis": "STRUCTURAL"},
    {"id": "EV-BLINDING-T", "element_kind": None, "element_id": None, "param": "BLINDING_THICKNESS_M", "value": 0.1,
     "unit": "m", "doc": "ST7757.pdf",
     "note": "p.13 '10cm Plain con.' under both typical isolated-footing details and a 10 cm layer dimensioned under "
             "every ground-beam section (T-044 r2 row 10, PRINTED; re-read T-193). Not the DXF TEXT 1877, which is the "
             "pool detail's note (EV-POOL-BLINDING-T). T-193 (G-T187-2)",
     "basis": "STRUCTURAL"},
    {"id": "EV-POOL-BLINDING-T", "element_kind": "POOL", "element_id": "POOL-1", "param": "BLINDING_THICKNESS_M",
     "value": 0.1, "unit": "m", "doc": "ST7757 dxf.dxf",
     "note": "TEXT 1877 '10cm PLAIN CONCRETE.' in the DETAIL OF SWIMMING POOL layer stack (beside TEXT 1876 '5cm "
             "INSULATION MEMBRANE.' and 1874 '5cm SECREED.'; nearest title TEXT 1864); pool blinding projection not "
             "printed (T-183 line B HELD). T-193",
     "basis": "STRUCTURAL"},
]


def sha(rel):
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()


def evidence_v2():
    ev = json.loads((ROOT / EV1).read_text(encoding="utf-8"))
    out = copy.deepcopy(ev)
    out["schema"] = ev["schema"]
    out["note"] = (ev.get("note", "") + " | VERSION 2 (T-193): version 1 + EV-POOL-WALL-H-STR, EV-BLINDING-T, "
                   "EV-POOL-BLINDING-T; version 1 unchanged.")
    have = {p["id"] for p in ev["printed"]}
    assert not have & {r["id"] for r in NEW_RECORDS}
    out["printed"] = ev["printed"] + NEW_RECORDS
    return out


def conventions():
    """the set the route ran on: V6 with the drawing profile's conventions overriding by id."""
    base = json.loads((ROOT / CONVENTIONS).read_text(encoding="utf-8"))["conventions"]
    prof = json.loads((ROOT / PROFILE).read_text(encoding="utf-8"))["conventions"]
    by = {c["id"]: c for c in base}
    for c in prof:
        by[c["id"]] = c
    return [by[k] for k in sorted(by)]


def pool_piece():
    sys.path.insert(0, str(T183_DIR))
    import t183_pool_rc as P   # noqa: E402
    led = P.ledger(json.loads((ROOT / T183_IN).read_text(encoding="utf-8")))
    c = led["concrete"]
    base, walls, steps = c["C_BASE"], c["D_WALLS"], c["E_STEPS"]
    assert abs(base["m3"] - 4.374226) < 1e-6 and abs(walls["m3"] - 2.828071) < 1e-6 and walls["height_m"] == 1.2
    assert steps["m3"] is None and steps["status"] == "NOT_DRAWN"
    assert led["heights"]["wall_h"] == 1.2 or abs(led["heights"]["wall_h"] - 1.2) < 1e-9
    src = {"file": T183_IN, "sha256": sha(T183_IN), "task": "T-183 r2 (pool as reinforced concrete)",
           "merge_commit": "6380294",
           "checker_run": "Verifier 2026-10-22 16:14 UTC (T-183 r2 MERGED; owner 11:50 conditions (a)-(h))"}
    v16 = ("Verifier 2026-10-22 16:14 (T-183 r2 MERGED 6380294): pool RC base 4.374 + walls 2.828 = 7.202 m3 "
           "VERIFIED; RC wall height rim -> structural base top 1.200 own re-read of the NW cut")
    recs = [
        {"element": "POOL-1", "component": "BASE", "floor": "GROUND", "state": "RELEASED", "value": round(base["m3"], 6),
         "dims": {"kind": "PRISM", "area_m2": round(base["plan_m2"], 6), "height_m": base["thickness_m"],
                  "height_basis": "STRUCTURAL"},
         "verified_by": v16 + "; base 10.935 m2 x 0.40 also re-measured by the Checker T-180 10:20",
         "printed": "ST7757.pdf p.7 DETAIL OF SWIMMING POOL '40' (base); ST7757 dxf.dxf GROUND BEAMS PLAN S-BW outer "
                    "outline 7C6 (D 3.50 x 1.75 + r 1.75)",
         "formula": "outer D 3.50 x 1.75 + pi 1.75^2 / 2 = 10.935564 m2 x printed base 0.40 (wall foot included, "
                    "measured once at the junction)",
         "geometry_source": "CAD_VECTOR", "guard_element": {"element_id": "POOL-1", "part": "FLOOR"}},
        {"element": "POOL-1", "component": "WALLS", "floor": "GROUND", "state": "RELEASED",
         "value": round(walls["m3"], 6),
         "dims": {"kind": "PRISM", "area_m2": round(walls["plan_m2"], 6), "height_m": walls["height_m"],
                  "height_basis": "STRUCTURAL"},
         "verified_by": v16,
         "printed": "ST7757 dxf.dxf S-BW outlines 7C6 / 7C5 (wall 20 all round incl. the curved half); P7757 dxf NW "
                    "elevation cut: rim +0.30, structure line -0.90 (the printed 1150 is the finished depth)",
         "formula": "wall band 10.935564 - 8.578838 = 2.356726 m2 x 1.20 (rim -> structure line, R-POOL-4 r2)",
         "geometry_source": "CAD_VECTOR", "guard_element": {"element_id": "POOL-1", "part": "WALLS"},
         "info": {"finished_depth_m": 1.15, "upstand_inside_m3": "0.15 above the deck finish, inside the 1.20"}},
        {"element": "POOL-1", "component": "STEPS", "floor": "GROUND", "state": "UNQUANTIFIED",
         "evidence_status": "HELD",
         "reasons": ["STEPS: NOT DRAWN - consultant item (access ladder or steps?) open: not drawn on the GF plan, ST "
                     "p.7 or the sections, an absence of evidence, not a verified zero (owner 2026-10-22 16:45); "
                     "closed only on a drawing or a consultant answer"],
         "printed": "GF plan, ST p.7, NW cut: no steps / benches drawn",
         "guard_element": {"element_id": "POOL-1", "part": "STEPS"}},
    ]
    return {"piece": "POOL_CONCRETE", "item_code": "STR.CONC.POOL", "unit": "m3", "source": src,
            "scope": {"physical_element": "POOL", "floors": ["GROUND"],
                      "supersede_lines": [
                          {"element_id": "P-C:SCOPE:POOL:GROUND:CC-4075a81d7f:FLOOR", "floor": "GROUND",
                           "convention_qty": 1.51125,
                           "why": "the pool base: route convention 0.25 m on a 6.045 m2 footprint (55.3 % of the drawn "
                                  "10.936 m2) where ST p.7 prints 40; replaced by the verified base 4.374226 m3"},
                          {"element_id": "P-C:SCOPE:POOL:GROUND:CC-4075a81d7f:WALLS", "floor": "GROUND",
                           "convention_qty": 1.984,
                           "why": "the pool walls: route convention height 1.60 on a 1.24 m2 band (half the ring, the "
                                  "straight runs only) where the drawn band is 2.357 m2 and the RC height 1.20; "
                                  "replaced by the verified walls 2.828071 m3"}],
                      "other_elements": [], "retire_lines": []},
            "records": recs,
            "declared_totals": {"released_added": 7.202297, "convention_superseded": 3.49525, "item_move": 3.707047},
            "line_group": {"POOL-1": "PARTIALLY VERIFIED (owner whole-line rule 2026-10-22 11:50 / 16:45): concrete "
                                     "base + walls 7.202297 m3 VERIFIED; STEPS NOT DRAWN - consultant item (HELD); bar "
                                     "populations R1 / R2 HELD (T-191, a later package); joints / waterstop, membrane "
                                     "termination, finishes UNKNOWN"}}


def dome_piece():
    led = json.loads((ROOT / T185).read_text(encoding="utf-8"))
    s0 = {(x["dome"], x["item"]): x for x in led["lines"] if x["scenario"] == "S0_APPROVED_DESIGN"}
    a, b = s0[("DOME-A", "shell concrete")], s0[("DOME-B", "shell concrete")]
    assert abs(a["qty"] - 2.5406806606781682) < 1e-12 and abs(b["qty"] - a["qty"]) < 1e-12
    assert s0[("DOME-TOWER", "shell concrete")]["qty"] is None
    src = {"file": T185, "sha256": sha(T185), "task": "T-185 (dome scenarios S0 / S1 / S2)",
           "merge_commit": "94e39ee6",
           "checker_run": "Verifier 2026-10-22 18:15 UTC (T-185 MERGED; own re-measure of ST p.7 DETAIL OF DOME)"}
    v18 = ("Verifier 2026-10-22 18:15 (T-185 MERGED 94e39ee6): printed 442 / 190 / 10, R_o 2.23529, R_i 2.13529, "
           "h_i 1.80 -> 2.5407 m3 per dome = worker (0.0 %); 2 terrace domes 5.081 m3 VERIFIED")
    dims = {"kind": "SPHERICAL_CAP_SHELL", "chord_m": 4.42, "rise_m": 1.90, "thickness_m": 0.10,
            "basis": {"chord_m": "PRINTED", "rise_m": "PRINTED", "thickness_m": "PRINTED"}}
    printed = ("ST7757 dxf.dxf p.7 DETAIL OF DOME: DIM 1A38 '442' chord, DIM 1A6D '190' rise to the outer apex, "
               "DIM 19B1 '10' shell (concentric arcs 182B / 182E)")
    recs = []
    for dome, reg, side in (("DOME-A", "DOME-1", "west"), ("DOME-B", "DOME-2", "east")):
        recs.append({"element": dome, "component": "SHELL", "floor": "2F", "state": "RELEASED",
                     "value": round(s0[(dome, "shell concrete")]["qty"], 6), "dims": dims, "verified_by": v18,
                     "printed": printed, "geometry_source": "CAD_VECTOR",
                     "formula": "pi/3 [h^2 (3 R_o - h) - h_i^2 (3 R_i - h_i)], c 4.42, h 1.90, t 0.10: R_o = (2.21^2 + "
                                "1.90^2) / 3.80 = 2.235289, R_i 2.135289, h_i 1.80 (shell above the springing; the "
                                "ring and the drum are their own items)",
                     "guard_element": {"element_id": reg, "part": "SHELL"},
                     "info": {"side": side, "scenario": "S0_APPROVED_DESIGN", "register_element": reg,
                              "intrados_m2": round(s0[(dome, "shell intrados (soffit form / internal finish)")]["qty"], 3),
                              "extrados_m2": round(s0[(dome, "shell extrados (external finish / waterproofing)")]["qty"],
                                                   3)}})
    beside = [{"scenario": x["scenario"], "element": x["dome"], "item": x["item"], "unit": x["unit"], "qty": x["qty"],
               "status": x["status"], "basis": x["basis"], "released": False}
              for x in led["lines"] if x["scenario"] != "S0_APPROVED_DESIGN"]
    piece = {"piece": "DOME_SHELL", "item_code": "STR.CONC.DOME", "unit": "m3", "source": src,
             "scope": {"physical_element": "DOMES", "floors": ["2F"],
                       "supersede_lines": [
                           {"element_id": "P-C:SCOPE:DOMES:2F:CC-6e7b8c8d1f:SHELL", "floor": "2F",
                            "convention_qty": 3.685858,
                            "why": "DOME-A (west; register DOME-1): route convention rise = radius 2.211 and shell "
                                   "0.12 on the outer area where ST p.7 prints 190 / 10; replaced by the verified "
                                   "shell 2.540681 m3"},
                           {"element_id": "P-C:SCOPE:DOMES:2F:CC-a0729cfebc:SHELL", "floor": "2F",
                            "convention_qty": 3.685858,
                            "why": "DOME-B (east; register DOME-2): as DOME-A; replaced by the verified shell "
                                   "2.540681 m3"}],
                       "other_elements": [
                           {"element_id": "DG5:DOME-3:SHELL", "floor": "2F",
                            "why": "the upper-roof dome (Q-27 A): architecture only, no structural detail; the V3.0.6 "
                                   "held placeholder stays (HELD, never 0, never the freelancer's 2.26)"}],
                       "retire_lines": [
                           {"element_id": "P-C:STAIRS:1F:SITE-b845e1e78b1f74a8", "floor": "1F",
                            "item_code": "STR.CONC.STAIR", "convention_qty": 4.450745, "counted_by": "DOME-B:SHELL",
                            "why": "DOME-B (east) drawn on its own slab sheet: the zone's face (SH04, the 1F roof slab "
                                   "sheet) lies round the east dome centre of that sheet (20 radial lines to r 2.211 "
                                   "on the opening layer); the same dome is drawn again on SH02, where the route took "
                                   "it as the 2F dome line CC-a0729cfebc; it is not a stair"}]},
             "records": recs,
             "declared_totals": {"released_added": 5.081361, "convention_superseded": 7.371716,
                                 "item_move": -2.290355},
             "line_group": {"DOMES": "terrace dome shells 5.081361 m3 VERIFIED (S0); rings (S0 CONFLICT plan band vs "
                                     "detail ring, depth 'AS PER ARCH'), drums, shell bars, the upper-roof dome HELD; "
                                     "S1 client request beside, never released; S2 UNKNOWN"}}
    return piece, beside


def inputs(project_id):
    pool = pool_piece()
    dome, beside = dome_piece()
    ev2 = json.loads((ROOT / EV2).read_text(encoding="utf-8"))
    if ev2 != evidence_v2():
        raise SystemExit(f"{EV2} is not version 1 + the T-193 records: rebuild it with --write-evidence")
    sys.path.insert(0, str(ROOT / "research/agents_t187"))
    import t187_inputs as L6   # noqa: E402  (V3.0.6 mapping additions and placeholders, unchanged)
    return {"schema": "URBAN_V307_INPUTS_V1", "project": project_id, "pieces": [pool, dome], "beside": beside,
            "guard": {"source": {"file": "engine/source/default_guard.py",
                                 "sha256": sha("engine/source/default_guard.py"), "task": "T-186 (default guard)",
                                 "merge_commit": "18b12176",
                                 "checker_run": "Verifier 2026-10-22 17:00 UTC (T-186 MERGED); T-190 465e0015"},
                      "evidence": ev2, "evidence_file": EV2, "evidence_sha256": sha(EV2),
                      "conventions": conventions(), "conventions_file": f"{CONVENTIONS} + {PROFILE}",
                      "conventions_sha256": f"{sha(CONVENTIONS)} + {sha(PROFILE)}",
                      "holding_checks": HOLD, "recorded_checks": RECORD, "equal_value_rebase": True,
                      "mapping_additions": L6.MAPPING_ADDITIONS, "placeholders": L6.PLACEHOLDERS,
                      "new_records": [r["id"] for r in NEW_RECORDS]}}


if __name__ == "__main__":
    if sys.argv[1:] == ["--write-evidence"]:
        (ROOT / EV2).write_text(json.dumps(evidence_v2(), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print("written", EV2, sha(EV2))
