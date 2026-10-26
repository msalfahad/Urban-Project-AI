"""T-308 formwork r5 rules on a hand-calculated villa (V308, not Alsenan).

Villa V308 (by hand):
  Continuous beam CB, 0.20 x 0.50 (total depth), slab t 0.15, over three supports in two candidate runs:
    span S1 3.00 m -> run line L1, span S2 4.00 m -> run line L2.
    element method soffit 0.20 x L: S1 0.600, S2 0.800; sides 2 x L x (0.50 - 0.15): S1 2.100, S2 2.800.
    the source E rows count S2 twice (row RS soffits 0.6 + 0.8 + 0.8 = 2.200; row RD sides 2.1 + 2.8 + 2.8 = 7.700).
    r5: L1 0.600 + 2.100, L2 0.800 + 2.800; -0.800 soffit and -2.800 sides removed (R-T308-1).
  Stair flight F under band beam B1: lane 1.20, going 0.30, riser 0.15: sec = hypot(0.30, 0.15) / 0.30 = 1.118034
    plan 1.20 x 3.00 = 3.600; the band B1 0.40 x 1.20 = 0.480 of it; volume / thickness soffit row 3.600 x sec = 4.024922
    drawn soffit (3.600 - 0.480) x sec = 3.488266 on the stair line LS; 0.480 x sec = 0.536656 under B1, whose own beam
    row books its soffit 0.480 on LB: removed from the stair row (R-T308-2), the beam row keeps it.
  Column CX on line LX (BLOCKED_RFI): face 1.250 CALCULATED -> HELD, blank, held_from 1.250 (R-T308-5).
  Boundary beam run R1 (no candidate line in part 1; later added HELD as LBG): 0.960 formed alternative -> tied to LBG
  and HELD with it (R-T308-6 + R-T308-5).
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t308"))
import t308_rules as R  # noqa: E402

SEC = math.hypot(0.30, 0.15) / 0.30
STATE = {"L1": "PROVISIONAL", "L2": "PROVISIONAL", "LS": "SOURCE_DERIVED", "LB": "PROVISIONAL", "LX": "BLOCKED_RFI",
         "LBG": "BLOCKED_RFI", "LNA": "NOT_APPLICABLE_WITH_EVIDENCE"}


def row(fid, m2=None, status="CALCULATED", tie="TIED", line="", members="BEAM:CB", method="E", split_of="", lo=None,
        hi=None, held_from=None, evidence="villa V308 by hand", **kw):
    r = {"face_id": fid, "split_of": split_of, "status": status, "status_in": kw.pop("status_in", status),
         "tie": tie, "line_id": line, "members": members, "method": method, "alternative": kw.pop("alternative", ""),
         "m2": "" if m2 is None else f"{m2:.6f}", "lo": "" if lo is None else f"{lo:.6f}",
         "hi": "" if hi is None else f"{hi:.6f}", "held_from": "" if held_from is None else f"{held_from:.6f}",
         "evidence": evidence, "element": kw.pop("element", "BEAM"), "item": fid, "tie_reason": kw.pop("tie_reason", "")}
    r.update(kw)
    return r


def villa():
    return [
        row("RS.S1", 0.600, line="L1", split_of="RS", span_key="S1|soffit"),
        row("RS.S2", 0.800, line="L2", split_of="RS", span_key="S2|soffit"),
        row("RS.S2.DUP", 0.800, tie="DUPLICATE_IN_SOURCE", split_of="RS", members="BEAM:CB"),
        row("RD.S1", 2.100, line="L1", split_of="RD", span_key="S1|side"),
        row("RD.S2", 2.800, line="L2", split_of="RD", span_key="S2|side"),
        row("RD.S2.DUP", 2.800, tie="DUPLICATE_IN_SOURCE", split_of="RD", members="BEAM:CB"),
        row("RF.SOFFIT", round(3.12 * SEC, 6), line="LS", split_of="RF", members="PIECE:F", method="G", part="P3",
            element="STAIR"),
        row("RF.B1", round(0.48 * SEC, 6), tie="DUPLICATE_IN_SOURCE", piece_kind="DUPLICATE_IN_SOURCE",
            split_of="RF", members="PIECE:F", method="G", part="P3", element="STAIR"),
        row("RB1", 0.480, line="LB", members="BEAM:B1", method="G", plan_region="BAND:B1"),
        row("RX", 1.250, line="LX", members="COLUMN:CX", method="G"),
        row("RG", 0.960, status="ALTERNATIVE", alternative="OQ10_FORMED", tie="NO_CANDIDATE_LINE",
            members="BOUNDARY_GB:R1", method="E=G"),
    ]


def run(rows=None, state=STATE):
    return R.apply(villa() if rows is None else rows, state, retie={"BOUNDARY_GB:": "LBG"})


def by_id(out):
    return {r["face_id"]: r for r in out}


# ------------------------------------------------------------------------------------------------------- normal


def test_continuous_beam_each_span_once():
    o = by_id(run())
    assert o["RS.S2.DUP"]["r5_status"] == R.REMOVED and o["RS.S2.DUP"]["rule"] == "R-T308-1"
    assert o["RD.S2.DUP"]["r5_status"] == R.REMOVED
    t = R.totals(run(), R.r5_value)
    assert t[("CALCULATED", "", "E")][0] == pytest.approx(0.600 + 0.800 + 2.100 + 2.800, abs=1e-9)
    t4 = R.totals(run(), R.r4_value)
    assert t4[("CALCULATED", "", "E")][0] == pytest.approx(2.200 + 7.700, abs=1e-9)


def test_by_line_r4_before_r5_after():
    bl = R.by_line(run())
    assert bl["L2"][("CALCULATED", "", "E")][0] == pytest.approx(0.8 + 0.8 + 2.8 + 2.8, abs=1e-9)   # r4: twice
    assert bl["L2"][("CALCULATED", "", "E")][3] == pytest.approx(0.8 + 2.8, abs=1e-9)               # r5: once
    assert bl["L1"][("CALCULATED", "", "E")][0] == bl["L1"][("CALCULATED", "", "E")][3] == pytest.approx(2.7)


def test_stair_soffit_under_band_beam_once():
    o = by_id(run())
    assert o["RF.B1"]["r5_status"] == R.REMOVED and o["RF.B1"]["rule"] == "R-T308-2"
    assert o["RF.SOFFIT"]["r5_m2"] == pytest.approx(3.488266, abs=1e-6)
    assert o["RB1"]["r5_m2"] == pytest.approx(0.480, abs=1e-9) and o["RB1"]["r5_line"] == "LB"
    # r4 row 4.024922 = drawn 3.488266 + under the band 0.536656
    assert float(o["RF.SOFFIT"]["m2"]) + float(o["RF.B1"]["m2"]) == pytest.approx(3.6 * SEC, abs=2e-6)


def test_face_held_with_its_held_line():
    o = by_id(run())
    x = o["RX"]
    assert (x["r5_status"], x["r5_m2"], x["r5_held_from"]) == ("HELD", None, pytest.approx(1.250))
    assert "R-T308-5" in x["rule"]


def test_retie_to_added_line_then_held():
    g = by_id(run())["RG"]
    assert g["r5_line"] == "LBG" and g["r5_tie"] == "TIED"
    assert g["r5_status"] == "HELD" and g["r5_held_from"] == pytest.approx(0.960) and g["r5_m2"] is None
    assert g["rule"] == "R-T308-6 + R-T308-5"


def test_mirror_order_invariant():
    a = R.totals(run(), R.r5_value)
    b = R.totals(run(list(reversed(villa()))), R.r5_value)
    assert {k: [round(x, 9) for x in v[:3]] for k, v in a.items()} == \
        {k: [round(x, 9) for x in v[:3]] for k, v in b.items()}


def test_band_binding_normal():
    assert R.band_binding(0.376924, {"BAND7": 0.375010}) == "BAND7"


def test_union_replaces_named_rows():
    p1 = [row("RS", 2.200, tie="NAMED_NOT_TIED", members="AGGREGATE:BEAM"), row("RZ", 1.0, line="L1")]
    p2 = [row("RS.S1", 0.600, line="L1", split_of="RS"), row("RS.S2", 1.600, line="L2", split_of="RS")]
    u = R.union([("P1", p1), ("P2", p2)])
    assert sorted(r["face_id"] for r in u) == ["RS.S1", "RS.S2", "RZ"]


# ------------------------------------------------------------------------------------------------------ adverse


def test_shared_span_booked_twice_refused():
    rows = villa()
    rows[2] = row("RS.S2.RUN1", 0.800, line="L1", split_of="RS", span_key="S2|soffit")   # S2 also on run 1
    with pytest.raises(R.Refused, match="booked twice"):
        run(rows)


def test_soffit_under_band_on_both_rows_refused():
    rows = villa()
    rows[7] = row("RF.B1", round(0.48 * SEC, 6), line="LS", split_of="RF", members="PIECE:F", method="G",
                  plan_region="BAND:B1")
    with pytest.raises(R.Refused, match="plan region"):
        run(rows)


def test_face_without_drawn_surface_refused():
    rows = villa() + [row("RN", 0.300, line="L1", evidence="")]
    with pytest.raises(R.Refused, match="no drawn evidence"):
        run(rows)
    with pytest.raises(R.Refused, match="cannot stay"):
        R.guards([dict(row("RQ", 0.2, line="L1"), r5_status="CALCULATED", r5_tie="NO_FACE_INSIDE_MEMBER",
                       r5_m2=0.2, r5_line="L1")])


def test_held_face_as_zero_refused():
    rows = villa() + [row("RH", 0.0, status="HELD", line="L1")]
    with pytest.raises(R.Refused, match="HELD face carries a number"):
        run(rows)
    with pytest.raises(R.Refused, match="HELD with a number"):
        R.guards([dict(row("RH2", None, status="HELD", line="L1"), r5_status="HELD", r5_tie="TIED", r5_m2=0.0,
                       r5_line="L1")])


def test_face_on_not_applicable_line_refused():
    with pytest.raises(R.Refused, match="NOT_APPLICABLE"):
        run(villa() + [row("RNA", 0.5, line="LNA")])


def test_face_on_unknown_line_refused():
    with pytest.raises(R.Refused, match="not in the current candidate"):
        run(villa() + [row("RU", 0.5, line="L-unknown")])


def test_union_double_booking_refused():
    p1 = [row("RS", 2.200, line="L1")]
    p2 = [row("RS.S1", 0.600, line="L1", split_of="RS")]
    with pytest.raises(R.Refused, match="not a NAMED"):
        R.union([("P1", p1), ("P2", p2)])


def test_band_binding_adverse():
    assert R.band_binding(1.0, {"B1": 0.90}) is None                  # below 95 %
    assert R.band_binding(1.0, {"B1": 0.99, "B2": 0.01}) is None       # two bands touch the face
    assert R.band_binding(1.0, {}) is None
    with pytest.raises(R.Refused):
        R.band_binding(0.0, {"B1": 0.0})
