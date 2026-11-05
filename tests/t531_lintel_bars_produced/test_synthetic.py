"""T-531 R-T531-1 on a NON-Alsenan synthetic villa, by hand (kg/m = d^2 / 162).

Fixture villa 'S' (its own schedule prints everything): opening 1.20 m, EXACT bearing 0.20 m each end (printed), section
B 0.20 x D 0.25, 2 T12 bottom + 2 T10 top, links R8@150, printed end cover 0.025, end bend leg 0.15, link cover 0.025,
link hook total 0.10, first link 0.05 from each end face.
  L = 1.20 + 2 x 0.20 = 1.60 m; main bar cut = 1.20 + 2 x (0.20 - 0.025) + 2 x 0.15 = 1.85 m
  bottom 2 x 1.85 x 144/162 = 3.288889 kg; top 2 x 1.85 x 100/162 = 2.283951 kg
  links N = 1 + floor((1.60 - 2 x 0.05) / 0.15) = 1 + floor(10) = 11; cut 2 x ((0.20 - 0.05) + (0.25 - 0.05)) + 0.10
        = 0.80 m; 11 x 0.80 x 64/162 = 3.476543 kg
  lintel COMPLETE 9.049383 kg.
Measured-end variant (bearing 'MIN 0.40', piers 0.55 / 0.70 m): span 2 x 1.20 x (144 + 100)/162 = 3.614815 kg AT_LEAST;
  straight ceiling (1.20 + 0.55 + 0.70) x 488/162 = 7.380247 kg; links PROVISIONAL ceil(2.00 / 0.15) = 14 ..
  ceil(2.45 / 0.15) = 17.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t531"))
import t531_lintel_bars_produced as T  # noqa: E402

P = "PRINTED villa S lintel detail"


def full(**kw):
    r = {"opening_id": "S-01", "piece_state": "PRODUCED", "width_m": 1.20, "schedule_row": "S1",
         "band_lo_m": 1.01, "band_hi_m": 2.00, "bottom": "2Ø12", "top": "2Ø10", "links": "R8@150",
         "B_m": 0.20, "D_m": 0.25,
         "ends": [{"side": "START", "kind": "MASONRY", "a_m": 0.90, "b_min_m": 0.20},
                  {"side": "END", "kind": "MASONRY", "a_m": 0.60, "b_min_m": 0.20}],
         "bearing_exact_m": 0.20, "bearing_exact_m_source": P,
         "end_cover_m": 0.025, "end_cover_m_source": P, "bend_m": 0.15, "bend_m_source": P,
         "link_cover_m": 0.025, "link_cover_m_source": P, "link_hook_m": 0.10, "link_hook_m_source": P,
         "first_link_m": 0.05, "first_link_m_source": P}
    r.update(kw)
    return r


def measured(**kw):
    r = {"opening_id": "S-02", "piece_state": "PRODUCED", "width_m": 1.20, "schedule_row": "S1",
         "bottom": "2Ø12", "top": "2Ø10", "links": "R8@150", "B_m": 0.20, "D_m": 0.25,
         "ends": [{"side": "START", "kind": "MASONRY", "a_m": 0.55, "b_min_m": 0.40},
                  {"side": "END", "kind": "MASONRY", "a_m": 0.70, "b_min_m": 0.40}]}
    r.update(kw)
    return r


def comp(row, mark, part):
    return [c for c in row["components"] if c["mark"] == mark and c["part"] == part][0]


def test_complete_by_hand():
    r = T.lintel_bars(full())
    assert r["state"] == "COMPLETE" and r["held_parts"] == []
    b = sum(c["kg"] for c in r["components"] if c["mark"] == "B1" and c["state"] == "COMPUTED")
    t = sum(c["kg"] for c in r["components"] if c["mark"] == "T1" and c["state"] == "COMPUTED")
    assert b == pytest.approx(3.288889, abs=1e-6) and t == pytest.approx(2.283951, abs=1e-6)
    s1 = comp(r, "S1", "LINKS")
    assert s1["count"] == 11 and s1["cut_each_m"] == pytest.approx(0.80) and s1["kg"] == pytest.approx(3.476543, abs=1e-6)
    assert r["kg"] == pytest.approx(9.049383, abs=1e-6)
    assert comp(r, "B1", "LAPS")["state"] == "NOT_REQUIRED"


def test_measured_ends_at_least_with_ceiling():
    r = T.lintel_bars(measured())
    assert r["state"] == "AT_LEAST" and r["kg"] is None
    assert r["at_least_kg"] == pytest.approx(3.614815, abs=1e-6)
    assert r["ceiling_straight_kg_beside"] == pytest.approx(7.380247, abs=1e-6)
    s1 = comp(r, "S1", "LINKS")
    assert s1["state"] == "HELD" and s1["count_state"] == "PROVISIONAL"
    assert (s1["count_lo"], s1["count_hi"]) == (14, 17)
    for p in ("EXTENSION_START", "EXTENSION_END", "BEND_START", "BEND_END"):
        assert comp(r, "B1", p)["state"] == "HELD" and comp(r, "B1", p)["kg"] is None


def test_hook_not_printed_is_held():
    r = T.lintel_bars(full(bend_m=None, bend_m_source=None))
    assert r["state"] == "AT_LEAST"
    assert "B1 BEND_START" in r["held_parts"] and "T1 BEND_END" in r["held_parts"]
    # span + both extensions stay computed: 2 x (1.20 + 0.35) x 488/162
    assert r["at_least_kg"] == pytest.approx(1.55 * 488 / 162 + 3.476543, abs=1e-6)
    r2 = T.lintel_bars(full(link_hook_m=None, link_hook_m_source=None))
    assert comp(r2, "S1", "LINKS")["state"] == "HELD" and comp(r2, "S1", "LINKS")["count"] == 11


def test_flagged_column_end_bar_reaches_far_face():
    r = T.lintel_bars(measured(piece_state="FLAGGED", width_m=1.00, span_in_column_m=0.05, ends=[
        {"side": "START", "kind": "COLUMN", "a_m": 0.0, "b_min_m": 0.40, "strip_m": 0.05,
         "column": {"id": "C-X", "along_m": 0.60, "gap_alt_m": 0.01}},
        {"side": "END", "kind": "MASONRY", "a_m": 0.45, "b_min_m": 0.40}]))
    assert r["piece_state"] == "FLAGGED" and r["state"] == "AT_LEAST"
    assert r["w_net_m"] == pytest.approx(0.95)
    assert r["at_least_kg"] == pytest.approx(0.95 * 488 / 162, abs=1e-9)
    # concrete stops at the column face (<= 0); bars <= max gap 0.01 + depth 0.60 into the column
    assert r["concrete_length_hi_m"] == pytest.approx(0.95 + 0.0 + 0.45)
    assert r["bar_straight_hi_m"] == pytest.approx(0.95 + 0.61 + 0.45)
    assert r["ceiling_straight_kg_beside"] == pytest.approx(2.01 * 488 / 162, abs=1e-6)


def test_cross_wall_and_pier_ends():
    r = T.lintel_bars(measured(piece_state="FLAGGED", ends=[
        {"side": "START", "kind": "END_OF_MASONRY", "a_m": 0.25, "b_min_m": 0.40},
        {"side": "END", "kind": "PIER", "a_m": 0.30, "b_min_m": 0.40, "shared_with": "S-03"}]))
    assert r["bar_straight_hi_m"] == pytest.approx(1.75) and r["concrete_length_lo_m"] == pytest.approx(1.20)
    assert comp(r, "B1", "EXTENSION_END")["end_kind"] == "PIER"


def test_held_end_has_no_ceiling_never_zero():
    r = T.lintel_bars(measured(piece_state="FLAGGED", ends=[
        {"side": "START", "kind": "MASONRY", "a_m": 0.55, "b_min_m": 0.40},
        {"side": "END", "kind": "HELD", "a_m": None}]))
    assert r["ceiling_straight_kg_beside"] is None and r["bar_straight_hi_m"] is None
    assert comp(r, "B1", "LAPS")["state"] == "HELD"
    assert r["at_least_kg"] > 0
    capped = T.lintel_bars(measured(ends=[{"side": "START", "kind": "MASONRY", "a_m": 3.0, "b_min_m": 0.40,
                                           "capped": True},
                                          {"side": "END", "kind": "MASONRY", "a_m": 0.70, "b_min_m": 0.40}]))
    assert capped["ceiling_straight_kg_beside"] is None


def test_mirror_invariance():
    a = T.lintel_bars(measured())
    e = measured()["ends"]
    b = T.lintel_bars(measured(ends=[dict(e[1], side="START"), dict(e[0], side="END")]))
    assert a["at_least_kg"] == b["at_least_kg"]
    assert a["ceiling_straight_kg_beside"] == pytest.approx(b["ceiling_straight_kg_beside"])
    assert a["bar_straight_hi_m"] == b["bar_straight_hi_m"]


def test_line_two_parts_never_one_number():
    d = T.ledger([full(), measured(opening_id="S-02", piece_state="FLAGGED")])
    ln = d["line"]
    assert ln["produced"]["state"] == "COMPLETE" and ln["produced"]["kg"] == pytest.approx(9.049383, abs=1e-6)
    assert ln["flagged"]["state"] == "AT_LEAST" and ln["flagged"]["kg"] is None
    assert ln["state"] == "AT_LEAST" and "kg" not in ln


@pytest.mark.parametrize("bad", [
    dict(end_cover_m=0.03, end_cover_m_source=None),                  # defaulted cover
    dict(bend_m=0.12, bend_m_source="ASSUMED 12 d"),                   # defaulted bend
    dict(first_link_m=0.075, first_link_m_source="beam detail"),      # borrowed offset
    dict(width_m=1200),                                                 # mm entry
    dict(width_m=0),
    dict(width_m=-1.2),
    dict(width_m=None),
    dict(width_m=2.30),                                                 # outside its band
    dict(bottom="2 T12 + 1"),
    dict(links="5 links"),
    dict(links="R8@30"),                                                # 30 mm spacing
    dict(piece_state="HELD"),                                           # a HELD opening carries no figure
    dict(bearing_exact_m=0.20, bearing_exact_m_source="MIN.20cm read as exact"),
    dict(bearing_exact_m=0.95),                                         # printed bearing longer than the pier
    dict(end_cover_m=0.20),                                             # cover leaves no bar
])
def test_refused(bad):
    with pytest.raises(T.LintelBarsError):
        T.lintel_bars(full(**bad))


@pytest.mark.parametrize("ends", [
    [{"side": "START", "kind": "MASONRY", "a_m": 0.30, "b_min_m": 0.40},      # a deficit labelled as bearing
     {"side": "END", "kind": "MASONRY", "a_m": 0.70, "b_min_m": 0.40}],
    [{"side": "START", "kind": "COLUMN", "a_m": 0.50, "b_min_m": 0.40, "column": {"along_m": 0.3}},
     {"side": "END", "kind": "MASONRY", "a_m": 0.70, "b_min_m": 0.40}],        # not a deficit
    [{"side": "START", "kind": "SOMETHING", "a_m": 0.50},
     {"side": "END", "kind": "MASONRY", "a_m": 0.70, "b_min_m": 0.40}],
    [{"side": "START", "kind": "MASONRY", "a_m": 0.50, "b_min_m": 0.40}],      # one end only
    [{"side": "START", "kind": "END_OF_MASONRY", "a_m": None, "b_min_m": 0.40},
     {"side": "END", "kind": "MASONRY", "a_m": 0.70, "b_min_m": 0.40}],        # deficit without a
])
def test_bad_ends_refused(ends):
    with pytest.raises(T.LintelBarsError):
        T.lintel_bars(measured(ends=ends))


def test_unidentified_column_keeps_bar_ceiling_held():
    r = T.lintel_bars(measured(piece_state="FLAGGED", ends=[
        {"side": "START", "kind": "COLUMN", "a_m": 0.10, "b_min_m": 0.40, "column": {}},
        {"side": "END", "kind": "MASONRY", "a_m": 0.70, "b_min_m": 0.40}]))
    assert r["bar_straight_hi_m"] is None and r["ceiling_straight_kg_beside"] is None
    assert r["concrete_length_hi_m"] == pytest.approx(1.20 + 0.10 + 0.70)


def test_second_record_and_held_as_zero_refused():
    with pytest.raises(T.LintelBarsError):
        T.ledger([full(), full()])
    r = T.lintel_bars(measured())
    bad = dict(r, components=[dict(c, kg=0.0) if c["state"] == "HELD" else c for c in r["components"]])
    with pytest.raises(T.LintelBarsError):
        T.check_row(bad)
