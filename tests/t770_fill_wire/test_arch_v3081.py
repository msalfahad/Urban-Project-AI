"""T-770 R-T770-1: fix-row wiring by line id (synthetic lines, no project data)."""
import copy
import json

import pytest

from engine.source import arch_v3081 as A

BASE = "ARCH_TAKEOFF_V3.0.78"


def _ix(lid, code, unit, cls, net=None, lo=None, hi=None, el="E"):
    return {"line_id": lid, "item_code": code, "unit": unit, "class": cls, "element_id": el, "measured_net": net,
            "held_low": lo, "held_high": hi, "binding": None, "unbound_records": []}


def _index():
    return {"schema": A.INDEX_SCHEMA, "candidate_version": BASE, "lines": [
        _ix("L-1", "FIN.FLOOR.BED.DRY", "m3", "HELD", lo=0.49, hi=0.65, el="R1:bed"),
        _ix("L-2", "STR.FORMWORK", "m2", "HELD", el="B1:fw"),
        _ix("L-3", "FIN.PAINT", "m2", "RELEASED", net=56.0, el="R2:paint"),
        _ix("L-4", "STR.EARTH.DISPOSAL", "m3", "HELD", el="EW"),
        _ix("L-5", "STR.CONC.BEAM", "m3", "RELEASED", net=4.08, el="B1"),
    ]}


def _row(lid, code, unit, before, after, label="DEFAULT", el=None):
    return {"set": "S", "line_id": lid, "item_code": code, "unit": unit, "element_id": el, "before": before,
            "after": after, "label": label, "basis": "hand: dims x default"}


def _rows(*rows):
    return {"schema": "MAIN_CHAT_FIX_ROWS_V1", "candidate_version": BASE, "sets": ["S"], "rows": list(rows)}


def _normal():
    return _rows(
        # 14.0 m2 x 0.035 m (hand) = 0.49 m3 -> point 0.49 within the old range
        _row("L-1", "FIN.FLOOR.BED.DRY", "m3", {"class": "HELD", "net": None, "low": 0.49, "high": 0.65},
             {"class": "RELEASED", "net": 0.49}, el="R1:bed"),
        # host 4.08 m3 x 6.32 m2/m3 = 25.7856 m2
        _row("L-2", "STR.FORMWORK", "m2", {"class": "HELD", "net": None, "low": None, "high": None},
             {"class": "RELEASED", "net": 25.7856}, label="ESTIMATE", el="B1:fw"),
        _row("L-3", "FIN.PAINT", "m2", {"class": "RELEASED", "net": 56.0, "low": None, "high": None},
             {"class": "RELEASED", "net": 53.59}, label="ESTIMATE", el="R2:paint"),
        # a range stays HELD
        _row("L-4", "STR.EARTH.DISPOSAL", "m3", {"class": "HELD", "net": None, "low": None, "high": None},
             {"class": "HELD", "low": 105.6, "high": 115.5}, label="ESTIMATE"),
    )


def test_normal_index_apply_and_outside_identical():
    base = _index()
    keep = copy.deepcopy(base)
    new, applied = A.apply_index(base, _normal())
    assert base == keep                                     # the base is never mutated
    by = {ln["line_id"]: ln for ln in new["lines"]}
    assert len(applied) == 4 and new["candidate_version"] == A.METHOD and new["extends"] == BASE
    assert by["L-1"]["class"] == "RELEASED" and by["L-1"]["measured_net"] == 0.49 and by["L-1"]["held_low"] is None
    assert by["L-2"]["measured_net"] == pytest.approx(4.08 * 6.32) and by["L-2"]["method_label"] == "ESTIMATE"
    assert by["L-3"]["measured_net"] == 53.59
    assert by["L-4"]["class"] == "HELD" and (by["L-4"]["held_low"], by["L-4"]["held_high"]) == (105.6, 115.5)
    assert by["L-5"] == keep["lines"][4]                    # outside the set: byte-identical
    t = A.totals_by_code(new["lines"])
    assert t[("STR.FORMWORK", "m2")]["blank"] == 0 and t[("STR.EARTH.DISPOSAL", "m3")]["blank"] == 0


@pytest.mark.parametrize("mutate, msg", [
    (lambda r: r["rows"][0]["before"].update(low=0.40), "stale"),                    # base moved since the set
    (lambda r: r["rows"][0].update(unit="m2"), "stale"),                              # unit slip
    (lambda r: r["rows"][0].update(element_id="R9:bed"), "stale"),                    # mirrored / other element
    (lambda r: r["rows"][1].update(line_id="L-404"), "no base line"),
    (lambda r: r["rows"].append(dict(r["rows"][0])), "two rows"),
    (lambda r: r["rows"][0].update(label="GUESS"), "label"),
    (lambda r: r["rows"][0].update(basis=""), "basis"),
    (lambda r: r["rows"][3].update(after={"class": "HELD", "low": None, "high": None}), "low <= high"),
    (lambda r: r["rows"][3].update(after={"class": "HELD", "low": 9.0, "high": 1.0}), "low <= high"),
    (lambda r: r["rows"][1].update(after={"class": "RELEASED", "net": None}), "figure"),
    (lambda r: r["rows"][1].update(after={"class": "RELEASED", "net": -1.0}), "figure"),
    (lambda r: r.update(candidate_version="ARCH_TAKEOFF_V3.0.77"), "rebuild"),
])
def test_adverse_rows_refused(mutate, msg):
    rows = _normal()
    mutate(rows)
    with pytest.raises(A.FillError, match=msg):
        A.apply_index(_index(), rows)


def test_adverse_excluded_never_filled():
    base = _index()
    base["lines"][1]["class"] = "EXCLUDED"
    rows = _normal()
    rows["rows"][1]["before"]["class"] = "EXCLUDED"
    with pytest.raises(A.FillError, match="excluded"):
        A.apply_index(base, rows)


def _boq(lid, code, unit, state, net=None, br=None, el="E"):
    return {"line_id": lid, "item_code": code, "unit": unit, "evidence_state": state, "measured_net": net,
            "gross": None, "bounded_range": br, "location": {"element_id": el}}


def test_boq_line_view_provisional_and_bounded():
    lines = [_boq("L-1", "FIN.FLOOR.BED.DRY", "m3", "BOUNDED_EXPOSURE", br={"low": 0.49, "high": 0.65}, el="R1:bed"),
             _boq("L-2", "STR.FORMWORK", "m2", "BLOCKED_RFI", el="B1:fw"),
             _boq("L-3", "FIN.PAINT", "m2", "MEASURED", net=56.0, el="R2:paint"),
             _boq("L-4", "STR.EARTH.DISPOSAL", "m3", "BLOCKED_RFI", el="EW"),
             _boq("L-5", "STR.CONC.BEAM", "m3", "MEASURED", net=4.08, el="B1")]
    keep = json.dumps(lines, sort_keys=True)
    new, applied = A.apply_boq_lines(lines, _normal(), BASE)
    assert json.dumps(lines, sort_keys=True) == keep and len(applied) == 4
    by = {ln["line_id"]: ln for ln in new}
    assert by["L-1"]["evidence_state"] == "PROVISIONAL" and A.line_class(by["L-1"]) == "RELEASED"
    assert by["L-2"]["evidence_state"] == "PROVISIONAL"            # an ESTIMATE is never MEASURED
    assert by["L-4"]["evidence_state"] == "BOUNDED_EXPOSURE" and by["L-4"]["measured_net"] is None
    assert A.line_class(by["L-4"]) == "HELD" and by["L-4"]["bounded_range"]["low"] == 105.6
    assert by["L-5"] == json.loads(keep)[4]


def test_boq_line_view_stale_blank_vs_range():
    lines = [_boq("L-1", "FIN.FLOOR.BED.DRY", "m3", "BLOCKED_RFI", el="R1:bed")]   # blank, the set read a range
    rows = _rows(_normal()["rows"][0])
    with pytest.raises(A.FillError, match="stale"):
        A.apply_boq_lines(lines, rows, BASE)
