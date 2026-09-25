"""PA07R1 fail-safes after the cold review (FM-P7-01..18): each test reproduces a counterexample that PA07 accepted
silently and asserts that PA07R1 fails loudly, plus the end-to-end pipeline7 run on a synthetic villa showing that a
clean room reaches the engines and an unresolved room never does."""

from __future__ import annotations

import json
import math

from engine.ingest import band_topology as BT, material_bands as MB, pipeline7 as P7, planar_faces as PF
from tests import pa07_fixtures as F
from tests.test_pa07_spaces import run as run_spaces
from tests.test_pa06_pipeline import REG, cfg


def frame():
    return F.wall((0, 0), (8000, 0), 200) + F.wall((0, 0), (0, 6000), 200) + F.cap((0, 0), (8000, 0), 200, "end") + F.cap((0, 0), (0, 6000), 200, "end")


def villa_with_frame(tmp_path, **kw):
    """The PA06 synthetic villa inside a drawing frame, so that no wall is the outermost line of the view."""
    from tests.test_pa06_pipeline import villa
    p = villa(tmp_path, **kw)
    doc = json.loads(p.read_text("utf-8"))
    for a, b in (((-3000, -3000), (15000, -3000)), ((15000, -3000), (15000, 7000)), ((15000, 7000), (-3000, 7000)), ((-3000, 7000), (-3000, -3000))):
        doc["primitives"].append({"kind": "SEGMENT", "layer": "FRAME", "x1": a[0], "y1": a[1], "x2": b[0], "y2": b[1]})
    doc["linetypes"]["FRAME"] = "CONTINUOUS"
    p.write_text(json.dumps(doc), "utf-8")
    return p


def test_fm01_wardrobe_outline_between_walls_is_not_a_wall():
    # a 2000 x 600 closed outline drawn wall-to-wall in a room corner: a wardrobe, not a wall
    prims = F.room(0, 0, 6000, 4000, 200) + F.rect(0, 0, 2000, 600, "J")
    rows, bands = MB.build("VW-t", prims, F.roles_of(prims), view_bbox=(-2000, -2000, 9000, 7000))
    ward = [r for r in rows if r["THICKNESS_MM"] == 600 and abs(r["DEVELOPED_LENGTH_MM"] - 2000) <= 10]
    assert ward and all(r["MATERIAL_STATUS"] != "ACCEPTED" for r in ward), [(r["MATERIAL_STATUS"], r["REJECTION_REASON"]) for r in ward]
    r = run_spaces(prims)
    assert len(r["spaces"]) == 1 and abs(r["spaces"][0]["MATERIAL_BOUNDARY_MM"] - 20000) <= 60, "the room boundary is the wall, not the wardrobe"


def test_fm02_bare_rectangle_is_not_a_column_but_a_crossed_one_is():
    bare = F.room(0, 0, 6000, 4000, 200) + F.rect(2000, 1500, 2400, 1900, "X")
    r = run_spaces(bare)
    assert not r["cols"] and len(r["spaces"]) == 1
    crossed = bare + [F.seg("X", (2000, 1500), (2400, 1900))]
    r = run_spaces(crossed)
    # PA07R2 (FM-R1-06): the cross makes it a COLUMN_CANDIDATE (column or symbol), never an accepted column on its own
    assert not r["cols"] and any((x["REJECTION_REASON"] or "").startswith("COLUMN_CANDIDATE") for x in r["rows"])


def test_fm03_unresolved_wall_still_separates_rooms_provisionally():
    # two rooms separated by three parallel lines (no fill, no returns): the partition is UNRESOLVED; the rooms must not merge into one ESTABLISHED space
    prims = F.room(0, 0, 8000, 4000, 200) + [F.seg("W", (4000, 0), (4000, 4000)), F.seg("W", (4200, 0), (4200, 4000)), F.seg("W", (4400, 0), (4400, 4000))]
    r = run_spaces(prims, texts=[{"TEXT": "BED", "X": 2000, "Y": 2000, "ROLE": "ROOM_NAME"}])
    assert len(r["spaces"]) >= 2, [(f["SPACE_ELIGIBILITY"], f["AREA_GEOMETRIC_M2"]) for f in r["faces"]]
    assert all(s["GEOMETRY_STATUS"] == "BOUNDARY_PROVISIONAL" for s in r["spaces"] if s["AREA_GEOMETRIC_M2"] > 5)
    # a thin (70 mm) partition too
    prims = F.room(0, 0, 8000, 4000, 200) + F.wall((4000, 0), (4000, 4000), 70)
    r = run_spaces(prims)
    assert len(r["spaces"]) >= 2 and all(s["GEOMETRY_STATUS"] == "BOUNDARY_PROVISIONAL" for s in r["spaces"])


def test_fm05_one_return_is_not_fill_evidence():
    # a wall and a void strip beside it that carries one perpendicular stub: the wall must not lose
    prims = frame() + F.wall((0, 3000), (5000, 3000), 200) + [F.seg("V", (0, 3250), (5000, 3250)), F.seg("V", (5000, 3100), (5000, 3250))]
    rows, bands = MB.build("VW-t", prims, F.roles_of(prims))
    void = [r for r in rows if r["THICKNESS_MM"] == 150]
    wall = [r for r in rows if r["THICKNESS_MM"] == 200 and r["ORIENTATION_TYPE"] == "HORIZONTAL" and r["DEVELOPED_LENGTH_MM"] == 5000]
    assert void and all(r["MATERIAL_STATUS"] != "ACCEPTED" for r in void)
    assert wall and wall[0]["MATERIAL_STATUS"] != "REJECTED" and not (wall[0]["REJECTION_REASON"] or "").startswith("VOID_BESIDE")


def test_fm04_open_passage_needs_two_distinct_faces():
    sites = [{"SITE_ID": "S1", "CLASS": "UNRESOLVED", "STATUS": "OPEN_PASSAGE_CANDIDATE", "REASON": "x"}]
    BT.promote_open_passages(sites, lambda s: ("NOT_INTERIOR", "NOT_INTERIOR"))
    assert sites[0]["CLASS"] == "UNRESOLVED"


def test_fm09_ai_label_never_establishes_identity(tmp_path):
    c = cfg(villa_with_frame(tmp_path, labels=("XX1", "XX2")), AI_LABELS=[{"TEXT": "LIVING", "X": 3000, "Y": 2200, "MODEL": "test"}], TRADES=["NORMAL_INTERNAL_PLASTER"], RULE_VERSION="T")
    r = P7.run(c)
    sp = [s for s in r.registers["PA07_PHYSICAL_SPACE_REGISTER"]["ROWS"] if any(a["TEXT"] == "LIVING" for a in s["ANCHORS"])]
    assert sp and sp[0]["SEMANTIC_IDENTITY"]["STATUS"] == "AI_INTERPRETED"
    assert all(r["GATES"]["IDENTITY_STATUS"]["STATUS"] != "PASS" for r in r.registers["PA07_QUANTITY_SAFETY_REGISTER"]["ROWS"] if r["SPACE_ID"] == sp[0]["SPACE_ID"])


def test_pipeline7_end_to_end_formed_region_and_blocked_unresolved(tmp_path):
    """A clean two-room villa: the labelled rooms pass every gate, the region forms with reversible closures and a number exists.
    The same villa with the door leaf and jambs removed: the gap is UNRESOLVED, no line reaches the engines."""
    c = cfg(villa_with_frame(tmp_path), OWNER_STOREY_NAMES={}, TRADES=["NORMAL_INTERNAL_PLASTER"], RULE_VERSION="T")
    r = P7.run(c)
    R = r.registers
    safety = R["PA07_QUANTITY_SAFETY_REGISTER"]
    allowed = [x for x in safety["ROWS"] if x["BRIDGE_ALLOWED"]]
    blocked = {g for x in safety["ROWS"] for g in x["BLOCKED_BY"]}
    # storey names are not established on a single unlabelled view: STOREY_STATUS blocks; every other gate passes for the two labelled rooms
    two = [x for x in safety["ROWS"] if set(x["BLOCKED_BY"]) <= {"STOREY_STATUS"}]
    assert len(two) == 2, [(x["BLOCKED_BY"]) for x in safety["ROWS"]]
    # with the storey told by the owner the bridge runs: force the storey through the register the same way the pipeline reads it
    r.storey_of_view = {k: "GROUND_FLOOR" for k in r.storey_of_view}
    for sp in R["PA07_PHYSICAL_SPACE_REGISTER"]["ROWS"]:
        sp["STOREY"] = "GROUND_FLOOR"
    r.stage_build_quantity_safety()
    safety = r.registers["PA07_QUANTITY_SAFETY_REGISTER"]; trace = r.registers["PA07_QUANTITY_INPUT_TRACE"]["LINES"]; tmr = r.registers["PA07_TRADE_MEASUREMENT_REGION_REGISTER"]
    allowed = [x for x in safety["ROWS"] if x["BRIDGE_ALLOWED"]]
    assert len(allowed) == 2 and tmr["COUNT"] == 2
    assert all(reg["MEASUREMENT_REGION_STATUS"] == "MEASUREMENT_REGION_CLOSED" for reg in tmr["ROWS"]), [reg.get("NOT_ESTABLISHED_BECAUSE") for reg in tmr["ROWS"]]
    assert tmr["REVERSIBILITY"]["ALL_REVERSIBLE"] is True and tmr["REVERSIBILITY"]["ALL_ZERO_MATERIAL"] is True
    lines = [l for l in trace if not l["BLOCKED_BY"]]
    assert lines and all(l["LENGTH_GEOMETRY"]["VECTOR_LM"] is not None and l["BARE_NUMBER"] is False for l in lines)
    lm = sorted(l["LENGTH_GEOMETRY"]["VECTOR_LM"] for l in lines)
    assert abs(lm[0] - (2 * (5.8 + 3.8) - 0.9)) <= 0.03 and abs(lm[1] - (2 * (5.8 + 3.8) - 0.9)) <= 0.03, lm     # each room: clear 5.8 x 3.8 minus the 0.9 door
    # unresolved: no leaf, no jambs -> the gap is UNRESOLVED and both rooms are BOUNDARY_PROVISIONAL: nothing reaches the engines
    p = villa_with_frame(tmp_path, with_leaf=False)
    doc = json.loads(p.read_text("utf-8")); doc["primitives"] = [q for q in doc["primitives"] if not (q["kind"] == "SEGMENT" and q.get("y1") == q.get("y2") and q["y1"] in (1500.0, 2400.0) and abs(q["x2"] - q["x1"]) == 200.0)]
    p.write_text(json.dumps(doc), "utf-8")
    r3 = P7.run(cfg(p, TRADES=["NORMAL_INTERNAL_PLASTER"], RULE_VERSION="T"))
    r3.storey_of_view = {k: "GROUND_FLOOR" for k in r3.storey_of_view}
    for sp in r3.registers["PA07_PHYSICAL_SPACE_REGISTER"]["ROWS"]:
        sp["STOREY"] = "GROUND_FLOOR"
    r3.stage_build_quantity_safety()
    s3 = r3.registers["PA07_QUANTITY_SAFETY_REGISTER"]
    assert s3["BRIDGE_ALLOWED"] == 0 and r3.registers["PA07_TRADE_MEASUREMENT_REGION_REGISTER"]["COUNT"] == 0
    assert all(set(x["BLOCKED_BY"]) & {"SPACE_STATUS", "OPENING_SITE_STATUS"} for x in s3["ROWS"]), [x["BLOCKED_BY"] for x in s3["ROWS"]]
