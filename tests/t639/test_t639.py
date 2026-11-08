"""T-639: rebar hold census (R-T639-1). Synthetic villa "V639" (not the training villa) by hand with adverse cases (bars
on a HELD concrete element released, a lap without an owner rule, missing diameter / length, mm read as m, a fractional
bar count, an unknown hold text, a column whose hold enters the bar length); then the development villa: the 801
HELD-blank and 6 open-high B11-01 STR.REBAR lines of the T-630 dry run classed A / B / C / D (repository files only)."""
from __future__ import annotations

import json
import os
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t639"))
import t639_rules as R  # noqa: E402
import t639_alsenan as A  # noqa: E402

D = Decimal

# ---- villa "V639" (hand) --------------------------------------------------------------------------------------------
# Beam B7 0.25 x 0.60, clear span 5.40 m face to face, schedule row: bottom 3 T16, top 2 T12, stirrups T8 @ 0.15 with
# the first link 0.075 from each support face (printed), link developed length 1.30 m printed on its section.
#   bottom 3 x 5.40 = 16.20 m x 16^2/162 (1.580247) = 25.600000 kg
#   top    2 x 5.40 = 10.80 m x 12^2/162 (0.888889) =  9.600000 kg
#   links  N = 1 + floor((5.40 - 2 x 0.075) / 0.15) = 1 + 35 = 36; 36 x 1.30 = 46.80 m x 8^2/162 (0.395062) = 18.488889 kg
#   total 53.688889 kg = 0.053689 t (no lap: none printed, none added)


def test_v639_beam_by_hand():
    bottom = R.population_kg(3, "5.40", 16)
    top = R.population_kg(2, "5.40", 12)
    n = 1 + int((D("5.40") - 2 * D("0.075")) / D("0.15"))
    links = R.population_kg(n, "1.30", 8)
    assert n == 36
    assert R.q(bottom) == D("25.600000") and R.q(top) == D("9.600000") and R.q(links) == D("18.488889")
    assert R.q((bottom + top + links) / 1000) == D("0.053689")


def test_v639_units_and_mirror():
    # the same population read in either order / from a mirrored plan gives the same kg; mm is refused as m
    assert R.population_kg(3, "5.40", 16) == R.population_kg("3", D("5.4"), "16")
    with pytest.raises(R.RuleError, match="UNIT_REFUSED"):
        R.population_kg(3, 5400, 16)
    with pytest.raises(R.RuleError, match="UNIT_REFUSED"):
        R.kg_per_m(0.016)


def test_adverse_bars_on_held_concrete_refused():
    for state in ("HELD", "EXCLUDED"):
        with pytest.raises(R.RuleError, match="RELEASE_REFUSED"):
            R.release_refusal(state)
    R.release_refusal("RELEASED")


def test_adverse_lap_without_owner_rule_refused():
    with pytest.raises(R.RuleError, match="LAP_REFUSED"):
        R.population_kg(3, "5.40", 16, laps_m="0.96")
    with pytest.raises(R.RuleError, match="LAP_REFUSED"):
        R.lap_refusal({"laps_m": "0.96"})
    assert R.population_kg(3, "5.40", 16, laps_m="0.96", lap_rule="approved") > R.population_kg(3, "5.40", 16)


def test_adverse_missing_input_stays_held_never_zero():
    for args in ((None, "5.40", 16), (3, None, 16), (3, "5.40", None)):
        with pytest.raises(R.RuleError, match="not printed"):
            R.population_kg(*args)
    with pytest.raises(R.RuleError, match="whole number"):
        R.population_kg("2.5", "5.40", 16)


def test_adverse_unknown_hold_text_refused():
    with pytest.raises(R.RuleError, match="unclassifiable"):
        R.cause_kind("something no rule names")
    assert R.cause_kind("diameter not printed; count Q-71")[1] == "B"
    assert R.cause_kind("PROFILE_VALUE_NOT_USABLE: ...")[1] == "C"


def _col(printed, reasons=None):
    return {"bar_group": "MAIN_BARS_NET", "printed": printed, "count": 8.0, "length_m": 4.5,
            "reasons": reasons or ["T-119 HELD: framing member BM-X (unlabelled, HELD); controlling depth NOT changed "
                                   "by it (D_ctrl settled by calculated members)"]}


T119 = {"hold_cause": "FRAMING_MEMBER_HELD_D_SETTLED", "interval": "4.5", "D_ctrl": "0.75"}
SIB = {"storey": "GF", "interval": "4.5"}
P = "p.9 C4 GF: 8 ø 16; height 3.75 + D_ctrl 0.75 (bars run through the joint) = interval 4.50"


def test_class_d_column_by_hand_and_adverse():
    f = R.d_column_main(_col(P), T119, "RELEASED", SIB)
    assert f["kg"] == "56.888889" and f["count"] == 8 and f["dia_mm"] == 16     # 8 x 4.50 x 256/162
    with pytest.raises(R.RuleError, match="RELEASE_REFUSED"):
        R.d_column_main(_col(P), T119, "HELD", SIB)
    with pytest.raises(R.RuleError, match="not only"):
        R.d_column_main(_col(P, [_col(P)["reasons"][0] + "; top bend drawn without length: BLOCKED_DETAILING"]),
                        T119, "RELEASED", SIB)
    with pytest.raises(R.RuleError, match="T-119 cause"):
        R.d_column_main(_col(P), dict(T119, hold_cause="FRAMING_MEMBER_HELD_D_OPEN"), "RELEASED", SIB)
    with pytest.raises(R.RuleError, match="reconcile"):
        R.d_column_main(_col(P.replace("3.75", "3.70")), T119, "RELEASED", SIB)
    with pytest.raises(R.RuleError, match="sibling"):
        R.d_column_main(_col(P), T119, "RELEASED", {"storey": "1F", "interval": "4.2"})


# ---- development villa --------------------------------------------------------------------------------------------
@pytest.fixture(scope="module")
def census():
    return A.build()


def test_every_line_classed_once_with_a_cause(census):
    c = census["counts"]
    assert c["lines"] == 807 and sum(c["by_class"].values()) == 807
    assert sum(n for k, n in c["by_class_state"].items() if k.endswith("|BLANK")) == 801
    assert sum(n for k, n in c["by_class_state"].items() if k.endswith("|OPEN_HIGH")) == 6
    assert all(r["cause"] and r["class"] in "ABCD" for r in census["lines"])
    assert len({r["line_id"] for r in census["lines"]}) == 807


def test_nothing_computed_outside_class_d(census):
    assert all("fix" not in r for r in census["lines"] if r["class"] != "D")
    assert census["totals_kg"]["A"] is None and census["totals_kg"]["B"] is None and census["totals_kg"]["C"] is None
    assert all(r["concrete_class"] not in ("HELD", "EXCLUDED") for r in census["lines"] if r["class"] != "A")


def test_class_d_rows_recomputed_by_hand(census):
    fx = {f["column"]: f for f in census["fix_rows"]}
    # COL-GF-09: p.9 C9 GF 14 ø 16 over the 4.50 storey interval: 14 x 4.50 x 256/162 = 99.555556 kg
    assert fx["COL-GF-09"]["kg"] == str(R.q(D(14) * D("4.5") * D(256) / D(162))) == "99.555556"
    # COL-GF-22: p.9 C5 GF 10 ø 16: 10 x 4.50 x 256/162 = 71.111111 kg
    assert fx["COL-GF-22"]["kg"] == "71.111111"
    # all six: (8 + 10 + 8 + 8 + 14 + 10) = 58 bars x 4.50 = 261 m x 256/162 = 412.444444 kg
    assert sorted(fx) == ["COL-GF-01", "COL-GF-02", "COL-GF-03", "COL-GF-05", "COL-GF-09", "COL-GF-22"]
    assert sum(f["count"] for f in fx.values()) == 58
    assert census["totals_kg"]["D"] == str(R.q(D(261) * D(256) / D(162))) == "412.444444"
    assert all(f["sibling"]["released_kg"] for f in fx.values())


def test_open_high_lines_name_what_keeps_them_open(census):
    oh = census["open_high"]
    assert len(oh) == 6 and all("high open by name:" in r["what_keeps_the_high_open"] for r in oh)


def test_outputs_current(census):
    p = A.OUT_JSON
    assert p.exists(), "run test_write_outputs with URBAN_T639_WRITE=1"
    assert json.loads(p.read_text(encoding="utf-8")) == json.loads(json.dumps(census, ensure_ascii=False,
                                                                              sort_keys=True))


@pytest.mark.skipif(os.environ.get("URBAN_T639_WRITE") != "1", reason="writer: URBAN_T639_WRITE=1")
def test_write_outputs():
    A.write()
