"""T-455 (owner directive 2026-11-02 B3): tile adhesive bags by tile size (UPC-ADHESIVE-001) rounded once at the
purchasing group, and tile boxes per tile product rounded at PROJECT level + one spare box. FINISH_MATERIALS_TABLE_V4.
Synthetic hand cases only (no project; packaging figures are fixture data, not supplier values).

Hand fixture (joint 1 mm inside, owner Q-42; layouts by TILE_COUNT_V1, checked by hand below):
    R1 2.00 x 1.50 m, 60 x 60: x 3 x 0.601 = 1.803 + cut 0.197; y 2 x 0.601 = 1.202 + cut 0.298 -> 4 x 3 = 12 positions,
       6 whole + 6 cut: 12 tiles without reuse; with in-room offcut reuse (usable side 0.20 m): the three 0.6 x 0.298
       strips come from 2 tiles, the two 0.197 x 0.6 strips and the 0.197 x 0.298 corner from 1 tile -> 6 + 3 = 9
    R2 L-shape 2.40 x 2.40 less a 1.20 x 1.20 corner = 4.32 m2, 60 x 60: 8 cells in the 2.40 x 1.20 arm + 4 in the
       1.20 x 1.20 arm = 12 (cuts 0.597 / 0.599 leave 1 - 3 mm: nothing reusable) -> 12 / 12
    R3 2.50 x 2.00 m, 60 x 60 -> 20 / 15 (layout record)
    product P-A (60 x 60, fixture 4 pieces per box): tiles 44 conservative, 36 optimised
        conservative: project ceil(44 / 4) = 11 + 1 spare = 12; per room 3 + 3 + 5 = 11 + 1 = 12 (no saving)
        optimised:    project ceil(36 / 4) = 9 + 1 = 10;      per room 3 + 3 + 4 = 10 + 1 = 11 (saving 1 box)
    wet wall WW-1 (t457 bath): net 20.16 m2 in 120 x 60
    adhesive, one group: 3.00 / 5 + 4.32 / 5 + 5.00 / 5 + 20.16 / 3 = 0.6 + 0.864 + 1.0 + 6.72 = 9.184 -> 10 bags
        V3 (any size 5 m2): 32.48 / 5 = 6.496 bags (the 120 x 60 wall understated by 2.688 bags)
"""

import random
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import finish_materials_table as V1        # noqa: E402
from engine.source import finish_materials_table_v3 as V3     # noqa: E402
from engine.source import finish_materials_table_v4 as V4     # noqa: E402
from engine.source import tile_count as TC                    # noqa: E402

SRC = "fixture: printed on the synthetic finishes schedule"
PACK = {"P-A": {"pieces_per_box": 4, "source": "fixture product sheet (synthetic)"},
        "P-B": {"pieces_per_box": 2, "source": "fixture product sheet (synthetic)"}}
R1 = [(0, 0), (2.0, 0), (2.0, 1.5), (0, 1.5)]
R2 = [(0, 0), (2.4, 0), (2.4, 1.2), (1.2, 1.2), (1.2, 2.4), (0, 2.4)]
R3 = [(0, 0), (2.5, 0), (2.5, 2.0), (0, 2.0)]


def counts(poly, l=0.6, w=0.6, units="m"):
    size = TC.resolve_size(owner={"length_m": l, "width_m": w, "source": SRC})[0]
    c = TC.count_room({"polygon": poly}, units=units, size=size, exposure="INSIDE", offcut_reuse=False)
    o = TC.count_room({"polygon": poly}, units=units, size=size, exposure="INSIDE", offcut_reuse=0.2)
    return V4.tiles_from_counts(c, o)


def floor(i, poly, **kw):
    e = {"id": i, "floor": "GF", "kind": V1.DRY_FLOOR, "polygon": poly, "tile_cm": "60x60", "tile_size_source": SRC,
         "tile_product": "P-A", "evidence_status": "DRAWING-CONFIRMED"}
    if "tiles" not in kw:
        e["tiles"] = counts(poly)
    e.update(kw)
    return e


def bath(u=1.0, **kw):
    s = 1.0 / u
    e = {"id": "WW-1", "floor": "GF", "kind": V1.WET_WALL, "wall_length": 8.40 * s, "door_widths": [0.80 * s],
         "height": 2.70 * s, "openings": [{"id": "W-1", "width": 0.60 * s, "height": 0.60 * s}], "unit_m": u,
         "tile_cm": (60, 120), "tile_size_source": SRC, "tile_product": "P-B", "evidence_status": "DRAWING-CONFIRMED"}
    e.update(kw)
    return e


def fixture():
    return [floor("R1", R1), floor("R2", R2), floor("R3", R3), bath()]


def test_layout_counts_match_the_hand_count():
    assert (counts(R1)["conservative"], counts(R1)["optimised"]) == (12, 9)
    assert (counts(R2)["conservative"], counts(R2)["optimised"]) == (12, 12)
    assert (counts(R3)["conservative"], counts(R3)["optimised"]) == (20, 15)


def test_adhesive_by_tile_size_rounded_once_at_the_purchasing_group():
    t = V4.table(fixture(), packaging=PACK)
    by = {r["id"]: r for r in t["rows"]}
    assert by["R1"]["adhesive_bags"] == pytest.approx(0.6)
    assert by["R2"]["adhesive_bags"] == pytest.approx(0.864)
    assert by["R3"]["adhesive_bags"] == pytest.approx(1.0)
    assert by["WW-1"]["adhesive_bags"] == pytest.approx(6.72)
    assert by["WW-1"]["adhesive_coverage_m2_per_bag"] == 3.0 and by["WW-1"]["tile_cm"] == "120x60"
    assert by["WW-1"]["adhesive_v3_flat_bags"] == pytest.approx(4.032)
    op = [o for o in by["WW-1"]["operations"] if o["op"] == "ADHESIVE_AND_PORCELAIN"][0]
    assert op["adhesive_bags"] == pytest.approx(6.72)
    g = t["purchase"]["adhesive"]["PROJECT"]
    assert g["status"] == V4.OK and g["bags_net"] == pytest.approx(9.184) and g["bags_to_buy"] == 10
    assert g["evidence_status"] == "DRAWING-CONFIRMED"
    for s in list(t["per_floor"].values()) + list(t["per_kind"].values()) + [t["project"]]:
        assert s["adhesive_bags_to_buy"] is None     # never rounded below the purchasing group


def test_boxes_at_project_level_per_tile_product_with_one_spare():
    p = V4.table(fixture(), packaging=PACK)["purchase"]["tiles"]["products"]["P-A"]
    assert p["status"] == V4.OK and p["tile_cm"] == "60x60" and p["area_m2"] == pytest.approx(12.32)
    c, o = p["conservative"], p["optimised"]
    assert (c["tiles"], c["boxes_net"], c["spare_boxes"], c["boxes_to_buy"], c["per_room_rounded_boxes"]) == \
        (44, 11, 1, 12, 12)
    assert (o["tiles"], o["boxes_net"], o["boxes_to_buy"], o["per_room_rounded_boxes"], o["saving_vs_per_room_boxes"]) \
        == (36, 9, 10, 11, 1)
    assert c["packaging_surplus_tiles"] == 0 and o["packaging_surplus_tiles"] == 0
    assert p["tiles_net_lower_bound"] == 35       # ceil(12.32 / 0.36) = 35: a bound, never the count


def test_project_rounding_never_exceeds_per_room_rounding():
    rnd = random.Random(455)
    for _ in range(300):
        cnt = [rnd.randint(0, 60) for _ in range(rnd.randint(1, 12))]
        b = V4._boxes(cnt, rnd.randint(1, 12))
        assert b["boxes_net"] <= b["per_room_rounded_boxes"] - 1


def test_no_tile_size_holds_adhesive_with_the_owner_rule_bound_never_the_60x60_rate():
    e = floor("R1", R1, tile_cm=None, tile_size_source=None, tile_product=None, tiles=None)
    t = V4.table([e, floor("R3", R3)], packaging=PACK)
    r = t["rows"][0]
    assert r["adhesive_bags"] is None and r["adhesive_status"] == V4.HELD
    assert "TILE_SIZE_NOT_GIVEN" in r["adhesive_reason"]
    assert r["adhesive_bound_bags"]["low"] == pytest.approx(0.6) and r["adhesive_bound_bags"]["high"] == pytest.approx(1.0)
    assert r["adhesive_v3_flat_bags"] == pytest.approx(0.6)      # V3 still printed it as a quantity
    g = t["purchase"]["adhesive"]["PROJECT"]
    assert g["status"] == V4.HELD and g["bags_to_buy"] is None and g["held_rows"] == ["R1"]
    assert g["bound_bags_to_buy"] == {"low": 2, "high": 2, "basis": g["bound_bags_to_buy"]["basis"]}
    assert t["purchase"]["tiles"]["product_not_named"] == ["R1"]


def test_a_size_with_no_source_or_a_bad_size_is_refused():
    with pytest.raises(ValueError, match="needs its source"):
        V4.table([floor("R1", R1, tile_size_source="")])
    with pytest.raises(ValueError, match="L x W"):
        V4.table([floor("R1", R1, tile_cm="sixty")])


def test_a_size_not_in_the_owner_table_is_held_unless_the_project_classifies_it_normal():
    t = V4.table([floor("R1", R1, tile_cm="30x30", tile_product="P-C", tiles=None)])
    assert t["rows"][0]["adhesive_bags"] is None and "not in the OWNER CONFIRMED table" in t["rows"][0]["adhesive_reason"]
    proj = {"UPC-ADHESIVE-001": {"normal_class_sizes": {"30x30": "owner project decision (synthetic)"}}}
    t2 = V4.table([floor("R1", R1, tile_cm="30x30", tile_product="P-C", tiles=None)], project=proj)
    assert t2["rows"][0]["adhesive_bags"] == pytest.approx(0.6)


def test_missing_packaging_or_layout_count_holds_boxes_never_m2_over_face():
    t = V4.table(fixture(), packaging={"P-A": PACK["P-A"]})
    b = t["purchase"]["tiles"]["products"]["P-B"]
    assert b["status"] == V4.HELD and b["conservative"] is None
    assert "LAYOUT_COUNT_NOT_GIVEN" in b["why"] and "PACKAGING_NOT_ESTABLISHED" in b["why"]
    assert b["tiles_net_lower_bound"] == 28        # ceil(20.16 / 0.72): shown as a bound only
    t2 = V4.table(fixture(), packaging=None)
    a = t2["purchase"]["tiles"]["products"]["P-A"]
    assert a["status"] == V4.HELD and a["tiles_conservative"] == 44 and a["conservative"] is None
    with pytest.raises(ValueError, match="no source"):
        V4.table(fixture(), packaging={"P-A": {"pieces_per_box": 4, "source": ""}})
    with pytest.raises(ValueError, match="whole number"):
        V4.table(fixture(), packaging={"P-A": {"pieces_per_box": 4.5, "source": "x"}})


def test_held_area_is_never_zero_and_holds_its_groups():
    e = floor("R9", None, polygon=None, area_status="HELD", area_reason="OUTLINE_NOT_CLOSED", tiles=None)
    t = V4.table([e, floor("R1", R1)], packaging=PACK)
    r = t["rows"][0]
    assert r["area_m2"] is None and r["adhesive_bags"] is None and r["evidence_status"] == "HELD"
    assert t["purchase"]["adhesive"]["PROJECT"]["bags_to_buy"] is None
    assert t["purchase"]["adhesive"]["PROJECT"]["bound_bags_to_buy"] is None   # no bound for an unknown area
    p = t["purchase"]["tiles"]["products"]["P-A"]
    assert p["status"] == V4.HELD and p["area_not_in_sum"] == ["R9"]


def test_stone_rows_hold_adhesive_and_boxes():
    st = {"id": "S1", "floor": "GF", "kind": V1.STAIR_LANDING, "length": 1.2, "width": 1.0}
    t = V4.table([st, floor("R1", R1)], packaging=PACK)
    assert t["rows"][0]["adhesive_bags"] is None and "Q-45" in t["rows"][0]["adhesive_reason"]
    assert t["purchase"]["tiles"]["stone_rows"] == ["S1"]
    assert t["purchase"]["adhesive"]["PROJECT"]["status"] == V4.HELD


def test_separate_adhesive_groups_are_rounded_separately():
    fx = fixture()
    fx[3]["adhesive_group"] = "C2TE large format"
    g = V4.table(fx, packaging=PACK)["purchase"]["adhesive"]
    assert g["PROJECT"]["bags_to_buy"] == 3 and g["C2TE large format"]["bags_to_buy"] == 7


def test_millimetre_units_mirror_and_rotation_give_the_same_purchase():
    base = V4.table(fixture(), packaging=PACK)["purchase"]
    mm = [floor("R1", [(x * 1000, y * 1000) for x, y in R1], unit_m=0.001,
                tiles=counts([(x * 1000, y * 1000) for x, y in R1], units="mm")),
          floor("R2", [(-x, y) for x, y in R2], tiles=counts([(-x, y) for x, y in R2])),
          floor("R3", [(-y, x) for x, y in R3], tiles=counts([(-y, x) for x, y in R3])),
          bath(u=0.001)]
    alt = V4.table(mm, packaging=PACK)["purchase"]
    assert alt["adhesive"]["PROJECT"]["bags_to_buy"] == base["adhesive"]["PROJECT"]["bags_to_buy"]
    assert alt["adhesive"]["PROJECT"]["bags_net"] == pytest.approx(base["adhesive"]["PROJECT"]["bags_net"])
    for k in ("conservative", "optimised"):
        assert alt["tiles"]["products"]["P-A"][k] == base["tiles"]["products"]["P-A"][k]


def test_bad_counts_are_refused():
    with pytest.raises(ValueError, match="exceeds"):
        V4.table([floor("R1", R1, tiles={"conservative": 9, "optimised": 12, "source": "x"})])
    with pytest.raises(ValueError, match="needs its source"):
        V4.table([floor("R1", R1, tiles={"conservative": 9})])
    with pytest.raises(ValueError, match="whole count"):
        V4.table([floor("R1", R1, tiles={"conservative": 9.5, "source": "x"})])
    with pytest.raises(ValueError, match="evidence_status"):
        V4.table([floor("R1", R1, evidence_status="PROBABLY")])


def test_product_with_two_sizes_is_a_conflict():
    fx = fixture()
    fx[3]["tile_product"] = "P-A"
    p = V4.table(fx, packaging=PACK)["purchase"]["tiles"]["products"]["P-A"]
    assert p["status"] == V4.HELD and "SIZE_CONFLICT" in p["why"]


@pytest.mark.parametrize("e", fixture())
def test_beds_render_and_area_are_v3_byte_identical(e):
    new = V4.row(e)
    old = V3.row({k: v for k, v in e.items()})
    extra = set(new) - set(old)
    assert extra <= {"adhesive_v3_flat_bags", "tile_cm", "tile_size_source", "adhesive_coverage_m2_per_bag",
                     "adhesive_basis", "adhesive_bound_bags", "adhesive_group", "adhesive_rule", "tile_product",
                     "tiles_conservative", "tiles_optimised", "tiles_source", "tiles_net_lower_bound", "tiles_reason",
                     "evidence_status"}
    for k in old:
        if k in V4.ADH_KEYS or k == "operations":
            continue
        assert new[k] == old[k], k
    assert new["adhesive_v3_flat_bags"] == old["adhesive_bags"]


def test_v3_module_unchanged_and_v4_is_unwired():
    assert V4.SUPERSEDES == "FINISH_MATERIALS_TABLE_V3" and V4.DEFAULT_GUARD_CLASS == "UNWIRED_PRODUCER"
    src = (ROOT / "engine" / "source").glob("arch_v30*.py")
    assert not any("finish_materials_table_v4" in p.read_text(encoding="utf-8") for p in src)


def test_purchase_from_measured_lines_normal_and_adverse():
    lines = [{"id": "L1", "kind": V4.DRY_FLOOR, "area_m2": 12.0, "tile_cm": "160x80", "tile_size_source": SRC},
             {"id": "L2", "kind": V4.WET_WALL, "area_m2": 9.0, "tile_cm": "120x60", "tile_size_source": SRC},
             {"id": "L3", "kind": V4.WET_FLOOR, "area_m2": 2.5, "tile_cm": "60x60", "tile_size_source": SRC}]
    g = V4.purchase_from_lines(lines)["adhesive"]["PROJECT"]
    assert g["bags_net"] == pytest.approx(4.0 + 3.0 + 0.5) and g["bags_to_buy"] == 8
    assert g["evidence_status"] == "UNKNOWN"                       # no evidence given: never upgraded by the rate
    held = lines + [{"id": "L4", "kind": V4.DRY_FLOOR, "area_m2": None, "area_reason": "HELD by source"}]
    h = V4.purchase_from_lines(held)
    assert h["adhesive"]["PROJECT"]["bags_to_buy"] is None and h["rows"][3]["adhesive_bags"] is None
    nosize = [{"id": "L5", "kind": V4.DRY_FLOOR, "area_m2": 15.0}]
    n = V4.purchase_from_lines(nosize)
    assert n["rows"][0]["adhesive_v3_flat_bags"] == pytest.approx(3.0)      # V1 .. V3 printed 3 bags at any size
    assert n["adhesive"]["PROJECT"]["bound_bags_to_buy"]["low"] == 3
    assert n["adhesive"]["PROJECT"]["bound_bags_to_buy"]["high"] == 5
    with pytest.raises(ValueError, match="duplicate"):
        V4.purchase_from_lines(lines + lines[:1])
    with pytest.raises(ValueError, match="kind"):
        V4.purchase_from_lines([{"id": "X", "kind": "WALLPAPER", "area_m2": 1.0}])
    with pytest.raises(ValueError, match="finite"):
        V4.purchase_from_lines([{"id": "X", "kind": V4.DRY_FLOOR, "area_m2": -1.0}])
