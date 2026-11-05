"""T-528: FINISH_MATERIALS_TABLE_V7, rule R-T528-1 'stair marble 1:3 bed: theoretical cement / sand = mortar m3 x the
UP-STAIR-017 (owner Q-53 answer C, CALCULATED PROVISIONAL RATE) rate derived from the mix'.

Q-53 derivation per 1.00 m3 finished 1:3 mortar (owner directive 2026-10-20, recomputed here as arithmetic):
    dry 1.00 x 1.33 = 1.33 m3; cement 1.33 x 1/4 = 0.3325 m3 x 1440 = 478.8 kg / 50 = 9.576 bags; sand 1.33 x 3/4 =
    0.9975 m3 loose (the owner's 'about 1.00 m3' is this figure rounded; the PRELIMINARY PURCHASING allowance 10 bags +
    1.00 m3 per m3 is a separate layer).

Synthetic hand fixture (NOT the training villa):
    S1 flight  20 treads x 0.30 x 1.25 = 7.50 m2 + 20 risers x 0.18 x 1.25 = 4.50 m2 = 12.00 m2, bed 0.03 m (Q-45)
        installed   12.00 x 0.03 = 0.360 m3 (no loss)
        cement      0.360 x 478.8 = 172.368 kg = 3.44736 bags (0.1197 m3 loose)
        sand        0.360 x 0.9975 = 0.3591 m3
        loss 5 %    0.018 m3 (Q-45 named loss, own account)  procurement 0.378 m3 -> 3.619728 bags, 0.377055 m3 sand
        allowance   0.360 x 10 = 3.60 bags, 0.360 x 1.00 = 0.360 m3 (labelled, never summed)
    L1 landing 3.00 x 4.00 = 12.00 m2 drawn in millimetres, rotated 30 deg and mirrored -> the same 0.360 m3 / bags.
    D1 dry floor 5.00 x 4.00 (1:4, the T-521 fixture): procurement cement 5.04 .. 6.72 bags.
    group PROJECT (D1 + S1): procurement cement 8.659728 .. 10.339728 -> buy 9 .. 11 bags (ONCE).

Adverse: bed thickness absent -> HELD (V6 identical); a mix other than 1:3 -> HELD (the 1:4 rate never borrowed); a
1:3 rate passed in values -> refused; a tampered / unapproved / incomplete rule record -> HELD, never patched; a held
area -> HELD and the group's bags HELD; a loss with no source -> installed cement produced, procurement HELD; every
non-stair row byte-identical to V6.
"""

import copy
import json
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import finish_materials_table_v6 as V6     # noqa: E402
from engine.source import finish_materials_table_v7 as V7     # noqa: E402
from engine.source import rule_store_v2 as RS                 # noqa: E402

SRC = "fixture: printed on the synthetic finishes schedule"
EV = "DRAWING-CONFIRMED"
A = pytest.approx

# the Q-53 arithmetic, written out (not read from the module under test)
BAGS_PER_M3 = 1.33 * 1 / 4 * 1440 / 50          # 9.576
KG_PER_M3 = 1.33 * 1 / 4 * 1440                 # 478.8
CEM_M3_PER_M3 = 1.33 * 1 / 4                    # 0.3325
SAND_PER_M3 = 1.33 * 3 / 4                      # 0.9975


def d1(**kw):
    e = {"id": "D1", "floor": "GF", "kind": V7.DRY_FLOOR, "length": 5.0, "width": 4.0, "tile_cm": "60x60",
         "tile_size_source": SRC, "evidence_status": EV}
    e.update(kw)
    return e


def b1(**kw):
    e = {"id": "B1", "floor": "GF", "kind": V7.WET_FLOOR, "length": 2.4, "width": 1.8, "tile_cm": "60x60",
         "tile_size_source": SRC, "evidence_status": EV}
    e.update(kw)
    return e


def w1(**kw):
    e = {"id": "W1", "floor": "GF", "kind": V7.WET_WALL, "wall_length": 2 * (2.4 + 1.8), "door_widths": [0.8],
         "height": 2.7, "openings": [{"id": "WN1", "width": 0.6, "height": 0.6}], "tile_cm": "60x60",
         "tile_size_source": SRC, "evidence_status": EV}
    e.update(kw)
    return e


def s1(**kw):
    e = {"id": "S1", "floor": "GF", "kind": V7.STAIR_FLIGHT, "steps": 20, "risers": 20, "riser": 0.18, "tread": 0.30,
         "width": 1.25, "evidence_status": EV}
    e.update(kw)
    return e


def _landing_mm(rot_deg=30.0, mirror=True):
    pts = [(0, 0), (3000, 0), (3000, 4000), (0, 4000)]
    c, s = math.cos(math.radians(rot_deg)), math.sin(math.radians(rot_deg))
    out = []
    for x, y in pts:
        if mirror:
            x = -x
        out.append((x * c - y * s + 125000.0, x * s + y * c - 7000.0))
    return out


def l1(**kw):
    e = {"id": "L1", "floor": "1F", "kind": V7.STAIR_LANDING, "polygon": _landing_mm(), "unit_m": 0.001,
         "evidence_status": EV}
    e.update(kw)
    return e


NORMAL = [d1(), b1(), w1()]


def _j(x):
    return json.dumps(x, sort_keys=True, default=str)


def _row(t, i):
    return next(r for r in t["rows"] if r["id"] == i)


# ---- the rate ----------------------------------------------------------------------------------------------------

def test_rate_is_the_q53_derivation_from_the_rule_record():
    rate, why = V7.stair_rate()
    assert why is None and rate["rule_id"] == "UP-STAIR-017" and rate["status"] == "CALCULATED PROVISIONAL"
    assert rate["cement_bags_per_m3"] == A(BAGS_PER_M3) == A(9.576)
    assert rate["cement_kg_per_m3"] == A(KG_PER_M3) == A(478.8)
    assert rate["cement_m3_per_m3"] == A(CEM_M3_PER_M3) == A(0.3325)
    assert rate["sand_m3_per_m3"] == A(SAND_PER_M3) == A(0.9975)
    assert rate["purchasing_allowance"] == {"cement_bags_per_m3": 10.0, "sand_m3_per_m3": 1.0}
    assert "Q-53" in rate["source"]


def test_rule_worked_example_reproduced():
    rule = RS.rule("UP-STAIR-017", "1.8.0")
    ex = rule["worked_examples"][0]
    t = V7.table([{"id": "X", "floor": "GF", "kind": V7.STAIR_LANDING, "area_m2": ex["stair_marble_m2"]}])
    r = _row(t, "X")
    assert r["mortar_m3_low"] == A(ex["mortar_m3"]) and r["cement_kg_low"] == A(ex["cement_kg"])
    assert r["cement_bags_low"] == A(ex["cement_bags"]) and r["sand_m3_low"] == A(ex["sand_m3"])
    assert r["bed_purchasing_allowance"]["cement_bags_low"] == A(ex["purchasing_bags"])
    assert r["bed_purchasing_allowance"]["sand_m3_low"] == A(ex["purchasing_sand_m3"])


# ---- normal: the 12.00 m2 flight by hand -------------------------------------------------------------------------

def test_flight_installed_theoretical_by_hand():
    r = _row(V7.table([s1()]), "S1")
    area = 20 * 0.30 * 1.25 + 20 * 0.18 * 1.25                          # 7.50 + 4.50 = 12.00 m2
    assert r["area_m2"] == A(area) == A(12.0)
    assert r["mix"] == "1:3" and r["mortar_stage"] == "INSTALLED"
    assert (r["mortar_m3_low"], r["mortar_m3_high"]) == (A(0.36), A(0.36))      # 12.00 x 0.03, no loss
    assert r["cement_bags_low"] == A(0.36 * BAGS_PER_M3) == A(3.44736)
    assert r["cement_kg_low"] == A(0.36 * KG_PER_M3) == A(172.368)
    assert r["cement_m3_low"] == A(0.1197)
    assert r["sand_m3_low"] == A(0.36 * SAND_PER_M3) == A(0.3591)
    assert r["cement_sand_status"] == "CALCULATED PROVISIONAL" and r["cement_sand_reason"] is None


def test_flight_loss_and_procurement_own_fields():
    r = _row(V7.table([s1()]), "S1")
    assert r["bed_loss_m3_low"] == A(0.018) and r["bed_procurement_m3_low"] == A(0.378)
    assert r["cement_bags_procurement_low"] == A(0.378 * BAGS_PER_M3) == A(3.619728)
    assert r["sand_m3_procurement_low"] == A(0.378 * SAND_PER_M3) == A(0.377055)
    # the theoretical (installed) cement never carries the loss
    assert r["cement_bags_low"] == A(r["mortar_m3_low"] * BAGS_PER_M3)


def test_purchasing_allowance_is_a_separate_layer():
    t = V7.table([s1()])
    r = _row(t, "S1")
    pa = r["bed_purchasing_allowance"]
    assert pa["cement_bags_low"] == A(3.6) and pa["sand_m3_low"] == A(0.36) and "PRELIMINARY" in pa["label"]
    g = t["purchase"]["bed_mortar"]["PROJECT"]
    assert g["cement_bags_to_buy_low"] == 4 == math.ceil(3.619728)        # from procurement, not from 3.6
    assert g["stair_1_3_rows"] == ["S1"]
    assert g["stair_purchasing_allowance"]["subtotals"]["cement_bags_low"]["value"] == A(3.6)
    assert t["project"]["cement_bags_low"] == A(3.44736)                  # theoretical sum, not the allowance


def test_never_the_1_4_rate_on_a_1_3_bed():
    r = _row(V7.table([s1()]), "S1")
    assert r["cement_bags_low"] != A(0.36 * 8.0) and r["sand_m3_low"] != A(0.36 * 1.1)


def test_landing_mm_rotated_mirrored_same_as_metres():
    t = V7.table([l1(), l1(id="L2", polygon=_landing_mm(0.0, False)),
                  {"id": "L3", "floor": "1F", "kind": V7.STAIR_LANDING, "length": 3.0, "width": 4.0}])
    for i in ("L1", "L2", "L3"):
        r = _row(t, i)
        assert r["area_m2"] == A(12.0) and r["mortar_m3_low"] == A(0.36)
        assert r["cement_bags_low"] == A(3.44736) and r["sand_m3_low"] == A(0.3591)


def test_mixed_group_ceil_once():
    t = V7.table([d1(), s1()])
    g = t["purchase"]["bed_mortar"]["PROJECT"]
    lo = 0.63 * 8.0 + 0.378 * BAGS_PER_M3                                   # 5.04 + 3.619728
    hi = 0.84 * 8.0 + 0.378 * BAGS_PER_M3                                   # 6.72 + 3.619728
    assert g["subtotals"]["cement_bags_procurement_low"]["value"] == A(lo) == A(8.659728)
    assert g["subtotals"]["cement_bags_procurement_high"]["value"] == A(hi) == A(10.339728)
    assert (g["cement_bags_to_buy_low"], g["cement_bags_to_buy_high"]) == (9, 11)
    # per floor / kind / project never round whole bags
    assert t["project"]["cement_bags_to_buy_low"] is None


def test_two_groups_one_ceil_each():
    t = V7.table([d1(), s1(mortar_group="STAIR")])
    bm = t["purchase"]["bed_mortar"]
    assert bm["STAIR"]["cement_bags_to_buy_low"] == 4 and bm["PROJECT"]["cement_bags_to_buy_low"] == 6
    assert "stair_1_3_rows" not in bm["PROJECT"]


# ---- V6 identity on every non-stair key ------------------------------------------------------------------------

def test_non_stair_rows_byte_identical_to_v6():
    els = NORMAL + [s1()]
    t6, t7 = V6.table(els), V7.table(els)
    for a, b in zip(t6["rows"], t7["rows"]):
        if a["kind"] in V7.STAIR_KINDS:
            continue
        assert _j(a) == _j(b)
    for rec in V7.diff_v6(els):
        assert (rec["moved"] == []) == (rec["kind"] not in V7.STAIR_KINDS)


def test_table_without_stairs_identical_to_v6():
    t6, t7 = V6.table(NORMAL), V7.table(NORMAL)
    for k in ("rows", "per_floor", "per_kind", "project", "purchase"):
        assert _j(t6[k]) == _j(t7[k])


def test_stair_row_only_moves_the_cement_sand_keys():
    rec = next(x for x in V7.diff_v6([s1()]) if x["id"] == "S1")
    assert set(rec["moved"]) == {
        "cement_bags_low", "cement_bags_high", "sand_m3_low", "sand_m3_high", "cement_kg_low", "cement_kg_high",
        "cement_m3_low", "cement_m3_high", "cement_bags_procurement_low", "cement_bags_procurement_high",
        "sand_m3_procurement_low", "sand_m3_procurement_high", "cement_sand_status", "cement_sand_reason",
        "stair_rate", "bed_purchasing_allowance"}
    assert rec["v6"]["cement_bags_low"] is None                              # V6 held it


# ---- adverse -----------------------------------------------------------------------------------------------------

def test_bed_thickness_absent_held():
    v = copy.deepcopy(V7.OWNER_VALUES)
    v["bed_m"][V7.STAIR_FLIGHT] = None
    r7, r6 = _row(V7.table([s1()], v), "S1"), _row(V6.table([s1()], v), "S1")
    assert r7["mortar_m3_low"] is None and r7["cement_bags_low"] is None and r7["mortar_status"] == "HELD"
    assert _j(r7) == _j(r6)
    g = V7.table([d1(), s1()], v)["purchase"]["bed_mortar"]["PROJECT"]
    assert g["cement_bags_to_buy_low"] is None and g["cement_bags_to_buy_low_status"] == "HELD"


@pytest.mark.parametrize("mix", ["1:2", "1:4", "", None])
def test_mix_not_1_3_never_derived(mix):
    v = copy.deepcopy(V7.OWNER_VALUES)
    v["mix"][V7.STAIR_FLIGHT] = mix
    r7, r6 = _row(V7.table([s1()], v), "S1"), _row(V6.table([s1()], v), "S1")
    assert _j(r7) == _j(r6) and "stair_rate" not in r7          # V7 adds nothing: no Q-53 figure on another mix
    if mix != "1:4":
        assert r7["cement_bags_low"] is None


def test_1_3_rate_in_values_refused():
    v = copy.deepcopy(V7.OWNER_VALUES)
    v["per_m3_of_mortar"]["1:3"] = {"cement_bags_50kg": 10.0, "sand_m3_loose": 1.0}
    with pytest.raises(ValueError, match="two rate sources"):
        V7.table([s1()], v)


def _rule(**params):
    r = RS.rule("UP-STAIR-017", "1.8.0")
    r["params"].update(params)
    return r


@pytest.mark.parametrize("rule,code", [
    (_rule(theoretical_cement_bags_per_m3=10.0), "STAIR_RATE_INCONSISTENT"),
    (_rule(theoretical_sand_m3_per_m3=1.0), "STAIR_RATE_INCONSISTENT"),
    (_rule(dry_volume_factor=None), "STAIR_RATE_PARAM_NOT_GIVEN"),
    (_rule(cement_bulk_density_kg_m3=0), "STAIR_RATE_PARAM_NOT_GIVEN"),
    (_rule(mix_cement_sand="1:4"), "STAIR_RATE_MIX_MISMATCH"),
    (dict(RS.rule("UP-STAIR-017", "1.8.0"), status="PROPOSED"), "STAIR_RATE_NOT_APPROVED"),
])
def test_bad_rule_record_held_never_patched(rule, code):
    t = V7.table([d1(), s1()], rule=rule)
    r = _row(t, "S1")
    assert r["cement_bags_low"] is None and r["sand_m3_low"] is None and r["cement_bags_procurement_low"] is None
    assert code in r["cement_sand_reason"] and r["stair_rate"] is None
    assert r["mortar_m3_low"] == A(0.36)                                     # the built bed is still produced
    g = t["purchase"]["bed_mortar"]["PROJECT"]
    assert g["cement_bags_to_buy_low"] is None and g["cement_bags_to_buy_low_status"] == "HELD"


def test_held_area_stays_held_never_zero():
    t = V7.table([d1(), s1(steps=None)])
    r = _row(t, "S1")
    assert r["area_m2"] is None and r["mortar_m3_low"] is None and r["cement_bags_low"] is None
    assert t["project"]["cement_bags_low"] is None and t["project"]["cement_bags_low_status"] == "HELD"
    assert t["project"]["cement_bags_low_at_least"] == A(4.8)
    g = t["purchase"]["bed_mortar"]["PROJECT"]
    assert g["cement_bags_to_buy_low"] is None


def test_loss_without_source_installed_produced_procurement_held():
    loss = {"value": 0.05, "source": "", "status": "?"}
    t = V7.table([s1()], loss=loss)
    r = _row(t, "S1")
    assert r["cement_bags_low"] == A(3.44736) and r["sand_m3_low"] == A(0.3591)
    assert r["cement_bags_procurement_low"] is None and r["bed_procurement_status"] == "HELD"
    g = t["purchase"]["bed_mortar"]["PROJECT"]
    assert g["cement_bags_to_buy_low"] is None and g["cement_bags_to_buy_low_status"] == "HELD"


def test_module_is_project_agnostic_and_unwired():
    src = (ROOT / "engine/source/finish_materials_table_v7.py").read_text(encoding="utf-8").lower()
    assert "alsenan" not in src and "7757" not in src
    assert V7.DEFAULT_GUARD_CLASS == "UNWIRED_PRODUCER"
    hits = [p for p in (ROOT / "engine").rglob("*.py")
            if p.name != "finish_materials_table_v7.py" and "finish_materials_table_v7" in p.read_text(encoding="utf-8")]
    assert hits == []
