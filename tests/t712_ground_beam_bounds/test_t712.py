"""T-712: one-sided floors / named blanks of held ground beams (R-T712-1 .. 3). Villa V712 is hand-made (not the
development villa): an exterior ground beam printed between an approved slab top +0.40 and outer ground +-0.00 whose
section cannot hold its bars; interior titles 'less than 3 m' 30x35, 'less than 6 m' 30x45, 'more than 6 m' 30x70; a
loaded run read at 5.95 / 6.05 m; a junction remainder; a court beam with no printed levels. The last tests rebuild the
development-villa census from committed files only (no drawing is opened)."""
from __future__ import annotations

import json
import sys
from decimal import Decimal as X
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t712"))
import t712_rules as R  # noqa: E402

V712_TITLES = [("LT", "3", "0.35"), ("LT", "6", "0.45"), ("GT", "6", "0.70")]


# ------------------------------------------------------------------ normal (hand)
def test_exterior_literal_floor_hand():
    d = R.depth_literal_levels(top="0.40", underside="0.00")
    assert d == X("0.40")
    f = R.floor(areas_m2=["1.20"], depth=d, basis="LITERAL_LEVELS", census_area_m2="1.20")
    assert f["at_least"] == X("0.480000") and f["at_most"] is None        # 4.00 x 0.30 x 0.40


def test_declared_zero_ground_is_a_level_not_missing():
    assert R.depth_literal_levels(top="0.40", underside=0) == X("0.40")


def test_least_title_short_span_two_titles_hold_hand():
    assert R.titles_holding("2.40", V712_TITLES) == [X("0.35"), X("0.45")]
    assert R.depth_least_title(["2.40"], V712_TITLES) == X("0.35")


def test_least_title_over_two_span_readings_hand():
    # 5.95 m reading: 'less than 6 m' 0.45; 6.05 m reading: 'more than 6 m' 0.70 -> floor 0.45
    assert R.depth_least_title(["6.05", "5.95"], V712_TITLES) == X("0.45")
    f = R.floor(areas_m2=["1.815", "1.785"], depth=X("0.45"), basis="LEAST_TITLE")
    assert f["area_min_m2"] == X("1.785") and f["at_least"] == X("0.803250")


def test_on_the_limit_takes_both_adjacent_titles():
    assert R.titles_holding("6", V712_TITLES) == [X("0.45"), X("0.70")]
    assert R.depth_least_title(["6.00"], V712_TITLES) == X("0.45")


def test_junction_takes_the_least_member_floor():
    assert R.depth_junction({"exterior (literal)": "0.40", "through band span": "0.45"}) == X("0.40")


def test_floor_is_directed_down():
    f = R.floor(areas_m2=["0.807695240"], depth="0.30", basis="LEAST_TITLE")
    assert f["at_least"] == X("0.242308")                 # 0.242308572 floored, never 0.242309


def test_frame_rule_floor_takes_shorter_net_length():
    g = R.governing_length({"GB frame (columns 0.30)": "5.45", "roof frame (columns 0.20)": "5.65"}, "GB frame (columns 0.30)")
    assert g["floor_length_m"] == X("5.45")


def test_blank_court_beam_gives_per_metre_quantity():
    b = R.blank(item="V712-D1 court levels", why="neither level printed", areas_m2=["0.39", "0.415"])
    assert b["at_least"] is None and b["at_most"] is None and b["m3_per_m_depth"] == ["0.390000", "0.415000"]


# ------------------------------------------------------------------ adverse
def test_unprinted_exterior_depth_gives_at_least_only_never_a_range():
    f = R.floor(areas_m2=["1.20"], depth="0.40", basis="LITERAL_LEVELS")
    s = R.statement("L-x", "E", "AT_LEAST", at_least=f["at_least"], item="V712-D35")
    assert s["at_most_m3"] is None and s["at_least_m3"] == "0.480000"


def test_at_most_needs_its_capping_level():
    with pytest.raises(R.Refused):
        R.floor(areas_m2=["1.20"], depth="0.40", basis="LITERAL_LEVELS", at_most="0.9")


def test_unapproved_level_is_no_guarantee():
    with pytest.raises(R.Refused):
        R.depth_literal_levels(top="0.40", underside="0.00", approved=False)


def test_top_below_ground_refused():
    with pytest.raises(R.Refused):
        R.depth_literal_levels(top="0.00", underside="0.15")


def test_unknown_basis_refused():
    with pytest.raises(R.Refused):
        R.floor(areas_m2=["1.20"], depth="0.60", basis="FREELANCER_SECTION")


@pytest.mark.parametrize("bad", [None, "0", "-0.3", "300"])
def test_bad_depth_refused(bad):
    with pytest.raises(R.Refused):
        R.floor(areas_m2=["1.20"], depth=bad, basis="LITERAL_LEVELS")


def test_area_below_census_run_refused():
    with pytest.raises(R.Refused):
        R.floor(areas_m2=["1.05"], depth="0.40", basis="LITERAL_LEVELS", census_area_m2="1.20")


def test_no_title_holds_refused():
    with pytest.raises(R.Refused):
        R.titles_holding("6", [("LT", "3", "0.35")])


def test_held_never_zero():
    with pytest.raises(R.Refused):
        R.statement("L-x", "E", "AT_LEAST", at_least="0", item="I")
    with pytest.raises(R.Refused):
        R.statement("L-x", "E", "BLANK_NAMED", at_least="0", item="I")
    with pytest.raises(R.Refused):
        R.blank(item="", why="w", areas_m2=["1"])
    with pytest.raises(R.Refused):
        R.blank(item="I", why="w", areas_m2=[])


def test_frame_rule_needs_gb_frame():
    with pytest.raises(R.Refused):
        R.governing_length({"roof frame": "5.65"}, "GB frame")


# ------------------------------------------------------------------ development villa (committed files only)
LEDGER = ROOT / "research" / "agents_t712" / "out" / "T712_LEDGER.json"
AREAS = ROOT / "research" / "agents_t712" / "out" / "T712_AREAS.json"


def _rebuild():
    sys.path.insert(0, str(ROOT / "research" / "agents_t712"))
    import t712_alsenan as A  # noqa: PLC0415
    return json.loads(json.dumps(A.build(), sort_keys=True, default=str))


def test_committed_ledger_rebuilds():
    assert _rebuild() == json.loads(LEDGER.read_text())


def test_census_20_of_20_and_no_range_no_zero():
    d = json.loads(LEDGER.read_text())
    assert d["census"] == {"lines": 20, "at_least": 17, "blank_named": 3}
    assert len({r["line_id"] for r in d["lines"]}) == 20
    for r in d["lines"]:
        assert r["at_most_m3"] is None and r["class_after"] == "HELD" and r["item"]
        if r["bound"] == "AT_LEAST":
            assert X(r["at_least_m3"]) > 0
        else:
            assert r["at_least_m3"] is None and r["d_id"].startswith("D-35")


def test_floors_contain_the_t658_floors_up_to_directed_rounding():
    d = json.loads(LEDGER.read_text())
    moved = {}
    for r in d["lines"]:
        if r.get("t658_floor") is not None:
            delta = X(r["vs_t658"])
            if abs(delta) > X("0.000001"):
                moved[r["line_id"]] = delta
            assert delta >= X("-0.000001")          # only R-T696-1 directed rounding may lower a T-658 floor
    assert moved == {"L-6bf14711798e5af93594": X("0.022500"),     # T-669 SE corner square (merged)
                     "L-e16c98075f69532a3dc7": X("0.000008")}     # exact ring area vs census centreline 1.8063


def test_measured_outlines_own_each_piece_once():
    a = json.loads(AREAS.read_text())
    assert a["overlaps_between_outlines"] == [] and a["outline_inside_column"] == []
    assert a["dxf_sha256_16"] == "9f9d1179a5d2a663"
    assert X(a["runs"]["BAND0013.1"]["area_m2"]) == X("0.03")      # the 0.10 x 0.30 junction remainder
    assert X(a["runs"]["BAND0012.1"]["area_m2"]) == X("0.45")      # 1.50 x 0.30 incl. the SE corner square


def test_per_designer_item_totals():
    d = json.loads(LEDGER.read_text())
    g = d["by_designer_item"]
    assert g["D-35"]["at_least_m3"] == "2.257981" and g["D-35"]["lines"] == 9
    assert g["D-33"]["at_least_m3"] == "2.841864" and g["D-33"]["lines"] == 8
    assert g["D-35 (court)"]["blank"] == 3 and g["D-35 (court)"]["at_least_m3"] == "0"
