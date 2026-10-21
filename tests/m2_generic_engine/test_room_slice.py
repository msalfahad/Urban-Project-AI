"""M2 architectural vertical slice: rooms, floor area, perimeter, skirting and wet-room waterproofing on a SYNTHETIC
plan whose truth is written by hand below (rectangles: area = w x h, perimeter = 2 (w + h)). Rule ids are the Urban
Projects library's (data/trade_rules/URBAN_PROJECTS_RULE_LIBRARY.json)."""

from __future__ import annotations

import pytest

ezdxf = pytest.importorskip("ezdxf")

from engine.source import room_slice as RS                   # noqa: E402
from tools import urban_intake as UI                         # noqa: E402

# inner faces (mm): LIVING 0-6000 x 0-5000, BEDROOM 6200-10200 x 0-5000, BATH 10400-12400 x 0-2500,
# STORE 10400-12400 x 2700-5000; walls 200 thick; doors LIVING|BEDROOM y 1000-1900 (0.9), BEDROOM|BATH y 500-1300 (0.8)
TRUTH = {"LIVING": (30.0, 22.0, 0.9), "BEDROOM": (20.0, 18.0, 1.7), "BATHROOM": (5.0, 9.0, 0.8),
         "STORE": (4.6, 8.6, 0.0)}


def _plan(path):
    doc = ezdxf.new("R2018")
    doc.header["$INSUNITS"] = 4
    m = doc.modelspace()

    def W(a, b):
        m.add_line(a, b, dxfattribs={"layer": "A-WALL"})

    def D(a, b):
        m.add_line(a, b, dxfattribs={"layer": "A-DOOR"})
    m.add_lwpolyline([(-200, -200), (12600, -200), (12600, 5200), (-200, 5200)], close=True,
                     dxfattribs={"layer": "A-WALL"})
    # LIVING
    W((0, 0), (6000, 0)); W((6000, 0), (6000, 1000)); W((6000, 1900), (6000, 5000)); W((6000, 5000), (0, 5000))
    W((0, 5000), (0, 0))
    # BEDROOM
    W((6200, 0), (10200, 0)); W((10200, 0), (10200, 500)); W((10200, 1300), (10200, 5000))
    W((10200, 5000), (6200, 5000)); W((6200, 5000), (6200, 1900)); W((6200, 1000), (6200, 0))
    # BATH and STORE
    W((10400, 0), (12400, 0)); W((12400, 0), (12400, 2500)); W((12400, 2500), (10400, 2500))
    W((10400, 2500), (10400, 1300)); W((10400, 500), (10400, 0))
    m.add_lwpolyline([(10400, 2700), (12400, 2700), (12400, 5000), (10400, 5000)], close=True,
                     dxfattribs={"layer": "A-WALL"})
    # jambs (wall layer), thresholds (door layer), leaves and swings (door layer)
    for y in (1000, 1900):
        W((6000, y), (6200, y))
    for y in (500, 1300):
        W((10200, y), (10400, y))
    D((6000, 1000), (6000, 1900)); D((6200, 1000), (6200, 1900))
    D((10200, 500), (10200, 1300)); D((10400, 500), (10400, 1300))
    D((6200, 1000), (7100, 1000)); m.add_arc((6200, 1000), 900, 0, 90, dxfattribs={"layer": "A-DOOR"})
    D((10400, 500), (11200, 500)); m.add_arc((10400, 500), 800, 0, 90, dxfattribs={"layer": "A-DOOR"})
    for txt, x, y in (("LIVING", 2500, 2500), ("غرفة نوم", 8000, 3000),
                      ("BATH", 11200, 1800), ("STORE", 11200, 3800)):
        m.add_text(txt, dxfattribs={"layer": "A-TEXT", "height": 200}).set_placement((x, y))
    doc.saveas(path)
    return path


@pytest.fixture(scope="module")
def plan(tmp_path_factory):
    p = _plan(tmp_path_factory.mktemp("arch") / "plan.dxf")
    I = UI.read(p)
    return {"segments": I["segments"], "arcs": I["arcs"], "texts": I["texts"]}


def test_rooms_area_perimeter_and_skirting(plan):
    R = RS.rooms(plan, {"A-WALL"}, {"A-DOOR"}, 0.001)
    got = {r["name"]: r for r in R["rooms"]}
    assert set(got) == set(TRUTH)                          # the Arabic label reads as BEDROOM; output is English
    for name, (area, per, doors) in TRUTH.items():
        r = got[name]
        assert r["floor_m2"] == pytest.approx(area, abs=1e-9), name
        assert r["perimeter_lm"] == pytest.approx(per, abs=1e-9), name
        assert r["door_widths_lm"] == pytest.approx(doors, abs=1e-9), name
        if not r["wet"]:
            assert r["skirting_lm"] == pytest.approx(per - doors, abs=1e-9), name          # UP-CER-003
    assert sorted(R["swing_widths_m"]) == [0.8, 0.9]
    assert not R["coverage_risk"]
    assert sum(1 for f in R["faces"] if f["class"] == "DOORWAY") == 2


def test_wet_room_rules(plan):
    R = RS.rooms(plan, {"A-WALL"}, {"A-DOOR"}, 0.001)
    b = next(r for r in R["rooms"] if r["name"] == "BATHROOM")
    assert b["wet"] and b["skirting_lm"] is None and b["skirting_state"] == "UNRESOLVED_WALL_TILE_HEIGHT"
    assert b["skirting_alternatives"]["PARTIAL_TILE"] == pytest.approx(9.0 - 0.8)
    assert b["wp_floor_m2"] == pytest.approx(5.0 + 0.2 * 0.8, abs=1e-9)                     # UP-WP-003 doorway piece
    assert b["wp_upturn_m2"] == pytest.approx((9.0 - 0.8) * 0.15, abs=1e-9)                 # UP-WP-002
    R2 = RS.rooms(plan, {"A-WALL"}, {"A-DOOR"}, 0.001, wall_tile_full_height=True)
    b2 = next(r for r in R2["rooms"] if r["name"] == "BATHROOM")
    assert b2["skirting_lm"] == 0.0 and "UP-CER-004" in b2["rules"]


def test_unlabelled_space_is_a_coverage_risk(plan):
    texts = [t for t in plan["texts"] if t["value"] != "STORE"]
    R = RS.rooms(dict(plan, texts=texts), {"A-WALL"}, {"A-DOOR"}, 0.001)
    assert [x["KIND"] for x in R["coverage_risk"]] == ["ROOM_UNLABELLED"]
    assert R["coverage_risk"][0]["area_m2"] == pytest.approx(4.6, abs=1e-9)
