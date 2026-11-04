"""T-495: finish-HELD outdoor floor rows in the tile purchase ledger V2, per finish option with the owner-rule bound,
and the scope guard (R-T495-1) that keeps every held floor-surface line inside the bound.

Fixture villa P495 (not the training villa), by hand:
  T1 open terrace, HELD [12.000, 12.000] m2, options porcelain / marble:
     porcelain adhesive 12 / 5 = 2.400 .. 12 / 3 = 4.000 bags; bed 12 x 0.03 x 1.05 = 0.378 .. 12 x 0.04 x 1.05 = 0.504 m3,
     cement x 8 = 3.024 .. 4.032 bags, sand x 1.1 = 0.4158 .. 0.5544 m3; marble adhesive HELD (Q-45), bed as above.
  T2 side deck, HELD [8.000, 9.500] m2 (unequal ends), options interlock / porcelain:
     porcelain adhesive 8 / 5 = 1.600 .. 9.5 / 3 = 3.166667; bed 8 x 0.03 x 1.05 = 0.252 .. 9.5 x 0.04 x 1.05 = 0.399 m3,
     cement 2.016 .. 3.192, sand 0.2772 .. 0.4389; interlock: no owner rule -> HELD, no bound (never 0).
  T3 roof deck, HELD with an OPEN range (no low / high), option porcelain -> no bound; the porcelain option total is then
     None (a partial sum is never the bound).
"""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t495"))

import t495_finish_held_ledger as L  # noqa: E402

P, M, T, I = L.PORCELAIN, L.MARBLE, L.TIMBER, L.INTERLOCK
OPTS = {"EXT.FLOOR.OUTDOOR": {"T1": ((P, M), "fixture owner words", "OWNER-STATED OPTIONS"),
                              "T2": ((I, P), "fixture open owner question", "OPTIONS FROM AN OPEN QUESTION"),
                              "T3": ((P,), "fixture owner words", "OWNER-STATED OPTIONS")}}


def _ln(i, code, eid, cls, net=None, lo=None, hi=None, unit="m2"):
    return {"line_id": i, "item_code": code, "element_id": eid, "class": cls, "unit": unit, "measured_net": net,
            "held_low": lo, "held_high": hi, "binding": None}


def _villa():
    return {"lines": [_ln("L1", "EXT.FLOOR.OUTDOOR", "GF-T1", "HELD", lo=12.0, hi=12.0),
                      _ln("L2", "EXT.FLOOR.OUTDOOR", "GF-T2", "HELD", lo=8.0, hi=9.5),
                      _ln("L3", "EXT.FLOOR.OUTDOOR", "RF-T3", "HELD"),
                      _ln("L4", "FIN.FLOOR.PORCELAIN", "GF-R1", "RELEASED", net=20.0),
                      _ln("L5", "FIN.FLOOR.BED.DRY", "GF-R1", "RELEASED", net=20.0),
                      _ln("L6", "EXT.PAVING.INTERLOCK", "GF-COURT", "RELEASED", net=50.0)]}


def _by(rows, i):
    return next(r for r in rows if r["id"] == i)


def _opt(row, f):
    return next(o for o in row["options"] if o["finish"] == f)


def test_fixture_rows_per_option_by_hand():
    rows = L.finish_held_rows(_villa(), OPTS)
    assert [r["id"] for r in rows] == ["L1", "L2", "L3"]
    assert all(r["status"] == "HELD" and r["area_m2"] is None for r in rows)
    p1 = _opt(_by(rows, "L1"), P)
    assert p1["adhesive_bags_20kg"]["low"] == pytest.approx(2.4)
    assert p1["adhesive_bags_20kg"]["high"] == pytest.approx(4.0)
    assert p1["bed"]["mortar_m3"] == {"low": pytest.approx(0.378), "high": pytest.approx(0.504)}
    assert p1["bed"]["cement_bags_50kg"] == {"low": pytest.approx(3.024), "high": pytest.approx(4.032)}
    assert p1["bed"]["sand_m3_loose"] == {"low": pytest.approx(0.4158), "high": pytest.approx(0.5544)}
    m1 = _opt(_by(rows, "L1"), M)
    assert m1["adhesive_bags_20kg"] is None and "Q-45" in m1["adhesive_reason"]
    assert m1["bed"]["mortar_m3"]["low"] == pytest.approx(0.378)
    p2 = _opt(_by(rows, "L2"), P)
    assert p2["adhesive_bags_20kg"]["low"] == pytest.approx(1.6)
    assert p2["adhesive_bags_20kg"]["high"] == pytest.approx(9.5 / 3)
    assert p2["bed"]["mortar_m3"] == {"low": pytest.approx(0.252), "high": pytest.approx(0.399)}
    assert p2["bed"]["cement_bags_50kg"] == {"low": pytest.approx(2.016), "high": pytest.approx(3.192)}
    assert p2["bed"]["sand_m3_loose"] == {"low": pytest.approx(0.2772), "high": pytest.approx(0.4389)}
    i2 = _opt(_by(rows, "L2"), I)
    assert i2["adhesive_bags_20kg"] is None and i2["bed"] is None
    assert "NO_OWNER_ADHESIVE_RULE" in i2["adhesive_reason"] and "NO_OWNER_BED_RULE" in i2["bed_reason"]


def test_open_range_gives_no_bound_never_zero():
    rows = L.finish_held_rows(_villa(), OPTS)
    p3 = _opt(_by(rows, "L3"), P)
    assert p3["adhesive_bags_20kg"] is None and p3["bed"] is None
    assert "AREA_RANGE_OPEN" in p3["adhesive_reason"]
    for r in rows:
        for o in r["options"]:
            for v in ((o["adhesive_bags_20kg"] or {}).get("low"), ((o["bed"] or {}).get("mortar_m3") or {}).get("low")):
                assert v is None or v > 0


def test_scope_guard_normal_every_floor_surface_line_placed():
    c = L.scope_guard(_villa(), OPTS)
    assert c["EXT.FLOOR.OUTDOOR"]["where"] == "FINISH_HELD_OPTIONS" and c["EXT.FLOOR.OUTDOOR"]["held"] == 3
    assert c["FIN.FLOOR.PORCELAIN"]["where"] == "T-455 SCOPE"
    assert c["EXT.PAVING.INTERLOCK"]["where"].startswith("DECLARED_OUT")
    assert "FIN.FLOOR.BED.DRY" not in c                                  # the bed is a material, not a floor surface


def test_scope_guard_adverse_new_held_outdoor_code_fails():
    d = _villa()
    d["lines"].append(_ln("L7", "EXT.FLOOR.ROOF_TERRACE", "RF-T9", "HELD", lo=5.0, hi=5.0))
    with pytest.raises(L.LedgerError, match="SCOPE_GAP.*EXT.FLOOR.ROOF_TERRACE"):
        L.scope_guard(d, OPTS)


def test_scope_guard_adverse_held_line_of_declared_out_code_fails():
    d = _villa()
    d["lines"].append(_ln("L8", "EXT.PAVING.INTERLOCK", "GF-COURT2", "HELD", lo=3.0, hi=4.0))
    with pytest.raises(L.LedgerError, match="SCOPE_GAP.*declared-out"):
        L.scope_guard(d, OPTS)


def test_adverse_options_never_invented_or_unsourced():
    with pytest.raises(L.LedgerError, match="not one of"):
        L.option_bound("GRANITE", 5.0, 5.0)
    d = _villa()
    d["lines"].append(_ln("L9", "EXT.FLOOR.OUTDOOR", "GF-T8", "HELD", lo=4.0, hi=4.0))
    with pytest.raises(L.LedgerError, match="no sourced finish options"):
        L.finish_held_rows(d, OPTS)


def test_adverse_released_or_wrong_unit_finish_held_line_refused():
    d = _villa()
    d["lines"][0].update({"class": "RELEASED", "measured_net": 12.0})
    with pytest.raises(L.LedgerError, match="must be HELD"):
        L.finish_held_rows(d, OPTS)
    d = _villa()
    d["lines"][1]["unit"] = "m"
    with pytest.raises(L.LedgerError, match="not m2"):
        L.finish_held_rows(d, OPTS)


def test_fixture_build_option_totals_none_when_a_line_is_unbounded(tmp_path):
    p = tmp_path / "idx.json"
    p.write_text(json.dumps(_villa()), encoding="utf-8")
    led = L.build(p, OPTS)
    po = led["finish_held_by_option"]
    assert po[P]["lines"] == ["L1", "L2", "L3"]
    assert po[P]["adhesive_low"] is None and po[P]["adhesive_unbounded_lines"] == ["L3"]   # partial sum never printed
    assert po[M]["adhesive_low"] is None and po[M]["mortar_m3_low"] == pytest.approx(0.378)
    assert po[I]["mortar_m3_low"] is None
    assert led["released_quantities_changed"] == 0


# ---- the training villa (pinned candidate line index; no drawing content) ----

def test_training_villa_outdoor_rows_and_bounds():
    led = L.build()
    rows = {r["element_id"]: r for r in led["finish_held_rows"]}
    porch, deck = rows["GF-COURT#PORCH"], rows["GF-COURT#POOL-DECK"]
    assert porch["area_held_low_m2"] == porch["area_held_high_m2"] == 10.6785
    assert deck["area_held_low_m2"] == deck["area_held_high_m2"] == 6.548912
    assert [o["finish"] for o in porch["options"]] == [T, P, M]
    assert [o["finish"] for o in deck["options"]] == [I, P]
    pp = _opt(porch, P)
    assert pp["adhesive_bags_20kg"]["low"] == pytest.approx(10.6785 / 5)
    assert pp["adhesive_bags_20kg"]["high"] == pytest.approx(10.6785 / 3)
    assert pp["bed"]["mortar_m3"]["low"] == pytest.approx(10.6785 * 0.03 * 1.05, abs=1e-6)
    assert pp["bed"]["mortar_m3"]["high"] == pytest.approx(10.6785 * 0.04 * 1.05, abs=1e-6)
    po = led["finish_held_by_option"][P]
    assert po["adhesive_low"] == pytest.approx((10.6785 + 6.548912) / 5, abs=1e-6)    # 3.445482
    assert po["adhesive_high"] == pytest.approx((10.6785 + 6.548912) / 3, abs=1e-6)   # 5.742471
    assert led["finish_held_by_option"][T]["adhesive_low"] is None
    assert all(o["status"] == "HELD" for r in led["finish_held_rows"] for o in r["options"])
    assert led["scope_census"]["EXT.FLOOR.OUTDOOR"] == {"lines": 2, "held": 2, "where": "FINISH_HELD_OPTIONS"}


def test_training_villa_t455_part_unchanged():
    import t455_tile_purchase as L455
    base = L455.build()
    led = L.build()
    assert led["t455_ledger_on_this_input"]["by_item_code"] == base["by_item_code"]
    assert led["t455_ledger_on_this_input"]["adhesive"] == base["purchase"]["adhesive"]


def test_ledger_refuses_an_unpinned_default_input(monkeypatch):
    monkeypatch.setattr(L, "PIN", "0" * 64)
    with pytest.raises(L.LedgerError, match="pinned"):
        L.build()


def test_committed_ledger_matches_a_rebuild(tmp_path):
    L.write(tmp_path)
    for name in ("TILE_PURCHASE_LEDGER_V2.json", "TILE_PURCHASE_LEDGER_V2.csv"):
        assert (tmp_path / name).read_bytes() == (L.HERE / "out" / name).read_bytes()
