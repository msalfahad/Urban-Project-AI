"""T-645: stair finish hold census (R-T645-1). Synthetic straight flight "K645" (not the training villa): 17 risers of
0.165 / going 0.29 / width 1.20, by hand, with adverse cases (generated winder, HELD riser as 0, mm read as m, missing
count, curved going, mirror / order); then the development villa: the 31 HELD-blank B7 lines of the T-630 dry run classed
with fix rows (repository files only)."""
from __future__ import annotations

import os
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t645"))
import t645_rules as R  # noqa: E402
import t645_alsenan as A  # noqa: E402

D = Decimal
E6 = D("0.000001")

# ---- flight "K645" (hand) -------------------------------------------------------------------------------------------
# FFL 0.000 -> 2.805 (printed), 17 risers drawn: R = 2.805 / 17 = 0.165. Width 1.20 at every front edge; 16 goings of
# 0.290 (the 17th riser arrives on the upper floor). Tread marble 0.030 (UP-STAIR-006).
#   visible riser: 17 x 1.20 x (0.165 - 0.030) = 20.40 x 0.135 = 2.754 m2
#   flight: 16 x hypot(0.290, 0.165) = 16 x sqrt(0.084100 + 0.027225) = 16 x sqrt(0.111325) = 16 x 0.333654011 ..
#           = 5.338464 lm (6 dp)
#   with a column 0.05 proud at fronts 3 and 4 (riser faces inside it): widths 1.15 x 2: 20.30 x 0.135 = 2.7405 m2
W = ["1.20"] * 17


def test_k645_by_hand():
    r = R.finished_riser("0.000", "2.805", 17)
    assert r == D("0.165")
    assert R.visible_riser_m2(W, r, "0.030") == D("2.754")
    assert R.q(R.flight_lm(["0.290"] * 16, r)) == D("5.338464")
    notched = W[:2] + ["1.15", "1.15"] + W[4:]
    assert R.visible_riser_m2(notched, r, "0.030") == D("2.7405")


def test_k645_mirror_order_invariant():
    notched = W[:2] + ["1.15", "1.15"] + W[4:]
    r = D("0.165")
    assert R.visible_riser_m2(list(reversed(notched)), r, "0.030") == R.visible_riser_m2(notched, r, "0.030")
    # the same flight going down (levels given top first) is refused, never a negative area
    with pytest.raises(R.RuleError, match="rises"):
        R.finished_riser("2.805", "0.000", 17)


def test_k645_adverse_never_zero():
    with pytest.raises(R.RuleError, match="riser count missing"):
        R.finished_riser("0", "2.805", None)
    with pytest.raises(R.RuleError, match="mm refused"):
        R.finished_riser("0", "2805", 17)
    with pytest.raises(R.RuleError, match="mm read as m"):
        R.visible_riser_m2(["1200"] * 17, "0.165", "0.030")
    with pytest.raises(R.RuleError, match="never 0"):
        R.visible_riser_m2([], "0.165", "0.030")
    with pytest.raises(R.RuleError, match="not positive"):
        R.visible_riser_m2(["0"] + W[1:], "0.165", "0.030")
    with pytest.raises(R.RuleError, match="not above the tread"):
        R.visible_riser_m2(W, "0.030", "0.030")
    with pytest.raises(R.RuleError, match="mm read as m"):
        R.flight_lm(["290"] * 16, "0.165")


def test_winder_and_curved_never_generated():
    with pytest.raises(R.RuleError, match="generated winder refused"):
        R.winder_area(5, "1.20")
    for k in ("WINDER", "CURVED"):
        with pytest.raises(R.RuleError, match="never generated"):
            R.flight_lm(["0.29"] * 4, "0.165", kind=k)


def test_soffit_low_one_method_at_a_time():
    lo, tot = R.soffit_low({"O": ["10", "3.6"], "D": ["10.1", "3.2"]})
    assert tot == {"O": D("13.6"), "D": D("13.3")} and lo == D("13.3")
    # never the smaller row of each method mixed (10 + 3.2 = 13.2 would understate a real total)
    assert lo != D("13.2")


BLANK = {"class": "HELD", "measured_net": None, "held_low": None, "held_high": None}


def entry(**kw):
    e = {"line_id": "L-x", "item_code": "FIN.MARBLE.RISER", "class": "A_DRAWN", "cause": "c", "sources": ["s"],
         "handles": "h", "fix": {"kind": "SET", "before": dict(BLANK), "basis": "b",
                                 "after": {"class": "RELEASED", "measured_net": "2.754", "evidence": "DRAWING-CONFIRMED"}}}
    e.update(kw)
    return e


def test_census_adverse():
    R.check_entry(entry())
    with pytest.raises(R.RuleError, match="released as 0"):
        R.check_entry(entry(fix={"kind": "SET", "before": dict(BLANK), "basis": "b",
                                 "after": {"class": "RELEASED", "measured_net": "0", "evidence": "DRAWING-CONFIRMED"}}))
    with pytest.raises(R.RuleError, match="without drawn handles"):
        R.check_entry(entry(handles=None))
    with pytest.raises(R.RuleError, match="evidence status"):
        R.check_entry(entry(fix={"kind": "SET", "before": dict(BLANK), "basis": "b",
                                 "after": {"class": "RELEASED", "measured_net": "1"}}))
    held0 = {"kind": "SET", "before": dict(BLANK), "basis": "b",
             "after": {"class": "HELD", "measured_net": None, "held_low": "0", "held_high": "1.2"}}
    with pytest.raises(R.RuleError, match="HELD 0 refused"):
        R.check_entry(entry(**{"class": "C_OPEN", "fix": held0}))
    with pytest.raises(R.RuleError, match="HELD with a value"):
        R.check_entry(entry(**{"class": "C_OPEN", "fix": dict(held0, after={"class": "HELD", "measured_net": "1",
                                                                            "held_low": "1", "held_high": "2"})}))
    with pytest.raises(R.RuleError, match="shown with a value"):
        R.check_entry(entry(**{"class": "B_HELD", "fix": None, "measured_net": "0"}))
    with pytest.raises(R.RuleError, match="carries no quantity"):
        R.check_entry(entry(**{"class": "B_HELD"}))
    with pytest.raises(R.RuleError, match="carrier"):
        R.check_entry(entry(**{"class": "A_CARRIED", "fix": None}))
    with pytest.raises(R.RuleError, match="named cause"):
        R.check_entry(entry(cause=" "))


# ---- development villa ----------------------------------------------------------------------------------------------

@pytest.mark.skipif(os.environ.get("URBAN_T645_WRITE") != "1", reason="writer only on request")
def test_write_outputs():
    A.write_outputs()


def test_build_reproduces_committed_output():
    b = A.build()
    assert A.dumps(b) == A.OUT_JSON.read_text(encoding="utf-8")
    assert A.render_md(b) == A.OUT_MD.read_text(encoding="utf-8")


def test_alsenan_census():
    b = A.build()
    c = b["counts"]
    assert c["lines"] == 31 and len({e["line_id"] for e in b["lines"]}) == 31
    assert c["by_class"] == {"A_DRAWN": 10, "A_CARRIED": 9, "B_HELD": 6, "C_OPEN": 6}
    assert (c["released_rows"], c["bounded_rows"], c["stay_held_blank"]) == (10, 6, 6)
    by = {e["line_id"]: e for e in b["lines"]}
    rel = {lid: e["fix"]["after"]["measured_net"] for lid, e in by.items()
           if e.get("fix") and e["fix"]["after"]["class"] == "RELEASED"}
    # hand values (every term a drawn length, a printed level or a governing count):
    assert rel["L-8938aa3b25bf605e4b9d"] == "0.667"       # D1 4 x 1.15 x (0.70 / 4 - 0.03)
    assert rel["L-07e0855f961a839c1277"] == "1.886"       # MS1-U 13.80 x (2.0 / 12 - 0.03)
    assert rel["L-0f060e9951c28c4cf074"] == "1.8975"      # MS2-L 13.75 x (4.2 / 25 - 0.03)
    assert rel["L-099fe9fcfa5667fb8b99"] == "1.633929"    # RS-S 12.50 x (4.5 / 28 - 0.03)
    assert rel["L-16e0c6682725260f28e7"] == "0.751607"    # RS-A 5.75 x (4.5 / 28 - 0.03)
    assert rel["L-54eb280b9f7bf5eda65f"] == "3.775064"    # MS1-U 11 x hypot(0.3, 1/6)
    assert rel["L-a08d67ca292ab16ef9c3"] == "3.782209"    # MS2-L 11 x hypot(0.3, 0.168)
    assert rel["L-cccf54f717124cd750b3"] == "1.041933"    # D1 3 x hypot(0.3, 0.175)
    assert rel["L-509c6af3d162ae145108"] == "3.403367"    # RS-S 10 x hypot(0.3, 0.160714..)
    assert rel["L-406aae9a9854e015c45e"] == "1.361347"    # RS-A 4 x hypot(0.3, 0.160714..)
    assert b["released_by_code"] == {"FIN.MARBLE.RISER": "6.836036", "FIN.STAIR.FLIGHT": "13.36392"}
    # held stays blank or bounded, never 0; MS1-L is not released while C-ST-4 is open (owner 2026-10-22)
    for e in b["lines"]:
        if e["class"] in ("B_HELD", "A_CARRIED"):
            assert "fix" not in e
    ms1l = by["L-ecc450d6cc865617f8f6"]["fix"]["after"]
    assert (ms1l["class"], ms1l["held_low"], ms1l["held_high"]) == ("HELD", "1.564833", "1.886")
    assert by["L-48bb13e2f1c94d852a03"]["fix"]["after"]["held_high"] is None      # MS2-U last going drawn nowhere
    assert by["L-1fcec3328ccd0ea243d4"]["fix"]["after"]["held_low"] == "20.468807"  # ST-01 soffit, method D total
    assert by["L-c77e3887f7e348b1461d"]["fix"]["after"]["held_low"] == "4.460946"
    # winder turn and curved flight never valued
    for lid in ("L-b4660de0ddd98ad0ffc2", "L-820baecf7f726b4d8f1e", "L-c6724654ee4ccdb0c508",
                "L-fa534ec5f9dc14947899", "L-913cda8eb6d73f6e28cc", "L-30009d8e" + "b01996ec6399"):
        assert by[lid]["class"] == "B_HELD"
    # one flight, one valued line: every carried line names a carrier that is itself in scope or valued
    for e in b["lines"]:
        if e["class"] == "A_CARRIED":
            assert e["carrier"] in by and e["carrier"] != e["line_id"]


def test_no_coordinates_or_client_text():
    s = A.OUT_JSON.read_text(encoding="utf-8")
    for bad in ("Alsenan", "alsenan", "chalet"):
        assert bad not in s
