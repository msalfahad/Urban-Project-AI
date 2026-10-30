"""T-378: rule R-T378-1 (note 9, a STARTER-bar note, values a stair bar end only where a separate starter is drawn
tied with the flight bar) on a hand-calculated villa that is NOT Alsenan (villa V378), adverse cases and one regression
on the committed Alsenan binding.

Villa V378 (synthetic, Urban bar table engine/bbs_steel.py: d16 1.578, d12 0.888, d8 0.395 kg/m), one flight F1 on a
ground beam: its stair detail S-3 draws 7 ø12 STARTERS left out of the G.B into the flight and tied with the flight's
main bars; the main bars' head ends are drawn as the bar's own hook into the floor beam.
  1. starters 7 ø12, one tie each at note 9:  7 x 0.48 .. 7 x 0.84 m = 3.36 .. 5.88 m x 0.888 = 2.98368 .. 5.22144 kg
                                                                                                  -> KEEP_RANGE
  2. flight main bars 8 ø16, 2 ends at note 9 (foot tied with the starter, head the bar's own hook):
     8 x 2 x 0.64 .. 8 x 2 x 1.12 = 10.24 .. 17.92 m x 1.578 = 16.15872 .. 28.27776 kg             -> HELD, BLANK
  3. step bars 10 ø8, 2 leg ends inside the waist at note 9:
     10 x 2 x 0.32 .. 10 x 2 x 0.56 = 6.40 .. 11.20 m x 0.395 = 2.52800 .. 4.42400 kg              -> HELD, BLANK
  valued 21.67040 .. 37.92320 kg -> 2.98368 .. 5.22144 kg kept, 2 lines BLANK.
"""

import importlib.util
import json
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


T = _load("t378", "research/agents_t378/t378_stair_note9.py")
KG = {16: Decimal("1.578"), 12: Decimal("0.888"), 8: Decimal("0.395")}
BASIS2 = "note 9: count A x 2 x 40 d .. count B x 2 x 70 d per bar"
BASIS1 = "note 9: count A x 1 x 40 d .. count B x 1 x 70 d per bar"


def kg(n, ends, mult_d, d):
    return Decimal(n) * ends * Decimal(mult_d) * Decimal(d) / 1000 * KG[d]


def line(lid, basis, low, high, unit="kg", state="BOUNDED_EXPOSURE", net=None):
    return {"line_id": lid, "unit": unit, "evidence_state": state, "measured_net": net,
            "bounded_range": {"basis": basis, "low": low, "high": high}}


def end(name, drawn, ref="V378 S-3", missing=None):
    e = {"end": name, "support": "x", "drawn_as": drawn, "ref": ref}
    if missing:
        e["missing"] = missing
    return e


STARTER = {"role": "STARTER_INTO_FLIGHT", "ends": [end("tie", "SEPARATE_STARTER_TIED")]}
MAIN = {"role": "FLIGHT_MAIN", "ends": [end("head", "OWN_BAR_INTO_SUPPORT"), end("foot", "SEPARATE_STARTER_TIED")]}
STEP = {"role": "STEP_BAR", "ends": [end("tread", "OWN_BAR_INSIDE_ELEMENT"), end("riser", "OWN_BAR_INSIDE_ELEMENT")]}


def test_hand_fixture_v378():
    s_lo, s_hi = kg(7, 1, 40, 12), kg(7, 1, 70, 12)
    m_lo, m_hi = kg(8, 2, 40, 16), kg(8, 2, 70, 16)
    t_lo, t_hi = kg(10, 2, 40, 8), kg(10, 2, 70, 8)
    assert (s_lo, s_hi) == (Decimal("2.98368"), Decimal("5.22144"))
    assert (m_lo, m_hi) == (Decimal("16.15872"), Decimal("28.27776"))
    assert (t_lo, t_hi) == (Decimal("2.52800"), Decimal("4.42400"))
    res = {}
    for lid, basis, lo, hi, role in (("S", BASIS1, s_lo, s_hi, STARTER), ("M", BASIS2, m_lo, m_hi, MAIN),
                                     ("T", BASIS2, t_lo, t_hi, STEP)):
        cls, prop, _, _ = T.classify_line(line(lid, basis, lo, hi), role)
        res[lid] = (cls, prop, T.value_after(prop, lo, hi))
    assert res["S"] == ("STARTER", "KEEP_RANGE", (s_lo, s_hi))
    assert res["M"][:2] == ("NOT_STARTER", "HELD") and res["M"][2] == (None, None)
    assert res["T"][:2] == ("NOT_STARTER", "HELD") and res["T"][2] == (None, None)
    assert s_lo + m_lo + t_lo == Decimal("21.67040") and s_hi + m_hi + t_hi == Decimal("37.92320")


def test_normal_drawn_starter_into_flight_keeps_note9_range():
    cls, prop, _, ends = T.classify_line(line("S", BASIS1, 1, 2), STARTER)
    assert (cls, prop, ends) == ("STARTER", "KEEP_RANGE", ["STARTER"])
    assert T.value_after(prop, Decimal(1), Decimal(2)) == (Decimal(1), Decimal(2))   # still a range, never released


def test_adverse_flight_main_bar_end_at_note9_held():
    own = {"role": "FLIGHT_MAIN", "ends": [end("head", "OWN_BAR_INTO_SUPPORT"), end("foot", "OWN_BAR_INTO_SUPPORT")]}
    assert T.classify_line(line("M", BASIS2, 1, 2), own)[:2] == ("NOT_STARTER", "HELD")


def test_adverse_unknown_end_needs_the_missing_print_and_is_held():
    with pytest.raises(T.RoleError):
        T.classify_end(end("foot", "NOT_PRINTED"))
    unk = {"role": "FLIGHT_MAIN", "ends": [end("head", "SEPARATE_STARTER_TIED"),
                                           end("foot", "NOT_PRINTED", missing="support under the foot")]}
    assert T.classify_line(line("U", BASIS2, 1, 2), unk)[:2] == ("UNKNOWN", "HELD")


def test_adverse_landing_lap_at_the_temperature_note_refused():
    cls, status, why = T.landing_lap_authority(["P15-NOTE1"])
    assert status == "HELD" and cls == "PRINTED_FOR_OTHER_GROUP" and "TEMPERATURE" in why
    assert T.landing_lap_authority(["P8-NOTE9"])[:2] == ("NOTE9_OUTSIDE_GROUP", "HELD")
    with pytest.raises(Exception):
        T.landing_lap_authority(["CODE-DEFAULT"])          # an unprinted 'code default' is no authority


def test_adverse_held_written_as_zero_refused():
    row = {"line_id": "M", "proposed": "HELD", "kg_low_now": Decimal(1), "kg_high_now": Decimal(2),
           "kg_low_after": Decimal(0), "kg_high_after": Decimal(0)}
    with pytest.raises(T.RoleError):
        T.check_record([row])
    with pytest.raises(T.RoleError):
        T.check_record([dict(row, kg_low_after=None, kg_high_after=None)] * 2)     # bound twice
    with pytest.raises(T.RoleError):
        T.check_record([dict(row, proposed="KEEP_RANGE", kg_low_after=Decimal(1), kg_high_after=Decimal(3))])


def test_adverse_refusals_role_units_release_and_ends():
    with pytest.raises(T.RoleError):                       # role must be defined first
        T.classify_line(line("M", BASIS2, 1, 2), {"role": None, "ends": MAIN["ends"]})
    with pytest.raises(T.RoleError):                       # tonnes are an export unit
        T.classify_line(line("M", BASIS2, 1, 2, unit="t"), MAIN)
    with pytest.raises(T.RoleError):                       # a note 9 length is never released
        T.classify_line(line("M", BASIS2, 1, 2, state="RELEASED", net=1), MAIN)
    with pytest.raises(T.RoleError):                       # two ends booked, one read
        T.classify_line(line("M", BASIS2, 1, 2), STARTER)
    with pytest.raises(T.RoleError):                       # not a note 9 line
        T.classify_line(line("M", "p.15 NOTE 1: 40 x DIA", 1, 2), MAIN)
    with pytest.raises(T.RoleError):                       # an end with no reference
        T.classify_end({"end": "head", "drawn_as": "OWN_BAR_INTO_SUPPORT", "ref": ""})


def test_regression_alsenan_committed_binding():
    roles = json.loads((ROOT / "research/agents_t378/ALSENAN_STAIR_ROLE_INPUT.json").read_text(encoding="utf-8"))
    extract = json.loads((ROOT / "research/agents_t297/CANDIDATE_V3016_REBAR_LINES.json").read_text(encoding="utf-8"))
    rows = T.bind(T.load_listed(ROOT / "research/agents_t373/T373_LAP_BINDING.csv"), extract["lines"], roles["roles"])
    s = T.summarise(rows)
    assert s["lines"] == 22 and s["line_class"] == {"NOT_STARTER": 22}
    assert s["end_class"] == {"NOT_STARTER": 43, "UNKNOWN": 1}
    assert s["downgrade_set"]["kg_now"] == ["373.39", "718.48"] and s["kept_bound"]["lines"] == 0
    assert s["str_rebar_bounded_after_t378"] == ["10903.179488", "13569.187938"]
    ms1l = [r for r in rows if r["stair_element"] == "ST-01:MS1-L" and r["role"] == "FLIGHT_MAIN"]
    assert len(ms1l) == 1 and ms1l[0]["end_classes"] == ["NOT_STARTER", "UNKNOWN"]
    assert all(r["kg_low_after"] is None and r["kg_high_after"] is None for r in rows)
    committed = json.loads((ROOT / "research/agents_t378/T378_SUMMARY.json").read_text(encoding="utf-8"))
    assert committed["downgrade_set"] == s["downgrade_set"]
