"""T-735: formwork conflict decider (R-T735-1 / -2 over R-T732-1). Villa V735 is hand-made (not the development villa):
roof plate one zone, top >= +6.40, t 0.20, base +3.00, finished roof caps the column height at 3.60 m.
- Q1 0.25 x 0.50 column (single section), framed by settled 0.60 beams, joint 0.30 m2, edge band 0.05 m2;
- Q2 a column drawn 0.20 x 0.40 vs scheduled 0.20 x 0.50 (section conflict);
- B1 a beam band 0.30 drawn / 0.25 scheduled, 0.60 deep, beside a 0.15 slab over 1.25 m that the walk booked 0 m2
  because it held the depth.
Two earlier merged pieces state each column line: piece A by P x (h - t) (upper-bound method), piece B BLANK.
Hand figures are written out in each test. The last tests rebuild the development-villa output from committed files."""
from __future__ import annotations

import json
import subprocess
import sys
from decimal import Decimal as X
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t735"))
sys.path.insert(0, str(ROOT / "research" / "agents_t732"))
import t735_rules as R  # noqa: E402
import t732_rules as R32  # noqa: E402


def _q1(**kw):
    # concrete 0.125 x (6.40 - 3.00) = 0.425 .. 0.125 x 3.60 = 0.45
    args = dict(member={"cls": "BOUNDED", "low": "0.425", "high": "0.45"}, sections_m=[("0.25", "0.50")],
                base="3.00", panel_tops_lo=["6.40"], panel_t=["0.20"], h_lo_conc="3.40", h_hi="3.60",
                d_min="0.60", d_max="0.60", d_settled=True,
                faces=[{"face_id": "J", "kind": "JOINT", "fig": "0.30", "recorded_at": "D_MIN"},
                       {"face_id": "E", "kind": "EDGE", "fig": "0.05"}])
    args.update(kw)
    return R32.column_line("Q1", **args)


def _earlier(a_lo="4.800000", a_hi="5.100000"):
    return [{"piece": "A", "form": {"cls": "BOUNDED", "low": a_lo, "high": a_hi},
             "cause": "UPPER_BOUND_METHOD_NOT_A_FLOOR"},
            {"piece": "B", "form": {"cls": "BLANK_NAMED", "low": None, "high": None, "cap": None},
             "cause": "BLANK_WITH_POSITIVE_FLOOR"}]


def _live(r):
    return {"cls": r["cls"], "low": format(r["low"], "f"), "high": None if r["high"] is None else format(r["high"], "f")}


B1_CANDS = [("0.25", "0.60", "4.00", "0.60"), ("0.30", "0.60", "4.00", "0.72")]


# ---------------------------------------------------------------- normal
def test_q1_single_section_decided_bounded_and_both_earlier_forms_superseded():
    # shaft 1.50 x (6.40 - 3.00 - 0.60) = 4.20 .. 1.50 x (3.60 - 0.60) = 4.50; + joint 0.30 + edge 0.05
    r = _q1()
    assert (r["cls"], r["low"], r["high"]) == ("BOUNDED", X("4.550000"), X("4.850000"))
    # piece A 'low' 1.50 x (3.40 - 0.20) = 4.80 sits ABOVE the true high 4.85's floor 4.55: never a floor
    dec = R.decide("Q1", _live(r), _earlier())
    assert [e["piece"] for e in dec["superseded"]] == ["A", "B"] and dec["live"]["low"] == "4.550000"


def test_q2_section_conflict_floor_is_the_shaft_at_least():
    # P 1.20 .. 1.40; shaft low 1.20 x 2.80 = 3.36; joint / edge recorded at one section -> DEPENDENT -> AT_LEAST
    r = _q1(member={"cls": "BOUNDED", "low": "0.272", "high": "0.36"}, sections_m=[("0.20", "0.40"), ("0.20", "0.50")])
    assert (r["cls"], r["low"], r["high"]) == ("AT_LEAST", X("3.360000"), None)
    dec = R.decide("Q2", _live(r), _earlier("3.840000", "4.760000"))
    assert dec["live"] == {"cls": "AT_LEAST", "low": "3.360000", "high": None}


def test_q1_mirror_and_rotation_do_not_change_the_line():
    assert _q1(sections_m=[("0.50", "0.25")])["low"] == _q1()["low"]


def test_b1_held_depth_zero_restated():
    # 1.25 x (0.60 - 0.15) = 0.5625, width-independent (edges along the band)
    r = R.held_depth_side(held_len="1.25", edges_along=[True, True], candidates=B1_CANDS, t="0.15")
    assert (r["cls"], r["low"], r["high"], r["dep"]) == ("BOUNDED", X("0.562500"), X("0.562500"), "INDEPENDENT")
    dec = R.decide("B1", {"cls": "BOUNDED", "low": "0.562500", "high": "0.562500"},
                   [{"piece": "B", "form": {"cls": "BLANK_NAMED", "cap": "0.000000"}, "cause": "CAP_ZERO_FROM_HELD_DEPTH"}])
    assert dec["live"]["low"] == "0.562500"


# ---------------------------------------------------------------- adverse
def test_later_blank_never_wins_silently():
    with pytest.raises(R.Refused, match="never wins by merge order"):
        R.decide("Q1", _live(_q1()), [{"piece": "B", "form": {"cls": "BLANK_NAMED"}, "cause": None}])


def test_no_earlier_form_is_not_a_decision():
    with pytest.raises(R.Refused, match="nothing to decide"):
        R.decide("Q1", _live(_q1()), [])


def test_cap_of_zero_never_enters_as_a_cap():
    with pytest.raises(R.Refused, match="cap of 0"):
        R.decide("B1", {"cls": "BLANK_NAMED", "low": None, "high": None, "cause": "x", "cap": "0"}, _earlier())
    with pytest.raises(R.Refused, match="CAP_ZERO cause"):
        R.decide("B1", {"cls": "BOUNDED", "low": "0.5", "high": "0.6"},
                 [{"piece": "B", "form": {"cls": "BLANK_NAMED", "cap": None}, "cause": "CAP_ZERO_FROM_HELD_DEPTH"}])


def test_blank_live_cannot_supersede_a_blank_by_positive_floor():
    with pytest.raises(R.Refused, match="BLANK_WITH_POSITIVE_FLOOR"):
        R.decide("Q", {"cls": "BLANK_NAMED", "low": None, "high": None, "cause": "D-66"}, _earlier()[1:])


def test_same_form_claim_must_match_and_shapes_checked():
    with pytest.raises(R.Refused, match="called the same form"):
        R.decide("Q", {"cls": "AT_LEAST", "low": "3.36", "high": None},
                 [{"piece": "A", "form": {"cls": "AT_LEAST", "low": "3.40", "high": None}, "cause": "RESTATED_SAME_FORM"}])
    with pytest.raises(R.Refused, match="AT_LEAST needs"):
        R.decide("Q", {"cls": "AT_LEAST", "low": "3.36", "high": "4.0"}, _earlier())
    with pytest.raises(R.Refused, match="BOUNDED needs"):
        R.decide("Q", {"cls": "BOUNDED", "low": "0", "high": "4.0"}, _earlier())
    with pytest.raises(R.Refused, match="two entries"):
        R.decide("Q", _live(_q1()), _earlier() + _earlier()[:1])


@pytest.mark.parametrize("kw, msg", [
    (dict(candidates=[("0.25", "0.60", "4.00", "0.60"), ("0.30", "0.75", "4.00", "0.90")]), "depth differs"),
    (dict(edges_along=[True, False]), "across the member"),
    (dict(t=None), "thickness missing"),
    (dict(t="0.60"), "no downstand"),
    (dict(held_len="0"), "held length <= 0"),
    (dict(held_len="1250"), "unit error"),
    (dict(candidates=[("0.25", "0.60", "4.00", "0.50")]), "does not decompose"),
])
def test_b1_adverse(kw, msg):
    args = dict(held_len="1.25", edges_along=[True], candidates=B1_CANDS, t="0.15")
    args.update(kw)
    with pytest.raises(R.Refused, match=msg):
        R.held_depth_side(**args)


def test_section_in_mm_is_refused_not_scaled():
    with pytest.raises(R32.Refused, match="unit error"):
        _q1(sections_m=[("250", "500")])


# ---------------------------------------------------------------- development villa (committed inputs only)
def test_development_villa_rebuild_and_one_live_form_per_line():
    out = subprocess.run([sys.executable, "-I", str(ROOT / "research" / "agents_t735" / "t735_alsenan.py"), "--check"],
                         capture_output=True, text=True, cwd=ROOT)
    assert out.returncode == 0 and "CHECK OK" in out.stdout, out.stderr[-2000:]
    doc = json.loads((ROOT / "research" / "agents_t735" / "out" / "T735_DECIDER.json").read_text(encoding="utf-8"))
    lines = doc["columns"] + [doc["beam_side"]]
    assert len({r["line_id"] for r in lines}) == 7
    live = {r["line_id"][:10]: (r["live"]["cls"], r["live"]["low"], r["live"]["high"]) for r in lines}
    assert live["L-6f83fc39"] == ("BOUNDED", "4.183916", "5.532116")      # 412: 1.40 x 2.537 + 0.5961 + 0.036016
    assert live["L-b35c1688"] == ("AT_LEAST", "2.893800", None)           # 415: 1.40 x (12.917 - 9.65 - 1.20)
    for k in ("L-6cba8c04", "L-ddec0b3f", "L-f9836bd6", "L-7fe93376"):    # annex: 1.20 x (3.544 - 0.25 - 0.75)
        assert live[k] == ("AT_LEAST", "3.052800", None)
    assert live["L-867e155d"] == ("BOUNDED", "0.102019", "0.102019")      # 0.300056 x (0.50 - 0.16)
    # every source T-730 carried on these lines has its supersession entry (no form left undeclared)
    sup = {(r["line_id"], e["piece"]) for r in lines for e in r["superseded"]}
    assert {(x["line_id"], x["source"]) for x in doc["t730_rows"]} <= sup
    assert doc["family"]["by_class"] == {"AT_LEAST": 40, "BLANK_NAMED": 244, "BOUNDED": 32, "FIX_ROW": 54}
