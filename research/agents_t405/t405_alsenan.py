"""T-405 on the development villa: the PLASTER CORNER BEAD edge ledger (B4-09), every plaster arris once.

    python3 -I research/agents_t405/t405_alsenan.py --write | --check
    python3 -I research/agents_t405/t405_alsenan.py --geometry <P7757.dxf> <ARCH_ROOMS.json of an ARCH_TAKEOFF_V2.9 run>

--write builds EDGE_LEDGER_T405.csv and summary.json from committed inputs only: the merged T-292 plaster face-to-line
ledger (finish class, owner height, drawing plaster top, FIN.PLASTER line ids), the merged T-313 r2 reveal ledger
(door / window rings, heights and their evidence), the merged T-377 arched outlines (W15 / W16 / W26), the T-162 r2
exterior corners (T-172 VERIFIED geometry) and the CORNERS table below (own reading this run: every reflex vertex of the
engine room polygons named by the wall / column entity that makes it). --check rebuilds byte for byte. --geometry re-reads
the CORNERS table from the private copies (counts, vertex indices and handles only; nothing written). No coordinate,
image or client name is committed.
"""

from __future__ import annotations

import csv
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import t405_bead_rules as B  # noqa: E402

T292 = os.path.join(ROOT, "research", "agents_t292")
T313 = os.path.join(ROOT, "research", "agents_t313", "REVEAL_LEDGER_T313.csv")
T162 = os.path.join(ROOT, "research", "agents_t162", "CORNERS_R2_T162.csv")
DXF_SHA8 = "ab54dd55"

# room (T-292 id) -> (engine room of the ARCH_TAKEOFF_V2.9 run, [(vertex index in ccw order, class, handles, note)])
# Own reading this run: B.arris_vertices on the engine polygon, each vertex matched to the entities within 12 mm.
COL = "EXTERNAL_CORNER"
CORNERS = {
    "1F-01": ("1F-RB72F22", [(6, COL, "2FFC", "column 2FFA / 2FFC proud 0.05 (face 0.70)"),
                             (7, COL, "2FFC", "same column, second arris"),
                             (16, COL, "3002", "column 3000 / 3002 proud 0.05 (face 0.80)"),
                             (17, COL, "3002", "same column, second arris")]),
    "1F-04": ("1F-RED0D19", [(13, COL, "2FFC", "column 2FFA / 2FFC proud 0.05 on the 1F-04 side (face 0.70; "
                                               "the 1F-01 side arrises are other vertices: no shared key)"),
                             (14, COL, "2FFC", "same column, second arris")]),
    "1F-10": ("1F-R0E919A", []),
    "1F-11": ("1F-R3CFCFD", [(3, COL, "2FEA", "column 2FEA proud 0.05 (return 0.30)"),
                             (6, COL, "300B", "column 3009 / 300B proud 0.05 (face 0.35)"),
                             (11, COL, "2FDB", "column 2FD9 / 2FDB proud 0.05 (face 0.475)"),
                             (13, "WALL_END", "C09 C15", "wall nib 0.15 thick standing 0.45 into the room (layer 1 "
                                                         "lines C09 / C0B / C15), first arris"),
                             (14, "WALL_END", "C0B C15", "same nib, second arris (layer-5 counter lines B0C / C17 "
                                                         "also end here: the wall lines decide, R-T368-6)"),
                             (16, COL, "2FDB", "column 2FDB, second arris (face 0.375)"),
                             (25, COL, "C0A C16", "wall corner 0.15 / 0.15 (layer 1 C0A / C16)")]),
    "1F-13": ("1F-R78C367", [(23, COL, "AEB AF7", "wall corner 0.15 / 0.15 (layer 1)"),
                             (27, COL, "300E", "column 300C / 300E proud 0.05 (face 0.80)"),
                             (28, COL, "300E", "same column, second arris"),
                             (31, COL, "3008", "column 3006 / 3008 proud 0.05 (face 0.60)"),
                             (32, COL, "3008", "same column, second arris"),
                             (58, COL, "AFB B10", "wall corner 0.15 / 0.15 (layer 1)"),
                             (69, COL, "AFE B16 2FF3", "wall AFE / B16 meeting column 2FF1 / 2FF3 (0.20 / 0.20), at "
                                                       "the stair-hall line outside the stair flights: hall side")]),
    "ST-1F": ("1F-R78C367", [(10, COL, "3005", "column 3003 / 3005 proud 0.05 inside the stair flights' extent"),
                             (11, COL, "3005", "same column, second arris")]),
    "2F-01": ("2F-R4D1B62", [(25, COL, "128A 129A 2F72", "wall 128A / 129A meeting column 2F70 / 2F72 (0.20 / 0.20), "
                                                         "outside the stair flights' extent: lobby side")]),
    "ST-2F": ("2F-R4D1B62", [(10, COL, "2F78", "column 2F76 / 2F78 proud 0.05 inside the stair flights' extent"),
                             (11, COL, "2F78", "same column, second arris")]),
    "2F-03": ("2F-R1DB2D2", []),
    "GF-01": ("GF-R7512EA", []),
    "GF-04": ("GF-R51E127", []),
    "GF-08": ("GF-RC99C2A", [(27, COL, "2F8A", "column 2F88 / 2F8A proud 0.05 (face 1.00)"),
                             (28, COL, "2F8A", "same column, second arris"),
                             (41, COL, "2FB4", "column 2FB2 / 2FB4 proud 0.05 (face 0.70)"),
                             (42, COL, "2FB4", "same column, second arris"),
                             (56, COL, "2FD2", "column 2FD0 / 2FD2 proud 0.05 (face 0.80)"),
                             (57, COL, "2FD2", "same column, second arris"),
                             (60, COL, "2FC6", "column 2FC4 / 2FC6 proud 0.05 (face 0.60)"),
                             (61, COL, "2FC6", "same column, second arris (return 0.25 to wall 337)"),
                             (62, COL, "337 2FC6", "wall 337 corner beside column 2FC6 (0.25 / 0.05)"),
                             (66, COL, "2FC3", "column 2FC1 / 2FC3 proud 0.05 (face 0.70)"),
                             (67, COL, "2FC3", "same column, second arris"),
                             (79, COL, "2FC0", "column 2FBE / 2FC0 proud 0.05 (face 0.90)"),
                             (80, COL, "2FC0", "same column, second arris")]),
    "GF-15": ("GF-R75FBAE", [(2, COL, "2DE 2F0", "wall corner 0.15 / 0.15 (layer 1)"),
                             (12, COL, "2FCC", "column 2FCA / 2FCC proud 0.10 (face 1.00)"),
                             (13, COL, "2FCC", "same column, second arris"),
                             (55, COL, "2FC9", "column 2FC7 / 2FC9 proud 0.05 (face 0.50)"),
                             (56, COL, "2FC9", "same column, second arris")]),
    "ST-GF": ("GF-R31F8AE", [(14, COL, "2FBD", "column 2FBB / 2FBD proud 0.05 (face 0.50)"),
                             (15, COL, "2FBD", "same column, second arris")]),
}
# reflex vertices of the same polygons that are NOT plaster beads (listed, never counted)
NOT_BEADS = {
    "GF-08": [(48, "TILED_FACE", "2FAE", "column 2FAC / 2FAE proud 0.05 inside the open pantry (tiled host walls, "
                                         "UP-PANTRY): tile external corner of T-368 (L-f5c5a1a9c9ee2b644cb5), "
                                         "never a plaster bead (Q-37 A)")],
}
ARC_FACETS = {"1F-11": (24, "W17 curved glazing / curved wall: one smooth surface"),
              "GF-08": (11, "W03 curved floor glazing: one smooth surface"),
              "GF-15": (35, "W03 curved floor glazing: one smooth surface")}

# arched heads (T-238 outline record, T-377 MERGED): developed jambs + head instead of the rectangle
ARCHED = {"W15": (6.8461, 7.7500), "W16": (6.8461, 7.7500), "W26": (4.0709, 4.6000)}

HEIGHT_SOURCE = "G1 (OWNER_RECONCILIATION_2026-10-20), Q-43 / Q-48 A owner plaster height (T-292 owner_h_m)"
DWG_SOURCE = "T-292 dwg_plaster_top_m (slab soffit / roof datum DCR-6; T-237 part 4)"
OD = "OD-V3B-8 STEEL_PLASTER_ANGLE_BEADS (owner 2026-10-04) + URBAN-FINISH-EXTRAS-SEPARATE-ITEMS@v1"

# the freelancer (Drive 'Alsenan chalet project', the interior / Sigma workbook; OWNER_NOTES_SIGMA_2026-10-21 s.
# 'Correction: how the corners are counted', main chat 2026-10-22 07:10)
FREELANCER = {"exterior_ml": 1297.35, "exterior_A_arrises_stop_ends_ml": 547.47, "exterior_B_corners_ml": 749.88,
              "exterior_payable_half_ml": 648.675, "interior_corners_ml": 770.75, "interior_payable_half_ml": 385.375,
              "exterior_B_parapet_tops_ml": 280.59, "exterior_B_boundary_wall_ml": 91.44, "exterior_B_drip_ml": 181.70,
              "exterior_B_vertical_corners_ml": 148.0}


def _read(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


ENGINE = {}   # T-292 room -> engine room polygon (filled by faces())


def faces():
    """room -> B.Face from the merged T-292 ledger (FIN.PLASTER rows of DRY / SHAFT / WET rooms)."""
    rows = [r for r in _read(os.path.join(T292, "FACE_TO_LINE_LEDGER_T292.csv")) if r["item_code"] == "FIN.PLASTER"]
    lines = {}
    for r in _read(os.path.join(T292, "LINE_SUMMARY_T292.csv")):
        if r["item_code"] == "FIN.PLASTER" and r["ledger_rooms"] and r["line_state"] != "NOT_APPLICABLE_WITH_EVIDENCE":
            lines[r["ledger_rooms"]] = r["line_id"]
    out = {}
    for room in sorted({r["room"] for r in rows}):
        rr = [r for r in rows if r["room"] == room]
        ENGINE[room] = rr[0]["engine_rooms"]
        cls = rr[0]["finish_class"]
        oh = _num(rr[0]["owner_h_m"])
        top = _num(rr[0]["dwg_plaster_top_m"])
        annex = any("annex" in (r["owner_source"] + r["owner_held_item"]).lower() for r in rr) or \
            rr[0]["owner_status"] == "HELD" and oh is not None
        if cls == "WET":
            out[room] = B.Face(room, "TILE", None, None, None, lines.get(room, ""))
            continue
        if oh is not None and not annex:
            owner = B.Top(oh, B.OA, HEIGHT_SOURCE)
        else:
            why = ("owner shaft height HELD (Q-72 open; T-173 shaft ledger)" if cls == "SHAFT" else
                   f"annex owner height not established (G2; Q-54 B HOLD, D-39): owner {oh} shown as information")
            owner = B.Top(None, B.HELD, HEIGHT_SOURCE, why)
        dwg = B.Top(None, B.HELD, DWG_SOURCE, f"drawing plaster top {top} m on a HELD datum ({rr[0]['dwg_status']})")
        lo_any = min(v for v in (oh, top) if v is not None) if (oh is not None or top is not None) else None
        out[room] = B.Face(room, "PLASTER", owner, dwg, lo_any, lines.get(room, ""))
    return out


def _status_from(ev):
    ev = (ev or "").upper()
    if ev.startswith("PRINTED") or ev.startswith("DRAWING-CONFIRMED") or ev.startswith("HELD (SILL"):
        return B.DC
    if "OWNER-APPROVED" in ev or ev == "ASSUMED":
        return B.OA
    return None


def _ledger_by_opening():
    by = {}
    for r in _read(T313):
        by.setdefault(r["opening"], []).append(r)
    return by


def interior_corners(F):
    edges = []
    for room, (eng, rows) in sorted(CORNERS.items()):
        face = F[room]
        for vid, cls, handles, note in rows:
            e = B.corner_edge(f"{room}#V{vid:02d}", room, cls, 1, face, handles,
                              f"own reading: {eng} vertex {vid} (ARCH_TAKEOFF_V2.9 run on P7757.dxf {DXF_SHA8}); "
                              f"{OD}", note)
            edges.append(e)
        for vid, cls, handles, note in NOT_BEADS.get(room, []):
            edges.append({"edge_id": f"{room}#V{vid:02d}", "scope": "INTERIOR", "room": room, "class": cls,
                          "count": 1, "owner_m": 0.0, "owner_status": B.NOT_BEAD, "dwg_m": 0.0,
                          "dwg_status": B.NOT_BEAD, "held_range": "", "line_id": face.line_id, "handles": handles,
                          "basis": "VERTICAL", "source": f"own reading: {eng} vertex {vid}", "note": note})
        if room in ARC_FACETS:
            n, why = ARC_FACETS[room]
            edges.append({"edge_id": f"{room}#ARC", "scope": "INTERIOR", "room": room, "class": "ARC_FACET",
                          "count": n, "owner_m": 0.0, "owner_status": B.NOT_BEAD, "dwg_m": 0.0,
                          "dwg_status": B.NOT_BEAD, "held_range": "", "line_id": face.line_id, "handles": "",
                          "basis": "ARC", "source": f"own reading: {eng} ({n} tessellation vertices)", "note": why})
    return edges


def door_faces(F):
    """Every census door / arch / gate, every face once (R-T405-3, R-T405-4)."""
    edges = []
    exterior = {"D-GF-01", "D-GF-03", "D-GF-05", "D-GF-06", "D-GF-07", "D-GF-09", "D-2F-01"}   # T-313 / T-162
    for op, rows in sorted(_ledger_by_opening().items()):
        kind = rows[0]["kind"]
        if kind not in ("DOOR", "ARCH", "GATE"):
            continue
        jam = next(r for r in rows if r["component"] == "JAMBS")
        head = next(r for r in rows if r["component"] == "HEAD")
        rooms = [x for x in jam["room"].split(";") if x]
        groups = []
        for x in rooms:   # two labels of one shared engine polygon = one physical face (R-T405-4)
            g = next((g for g in groups if ENGINE.get(g[0]) and ENGINE.get(g[0]) == ENGINE.get(x)), None)
            if g is None:
                groups.append([x])
            else:
                g.append(x)
        if kind == "GATE":
            edges.append(B.held_edge(f"{op}#ALL", "EXTERIOR", "site", "DOOR_JAMB_HEAD", 2,
                                     "gate width / wall thickness not established (T-313 UNRESOLVED; site frontage, "
                                     "T-396 / T-404 fence)", handles=op, source="T-313 r2 REVEAL_LEDGER"))
            continue
        if kind == "ARCH":
            for g in groups:
                room = "|".join(g)
                face = F.get(g[0])
                if face is not None and face.finish == "TILE":
                    o = B.Opening(op, "ARCH", None, None, B.HELD)
                    edges.append(B.opening_face_edge(f"{op}#{room}", room, o, face, "T-313 r2; T-238"))
                    continue
                why = ("arch outline pending D-45: springing height not printed (Q-55 C is a door height, not an arch "
                       "springing, R-T405-7); head on the drawn arc 1.223795 m (T-238 ARC 2422, DRAWING-CONFIRMED)"
                       if op == "A-GF-01" else "arch drawn on no view (T-313 UNRESOLVED)")
                edges.append(B.held_edge(f"{op}#{room}", "INTERIOR", room, "OPENING_UNDER_HEAD", 3, why,
                                         face.line_id if face else "", op, "T-313 r2 REVEAL_LEDGER; T-238"))
            continue
        h2 = _num(jam["ml"])
        w = _num(head["ml"])
        hst = _status_from(jam["evidence"]) or B.OA
        o = B.Opening(op, "DOOR", w, None if h2 is None else h2 / 2.0, hst)
        for g in groups:
            room = "|".join(g)
            face = F.get(g[0])
            if face is None:
                edges.append(B.held_edge(f"{op}#{room}", "INTERIOR", room, "DOOR_JAMB_HEAD", 3,
                                         "face not in the T-292 face ledger", handles=op, source="T-313 r2"))
                continue
            if len(g) > 1:
                face = B.Face(face.face_id, face.finish, face.owner, face.dwg,
                              min(v for v in (face.lo_any_m, F[g[1]].lo_any_m) if v is not None),
                              f"{face.line_id} | {F[g[1]].line_id}")
            e = B.opening_face_edge(f"{op}#{room}", room, o, face, f"T-313 r2 REVEAL_LEDGER ({jam['basis']}; "
                                    f"head {head['basis']}); {OD}",
                                    "one face of the opening; the other face is its own arris")
            edges.append(e)
        if len(groups) == 1:
            if op in exterior:
                ring = h2 + w
                edges.append(B.cited_edge(f"{op}#EXT", "EXTERIOR", "facade", "DOOR_JAMB_HEAD", 1, ring, hst,
                                          f"T-313 r2 (2 h + w, outer face; T-162 r2 'door arrises at 2.20' carries "
                                          f"the 6 assumed ones 32.200, D-GF-07 printed 2.50); {OD}", "FIN.EXT.FINISH "
                                          "(T-314 lines)", op, "STRAIGHT"))
            else:
                edges.append(B.held_edge(f"{op}#FAR", "INTERIOR", "unlabelled space", "DOOR_JAMB_HEAD", 3,
                                         "far side is an unlabelled engine space not in the T-292 face ledger "
                                         "(D-1F-07: the lobby by 1F-10 / A-1F-01): finish of that face not established",
                                         handles=op, source="T-313 r2; T-249 OPENINGS (OP-019)",
                                         physical_m=h2 + w))
    return edges


def windows(F):
    """Room faces (flush frames) and outer faces (cited T-313 r2 rings, arched heads developed: T-377)."""
    edges = []
    sills = []
    for op, rows in sorted(_ledger_by_opening().items()):
        if rows[0]["kind"] not in ("WINDOW", "FLOOR_GLAZING"):
            continue
        room = rows[0]["room"]
        face = F.get(room)
        lid = face.line_id if face else ""
        ins = [r for r in rows if r["side"] == "IN" and r["component"] in ("JAMBS", "HEAD")]
        if all(r["state"] == "NONE" for r in ins):
            edges.append(B.flush_window_face(f"{op}#IN", room, B.Opening(op, "WINDOW", None, None, B.DC),
                                             face or B.Face(room, "UNKNOWN", None, None), "T-313 r2 WINDOW_DEPTHS"))
        else:
            edges.append(B.held_edge(f"{op}#IN", "INTERIOR", room, "WINDOW_JAMB_HEAD", 3,
                                     "curved opening: room side not measured (T-238 / T-302 developed surface)",
                                     lid, op, "T-313 r2"))
        jam = next((r for r in rows if r["side"] == "OUT" and r["component"] == "JAMBS"), None)
        head = next((r for r in rows if r["side"] == "OUT" and r["component"] == "HEAD"), None)
        sill = next((r for r in rows if r["side"] == "OUT" and r["component"] == "SILL"), None)
        if jam and head and jam["state"] == "MEASURED" and head["state"] == "MEASURED":
            ring = _num(jam["ml"]) + _num(head["ml"])
            basis, note = "STRAIGHT", ""
            if op in ARCHED:
                dev, rect = ARCHED[op]
                assert abs(rect - ring) < 1e-6, (op, ring, rect)
                ring, basis = dev, "ARC_DEVELOPED"
                note = f"arched: developed outline {dev} m.l instead of the rectangle {rect} (T-377 R-T377-2, T-238)"
            st = _status_from(jam["height_status"]) or B.DC
            edges.append(B.cited_edge(f"{op}#OUT", "EXTERIOR", "facade", "WINDOW_JAMB_HEAD", 1, ring, st,
                                      f"T-313 r2 REVEAL_LEDGER outer jambs + head ({jam['height_status'][:40]}); {OD}",
                                      "FIN.EXT.FINISH (T-314 lines)", op, basis, note))
        else:
            edges.append(B.held_edge(f"{op}#OUT", "EXTERIOR", "facade", "WINDOW_JAMB_HEAD", 3,
                                     "outer jambs / head not measured (T-313: " + (jam["state"] if jam else "none")
                                     + "; " + (jam["height_status"][:50] if jam else "") + ")", "", op, "T-313 r2",
                                     physical_m=_num(head["ml"]) if head and head["state"] == "MEASURED" else None,
                                     note="head width only, where measured"))
        if sill and sill["state"] == "MEASURED" and _num(sill["ml"]):
            sills.append((op, _num(sill["ml"])))
    edges.append(B.held_edge("WINDOW_SILL_EDGES", "EXTERIOR", "facade", "WINDOW_SILL_EDGE", len(sills),
                             "OD-V3B-8: sill edges take a bead only 'where the site method requires' and the "
                             "external sill material / section is not specified (RFI A13): SITE_METHOD_NOT_RECORDED",
                             "", " ".join(o for o, _ in sills), "T-313 r2 external sill rows",
                             physical_m=round(sum(v for _, v in sills), 4)))
    return edges


def exterior_corners():
    """T-162 r2 corner components (T-172 VERIFIED geometry) with the bead decision per component."""
    rows = {r["COMPONENT"]: r for r in _read(T162)}
    edges = []
    for comp, eid, cls in (("GF convex arrises", "EXT#GF-CONVEX", "EXTERNAL_CORNER"),
                           ("1F convex arrises", "EXT#1F-CONVEX", "EXTERNAL_CORNER"),
                           ("2F convex arrises", "EXT#2F-CONVEX", "EXTERNAL_CORNER"),
                           ("GF wall ends at the two passage mouths (facade + passage side)", "EXT#GF-MOUTHS",
                            "MOUTH_WALL_END")):
        r = rows[comp]
        edges.append(B.cited_edge(eid, "EXTERIOR", "facade", cls, int(r["COUNT"]), float(r["PHYSICAL_ML"]), B.DC,
                                  f"T-162 r2 CORNERS_R2 ({r['SOURCE']}; T-172 VERIFIED); {OD}",
                                  "FIN.EXT.FINISH (T-314 lines)", "", "VERTICAL",
                                  f"held parts of the same corners: {r['HELD_OR_UNKNOWN']}"))
    for comp, eid in (("parapet outer top arrises", "EXT#PARAPET-OUTER-TOP"),
                      ("parapet inner top arrises", "EXT#PARAPET-INNER-TOP")):
        r = rows[comp]
        edges.append(B.held_edge(eid, "EXTERIOR", "roof", "PARAPET_TOP", int(r["COUNT"]),
                                 "COPING_NOT_SPECIFIED: a coping / cap over the parapet top hides both top arrises "
                                 "(OD-V3B-8 'never on a hidden edge'); material and section not specified (RFI A13, "
                                 "T-324)", "", "", "T-162 r2 CORNERS_R2; T-324", physical_m=float(r["PHYSICAL_ML"])))
    for comp, eid, cls, why in (
            ("1F slab edge over open air (lower arris)", "EXT#SLAB-EDGE", "SLAB_EDGE",
             "slab edges below +5.50 HELD (Q-68; T-162 r2)"),
            ("arch frames SE stair tower / NW pool court", "EXT#ARCH-FRAMES", "WINDOW_JAMB_HEAD",
             "arch frames HELD (T-162 r2; T-238 D-45)"),
            ("drip / throat under a slab edge or parapet cap", "EXT#DRIP", "SLAB_EDGE",
             "drip / throat profile not specified (RFI A13): a drip profile is not an angle bead"),
            ("boundary wall arrises", "EXT#FENCE", "FENCE_EDGE",
             "boundary fence: block HELD (T-396), fence finishes T-404 (arrises named for T-405): top / end arrises "
             "follow the fence coping and block decision")):
        edges.append(B.held_edge(eid, "EXTERIOR", "facade", cls, 1, why, "", "", f"T-162 r2 CORNERS_R2 '{comp}'"))
    return edges


def other_interior():
    """Interior edge classes whose bead length is not established this run (named, never 0)."""
    return [
        B.held_edge("LIFT#GF-08", "INTERIOR", "GF-08", "OPENING_UNDER_HEAD", 3,
                    "lift entrance (engine passage OP-011 into the 1.80 x 1.80 shaft GF-R89E756, masonry jambs, 1.00): "
                    "landing frame by the lift supplier, entrance height not printed: LIFT_ENTRANCE_HEAD_NOT_ESTABLISHED"
                    " (T-401 owns the shaft)", "L-8cecb1d010d5aafbf25d", "OP-011", "ARCH_OPENINGS (V2.9 run)"),
        B.held_edge("LIFT#1F-13", "INTERIOR", "1F-13", "OPENING_UNDER_HEAD", 3,
                    "lift entrance (engine passage OP-007 into shaft 1F-RCCB686, 1.00): LIFT_ENTRANCE_HEAD_NOT_ESTABLISHED",
                    "L-9b4a7bab033d677e2017", "OP-007", "ARCH_OPENINGS (V2.9 run)"),
        B.held_edge("LIFT#2F-01", "INTERIOR", "2F-01|ST-2F", "OPENING_UNDER_HEAD", 3,
                    "lift entrance (engine passage OP-002 into shaft 2F-R2BDCEE, 1.00): LIFT_ENTRANCE_HEAD_NOT_ESTABLISHED",
                    "L-ae0cdd794cc5fdbe0c29 | L-418121a4b223cb4e8646", "OP-002", "ARCH_OPENINGS (V2.9 run)"),
        B.held_edge("OPEN#ST-GF-OP020", "INTERIOR", "ST-GF", "OPENING_UNDER_HEAD", 3,
                    "doorless 0.90 opening stair hall -> GF-11 (engine passage OP-020, column + masonry jamb): head not "
                    "read on the slab plan this run (R-T368-7 reading pending): OPEN_SIDE_HEAD_NOT_READ; the GF-11 face "
                    "is tiled (no bead)", "L-95f2c45c2eccaaeccb08", "OP-020", "ARCH_OPENINGS (V2.9 run)"),
        B.held_edge("OPEN#GF-08-OP003", "INTERIOR", "GF-08", "OPENING_UNDER_HEAD", 2,
                    "11.22 m open side of the living zone toward the court / pantry zones (engine passage OP-003, "
                    "column jambs both ends): an engine zone edge, not a drawn opening; whether its end columns stand "
                    "proud into the court is not read this run: ZONE_EDGE_NOT_READ", "L-8cecb1d010d5aafbf25d", "OP-003",
                    "ARCH_OPENINGS (V2.9 run)"),
        B.held_edge("STAIR#GF-08", "INTERIOR", "GF-08", "STAIR_EDGE", 1,
                    "round stair inside GF-08 (radial flights) and the two staircases: stringer / soffit / landing-edge "
                    "arrises follow the stair soffit finish, BLANK in the candidate (T-284 / T-281)", "", "",
                    "T-284 Gate B"),
        B.held_edge("VOID#1F-13", "INTERIOR", "1F-13", "VOID_EDGE", 1,
                    "double-height void V01 (16.005 m2) in the 1F slab: the slab-edge soffit arris follows the GF "
                    "ceiling finish under it and the guard fixing (T-393 railings, T-348 faces round the void): "
                    "CEILING_FINISH_AT_VOID_NOT_ESTABLISHED", "", "V01", "ARCH_ROOMS (V2.9 run)"),
        B.held_edge("CEIL#ALL", "INTERIOR", "all dry rooms", "CEILING_EDGE", 1,
                    "beam soffits / bulkheads: the plaster stops at the decor ceiling under the owner method (G1), so "
                    "beam arrises above it are hidden; bulkhead edges are gypsum (27.9345 m2 bulkheads, T-284), not "
                    "plaster; a room left without a decor ceiling would expose beam arrises: CEILING_TYPE_PER_ROOM "
                    "(O-P8-02)", "", "", "T-284 Gate B; O-P8-02"),
    ]


def stop_ends():
    """STOP_END: the plastered face length of every dry / shaft room (T-292 ROOM_CLOSURE t128_face_m): physical length
    of a horizontal plaster termination; no Urban rule or printed note asks for a stop profile there -> HELD."""
    rows = [r for r in _read(os.path.join(T292, "ROOM_CLOSURE_T292.csv")) if r["finish_class"] in ("DRY", "SHAFT")]
    phys = round(sum(float(r["t128_face_m"]) for r in rows), 4)
    return [B.held_edge("STOP_END#ALL", "INTERIOR", "dry + shaft rooms", "STOP_END", len(rows),
                        "STOP_END_SCOPE_NOT_IN_URBAN_RULE: a horizontal plaster termination (top under the decor ceiling "
                        "or bottom at the skirting) is not an angle-bead arris (OD-V3B-8) and no Urban rule or printed "
                        "note asks for a stop profile; the freelancer's column A 'ends' (282.85 m.l) is this class",
                        "", " ".join(r["room"] for r in rows), "T-292 ROOM_CLOSURE t128_face_m", physical_m=phys)]


# the freelancer's interior corners cover row 17 = detail sheet rows 4 .. 44, column A 282.85 + column B 487.90 (raw
# rows: tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json, file PLS, detail sheet), grouped by physical class
FREELANCER_INTERIOR = [
    ("A: room-perimeter 'ends' (rows 4-24, per room = its perimeter less its door widths)", 282.85, "STOP_END",
     "RULE_DIFFERENCE (scope): not an arris; engine HELD with the physical face length beside it"),
    ("B: room corners at 3.6 / 3.8 / 3.4 m (rows 4, 6, 7, 8, 9, 13, 14, 15)", 100.0, "EXTERNAL_CORNER + WALL_END",
     "count ENGINE_RIGHT (every arris drawn at a column / wall entity, 0.05 m column projections included); height "
     "RULE_DIFFERENCE (his storey heights vs the owner plaster height G1)"),
    ("B: door rings, 14 doors x 2 faces x (2 x 2.35 + 1.00) (row 26)", 159.6, "DOOR_JAMB_HEAD",
     "UNRESOLVED count (his 14 doors vs 27 census doors, 26 plastered interior faces); height RULE_DIFFERENCE "
     "(2.35 vs Q-55 C 2.20)"),
    ("B: window / door perimeters 'external spaces' (rows 29-41)", 155.3, "FLUSH_FRAME / exterior rings",
     "ENGINE_RIGHT for the room side (frame flush with the room face on every straight window, T-313 MERGED: no room-"
     "side arris); the outer-face arrises are in the exterior ledger (T-313 rings), not interior"),
    ("B: bathroom windows (row 42)", 26.4, "TILED_FACE", "ENGINE_RIGHT: tiled face, no plaster bead (Q-37 A)"),
    ("B: lift doors (row 10)", 17.4, "OPENING_UNDER_HEAD (lift)", "UNRESOLVED: lift entrance head / frame HELD"),
    ("B: stair stringers (row 17)", 29.2, "STAIR_EDGE", "UNRESOLVED: stair soffit finish BLANK (T-284)"),
]


def build():
    F = faces()
    edges = (interior_corners(F) + door_faces(F) + windows(F) + other_interior() + stop_ends()
             + exterior_corners())
    return B.check_ledger(edges)


COLS = ["edge_id", "scope", "room", "class", "count", "owner_m", "owner_status", "dwg_m", "dwg_status", "held_range",
        "line_id", "handles", "basis", "source", "note"]


def render(edges):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=COLS, lineterminator="\n")
    w.writeheader()
    for e in edges:
        w.writerow({k: ("" if e.get(k) is None else (f"{e[k]:.4f}" if isinstance(e.get(k), float) else e.get(k)))
                    for k in COLS})
    return buf.getvalue()


def summary(edges):
    def part(scope):
        return [e for e in edges if e["scope"] == scope]
    interior, exterior = part("INTERIOR"), part("EXTERIOR")
    out = {"task": "T-405", "family": "B4-09 plaster corner beads / profiles (m.l)", "dxf_sha8": DXF_SHA8,
           "owner_basis": OD, "rows": len(edges),
           "interior_owner_method": B.totals(interior, "owner"), "interior_drawing_method": B.totals(interior, "dwg"),
           "exterior": B.totals(exterior, "owner"), "all_owner_method": B.totals(edges, "owner"),
           "interior_corner_vertices": sum(len(v[1]) for v in CORNERS.values()),
           "interior_corner_vertices_not_beads": sum(len(v) for v in NOT_BEADS.values()),
           "freelancer": FREELANCER,
           "freelancer_interior_by_class": [{"his_rows": a, "his_ml": b, "engine_class": c, "verdict_proposal": d}
                                            for a, b, c, d in FREELANCER_INTERIOR],
           "freelancer_interior_check_ml": round(sum(b for _, b, _, _ in FREELANCER_INTERIOR), 2)}
    ip = out["interior_owner_method"]["measured_m"]
    ex = out["exterior"]["measured_m"]
    out["engine_vs_freelancer"] = {
        "interior_measured_m": ip, "interior_freelancer_m": FREELANCER["interior_corners_ml"],
        "interior_diff_m": round(ip - FREELANCER["interior_corners_ml"], 4),
        "interior_diff_pct": round(100.0 * (ip - FREELANCER["interior_corners_ml"]) / FREELANCER["interior_corners_ml"], 2),
        "exterior_measured_m": ex, "exterior_freelancer_m": FREELANCER["exterior_ml"],
        "exterior_diff_m": round(ex - FREELANCER["exterior_ml"], 4),
        "exterior_diff_pct": round(100.0 * (ex - FREELANCER["exterior_ml"]) / FREELANCER["exterior_ml"], 2),
        "note": "measured only; every HELD class is outside these figures (never 0) and listed by count"}
    return out


def outputs():
    edges = build()
    return {"EDGE_LEDGER_T405.csv": render(edges),
            "summary.json": json.dumps(summary(edges), indent=1, sort_keys=True, ensure_ascii=False) + "\n"}


def geometry(dxf_path, rooms_json):
    """Re-read CORNERS on the private copies: arris vertex indices per engine room, handles within 12 mm, and no vertex
    shared by two edge ids (prints ids and handles only)."""
    import ast
    import ezdxf
    rooms = {r["room_id"]: r for r in json.load(open(rooms_json, encoding="utf-8"))["rooms"]}
    doc = ezdxf.readfile(dxf_path)
    pts_by = {}
    for e in doc.modelspace().query("LINE LWPOLYLINE"):
        pts = ([tuple(e.dxf.start)[:2], tuple(e.dxf.end)[:2]] if e.dxftype() == "LINE"
               else [tuple(p[:2]) for p in e.get_points()])
        pts_by[e.dxf.handle] = pts
    bad = 0
    expected = {}
    for room, (eng, rows) in CORNERS.items():
        expected.setdefault(eng, set()).update(v for v, *_ in rows)
    for room, rows in NOT_BEADS.items():
        expected.setdefault(CORNERS[room][0], set()).update(v for v, *_ in rows)
    keys = []
    for eng, want in sorted(expected.items()):
        P = rooms[eng]["polygon_m"]
        P = ast.literal_eval(P) if isinstance(P, str) else P
        arr, arc = B.arris_vertices(P)
        ok = set(arr) == want
        bad += not ok
        print(f"{eng}: arris {sorted(arr)} committed {sorted(want)} {'OK' if ok else 'DIFFERS'}; arc facets {len(arc)}")
        ccw = B._ccw(P)
        for room, (e2, rows) in CORNERS.items():
            if e2 != eng:
                continue
            for vid, _cls, handles, _n in rows + NOT_BEADS.get(room, []):
                x, y = ccw[vid][0] * 1000.0, ccw[vid][1] * 1000.0
                keys.append((f"{room}#V{vid:02d}", (eng[:2], round(x), round(y))))
                for h in handles.split():
                    near = any(abs(px - x) < 12 and abs(py - y) < 12 for px, py in pts_by.get(h, ()))
                    bad += not near
                    if not near:
                        print(f"  {room} v{vid}: handle {h} not within 12 mm DIFFERS")
    try:
        B.check_corner_keys(keys)
        print(f"corner keys: {len(keys)} distinct OK")
    except B.BeadError as exc:
        bad += 1
        print("corner keys DIFFER:", exc)
    for eng in ("1F-R0E919A", "2F-R1DB2D2", "GF-R7512EA", "GF-R51E127"):
        P = rooms[eng]["polygon_m"]
        P = ast.literal_eval(P) if isinstance(P, str) else P
        n = len(B.arris_vertices(P)[0])
        bad += n != 0
        print(f"{eng}: arris {n} (committed 0) {'OK' if n == 0 else 'DIFFERS'}")
    return bad


def main(argv):
    if argv[:1] == ["--write"]:
        for name, text in outputs().items():
            with open(os.path.join(HERE, name), "w", encoding="utf-8", newline="") as f:
                f.write(text)
        print(json.dumps(json.loads(outputs()["summary.json"])["engine_vs_freelancer"], indent=1))
        return 0
    if argv[:1] == ["--check"]:
        bad = 0
        for name, text in outputs().items():
            with open(os.path.join(HERE, name), encoding="utf-8", newline="") as f:
                same = f.read() == text
            print(name, "SAME" if same else "DIFFERS")
            bad += not same
        return 1 if bad else 0
    if argv[:1] == ["--geometry"] and len(argv) == 3:
        return 1 if geometry(argv[1], argv[2]) else 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
