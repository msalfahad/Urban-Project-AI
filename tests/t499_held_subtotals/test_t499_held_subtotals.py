"""T-499 (F-T496-1): FINISH_MATERIALS_TABLE_V5, rule R-T499-1 'a subtotal over any HELD row is HELD; the known part
AT_LEAST with the held rows listed; a fully determinate subtotal unchanged'. Synthetic hand fixture (no project data;
sizes are fixture data printed on a synthetic finishes schedule):

    F1 hall    4.00 x 2.50 = 10.00 m2, 60 x 60  (5 m2 / 20 kg bag)  -> 2.000 bags
    F2 lounge  6.00 x 4.50 = 27.00 m2, 120 x 60 (3 m2 / bag)        -> 9.000 bags
    F3 bedroom 4.00 x 3.75 = 15.00 m2, 160 x 80 (3 m2 / bag)        -> 5.000 bags
    NORMAL   adhesive 16.000 -> 16 bags; area 52.00 m2; bed 52 x 0.03 .. 0.04 x 1.05 = 1.638 .. 2.184 m3;
             cement x 8 = 13.104 .. 17.472 -> 14 .. 18 bags; sand x 1.1 = 1.8018 .. 2.4024 m3
    ADVERSE size  F3 size unprinted: bags HELD, known 11.000 AT_LEAST, bound 11 + 15 / 5 .. 11 + 15 / 3 = 14 .. 16
    ADVERSE area  F4 4.00 x 3.00 area HELD by source: area HELD AT_LEAST 52.00; cement bags to buy HELD (V4 prints 14
                  from the partial 13.104)
    ADVERSE none  every size unprinted: no known part: bags_known / bags_at_least None (V4 prints 0.0)
"""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import finish_materials_table_v4 as V4     # noqa: E402
from engine.source import finish_materials_table_v5 as V5     # noqa: E402

SRC = "fixture: printed on the synthetic finishes schedule"


def fl(i, ln, wd, size=None, **kw):
    e = {"id": i, "floor": "GF", "kind": V5.DRY_FLOOR, "length": ln, "width": wd,
         "evidence_status": "DRAWING-CONFIRMED"}
    if size:
        e.update(tile_cm=size, tile_size_source=SRC)
    e.update(kw)
    return e


NORMAL = [fl("F1", 4.0, 2.5, "60x60"), fl("F2", 6.0, 4.5, "120x60"), fl("F3", 4.0, 3.75, "160x80")]


def _j(x):
    return json.dumps(x, sort_keys=True, default=str)


# ---- subtotal primitive -------------------------------------------------------------------------------------------

def test_subtotal_primitive():
    assert V5.subtotal([("a", 1.5), ("b", 2.25)]) == {"value": 3.75, "status": "COMPUTED", "at_least": None,
                                                      "held_rows": [], "rows": 2}
    s = V5.subtotal([("a", 1.5), ("b", None)])
    assert (s["value"], s["status"], s["at_least"], s["held_rows"]) == (None, "HELD", 1.5, ["b"])
    s = V5.subtotal([("a", None), ("b", None)])
    assert (s["value"], s["status"], s["at_least"]) == (None, "HELD", None)       # never 0.0
    assert V5.subtotal([])["status"] == "NO_ROWS" and V5.subtotal([])["value"] is None
    assert V5.subtotal([("a", 0.0)])["value"] == 0.0                             # a real 0 stays a real 0


# ---- normal: fully determinate group unchanged --------------------------------------------------------------------

def test_normal_all_sizes_printed_hand_values_and_identical_to_v4():
    t5, t4 = V5.table(NORMAL), V4.table(NORMAL)
    assert _j(t5["rows"]) == _j(t4["rows"])
    for scope in ("project", "per_floor", "per_kind"):
        assert _j(t5[scope]) == _j(t4[scope]), scope
    assert _j(t5["purchase"]) == _j(t4["purchase"])
    p = t5["project"]
    assert p["area_m2"] == 52.0
    assert (p["mortar_m3_low"], p["mortar_m3_high"]) == (1.638, 2.184)
    assert (p["cement_bags_low"], p["cement_bags_high"]) == (13.104, 17.472)
    assert (p["cement_bags_to_buy_low"], p["cement_bags_to_buy_high"]) == (14, 18)
    assert (p["sand_m3_low"], p["sand_m3_high"]) == (1.8018, 2.4024)
    g = t5["purchase"]["adhesive"]["PROJECT"]
    assert (g["status"], g["bags_net"], g["bags_to_buy"]) == ("COMPUTED", 16.0, 16)
    assert not any(k.endswith("_at_least") or k.endswith("_status") and k != "evidence_status" for k in p)
    assert t5["method"] == "FINISH_MATERIALS_TABLE_V5" and t5["supersedes"] == V4.METHOD_ID


# ---- adverse: one size unprinted ------------------------------------------------------------------------------------

def test_adverse_one_size_unprinted_group_held_with_known_part():
    els = [fl("F1", 4.0, 2.5, "60x60"), fl("F2", 6.0, 4.5, "120x60"), fl("F3", 4.0, 3.75)]
    t5, t4 = V5.table(els), V4.table(els)
    g5, g4 = t5["purchase"]["adhesive"]["PROJECT"], t4["purchase"]["adhesive"]["PROJECT"]
    assert g5["status"] == "HELD" and g5["bags_to_buy"] is None
    assert g5["bags_known"] == 11.0 and g5["bags_at_least"] == 11.0 and g5["held_rows"] == ["F3"]
    assert g5["bound_bags_to_buy"] == g4["bound_bags_to_buy"]
    assert (g5["bound_bags_to_buy"]["low"], g5["bound_bags_to_buy"]["high"]) == (14, 16)
    p = t5["project"]
    assert p["adhesive_bags"] is None and p["adhesive_bags_status"] == "HELD"
    assert p["adhesive_bags_at_least"] == 11.0 and p["not_in_sum"]["adhesive_bags"] == ["F3"]
    assert t4["project"]["adhesive_bags"] == 11.0                                 # the V4 defect: known part as total
    assert p["area_m2"] == 52.0 and "area_m2_status" not in p                     # area itself is determinate
    assert p["adhesive_bound_bags_held_rows"] == {"low": 3.0, "high": 5.0}         # complete bound: unchanged


# ---- adverse: an area held ------------------------------------------------------------------------------------------

def test_adverse_area_held_subtotal_held_and_no_bags_to_buy_from_partial():
    els = NORMAL + [fl("F4", 4.0, 3.0, "60x60", area_status="HELD", area_reason="DIMENSION_NOT_PRINTED")]
    t5, t4 = V5.table(els), V4.table(els)
    assert t4["project"]["area_m2"] == 52.0 and t4["project"]["cement_bags_to_buy_low"] == 14    # V4 defect
    p = t5["project"]
    assert p["area_m2"] is None and p["area_m2_status"] == "HELD" and p["area_m2_at_least"] == 52.0
    assert p["not_in_sum"]["area_m2"] == ["F4"] and p["held_rows"] == ["F4"]
    assert p["cement_bags_low"] is None and p["cement_bags_low_at_least"] == 13.104
    assert p["cement_bags_to_buy_low"] is None and p["cement_bags_to_buy_low_status"] == "HELD"
    assert p["cement_bags_to_buy_high"] is None
    g = t5["purchase"]["adhesive"]["PROJECT"]
    assert g["status"] == "HELD" and g["bags_at_least"] == 16.0
    assert g["bound_bags_to_buy"] is None                                          # F4 has no bound (area HELD)
    assert g["bound_bags_held_rows"]["unbounded_rows"] == ["F4"]
    assert p["adhesive_bound_bags_held_rows"] is None                             # no held row bounded: as V4
    assert _j(t5["rows"]) == _j(t4["rows"])


def test_adverse_partial_bound_is_at_least_not_a_bound():
    els = [fl("F1", 4.0, 2.5), fl("F4", 4.0, 3.0, area_status="HELD")]
    p = V5.table(els)["project"]
    b = p["adhesive_bound_bags_held_rows"]
    assert b["status"] == "HELD" and b["low"] is None and b["high"] is None
    assert b["low_at_least"] == 2.0 and b["unbounded_rows"] == ["F4"]
    assert V4.table(els)["project"]["adhesive_bound_bags_held_rows"] == {"low": 2.0, "high": 3.333333}   # V4: looks complete


# ---- adverse: nothing known -----------------------------------------------------------------------------------------

def test_adverse_no_size_anywhere_never_zero():
    els = [fl("F1", 4.0, 2.5), fl("F2", 6.0, 4.5)]
    g4 = V4.table(els)["purchase"]["adhesive"]["PROJECT"]
    assert g4["bags_known"] == 0.0                                                # the F-T496-1 defect reproduced
    g = V5.table(els)["purchase"]["adhesive"]["PROJECT"]
    assert g["status"] == "HELD" and g["bags_known"] is None and g["bags_at_least"] is None
    assert "no known part" in g["why"] and "0.000000" not in g["why"]
    assert (g["bound_bags_to_buy"]["low"], g["bound_bags_to_buy"]["high"]) == (8, 13)   # 37 / 5 = 7.4 .. 37 / 3 = 12.33


def test_wet_wall_operations_partial_area_held():
    def ww(i, held=False):
        e = {"id": i, "floor": "GF", "kind": V5.WET_WALL, "wall_length": 8.40, "door_widths": [0.80],
             "height": 2.40, "tile_cm": "120x60", "tile_size_source": SRC}
        if held:
            e = {"id": i, "floor": "GF", "kind": V5.WET_WALL, "tile_cm": "120x60", "tile_size_source": SRC}
        return e
    t5, t4 = V5.table([ww("W1"), ww("W2", True)]), V4.table([ww("W1"), ww("W2", True)])
    for op, rec in t5["project"]["wet_wall_operations"].items():
        r4 = t4["project"]["wet_wall_operations"][op]
        if r4["area_not_in_sum"]:
            assert rec["area_m2"] is None and rec["area_m2_at_least"] == r4["area_m2"]
    full, f4 = V5.table([ww("W1")]), V4.table([ww("W1")])
    for op, rec in full["project"]["wet_wall_operations"].items():
        r4 = f4["project"]["wet_wall_operations"][op]
        assert rec["area_m2"] == r4["area_m2"] and rec["area_m2"] is not None and "area_m2_status" not in rec
        # the render mortar is HELD on the row itself (no sourced per-m3 mix): labelled HELD, never 0
        assert rec["mortar_m3"] is None and rec["mortar_m3_status"] == "HELD" and rec["mortar_m3_at_least"] is None


def test_box_area_partial_held():
    lines = [{"id": "A", "kind": V5.DRY_FLOOR, "area_m2": 10.0, "tile_cm": "60x60", "tile_size_source": SRC,
              "tile_product": "P"},
             {"id": "B", "kind": V5.DRY_FLOOR, "area_m2": None, "tile_cm": "60x60", "tile_size_source": SRC,
              "tile_product": "P"}]
    r5, r4 = V5.purchase_from_lines(lines), V4.purchase_from_lines(lines)
    assert r4["tiles"]["products"]["P"]["area_m2"] == 10.0
    p = r5["tiles"]["products"]["P"]
    assert p["area_m2"] is None and p["area_m2_at_least"] == 10.0 and p["area_not_in_sum"] == ["B"]
    assert _j(r5["rows"]) == _j(r4["rows"])


# ---- the T-455 ledger (V3.0.45 line index, committed and pinned) read through V5 -------------------------------------

def _t455():
    import importlib.util
    spec = importlib.util.spec_from_file_location("t455", ROOT / "research/agents_t455/t455_tile_purchase.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


@pytest.fixture(scope="module")
def ledger():
    m = _t455()
    led = m.build()
    code = {r["id"]: None for r in led["rows"]}
    d = m._load()
    for ln in d["lines"]:
        if ln["line_id"] in code:
            code[ln["line_id"]] = ln["item_code"]
    return led, code


def test_t455_rows_identical_and_determinate_subtotals_reproduced(ledger):
    led, code = ledger
    rows = led["rows"]
    by = V5.by_group(rows, lambda r: code[r["id"]])
    old = led["by_item_code"]
    assert set(by) == set(old)
    for c, g in by.items():
        o = old[c]
        assert (g["lines"], g["released"], g["held"]) == (o["lines"], o["released"], o["held"])
        if g["area_m2"]["status"] == "COMPUTED":
            assert g["area_m2"]["value"] == o["area_m2"], c
        else:
            assert g["area_m2"]["at_least"] == o["area_m2"], c
        b = g["adhesive_bound_bags_held_rows"]
        if b["status"] == "BOUND":
            assert (b["low"], b["high"]) == (o["bound_low"], o["bound_high"]), c
    assert by["FIN.FLOOR.PORCELAIN"]["area_m2"]["value"] == 305.020973
    assert by["FIN.FLOOR.PORCELAIN"]["adhesive_v3_flat_bags"]["value"] == 61.004193
    assert (by["FIN.FLOOR.PORCELAIN"]["adhesive_bound_bags_held_rows"]["low"],
            by["FIN.FLOOR.PORCELAIN"]["adhesive_bound_bags_held_rows"]["high"]) == (61.004193, 101.673658)
    assert by["FIN.FLOOR.WET_TILE"]["area_m2"]["value"] == 75.945577
    assert by["EXT.FLOOR.PORCELAIN"]["area_m2"]["value"] == 21.0142
    # held groups: the known part AT_LEAST, never the total
    w = by["FIN.WALL.TILE"]
    assert w["area_m2"]["value"] is None and w["area_m2"]["at_least"] == 340.3038 and len(w["area_m2"]["held_rows"]) == 6
    assert w["adhesive_bound_bags_held_rows"]["low_at_least"] == 68.06076
    assert w["adhesive_bound_bags_held_rows"]["high"] is None


def test_t455_every_f_t496_1_zero_is_none(ledger):
    led, code = ledger
    by = V5.by_group(led["rows"], lambda r: code[r["id"]])
    for c, o in led["by_item_code"].items():
        assert o["v4_bags_known"] == 0.0                                          # defect present in the reader
        g = by[c]["adhesive_bags"]
        assert g["value"] is None and g["at_least"] is None and g["status"] == "HELD"
    fh = by["FIN.FLOOR.FINISH_HELD"]
    assert led["by_item_code"]["FIN.FLOOR.FINISH_HELD"]["v3_flat_bags"] == 0.0
    assert fh["adhesive_v3_flat_bags"]["value"] is None and fh["adhesive_v3_flat_bags"]["at_least"] is None
    b = fh["adhesive_bound_bags_held_rows"]
    assert b["low"] is None and b["high"] is None and b["low_at_least"] is None and len(b["unbounded_rows"]) == 3
    lines = [{"id": r["id"], "kind": r["kind"], "finish": r["finish"], "area_m2": r["area_m2"],
              "evidence_status": None if r["area_m2"] is None else r["evidence_status"]} for r in led["rows"]]
    res = V5.purchase_from_lines(lines)
    g = res["adhesive"]["PROJECT"]
    assert led["purchase"]["adhesive"]["PROJECT"]["bags_known"] == 0.0
    assert g["status"] == "HELD" and g["bags_known"] is None and g["bags_at_least"] is None and g["rows"] == 64
    assert len(g["bound_bags_held_rows"]["unbounded_rows"]) == 9          # 6 wall-tile areas HELD + 3 finish-less floor lines


def test_no_zero_subtotal_without_a_number_behind_it(ledger):
    """generic scan: no V5 subtotal value is 0 where no row carries a number for it."""
    led, code = ledger
    by = V5.by_group(led["rows"], lambda r: code[r["id"]])
    for c, g in by.items():
        for k in ("area_m2", "adhesive_v3_flat_bags", "adhesive_bags"):
            assert not (g[k]["value"] == 0 or g[k]["at_least"] == 0), (c, k)


def test_v4_module_untouched():
    assert V4.METHOD_ID == "FINISH_MATERIALS_TABLE_V4" and V5.SUPERSEDES == V4.METHOD_ID
    assert V5.row is V4.row
