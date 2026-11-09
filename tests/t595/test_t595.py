"""T-595: restatement rule versions R-T595-1 (side-bar population from the drawn section) and R-T595-2 (scenario-set
bound). Hand villa "K595" (not the training villa): a ring 0.25 x 0.60 with side bars, a footing with three accepted
readings; normal and adverse cases; then the development-villa restatement rebuilt from merged repository files."""
from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t595"))
import t595_rules as R  # noqa: E402
import t595_alsenan as A  # noqa: E402

D = Decimal


# ---- R-T595-1: K595 ring, in-bay length 6.48 m, d12 side bars ------------------------------------------------------
def test_k595_side_bars_one_face_drawn_by_hand():
    # section draws one face only, two levels: 2 bars; 2 x 6.48 x 144/162 = 11.52 kg
    p = R.side_bar_population(levels_drawn=2, faces_drawn=1)
    assert p["n"] == 2
    assert R.side_bar_low_kg(p, 6.48, 12) == pytest.approx(11.52, abs=1e-9)


def test_k595_side_bars_two_faces_drawn_by_hand():
    # both faces, two levels: 4 bars; 4 x 6.48 x 0.888889 = 23.04 kg (twice the one-face figure)
    p = R.side_bar_population(levels_drawn=2, faces_drawn=2, label_n=2)
    assert p["n"] == 4 and p["status"] == "DRAWN"
    assert R.side_bar_low_kg(p, 6.48, 12) == pytest.approx(23.04, abs=1e-9)


def test_three_levels_two_faces_rotation_free():
    # a deeper section drawn with three levels: 6 bars whatever the plan orientation (no geometry input)
    assert R.side_bar_population(3, 2)["n"] == 6


def test_adverse_single_face_reading_where_two_faces_drawn_refused():
    with pytest.raises(R.T595Error, match="single-face"):
        R.side_bar_population(levels_drawn=2, faces_drawn=2, faces_counted=1)


def test_adverse_dropped_level_refused():
    with pytest.raises(R.T595Error):
        R.side_bar_population(levels_drawn=2, faces_drawn=2, levels_counted=1)


def test_adverse_more_faces_than_drawn_refused():
    with pytest.raises(R.T595Error):
        R.side_bar_population(levels_drawn=2, faces_drawn=1, faces_counted=2)
    with pytest.raises(R.T595Error):
        R.side_bar_population(levels_drawn=1, faces_drawn=3)


def test_adverse_label_conflict_is_held_not_valued():
    p = R.side_bar_population(2, 2, label_n=3)
    assert p["status"] == "DRAWING_CONFLICT"
    with pytest.raises(R.T595Error, match="DRAWING_CONFLICT"):
        R.side_bar_low_kg(p, 6.48, 12)


def test_adverse_units_mm_refused():
    p = R.side_bar_population(2, 2)
    with pytest.raises(R.T595Error):
        R.side_bar_low_kg(p, 6480, 12)          # length in mm
    with pytest.raises(R.T595Error):
        R.kgm(12.0)                              # diameter not a whole mm


# ---- R-T595-2: K595 footing with three accepted readings ------------------------------------------------------------
K595 = {"pad alone": R.box("2.40", "1.20", "0.60"),                                     # 1.728
        "pad + second pad": R.box("2.40", "1.20", "0.60") + R.box("1.00", "0.70", "0.40"),  # 1.728 + 0.280 = 2.008
        "drawn outline": R.box("2.90", "1.20", "0.60")}                                 # 2.088


def test_k595_footing_scenario_bound_by_hand():
    b = R.scenario_bound(K595)
    assert (b["low"], b["high"]) == ("1.728000", "2.088000")
    assert b["low_scenario"] == "pad alone" and b["high_scenario"] == "drawn outline"


def test_adverse_old_reading_low_not_strict_refused():
    # the 'pad + second pad' reading used as the low is above an accepted scenario: refused
    with pytest.raises(R.T595Error, match="not a strict low"):
        R.scenario_bound(K595, stated_low="2.008")
    with pytest.raises(R.T595Error, match="not a strict high"):
        R.scenario_bound(K595, stated_high="2.008")


def test_adverse_missing_scenario_value_never_zero():
    with pytest.raises(R.T595Error, match="SCENARIO_SPLIT_OPEN"):
        R.scenario_bound({"a": "1.0", "b": None})


def test_scenario_view_consistent_and_mixed_refused():
    table = {"concrete": {"A": "1.728", "B": "2.088"}, "blinding": {"A": "0.340", "B": "0.372"}}
    v = R.scenario_view(table, {"concrete": "A", "blinding": "A"})
    assert v == {"scenario": "A", "values": {"concrete": "1.728000", "blinding": "0.340000"}}
    with pytest.raises(R.T595Error, match="mixes"):
        R.scenario_view(table, {"concrete": "A", "blinding": "B"})
    with pytest.raises(R.T595Error, match="SCENARIO_SPLIT_OPEN"):
        R.scenario_view(table, {"concrete": "C", "blinding": "C"})


def test_adverse_box_mm_and_zero_refused():
    with pytest.raises(R.T595Error):
        R.box("2400", "1.20", "0.60")
    with pytest.raises(R.T595Error):
        R.box("0", "1.20", "0.60")


# ---- development villa (merged files only) --------------------------------------------------------------------------
@pytest.fixture(scope="module")
def doc():
    return A.build()


def test_dev_rebuild_equals_committed(doc):
    txt = json.dumps(doc, indent=1, sort_keys=True, ensure_ascii=False, default=str) + "\n"
    assert A.OUT.read_text(encoding="utf-8") == txt


def test_dev_ring_rows(doc):
    rows = {r["row_id"]: r for r in doc["rebar"]["rows"]}
    east = [r for k, r in rows.items() if "DOME-1F-E" in k][0]
    west = [r for k, r in rows.items() if "DOME-1F-W" in k][0]
    assert east["t583_t_low"] == 0.122518 and float(east["t_low"]) == 0.14429   # +21.771 kg (2 more d14)
    assert west["t583_t_low"] == west["t_low"] == 0.063897 and west["low_reading"] == "B4"
    side = [g for g in east["readings"][0]["groups"] if g["group"].startswith("RING_SIDE")][0]
    assert side["population"]["n"] == 4 and side["kg_low"] == pytest.approx(2 * side["t583_kg_low"])
    assert doc["rebar"]["totals"]["t583_t_low"] == 0.767783
    assert doc["rebar"]["totals"]["t_low"] == 0.789555 and doc["rebar"]["totals"]["t_high"] is None


def test_dev_other_rebar_rows_byte_equal_to_t583(doc):
    src = {r["row_id"]: r for r in A.A583.build()["rows"]}
    for r in doc["rebar"]["rows"]:
        if "V1" in r["version"]:
            x = dict(r)
            x.pop("version")
            assert x == src[r["row_id"]]


def test_dev_f10_footing(doc):
    f = doc["footing"]
    assert (f["t572_component"]["low"], f["component"]["low"], f["component"]["high"]) == \
        ("2.176000", "1.960000", "2.275000")
    assert f["component"]["scenarios"] == {"S02-1 F10 alone": "1.960000", "S02-2 F10 + F": "2.176000",
                                           "S02-3 drawn outline": "2.275000"}
    assert f["t572_low_was_strict"] is False
    assert (f["family_t572"]["bounded_part_low"], f["family_v2"]["bounded_part_low"]) == ("7.844500", "7.628500")
    assert f["family_v2"]["bounded_part_high"] == "13.961300" and f["family_v2"]["family_low"] is None
    assert f["beside_his"]["class"] == "WITHIN" and f["beside_his"]["t572_class"] == "BELOW_DRAWN_LOWER"


def test_dev_t572_rows_untouched_on_disk():
    t572 = json.loads((ROOT / "research" / "agents_t572" / "out" / "T572_HELD_BOUNDS.json").read_text(encoding="utf-8"))
    c = [x for x in t572["components"] if x["element_id"] == A.F10_KEY][0]
    assert (c["low"], c["high"]) == ("2.176000", "2.275000")
