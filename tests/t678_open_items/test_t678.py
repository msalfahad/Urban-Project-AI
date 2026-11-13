"""T-678: lintel existence from a bounded soffit (R-T678-1), slab-top lower bound from a drawn head under a printed beam
(R-T678-2), open lintel end (R-T678-3), planted / annex column bounds. Villa V678 is hand-made (not the development
villa); the last tests rebuild the development-villa census from committed files only."""
from __future__ import annotations

import json
import sys
from decimal import Decimal as X
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t678"))
import t678_rules as R  # noqa: E402

R73 = R.R73


# ------------------------------------------------------------------ villa V678 (hand): storey +0.20 .. roof finished +3.80
def test_slab_bound_normal_hand():
    # window W1 head drawn +2.60 (tol 0.010) under beam K1 0.60; W2 head +2.50 (tol 0.002) under K1
    b = R.slab_top_lower_bound(heads=[
        {"id": "W1", "head_abs": "2.60", "tol": "0.010", "status": "DRAWING-CONFIRMED", "beam_depth": "0.60"},
        {"id": "W2", "head_abs": "2.50", "tol": "0.002", "status": "DRAWING-CONFIRMED", "beam_depth": "0.60"}],
        one_plane=True, finished_ceiling="3.80")
    assert b["state"] == "BOUNDED" and b["s_lo"] == X("3.190000") and b["governing"] == "W1"   # 2.60 - 0.01 + 0.60


def test_door_under_bounded_soffit_required_hand():
    s_lo = X("3.19")
    c_lo = R.soffit_lower_bound(s_lo, "0.40") - X("0.20")          # 2.59 above FFL +0.20
    st, spare, why = R.existence_bounded(head="2.10", tol=0, head_status="ASSUMED - OWNER-APPROVED", c_lo=c_lo,
                                         c_hi="3.20", d="0.15", bed="0.06")
    assert st == R.REQUIRED and spare == X("0.280000") and "OWNER-APPROVED" in why   # 2.59 - 2.10 - 0.21


def test_slab_piece_uses_deepest_beam_of_the_plane():
    assert R.soffit_lower_bound("3.19", slab_only=True, d_max="0.60") == X("2.590000")
    with pytest.raises(R.Refused):
        R.soffit_lower_bound("3.19", slab_only=True)


def test_threshold_named_when_bound_is_short():
    # window under the same beam as the bound source: decision lies inside the datum range
    st, spare, why = R.existence_bounded(head="2.40", tol="0.010", head_status="DRAWING-CONFIRMED", c_lo="2.39",
                                         c_hi="3.00", d="0.20", bed="0.06")
    assert st == R.HELD_BY_NAME and "rises 0.280000 m" in why            # 2.40 + 0.01 + 0.26 - 2.39


def test_member_serves_opening_flagged():
    st, _, _ = R.existence_bounded(head="2.40", tol=0, head_status="PRINTED", c_lo="2.40", c_hi="2.55", d="0.20",
                                   bed="0.06")
    assert st == R.FLAGGED


def test_no_head_held_never_zero():
    assert R.existence_bounded(head=None, tol=0, head_status=None, c_lo="3", c_hi="3", d="0.2", bed="0.06")[0] == R.HELD
    assert R.existence_bounded(head="2.1", tol=0, head_status="PRINTED", c_lo=None, c_hi=None, d="0.2",
                               bed="0.06")[0] == R.HELD


@pytest.mark.parametrize("kw", [
    {"head_status": "ASSUMED"},                    # a plain assumption cannot decide
    {"c_lo": "2590"},                              # mm passed as m
    {"tol": "19"},                                 # mm tolerance
    {"head": True},                                # bool
    {"c_lo": float("nan")},
])
def test_existence_refusals(kw):
    base = dict(head="2.10", tol=0, head_status="PRINTED", c_lo="2.59", c_hi="3.2", d="0.15", bed="0.06")
    base.update(kw)
    with pytest.raises(R.Refused):
        R.existence_bounded(**base)


@pytest.mark.parametrize("bad", [
    dict(one_plane=False),
    dict(heads=[{"id": "W1", "head_abs": "2.6", "tol": "0.01", "status": "DRAWING-CONFIRMED", "beam_depth": None}]),
    dict(heads=[{"id": "W1", "head_abs": "2.6", "tol": "0.01", "status": "ASSUMED", "beam_depth": "0.6"}]),
    dict(heads=[{"id": "W1", "head_abs": "2.6", "tol": "0.01", "status": "DRAWING-CONFIRMED", "beam_depth": "600"}]),
    dict(heads=[]),
])
def test_slab_bound_refusals(bad):
    kw = dict(heads=[{"id": "W1", "head_abs": "2.6", "tol": "0.01", "status": "DRAWING-CONFIRMED",
                      "beam_depth": "0.6"}], one_plane=True)
    kw.update(bad)
    with pytest.raises(R.Refused):
        R.slab_top_lower_bound(**kw)


def test_slab_bound_above_finished_is_a_contradiction():
    b = R.slab_top_lower_bound(heads=[{"id": "W1", "head_abs": "3.40", "tol": "0", "status": "PRINTED",
                                       "beam_depth": "0.60"}], one_plane=True, finished_ceiling="3.80")
    assert b["state"] == R.FLAGGED


# ------------------------------------------------------------------ position-resolved pieces (normal + mirror)
RUN = [("0", "0.5", "COLUMN", None), ("0.5", "1.3", "BEAM", "0.75"), ("1.3", "4.0", "BEAM", "0.40"),
       ("4.0", "4.4", "COLUMN", None)]


def _mirror(run, L=X("4.4")):
    return [(str(L - X(t)), str(L - X(f)), k, d) for f, t, k, d in reversed(run)]


@pytest.mark.parametrize("run,x0,x1", [(RUN, "2.0", "3.2"), (_mirror(RUN), "1.2", "2.4")])
def test_opening_under_shallow_piece_only(run, x0, x1):
    over = R.pieces_over(run, x0, x1)
    assert [d for *_, d in over] == ["0.40"]
    c = X("3.60") - X("0.40")                                    # storey 3.60
    assert R.existence_bounded(head="2.70", tol=0, head_status="PRINTED", c_lo=c, c_hi=c, d="0.20",
                               bed="0.06")[0] == R.REQUIRED            # 3.20 - 2.70 - 0.26 = 0.24
    cmin = X("3.60") - X("0.75")                                 # min over every piece (T-673): not decided
    assert R.existence_bounded(head="2.70", tol=0, head_status="PRINTED", c_lo=cmin, c_hi=c, d="0.20",
                               bed="0.06")[0] == R.HELD_BY_NAME


def test_pieces_over_empty_extent_refused():
    with pytest.raises(R.Refused):
        R.pieces_over(RUN, "2.0", "2.0")


# ------------------------------------------------------------------ R-T678-3 open end (adverse: no printed bearing)
def test_lintel_without_recorded_bearing_stays_held():
    q = R.lintel_m3_open_end({"id": "D1", "width_m": "0.90", "B": "0.20", "D": "0.20", "ends": [
        {"side": "START", "a": "0.55", "stopper": "COLUMN"},
        {"side": "END", "a": "0.05", "stopper": "OPENING", "stopper_id": "X:CROSSING"}]})
    assert q["lo_m3"] == X("0.052000") and q["hi_m3"] is None    # 0.04 x (0.90 + 0.40), high OPEN, never a ceiling
    q2 = R.lintel_m3_open_end({"id": "D2", "width_m": "0.90", "B": "0.20", "D": "0.20", "ends": [
        {"side": "START", "a": "0.10", "stopper": "COLUMN"},
        {"side": "END", "a": "0.05", "stopper": "OPENING", "stopper_id": "X"}]})
    assert q2["lo_m3"] == X("0.036000") and q2["hi_m3"] is None   # no bounded end: the opening span only, never 0


def test_t673_quantity_hand_v678():
    q = R73.lintel_m3({"id": "D3", "width_m": "1.00", "B": "0.15", "D": "0.20", "form": "STRAIGHT", "ends": [
        {"side": "START", "a": "0.25", "stopper": "COLUMN", "stopper_id": ""},
        {"side": "END", "a": "1.10", "stopper": "COLUMN", "stopper_id": ""}]}, {})
    assert (q["lo_m3"], q["hi_m3"]) == (X("0.042000"), X("0.049500"))   # 0.03 x 1.40 / 0.03 x 1.65


# ------------------------------------------------------------------ columns
def test_planted_column_to_beam_soffit_hand():
    c = R.column_m3("0.06", "0.08", "6.10", "8.90", "9.60", "0.60")
    assert (c["h_lo"], c["h_hi"], c["lo_m3"], c["hi_m3"]) == (X("2.2"), X("2.9"), X("0.132"), X("0.232"))


@pytest.mark.parametrize("args", [("0.08", "0.06", "1", "4", "4.3"), ("0.06", "0.08", "5", "4", "4.3"),
                                  ("0.06", "0.08", "0.25", "4000", "4300")])
def test_column_refusals(args):
    with pytest.raises(R.Refused):
        R.column_m3(*args)


# ------------------------------------------------------------------ development villa (committed files only)
@pytest.fixture(scope="module")
def led():
    import t678_alsenan as A
    return A.build()


def test_census_complete_each_line_once(led):
    rows = led["lintels"]
    assert len(rows) == 22 and len({r["line_id"] for r in rows}) == 22
    assert led["counts"] == {"open_bound_before": 22, "open_bound_after": 13, "measurable_now": 9}
    for r in rows:
        if r["cause"] == "OPEN BOUND":
            assert r["low_m3"] is None and r["missing_datum"]        # blank, never 0, the datum named
        else:
            assert X(r["low_m3"]) > 0 and r["existence"].startswith("REQUIRED")


def test_development_figures(led):
    t = led["lintel_totals_m3"]
    assert (t["low"], t["high"], t["high_of_closed_lines"]) == ("0.520000", None, "0.554224")
    assert sorted(t["open_high_lines"]) == ["D-1F-06", "D-GF-04"]
    q = {r["opening"]: (r["low_m3"], r["high_m3"]) for r in led["lintels"]}
    assert q["W13"] == ("0.080000", "0.108000") and q["D-GF-03"] == ("0.052000", "0.058000")
    assert q["D-GF-07"] == ("0.096000", "0.108000")
    assert led["annex_slab_top"]["s_lo"] == "3.544000" and led["annex_slab_top"]["governing"] == "W08"
    o = led["outline_778"]
    assert o["owner_line"] == "L-541c7e565bb93ecdb78b" and (o["lo_m3"], o["hi_m3"]) == ("0.182400", "0.350000")
    c = led["annex_C3"]
    assert (c["after_lo_m3"], c["after_hi_m3"]) == ("0.411750", "0.506250")


def test_778_line_exists_held_blank_in_v3065():
    ix = json.loads((ROOT / "research/agents_t671/out/LINE_INDEX_V3_0_65.json").read_text(encoding="utf-8"))
    ln = [x for x in ix["lines"] if x["line_id"] == "L-541c7e565bb93ecdb78b"][0]
    assert ln["element_id"] == "HL:PLANTED_COLUMN:PC-2F:CONCRETE" and ln["class"] == "HELD" and ln["measured_net"] is None


def test_no_absolute_coordinate_committed():
    txt = (ROOT / "research/agents_t678/out/T678_LEDGER.json").read_text(encoding="utf-8")
    import re
    assert not re.search(r"\d{5,}\.\d", txt)                    # only relative metres
