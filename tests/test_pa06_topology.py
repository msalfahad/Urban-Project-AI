"""PA06 regression tests: source units, primitive roles, wall-material continuity (fixtures A-J), cells / regions,
vector wall length, storeys, semantics, states.  Synthetic drawings only; P7757 enters only through fixtures."""

from __future__ import annotations

import math
from types import SimpleNamespace

import pytest

from engine.ingest import primitive_roles as PRO, wall_continuity as WC, spaces_v2 as SP, space_boundary as SB, source_units as SU, storeys as STY, semantics as SEM, states as STS
from engine.ingest import units as U


# ------------------------------------------------------------------ builders
_n = [0]


def seg(layer, a, b, block=()):
    _n[0] += 1
    return SimpleNamespace(kind="SEGMENT", object_id=f"E{_n[0]}", x1=a[0], y1=a[1], x2=b[0], y2=b[1], cx=0.0, cy=0.0, radius=0.0, start_angle=0.0, end_angle=0.0,
                           provenance=SimpleNamespace(layer=layer, handle=_n[0], entity_type="LINE", block_path=tuple(block), instance_path=()))


def arc(layer, c, r, a0, a1):
    _n[0] += 1
    return SimpleNamespace(kind="ARC", object_id=f"E{_n[0]}", x1=0.0, y1=0.0, x2=0.0, y2=0.0, cx=c[0], cy=c[1], radius=r, start_angle=a0, end_angle=a1,
                           provenance=SimpleNamespace(layer=layer, handle=_n[0], entity_type="ARC", block_path=(), instance_path=()))


def wall(layer, a, b, t=200.0):
    """A double-line wall from a to b (axis), thickness t."""
    L = math.hypot(b[0] - a[0], b[1] - a[1]); ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L; nx, ny = -uy, ux
    return [seg(layer, (a[0] + nx * t / 2, a[1] + ny * t / 2), (b[0] + nx * t / 2, b[1] + ny * t / 2)), seg(layer, (a[0] - nx * t / 2, a[1] - ny * t / 2), (b[0] - nx * t / 2, b[1] - ny * t / 2))]


LAYERS = {"WALL_LAYERS": ["W"], "DOOR_LAYER": "D", "DIMENSION_LAYERS": ["DIM"], "HIDDEN_LAYERS": ["HID"], "GLAZING_LAYERS": ["GLZ"], "TEXT_LAYERS": []}


def run(prims, box=(0, 0, 12000, 8000)):
    roles = PRO.classify(prims, LAYERS)
    view = {"VIEW_ID": "VW-test", "BBOX_MM": list(box)}
    eids = {p.object_id: p.object_id for p in prims}
    sites, non, bands = WC.find_sites("VW-test", prims, roles, eids)
    cells, regions, grids = SP.build(view, prims, roles, sites)
    return roles, sites, non, bands, cells, regions, grids


def two_rooms(gap=(1500.0, 2400.0), leaf=True, wall_t=200.0):
    """Two rooms 6 x 4 m side by side (x 0..12000, y 0..4000), shared wall at x = 6000 with a gap in y."""
    prims = wall("W", (0, 0), (12000, 0), wall_t) + wall("W", (0, 4000), (12000, 4000), wall_t) + wall("W", (0, 0), (0, 4000), wall_t) + wall("W", (12000, 0), (12000, 4000), wall_t)
    prims += wall("W", (6000, 0), (6000, gap[0]), wall_t) + wall("W", (6000, gap[1]), (6000, 4000), wall_t)
    # jamb returns
    prims += [seg("W", (6000 - wall_t / 2, gap[0]), (6000 + wall_t / 2, gap[0])), seg("W", (6000 - wall_t / 2, gap[1]), (6000 + wall_t / 2, gap[1]))]
    if leaf:
        prims.append(arc("D", (6000 + wall_t / 2, gap[0]), gap[1] - gap[0], 0.0, math.pi / 2))
    return prims


def in_range(cells):
    return [c for c in cells if c["IN_RANGE"]]


# ------------------------------------------------------------------ WS3 fixtures A-J
def test_A_corridor_crossed_by_collinear_stubs_is_one_space():
    # corridor y 3000..5000 across the plan; rooms above and below; partitions at x = 6000 above and below the corridor are collinear stubs
    prims = wall("W", (0, 0), (12000, 0)) + wall("W", (0, 8000), (12000, 8000)) + wall("W", (0, 0), (0, 8000)) + wall("W", (12000, 0), (12000, 8000))
    prims += wall("W", (0, 3000), (12000, 3000)) + wall("W", (0, 5000), (12000, 5000))
    prims += wall("W", (6000, 0), (6000, 3000)) + wall("W", (6000, 5000), (6000, 8000))
    roles, sites, non, bands, cells, regions, grids = run(prims)
    assert any(n["RECORD"] == "COLLINEAR_STUBS_NOT_A_SITE" for n in non), "the corridor crossing must be recorded as a non-site"
    assert not any(s["CLASS"] in ("UNRESOLVED_SITE", "CONFIRMED_DOOR_OPENING") and s.get("GAP_SPAN_MM") and abs(s["GAP_SPAN_MM"] - 2000) < 300 for s in sites)
    corridor = [c for c in in_range(cells) if 20 < c["AREA_M2"] < 26]
    assert len(corridor) == 1, [c["AREA_M2"] for c in in_range(cells)]
    assert len(in_range(cells)) == 5


def test_B_true_doorway_with_leaf():
    roles, sites, non, bands, cells, regions, grids = run(two_rooms())
    doors = [s for s in sites if s["CLASS"] == "CONFIRMED_DOOR_OPENING"]
    assert len(doors) == 1 and abs(doors[0]["GAP_SPAN_MM"] - 900) < 5 and doors[0]["PHYSICAL_SEPARATOR"]
    assert doors[0]["LEFT_TERMINATION"]["KIND"] == "JAMB_RETURN" and doors[0]["RIGHT_TERMINATION"]["KIND"] == "JAMB_RETURN"
    assert len(in_range(cells)) == 2 and len([r for r in regions if r["IN_RANGE"]]) == 2


def test_C_double_leaf_doorway():
    prims = two_rooms(gap=(1000.0, 2800.0), leaf=False)
    prims.append(arc("D", (6100, 1000), 900, 0.0, math.pi / 2)); prims.append(arc("D", (6100, 2800), 900, 3 * math.pi / 2, 2 * math.pi))
    roles, sites, non, bands, cells, regions, grids = run(prims)
    doors = [s for s in sites if s["CLASS"] == "CONFIRMED_DOOR_OPENING"]
    assert len(doors) == 1 and doors[0]["OPENING_EVIDENCE"]["DOUBLE_LEAF"] and abs(doors[0]["GAP_SPAN_MM"] - 1800) < 5


def test_D_missing_leaf_with_jamb_pair_is_unresolved_site_two_cells_one_region():
    roles, sites, non, bands, cells, regions, grids = run(two_rooms(leaf=False))
    unresolved = [s for s in sites if s["CLASS"] == "UNRESOLVED_SITE"]
    assert len(unresolved) == 1 and not unresolved[0]["PHYSICAL_SEPARATOR"] and unresolved[0]["TOPOLOGY_CELL_BARRIER"]
    assert len(in_range(cells)) == 2, "cells stay separate at an unresolved site"
    regs = [r for r in regions if r["IN_RANGE"]]
    assert len(regs) == 1 and regs[0]["CELL_COUNT"] == 2 and regs[0]["TOPOLOGY_STATUS"] == "OPEN_GROUP_OF_CELLS", "the physical region is one open group"


def test_E_T_junction_is_not_a_site():
    prims = wall("W", (0, 0), (12000, 0)) + wall("W", (0, 4000), (12000, 4000)) + wall("W", (0, 0), (0, 4000)) + wall("W", (12000, 0), (12000, 4000)) + wall("W", (6000, 0), (6000, 4000))
    roles, sites, non, bands, cells, regions, grids = run(prims)
    assert not [s for s in sites if s["CLASS"] in ("UNRESOLVED_SITE", "CONFIRMED_DOOR_OPENING")]
    assert len(in_range(cells)) == 2


def test_F_tiny_cad_gap_is_junction_gap_and_no_leak():
    prims = two_rooms(gap=(2000.0, 2060.0), leaf=False)
    roles, sites, non, bands, cells, regions, grids = run(prims)
    assert [s["CLASS"] for s in sites if s.get("GAP_SPAN_MM") and s["GAP_SPAN_MM"] < 120] == ["CAD_JUNCTION_GAP"]
    assert len(in_range(cells)) == 2


def test_G_open_plan_transition_is_true_termination_one_cell():
    # the shared wall stops after 1.5 m: a 2.5 m ... no: leaves a 5 m opening -> TRUE_WALL_TERMINATION, one physical region and one cell
    prims = wall("W", (0, 0), (12000, 0)) + wall("W", (0, 4000), (12000, 4000)) + wall("W", (0, 0), (0, 4000)) + wall("W", (12000, 0), (12000, 4000)) + wall("W", (6000, 0), (6000, 1500))
    roles, sites, non, bands, cells, regions, grids = run(prims)
    assert not [s for s in sites if s["CLASS"] in ("UNRESOLVED_SITE", "CONFIRMED_DOOR_OPENING")]
    assert len(in_range(cells)) == 1 and abs(in_range(cells)[0]["AREA_M2"] - (11.8 * 3.8 - 0.2 * 1.4)) < 1.5


def test_H_window_in_wall():
    prims = two_rooms(gap=(1500.0, 3000.0), leaf=False)
    prims += [seg("X", (5950, 1500), (5950, 3000)), seg("X", (6050, 1500), (6050, 3000))]      # frame lines inside the wall strip across the gap
    roles, sites, non, bands, cells, regions, grids = run(prims)
    win = [s for s in sites if s["CLASS"] == "CONFIRMED_WINDOW_OPENING"]
    assert len(win) == 1 and win[0]["PHYSICAL_SEPARATOR"] and len(in_range(cells)) == 2


def test_I_glazing_separator():
    prims = two_rooms(gap=(500.0, 3500.0), leaf=False)
    prims.append(seg("GLZ", (6000, 500), (6000, 3500)))
    roles, sites, non, bands, cells, regions, grids = run(prims)
    assert roles[prims[-1].object_id]["ROLE"] == "GLAZING"
    assert len(in_range(cells)) == 2 and len([r for r in regions if r["IN_RANGE"]]) == 2, "glazing is a physical separator"


def test_J_annotation_line_aligned_with_wall_is_not_material():
    prims = two_rooms(leaf=True)
    prims.append(seg("DIM", (6000, 1500), (6000, 2400)))       # a dimension line exactly across the doorway
    roles, sites, non, bands, cells, regions, grids = run(prims)
    assert roles[prims[-1].object_id]["ROLE"] in ("DIMENSION_LINE", "DIMENSION_EXTENSION") and not roles[prims[-1].object_id]["MATERIAL"]
    assert [s["CLASS"] for s in sites if s.get("GAP_SPAN_MM") and 800 < s["GAP_SPAN_MM"] < 1000] == ["CONFIRMED_DOOR_OPENING"]


# ------------------------------------------------------------------ WS2 role tests
def test_door_swing_and_hatch_on_wall_layer_are_not_walls():
    prims = two_rooms()
    prims.append(arc("W", (6100, 1500), 900, 0.0, math.pi / 2))                 # swing drawn on the wall layer, hinged at the jamb
    prims += [seg("W", (1000 + i * 60, 100), (1040 + i * 60, 140)) for i in range(20)]   # dense hatch strokes on the wall layer
    roles = PRO.classify(prims, LAYERS)
    assert roles[prims[-21].object_id]["ROLE"] == "DOOR_SWING"
    assert all(roles[p.object_id]["ROLE"] == "HATCH_STROKE" for p in prims[-20:])


def test_angled_and_curved_walls_stay_walls_and_column_is_a_column():
    prims = wall("W", (0, 0), (5000, 3000)) + [arc("W", (0, 0), 3000, 0.0, math.pi / 2), arc("W", (0, 0), 3200, 0.0, math.pi / 2)]
    prims += [seg("W", (8000, 8000), (8400, 8000)), seg("W", (8400, 8000), (8400, 8400)), seg("W", (8400, 8400), (8000, 8400)), seg("W", (8000, 8400), (8000, 8000))]
    roles = PRO.classify(prims, LAYERS)
    assert roles[prims[0].object_id]["ROLE"] == "MATERIAL_WALL_FACE" and roles[prims[0].object_id]["ROLE_STATUS"] == "ESTABLISHED"
    assert roles[prims[2].object_id]["ROLE"] == "MATERIAL_WALL_FACE" and roles[prims[3].object_id]["ROLE"] == "MATERIAL_WALL_FACE"
    assert all(roles[p.object_id]["ROLE"] == "COLUMN_FACE" for p in prims[-4:])


def test_dimension_extension_crossing_a_wall_is_never_material():
    prims = two_rooms()
    ext = seg("DIM", (3000, -500), (3000, 4500))
    d = SimpleNamespace(x1=3000, y1=-500, x2=8000, y2=-500)
    roles = PRO.classify(prims + [ext], LAYERS, dims=[d])
    assert roles[ext.object_id]["ROLE"] == "DIMENSION_EXTENSION" and roles[ext.object_id]["MATERIAL"] is False


# ------------------------------------------------------------------ WS4 vector wall length
def test_vector_wall_length_rotated_room_and_curved_room():
    for deg in (0, 10, 30, 45):
        a = math.radians(deg); c, s = math.cos(a), math.sin(a)
        R = lambda x, y: (6000 + x * c - y * s, 4000 + x * s + y * c)
        prims = wall("W", R(-4000, -2500), R(4000, -2500)) + wall("W", R(4000, -2500), R(4000, 2500)) + wall("W", R(4000, 2500), R(-4000, 2500)) + wall("W", R(-4000, 2500), R(-4000, -2500))
        roles, sites, non, bands, cells, regions, grids = run(prims, box=(0, 0, 12000, 8000))
        inner = [x for x in in_range(cells)]
        assert len(inner) == 1, deg
        edges, _ = SB.boundary_faces("VW-test", prims, roles, cells, grids, sites, {p.object_id: p.object_id for p in prims})
        wl = [w for w in SB.wall_lengths(cells, regions, edges) if w["SPACE_ID"] == inner[0]["CELL_ID"]][0]
        expected = 2 * (8.0 - 0.2) + 2 * (5.0 - 0.2)
        assert abs(wl["VECTOR_MATERIAL_WALL_M"] - expected) / expected < 0.02, (deg, wl["VECTOR_MATERIAL_WALL_M"])
        assert wl["POLYGON_PERIMETER_USED"] is False and wl["RASTER_RUNS_USED"] is False
    # curved room: annulus sector between two concentric arcs closed by two radial walls
    prims = [arc("W", (6000, 4000), 2000, 0.0, math.pi / 2), arc("W", (6000, 4000), 2200, 0.0, math.pi / 2), arc("W", (6000, 4000), 5000, 0.0, math.pi / 2), arc("W", (6000, 4000), 5200, 0.0, math.pi / 2)]
    prims += wall("W", (8100, 4000), (11100, 4000)) + wall("W", (6000, 6100), (6000, 9100))
    roles, sites, non, bands, cells, regions, grids = run(prims, box=(0, 0, 12000, 10000))
    inner = in_range(cells)
    assert len(inner) == 1
    edges, _ = SB.boundary_faces("VW-test", prims, roles, cells, grids, sites, {p.object_id: p.object_id for p in prims})
    arc_edges = [e for e in edges if e["SPACE_ID"] == inner[0]["CELL_ID"] and e["GEOMETRY_SOURCE"] == "VECTOR_ARC"]
    developed = sum(e["DEVELOPED_LENGTH_MM"] for e in arc_edges) / 1000
    expected = ((2200 + 5000) * math.pi / 2 - 400) / 1000        # each arc loses one wall thickness of exposure at the two radial walls
    assert abs(developed - expected) / expected < 0.03, developed


# ------------------------------------------------------------------ WS1 units
def _drawing(insunits, scale_units, dims_text=None, door_r=None):
    prims = [seg("W", (0, 0), (8000 / scale_units, 0)), seg("W", (0, 200 / scale_units), (8000 / scale_units, 200 / scale_units))]
    if door_r:
        prims.append(arc("D", (0, 0), door_r, 0.0, math.pi / 2))
    dims = []
    for i, (g, disp, txt) in enumerate(dims_text or []):
        dims.append(SimpleNamespace(geometry_mm=g, display_value=disp, dimlfac=1.0, user_text=txt, x1=0, y1=0, x2=g, y2=0, provenance=SimpleNamespace(handle=i, layer="DIM", entity_type="21")))
    return SimpleNamespace(insunits_code=insunits, drawing_unit="", dimlfac=1.0, primitives=prims, texts=[], dimensions=dims, source_file="x")


def test_units_mm_and_m_and_unitless_and_conflict():
    r = SU.resolve(_drawing(4, 1.0, [(8000, 8000, ""), (3000, 3000, "")], door_r=900), source_id="a")
    assert r["STATUS"] == "SOURCE_ESTABLISHED" and r["UNIT_SCALE_TO_MM"] == 1.0 and r["ACCEPTABLE_FOR_QUANTITIES"]
    r = SU.resolve(_drawing(6, 1000.0, [(8.0, 8.0, ""), (3.0, 3.0, "")], door_r=0.9), source_id="b")
    assert r["STATUS"] == "SOURCE_ESTABLISHED" and r["UNIT_SCALE_TO_MM"] == 1000.0
    r = SU.resolve(_drawing(0, 1000.0, [(8.0, 8.0, "8.00 m"), (3.0, 3.0, "3.00 m")]), source_id="c")
    assert r["STATUS"] == "SOURCE_ESTABLISHED" and r["PROVENANCE"] == "DIMENSION_TEXT_UNIT_SUFFIX" and abs(r["UNIT_SCALE_TO_MM"] - 1000.0) < 1e-6
    r = SU.resolve(_drawing(4, 1.0, [(8.0, 8.0, "8.00 m"), (3.0, 3.0, "3.00 m")]), source_id="d")     # INSUNITS says mm, the texts say the units are metres
    assert r["STATUS"] == "CONFLICT" and r["CONFLICT"]["KIND"] == "INSUNITS_VS_DIMENSION_TEXT" and not r["ACCEPTABLE_FOR_QUANTITIES"]
    r = SU.resolve(_drawing(0, 1.0), source_id="e")
    assert r["STATUS"] == "NOT_ESTABLISHED" and r["UNIT_SCALE_TO_MM"] is None
    r = SU.resolve(_drawing(0, 1.0), source_id="f", declared_unit="mm")
    assert r["STATUS"] == "DECLARED_ESTABLISHED"
    r = SU.resolve(_drawing(4, 1.0, [(8000, 8000, "")], door_r=0.9), source_id="g", door_layer="D")
    assert r["STATUS"] == "CONFLICT", "a door swing of 0.9 units under a mm candidate is outside the band"


def test_scaling_keeps_identity():
    from engine.ingest import ids
    d_mm = _drawing(4, 1.0); d_m = _drawing(6, 1000.0)
    s = SU.scale_drawing(d_m, 1000.0)
    a = ids.entity_id("VW", "W", "SEGMENT", ((d_mm.primitives[0].x1, d_mm.primitives[0].y1), (d_mm.primitives[0].x2, d_mm.primitives[0].y2)))
    b = ids.entity_id("VW", "W", "SEGMENT", ((s.primitives[0].x1, s.primitives[0].y1), (s.primitives[0].x2, s.primitives[0].y2)))
    assert a == b


# ------------------------------------------------------------------ WS5 storeys
def test_storeys_from_copies_levels_and_unrelated_clusters():
    def plan(dx, dy, rot=0, level=None, label=None):
        prims = [seg("W", (0 + dx, 0 + dy), (8000 + dx, 0 + dy))] * 0
        base = wall("W", (0, 0), (8000, 0)) + wall("W", (8000, 0), (8000, 5000)) + wall("W", (8000, 5000), (0, 5000)) + wall("W", (0, 5000), (0, 0)) + wall("W", (3000, 0), (3000, 5000))
        out = []
        for p in base:
            x1, y1, x2, y2 = p.x1, p.y1, p.x2, p.y2
            for _ in range(rot):
                x1, y1, x2, y2 = -y1, x1, -y2, x2
            out.append(seg("W", (x1 + dx, y1 + dy), (x2 + dx, y2 + dy)))
        texts = []
        if level is not None:
            texts.append(SimpleNamespace(value=level, x=1000 + dx, y=1000 + dy, provenance=SimpleNamespace(layer="T", handle=1)))
        if label:
            texts.append(SimpleNamespace(value=label, x=1500 + dx, y=1500 + dy, provenance=SimpleNamespace(layer="T", handle=2)))
        return out, texts
    p1, t1 = plan(0, 0, level="%%p0.00", label="GROUND FLOOR PLAN"); p2, t2 = plan(20000, 0, level="+4.50"); p3, t3 = plan(40000, 0, rot=1, level="+9.00")
    detail = [seg("W", (70000 + i * 100, 0), (70000 + i * 100 + 50, 30)) for i in range(60)]
    views = [{"VIEW_ID": "V1", "PRIMITIVES": p1, "TEXTS": t1, "ROLE": {"FINAL_ROLE": "FLOOR_PLAN"}}, {"VIEW_ID": "V2", "PRIMITIVES": p2, "TEXTS": t2, "ROLE": {"FINAL_ROLE": "FLOOR_PLAN"}},
             {"VIEW_ID": "V3", "PRIMITIVES": p3, "TEXTS": t3, "ROLE": {"FINAL_ROLE": "FLOOR_PLAN"}}, {"VIEW_ID": "V4", "PRIMITIVES": detail, "TEXTS": [], "ROLE": {"FINAL_ROLE": "DETAIL"}}]
    fams, links = STY.copy_families(views, min_matches=10)
    assert len(fams) == 1 and set(fams[0]["MEMBERS"]) == {"V1", "V2", "V3"}
    assert any(l["ROTATION_DEG"] % 180 == 90 for l in links), links
    rows = STY.storey_register(views, fams)
    by = {r["PLAN_COPY_ID"]: r for r in rows}
    assert by["V1"]["STOREY_NAME"] == "GROUND_FLOOR" and by["V1"]["NAME_STATUS"] == "SOURCE_ESTABLISHED"
    assert by["V2"]["STOREY_NAME"] is None and by["V2"]["GENERIC_NAME"] == "FLOOR_02" and by["V2"]["STOREY_RELATION_STATUS"] == "ORDERED_BY_LEVEL_TEXT"
    assert by["V3"]["GENERIC_NAME"] == "FLOOR_03" and "V4" not in by
    # two plans at the same level: order not established
    p2b, t2b = plan(20000, 0, level="%%p0.00")
    views2 = [views[0], {"VIEW_ID": "V2", "PRIMITIVES": p2b, "TEXTS": t2b, "ROLE": {"FINAL_ROLE": "FLOOR_PLAN"}}]
    fams2, _ = STY.copy_families(views2, min_matches=10)
    rows2 = STY.storey_register(views2, fams2)
    assert all(r["STOREY_RELATION_STATUS"] == "ORDER_NOT_ESTABLISHED" and r["GENERIC_NAME"] == "FLOOR_UNORDERED" for r in rows2)


# ------------------------------------------------------------------ WS7 semantics
def test_bilingual_text_ontology_and_no_geometry_from_text():
    assert SEM.classify_text("MASTER BED ROOM")["CANONICAL_CLASS"] == "MASTER_BEDROOM"
    assert SEM.classify_text("غرفة نوم رئيسية") == {"TEXT_ROLE": "ROOM_NAME", "CANONICAL_CLASS": "MASTER_BEDROOM", "LANGUAGE": "AR", "MATCHED": "غرفة نوم رئيسية"}
    assert SEM.classify_text("W.C")["CANONICAL_CLASS"] == "WC" and SEM.classify_text("مطبخ")["CANONICAL_CLASS"] == "KITCHEN"
    assert SEM.classify_text("%%p0.00")["TEXT_ROLE"] == "LEVEL_MARK" and SEM.classify_text("31.37")["TEXT_ROLE"] == "DIMENSION_OR_NUMBER"
    assert SEM.classify_text("NEIGHBOUR")["TEXT_ROLE"] == "SITE_LABEL"
    assert SEM.classify_text("M—HAe")["TEXT_ROLE"] == "UNDECODABLE_TEXT"
    roles, sites, non, bands, cells, regions, grids = run(two_rooms(leaf=False))
    view = {"VIEW_ID": "VW-test"}
    texts = [SimpleNamespace(value="SALOON", x=3000, y=2000, provenance=SimpleNamespace(layer="T", handle=1)), SimpleNamespace(value="طعام", x=9000, y=2000, provenance=SimpleNamespace(layer="T", handle=2)),
             SimpleNamespace(value="STORE", x=20000, y=20000, provenance=SimpleNamespace(layer="T", handle=3))]
    n_cells = len(cells)
    anchors, zones = SEM.anchors(view, cells, regions, grids, texts)
    assert len(cells) == n_cells and all(a["CREATES_GEOMETRY"] is False for a in anchors)
    reg = [r for r in regions if r["IN_RANGE"]][0]
    assert sorted(z[0] for z in reg["SEMANTIC_IDENTITY"]["ZONES"]) == ["DINING", "SALOON"] and reg["SEMANTIC_IDENTITY"]["STATUS"] == "MULTIPLE_FUNCTIONAL_ZONES_ONE_PHYSICAL_REGION"
    assert [a for a in anchors if a["RAW_TEXT"] == "STORE"][0]["IDENTITY_STATUS"] == "UNRESOLVED"
    assert all(a["IDENTITY_STATUS"] != "SOURCE_TEXT_ESTABLISHED" for a in anchors if a["SOURCE"]["KIND"] == "AI_VISUAL_READ")


# ------------------------------------------------------------------ WS10 states / units
def test_state_lattice_and_adapters():
    assert STS.adapt("OWNER_AUTHORISED", "height_parameters") == "OWNER_PROJECT_INPUT" and STS.adapt("TEMPORARY_DEFAULT", "a21_provenance") == "PROVISIONAL"
    assert STS.adapt("whatever", "quantity_state") == "HUMAN_REVIEW"
    assert STS.weakest(["SOURCE_ESTABLISHED", "OWNER_PARAMETRIC", "PROVISIONAL"]) == "PROVISIONAL" and STS.weakest(["SOURCE_ESTABLISHED", "SOURCE_REQUIRED"]) == "SOURCE_REQUIRED"
    with pytest.raises(ValueError):
        STS.record(CONFIDENCE="HIGH")
    with pytest.raises(U.UnitError):
        U.Q(1, "m") + U.Q(1, "m2")
    assert (U.Q(2, "lm") + U.Q(1, "m")).v == 3 and U.Q(2, "lm").record()["INTERNAL_UNIT"] == "m"
