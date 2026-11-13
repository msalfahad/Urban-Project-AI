"""T-699: one-sided bounds of a lintel line (R-T699-1). Villa V699 is hand-made (not the development villa): a 1.20 m
door in a 0.20 wall, lintel depth 0.20, no printed bearing (owner minimum 0.15 m). The last tests rebuild the
development-villa census of the 21 blank lintel lines from committed files only."""
from __future__ import annotations

import json
import sys
from decimal import Decimal as X
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t699"))
import t699_rules as R  # noqa: E402

B015 = R.b_min_of(None)


def door(**kw):
    d = {"id": "V699-D1", "width_m": "1.20", "B": "0.20", "D": "0.20", "form": "STRAIGHT",
         "ends": [{"side": "START", "a": "0.25", "stopper": "COLUMN"}, {"side": "END", "a": "0.50", "stopper": "COLUMN"}]}
    d.update(kw)
    return d


# ------------------------------------------------------------------ normal (hand)
def test_owner_bearing_when_none_printed():
    assert B015 == X("0.15") and R.b_min_of("0.40") == X("0.40")


def test_required_at_least_hand():
    s = R.one_sided(existence=R.REQUIRED, lintel=door(), b_min=B015)
    assert s["at_least"] == X("0.060000")           # (1.20 + 2 x 0.15) x 0.20 x 0.20
    assert s["at_most"] == X("0.078000")            # (1.20 + 0.25 + 0.50) x 0.04 (CEILING: both ends >= 0.15)
    assert s["conditional_lo"] is None and s["convention"] == "CEILING"


def test_existence_open_gives_at_most_only():
    s = R.one_sided(existence="OPEN", lintel=door(), b_min=B015)
    assert s["at_least"] is None                     # the line may be 0: no lower bound
    assert s["conditional_lo"] == X("0.060000") and s["at_most"] == X("0.078000")


def test_mirror_same_bounds():
    d = door()
    d["ends"] = [dict(d["ends"][1], side="START"), dict(d["ends"][0], side="END")]
    s = R.one_sided(existence=R.REQUIRED, lintel=d, b_min=B015)
    assert (s["at_least"], s["at_most"]) == (X("0.060000"), X("0.078000"))


def test_deficit_end_min_bearing_hand():
    d = door(ends=[{"side": "START", "a": "0.10", "stopper": "COLUMN"}, {"side": "END", "a": "0.90", "stopper": "COLUMN"}])
    s = R.one_sided(existence=R.REQUIRED, lintel=d, b_min=B015)
    assert s["at_least"] == X("0.054000")            # (1.20 + 0.15) x 0.04
    assert s["at_most"] == X("0.058000")             # (1.20 + 0.15 + 0.10) x 0.04
    assert s["convention"] == "MIN_BEARING"


def test_directed_rounding_high_up():
    d = door(width_m="1.00", B="0.15", ends=[{"side": "START", "a": "0.1000001", "stopper": "COLUMN"},
                                               {"side": "END", "a": "0.80", "stopper": "END_OF_MASONRY"}])
    m = R.at_most(d, b_min=B015)
    assert m["at_most_exact"] == X("0.037500003") and m["at_most"] == X("0.037501")   # half-up would print 0.0375


def test_shared_pier_neighbours():
    d = door(ends=[{"side": "START", "a": "0.70", "stopper": "OPENING", "stopper_id": "N1"},
                   {"side": "END", "a": "0.30", "stopper": "COLUMN"}])
    held = R.at_most(d, {"N1": "HELD"}, b_min=B015)["at_most"]       # full pier as ceiling
    rel = R.at_most(d, {"N1": "RELEASED"}, b_min=B015)["at_most"]    # the released neighbour keeps 0.15 of the pier
    assert held == X("0.088000") and rel == X("0.082000")            # 0.04 x (1.2 + 0.70 + 0.30) / (1.2 + 0.55 + 0.30)


def test_width_conflict_takes_the_largest_hi():
    d = door(width_m=None, width_range=["1.10", "1.20"],
             ends=[{"side": "START", "a": "0.60", "stopper": "COLUMN"}, {"side": "END", "a": "0.12", "stopper": "COLUMN"}])
    m = R.at_most(d, b_min=B015)
    # w 1.20 with the extra 0.10 taken from START: 0.04 x (1.20 + 0.15 + 0.12) = 0.0588
    assert m["at_most"] == X("0.058800") and m["width_used"] == X("1.20")
    assert R.conditional_lo(d, b_min=B015)["lo"] == X("0.050000")    # w 1.10 + 0.15 (END deficit)


def test_family_counts_a_shared_pier_once():
    rows = [{"id": "A", "at_most_exact": X("0.10")}, {"id": "B", "at_most_exact": X("0.09")}]
    assert R.family_at_most(rows, [("A", "B", "0.03")]) == X("0.160000")


# ------------------------------------------------------------------ adverse
def test_head_at_beam_soffit_is_no_lintel():
    s = R.one_sided(existence="EXCLUDED", lintel=door(), b_min=B015, excluded_by="K1 0.60 at the head")
    assert s["at_most"] is None and s["at_least"] is None and s["conditional_lo"] is None
    with pytest.raises(R.Refused):
        R.one_sided(existence="EXCLUDED", lintel=door(), b_min=B015)
    with pytest.raises(R.Refused):
        R.one_sided(existence="CONDITIONAL_EXCLUSION", lintel=door(), b_min=B015)


def test_missing_depth_held_never_zero():
    s = R.one_sided(existence=R.REQUIRED, lintel=door(D=None), b_min=B015)
    assert s["at_least"] is None and s["at_most"] is None and "never 0" in s["why_no_at_most"]
    assert "never 0" in s["why_no_lo"]


def test_open_end_lower_only():
    d = door(ends=[{"side": "START", "a": "0.40", "stopper": "COLUMN"}, {"side": "END", "a": "0.05", "stopper": "CROSSING_WALL"}])
    s = R.one_sided(existence=R.REQUIRED, lintel=d, b_min=B015)
    assert s["at_most"] is None and "OPEN" in s["why_no_at_most"] and s["at_least"] == X("0.054000")


def test_search_limit_counts_for_lo_not_hi():
    d = door(ends=[{"side": "START", "a": "0.40", "stopper": "COLUMN"}, {"side": "END", "a": "3.0", "stopper": "SEARCH_LIMIT"}])
    s = R.one_sided(existence=R.REQUIRED, lintel=d, b_min=B015)
    assert s["at_most"] is None and s["at_least"] == X("0.060000")
    d["ends"][1].update(extended="0.90", extended_stopper="COLUMN")
    assert R.one_sided(existence=R.REQUIRED, lintel=d, b_min=B015)["at_most"] == X("0.100000")   # 0.04 x 2.50


def test_unrecorded_pier_neighbour_open():
    d = door(ends=[{"side": "START", "a": "0.70", "stopper": "OPENING", "stopper_id": "N9"},
                   {"side": "END", "a": "0.30", "stopper": "COLUMN"}])
    assert R.one_sided(existence="OPEN", lintel=d, b_min=B015)["at_most"] is None


def test_curved_and_no_jambs_refused():
    assert R.one_sided(existence="OPEN", lintel=door(form="CURVED"), b_min=B015)["at_most"] is None
    s = R.one_sided(existence="OPEN", lintel=door(ends=[]), b_min=B015)
    assert s["at_most"] is None and s["conditional_lo"] == X("0.048000")      # w x B x D only, beside


def test_units_refused():
    with pytest.raises(R.Refused):
        R.at_most(door(width_m="1200"), b_min=B015)                         # mm passed as m
    with pytest.raises(R.Refused):
        R.at_most(door(B="20"), b_min=B015)
    with pytest.raises(R.Refused):
        R.b_min_of("150")
    with pytest.raises(R.Refused):
        R.one_sided(existence="MAYBE", lintel=door(), b_min=B015)


# ------------------------------------------------------------------ development villa rebuild (committed inputs only)
@pytest.fixture(scope="module")
def led():
    sys.path.insert(0, str(ROOT / "research" / "agents_t699"))
    import t699_alsenan as A
    return A.build()


def test_dev_21_lines_each_classed(led):
    assert len(led["lines"]) == 21 and led["lintel_census_before"]["blank"] == 21
    for r in led["lines"]:
        assert r["at_most_m3"] or r["at_least_m3"] or r["deciding_datum"]
        for k in ("at_most_m3", "at_least_m3", "conditional_lo_m3"):
            assert r[k] is None or X(r[k]) > 0                               # never 0
        if r["existence"] != R.REQUIRED:
            assert r["at_least_m3"] is None
    assert led["counts"] == {"AT_MOST": 16, "+AT_LEAST": 2, "NONE (datum named)": 3}


def test_dev_hand_rows(led):
    by = {r["opening"]: r for r in led["lines"]}
    assert by["W08"]["at_most_m3"] == "0.100000"        # 0.04 x (1.50 + (0.85 - 0.40 D-GF-03) + 0.55)
    assert by["W04"]["at_most_m3"] == "0.040000"        # 0.04 x (0.60 + 0.40 + 0): pier 0.15 already in D-GF-03
    assert by["L-GF-01"]["at_most_m3"] == by["L-GF-01"]["conditional_lo_m3"] == "0.072000"   # 0.04 x 1.80
    assert by["D-2F-02"]["at_most_m3"] == "0.056000"    # 0.04 x (0.90 + 0.2516 + 0.2484)
    assert by["D-GF-04"]["at_least_m3"] == "0.048000" and by["D-1F-06"]["at_least_m3"] == "0.036000"
    assert by["A-GF-01"]["at_most_m3"] is None and by["D-GF-14"]["cause_class"] == "MEASURABLE NOW"
    assert led["family"]["at_most_sum_m3"] == "1.321826" and led["family"]["at_least_sum_m3"] == "0.084000"


def test_dev_no_absolute_coordinates_or_names(led):
    txt = json.dumps(led)
    assert "chalet" not in txt.lower() and "alsenan" not in txt.lower()
