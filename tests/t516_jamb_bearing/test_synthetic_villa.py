"""T-516 R-T516-1 on a synthetic villa (not the training villa): lintel jamb bearing from the masonry beside each jamb.

Villa S, lintel detail 'MIN 40 cm' (b_min 0.40), links 5/m, L2 bars 2Ø14 + 2Ø12 (kg/m 196/162 x 2 + 144/162 x 2 =
680/162 = 4.197531), L1 bars 2Ø12 + 2Ø10 (488/162 = 3.012346 kg/m).
  LA w 1.20, PRINTED bearings 0.45 / 0.50 (masonry 0.80 / 0.60): MEASURED both; L = 2.15 m exactly; links ceil(10.75)
     = 11 both bounds; straight ceiling 680/162 x 2.15 = 9.024691 kg.
  LB w 0.90, no printed bearing, masonry 0.55 to a column / 1.20 to a clean L corner: BOUNDED both; L in [1.70, 2.65];
     links [ceil 8.5 = 9, ceil 13.25 = 14]; ceiling 488/162 x 2.65 = 7.982716 kg.
  LC (adverse) w 1.00, no printed bearing, 0.30 m of masonry before a column (< 0.40) / 0.70 m: FLAGGED_DEFICIT at
     START, bearing at most 0.30 (never 0.40, never 0); L has no lower bound, at most 2.00 m; links at most 10.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t516"))

import t516_jamb_bearing as T  # noqa: E402

L1 = [(2, 144 / 162), (2, 100 / 162)]
L2 = [(2, 196 / 162), (2, 144 / 162)]


def end(side, a, stopper="END_OF_MASONRY", own=None, **kw):
    base = dict(side=side, available_m=a, own_band_m=a if own is None else own, stopper=stopper, stopper_id="",
                beyond_band_end="", search_capped="")
    base.update(kw)
    return base


def rec(oid, w, ends, bars=L1, **kw):
    return dict(opening_id=oid, floor="GF", decision="REQUIRED", width_m=w, bars=bars, links_rate=5,
                span_at_least_kg=1.0, ends=ends, **kw)


LA = rec("LA", 1.20, [end("START", 0.80, printed_bearing_m=0.45, printed_bearing_source="PRINTED S-01 detail A"),
                      end("END", 0.60, printed_bearing_m=0.50, printed_bearing_source="PRINTED S-01 detail A")], L2)
LB = rec("LB", 0.90, [end("START", 0.55, "COLUMN"), end("END", 1.20, beyond_band_end="ORTHOGONAL:W2", own=1.05)])
LC = rec("LC", 1.00, [end("START", 0.30, "COLUMN"), end("END", 0.70)])


def run(*rs):
    return {r["opening_id"]: r for r in T.census(list(rs), 0.40)["rows"]}


def test_normal_printed_bearings_by_hand():
    r = run(LA)["LA"]
    assert r["state"] == T.OK and [e["state"] for e in r["ends"]] == [T.MEASURED, T.MEASURED]
    assert r["length_lo_m"] == r["length_hi_m"] == 2.15
    assert r["links_lo"] == r["links_hi"] == 11
    assert r["straight_ceiling_kg"] == pytest.approx(680 / 162 * 2.15, abs=1e-9)


def test_normal_bounded_by_masonry_by_hand():
    r = run(LB)["LB"]
    assert r["state"] == T.OK and {e["state"] for e in r["ends"]} == {T.BOUNDED}
    assert (r["length_lo_m"], r["length_hi_m"]) == (1.7, 2.65)
    assert (r["links_lo"], r["links_hi"]) == (9, 14)
    assert r["straight_ceiling_kg"] == pytest.approx(488 / 162 * 2.65, abs=1e-9)
    assert r["t453_length_label"].startswith("LOWER BOUND")


def test_adverse_short_pier_flagged_never_the_minimum():
    r = run(LC)["LC"]
    s = r["ends"][0]
    assert r["state"] == T.FLAGGED and s["state"] == T.DEFICIT
    assert s["bearing_lo_m"] is None and s["bearing_hi_m"] == 0.3
    assert r["length_lo_m"] is None and r["links_lo"] is None
    assert r["length_hi_m"] == 2.0 and r["links_hi"] == 10
    assert "NOT BUILDABLE" in r["t453_length_label"]


def test_no_measure_held_not_zero():
    r = run(rec("LD", 1.0, [end("START", None), end("END", 0.9)]))["LD"]
    assert r["state"] == T.LHELD and r["length_lo_m"] is None and r["links_lo"] is None
    assert r["ends"][0]["state"] == T.HELD and r["ends"][0]["bearing_hi_m"] is None


@pytest.mark.parametrize("a", [350, 35.0, -0.1, float("nan"), True])
def test_units_refused(a):
    with pytest.raises(T.JambBearingError):
        run(rec("LE", 1.0, [end("START", a), end("END", 0.9)]))


def test_default_bearing_refused():
    with pytest.raises(T.JambBearingError):
        run(rec("LF", 1.0, [end("START", 0.9, printed_bearing_m=0.40, printed_bearing_source="usual practice"),
                            end("END", 0.9)]))


def test_printed_bearing_longer_than_masonry_refused():
    with pytest.raises(T.JambBearingError):
        run(rec("LG", 1.0, [end("START", 0.30, printed_bearing_m=0.40, printed_bearing_source="PRINTED x"),
                            end("END", 0.9)]))


def test_shared_pier_two_required_lintels():
    a = rec("P1", 0.8, [end("START", 0.9), end("END", 0.60, "OPENING", stopper_id="P2")])
    b = rec("P2", 0.8, [end("START", 0.60, "OPENING", stopper_id="P1"), end("END", 0.9)])
    r = run(a, b)
    assert r["P1"]["ends"][1]["state"] == T.DEFICIT and r["P2"]["ends"][0]["state"] == T.DEFICIT
    a2 = rec("P1", 0.8, [end("START", 0.9), end("END", 1.00, "OPENING", stopper_id="P2")])
    b2 = rec("P2", 0.8, [end("START", 1.00, "OPENING", stopper_id="P1"), end("END", 0.9)])
    r = run(a2, b2)
    assert r["P1"]["ends"][1]["state"] == T.BOUNDED and r["P1"]["ends"][1]["bearing_hi_m"] == 0.6


def test_shared_pier_read_differently_refused():
    a = rec("P1", 0.8, [end("START", 0.9), end("END", 1.00, "OPENING", stopper_id="P2")])
    b = rec("P2", 0.8, [end("START", 0.95, "OPENING", stopper_id="P1"), end("END", 0.9)])
    with pytest.raises(T.JambBearingError):
        run(a, b)


def test_held_neighbour_conditional_flag():
    a = rec("P1", 0.8, [end("START", 0.9), end("END", 0.50, "OPENING", stopper_id="NX")],
            neighbour_decisions={"NX": "HELD"})
    e = run(a)["P1"]["ends"][1]
    assert e["state"] == T.BOUNDED and e["bearing_hi_m"] == 0.5 and "IF it gets a lintel" in e["shared_pier"]


def test_oblique_junction_only_own_band_trusted():
    r = run(rec("LJ", 1.0, [end("START", 0.9), end("END", 0.64, own=0.14, beyond_band_end="OBLIQUE:W9")]))["LJ"]
    assert r["ends"][1]["state"] == T.HELD and r["state"] == T.LHELD
    r = run(rec("LK", 1.0, [end("START", 0.9), end("END", 0.9, own=0.5, beyond_band_end="HELD_JUNCTION:W9")]))["LK"]
    assert r["ends"][1]["state"] == T.BOUNDED and r["ends"][1]["bearing_hi_m"] is None
    assert r["state"] == T.OK and r["length_hi_m"] is None and r["straight_ceiling_kg"] is None


def test_search_limit_gives_no_ceiling():
    r = run(rec("LL", 1.0, [end("START", 3.0, "SEARCH_LIMIT", search_capped="YES"), end("END", 0.5)]))["LL"]
    assert r["state"] == T.OK and r["length_lo_m"] == 1.8 and r["length_hi_m"] is None


def test_record_shape_refused():
    with pytest.raises(T.JambBearingError):
        run(LB, dict(LB))
    with pytest.raises(T.JambBearingError):
        run(rec("LM", 1.0, [end("START", 0.9)]))


def test_precast_beside_never_governs():
    r = run(rec("LN", 1.0, [end("START", 0.20), end("END", 0.35)]))["LN"]
    p = r["precast_beside"]
    assert p["piece_m"] == 1.5 and p["fit_on_measured_piers"] == "FITS" and p["governs"].startswith("no")
    assert r["state"] == T.FLAGGED                    # the printed RC minimum still governs the census
    r = run(rec("LO", 1.0, [end("START", 0.10, "COLUMN"), end("END", 0.70)]))["LO"]
    assert r["precast_beside"]["fit_on_measured_piers"] == "DOES_NOT_FIT"


def test_order_and_mirror_invariant():
    m = rec("LBm", 0.90, [end("START", 1.20, beyond_band_end="ORTHOGONAL:W2", own=1.05), end("END", 0.55, "COLUMN")])
    a, b = run(LB)["LB"], run(m)["LBm"]
    assert (a["length_lo_m"], a["length_hi_m"], a["links_hi"]) == (b["length_lo_m"], b["length_hi_m"], b["links_hi"])
    x = run(LA, LB, LC)
    y = run(LC, LB, LA)
    assert {k: v["state"] for k, v in x.items()} == {k: v["state"] for k, v in y.items()}
