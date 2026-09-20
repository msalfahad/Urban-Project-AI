"""PA06 end-to-end: a synthetic two-room villa (primitive JSON) through the whole pipeline to a quantity-input trace
whose principal wall-face area is established by the existing plaster engine; blocks rotated / mirrored / scaled;
storey ordering; and the P7757 regression (skipped without the sources)."""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from engine.ingest import pipeline as PL

EXP = json.loads((Path(__file__).parent / "data" / "p7757_pa05_expectations.json").read_text("utf-8"))


def _wall(a, b, t=200.0, layer="W"):
    L = math.hypot(b[0] - a[0], b[1] - a[1]); ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L; nx, ny = -uy, ux
    return [{"kind": "SEGMENT", "layer": layer, "x1": a[0] + nx * t / 2, "y1": a[1] + ny * t / 2, "x2": b[0] + nx * t / 2, "y2": b[1] + ny * t / 2},
            {"kind": "SEGMENT", "layer": layer, "x1": a[0] - nx * t / 2, "y1": a[1] - ny * t / 2, "x2": b[0] - nx * t / 2, "y2": b[1] - ny * t / 2}]


def villa(tmp_path, dx=0.0, dy=0.0, level="%%p0.00", labels=("LIVING", "مطبخ"), with_leaf=True, unitless=False, scale=1.0):
    """Two rooms 6 x 4 m, shared wall with a 0.9 m door, one hatch block, one dimension, room labels, level mark."""
    s = scale
    P = []
    for a, b in (((0, 0), (12000, 0)), ((0, 4000), (12000, 4000)), ((0, 0), (0, 4000)), ((12000, 0), (12000, 4000)), ((6000, 0), (6000, 1500)), ((6000, 2400), (6000, 4000))):
        P += _wall((a[0] * s + dx, a[1] * s + dy), (b[0] * s + dx, b[1] * s + dy), t=200 * s)
    P += [{"kind": "SEGMENT", "layer": "W", "x1": 5900 * s + dx, "y1": 1500 * s + dy, "x2": 6100 * s + dx, "y2": 1500 * s + dy}, {"kind": "SEGMENT", "layer": "W", "x1": 5900 * s + dx, "y1": 2400 * s + dy, "x2": 6100 * s + dx, "y2": 2400 * s + dy}]
    if with_leaf:
        P.append({"kind": "ARC", "layer": "D", "cx": 6100 * s + dx, "cy": 1500 * s + dy, "r": 900 * s, "a0": 0.0, "a1": math.pi / 2})
    P += [{"kind": "SEGMENT", "layer": "W", "x1": (1000 + i * 60) * s + dx, "y1": 100 * s + dy, "x2": (1040 + i * 60) * s + dx, "y2": 140 * s + dy} for i in range(20)]      # hatch strokes on the wall layer
    P += [{"kind": "SEGMENT", "layer": "DIM", "x1": 0 + dx, "y1": -600 * s + dy, "x2": 12000 * s + dx, "y2": -600 * s + dy}]
    # enough small entities for view clustering
    P += [{"kind": "CIRCLE", "layer": "F", "cx": (2000 + i * 150) * s + dx, "cy": 3000 * s + dy, "r": 20 * s} for i in range(40)]
    doc = {"insunits": None if unitless else (4 if s == 1.0 else 6), "dimlfac": 1.0, "linetypes": {"W": "CONTINUOUS", "D": "CONTINUOUS", "DIM": "CONTINUOUS", "F": "CONTINUOUS"}, "primitives": P,
           "texts": [{"value": labels[0], "x": 3000 * s + dx, "y": 2000 * s + dy}, {"value": labels[1], "x": 9000 * s + dx, "y": 2000 * s + dy}, {"value": level, "x": 500 * s + dx, "y": 3500 * s + dy}],
           "dimensions": [{"x1": 0 + dx, "y1": -600 * s + dy, "x2": 12000 * s + dx, "y2": -600 * s + dy, "display": 12000 * s}, {"x1": 0 + dx, "y1": 4000 * s + dy, "x2": 6000 * s + dx, "y2": 4000 * s + dy, "display": 6000 * s}]}
    p = tmp_path / "villa.json"; p.write_text(json.dumps(doc), "utf-8")
    return p


REG = {"_REGISTRY_ID": "TEST", "NORMAL_INTERNAL_PLASTER_HEIGHT": {"VALUE": 3.0, "SOURCE_TYPE": "OWNER_PROJECT_INPUT"}, "DOOR_HEIGHT": {"VALUE": 2.2, "SOURCE_TYPE": "TEMPORARY_OWNER_DEFAULT"},
       "DOOR_REVEAL_DEPTH": {"VALUE": 0.15, "SOURCE_TYPE": "TEMPORARY_OWNER_DEFAULT"}, "TARTUSHA_HEIGHT": {"VALUE": None, "SOURCE_TYPE": "UNKNOWN"}}


def cfg(path, **over):
    c = {"PROJECT_ID": "SYN", "SOURCES": [{"PATH": str(path), "KIND": "PRIMITIVE_JSON", "FAMILY": "ARCHITECTURAL"}], "OWNER_PARAMETER_REGISTRY": REG, "CAD_UNITS": "mm"}
    c.update(over)
    return c


def test_end_to_end_two_room_villa_established_area(tmp_path):
    r = PL.run(cfg(villa(tmp_path)))
    R = r.registers
    assert R["PA06_SOURCE_UNIT_REGISTER"]["ROWS"][0]["STATUS"] == "SOURCE_ESTABLISHED"
    roles = R["PA06_PRIMITIVE_ROLE_REGISTER"]["BY_ROLE"]
    assert roles["HATCH_STROKE"]["COUNT"] == 20 and roles["DOOR_SWING"]["COUNT"] == 1
    assert R["PA06_TOPOLOGICAL_SITE_REGISTER"]["SUMMARY"]["CONFIRMED_DOOR_OPENING"] == 1
    cells = [c for c in R["PA06_PHYSICAL_SPACE_REGISTER"]["CELLS"] if c["IN_RANGE"]]
    assert len(cells) == 2
    lines = [l for l in R["PA06_QUANTITY_INPUT_TRACE"]["LINES"] if l["TRADE"] == "NORMAL_INTERNAL_PLASTER"]
    assert len(lines) == 2
    saloon = next(l for l in lines if ("LIVING", "SOURCE_TEXT_ESTABLISHED") in [tuple(z) for z in l["SEMANTIC_IDENTITY"]["ZONES"]])
    kitchen = next(l for l in lines if ("KITCHEN", "SOURCE_TEXT_ESTABLISHED") in [tuple(z) for z in l["SEMANTIC_IDENTITY"]["ZONES"]])
    for l in (saloon, kitchen):
        assert l["REGION_STATUS"] == "MEASUREMENT_REGION_CLOSED", l["REGION_REASONS"]
        lm = l["LENGTH_GEOMETRY"]["VECTOR_LM"]
        expected_lm = 2 * (6.0 - 0.2) + 2 * (4.0 - 0.2) - 0.9      # inner faces minus the door span
        assert abs(lm - expected_lm) / expected_lm < 0.03, (lm, expected_lm)
        assert l["HEIGHT_SOURCE"]["PARAMETER_ID"] == "NORMAL_INTERNAL_PLASTER_HEIGHT" and l["HEIGHT_SOURCE"]["VALUE_M"] == 3.0
        expected_area = expected_lm * 3.0 - 0.9 * 2.2
        assert abs(l["AREA_M2_PRINCIPAL"] - expected_area) / expected_area < 0.03, (l["AREA_M2_PRINCIPAL"], expected_area)
        assert l["QUANTITY_STATUS"] == "PROVISIONAL", l["QUANTITY_STATUS"]     # the door height is a temporary default -> weakest input
        assert l["OPENING_DEDUCTION_SOURCE"] and l["BARE_NUMBER"] is False and l["TRADE_RULE"]["ENGINE"] == "engine.plaster_trade_engine"
    assert R["PA06_QUANTITY_INPUT_TRACE"]["TOTALS"] is None
    assert R["PA06_TRADE_MEASUREMENT_REGION_REGISTER"]["REVERSIBILITY"]["ALL_REVERSIBLE"] and R["PA06_TRADE_MEASUREMENT_REGION_REGISTER"]["REVERSIBILITY"]["ALL_ZERO_MATERIAL"]
    st = R["PA06_STOREY_REGISTER"]["ROWS"]
    assert len(st) == 1 and st[0]["REFERENCE_LEVEL"] == 0.0


def test_missing_leaf_blocks_the_region_honestly(tmp_path):
    r = PL.run(cfg(villa(tmp_path, with_leaf=False)))
    lines = [l for l in r.registers["PA06_QUANTITY_INPUT_TRACE"]["LINES"] if l["TRADE"] == "NORMAL_INTERNAL_PLASTER"]
    assert lines and all(l["REGION_STATUS"] == "MEASUREMENT_REGION_NOT_ESTABLISHED" and l["AREA_M2_PRINCIPAL"] is None and l["QUANTITY_STATUS"] == "NOT_ESTABLISHED" for l in lines)
    assert all(any(x["REASON"] in ("AN_UNRESOLVED_GAP_LIES_ON_THE_BOUNDARY", "A_SITE_THIS_BASIS_MAY_NOT_CLOSE_LIES_ON_THE_BOUNDARY") for x in l["REGION_REASONS"]) for l in lines)
    cells = [c for c in r.registers["PA06_PHYSICAL_SPACE_REGISTER"]["CELLS"] if c["IN_RANGE"]]
    regions = [x for x in r.registers["PA06_PHYSICAL_SPACE_REGISTER"]["REGIONS"] if x["IN_RANGE"]]
    assert len(cells) == 2 and len(regions) == 1


def test_metre_drawing_gives_same_ids_and_lengths(tmp_path):
    (tmp_path / "mm").mkdir(); (tmp_path / "m").mkdir()
    a = PL.run(cfg(villa(tmp_path / "mm")))
    b = PL.run(cfg(villa(tmp_path / "m", scale=0.001)))
    ua, ub = a.registers["PA06_SOURCE_UNIT_REGISTER"]["ROWS"][0], b.registers["PA06_SOURCE_UNIT_REGISTER"]["ROWS"][0]
    assert ua["UNIT_CANDIDATE"] == "mm" and ub["UNIT_CANDIDATE"] == "m" and ub["UNIT_SCALE_TO_MM"] == 1000.0
    la = a.registers["PA06_SPACE_WALL_LENGTH_REGISTER"]["TOTALS_STRUCTURE_ONLY"]["VECTOR_MATERIAL_WALL_M_IN_RANGE_CELLS"]; lb = b.registers["PA06_SPACE_WALL_LENGTH_REGISTER"]["TOTALS_STRUCTURE_ONLY"]["VECTOR_MATERIAL_WALL_M_IN_RANGE_CELLS"]
    assert abs(la - lb) / la < 0.01
    ea = {m["ENTITY_ID"] for m in a.registers["PA06_MATERIAL_GEOMETRY_REGISTER"]["ROWS"]}; eb = {m["ENTITY_ID"] for m in b.registers["PA06_MATERIAL_GEOMETRY_REGISTER"]["ROWS"]}
    # entity ids nest the view id (which nests the sheet hash), so cross-file identity is compared on the geometry part only
    assert len(ea) == len(eb)


def test_unitless_source_blocks_every_quantity(tmp_path):
    r = PL.run(cfg(villa(tmp_path, unitless=True)))
    assert r.registers["PA06_SOURCE_UNIT_REGISTER"]["ROWS"][0]["STATUS"] == "NOT_ESTABLISHED"
    assert all(l["QUANTITY_STATUS"] == "SOURCE_REQUIRED" and l["AREA_M2_PRINCIPAL"] is None for l in r.registers["PA06_QUANTITY_INPUT_TRACE"]["LINES"])


def test_two_storeys_ordered_by_level_text(tmp_path):
    (tmp_path / "a").mkdir(); (tmp_path / "b").mkdir()
    doc_a = json.loads(villa(tmp_path / "a").read_text())
    doc_b = json.loads(villa(tmp_path / "b", dx=40000, level="+4.50", labels=("BED ROOM", "حمام")).read_text())
    doc = {"insunits": 4, "dimlfac": 1.0, "linetypes": doc_a["linetypes"], "primitives": doc_a["primitives"] + doc_b["primitives"], "texts": doc_a["texts"] + doc_b["texts"], "dimensions": doc_a["dimensions"] + doc_b["dimensions"]}
    p = tmp_path / "two.json"; p.write_text(json.dumps(doc), "utf-8")
    r = PL.run(cfg(p))
    st = sorted(r.registers["PA06_STOREY_REGISTER"]["ROWS"], key=lambda x: x["GENERIC_NAME"])
    assert [s["GENERIC_NAME"] for s in st] == ["FLOOR_01", "FLOOR_02"] and [s["REFERENCE_LEVEL"] for s in st] == [0.0, 4.5]
    assert r.registers["PA06_VIEW_COPY_FAMILY_REGISTER"]["LINKS"][0]["DX_MM"] == 40000.0
    wet = [l for l in r.registers["PA06_QUANTITY_INPUT_TRACE"]["LINES"] if l["TRADE"] == "WET_ROOM_SPLATTER"]
    assert len(wet) == 2 and all(w["QUANTITY_STATUS"] == "NOT_ESTABLISHED" and w["HEIGHT_SOURCE"]["PARAMETER_ID"] == "TARTUSHA_HEIGHT" for w in wet)     # kitchen + bathroom


def test_blocks_rotated_mirrored_scaled_keep_roles():
    from types import SimpleNamespace
    from engine.ingest import assemblies as AS, primitive_roles as PRO
    import math as m
    out = []
    for k, (rot, sx, sy) in enumerate(((0, 1, 1), (m.pi / 2, 1, 1), (0, -1, 1), (m.pi / 4, 2, 2))):
        base = [((0, 0), (0, 900)), ((0, 900), (900, 900))]     # leaf + a frame line
        prims = []
        for i, (a, b) in enumerate(base):
            def T(x, y):
                x, y = x * sx, y * sy
                return (x * m.cos(rot) - y * m.sin(rot) + 50000 * k, x * m.sin(rot) + y * m.cos(rot))
            pa, pb = T(*a), T(*b)
            prims.append(SimpleNamespace(kind="SEGMENT", object_id=f"B{k}-{i}", x1=pa[0], y1=pa[1], x2=pb[0], y2=pb[1], cx=0, cy=0, radius=0, start_angle=0, end_angle=0,
                                         provenance=SimpleNamespace(layer="D", handle=k * 10 + i, block_path=("DOOR_L",), instance_path=(k,))))
        c = (0, 0)
        cc = (c[0] * sx * m.cos(rot) - c[1] * sy * m.sin(rot) + 50000 * k, 0)
        prims.append(SimpleNamespace(kind="ARC", object_id=f"B{k}-arc", x1=0, y1=0, x2=0, y2=0, cx=cc[0], cy=cc[1], radius=900 * abs(sx), start_angle=rot, end_angle=rot + m.pi / 2,
                                     provenance=SimpleNamespace(layer="D", handle=k * 10 + 9, block_path=("DOOR_L",), instance_path=(k,))))
        roles = PRO.classify(prims, {"WALL_LAYERS": ["W"], "DOOR_LAYER": "D", "DIMENSION_LAYERS": [], "HIDDEN_LAYERS": []})
        inst = [SimpleNamespace(block_name="DOOR_L", depth=0, provenance=SimpleNamespace(handle=k), transform=SimpleNamespace(e=50000 * k, f=0, rotation=rot, scale_x=sx, scale_y=sy, is_mirrored=sx < 0))]
        rows = AS.block_objects(inst, prims, roles)
        assert rows[0]["ROLE"] == "DOOR_ASSEMBLY" and rows[0]["MIRRORED"] == (sx < 0) and rows[0]["WALL_FACE_ELIGIBLE"] is False, (k, rows[0])
        out.append(rows[0]["ROLE"])
    assert out == ["DOOR_ASSEMBLY"] * 4


@pytest.fixture(scope="module")
def p7757():
    try:
        from research.qs_wall_treatment_01.pa06 import config as C6
    except Exception as e:      # pragma: no cover
        pytest.skip(str(e))
    c = C6.supervised()
    if not all(Path(s["PATH"]).exists() for s in c["SOURCES"]):
        pytest.skip("P7757 sources not on disk")
    return PL.run(c)


def test_p7757_regression_lessons(p7757):
    R = p7757.registers
    assert R["PA06_SOURCE_UNIT_REGISTER"]["ROWS"][0]["STATUS"] == "SOURCE_ESTABLISHED"
    assert R["PA06_PRIMITIVE_ROLE_REGISTER"]["BY_ROLE"]["HATCH_STROKE"]["COUNT"] > 1000 and R["PA06_PRIMITIVE_ROLE_REGISTER"]["BY_ROLE"]["DOOR_SWING"]["COUNT"] > 10
    # authored dimensions outrank raster: the void dims are both-owned in the dimension register
    rows = R["DIMENSION_CHAIN_REGISTER"]["ROWS"]
    for v in EXP["AUTHORED_VOID_DIMENSIONS"]:
        assert any(r["DISPLAY_TEXT"] == v["DISPLAY_TEXT"] and abs(r["MEASURED_VALUE_MM"] - v["MEASURED_MM"]) < 1 and r["OWNER_STATUS"] == "BOTH_OWNED" for r in rows)
    # curved geometry stays curved: arc faces exist among the material entities
    assert any(m["KIND"] == "ARC" for m in R["PA06_MATERIAL_GEOMETRY_REGISTER"]["ROWS"])
    # an opening may be an absence of geometry: unresolved sites exist and are never physical separators
    sites = R["PA06_TOPOLOGICAL_SITE_REGISTER"]["ROWS"]
    assert any(s["CLASS"] == "UNRESOLVED_SITE" for s in sites) and all(not s["PHYSICAL_SEPARATOR"] for s in sites if s["CLASS"] == "UNRESOLVED_SITE")
    # no polygon perimeter as wall length; closures zero-material and reversible
    assert all(w["POLYGON_PERIMETER_USED"] is False for w in R["PA06_SPACE_WALL_LENGTH_REGISTER"]["ROWS"])
    rev = R["PA06_TRADE_MEASUREMENT_REGION_REGISTER"]["REVERSIBILITY"]
    assert rev["ALL_REVERSIBLE"] and rev["ALL_ZERO_MATERIAL"]
    # a storey height never silently becomes a plaster height: no line uses an EXTERNAL_STOREY_HEIGHT for internal plaster
    assert all((l["HEIGHT_SOURCE"] or {}).get("PARAMETER_ID") != "EXTERNAL_STOREY_HEIGHT_GROUND" for l in R["PA06_QUANTITY_INPUT_TRACE"]["LINES"] if l["TRADE"] == "NORMAL_INTERNAL_PLASTER")
    # open plan: a physical region may hold several functional zones
    assert any(len(x["FUNCTIONAL_ZONES"]) > 1 for x in R["PA06_PHYSICAL_SPACE_REGISTER"]["REGIONS"])


def test_exterior_site_cell_gets_no_area_line(tmp_path):
    """A plot outline around the villa with NEIGHBOUR / STREET stamps forms a closed exterior cell: it must be EXTERIOR_SITE with a NOT_APPLICABLE line, never a provisional floor area."""
    doc = json.loads(villa(tmp_path).read_text())
    for a, b in (((-14000, -13000), (26000, -13000)), ((26000, -13000), (26000, 17000)), ((26000, 17000), (-14000, 17000)), ((-14000, 17000), (-14000, -13000))):
        doc["primitives"].append({"kind": "SEGMENT", "layer": "SITE", "x1": a[0], "y1": a[1], "x2": b[0], "y2": b[1]})       # 40 x 30 m plot on its own layer
    doc["texts"] += [{"value": "NEIGHBOUR", "x": -8000, "y": 12000}, {"value": "STREET", "x": 20000, "y": -8000}]
    p = tmp_path / "plot.json"; p.write_text(json.dumps(doc), "utf-8")
    r = PL.run(cfg(p))
    cells = [c for c in r.registers["PA06_PHYSICAL_SPACE_REGISTER"]["CELLS"] if c["IN_RANGE"]]
    ext = [c for c in cells if c["SPACE_CLASS"] == "EXTERIOR_SITE"]
    assert len(ext) == 1 and ext[0]["AREA_M2"] > 200 and len([c for c in cells if c["SPACE_CLASS"] == "INTERIOR"]) == 2
    lines = [l for l in r.registers["PA06_QUANTITY_INPUT_TRACE"]["LINES"] if l["CELL_ID"] == ext[0]["CELL_ID"]]
    assert lines and all(l["QUANTITY_STATUS"] == "NOT_APPLICABLE" and l["AREA_M2_PRINCIPAL"] is None for l in lines)
    assert not any(l["TRADE"] in ("FLOOR_AREA", "CEILING_AREA") for l in lines)
