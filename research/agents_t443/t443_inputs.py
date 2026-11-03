"""T-443: URBAN_V3047_INPUTS_V1 for the development villa: the Checker-verified T-441 face tables of the two walled
stair rooms (merged ece154fe) re-booked as the stair-room skirting split of ARCH_TAKEOFF_V3.0.47. Nothing here is
measured anew: every stretch, handle, opening id and cause is the merged T-441 table (research/agents_t441/
t441_alsenan.py parts(), FLIGHT_STRETCHES), every closure term the merged T-441 summary (s.3). Line ids are the
candidate of record's (V3.0.46 on the drawings of the T-441 run; bound and checked at load: a stale id stops the run).

    from t443_inputs import build; build(project_id)
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "agents_t441"))
import t441_alsenan as T441  # noqa: E402

SCHEMA = "URBAN_V3047_INPUTS_V1"
SOURCES = [
    {"task": "T-441", "file": "research/agents_t441/FACES_T441.csv",
     "sha256": "084fdf8f95b6f3e15753112e36bf7152f0ea33b8a0d73b57ae58c570131fb592", "merge_commit": "ece154fe",
     "checker_run": "Verifier 2026-11-01T19:55Z session_01E6cPnciuxNnnDivYkfWWZ6 Gate A PASS (own re-measure 2F lobby "
                    "3.350 lm AGREE; OP-002 a lift)"},
    {"task": "T-410", "file": "research/agents_t410/SIDE_TABLE_T410.csv",
     "sha256": "794c27f56afd01c7d173c6710a32f14e6c65c0b38e1385e87f31004bf61d9a85", "merge_commit": "2fb91300",
     "checker_run": "Verifier 2026-11-01T01:53Z session_01E6cPnc5gL6RHXBManM5toB Gate A r2 PASS (stair side table)"},
]
TASKS = ["T-441", "T-410"]

PARENT_GF = "L-47fa825d197d32754240"       # FIN.SKIRTING GF-R31F8AE, BLOCKED_RFI (T-441 summary parents)
PARENT_2F = "L-b8d4a7f04277deb1b0b0"       # FIN.SKIRTING 2F-R4D1B62, BLOCKED_RFI
FLOOR = {"GF-ST-HALL": "L-f53d498668da3dc7c228",      # FIN.FLOOR.FINISH_HELD 4.805 m2 (T-421, V3.0.38)
         "GF-ST-LOBBY030": "L-b4441a1b55eda53d98ea",  # FIN.FLOOR.FINISH_HELD 1.3225 m2
         "2F-ST-LOBBY": "L-9bd25c0cec9da3a8f4d2",     # FIN.FLOOR.PORCELAIN 2.200 m2 (Q-70 A)
         "2F-ST-ARRIVAL": "L-5d2be30dd8d2ffeacc42"}   # FIN.MARBLE.LANDING 2F-R4D1B62:landings, HELD 0 .. 9.225 (T-421)

# the row's word, per part (T-443 row; T-441 s.7 lane I proposal)
PART_STATUS = {
    "GF-ST-HALL": ("DRAWING-CONFIRMED", {"kind": "HELD_WITH_FLOOR", "basis": "the hall floor finish is HELD (T-418 / "
                                                                       "T-421: porcelain floor or marble landing, no "
                                                                       "finish schedule; designer item)"}),
    "GF-ST-LOBBY030": ("DRAWING-CONFIRMED", {"kind": "HELD_WITH_FLOOR", "basis": "the back lobby floor finish is HELD "
                                                                           "(T-418 / T-421; designer item)"}),
    "2F-ST-LOBBY": ("VERIFIED", {"kind": "OWNER_APPROVED", "basis": "porcelain skirting, finish ASSUMED - "
                                                                  "OWNER-APPROVED Q-70 A (dry lobby, tiled floor)"}),
    "2F-ST-ARRIVAL": ("DRAWING-CONFIRMED", {"kind": "HELD_WITH_FLOOR", "basis": "skirting material beside the Q-70 A "
                                                                          "marble landing is not stated (HELD)"}),
}
GROUPS = {   # T-441 held stretches -> one held child per physical face group
    ("GF-ST-HALL", "DIV-E"): "DIVIDER-BAND", ("GF-ST-HALL", "DIV-END"): "DIVIDER-BAND",
    ("GF-ST-HALL", "DIV-W"): "DIVIDER-BAND", ("GF-ST-LOBBY030", "W"): "WEST-FACE",
}
HELD_GROUPS_GF = [
    {"group": "DIVIDER-BAND", "part": "GF-ST-HALL",
     "cause": "solid stair band between the two lower flights: guard upstand or wall face not established, its south "
              "end at the cut (1.05) or the outline (0.45) not settled; skirting along a railing / void edge is defect "
              "B12 territory (T-441 s.2, RFI a)",
     "beside": "2.200 lm on the cut outline, 3.400 lm on the T-418 outline (drawn; never the quantity)",
     "rfi": "GF stair divider between the two lower flights: construction (solid upstand, wall or balustrade on a "
            "curb), its south end on the GF and its finish (designer RFI a, T-441)"},
    {"group": "OP-020-JAMBS", "part": "GF-ST-HALL",
     "cause": "reveal jamb returns of the doorless opening to the wet wash space (column north face, wall end): tile "
              "return or skirting not printed (T-441 s.2, RFI b)",
     "beside": "2 x 0.200, i.e. 0.400 lm (never the quantity)",
     "rfi": "reveal of the doorless opening from the GF stair hall to the wash space: tile return or skirting "
            "(designer RFI b, T-441)"},
    {"group": "WEST-FACE", "part": "GF-ST-LOBBY030",
     "cause": "west boundary of the +0.30 back lobby under the winders: no face drawn on the wall layers; the space "
              "under the winders open or enclosed is not drawn (T-441 s.2, RFI c)",
     "beside": "1.150 lm if the face stands on the drawn line (never the quantity)",
     "rfi": "space under the GF winders beside the +0.30 back lobby: open or enclosed, and where its face stands "
            "(designer RFI c, T-441)"},
]


def _part(p):
    q = copy.deepcopy(p)
    st, mat = PART_STATUS[q["part"] if "part" in q else q["id"]]
    pid = q.pop("id")
    for sd in q["sides"]:
        for x in sd["stretches"]:
            g = GROUPS.get((pid, sd["id"]))
            if g and x["kind"] in ("GUARD_HELD", "HELD", "UNKNOWN"):
                x["group"] = g
            x.pop("candidate_lm", None)
            x.pop("candidate_high_lm", None)
    for j in q.get("jambs") or ():
        j["group"] = "OP-020-JAMBS"
        j.pop("status", None)
    q.update(part=pid, evidence_status=st, evidence_state="MEASURED", material=mat, floor_line=FLOOR[pid])
    q.pop("area_m2", None)
    q.pop("room", None)
    return q


def build(project_id, owner_lines=None):
    """-> the URBAN_V3047_INPUTS_V1 doc. owner_lines: {'GF': id} the stair skirting line named beside the GF flight
    faces (optional; the owner is named by its T-410 stretches either way)."""
    parts = {p["id"]: p for p in T441.parts()}
    ol = owner_lines or {}
    gf = {"parent": PARENT_GF, "room": "GF-R31F8AE", "floor": "GF", "expect": {"evidence_state": "BLOCKED_RFI"},
          "engine_run_lm": 11.1, "source_tasks": TASKS,
          "parts": [_part(parts["GF-ST-HALL"]), _part(parts["GF-ST-LOBBY030"])],
          "held_groups": HELD_GROUPS_GF,
          "owned_elsewhere": [
              {"what": "west shaft face y 1.10 .. 5.00 (wall 0.40 + column 0.60 + wall 0.75 + wall 1.05; window OP-022 "
                       "not a face)", "lm": 2.8, "owner": "T-410 MS1-L.W1 / W1C / W1B / MS1-T west (stair skirting "
                                                          "B7-07 / B7-08, form HELD ORR-007)",
               "owner_line": ol.get("GF")},
              {"what": "MS1-T north face x 0 .. 1.15", "lm": 1.15, "owner": "T-410 MS1-T north (stair skirting)",
               "owner_line": ol.get("GF")},
              {"what": "D1 east face y 2.95 .. 3.85", "lm": 0.9, "owner": "T-410 D1 east (stair skirting)",
               "owner_line": ol.get("GF")}],
          "remainder": [
              {"what": "GF-ST-CN strip north face x 1.15 .. 1.35 (T-418 strip UNREAD)", "lm": 0.2,
               "why": "the strip under the winders between the hall band and the lobby is not read (T-418): its floor "
                      "and so its skirting are open",
               "rfi": "GF strip under the winders (T-418 GF-ST-CN): floored or not; with designer RFI c"}]}
    f2 = {"parent": PARENT_2F, "room": "2F-R4D1B62", "floor": "2F", "expect": {"evidence_state": "BLOCKED_RFI"},
          "engine_run_lm": 16.9, "source_tasks": TASKS,
          "parts": [_part(parts["2F-ST-LOBBY"]), _part(parts["2F-ST-ARRIVAL"])],
          "no_floor": [
              {"what": "north faces y 6.45 (wall 0.10 + 1.40; window OP-003 not a face)", "lm": 1.5,
               "why": "beside the slab opening over the 1F-2F flights: no floor at +9.70 (T-418 O-2F)"},
              {"what": "west faces x 0 from y 1.95 (wall 1.00 + column 0.60 + wall 0.75 + wall 0.75 + column-wall 0.30; "
                       "window OP-008 not a face)", "lm": 3.4,
               "why": "beside the slab opening: no floor at +9.70 (T-418 O-2F)"},
              {"what": "east faces x 2.5 from y 1.95 (the MS2-U lift wall: wall 1.00 + column-wall 0.50 + wall 2.70 + "
                       "0.30)", "lm": 4.5,
               "why": "beside the slab opening: no floor at +9.70; the flight skirting below is T-410's (B7)"}]}
    return {"schema": SCHEMA, "project_id": project_id, "sources": SOURCES,
            "owners": copy.deepcopy(T441.FLIGHT_STRETCHES), "splits": [gf, f2]}
