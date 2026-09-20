"""PA07D / PA07E tests: planar faces without a seed grid, physical spaces, boundary lengths from band geometry,
MISSING_SPACE_QA, and column / beam junctions."""

from __future__ import annotations

import math

from engine.ingest import band_topology as BT, junctions as JN, material_bands as MB, planar_faces as PF
from tests import pa07_fixtures as F

BOX = (-2000, -2000, 12000, 9000)


def run(prims, texts=(), box=BOX):
    roles = F.roles_of(prims)
    rows, bands = MB.build("VW-t", prims, roles, view_bbox=box)
    intervals, sites, seals = BT.build_view("VW-t", prims, roles, bands)
    seals = seals + PF.glazing_separators(prims, roles)
    faces, grids = PF.build("VW-t", box, seals, bands, texts)
    brows = PF.boundary_faces("VW-t", faces, grids, bands, intervals, seals)
    spaces = PF.space_register("VW-t", faces, brows)
    qa = PF.missing_space_qa(faces, spaces, texts)
    cols, beams, ext = JN.build("VW-t", bands, brows, prims, roles)
    return dict(rows=rows, bands=bands, intervals=intervals, sites=sites, seals=seals, faces=faces, grids=grids, brows=brows, spaces=spaces, qa=qa, cols=cols, beams=beams)


def eligible(r):
    return [f for f in r["faces"] if f["SPACE_ELIGIBILITY"] == "ELIGIBLE"]


def test_narrow_rooms_0_60_and_0_40_m_exist():
    for w in (600.0, 400.0):
        prims = F.room(0, 0, w, 3000, 200)
        r = run(prims)
        sp = r["spaces"]
        assert len(sp) == 1, [(f["SPACE_ELIGIBILITY"], f["AREA_GEOMETRIC_M2"]) for f in r["faces"]]
        assert abs(sp[0]["AREA_GEOMETRIC_M2"] - w * 3000 / 1e6) <= 0.05
        assert abs(sp[0]["MATERIAL_BOUNDARY_MM"] - 2 * (w + 3000)) <= 20


def test_triangular_rotated_l_shaped_concave_rooms():
    # triangular: three walls
    t = 200.0
    pts = [(0, 0), (6000, 0), (0, 4500)]
    prims = []
    for a, b in zip(pts, pts[1:] + pts[:1]):
        prims += F.wall(a, b, t)
    r = run(prims)
    assert len(r["spaces"]) == 1 and 10 < r["spaces"][0]["AREA_GEOMETRIC_M2"] < 13.5
    # rotated rectangle 5 x 3 at 30 degrees
    ang = math.radians(30); c, s = math.cos(ang), math.sin(ang)
    corners = [(0, 0), (5000, 0), (5000, 3000), (0, 3000)]
    rot = [(x * c - y * s + 2000, x * s + y * c + 1000) for x, y in corners]
    prims = []
    for a, b in zip(rot, rot[1:] + rot[:1]):
        prims += F.wall(a, b, t)
    r = run(prims)
    assert len(r["spaces"]) == 1 and abs(r["spaces"][0]["AREA_GEOMETRIC_M2"] - 15.0) < 1.6
    # L-shaped: outer 6 x 5 with a 3 x 2 notch
    L = [(0, 0), (6000, 0), (6000, 3000), (3000, 3000), (3000, 5000), (0, 5000)]
    prims = []
    for a, b in zip(L, L[1:] + L[:1]):
        prims += F.wall(a, b, t)
    r = run(prims)
    assert len(r["spaces"]) == 1 and abs(r["spaces"][0]["AREA_GEOMETRIC_M2"] - 24.0) < 3.0


def test_curved_room_boundary_is_developed_length():
    r_axis, t = 3000.0, 200.0
    prims = F.curved_wall((3000, 0), r_axis, t, 0.0, math.pi) + F.wall((0, 0), (6000, 0), t)
    r = run(prims)
    assert len(r["spaces"]) == 1
    s = r["spaces"][0]
    inner_arc = (r_axis - t / 2) * math.pi
    assert abs(s["MATERIAL_BOUNDARY_MM"] - (inner_arc + 6000 - 200)) <= 0.01 * inner_arc + 60
    assert any(b["CURVATURE_TYPE"] == "ARC" for b in r["brows"] if b["SPACE_FACE_ID"] == s["FACE_ID"])


def test_region_touching_border_and_courtyard_and_shaft():
    # a room whose wall is missing on one side leaks to the view border: not a space, label raises ANCHOR_WITHOUT_SPACE
    prims = F.wall((0, 0), (6000, 0), 200) + F.wall((0, 0), (0, 4000), 200) + F.wall((6000, 0), (6000, 4000), 200)
    r = run(prims, texts=[{"TEXT": "MAJLIS", "X": 3000, "Y": 2000, "ROLE": "ROOM_NAME"}])
    assert not r["spaces"]
    assert {i["KIND"] for i in r["qa"]} >= {"ANCHOR_WITHOUT_SPACE", "POSSIBLE_MISSED_SPACE"}
    # courtyard: an outer room 10 x 8 with an inner enclosed court 3 x 3 (two nested rooms); both are planar faces, both eligible physically
    prims = F.room(0, 0, 10000, 8000, 200) + F.room(3500, 2500, 6500, 5500, 200)
    r = run(prims)
    areas = sorted(s["AREA_GEOMETRIC_M2"] for s in r["spaces"])
    assert len(areas) == 2 and abs(areas[0] - 9.0) < 0.3 and 65 < areas[1] < 80
    # shaft: 0.8 x 0.8 enclosed inside a room, no label: SPACE_WITHOUT_IDENTITY, still a physical space
    prims = F.room(0, 0, 6000, 4000, 200) + F.room(1000, 1000, 1800, 1800, 100)
    r = run(prims, texts=[{"TEXT": "BED", "X": 4000, "Y": 2000, "ROLE": "ROOM_NAME"}])
    assert len(r["spaces"]) == 2
    kinds = [i["KIND"] for i in r["qa"]]
    assert kinds.count("SPACE_WITHOUT_IDENTITY") == 1


def test_annotation_and_furniture_enclosures_are_not_spaces():
    prims = F.room(0, 0, 6000, 4000, 200)
    prims += F.rect(1000, 1000, 1500, 1300, "ANNOT")                  # a small annotation box (single lines, 300 apart -> a candidate pair, isolated)
    prims += F.rect(3000, 1000, 4800, 1900, "FURN")                   # a table 1800 x 900
    r = run(prims, texts=[{"TEXT": "BED", "X": 2000, "Y": 3000, "ROLE": "ROOM_NAME"}])
    assert len(r["spaces"]) == 1 and abs(r["spaces"][0]["AREA_GEOMETRIC_M2"] - 24.0) < 0.2


def test_open_plan_doorway_and_missing_leaf_relations():
    # two rooms separated by a partition with a confirmed door: two spaces, OPEN_REGION relation on both
    prims = F.room(0, 0, 7200, 3000, 200)
    prims += F.wall((4000, 0), (4000, 1000), 200) + F.wall((4000, 1900), (4000, 3000), 200)
    prims += [F.seg("J", (3900, 1000), (4100, 1000)), F.seg("J", (3900, 1900), (4100, 1900)), F.arc("S", (4100, 1000), 900, 0.0, math.pi / 2)]
    r = run(prims, texts=[{"TEXT": "BED", "X": 2000, "Y": 1500, "ROLE": "ROOM_NAME"}, {"TEXT": "BATH", "X": 5500, "Y": 1500, "ROLE": "ROOM_NAME"}])
    assert len(r["spaces"]) == 2 and all(s["OPEN_RELATIONS"] for s in r["spaces"]) and all(s["IDENTITY_STATUS"] == "SINGLE" for s in r["spaces"])
    assert sorted(round(s["MATERIAL_BOUNDARY_MM"]) for s in r["spaces"]) == [11300, 12900]
    # missing leaf and no jambs: UNRESOLVED chord separates the rooms, both spaces BOUNDARY_PROVISIONAL
    prims = F.room(0, 0, 7200, 3000, 200) + F.wall((4000, 0), (4000, 1000), 200) + F.wall((4000, 1900), (4000, 3000), 200)
    r = run(prims)
    assert len(r["spaces"]) == 2 and all(s["GEOMETRY_STATUS"] == "BOUNDARY_PROVISIONAL" and s["UNRESOLVED_RELATIONS"] for s in r["spaces"])
    # open plan: one room with two labels -> MULTIPLE_ANCHORS_ONE_SPACE, never split
    r = run(F.room(0, 0, 8000, 4000, 200), texts=[{"TEXT": "LIVING", "X": 2000, "Y": 2000, "ROLE": "ROOM_NAME"}, {"TEXT": "DINING", "X": 6000, "Y": 2000, "ROLE": "ROOM_NAME"}])
    assert len(r["spaces"]) == 1 and r["spaces"][0]["IDENTITY_STATUS"] == "MULTIPLE" and "MULTIPLE_ANCHORS_ONE_SPACE" in [i["KIND"] for i in r["qa"]]


def _room_with_corner_gaps(gap):
    """Four wall pieces whose face lines stop `gap` mm short of the corners."""
    t = 200.0
    x0, y0, x1, y1 = 0.0, 0.0, 6000.0, 4000.0
    prims = []
    for (a, b) in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
        L = math.hypot(b[0] - a[0], b[1] - a[1]); ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L; nx, ny = -uy, ux
        # inner face on the room side is the axis line itself shifted by 0 (walls drawn outside the clear rectangle)
        inner = ((a[0] + ux * gap, a[1] + uy * gap), (b[0] - ux * gap, b[1] - uy * gap))
        outer = ((a[0] + ux * gap - nx * t, a[1] + uy * gap - ny * t), (b[0] - ux * gap - nx * t, b[1] - uy * gap - ny * t))
        prims += [F.seg("W", *inner), F.seg("W", *outer)]
    return prims


def test_corner_gaps_2_5_10_25_mm_keep_one_room():
    for gap in (2.0, 5.0, 10.0, 25.0):
        r = run(_room_with_corner_gaps(gap))
        assert len(r["spaces"]) == 1, (gap, [(f["SPACE_ELIGIBILITY"], f["AREA_GEOMETRIC_M2"]) for f in r["faces"]])
        assert abs(r["spaces"][0]["AREA_GEOMETRIC_M2"] - 24.0) < 0.3


def test_nested_column_region_is_material_not_a_space():
    prims = F.room(0, 0, 6000, 4000, 200) + F.rect(2000, 1500, 2400, 1900, "C") + [F.seg("C", (2000, 1500), (2400, 1900))]   # PA07R1: a free-standing column carries its cross
    r = run(prims)
    assert len(r["spaces"]) == 1
    inner = [f for f in r["faces"] if f["SPACE_ELIGIBILITY"] == "MATERIAL_INTERIOR" and f["AREA_GEOMETRIC_M2"] < 0.2]
    assert inner
    col = r["cols"]
    assert len(col) == 1 and col[0]["EXPOSED_TO_SPACE"]["STATUS"] == "EXPOSED" and abs(col[0]["EXPOSED_TO_SPACE"]["EXPOSED_MM_STRUCTURE_ONLY"] - 1600) <= 1
    assert col[0]["TRADE_ELIGIBILITY"]["COLUMN_BONDING"] == "CANDIDATE_LINEAR_RUN" and col[0]["TRADE_ELIGIBILITY"]["WALL_PLASTER"] == "NONE"
    assert col[0]["OBJECT_EXISTS"]["STATUS"] == "ESTABLISHED" and not col[0]["HOSTS_WALL"]


def test_embedded_and_corner_columns_are_not_double_counted():
    # column bonded into the bottom wall, flush with the inner face: the wall face is cut over the footprint, the column owns it
    prims = F.room(0, 0, 6000, 4000, 200) + F.rect(2000, -200, 2400, 200, "C")
    r = run(prims)
    s = r["spaces"][0]
    col = r["cols"][0]
    exposed = col["EXPOSED_TO_SPACE"]["EXPOSED_MM_STRUCTURE_ONLY"]
    # room perimeter 20000: bottom wall face 6000 - 400 (cut) + column face 400 proud... here the column is flush so its exposed face is 400 at y = 200
    total = s["MATERIAL_BOUNDARY_MM"]
    assert abs(total - 20000 - 2 * 200) <= 60, (total, exposed)      # flush column proud by 200 adds two 200 returns
    cut = [b for b in r["brows"] if b["SEAL_KIND"] == "JUNCTION_CUT" and b["BAND_ID"] != col["BAND_ID"]]
    assert any(abs(b["LENGTH_MM"] - 400) <= 20 for b in cut), "the wall face over the column footprint must be a JUNCTION_CUT"
    assert col["TERMINATES_WALL"] or col["EXPOSED_TO_SPACE"]["STATUS"] == "EXPOSED"


def test_wall_terminating_on_column_is_shortened():
    prims = F.room(0, 0, 6000, 4000, 200) + F.wall((3000, 0), (3000, 1500), 200) + F.rect(2700, 1500, 3300, 2100, "C")
    r = run(prims)
    col = [c for c in r["cols"] if c["OBJECT_GEOMETRY"]["SIDES_MM"] == [600.0, 600.0]]
    assert len(col) == 1 and col[0]["HOSTS_WALL"], col
    part = [b for b in r["brows"] if b["SEAL_KIND"] == "FACE" and abs(b["LENGTH_MM"] - 1500) <= 20 and b["SPACE_FACE_ID"]]
    assert len(part) == 2, "each face of the partition is 1500 long: it stops at the column, the footprint is not wall face"


def test_beam_edges_never_material_and_never_boundary():
    prims = F.room(0, 0, 6000, 4000, 200) + [F.seg("B", (0, 2000), (6000, 2000), linetype="HIDDEN", role="BEAM_EDGE"), F.seg("B", (0, 2300), (6000, 2300), linetype="HIDDEN", role="BEAM_EDGE")]
    r = run(prims)
    assert len(r["spaces"]) == 1 and abs(r["spaces"][0]["AREA_GEOMETRIC_M2"] - 24.0) < 0.2
    assert r["beams"]["COUNT"] == 2 and r["beams"]["USED_AS_MATERIAL_FACE"] is False and r["beams"]["TRADE_ELIGIBILITY"]["WALL_PLASTER"] == "NONE"


def test_glazing_separator_splits_topology_without_material():
    prims = F.room(0, 0, 8000, 4000, 200) + [F.seg("G", (4000, 0), (4000, 4000), role="GLAZING")]
    r = run(prims)
    assert len(r["spaces"]) == 2 and all(s["GEOMETRY_STATUS"] == "BOUNDARY_PROVISIONAL" for s in r["spaces"])
    assert all(s["MATERIAL_BOUNDARY_MM"] < 13000 for s in r["spaces"])   # 2 x (4000 + 4000) - glazing side 4000 = 12000 each
