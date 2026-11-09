"""T-521 (D-T518-1): FINISH_MATERIALS_TABLE_V6, rule R-T521-1 'tile-bed / screed mortar INSTALLED = area x bed, no loss;
the named loss and the procurement each their own field; cement bags rounded once per purchasing group'.

Synthetic hand fixture (NOT the training villa; sizes are fixture data printed on a synthetic finishes schedule):

    D1 dry floor (majlis)  5.00 x 4.00 = 20.00 m2, bed 0.03 .. 0.04 (Q-45 floors), 1:4
        installed   20 x 0.03 = 0.600   .. 20 x 0.04 = 0.800 m3
        loss 5 %    0.030 .. 0.040 m3          procurement 0.630 .. 0.840 m3
        cement x 8  installed 4.800 .. 6.400   procurement 5.040 .. 6.720 bags
        sand x 1.1  installed 0.660 .. 0.880   procurement 0.693 .. 0.924 m3
    B1 bathroom floor      2.40 x 1.80 = 4.32 m2, bed 0.04 .. 0.06 (Q-45 bathrooms), 1:4
        installed   0.1728 .. 0.2592 m3        procurement 0.18144 .. 0.27216 m3
        cement      installed 1.3824 .. 2.0736 procurement 1.45152 .. 2.17728 bags
        sand        installed 0.19008 .. 0.28512 procurement 0.199584 .. 0.299376 m3
    W1 bathroom wet wall   (2 x (2.40 + 1.80) - door 0.80) x 2.70 - window 0.60 x 0.60 = 20.52 - 0.36 = 20.16 m2
        no fixing bed (owner 2026-11-02: render + adhesive); adhesive 60 x 60: 20.16 / 5 = 4.032 bags
    group PROJECT  installed 0.7728 .. 1.0592 m3; procurement 0.81144 .. 1.11216 m3;
                   cement procurement 6.49152 .. 8.89728 -> buy 7 .. 9 bags (ONCE); installed 6.1824 .. 8.4736

Adverse: loss with no source / no loss / invalid loss -> procurement HELD, installed still produced; a held area -> bed
HELD (None, never 0) and the group's whole bags HELD; a 1:3 stair bed -> cement HELD, group bags HELD; millimetre,
rotated and mirrored outline -> the same area; two disagreeing waste sources refused; two purchasing groups -> one ceil
each; V5 reproduced as procurement and installed = V5 / 1.05 on every bedded row, every other key byte-identical.
"""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import finish_materials_table_v5 as V5     # noqa: E402
from engine.source import finish_materials_table_v6 as V6     # noqa: E402

SRC = "fixture: printed on the synthetic finishes schedule"
EV = "DRAWING-CONFIRMED"


def d1(**kw):
    e = {"id": "D1", "floor": "GF", "kind": V6.DRY_FLOOR, "length": 5.0, "width": 4.0, "tile_cm": "60x60",
         "tile_size_source": SRC, "evidence_status": EV}
    e.update(kw)
    return e


def b1(**kw):
    e = {"id": "B1", "floor": "GF", "kind": V6.WET_FLOOR, "length": 2.4, "width": 1.8, "tile_cm": "60x60",
         "tile_size_source": SRC, "evidence_status": EV}
    e.update(kw)
    return e


def w1(**kw):
    e = {"id": "W1", "floor": "GF", "kind": V6.WET_WALL, "wall_length": 2 * (2.4 + 1.8), "door_widths": [0.8],
         "height": 2.7, "openings": [{"id": "WN1", "width": 0.6, "height": 0.6}], "tile_cm": "60x60",
         "tile_size_source": SRC, "evidence_status": EV}
    e.update(kw)
    return e


NORMAL = [d1(), b1(), w1()]
A = pytest.approx


def _j(x):
    return json.dumps(x, sort_keys=True, default=str)


def _row(t, i):
    return next(r for r in t["rows"] if r["id"] == i)


# ---- normal: hand figures -----------------------------------------------------------------------------------------

def test_dry_floor_installed_loss_procurement_by_hand():
    r = _row(V6.table(NORMAL), "D1")
    assert r["area_m2"] == A(20.0) and r["mortar_stage"] == "INSTALLED"
    assert (r["mortar_m3_low"], r["mortar_m3_high"]) == (A(0.6), A(0.8))
    assert (r["bed_loss_m3_low"], r["bed_loss_m3_high"]) == (A(0.03), A(0.04))
    assert (r["bed_procurement_m3_low"], r["bed_procurement_m3_high"]) == (A(0.63), A(0.84))
    assert (r["cement_bags_low"], r["cement_bags_high"]) == (A(4.8), A(6.4))
    assert (r["cement_bags_procurement_low"], r["cement_bags_procurement_high"]) == (A(5.04), A(6.72))
    assert (r["sand_m3_low"], r["sand_m3_high"]) == (A(0.66), A(0.88))
    assert (r["sand_m3_procurement_low"], r["sand_m3_procurement_high"]) == (A(0.693), A(0.924))
    assert r["bed_loss"]["value"] == 0.05 and "Q-45" in r["bed_loss"]["source"]
    assert r["bed_loss"]["status"] == "ASSUMED — OWNER-APPROVED"
    assert r["bed_procurement_status"] == "PROVISIONAL" and r["bed_procurement_reason"] is None


def test_bathroom_floor_by_hand():
    r = _row(V6.table(NORMAL), "B1")
    assert r["area_m2"] == A(4.32)
    assert (r["mortar_m3_low"], r["mortar_m3_high"]) == (A(0.1728), A(0.2592))
    assert (r["bed_procurement_m3_low"], r["bed_procurement_m3_high"]) == (A(0.18144), A(0.27216))
    assert (r["cement_bags_low"], r["cement_bags_high"]) == (A(1.3824), A(2.0736))
    assert (r["cement_bags_procurement_low"], r["cement_bags_procurement_high"]) == (A(1.45152), A(2.17728))
    assert (r["sand_m3_procurement_low"], r["sand_m3_procurement_high"]) == (A(0.199584), A(0.299376))


def test_wet_wall_no_bed_no_loss_adhesive_only():
    r = _row(V6.table(NORMAL), "W1")
    assert r["area_m2"] == A(20.16)
    assert r["mortar_status"] == "NOT_APPLICABLE" and r["mortar_stage"] == "NOT_APPLICABLE"
    assert r["bed_procurement_status"] == "NOT_APPLICABLE" and r["bed_loss"] is None
    assert all(r[k] is None for k in V6.INSTALLED_KEYS + V6.PROC_KEYS)
    assert r["adhesive_bags"] == A(4.032) and r["fixing_material"] == "ADHESIVE"
    assert [o["op"] for o in r["operations"]] == ["SPATTER_DASH", "LEVELLING_RENDER", "ADHESIVE_AND_PORCELAIN"]


def test_second_fixing_bed_on_wet_wall_still_refused():
    with pytest.raises(ValueError, match="SECOND_FIXING_BED"):
        V6.table([w1(fixing_bed_m=0.02)])


def test_purchase_group_ceil_once_from_procurement():
    t = V6.table(NORMAL)
    g = t["purchase"]["bed_mortar"]["PROJECT"]
    assert g["row_ids"] == ["D1", "B1"]                                     # the wet wall is not a bedded row
    s = g["subtotals"]
    assert s["mortar_m3_low"]["value"] == A(0.7728) and s["mortar_m3_high"]["value"] == A(1.0592)
    assert s["bed_procurement_m3_low"]["value"] == A(0.81144) and s["bed_procurement_m3_high"]["value"] == A(1.11216)
    assert s["cement_bags_low"]["value"] == A(6.1824)
    assert s["cement_bags_procurement_low"]["value"] == A(6.49152)
    assert s["cement_bags_procurement_high"]["value"] == A(8.89728)
    assert (g["cement_bags_to_buy_low"], g["cement_bags_to_buy_high"]) == (7, 9)
    assert s["sand_m3_procurement_high"]["value"] == A(1.223376) and g["sand"].startswith("SAND_PACK_NOT_ESTABLISHED")
    # no whole bags below the purchasing group
    for scope in [t["project"]] + list(t["per_floor"].values()) + list(t["per_kind"].values()):
        assert scope["cement_bags_to_buy_low"] is None and scope["cement_bags_to_buy_high"] is None
    assert t["project"]["mortar_m3_low"] == A(0.7728)                        # installed sum
    assert t["project"]["bed_procurement"]["bed_procurement_m3_low"]["value"] == A(0.81144)


def test_two_purchasing_groups_one_ceil_each():
    t = V6.table([d1(mortar_group="VILLA_A"), b1(mortar_group="VILLA_B")])
    p = t["purchase"]["bed_mortar"]
    assert p["VILLA_A"]["cement_bags_to_buy_low"] == 6 and p["VILLA_A"]["cement_bags_to_buy_high"] == 7  # 5.04, 6.72
    assert p["VILLA_B"]["cement_bags_to_buy_low"] == 2 and p["VILLA_B"]["cement_bags_to_buy_high"] == 3  # 1.45, 2.18


# ---- the V5 -> V6 diff -----------------------------------------------------------------------------------------------

def test_v5_reproduced_as_procurement_installed_drops_by_1_05():
    t5, t6 = V5.table(NORMAL), V6.table(NORMAL)
    for a, b in zip(t5["rows"], t6["rows"]):
        for k in V6.INSTALLED_KEYS:
            if a[k] is None:
                assert b[k] is None
                continue
            lh = k.rsplit("_", 1)[1]
            proc = {"mortar_m3": "bed_procurement_m3_", "cement_bags": "cement_bags_procurement_",
                    "sand_m3": "sand_m3_procurement_"}[k.rsplit("_", 1)[0]] + lh
            assert b[proc] == a[k]                                           # byte-identical to V5
            assert b[k] == A(a[k] / 1.05, abs=1e-6)
        for k in a:
            if k not in V6.INSTALLED_KEYS:
                assert _j(a[k]) == _j(b[k]), k                               # nothing else moves
    assert _j(t5["purchase"]["adhesive"]) == _j(t6["purchase"]["adhesive"])
    assert _j(t5["purchase"]["tiles"]) == _j(t6["purchase"]["tiles"])
    # V5's project whole bags (from the 5 % mortar) == V6's group whole bags (from procurement)
    g = t6["purchase"]["bed_mortar"]["PROJECT"]
    assert (t5["project"]["cement_bags_to_buy_low"], t5["project"]["cement_bags_to_buy_high"]) == \
        (g["cement_bags_to_buy_low"], g["cement_bags_to_buy_high"])


def test_diff_table():
    d = {x["id"]: x for x in V6.diff_v5(NORMAL)}
    assert d["D1"]["other_keys_moved"] == [] and d["W1"]["other_keys_moved"] == []
    for k, v in d["D1"]["keys"].items():
        assert v["ratio_v6_v5"] == A(1 / 1.05, abs=1e-6) and v["v6_procurement"] == v["v5"]
    assert all(v["ratio_v6_v5"] is None and v["v5"] is None for v in d["W1"]["keys"].values())


# ---- adverse ---------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("loss,why", [
    ({"value": 0.05, "source": "", "status": None}, "LOSS_SOURCE_NOT_GIVEN"),
    (None, "LOSS_NOT_GIVEN"),
    ({"value": 1.5, "source": "x"}, "LOSS_INVALID"),
    ({"value": True, "source": "x"}, "LOSS_INVALID"),
])
def test_no_sourced_loss_procurement_held_installed_produced(loss, why):
    t = V6.table(NORMAL, loss=loss)
    r = _row(t, "D1")
    assert r["mortar_m3_low"] == A(0.6) and r["cement_bags_high"] == A(6.4)        # installed still produced
    assert r["bed_procurement_status"] == "HELD" and r["bed_procurement_reason"].startswith(why)
    assert all(r[k] is None for k in V6.PROC_KEYS)
    g = t["purchase"]["bed_mortar"]["PROJECT"]
    assert g["cement_bags_to_buy_low"] is None and g["cement_bags_to_buy_low_status"] == "HELD"
    assert g["subtotals"]["cement_bags_procurement_low"]["at_least"] is None        # no known part: never 0.0
    assert g["subtotals"]["mortar_m3_low"]["value"] == A(0.7728)


def test_held_area_never_zero_and_blocks_group_bags():
    f4 = {"id": "F4", "floor": "1F", "kind": V6.DRY_FLOOR, "area_status": "HELD", "area_reason": "AREA_HELD_BY_SOURCE"}
    t = V6.table(NORMAL + [f4])
    r = _row(t, "F4")
    assert r["mortar_m3_low"] is None and r["bed_procurement_m3_low"] is None and r["bed_procurement_status"] == "HELD"
    g = t["purchase"]["bed_mortar"]["PROJECT"]
    s = g["subtotals"]["cement_bags_procurement_low"]
    assert s["status"] == "HELD" and s["at_least"] == A(6.49152) and s["held_rows"] == ["F4"]
    assert g["cement_bags_to_buy_low"] is None and "F4" in g["cement_bags_to_buy_low_reason"]
    assert g["evidence_status"] == "HELD"
    p = t["project"]
    assert p["mortar_m3_low"] is None and p["mortar_m3_low_at_least"] == A(0.7728)   # V5 R-T499-1 on installed


def test_stair_1_3_cement_held_group_bags_held():
    st = {"id": "S1", "floor": "GF", "kind": V6.STAIR_FLIGHT, "steps": 10, "risers": 11, "riser": 0.16, "tread": 0.30,
          "width": 1.20, "evidence_status": EV}
    t = V6.table(NORMAL + [st])
    r = _row(t, "S1")
    area = 10 * 0.30 * 1.20 + 11 * 0.16 * 1.20                              # 3.600 + 2.112 = 5.712 m2
    assert r["area_m2"] == A(area)
    assert r["mortar_m3_low"] == A(area * 0.03) and r["bed_procurement_m3_low"] == A(area * 0.03 * 1.05)
    assert r["cement_bags_low"] is None and r["cement_bags_procurement_low"] is None   # 1:3 cement HELD as V1
    g = t["purchase"]["bed_mortar"]["PROJECT"]
    assert g["subtotals"]["bed_procurement_m3_low"]["status"] == "COMPUTED"
    assert g["cement_bags_to_buy_low"] is None and g["cement_bags_to_buy_low_status"] == "HELD"


@pytest.mark.parametrize("pts", [
    [(0, 0), (5000, 0), (5000, 4000), (0, 4000)],
    [(0, 0), (0, 4000), (5000, 4000), (5000, 0)],                                 # mirrored (clockwise)
    [(0, 0), (3000, 4000), (-200, 6400), (-3200, 2400)],                          # rotated 53.13 deg
])
def test_millimetre_rotated_mirrored_outline_same_bed(pts):
    r = _row(V6.table([d1(length=None, width=None, polygon=pts, unit_m=0.001)]), "D1")
    assert r["area_m2"] == A(20.0)
    assert r["mortar_m3_low"] == A(0.6) and r["bed_procurement_m3_high"] == A(0.84)


def test_two_disagreeing_waste_sources_refused():
    vals = dict(V6.OWNER_VALUES, mortar_waste=0.08)
    with pytest.raises(ValueError, match="two waste sources disagree"):
        V6.table(NORMAL, values=vals)


def test_custom_sourced_loss_applied():
    t = V6.table([d1()], loss={"value": 0.10, "source": "fixture: approved project allowance", "status": "VERIFIED"})
    r = _row(t, "D1")
    assert r["mortar_m3_low"] == A(0.6) and r["bed_procurement_m3_low"] == A(0.66) and r["bed_loss_m3_low"] == A(0.06)


def test_module_declarations():
    assert V6.DEFAULT_GUARD_CLASS == "UNWIRED_PRODUCER" and V6.SUPERSEDES == V5.METHOD_ID
    assert V6.METHOD_ID == "FINISH_MATERIALS_TABLE_V6" and any("R-T521-1" in x for x in V6.RULES)
    src = (ROOT / "engine/source/finish_materials_table_v6.py").read_text(encoding="utf-8")
    assert "Alsenan" not in src and "alsenan" not in src.lower()
