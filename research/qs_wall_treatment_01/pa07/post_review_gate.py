"""PA07R1 post-review safety gate: fifteen questions, each answered by EXECUTING a synthetic counterexample through the
generic modules (material bands, band topology, planar faces, junctions) or the whole pipeline7, never by pointing at
a test that exists.  PASS means the counterexample produced a loud state (UNRESOLVED / HUMAN_REVIEW / NOT_ESTABLISHED /
blocked gate) or the correct number; FAIL means a wrong number or a wrong role reached an ESTABLISHED / bridge-allowed
state; NOT_TESTED means the fixture could not be executed.  No P7757 geometry anywhere.

Run:  python -m research.qs_wall_treatment_01.pa07.post_review_gate  [OUT_TAG]
"""

from __future__ import annotations

import json
import math
import os
import sys
import tempfile
import traceback
from pathlib import Path

from engine.ingest import band_topology as BT, junctions as JN, material_bands as MB, pipeline7 as P7, planar_faces as PF
from tests import pa07_fixtures as F

BOX = (-2000.0, -2000.0, 14000.0, 10000.0)
REG = {"_REGISTRY_ID": "GATE_TEST", "NORMAL_INTERNAL_PLASTER_HEIGHT": {"VALUE": 3.0, "SOURCE_TYPE": "OWNER_PROJECT_INPUT"}, "DOOR_HEIGHT": {"VALUE": 2.2, "SOURCE_TYPE": "OWNER_PROJECT_INPUT"},
       "DOOR_REVEAL_DEPTH": {"VALUE": 0.15, "SOURCE_TYPE": "OWNER_PROJECT_INPUT"}, "TARTUSHA_HEIGHT": {"VALUE": None, "SOURCE_TYPE": "UNKNOWN"}}


# ----------------------------------------------------------------------------------------------- module-level runner
def run_modules(prims, texts=(), box=BOX, promote=True):
    roles = F.roles_of(prims)
    rows, bands = MB.build("VW-g", prims, roles, view_bbox=box)
    intervals, sites, seals = BT.build_view("VW-g", prims, roles, bands)
    seals = seals + PF.glazing_separators(prims, roles)
    faces, grids = PF.build("VW-g", box, seals, bands, list(texts))
    brows = PF.boundary_faces("VW-g", faces, grids, bands, intervals, seals)
    spaces = PF.space_register("VW-g", faces, brows)
    qa = PF.missing_space_qa(faces, spaces, list(texts))
    cols, beams, ext = JN.build("VW-g", bands, brows, prims, roles)
    return dict(rows=rows, bands=bands, intervals=intervals, sites=sites, seals=seals, faces=faces, brows=brows, spaces=spaces, qa=qa, cols=cols, beams=beams)


def accepted(r):
    return [x for x in r["rows"] if x["MATERIAL_STATUS"] == "ACCEPTED"]


def space_of(r, label):
    for s in r["spaces"]:
        if any(a.get("TEXT") == label for a in s.get("ANCHORS", [])):
            return s
    return None


def text(label, x, y):
    return {"TEXT": label, "X": x, "Y": y, "ROLE": "ROOM_NAME"}


# ----------------------------------------------------------------------------------------------- pipeline-level runner
def to_doc(prims, labels, level="%%p0.00", extra=()):
    P = []
    for p in prims:
        if p.kind == "SEGMENT":
            P.append({"kind": "SEGMENT", "layer": p.provenance.layer, "x1": p.x1, "y1": p.y1, "x2": p.x2, "y2": p.y2, "linetype": p.provenance.linetype})
        else:
            P.append({"kind": "ARC", "layer": p.provenance.layer, "cx": p.cx, "cy": p.cy, "r": p.radius, "a0": p.start_angle, "a1": p.end_angle})
    P += [{"kind": "CIRCLE", "layer": "F", "cx": 2000 + i * 150, "cy": 1000, "r": 20} for i in range(40)]
    for a, b in (((-3000, -3000), (15000, -3000)), ((15000, -3000), (15000, 11000)), ((15000, 11000), (-3000, 11000)), ((-3000, 11000), (-3000, -3000))):
        P.append({"kind": "SEGMENT", "layer": "FRAME", "x1": a[0], "y1": a[1], "x2": b[0], "y2": b[1]})
    P += list(extra)
    lts = {p.get("layer"): "CONTINUOUS" for p in P}
    return {"insunits": 4, "dimlfac": 1.0, "linetypes": lts, "primitives": P,
            "texts": [{"value": t["TEXT"], "x": t["X"], "y": t["Y"]} for t in labels] + ([{"value": level, "x": 500, "y": 500}] if level else []), "dimensions": []}


def run_pipeline(doc, registry=REG, storey=True, **over):
    tmp = Path(tempfile.mkdtemp()); p = tmp / "v.json"; p.write_text(json.dumps(doc), "utf-8")
    cfg = {"PROJECT_ID": "GATE", "SOURCES": [{"PATH": str(p), "KIND": "PRIMITIVE_JSON", "FAMILY": "ARCHITECTURAL"}], "OWNER_PARAMETER_REGISTRY": registry, "CAD_UNITS": "mm",
           "TRADES": ["NORMAL_INTERNAL_PLASTER"], "RULE_VERSION": "T"}
    cfg.update(over)
    if storey:
        pre = P7.run(dict(cfg))
        cfg["OWNER_STOREY_NAMES"] = {k: "GROUND_FLOOR" for k in pre.storey_of_view}
    return P7.run(cfg)


def pipeline_summary(r):
    R = r.registers
    return {"SPACES": [{"LABELS": [a["TEXT"] for a in s["ANCHORS"]], "GEOMETRY_STATUS": s["GEOMETRY_STATUS"], "MATERIAL_MM": s["MATERIAL_BOUNDARY_MM"], "OPENING_MM": s["OPENING_MM"], "UNRESOLVED_MM": s["UNRESOLVED_MM"],
                        "COLUMN_FACE_MM": s["COLUMN_FACE_MM"], "IDENTITY": s["SEMANTIC_IDENTITY"]["STATUS"], "CLASS": s.get("SPACE_CLASS"), "STOREY": s.get("STOREY")} for s in R["PA07_PHYSICAL_SPACE_REGISTER"]["ROWS"]],
            "SITES": [(s["CLASS"], s["STATUS"], s["SPAN_MM"]) for s in R["PA07_OPENING_SITE_REGISTER"]["ROWS"]],
            "SAFETY": [{"BRIDGE_ALLOWED": x["BRIDGE_ALLOWED"], "BLOCKED_BY": x["BLOCKED_BY"]} for x in R["PA07_QUANTITY_SAFETY_REGISTER"]["ROWS"]],
            "LINES": [{"BLOCKED_BY": l.get("BLOCKED_BY"), "VECTOR_LM": (l.get("LENGTH_GEOMETRY") or {}).get("VECTOR_LM"), "QUANTITY_STATUS": l.get("QUANTITY_STATUS"), "REGION_STATUS": l.get("REGION_STATUS")} for l in R["PA07_QUANTITY_INPUT_TRACE"]["LINES"]],
            "VIEW_ROLES": [(v["VIEW_ID"], v["FINAL_ROLE"]) for v in R["SHEET_ROLE_REGISTER"]["VIEWS"]], "STOREYS": [(x["STOREY_NAME"], x["NAME_STATUS"], x.get("STACKED_STOREYS_SUSPECTED")) for x in R["PA07_STOREY_REGISTER"]["ROWS"]]}


# ----------------------------------------------------------------------------------------------- fixtures
def wall(a, b, t=200.0):
    return F.wall(a, b, t)


def door(axis_a, axis_b, t=200.0, leaf=True, jambs=True):
    (xa, ya), (xb, yb) = axis_a, axis_b
    out = []
    if abs(ya - yb) < 1e-9:
        if jambs:
            out += [F.seg("W", (xa, ya - t / 2), (xa, ya + t / 2)), F.seg("W", (xb, yb - t / 2), (xb, yb + t / 2))]
        if leaf:
            out.append(F.arc("D", (xb, yb + t / 2), abs(xb - xa), math.pi / 2, math.pi))
    else:
        if jambs:
            out += [F.seg("W", (xa - t / 2, ya), (xa + t / 2, ya)), F.seg("W", (xb - t / 2, yb), (xb + t / 2, yb))]
        if leaf:
            out.append(F.arc("D", (xa + t / 2, ya), abs(yb - ya), 0.0, math.pi / 2))
    return out


def two_rooms(gap=(1500.0, 2400.0), leaf=True, jambs=True, partition=True):
    """Two 6 x 4 m clear rooms side by side (LIVING west, KITCHEN east), partition on axis x=6000 with a door gap."""
    F.reset()
    P = F.room(0, 0, 12000, 4000, 200)
    if partition:
        P += wall((6000, 0), (6000, gap[0])) + wall((6000, gap[1]), (6000, 4000)) + door((6000, gap[0]), (6000, gap[1]), leaf=leaf, jambs=jambs)
    return P


LABELS2 = [text("LIVING", 3000, 2000), text("KITCHEN", 9000, 2000)]
EXPECTED_ROOM_FACE = 2 * (5900 + 4000) - 900          # each room: clear 5900 x 4000 (partition faces at 5900 / 6100) minus the 900 door


# ----------------------------------------------------------------------------------------------- the fifteen questions
def q01_window_frame():
    """A window in the north wall of a room: gap 2000..3200 with jambs, two frame lines 100 mm apart and a glazing line inside the gap.
    Can the frame pair become an accepted material band or a column, and can the window be ESTABLISHED without a glazing role?"""
    F.reset()
    P = F.room(0, 0, 6000, 4000, 200)
    # north wall inner face y=4000, outer face y=4200 (F.room): cut both faces at 2000..3200 -> redraw the north wall as two pieces on the outer rect
    P = [p for p in P if not (p.kind == "SEGMENT" and abs(p.y1 - p.y2) < 1e-9 and p.y1 in (4000.0, 4200.0))]
    P += [F.seg("W", (0, 4000), (2000, 4000)), F.seg("W", (3200, 4000), (6000, 4000)), F.seg("W", (-200, 4200), (2000, 4200)), F.seg("W", (3200, 4200), (6200, 4200))]
    P += [F.seg("W", (2000, 4000), (2000, 4200)), F.seg("W", (3200, 4000), (3200, 4200))]                         # jambs
    P += [F.seg("WIN", (2000, 4050), (3200, 4050)), F.seg("WIN", (2000, 4150), (3200, 4150)), F.seg("WIN", (2000, 4100), (3200, 4100))]   # frame pair + glazing line, no role
    r = run_modules(P, [text("BED", 3000, 2000)])
    thin = [x for x in accepted(r) if x["THICKNESS_MM"] < MB.WALL_MIN_MM]
    frame_bands = [x for x in r["rows"] if abs(x["THICKNESS_MM"] - 100) < 1 and abs(x["DEVELOPED_LENGTH_MM"] - 1200) < 50]
    frame_acc = [x for x in frame_bands if x["MATERIAL_STATUS"] == "ACCEPTED"]
    win = [s for s in r["sites"] if abs(s["SPAN_MM"] - 1200) < 60]
    sp = space_of(r, "BED")
    ok = not thin and not frame_acc and not r["cols"] and all(s["STATUS"] != "ESTABLISHED" or s["CLASS"] not in ("CONFIRMED_WINDOW_OPENING",) for s in win) and (sp is None or sp["GEOMETRY_STATUS"] != "ESTABLISHED" or sp["COLUMN_FACE_MM"] == 0)
    return ok, {"ACCEPTED_BELOW_WALL_MIN": len(thin), "FRAME_PAIR_BANDS": [(x["MATERIAL_STATUS"], (x.get("REJECTION_REASON") or "")[:60]) for x in frame_bands], "COLUMNS": len(r["cols"]),
                "WINDOW_SITES": [(s["CLASS"], s["STATUS"], s["SPAN_MM"]) for s in win], "SPACE": None if sp is None else (sp["GEOMETRY_STATUS"], sp["MATERIAL_BOUNDARY_MM"], sp["OPENING_MM"], sp["UNRESOLVED_MM"], sp["COLUMN_FACE_MM"])}


def q02_stair():
    """A stair well between two walls: twelve treads 250 mm apart, stringers along the well; with and without a STAIR role."""
    out = {}
    for role in (None, "STAIR_TREAD"):
        F.reset()
        P = F.room(0, 0, 6000, 4000, 200) + wall((2000, 0), (2000, 4000)) + wall((3200, 0), (3200, 4000))
        P += [F.seg("S", (2100, 400 + i * 250), (3100, 400 + i * 250), role=role) for i in range(12)]
        r = run_modules(P)
        tread_bands = [x for x in r["rows"] if abs((x["DEVELOPED_LENGTH_MM"] or 0) - 1000) < 30 and (x["THICKNESS_MM"] or 0) <= 500]
        acc = [x for x in tread_bands if x["MATERIAL_STATUS"] == "ACCEPTED"]
        out[role or "NO_ROLE"] = {"TREAD_PAIR_BANDS": len(tread_bands), "ACCEPTED": len(acc), "STATUSES": sorted({(x["MATERIAL_STATUS"], (x.get("REJECTION_REASON") or "")[:40]) for x in tread_bands}),
                                  "SPACES": [(round(s["AREA_GEOMETRIC_M2"], 2), s["GEOMETRY_STATUS"]) for s in r["spaces"]]}
    ok = all(v["ACCEPTED"] == 0 for v in out.values())
    return ok, out


def q03_single_face_gap():
    """Partition drawn with the west face interrupted for 900 mm and the east face continuous: no door, no opening."""
    F.reset()
    P = F.room(0, 0, 12000, 4000, 200) + [F.seg("W", (6100, 0), (6100, 4000)), F.seg("W", (5900, 0), (5900, 1500)), F.seg("W", (5900, 2400), (5900, 4000))]
    r = run_modules(P, LABELS2, promote=False)
    sites = [(s["CLASS"], s["STATUS"], s["SPAN_MM"], (s.get("REASON") or "")[:50]) for s in r["sites"]]
    doorish = [s for s in r["sites"] if s["CLASS"] in ("CONFIRMED_DOOR_OPENING", "PROBABLE_DOOR_OPENING", "CONFIRMED_OPEN_PASSAGE") and s["STATUS"] == "ESTABLISHED"]
    sp = [(s["GEOMETRY_STATUS"], s["MATERIAL_BOUNDARY_MM"], s["UNRESOLVED_MM"]) for s in r["spaces"]]
    ok = not doorish and all(s["GEOMETRY_STATUS"] != "ESTABLISHED" for s in r["spaces"] if s["AREA_GEOMETRIC_M2"] > 20)
    return ok, {"SITES": sites, "SPACES": sp}


def q04_jambless_gap():
    """Gap in both faces of the partition, no jambs, no leaf: the rooms must not merge into one ESTABLISHED space nor be two ESTABLISHED rooms with a door."""
    r = run_modules(two_rooms(leaf=False, jambs=False), LABELS2, promote=False)
    sites = [(s["CLASS"], s["STATUS"], s["SPAN_MM"]) for s in r["sites"]]
    big = [s for s in r["spaces"] if s["AREA_GEOMETRIC_M2"] > 20]
    ok = all(s["GEOMETRY_STATUS"] != "ESTABLISHED" for s in big) and all(s["STATUS"] != "ESTABLISHED" for s in r["sites"] if s["SPAN_MM"] > 500)
    return ok, {"SITES": sites, "SPACES": [(round(s["AREA_GEOMETRIC_M2"], 2), s["GEOMETRY_STATUS"], s["UNRESOLVED_MM"]) for s in big], "SPACE_COUNT": len(big)}


def q05_curved():
    """(a) a true-arc curved wall: developed length must be r*theta; (b) the same wall drawn as a chord polyline (15 deg facets): what does the engine measure?"""
    out = {}
    r_axis, t = 3000.0, 200.0
    F.reset()
    frame = wall((0, 0), (8000, 0)) + wall((0, 0), (0, 6000)) + F.cap((0, 0), (8000, 0), 200, "end") + F.cap((0, 0), (0, 6000), 200, "end")
    P = frame + F.curved_wall((3000, 3000), r_axis, t, 0.0, math.pi / 2) + wall((6000, 0), (6000, 3000)) + wall((0, 6000), (3000, 6000))
    ra = run_modules(P)
    cur = [x for x in accepted(ra) if x["CURVATURE_TYPE"] == "ARC"]
    true_len = r_axis * math.pi / 2
    out["TRUE_ARC"] = {"ACCEPTED_CURVED": len(cur), "DEVELOPED_MM": [round(x["DEVELOPED_LENGTH_MM"], 1) for x in cur], "TRUE_MM": round(true_len, 1), "CHORD_MM": round(math.hypot(3000, 3000), 1)}
    ok_a = len(cur) == 1 and abs(cur[0]["DEVELOPED_LENGTH_MM"] - true_len) <= 0.005 * true_len
    # (b) faceted: 6 chords of 15 degrees on each face
    F.reset()
    n = 6
    P = list(frame) + wall((6000, 0), (6000, 3000)) + wall((0, 6000), (3000, 6000))
    for rr in (r_axis - t / 2, r_axis + t / 2):
        for i in range(n):
            a0, a1 = i * math.pi / 2 / n, (i + 1) * math.pi / 2 / n
            P.append(F.seg("W", (3000 + rr * math.cos(a0), 3000 + rr * math.sin(a0)), (3000 + rr * math.cos(a1), 3000 + rr * math.sin(a1))))
    rb = run_modules(P)
    facet = [x for x in rb["rows"] if x["ORIENTATION_TYPE"] not in ("HORIZONTAL", "VERTICAL") and x["THICKNESS_MM"] <= 260]
    acc_f = [x for x in facet if x["MATERIAL_STATUS"] == "ACCEPTED"]
    chord_sum = sum(x["DEVELOPED_LENGTH_MM"] for x in acc_f)
    out["FACETED_POLYLINE"] = {"FACET_BANDS": len(facet), "ACCEPTED": len(acc_f), "STATUSES": sorted({(x["MATERIAL_STATUS"], (x.get("REJECTION_REASON") or "")[:40]) for x in facet}),
                               "SUM_OF_ACCEPTED_CHORDS_MM": round(chord_sum, 1), "TRUE_ARC_MM": round(true_len, 1), "SHORTFALL_REL": round((true_len - chord_sum) / true_len, 4) if chord_sum else None,
                               "NOTE": "the drawn geometry is faceted: the engine measures the drawn chords; the difference to the physical curve is bounded by the facet angle (15 deg: 0.29 %, 30 deg: 1.15 %)"}
    ok_b = (not acc_f) or abs(chord_sum - true_len) <= 0.005 * true_len
    return ok_a and ok_b, out


def q06_narrow_room():
    """A 600, 400 and 300 mm wide labelled duct / corridor: it must exist as a space, or MISSING_SPACE_QA must name the orphan anchor."""
    out, ok = {}, True
    for w in (600.0, 400.0, 300.0, 150.0):
        F.reset()
        P = F.room(0, 0, w, 3000, 200)
        lab = [text("DUCT", w / 2, 1500)]
        r = run_modules(P, lab)
        sp = space_of(r, "DUCT")
        orphan = [q for q in r["qa"] if q["KIND"] in ("ANCHOR_WITHOUT_SPACE", "POSSIBLE_MISSED_SPACE")]
        out[f"W{int(w)}"] = {"SPACE": None if sp is None else (round(sp["AREA_GEOMETRIC_M2"], 3), sp["GEOMETRY_STATUS"], sp["MATERIAL_BOUNDARY_MM"]), "QA": [q["KIND"] for q in orphan],
                             "FACES": [(f["SPACE_ELIGIBILITY"], round(f["AREA_GEOMETRIC_M2"], 3)) for f in r["faces"] if f["AREA_GEOMETRIC_M2"] < 5]}
        ok = ok and (sp is not None or bool(orphan))
    return ok, out


def q07_merged_cell():
    """Partition wholly absent: (a) two labels in one cell -> identity must not be SINGLE; (b) one label -> one physical space, one identity (the drawing shows one space)."""
    F.reset()
    P = F.room(0, 0, 12000, 4000, 200)
    ra = run_modules(P, LABELS2)
    big = [s for s in ra["spaces"] if s["AREA_GEOMETRIC_M2"] > 20]
    ident_a = [s["IDENTITY_STATUS"] for s in big]
    # pipeline-level: identity gate
    r = run_pipeline(to_doc(P, LABELS2))
    S = pipeline_summary(r)
    ok = len(big) == 1 and all(x != "SINGLE" for x in ident_a) and all(("IDENTITY_STATUS" in x["BLOCKED_BY"]) or not x["BRIDGE_ALLOWED"] for x in S["SAFETY"])
    return ok, {"MODULE_IDENTITY": ident_a, "PIPELINE": {"SPACES": S["SPACES"], "SAFETY": S["SAFETY"]}}


def q08_unresolved_band():
    """Three parallel lines as the partition (no fill, no returns): the band is UNRESOLVED; no space beside it may be ESTABLISHED and no line may reach the bridge."""
    F.reset()
    P = F.room(0, 0, 12000, 4000, 200) + [F.seg("W", (5800, 0), (5800, 4000)), F.seg("W", (6000, 0), (6000, 4000)), F.seg("W", (6200, 0), (6200, 4000))]
    r = run_pipeline(to_doc(P, LABELS2))
    S = pipeline_summary(r)
    unres = [x for x in r.registers["PA07_MATERIAL_BAND_REGISTER"]["ROWS"] if x["MATERIAL_STATUS"] == "UNRESOLVED"]
    ok = bool(unres) and all(s["GEOMETRY_STATUS"] != "ESTABLISHED" for s in S["SPACES"] if s["LABELS"]) and not any(x["BRIDGE_ALLOWED"] for x in S["SAFETY"])
    return ok, {"UNRESOLVED_BANDS": [(x["THICKNESS_MM"], (x.get("REJECTION_REASON") or "")[:40]) for x in unres], "SPACES": S["SPACES"], "SAFETY": S["SAFETY"]}


def q09_unresolved_opening():
    """Door gap with jambs but no leaf and no swing (PROBABLE at best): the bridge must stay closed for both rooms; with the leaf it opens and the number is right."""
    r0 = run_pipeline(to_doc(two_rooms(leaf=False), LABELS2))
    S0 = pipeline_summary(r0)
    r1 = run_pipeline(to_doc(two_rooms(leaf=True), LABELS2))
    S1 = pipeline_summary(r1)
    allowed1 = [l for l in S1["LINES"] if not l["BLOCKED_BY"]]
    ok = not any(x["BRIDGE_ALLOWED"] for x in S0["SAFETY"]) and len(allowed1) == 2 and all(abs(l["VECTOR_LM"] * 1000 - EXPECTED_ROOM_FACE) <= 30 for l in allowed1)
    return ok, {"NO_LEAF": {"SITES": S0["SITES"], "SAFETY": S0["SAFETY"]}, "WITH_LEAF": {"SITES": S1["SITES"], "LINES": S1["LINES"], "EXPECTED_MM": EXPECTED_ROOM_FACE}}


def q10_exterior_cell():
    """The region between the drawing frame and the house, and a walled courtyard labelled GARDEN: neither may become an INTERIOR established space with a quantity."""
    F.reset()
    P = two_rooms() + wall((-100, 4200), (-100, 8200)) + wall((12100, 4200), (12100, 8200)) + wall((-100, 8100), (12100, 8100))      # a walled court north of the rooms, its side walls continuing the house walls
    labels = LABELS2 + [text("GARDEN", 6000, 6200)]
    r = run_pipeline(to_doc(P, labels))
    S = pipeline_summary(r)
    garden = [s for s in S["SPACES"] if "GARDEN" in s["LABELS"]]
    frame_region = [s for s in S["SPACES"] if not s["LABELS"] and s["MATERIAL_MM"] > 40000]
    ok = bool(garden) and all(s["CLASS"] != "INTERIOR" for s in garden) and not frame_region and all(not x["BRIDGE_ALLOWED"] for x, s in zip(S["SAFETY"], S["SPACES"]) if "GARDEN" in s["LABELS"])
    return ok, {"SPACES": S["SPACES"], "SAFETY": S["SAFETY"], "FACE_ELIGIBILITY": sorted({(f["SPACE_ELIGIBILITY"]) for f in r.registers["PA07_PLANAR_FACE_REGISTER"]["ROWS"]})}


def q11_beam():
    """A 300 mm beam drawn as two hidden lines across a room (a) with a BEAM_EDGE role, (b) with no role but a HIDDEN linetype, (c) continuous lines and no role (the dangerous case)."""
    out = {}
    for tag, role, lt in (("ROLE_BEAM", "BEAM_EDGE", "CONTINUOUS"), ("HIDDEN_LINETYPE", None, "HIDDEN"), ("BARE_CONTINUOUS", None, "CONTINUOUS")):
        F.reset()
        P = F.room(0, 0, 6000, 4000, 200) + [F.seg("B", (0, 1850), (6000, 1850), linetype=lt, role=role), F.seg("B", (0, 2150), (6000, 2150), linetype=lt, role=role)]
        r = run_modules(P, [text("LIVING", 3000, 800)])
        beam = [x for x in r["rows"] if abs(x["THICKNESS_MM"] - 300) < 1]
        acc = [x for x in beam if x["MATERIAL_STATUS"] == "ACCEPTED"]
        sp = [(round(s["AREA_GEOMETRIC_M2"], 2), s["GEOMETRY_STATUS"], s["MATERIAL_BOUNDARY_MM"]) for s in r["spaces"]]
        out[tag] = {"BEAM_PAIR": [(x["MATERIAL_STATUS"], (x.get("REJECTION_REASON") or "")[:50]) for x in beam], "ACCEPTED": len(acc), "SPACES": sp}
        if tag == "BARE_CONTINUOUS":
            # band level cannot tell a continuous-line beam from a partition; the quantity must still not escape: pipeline level
            rp = run_pipeline(to_doc(P, [text("LIVING", 3000, 800)]))
            S = pipeline_summary(rp)
            out[tag]["PIPELINE"] = {"SPACES": S["SPACES"], "SAFETY": S["SAFETY"]}
            out[tag]["ESCAPED"] = sum(1 for x in S["SAFETY"] if x["BRIDGE_ALLOWED"])
            out[tag]["NOTE"] = "PA07R2: the labelled half is HUMAN_REVIEW because an unlabelled eligible cell lies across an unevidenced band; the band itself stays a known limitation (source convention: beam layer / hidden linetype)"
    ok = out["ROLE_BEAM"]["ACCEPTED"] == 0 and out["HIDDEN_LINETYPE"]["ACCEPTED"] == 0 and out["BARE_CONTINUOUS"]["ESCAPED"] == 0
    return ok, out


def q12_column_double_count():
    """(a) a 400 x 400 crossed column protruding from the north wall: boundary = perimeter - 400 + 3 x 400.  (b) a 200 x 500 wall stub between a cross wall and a door jamb:
    it is a wall piece closed by the jamb, not a column; if it becomes a column its side faces are counted twice (as FACE and as COLUMN_FACE)."""
    F.reset()
    P = F.room(0, 0, 6000, 4000, 200) + F.rect(2800, 3600, 3200, 4000, "C") + [F.seg("C", (2800, 3600), (3200, 4000))]
    ra = run_modules(P, [text("LIVING", 3000, 1500)])
    sa = space_of(ra, "LIVING")
    exp_a = 2 * (6000 + 4000) - 400 + 3 * 400
    out = {"PROTRUDING_COLUMN": {"COLUMNS": len(ra["cols"]), "SPACE": None if sa is None else (sa["GEOMETRY_STATUS"], sa["MATERIAL_BOUNDARY_MM"], sa["COLUMN_FACE_MM"], sa["BOUNDARY_COMPOSITION_MM"]), "EXPECTED_MM": exp_a}}
    ok_a = sa is not None and abs(sa["MATERIAL_BOUNDARY_MM"] - exp_a) <= 30
    # (b) stub
    F.reset()
    P = F.room(0, 0, 12000, 8000, 200) + wall((0, 4000), (12000, 4000)) + wall((6000, 4000), (6000, 4600)) + wall((6000, 5500), (6000, 8000)) + door((6000, 4600), (6000, 5500))
    P += wall((6000, 0), (6000, 1500)) + wall((6000, 2400), (6000, 4000)) + door((6000, 1500), (6000, 2400))
    labels = [text("LIVING", 3000, 2000), text("KITCHEN", 9000, 2000), text("STUDY", 3000, 6000), text("DINING", 9000, 6000)]
    exp_b = 2 * (5900 + 3900) - 900
    try:
        r = run_pipeline(to_doc(P, labels))
        S = pipeline_summary(r)
        study = [s for s in S["SPACES"] if "STUDY" in s["LABELS"]]
        cols = [(c["OBJECT_GEOMETRY"]["SIDES_MM"], c["EXPOSED_TO_SPACE"]["STATUS"]) for c in r.registers["PA07_COLUMN_JUNCTION_REGISTER"]["ROWS"]]
        wrong_established = [s for s in study if s["GEOMETRY_STATUS"] == "ESTABLISHED" and abs(s["MATERIAL_MM"] - exp_b) > 30]
        escaped = [l for l in S["LINES"] if not l["BLOCKED_BY"] and l["VECTOR_LM"] is not None and abs(l["VECTOR_LM"] * 1000 - exp_b) > 30 and abs(l["VECTOR_LM"] * 1000 - 31800) > 30 and l["REGION_STATUS"] == "MEASUREMENT_REGION_CLOSED"]
        out["WALL_STUB_AT_JAMB"] = {"COLUMNS": cols, "STUDY": study, "EXPECTED_MM": exp_b, "WRONG_AND_ESTABLISHED": len(wrong_established), "ESCAPED_TO_A_CLOSED_REGION": len(escaped), "LINES": S["LINES"], "SAFETY": S["SAFETY"]}
        ok_b = not wrong_established and not escaped
    except Exception as e:
        out["WALL_STUB_AT_JAMB"] = {"PIPELINE_CRASH": repr(e)[:300], "TRACE": traceback.format_exc().splitlines()[-3:], "EXPECTED_MM": exp_b,
                                   "NOTE": "the whole run died (loud, but every other space is lost too); the space register before the crash is reported by the module-level run below"}
        rm = run_modules(P, labels)
        st = space_of(rm, "STUDY")
        out["WALL_STUB_AT_JAMB"]["MODULE_LEVEL"] = {"COLUMNS": [(c["OBJECT_GEOMETRY"]["SIDES_MM"]) for c in rm["cols"]], "STUDY": None if st is None else (st["GEOMETRY_STATUS"], st["MATERIAL_BOUNDARY_MM"], st["COLUMN_FACE_MM"], st["BOUNDARY_COMPOSITION_MM"])}
        ok_b = False
    return ok_a and ok_b, out


def q13_storey():
    """(a) one plan view, no owner storey name: STOREY_STATUS must block.  (b) two identical plan copies with two different level marks in ONE view region: stacked storeys suspected -> HUMAN_REVIEW."""
    ra = run_pipeline(to_doc(two_rooms(), LABELS2), storey=False)
    Sa = pipeline_summary(ra)
    P = two_rooms()
    doc = to_doc(P, LABELS2, level="%%p0.00", extra=[{"kind": "TEXT_PLACEHOLDER"}])
    doc["primitives"] = [p for p in doc["primitives"] if p.get("kind") != "TEXT_PLACEHOLDER"]
    doc["texts"].append({"value": "+3.50", "x": 9000, "y": 3500})
    rb = run_pipeline(doc, storey=False)
    Sb = pipeline_summary(rb)
    ok = not any(x["BRIDGE_ALLOWED"] for x in Sa["SAFETY"]) and all("STOREY_STATUS" in x["BLOCKED_BY"] for x in Sa["SAFETY"]) and not any(x["BRIDGE_ALLOWED"] for x in Sb["SAFETY"])
    return ok, {"NO_OWNER_NAME": {"STOREYS": Sa["STOREYS"], "SAFETY": Sa["SAFETY"]}, "TWO_LEVEL_MARKS_ONE_VIEW": {"STOREYS": Sb["STOREYS"], "SAFETY": Sb["SAFETY"], "SPACES": [(s["LABELS"], s["STOREY"]) for s in Sb["SPACES"]]}}


def q14_unknown_height():
    """Height parameter TEMPORARY_OWNER_DEFAULT / UNKNOWN / missing: HEIGHT_STATUS must block; OWNER_PROJECT_INPUT passes."""
    out, ok = {}, True
    for tag, h in (("TEMPORARY_DEFAULT", {"VALUE": 3.0, "SOURCE_TYPE": "TEMPORARY_OWNER_DEFAULT"}), ("UNKNOWN", {"VALUE": None, "SOURCE_TYPE": "UNKNOWN"}), ("AI_GUESS", {"VALUE": 3.0, "SOURCE_TYPE": "AI_INTERPRETED"}), ("OWNER", {"VALUE": 3.0, "SOURCE_TYPE": "OWNER_PROJECT_INPUT"})):
        reg = dict(REG, NORMAL_INTERNAL_PLASTER_HEIGHT=h)
        r = run_pipeline(to_doc(two_rooms(), LABELS2), registry=reg)
        S = pipeline_summary(r)
        allowed = [x for x in S["SAFETY"] if x["BRIDGE_ALLOWED"]]
        out[tag] = {"SAFETY": S["SAFETY"], "LINES": S["LINES"]}
        ok = ok and ((tag == "OWNER") == bool(allowed))
    return ok, out


def q15_provisional_role():
    """A window with jambs and frame lines but no GLAZING role is PROVISIONAL: OPENING_SITE_STATUS must block and no line may carry SOURCE_ESTABLISHED."""
    P = two_rooms()
    # a window in the south wall of LIVING: faces y=0 (inner) and y=-200 (outer) cut at x 1000..2200 with jambs and two frame lines
    P = [p for p in P if not (p.kind == "SEGMENT" and abs(p.y1 - p.y2) < 1e-9 and p.y1 in (0.0, -200.0))]
    P += [F.seg("W", (0, 0), (1000, 0)), F.seg("W", (2200, 0), (12000, 0)), F.seg("W", (-200, -200), (1000, -200)), F.seg("W", (2200, -200), (12200, -200)), F.seg("W", (1000, 0), (1000, -200)), F.seg("W", (2200, 0), (2200, -200)),
          F.seg("WIN", (1000, -60), (2200, -60)), F.seg("WIN", (1000, -140), (2200, -140))]
    r = run_pipeline(to_doc(P, LABELS2))
    S = pipeline_summary(r)
    win = [s for s in S["SITES"] if abs(s[2] - 1200) < 60]
    living_idx = [i for i, s in enumerate(S["SPACES"]) if "LIVING" in s["LABELS"]]
    blocked = [S["SAFETY"][i] for i in living_idx]
    est = [l for l in S["LINES"] if l["QUANTITY_STATUS"] == "SOURCE_ESTABLISHED"]
    ok = bool(win) and all(w[1] != "ESTABLISHED" for w in win) and all(not b["BRIDGE_ALLOWED"] for b in blocked) and not est
    return ok, {"WINDOW_SITES": win, "LIVING_SAFETY": blocked, "LINES": S["LINES"]}


QUESTIONS = [
    ("Q01", "Can a window frame become an eligible wall?", q01_window_frame),
    ("Q02", "Can stair geometry become wall material?", q02_stair),
    ("Q03", "Can a one-face interruption become a door / opening?", q03_single_face_gap),
    ("Q04", "Can a jamb-less gap merge rooms silently?", q04_jambless_gap),
    ("Q05", "Can curved geometry produce a wrong chord-based length?", q05_curved),
    ("Q06", "Can a narrow / unusual room disappear without QA?", q06_narrow_room),
    ("Q07", "Can a merged multi-room cell inherit one label and become valid?", q07_merged_cell),
    ("Q08", "Can an unresolved band be quantity-eligible?", q08_unresolved_band),
    ("Q09", "Can an unresolved opening be quantity-eligible?", q09_unresolved_opening),
    ("Q10", "Can an exterior / site cell become a room?", q10_exterior_cell),
    ("Q11", "Can a beam become wall material?", q11_beam),
    ("Q12", "Can a column be double-counted with its host wall?", q12_column_double_count),
    ("Q13", "Can a storey mistake produce a plaster quantity?", q13_storey),
    ("Q14", "Can an unknown height produce a quantity?", q14_unknown_height),
    ("Q15", "Can a provisional physical role become SOURCE_ESTABLISHED downstream?", q15_provisional_role),
]


def evaluate():
    rows = []
    for qid, q, fn in QUESTIONS:
        try:
            ok, ev = fn()
            rows.append({"ID": qid, "QUESTION": q, "STATUS": "PASS" if ok else "FAIL", "EVIDENCE": ev, "EVIDENCE_KIND": "EXECUTED_COUNTEREXAMPLE"})
        except Exception as e:
            rows.append({"ID": qid, "QUESTION": q, "STATUS": "NOT_TESTED", "EVIDENCE": {"ERROR": repr(e)[:300], "TRACE": traceback.format_exc().splitlines()[-4:]}, "EVIDENCE_KIND": "FIXTURE_FAILED"})
        print(qid, rows[-1]["STATUS"], flush=True)
    counts = {k: sum(1 for r in rows if r["STATUS"] == k) for k in ("PASS", "FAIL", "NOT_TESTED")}
    return {"ARTIFACT": "PA07R1_POST_REVIEW_GATE", "RULE": "PASS only on an executed counterexample that ends loud or correct; a test's existence is never evidence", "QUESTIONS": rows, "COUNTS": counts,
            "VERDICT": "ALL_PASS" if counts["FAIL"] == 0 and counts["NOT_TESTED"] == 0 else "OPEN_FAILURES"}


def _default(o):
    try:
        import numpy as np
        if isinstance(o, (np.floating, np.integer)):
            return float(o)
    except Exception:
        pass
    return str(o)


if __name__ == "__main__":
    from research.qs_wall_treatment_01 import protocol as PR
    tag = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("PA07_OUT_TAG", "pa07r1")
    out = Path(PR.OUT_DIR) / tag
    out.mkdir(parents=True, exist_ok=True)
    g = evaluate()
    (out / "PA07R1_POST_REVIEW_GATE.json").write_text(json.dumps(g, indent=1, ensure_ascii=False, default=_default), "utf-8")
    print(json.dumps(g["COUNTS"]), g["VERDICT"], "->", out / "PA07R1_POST_REVIEW_GATE.json")
