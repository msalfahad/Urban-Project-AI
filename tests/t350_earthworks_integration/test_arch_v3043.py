"""T-350: ARCH_TAKEOFF_V3.0.43 (the missing EARTHWORKS categories B1-02 / B1-03 / B1-04 as HELD BLANK zone lines with
the proved bound beside; held-range fixes of named buried concrete lines) on a hand-calculated NON-Alsenan villa (E350).

Villa E350, by hand (own figures; nothing from the development villa). Printed: 'founding not less than 1.20 m below the
existing ground' (a minimum, not the founding level); working space not printed; no bulking rule.
  Pits P1 2.00 x 2.00 = 4.00 m2 and P2 1.80 x 1.60 = 2.88 m2 overlap 0.20 x 1.60 = 0.32 m2 (counted once):
     union 4.00 + 2.88 - 0.32 = 6.56 m2 x 1.20 = 7.872 m3 = AT_LEAST bound beside a HELD line (never its quantity);
     every metre of unknown depth below 1.20 adds 6.56 m3.
  Lift pit: floor 'as per manufacturer' -> HELD, no bound.  Interior trench T1 wholly above EG while its soffit stays
     above EG -> ZERO_BY_BOUND under that condition (a bound, the line stays held blank).
  Backfill pits: HELD (excavation held).  Disposal: HELD (no bulking rule, fill re-use open).
  Strap blinding line S1 held 0.10 .. 0.20 m3 (an inadmissible deduction); merged ledger: 0 .. 1.50 x 0.20 x 1.00 = 0.30.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v30 as A30  # noqa: E402
from engine.source import arch_v3043 as A  # noqa: E402
from engine.source import boq_line as BL  # noqa: E402

PID, REV = "villa-e350", "f" * 64
DOCS = [{"file": "e350_struct.dxf", "sha256": "d" * 64}]


def _src(t):
    return {"task": t, "file": f"research/e350/{t}.csv", "sha256": t[-1] * 64, "merge_commit": "a" * 40,
            "checker_run": f"checker {t} Gate A PASS"}


def _ln(code, eid, ev, net=None, br=None, rfi=None, formula=None, unit="m3"):
    return BL.make_line(project_id=PID, revision_set_sha256=REV, item_code=code, unit=unit, evidence_state=ev,
                        measured_net=net, gross=net, bounded_range=br, element_id=eid, floor="FOUNDATION",
                        formula=formula or f"{code} {eid}", documents=DOCS, rule_id="G", rule_version="1", rfi=rfi,
                        notes="e")


def lines_3042():
    f1 = _ln("STR.CONC.FOOTING", "FTG:P1", "SOURCE_DERIVED", net=1.6, formula="2.00 x 2.00 x 0.40 = 1.6 m3")
    f2 = _ln("STR.CONC.FOOTING", "FTG:P2", "SOURCE_DERIVED", net=1.152, formula="1.80 x 1.60 x 0.40 = 1.152 m3")
    bl = _ln("STR.CONC.BLINDING", "BLD:PITS", "SOURCE_DERIVED", net=0.656, formula="6.56 x 0.10 = 0.656 m3")
    s1 = _ln("STR.CONC.BLINDING", "BLD:STRAP:S1", "BOUNDED_EXPOSURE",
             br={"low": 0.10, "high": 0.20, "basis": "strip less a ground-beam blinding deduction"},
             rfi={"question": "blinding under straps (D-1)", "unlocks": "BLD:STRAP:S1"},
             formula="HELD (never a value): strap blinding 0.10 .. 0.20 m3 (D-1)")
    gb = _ln("STR.CONC.GROUND_BEAM", "GB:T1", "SOURCE_DERIVED", net=0.48, formula="4.00 x 0.30 x 0.40 = 0.48 m3")
    floor = _ln("FIN.FLOOR.PORCELAIN", "R1:floor", "PROVISIONAL", net=40.0, unit="m2", formula="R1 = 40.0 m2")
    return [f1, f2, bl, s1, gb, floor]


def _id(lines, eid):
    return next(x["line_id"] for x in lines if x["location"]["element_id"] == eid)


def inputs(lines, zones=None, ranges=None, eg=None):
    f1, f2, bl, gb = (_id(lines, e) for e in ("FTG:P1", "FTG:P2", "BLD:PITS", "GB:T1"))
    z = [
        {"family": "B1-02", "zone": "Z1-PITS (2 pits, overlap once)", "element_id": "EW:B1-02:Z1-PITS",
         "floor": "FOUNDATION", "bound": "AT_LEAST", "at_least": 7.872, "coef_per_m": 6.56,
         "held_items": "formation only a minimum (printed 1.20); working space not printed",
         "bound_lines": [f1, f2, bl], "known_parts": "union 6.56 m2 x 1.20 (printed minimum)",
         "basis": "neat plans net of the overlap 0.32 m2", "eg_coef_per_m": "0.0 (RELATIVE_TO_EG)",
         "source_tasks": ["T-A", "T-B"]},
        {"family": "B1-02", "zone": "Z1-LIFT", "element_id": "EW:B1-02:Z1-LIFT", "floor": "FOUNDATION",
         "bound": "HELD", "held_items": "pit floor as per manufacturer; working space", "bound_lines": [],
         "source_tasks": ["T-A"]},
        {"family": "B1-02", "zone": "Z1-TRENCH-T1", "element_id": "EW:B1-02:Z1-T1", "floor": "FOUNDATION",
         "bound": "ZERO_BY_BOUND", "upper": 0.0, "condition": "the T1 soffit stays above the existing ground",
         "held_items": "condition: the T1 soffit stays above the existing ground", "bound_lines": [gb],
         "source_tasks": ["T-A"]},
        {"family": "B1-03", "zone": "Z1-PITS", "element_id": "EW:B1-03:Z1-PITS", "floor": "FOUNDATION",
         "bound": "HELD", "coef_per_m": 6.16, "held_items": "excavation held (formation, working space)",
         "bound_lines": [f1, f2, bl], "source_tasks": ["T-A"]},
        {"family": "B1-04", "zone": "ALL", "element_id": "EW:B1-04:ALL", "floor": "FOUNDATION", "bound": "HELD",
         "held_items": "no bulking rule; fill re-use open; excavation held", "bound_lines": [],
         "source_tasks": ["T-A"]},
    ]
    r = [{"line_id": _id(lines, "BLD:STRAP:S1"), "item_code": "STR.CONC.BLINDING",
          "expect": {"low": 0.10, "high": 0.20}, "low": 0.0, "high": 0.30,
          "basis": "0 (none drawn under straps) .. own strip 1.50 x 0.20 x 1.00",
          "why": "the ground-beam deduction sits at another level", "source_tasks": ["T-B"]}]
    return {"schema": A.INPUTS_SCHEMA, "project_id": PID, "sources": [_src("T-A"), _src("T-B")],
            "existing_ground": eg or {"status": "DERIVED", "datum": "+-0.00", "source": "corner marks"},
            "template_line": f1, "zones": z if zones is None else zones, "ranges": r if ranges is None else ranges}


def run(doc=None, l42=None):
    l42 = l42 or lines_3042()
    d = A.load_inputs(doc or inputs(l42), PID)
    ch, log = A.changes_for(d, l42)
    return l42, ch, log


# ================================================================================================ normal case
def test_hand_villa_lines_held_blank_with_bound_beside():
    l42, ch, log = run()
    l43, ident = A.integrate(l42, ch)
    ew = [ln for ln in l43 if ln["item_code"] in A.EW_CODES]
    assert len(ew) == 5 and log["lines_added"] == 5 and log["lines_changed"] == 1
    for ln in ew:
        assert ln["evidence_state"] == "BLOCKED_RFI" and ln["measured_net"] is None and ln["gross"] is None
        assert ln["bounded_range"] is None and ln["trade"] == "EARTHWORKS" and ln["rfi"]["question"]
    pits = next(ln for ln in ew if ln["location"]["element_id"] == "EW:B1-02:Z1-PITS")
    rec = pits["calculation"]["inputs"][A.REC_KEY]
    assert rec["at_least_m3"] == pytest.approx(6.56 * 1.20) and rec["coef_m3_per_m_depth"] == 6.56
    assert "at least 7.872 m3" in pits["calculation"]["formula"]
    assert ident["earthworks"]["by_family"] == {"B1-02": 3, "B1-03": 1, "B1-04": 1}
    assert ident["earthworks"]["at_least_m3"] == pytest.approx(7.872)
    # one line in the pits list of B1-02 and of B1-03: different families, no shared-zone line inside one family
    assert ident["earthworks"]["lines_in_two_zones"] == []


def test_range_fix_moves_only_the_held_range():
    l42, ch, _ = run()
    l43, _ = A.integrate(l42, ch)
    sid = _id(l42, "BLD:STRAP:S1")
    b, a = next(x for x in l42 if x["line_id"] == sid), next(x for x in l43 if x["line_id"] == sid)
    assert (a["bounded_range"]["low"], a["bounded_range"]["high"]) == (0.0, 0.30)
    for k in ("evidence_state", "measured_net", "gross", "rfi", "line_id", "item_code", "location"):
        assert a[k] == b[k]
    assert a["calculation"]["inputs"][A.REC_KEY]["was"]["high"] == 0.20


def test_every_other_line_byte_identical_and_totals(tmp_path):
    l42, ch, log = run()
    names, ident, led = A.write(tmp_path, l42, ch, log)
    assert ident["outside_rows_identical_to_v3_0_42"] == len(l42) - 1
    run_ = json.loads((tmp_path / "V3_0_43_RUN.json").read_text(encoding="utf-8"))
    moved = run_["totals_moved_by_code"]
    assert set(moved) == {"EARTH.EXCAVATION|m3", "EARTH.BACKFILL|m3", "EARTH.DISPOSAL|m3", "STR.CONC.BLINDING|m3"}
    assert moved["EARTH.EXCAVATION|m3"]["v3_0_43"]["released"] == 0 and \
        moved["EARTH.EXCAVATION|m3"]["v3_0_43"]["blocked_lines"] == 3
    b = moved["STR.CONC.BLINDING|m3"]
    assert b["v3_0_42"]["released"] == b["v3_0_43"]["released"] == 0.656
    assert b["v3_0_43"]["held_high"] == pytest.approx(0.30)
    assert led["integration_package"] is True and len(led["rows"]) == 6
    csv_ = (tmp_path / "V3_0_43_INTEGRATION_LEDGER.csv").read_text(encoding="utf-8")
    assert "BLOCKED_RFI" in csv_ and ",0.0," not in csv_


def test_mirror_order_of_zones_does_not_change_lines():
    l42 = lines_3042()
    d1 = inputs(l42)
    d2 = copy.deepcopy(d1)
    d2["zones"] = list(reversed(d2["zones"]))
    a = {x["after"]["line_id"]: A30.line_sha(x["after"]) for x in run(d1, l42)[1]}
    b = {x["after"]["line_id"]: A30.line_sha(x["after"]) for x in run(d2, l42)[1]}
    assert a == b


# ================================================================================================ adverse cases
def _z(l42, i, **kw):
    d = inputs(l42)
    d["zones"][i].update(kw)
    return d


@pytest.mark.parametrize("i,kw,msg", [
    (1, {"value": 5.0}, "HELD_WITH_VALUE"),                                    # a held zone given a value
    (0, {"at_least": 0.0}, "positive figure"),                                 # held written as 0
    (0, {"at_least": 7872000000.0}, "not a quantity in m3"),                   # mm3 for m3
    (2, {"condition": None}, "ZERO_BY_BOUND needs"),                           # a zero with no condition
    (1, {"at_least": 3.0}, "carries no bound figure"),                         # a held zone with a bound figure
    (0, {"upper": 9.0}, "no upper end"),                                       # minimum depth read as the founding level
    (0, {"family": "B1-09"}, "B1-02 / B1-03 / B1-04"),
    (0, {"bound": "ESTIMATE"}, "is not one of"),
    (0, {"source_tasks": ["T-X"]}, "no merged source"),
])
def test_adverse_zone_inputs_refused(i, kw, msg):
    l42 = lines_3042()
    with pytest.raises(A.InputsError, match=msg):
        A.load_inputs(_z(l42, i, **kw), PID)


def test_zone_named_twice_refused():
    l42 = lines_3042()
    d = inputs(l42)
    d["zones"].append(dict(d["zones"][0], element_id="EW:B1-02:OTHER"))
    with pytest.raises(A.InputsError, match="named twice"):
        A.load_inputs(d, PID)


def test_line_twice_in_one_zone_refused():
    l42 = lines_3042()
    f1 = _id(l42, "FTG:P1")
    with pytest.raises(A.InputsError, match="named twice"):
        A.load_inputs(_z(l42, 0, bound_lines=[f1, f1]), PID)


def test_stale_bound_line_refused():
    l42 = lines_3042()
    d = A.load_inputs(_z(l42, 0, bound_lines=["L-" + "9" * 20]), PID)
    with pytest.raises(A.InputsError, match="stale binding"):
        A.changes_for(d, l42)


def test_formula_never_concludes_on_a_figure():
    l42 = lines_3042()
    ch = A.changes_for(A.load_inputs(_z(l42, 1, basis="pit = 7.5 m3, net 2.5 m3"), PID), l42)[0]
    ln = next(c["after"] for c in ch if c["after"]["location"]["element_id"] == "EW:B1-02:Z1-LIFT")
    assert "pit equals 7.5 m3, net of 2.5 m3" in ln["calculation"]["formula"]
    assert ln["calculation"]["inputs"][A.REC_KEY]["basis"] == "pit = 7.5 m3, net 2.5 m3"
    d = A.load_inputs(inputs(l42, eg={"status": "DERIVED", "datum": "+-0.00", "source": "marks = 0.5 m3"}), PID)
    with pytest.raises(A.InputsError, match="conclude on a figure"):
        A.changes_for(d, l42)


def test_stale_range_and_valued_line_refused():
    l42 = lines_3042()
    d = inputs(l42)
    d["ranges"][0]["expect"] = {"low": 0.10, "high": 0.25}
    with pytest.raises(A.InputsError, match="stale binding"):
        A.changes_for(A.load_inputs(d, PID), l42)
    d = inputs(l42)
    d["ranges"][0].update(line_id=_id(l42, "BLD:PITS"))
    with pytest.raises(A.InputsError, match="held ranged line"):
        A.changes_for(A.load_inputs(d, PID), l42)
    d = inputs(l42)
    d["ranges"][0].update(low=0.4, high=0.3)
    with pytest.raises(A.InputsError, match="low"):
        A.load_inputs(d, PID)


def test_existing_ground_never_assumed():
    l42 = lines_3042()
    with pytest.raises(A.InputsError, match="never assumed"):
        A.load_inputs(inputs(l42, eg={"status": "HELD", "datum": "+-0.00", "source": "x"}), PID)
    with pytest.raises(A.InputsError, match="PRINTED / DERIVED / HELD"):
        A.load_inputs(inputs(l42, eg={"status": "ASSUMED", "source": "x"}), PID)
    A.load_inputs(inputs(l42, eg={"status": "HELD", "source": "no ground mark"}), PID)


def test_applied_once_and_check_catches_a_valued_earthworks_line():
    l42, ch, _ = run()
    l43, _ = A.integrate(l42, ch)
    with pytest.raises(A.InputsError, match="applied once|already carries"):
        A.changes_for(A.load_inputs(inputs(l42), PID), l43)
    bad = copy.deepcopy(l43)
    ln = next(x for x in bad if x["item_code"] == A.EXC)
    ln.update(evidence_state="SOURCE_DERIVED", measured_net=0.0, gross=0.0, rfi=None)
    with pytest.raises(ValueError, match="HELD BLANK"):
        A.check_earthworks(bad)


def test_project_mismatch_refused():
    l42 = lines_3042()
    with pytest.raises(A.InputsError, match="the run is"):
        A.load_inputs(inputs(l42), "villa-other")


# ================================================================================================ committed inputs
def test_committed_fill_builds_18_held_zones():
    sys.path.insert(0, str(ROOT / "research" / "agents_t350"))
    import t350_inputs as T
    d = T.build("p", template="L-" + "0" * 20)
    zs = d["zones"]
    assert len(zs) == 18
    assert sum(z["family"] == "B1-02" for z in zs) == 12 and sum(z["family"] == "B1-04" for z in zs) == 1
    assert {z["element_id"]: z["at_least"] for z in zs if z["at_least"]} == {
        "EW-T350:B1-02:Z1-PITS-24": 188.017207, "EW-T350:B1-02:Z1-POOL": 17.776576}
    assert all(z["at_least"] is None and z["upper"] is None for z in zs if z["bound"] == "HELD")
    A.load_inputs(d, "p")
    assert [(r["line_id"][:10], r["low"], r["high"]) for r in d["ranges"]] == [
        ("L-35382b18", 0.0, 0.912684), ("L-c823e0db", 0.0295, 0.2683)]
