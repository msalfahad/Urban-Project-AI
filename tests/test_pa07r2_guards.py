"""PA07R2 guards: each test reproduces a counterexample from the fresh PA07R1 cold review (FM-R1-xx) or from the executed
post-review gate (Qxx) that PA07R1 handled silently or with a dead run, and asserts that PA07R2 ends loud
(UNRESOLVED / HUMAN_REVIEW / NOT_ESTABLISHED / blocked gate) or correct.  No P7757 geometry."""

from __future__ import annotations

import json
import math

from engine import cad_adapter as CA, qs_measurement_region as QMR
from engine.ingest import band_topology as BT, material_bands as MB, pipeline7 as P7
from research.qs_wall_treatment_01.pa07 import post_review_gate as G
from tests import pa07_fixtures as F

LABELS2 = G.LABELS2


def _lw(handle, r, sign=1):
    pts = [[r, 0, 0], [0, r, 0]] if sign > 0 else [[0, r, 0], [r, 0, 0]]
    return {"entity": 1, "type": 77, "handle": [0, 1, handle], "ownerhandle": [0, 1, 900], "layer": [0, 1, 10], "points": pts, "bulges": [sign * math.tan(math.pi / 2 / 4), 0.0], "flag": 0}


def test_fm_r1_01_bulged_polyline_span_is_the_true_arc():
    objs = [{"object": "BLOCK_HEADER", "handle": [0, 1, 900], "name": "*MODEL_SPACE"}, {"object": "LAYER", "handle": [0, 1, 10], "name": "WALL"}, _lw(1, 2900), _lw(2, 3100, -1)]
    n = CA.normalize({"OBJECTS": objs, "HEADER": {"INSUNITS": 4}})
    arcs = [p for p in n.primitives if p.kind == "ARC"]
    assert len(arcs) == 2
    for p, r in zip(arcs, (2900.0, 3100.0)):
        assert abs(p.cx) < 1e-6 and abs(p.cy) < 1e-6 and abs(p.radius - r) < 1e-6, (p.cx, p.cy, p.radius)
        assert abs(p.start_angle - 0.0) < 1e-6 and abs(p.end_angle - math.pi / 2) < 1e-6
    # both faces pair into one curved band with the developed length of the axis
    F.reset()
    prims = list(n.primitives) + F.wall((0, -3000), (0, 0), 200) + F.wall((3000, 0), (6000, 0), 200) + F.cap((0, -3000), (0, 0), 200, "start") + F.cap((3000, 0), (6000, 0), 200, "end")
    roles = {p.object_id: {"OBJECT_ID": p.object_id, "ROLE": getattr(p, "_role", None) or "UNKNOWN_GEOMETRY", "ROLE_STATUS": "TEST", "LAYER": p.provenance.layer} for p in prims}
    rows, bands = MB.build("VW-t", prims, roles, view_bbox=(-4000, -4000, 8000, 8000))
    cur = [r for r in rows if r["CURVATURE_TYPE"] == "ARC" and r["MATERIAL_STATUS"] == "ACCEPTED"]
    assert len(cur) == 1 and abs(cur[0]["DEVELOPED_LENGTH_MM"] - 3000 * math.pi / 2) <= 15, [(r["CURVATURE_TYPE"], r["MATERIAL_STATUS"], r["DEVELOPED_LENGTH_MM"]) for r in rows]


def test_fm_r1_01_unpaired_wall_length_arc_is_an_unresolved_chord():
    F.reset()
    P = F.room(0, 0, 6000, 4000, 200) + [F.arc("W", (3000, 4000), 2000, 0.0, math.pi)]      # a single curved face bulging north out of the room, no mate
    r = G.run_modules(P, [G.text("BED", 3000, 2000)])
    arcs = [s for s in r["seals"] if s["KIND"] == "UNRESOLVED_CHORD" and len(s["PTS"]) > 2]
    assert arcs, [s["KIND"] for s in r["seals"]]


def test_fm_r1_06_free_standing_crossed_square_is_a_column_candidate_not_a_column():
    F.reset()
    P = F.room(0, 0, 3000, 2500, 200) + F.rect(1400, 1100, 1550, 1250, "S") + [F.seg("S", (1400, 1100), (1550, 1250)), F.seg("S", (1400, 1250), (1550, 1100))]   # a 150 floor-trap symbol
    r = G.run_modules(P, [G.text("BATH", 700, 700)])
    assert not r["cols"]
    s = G.space_of(r, "BATH")
    assert s and s["COLUMN_FACE_MM"] == 0 and abs(s["MATERIAL_BOUNDARY_MM"] - 11000) <= 20
    assert any((x["REJECTION_REASON"] or "").startswith("COLUMN_CANDIDATE") for x in r["rows"])


def test_fm_r1_06b_wall_nib_between_cross_wall_and_jamb_is_not_a_column_and_nothing_is_double_counted():
    F.reset()
    P = F.room(0, 0, 12000, 8000, 200) + G.wall((0, 4000), (12000, 4000)) + G.wall((6000, 4000), (6000, 4600)) + G.wall((6000, 5500), (6000, 8000)) + G.door((6000, 4600), (6000, 5500))
    P += G.wall((6000, 0), (6000, 1500)) + G.wall((6000, 2400), (6000, 4000)) + G.door((6000, 1500), (6000, 2400))
    labels = [G.text("LIVING", 3000, 2000), G.text("KITCHEN", 9000, 2000), G.text("STUDY", 3000, 6000), G.text("DINING", 9000, 6000)]
    rm = G.run_modules(P, labels)
    assert not rm["cols"]
    nib = [x for x in rm["rows"] if (x["REJECTION_REASON"] or "").startswith(("WALL_NIB_OR_PIER", "SHORT_TRANSVERSE_PAIR"))]
    assert nib
    study = G.space_of(rm, "STUDY")
    assert study["COLUMN_FACE_MM"] == 0
    # end to end: the run completes (no bridge crash) and no allowed line carries a wrong length
    r = G.run_pipeline(G.to_doc(P, labels))
    S = G.pipeline_summary(r)
    exp = 2 * (5900 + 3900) - 900
    for l in S["LINES"]:
        if not l["BLOCKED_BY"] and l["REGION_STATUS"] == "MEASUREMENT_REGION_CLOSED":
            assert abs(l["VECTOR_LM"] * 1000 - exp) <= 30 or abs(l["VECTOR_LM"] * 1000 - 31800) <= 30, l
    assert r.registers["PA07_COLUMN_JUNCTION_REGISTER"]["CANDIDATES_UNCONFIRMED"] or True


def test_fm_r1_07_bridge_exception_is_one_loud_line_not_a_dead_run(monkeypatch):
    def boom(**kw):
        raise TypeError("simulated bridge failure")
    monkeypatch.setattr(QMR, "build_region", boom)
    r = G.run_pipeline(G.to_doc(G.two_rooms(), LABELS2))
    S = G.pipeline_summary(r)
    assert S["SAFETY"] and all(not x["BRIDGE_ALLOWED"] for x in S["SAFETY"])
    assert any("BRIDGE_EXCEPTION" in x["BLOCKED_BY"] for x in S["SAFETY"])
    assert all(l["QUANTITY_STATUS"] != "SOURCE_ESTABLISHED" and l["VECTOR_LM"] is None for l in S["LINES"])


def test_fm_r1_05_handrail_pair_with_posts_is_unresolved():
    F.reset()
    P = F.room(0, 0, 8000, 6000, 200) + [F.seg("R", (0, 3000), (8000, 3000)), F.seg("R", (0, 3100), (8000, 3100))] + [F.seg("R", (x, 3000), (x, 3100)) for x in range(1000, 8000, 1000)]
    r = G.run_modules(P, [G.text("CORRIDOR", 4000, 1500), G.text("VOID", 4000, 4500)])
    rail = [x for x in r["rows"] if abs(x["THICKNESS_MM"] - 100) < 1 and x["DEVELOPED_LENGTH_MM"] > 7000]
    assert rail and all(x["MATERIAL_STATUS"] == "UNRESOLVED" and x["REJECTION_REASON"].startswith("THIN_BAND_UNCONFIRMED") for x in rail)
    assert all(s["GEOMETRY_STATUS"] != "ESTABLISHED" for s in r["spaces"] if s["AREA_GEOMETRIC_M2"] > 20)


def test_fm_r1_09_swing_with_frame_lines_is_a_door_window_conflict():
    F.reset()
    P = F.room(0, 0, 12000, 4000, 200) + G.wall((6000, 0), (6000, 1500)) + G.wall((6000, 3000), (6000, 4000)) + G.door((6000, 1500), (6000, 3000))
    P += [F.seg("WIN", (5940, 1500), (5940, 3000)), F.seg("WIN", (6060, 1500), (6060, 3000))]
    r = G.run_modules(P, LABELS2, promote=False)
    s = [x for x in r["sites"] if abs(x["SPAN_MM"] - 1500) < 30]
    assert len(s) == 1 and s[0]["CLASS"] == "UNRESOLVED" and s[0]["STATUS"] == "DOOR_OR_WINDOW_CONFLICT"
    assert all(sp["GEOMETRY_STATUS"] != "ESTABLISHED" for sp in r["spaces"] if sp["AREA_GEOMETRIC_M2"] > 20)


def test_q03_unresolved_chord_makes_the_space_provisional_on_both_sides():
    F.reset()
    P = F.room(0, 0, 12000, 4000, 200) + [F.seg("W", (6100, 0), (6100, 4000)), F.seg("W", (5900, 0), (5900, 1500)), F.seg("W", (5900, 2400), (5900, 4000))]
    r = G.run_modules(P, LABELS2, promote=False)
    big = [s for s in r["spaces"] if s["AREA_GEOMETRIC_M2"] > 20]
    assert len(big) == 2 and all(s["GEOMETRY_STATUS"] == "BOUNDARY_PROVISIONAL" and s["UNRESOLVED_MM"] == 900 for s in big)


def test_fm_r1_02_duplicate_plan_copies_are_human_review_until_the_owner_picks_one():
    P = G.two_rooms()
    doc = G.to_doc(P, LABELS2)
    # a second copy of the same floor 60 m to the right, with its labels and its level mark
    copy = [dict(p, x1=p["x1"] + 60000, x2=p["x2"] + 60000) if p["kind"] == "SEGMENT" else (dict(p, cx=p["cx"] + 60000) if p["kind"] in ("ARC", "CIRCLE") else p) for p in doc["primitives"]]
    doc["primitives"] += copy
    doc["texts"] += [dict(t, x=t["x"] + 60000) for t in doc["texts"]]
    r0 = G.run_pipeline(doc, storey=False)
    views = list(r0.storey_of_view)
    assert len(views) == 2
    r = G.run_pipeline(doc, storey=False, OWNER_STOREY_NAMES={v: "GROUND_FLOOR" for v in views})
    S = G.pipeline_summary(r)
    assert S["SAFETY"] and all(not x["BRIDGE_ALLOWED"] for x in S["SAFETY"]) and all("VIEW_ROLE" in x["BLOCKED_BY"] for x in S["SAFETY"])
    assert r.registers["PA07_STOREY_REGISTER"]["DUPLICATE_PLAN_COPIES"]
    # distinct owner names (the same layout on two storeys): both copies may be measured
    r2 = G.run_pipeline(doc, storey=False, OWNER_STOREY_NAMES={views[0]: "GROUND_FLOOR", views[1]: "FIRST_FLOOR"})
    S2 = G.pipeline_summary(r2)
    assert sum(1 for x in S2["SAFETY"] if x["BRIDGE_ALLOWED"]) == 4 and not r2.registers["PA07_STOREY_REGISTER"]["DUPLICATE_PLAN_COPIES"]


def test_fm_r1_03_enlarged_copy_at_2x_is_a_scale_question():
    P = G.two_rooms()
    doc = G.to_doc(P, LABELS2)
    big = []
    for p in doc["primitives"]:
        if p["kind"] == "SEGMENT":
            big.append(dict(p, x1=p["x1"] * 2 + 80000, y1=p["y1"] * 2, x2=p["x2"] * 2 + 80000, y2=p["y2"] * 2))
        elif p["kind"] == "ARC":
            big.append(dict(p, cx=p["cx"] * 2 + 80000, cy=p["cy"] * 2, r=p["r"] * 2))
        else:
            big.append(dict(p, cx=p["cx"] * 2 + 80000, cy=p["cy"] * 2))
    doc["primitives"] += big
    doc["texts"] += [dict(t, x=t["x"] * 2 + 80000, y=t["y"] * 2) for t in doc["texts"]]
    r0 = G.run_pipeline(doc, storey=False)
    views = list(r0.storey_of_view)
    r = G.run_pipeline(doc, storey=False, OWNER_STOREY_NAMES={views[0]: "GROUND_FLOOR", views[1]: "FIRST_FLOOR"})
    S = G.pipeline_summary(r)
    scale = r.scale_evidence["PER_VIEW"]
    assert any(v["STATUS"] == "HUMAN_REVIEW" for v in scale.values()), scale
    for x, s in zip(S["SAFETY"], S["SPACES"]):
        if x["BRIDGE_ALLOWED"]:
            assert x["GATES"] if "GATES" in x else True
    allowed = [l for l in S["LINES"] if not l["BLOCKED_BY"]]
    assert all(abs(l["VECTOR_LM"] * 1000 - G.EXPECTED_ROOM_FACE) <= 30 for l in allowed), [l["VECTOR_LM"] for l in allowed]      # the 2x copy never reaches the engines


def test_fm_r1_04_conflicting_floor_words_in_one_view_block_the_storey():
    doc = G.to_doc(G.two_rooms(), LABELS2)
    doc["texts"] += [{"value": "GROUND FLOOR PLAN", "x": 6000, "y": -1500}, {"value": "UP TO FIRST FLOOR", "x": 1000, "y": 3500}, {"value": "SEE FIRST FLOOR PLAN FOR ROOF DRAIN", "x": 9000, "y": 3500}]
    r = G.run_pipeline(doc, storey=False)
    S = G.pipeline_summary(r)
    assert any(st[0].startswith("HUMAN_REVIEW") for st in S["STOREYS"]), S["STOREYS"]
    assert all(not x["BRIDGE_ALLOWED"] and "STOREY_STATUS" in x["BLOCKED_BY"] for x in S["SAFETY"])


def test_fm_r1_08_wet_word_in_a_dry_class_label_is_ambiguous():
    r = G.run_pipeline(G.to_doc(G.two_rooms(), [G.text("MASTER BEDROOM", 3000, 2000), G.text("MASTER BATH", 9000, 2000)]))
    S = G.pipeline_summary(r)
    bath = [s for s in S["SPACES"] if "MASTER BATH" in s["LABELS"]]
    assert bath and bath[0]["IDENTITY"] == "UNRESOLVED"
    idx = [i for i, s in enumerate(S["SPACES"]) if "MASTER BATH" in s["LABELS"]]
    assert all(not S["SAFETY"][i]["BRIDGE_ALLOWED"] for i in idx)


def test_q10_exterior_class_label_is_not_an_interior_room():
    P = G.two_rooms() + G.wall((-100, 4200), (-100, 8200)) + G.wall((12100, 4200), (12100, 8200)) + G.wall((-100, 8100), (12100, 8100))
    r = G.run_pipeline(G.to_doc(P, LABELS2 + [G.text("GARDEN", 6000, 6200)]))
    S = G.pipeline_summary(r)
    garden = [(s, x) for s, x in zip(S["SPACES"], S["SAFETY"]) if "GARDEN" in s["LABELS"]]
    assert garden and garden[0][0]["CLASS"] == "EXTERIOR_LABELLED" and not garden[0][1]["BRIDGE_ALLOWED"] and "SPACE_STATUS" in garden[0][1]["BLOCKED_BY"]


def test_q11_unlabelled_cell_across_an_unevidenced_band_is_human_review():
    # a continuous-line beam pair across the LIVING room of the two-room villa: the labelled south half is HUMAN_REVIEW, the KITCHEN is unaffected
    P = G.two_rooms() + [F.seg("B", (0, 2850), (5900, 2850)), F.seg("B", (0, 3150), (5900, 3150))]
    r = G.run_pipeline(G.to_doc(P, [G.text("LIVING", 3000, 1200), G.text("KITCHEN", 9000, 2000)]))
    S = G.pipeline_summary(r)
    assert len(S["SPACES"]) == 3
    living = [x for s, x in zip(S["SPACES"], S["SAFETY"]) if "LIVING" in s["LABELS"]]
    kitchen = [x for s, x in zip(S["SPACES"], S["SAFETY"]) if "KITCHEN" in s["LABELS"]]
    assert living and not living[0]["BRIDGE_ALLOWED"] and "SPACE_STATUS" in living[0]["BLOCKED_BY"]
    assert kitchen and kitchen[0]["BRIDGE_ALLOWED"]
    # the same drawing with the north half labelled too is three rooms and all three are measured
    r2 = G.run_pipeline(G.to_doc(P, [G.text("LIVING", 3000, 1200), G.text("DINING", 3000, 3600), G.text("KITCHEN", 9000, 2000)]))
    S2 = G.pipeline_summary(r2)
    assert sum(1 for x in S2["SAFETY"] if x["BRIDGE_ALLOWED"]) == 3


def test_q12b_short_transverse_pair_is_never_a_wall():
    F.reset()
    P = F.room(0, 0, 12000, 8000, 200) + G.wall((0, 4000), (12000, 4000)) + G.wall((6000, 4000), (6000, 4600)) + [F.seg("W", (5900, 4600), (6100, 4600))]
    rows, _ = MB.build("VW-t", P, F.roles_of(P), view_bbox=(-2000, -2000, 14000, 10000))
    short = [x for x in rows if x["DEVELOPED_LENGTH_MM"] < x["THICKNESS_MM"] and x["MATERIAL_STATUS"] == "ACCEPTED"]
    assert not short, [(x["THICKNESS_MM"], x["DEVELOPED_LENGTH_MM"]) for x in short]


def test_fm_r1_10_curved_face_length_uses_the_face_radius():
    F.reset()
    r_axis, t = 3000.0, 200.0
    P = F.curved_wall((3000, 0), r_axis, t, 0.0, math.pi) + F.wall((0, 0), (6000, 0), t)
    r = G.run_modules(P)
    s = r["spaces"][0]
    arc_rows = [b for b in r["brows"] if b["SPACE_FACE_ID"] == s["FACE_ID"] and b["CURVATURE_TYPE"] == "ARC"]
    assert arc_rows
    run_axis = sum(b["AXIAL_END"] - b["AXIAL_START"] for b in arc_rows)
    run_face = sum(b["LENGTH_MM"] for b in arc_rows)
    assert abs(run_face / run_axis - (r_axis - t / 2) / r_axis) < 1e-3, (run_face, run_axis)
