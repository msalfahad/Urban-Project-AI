"""T-673: lintel existence from a drawn head (R-T673-1), bearing at printed precision (R-T673-2), the RC lintel m3 range on
one masonry line (R-T673-3) and the census of the 49 HELD blank STR.CONC lines outside B10 in V3.0.64
(research/agents_t673). Hand villa "V673" (not the training villa) with normal and adverse cases, then the
development-villa ledger rebuilt from committed files."""
from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t673"))
sys.path.insert(0, str(ROOT / "research" / "agents_t524"))
import t673_rules as R  # noqa: E402

D = Decimal
OUT = ROOT / "research" / "agents_t673" / "out" / "T673_LEDGER.json"


def ex(**kw):
    base = dict(head_lo="2.10", head_hi="2.10", tol="0.010", fill_state="DEDUCTED", clear_heights=["3.00", "3.20"],
                d="0.20", bed="0.06", head_status="DRAWING-CONFIRMED")
    base.update(kw)
    return R.existence(**base)


def lintel(w="0.90", ends=None, B="0.20", Dd="0.20", form="STRAIGHT", oid="V-W1"):
    ends = ends or [{"side": "START", "a": "0.55", "stopper": "COLUMN", "stopper_id": ""},
                    {"side": "END", "a": "1.20", "stopper": "COLUMN", "stopper_id": ""}]
    return {"id": oid, "width_m": w, "B": B, "D": Dd, "form": form, "ends": ends}


# ---- R-T673-1 existence ------------------------------------------------------------------------------------------
def test_existence_normal_drawn_head():
    # villa V673 W1: head 2.10 drawn (tol 0.01), pieces 3.00 / 3.20, L1 D 0.20 + bed 0.06: 3.00 - 2.11 - 0.26 = 0.63
    st, spare, _ = ex()
    assert st == R.REQUIRED and spare == D("0.630000")


def test_existence_flips_inside_tolerance_is_held_by_name():
    st, spare, _ = ex(head_lo="2.73", head_hi="2.73", tol="0.020", clear_heights=["3.00"])
    assert st == R.HELD_BY_NAME and spare == D("-0.010000")
    st2, _, _ = ex(head_lo="2.73", head_hi="2.73", tol="0.020", clear_heights=["3.00"], head_status="PRINTED")
    assert st2 == R.REQUIRED            # a printed head carries no read tolerance


def test_existence_member_serves_opening_flagged():
    st, _, _ = ex(head_lo="2.85", head_hi="2.85", tol="0", clear_heights=["3.00"])
    assert st == R.FLAGGED


def test_existence_range_uses_the_high_head():
    # 3.00 - 2.76 - 0.26 = -0.02 (the high head decides); 3.00 - 2.74 - 0.26 = 0 (edge: REQUIRED)
    assert ex(head_lo="2.30", head_hi="2.76", tol="0", clear_heights=["3.00"])[0] == R.HELD_BY_NAME
    assert ex(head_lo="2.30", head_hi="2.74", tol="0", clear_heights=["3.00"])[0] == R.REQUIRED


@pytest.mark.parametrize("fill", ["ON_HELD_WALL", "IN_HELD_PIECE", "HELD"])
def test_existence_host_not_established_held(fill):
    assert ex(fill_state=fill)[0] == R.HELD


def test_existence_missing_head_held_never_zero():
    assert ex(head_lo=None, head_hi=None)[0] == R.HELD
    assert ex(clear_heights=[])[0] == R.HELD


@pytest.mark.parametrize("kw", [dict(tol="5"), dict(head_lo=True), dict(head_status="ASSUMED"),
                                dict(clear_heights=["3000"]), dict(head_lo="2.5", head_hi="2.1"),
                                dict(head_lo="nan")])
def test_existence_adverse_refused(kw):
    with pytest.raises(R.Refused):
        ex(**kw)


# ---- R-T673-2 bearing --------------------------------------------------------------------------------------------
def test_bearing_printed_precision_rounded_not_truncated():
    assert R.bearing_state("0.3996")[0] == R.BOUNDED      # rounds to 0.400
    assert R.bearing_state("0.3994")[0] == R.DEFICIT      # rounds to 0.399
    assert R.bearing_state("0.40")[0] == R.BOUNDED


# ---- R-T673-3 quantity ---------------------------------------------------------------------------------------------
def test_both_bounded_ceiling_range():
    q = R.lintel_m3(lintel(), {})
    assert q["lo_m3"] == D("0.068000")       # 0.20 x 0.20 x (0.90 + 0.80)
    assert q["hi_m3"] == D("0.106000")       # 0.04 x (0.90 + 0.55 + 1.20)
    assert q["convention"] == "CEILING"


def test_mirror_invariance():
    a = R.lintel_m3(lintel(), {})
    e = lintel()["ends"]
    b = R.lintel_m3(lintel(ends=[dict(e[1], side="START"), dict(e[0], side="END")]), {})
    assert (a["lo_m3"], a["hi_m3"]) == (b["lo_m3"], b["hi_m3"])


def test_deficit_column_end_agrees_with_r_t524_1():
    ends = [{"side": "START", "a": "0.12", "stopper": "COLUMN", "stopper_id": ""},
            {"side": "END", "a": "1.20", "stopper": "COLUMN", "stopper_id": ""}]
    q = R.lintel_m3(lintel(ends=ends), {})
    assert (q["lo_m3"], q["hi_m3"]) == (D("0.052000"), D("0.056800"))   # 0.04 x 1.30 / 0.04 x 1.42
    import t524_lintel_end_ownership as T524   # second route: the merged R-T524-1 code
    r = T524.assess_lintel({"id": "V-W1", "width_m": 0.90, "B": 0.20, "D": 0.20, "t453_length_m": 1.70,
                            "t453_concrete_m3": 0.068,
                            "ends": [{"side": "START", "state": "FLAGGED_DEFICIT", "available_m": 0.12,
                                      "stopper": "COLUMN", "host": {"id": "C-x", "along_m": 0.30}},
                                     {"side": "END", "state": "BOUNDED", "available_m": 1.20, "stopper": "COLUMN"}]})
    assert (round(r["concrete_lo_m3"], 6), round(r["concrete_hi_m3"], 6)) == (0.052, 0.0568)


def test_ceiling_pair_pier_once():
    # W1 (0.90) and W2 (0.90) share a 1.00 pier; outer ends 0.55 / 0.60: union hi = 0.04 x (0.55+0.90+1.00+0.90+0.60)
    e1 = [{"side": "START", "a": "0.55", "stopper": "COLUMN", "stopper_id": ""},
          {"side": "END", "a": "1.00", "stopper": "OPENING", "stopper_id": "V-W2"}]
    e2 = [{"side": "START", "a": "1.00", "stopper": "OPENING", "stopper_id": "V-W1"},
          {"side": "END", "a": "0.60", "stopper": "COLUMN", "stopper_id": ""}]
    nb = {"V-W1": "CEILING", "V-W2": "CEILING"}
    q1 = R.lintel_m3(lintel(ends=e1), nb)
    q2 = R.lintel_m3(lintel(ends=e2, oid="V-W2"), nb)
    rem = R.pier_remainder("1.00", "0.20", "0.20")
    assert rem == D("0.008000")
    assert q1["hi_m3"] + q2["hi_m3"] + rem == D("0.158000")
    assert q1["lo_m3"] + q2["lo_m3"] == D("0.136000")


def test_released_neighbour_takes_its_minimum_of_the_pier():
    e = [{"side": "START", "a": "0.50", "stopper": "OPENING", "stopper_id": "V-W0"},
         {"side": "END", "a": "1.20", "stopper": "COLUMN", "stopper_id": ""}]
    q = R.lintel_m3(lintel(ends=e), {"V-W0": "RELEASED"})
    assert q["state"] == "HELD_BY_NAME"
    assert (q["lo_m3"], q["hi_m3"]) == (D("0.052000"), D("0.056000"))   # 0.04 x 1.30 / 0.04 x (1.30 + 0.10)


def test_held_neighbour_full_pier_is_the_ceiling():
    e = [{"side": "START", "a": "0.50", "stopper": "OPENING", "stopper_id": "V-W0"},
         {"side": "END", "a": "1.20", "stopper": "COLUMN", "stopper_id": ""}]
    q = R.lintel_m3(lintel(ends=e), {"V-W0": "HELD"})
    assert q["hi_m3"] == D("0.104000")


def test_search_capped_end_open_or_extended():
    e = [{"side": "START", "a": "0.55", "stopper": "COLUMN", "stopper_id": ""},
         {"side": "END", "a": "3.00", "stopper": "SEARCH_LIMIT", "stopper_id": ""}]
    assert R.lintel_m3(lintel(ends=e), {})["hi_m3"] is None
    e[1]["extended"] = "4.2188"
    assert R.lintel_m3(lintel(ends=e), {})["hi_m3"] == D("0.226760")   # 0.04 x (0.90 + 0.55 + 4.219)


def test_adverse_door_wider_than_its_schedule_mark():
    # a 1.05 door read under an L1 (0 - 100) mark: the band is re-read from the width, never the mark
    sys.path.insert(0, str(ROOT / "research" / "agents_t453"))
    import t453_material_ledger as T
    rows = [{"row": "L1", "lo_mm": 0.0, "hi_mm": 1000.0, "d_m": 0.20, "bottom": "", "top": "", "stirrups": ""},
            {"row": "L2", "lo_mm": 1010.0, "hi_mm": 2000.0, "d_m": 0.25, "bottom": "", "top": "", "stirrups": ""}]
    b, _ = T.band(1.05, rows)
    assert b["row"] == "L2"
    q = R.lintel_m3(lintel(w="1.05", Dd=str(b["d_m"])), {})
    assert q["lo_m3"] == D("0.092500")                      # 0.20 x 0.25 x 1.85, not 0.20 x 0.20 x 1.85
    b2, why = T.band(1.005, rows)                            # in the unprinted 1.00 .. 1.01 gap
    assert b2 is None and "unprinted" in why
    with pytest.raises(R.Refused):
        R.lintel_m3(lintel(w="3.50", form="ABOVE_LAST_BAND"), {})


def test_adverse_curved_head_flagged():
    with pytest.raises(R.Refused):
        R.lintel_m3(lintel(form="CURVED"), {})


@pytest.mark.parametrize("bad", [dict(w="900"), dict(w="0"), dict(B="200"), dict(Dd="0.02")])
def test_adverse_units(bad):
    with pytest.raises(R.Refused):
        R.lintel_m3(lintel(**bad), {})


def test_adverse_unrecorded_neighbour_and_ends():
    e = [{"side": "START", "a": "0.50", "stopper": "OPENING", "stopper_id": "V-W9"},
         {"side": "END", "a": "1.20", "stopper": "COLUMN", "stopper_id": ""}]
    with pytest.raises(R.Refused):
        R.lintel_m3(lintel(ends=e), {})
    with pytest.raises(R.Refused):
        R.lintel_m3(lintel(ends=[e[1], dict(e[1])]), {})
    with pytest.raises(R.Refused):
        R.pier_remainder("0.70", "0.20", "0.20")


def test_census_row_and_totals_guards():
    with pytest.raises(R.Refused):
        R.census_row(member="x", line_id="L-1", cause="OPEN BOUND", cause_ref="r", fix="f", lo="0")
    with pytest.raises(R.Refused):
        R.census_row(member="x", line_id="L-1", cause="DESIGNER ITEM", cause_ref="", fix="f")
    with pytest.raises(R.Refused):
        R.census_row(member="x", line_id="L-1", cause="MEASURABLE NOW", cause_ref="r", fix="f")
    with pytest.raises(R.Refused):
        R.census_row(member="x", line_id="L-1", cause="SOMETHING", cause_ref="r", fix="f")
    with pytest.raises(R.Refused):
        R.family_total([{"lo_m3": None, "hi_m3": None}])
    assert R.family_total([{"lo_m3": "0.05", "hi_m3": None}, {"lo_m3": "0.02", "hi_m3": "0.03"}]) == \
        (D("0.070000"), None)


# ---- development villa (committed inputs only) -------------------------------------------------------------------
@pytest.fixture(scope="module")
def led():
    import t673_alsenan as A
    return A.build()


def test_census_count_equals_master(led):
    ix = json.loads((ROOT / "research" / "agents_t668" / "out" / "LINE_INDEX_V3_0_64.json").read_text())
    want = {ln["line_id"] for ln in ix["lines"] if ln["item_code"] in ("STR.CONC.LINTEL", "STR.CONC.STAIR")
            and ln["class"] == "HELD" and ln["measured_net"] is None and ln["held_low"] is None}
    got = [r["line_id"] for r in led["lintels"] + led["stairs"]]
    assert len(want) == 49 and len(got) == 49 and set(got) == want
    assert led["count"] == {"lintel": 44, "stair": 5, "total": 49}
    assert led["by_cause"] == {"DESIGNER ITEM": 10, "MEASURABLE NOW": 17, "OPEN BOUND": 22}


def test_measurable_lintels_by_hand(led):
    q = {r["opening"]: (r["low_m3"], r["high_m3"]) for r in led["lintels"] if r["cause"] == "MEASURABLE NOW"}
    assert q["W07"] == ("0.056000", "0.134000")          # 0.04 x 1.40 / 0.04 x (0.60 + 0.400 + 2.350)
    assert q["W24"] == ("0.094000", "0.268280")          # 0.04 x 2.35 / 0.04 x (1.55 + 0.938 + 4.219)
    assert q["W16"] == ("0.078000", "0.081732")          # pier 0.4933 - W15's 0.40 = 0.0933
    assert q["W09"] == ("0.092000", "0.118000")          # pier 1.05 - W10's 0.40 = 0.65
    assert q["A-1F-01"] == ("0.054000", "0.118500")
    assert len(q) == 16
    t = led["totals_m3"]["lintel_measurable_now"]
    assert (t["low"], t["high"]) == ("0.925000", "1.496412")
    assert led["pier_remainders"][0]["pair"] == ["W19", "W20"] and led["pier_remainders"][0]["hi_m3"] == "0.003000"


def test_held_never_zero_and_named(led):
    for r in led["lintels"] + led["stairs"]:
        assert r["low_m3"] != "0.000000"
        assert r["cause_ref"] and r["fix"]
        if r["cause"] != "MEASURABLE NOW" and r["line_id"] != "L-7863355dfcb68a681d2d":
            assert r["low_m3"] is None and r["high_m3"] is None


def test_stairs(led):
    s = {r["element_id"]: r for r in led["stairs"]}
    st3 = s["P-C:SCOPE:STAIRS:GROUND:CC-5ab1872c70:FLIGHTS"]
    assert st3["cause"] == "MEASURABLE NOW" and st3["low_m3"] == "0.355017" and st3["high_m3"] is None
    st1 = s["P-C:SCOPE:STAIRS:GF:CC-7390ea1139:FLIGHTS"]
    assert (st1["cause"], st1["low_m3"], st1["high_m3"]) == ("DESIGNER ITEM", "1.213429", "1.434413")


def test_committed_ledger_is_the_rebuild(led):
    assert json.loads(OUT.read_text(encoding="utf-8")) == json.loads(json.dumps(led, sort_keys=True, default=str))
