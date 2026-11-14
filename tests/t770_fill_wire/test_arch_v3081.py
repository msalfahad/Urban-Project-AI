"""T-770 R-T770-1 / R-T770-2: fix-row wiring by line id (synthetic lines, no project data)."""
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
    (lambda r: r["rows"][1].update(after={"class": "RELEASED", "net": -1.0}), "no positive host"),   # R-T770-2 f
    (lambda r: r["rows"][2].update(after={"class": "RELEASED", "net": -1.0}), "only a STR.FORMWORK"),
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


# ------------------------------------------------------------------------------------------------ R-T770-2 (r2)
def _index2():
    return {"schema": A.INDEX_SCHEMA, "candidate_version": BASE, "lines": [
        _ix("L-a", "STR.FORMWORK", "m2", "HELD", el="FW:L-host1:FACES:G"),
        _ix("L-b", "STR.FORMWORK", "m2", "HELD", el="FW:L-host1:OQ10:G"),
        _ix("L-c", "STR.FORMWORK", "m2", "HELD", el="FW:L-host1:COVER:G"),
        _ix("L-d", "STR.CONC.BEAM", "m3", "HELD", el="BM-1#corner"),
        _ix("L-e", "STR.CONC.BEAM", "m3", "HELD", el="BM-2#corner"),
        _ix("L-f", "STR.CONC.BEAM", "m3", "HELD", el="BM-3"),
        _ix("L-g", "FIN.PAINT", "m2", "RELEASED", net=10.0, el="R"),
    ]}


BLANK = {"class": "HELD", "net": None, "low": None, "high": None}


def _set2(**over):
    rows = [
        # host faces 2 x (0.45 + 0.30) x 4.00 = 6.00 m2; a second face 1.50 m2; a cover deduction -0.12 m2
        _row("L-a", "STR.FORMWORK", "m2", BLANK, {"class": "RELEASED", "net": 6.0}, "ESTIMATE", "FW:L-host1:FACES:G"),
        _row("L-b", "STR.FORMWORK", "m2", BLANK, {"class": "RELEASED", "net": 1.5}, "ESTIMATE", "FW:L-host1:OQ10:G"),
        _row("L-c", "STR.FORMWORK", "m2", BLANK, {"class": "RELEASED", "net": -0.12}, "ESTIMATE",
             "FW:L-host1:COVER:G"),
        # two known corner pieces 0.0176 + 0.0300 m3 (< 0.05) under one safety line of max(1, 0.0476) = 1 m3
        _row("L-d", "STR.CONC.BEAM", "m3", BLANK, {"class": "IGNORED_SMALL", "size_m3": 0.0176,
                                                   "covered_by": "NEW:STR.CONC.SAFETY"}, el="BM-1#corner"),
        _row("L-e", "STR.CONC.BEAM", "m3", BLANK, {"class": "IGNORED_SMALL", "size_m3": 0.03,
                                                   "covered_by": "NEW:STR.CONC.SAFETY"}, el="BM-2#corner"),
        # 0.20 x 0.60 x 3.00 = 0.36 m3
        _row("L-f", "STR.CONC.BEAM", "m3", BLANK, {"class": "RELEASED", "net": 0.36}, el="BM-3"),
    ]
    d = {"schema": "DELIVERY_FIX_ROWS_V1", "task": "T-X", "candidate_version": BASE, "rows": rows,
         "safety_line": {"line_id": "NEW:STR.CONC.SAFETY", "item_code": "STR.CONC.SAFETY", "unit": "m3",
                         "after": {"class": "RELEASED", "net": 1.0}, "label": "SAFETY",
                         "basis": "ignored 0.0476 m3 < 1 m3 -> 1 m3"}}
    d.update(over)
    return d


def test_normal_netting_and_safety_line():
    base = _index2()
    new, applied = A.apply_index(base, _set2())
    by = {ln["line_id"]: ln for ln in new["lines"]}
    assert by["L-a"]["measured_net"] == pytest.approx(5.88) and "nets L-c -0.12" in by["L-a"]["fill_basis"]
    assert by["L-b"]["measured_net"] == 1.5                                   # the smaller host row is untouched
    assert by["L-c"]["class"] == "EXCLUDED" and "NETTED_INTO_HOST" in by["L-c"]["excluded_reason"]
    assert by["L-d"]["class"] == "EXCLUDED" and "IGNORED_SMALL" in by["L-d"]["excluded_reason"]
    assert by["L-d"]["measured_net"] is None                                  # never written as 0
    t = A.totals_by_code(new["lines"])
    assert t[("STR.FORMWORK", "m2")]["released"] == pytest.approx(6.0 + 1.5 - 0.12)   # trade sum unchanged by netting
    assert t[("STR.FORMWORK", "m2")]["lines"] == 2 and t[("STR.FORMWORK", "m2")]["blank"] == 0
    safety = [ln for ln in new["lines"] if ln["item_code"] == "STR.CONC.SAFETY"]
    assert len(safety) == 1 and safety[0]["measured_net"] == 1.0 and safety[0]["method_label"] == "SAFETY"
    assert by["L-d"]["excluded_reason"].endswith("logged in IGNORED_SMALL") and safety[0]["line_id"] in \
        by["L-d"]["excluded_reason"]
    assert len(new["lines"]) == len(base["lines"]) + 1 and by["L-g"] == base["lines"][6]
    assert all(min(x["measured_net"] or 0, 0) == 0 for x in new["lines"])  # no negative line anywhere


def _mut_net(lid, net):
    def f(d):
        for r in d["rows"]:
            if r["line_id"] == lid:
                r["after"] = dict(r["after"], net=net)
    return f


def _mut_after(lid, after):
    def f(d):
        for r in d["rows"]:
            if r["line_id"] == lid:
                r["after"] = after
    return f


@pytest.mark.parametrize("mutate, msg", [
    (_mut_net("L-c", -9.0), "below 0"),                                        # deduction larger than its host
    (lambda d: d["rows"].__setitem__(0, dict(d["rows"][0], element_id="FW:L-other:FACES:G")), "stale"),
    (_mut_after("L-d", {"class": "IGNORED_SMALL", "size_m3": 0.06, "covered_by": "NEW:STR.CONC.SAFETY"}), "0 < size"),
    (_mut_after("L-d", {"class": "IGNORED_SMALL", "size_m3": 0.0, "covered_by": "NEW:STR.CONC.SAFETY"}), "0 < size"),
    (_mut_after("L-d", {"class": "IGNORED_SMALL", "size_m3": 0.0176, "covered_by": "NEW:OTHER"}), "not a line"),
    (_mut_after("L-d", {"class": "IGNORED_SMALL", "size_m3": 0.0176}), "no added safety"),
    (lambda d: d["safety_line"]["after"].update(net=0.0476), "max\\(1 m3"),  # a safety line below 1 m3
    (lambda d: d.update(safety_line=None), "not a line"),                     # ignored pieces with no cover
])
def test_adverse_r_t770_2_refused(mutate, msg):
    d = _set2()
    mutate(d)
    with pytest.raises(A.FillError, match=msg):
        A.apply_index(_index2(), d)


def test_adverse_two_safety_lines_and_stale_package_base():
    a = _set2()
    b = {"schema": "DELIVERY_FIX_ROWS_V1", "task": "T-Y", "candidate_version": BASE,
         "rows": [_row("L-g", "FIN.PAINT", "m2", {"class": "RELEASED", "net": 10.0, "low": None, "high": None},
                       {"class": "RELEASED", "net": 9.0}, "ESTIMATE", "R")],
         "safety_line": dict(a["safety_line"])}
    pkg = {"schema": A.PACKAGE_SCHEMA, "base": "ARCH_TAKEOFF_V3.0.79", "row_bases": [BASE], "sets": [a, b]}
    with pytest.raises(A.FillError, match="second safety line"):
        A.check_package(pkg, "ARCH_TAKEOFF_V3.0.79")
    pkg["sets"] = [a]
    with pytest.raises(A.FillError, match="package built for"):
        A.check_package(pkg, "ARCH_TAKEOFF_V3.0.80")
    pkg["row_bases"] = []                                                    # a set on an undeclared older base
    with pytest.raises(A.FillError, match="rebuild"):
        A.check_package(pkg, "ARCH_TAKEOFF_V3.0.79")


def test_package_on_newer_base_rechecks_each_line():
    """normal: a set built on V3.0.78 applies on V3.0.79 when its lines did not move; adverse: one moved -> stale"""
    base = _index2()
    base["candidate_version"] = "ARCH_TAKEOFF_V3.0.79"
    pkg = {"schema": A.PACKAGE_SCHEMA, "base": "ARCH_TAKEOFF_V3.0.79", "row_bases": [BASE], "sets": [_set2()]}
    new, applied = A.apply_index(base, pkg)
    assert len(applied) == 6 and new["extends"] == "ARCH_TAKEOFF_V3.0.79"
    base["lines"][5].update({"class": "RELEASED", "measured_net": 0.30})     # the newer base moved L-f
    with pytest.raises(A.FillError, match="stale"):
        A.apply_index(base, pkg)


def _boq2(lid, code, unit, el):
    return {"line_id": lid, "item_code": code, "unit": unit, "evidence_state": "BLOCKED_RFI", "measured_net": None,
            "gross": None, "bounded_range": None, "location": {"element_id": el}, "notes": ""}


def test_boq_line_view_netting_and_safety():
    lines = [_boq2(x["line_id"], x["item_code"], x["unit"], x["element_id"]) for x in _index2()["lines"][:6]]
    new, applied = A.apply_boq_lines(lines, _set2(), BASE)
    by = {ln["line_id"]: ln for ln in new}
    assert by["L-a"]["evidence_state"] == "PROVISIONAL" and by["L-a"]["measured_net"] == pytest.approx(5.88)
    assert by["L-c"]["evidence_state"] == "EXCLUDED_WITH_REASON" and by["L-c"]["measured_net"] is None
    assert by["L-d"]["evidence_state"] == "EXCLUDED_WITH_REASON" and "IGNORED_SMALL" in by["L-d"]["notes"]
    s = new[-1]
    assert len(new) == 7 and s["item_code"] == "STR.CONC.SAFETY" and s["measured_net"] == 1.0
    assert s["evidence_state"] == "PROVISIONAL" and s["method_label"] == "SAFETY"
