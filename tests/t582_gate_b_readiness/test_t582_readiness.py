"""T-582: GATE B READINESS (R-T582-1). A quantity class per line from its source verdict's state, a stated before, and
an address checked by element id. Synthetic villa V582 (not Alsenan; hand values): 4 RC lintels, B 0.20 x D 0.20 m,
printed minimum bearing 0.40 m each side:

  LA  w 1.00, built bearing printed 0.30 + 0.30          MEASURED            L 1.60 -> 0.20 x 0.20 x 1.60 = 0.064 m3
  LB  w 1.20, piers 0.90 / 0.50 >= 0.40                  BOUNDED_MIN_BEARING low 0.20 x 0.20 x 2.00 = 0.080 m3,
                                                                            high 0.20 x 0.20 x 2.60 = 0.104 m3
  LC  w 2.00, piers 0.60 / open (pier length not drawn)  BOUNDED_MIN_BEARING low 0.20 x 0.20 x 2.80 = 0.112 m3, OPEN
  LD  w 0.90, one jamb 0.10 against a column (< 0.40)    HELD_BY_NAME        beside [0.20 x 0.20 x 1.40, 0.20 x 0.20 x
                                                                            1.70] = [0.056, 0.068] m3
Hand totals: RELEASED 1 line 0.064 m3; AT_LEAST 2 lines low 0.080 + 0.112 = 0.192 m3, high 0.104 + 1 OPEN; HELD 1 line
blank, beside 0.056 .. 0.068 m3. Released total 0.064 m3, never 0.064 + 0.192.
Adverse: class missing, unsourced row, HELD printed 0, AT_LEAST with no low, renumbered id on another element, mirror
order of rows (totals equal). Then the training-villa readiness (research/agents_t582/out/T582_READINESS.json) must be
the rebuild and close on the figures its sources print."""

import json
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research/agents_t582"))
import t582_readiness as R      # noqa: E402

D = Decimal


def _row(lid, state, verdicts=("V-1",)):
    return {"line_id": lid, "source_state": state, "verdicts": list(verdicts)}


def _villa():
    spec = [("LA", "MEASURED", dict(value=0.064), None),
            ("LB", "BOUNDED_MIN_BEARING", dict(low=0.080, high=0.104), None),
            ("LC", "BOUNDED_MIN_BEARING", dict(low=0.112, high=None), None),
            ("LD", "HELD_BY_NAME", {}, {"low": 0.056, "high": 0.068})]
    rows = []
    for lid, st, q, beside in spec:
        r = _row(lid, st)
        c = R.classify(r)
        rows.append(dict(r, qclass=c, after=R.class_state(c, **q), beside_bound=beside))
    return rows


def test_hand_totals_per_class():
    t = R.class_totals(_villa())
    assert t["RELEASED"]["lines"] == 1 and D(str(t["RELEASED"]["released"])) == D("0.064")
    assert t["AT_LEAST"]["lines"] == 2 and D(str(t["AT_LEAST"]["low"])) == D("0.192")
    assert D(str(t["AT_LEAST"]["high"])) == D("0.104") and t["AT_LEAST"]["high_open_n"] == 1
    assert t["AT_LEAST"]["released"] == 0.0                     # an AT_LEAST low is never released
    assert t["HELD"]["blank_n"] == 1 and t["HELD"]["released"] == 0.0
    assert (D(str(t["HELD"]["beside_low"])), D(str(t["HELD"]["beside_high"]))) == (D("0.056"), D("0.068"))


def test_class_states():
    rows = {r["line_id"]: r for r in _villa()}
    assert rows["LA"]["after"] == {"class": "RELEASED", "measured_net": 0.064, "held_low": None, "held_high": None}
    assert rows["LB"]["after"]["class"] == "HELD" and rows["LB"]["after"]["held_low"] == 0.080
    assert rows["LC"]["after"]["held_high"] is None                # OPEN, never 0
    assert rows["LD"]["after"] == {"class": "HELD", "measured_net": None, "held_low": None, "held_high": None}


def test_mirror_order_same_totals():
    assert R.class_totals(_villa()) == R.class_totals(list(reversed(_villa())))


def test_pair_bound_counted_once():
    rows = [dict(_row(x, "HELD_BY_NAME"), qclass="HELD", after=R.class_state("HELD"),
                 beside_bound={"pair": ["P1", "P2"], "low": 0.060, "high": 0.079}) for x in ("P1", "P2")]
    t = R.class_totals(rows)
    assert (t["HELD"]["beside_low"], t["HELD"]["beside_high"]) == (0.06, 0.079)


@pytest.mark.parametrize("state", [None, "", "SOMETHING_ELSE"])
def test_adverse_class_missing_refused(state):
    with pytest.raises(R.ReadinessError, match="CLASS_MISSING"):
        R.classify(_row("LX", state))
    with pytest.raises(R.ReadinessError, match="CLASS_MISSING"):
        R.class_state(state)


def test_adverse_unsourced_refused():
    with pytest.raises(R.ReadinessError, match="CLASS_UNSOURCED"):
        R.classify(_row("LX", "HELD_BY_NAME", verdicts=()))


def test_adverse_held_printed_as_0_refused():
    with pytest.raises(R.ReadinessError, match="HELD_AS_0"):
        R.class_state("HELD", value=0.0)
    with pytest.raises(R.ReadinessError, match="HELD_AS_0"):
        R.class_state("HELD", low=0.0, high=0.0)


def test_adverse_at_least_needs_a_low():
    for lo in (None, 0.0):
        with pytest.raises(R.ReadinessError, match="AT_LEAST_NO_LOW"):
            R.class_state("AT_LEAST", low=lo)
    with pytest.raises(R.ReadinessError, match="AT_LEAST_HIGH_BELOW_LOW"):
        R.class_state("AT_LEAST", low=0.1, high=0.05)
    with pytest.raises(R.ReadinessError, match="RELEASED_BLANK"):
        R.class_state("RELEASED")


def _idx(*lines):
    return {l[0]: {"line_id": l[0], "item_code": l[1], "element_id": l[2], "unit": l[3]} for l in lines}


def test_remap_by_element():
    old = _idx(("L-1", "FIN.CEILING", "R1:ceiling", "m2"), ("L-2", "FIN.CEILING", "R2:ceiling", "m2"))
    new = _idx(("L-1", "FIN.CEILING", "R1:ceiling", "m2"), ("L-9", "FIN.CEILING", "R2:ceiling", "m2"),
               ("L-5", "FIN.WP.ROOF", "ROOF", "m2"))
    m = R.remap(old, new, ["L-1", "L-2", "L-7"])
    assert [(x["old"], x["new"], x["status"]) for x in m] == [("L-1", "L-1", "SAME_ID"), ("L-2", "L-9", "RENUMBERED"),
                                                              ("L-7", None, "NO_LINE")]
    assert R.check_remap(m, new)


def test_adverse_renumbered_id_on_another_element_refused():
    new = _idx(("L-9", "FIN.CEILING", "R2:ceiling", "m2"), ("L-5", "FIN.WP.ROOF", "ROOF", "m2"))
    bad = [{"old": "L-2", "new": "L-5", "element_id": "R2:ceiling"}]
    with pytest.raises(R.ReadinessError, match="REMAP_OTHER_ELEMENT"):
        R.check_remap(bad, new)
    with pytest.raises(R.ReadinessError, match="REMAP_UNKNOWN_ID"):
        R.check_remap([{"old": "L-2", "new": "L-404", "element_id": "R2:ceiling"}], new)


# ---- training villa ------------------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def built():
    return R.run()


def test_villa_output_is_the_rebuild(built):
    assert R.OUT_JSON.read_text(encoding="utf-8") == R.dumps(built)


def test_villa_lintel_classes(built):
    f = built["F_T580_1_lintel_classes"]
    pc = f["per_class"]
    assert (pc["RELEASED"]["lines"], pc["AT_LEAST"]["lines"], pc["HELD"]["lines"]) == (0, 6, 10)
    assert f["released_m3"] == {"before": 1.016, "after": 0.0, "change": -1.016}
    # AT_LEAST lows = B x D x (w + 0.80) on the 6 BEARING_OK lintels (T-516: 0.502 m3), 1 high OPEN (D-2F-01)
    assert pc["AT_LEAST"]["low"] == 0.502 and pc["AT_LEAST"]["high_open_n"] == 1
    assert D(str(pc["AT_LEAST"]["high"])) == D("0.13197") + D("0.14208") + D("0.11289") + D("0.246") + D("0.11348")
    # HELD beside closes on the T-524 set bound (residual 0): 8 single lintels + the D-GF-11 / 12 pair once
    assert [pc["HELD"]["beside_low"], pc["HELD"]["beside_high"]] == f["t524_set_bound_m3"] == [0.372692, 0.437542]
    assert pc["HELD"]["blank_n"] == 10 and pc["HELD"]["beside_none_n"] == 0
    for r in f["rows"]:
        assert r["verdicts"] and r["qclass"] in ("AT_LEAST", "HELD")
        assert r["after"]["measured_net"] is None


def test_villa_overlay_closes(built):
    o = built["overlay"]
    assert (o["stale"], o["no_before"], o["missing_line"], o["unexplained_conflicts"]) == (0, 0, 0, 0)
    assert o["flagged_rows"] == [] and o["lines"] == {"before": 4999, "after": 5123}
    assert o["t423_totals_changed"] == {}
    lin = o["t498_totals_changed"]["STR.CONC.LINTEL|m3"]["after"]
    assert lin["released"] == "0" and lin["held_low"] == "0.502" and lin["held_high_open_n"] == 1


def test_villa_l4ccc_and_identity(built):
    l4 = built["F_T580_3_l4ccc"]
    assert l4["before"] == l4["after"] == {"class": "HELD", "measured_net": None, "held_low": None, "held_high": None}
    g = built["F_T580_2_t498_identity"]["regenerated"]
    assert (g["base_lines"], g["added"], g["replaced"], g["expected_lines"]) == (4999, 74, 0, 5073)
    assert g["extends"] == "ARCH_TAKEOFF_V3.0.58" and g["method"] == "ARCH_TAKEOFF_V3.0.59"


def test_villa_t423_all_addressed(built):
    t = built["F_T580_4_t423_r2"]
    assert t["summary"] == {"lines": 24, "same_id": 24, "renumbered": 0, "formerly_unaddressable_now_addressed": 6,
                            "no_line": 0}
    assert t["slot"]["r2"]["module"] == "engine/source/arch_v3060.py"
    gaps = sorted(D(r["piece"].split("gap ")[1].split()[0]) for r in t["lines"] if r["piece"].startswith("CEILING"))
    assert gaps == sorted(D(x) for x in ("1.4227", "11.5808", "0.341845", "1.2410", "0.4472"))


def test_nothing_wired(built):
    assert built["candidate_files_touched"] == 0 and built["released_quantities_changed"] == 0
    assert json.loads(R.dumps(built))["rule"] == "R-T582-1"
