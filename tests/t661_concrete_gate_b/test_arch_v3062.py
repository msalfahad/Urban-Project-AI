"""T-661: ARCH_TAKEOFF_V3.0.62 (CONCRETE_GATE_B_V1, R-T661-1) on the hand-calculated NON-Alsenan villa V661 (own
figures, no drawing). Printed: minimum excavation 1.50 m below EG, footing stack 0.17 m, single-row detail 'LESS THAN
2.5m' (footing underside .. GB line); neck tops at +0.95.

  N1 neck, section 0.30 x 0.50 = 0.15 m2, footing H 0.60, generic HELD 0.075 .. 0.375 (h 0.50 .. 2.50):
      h low = 0.95 + 1.50 - 0.17 - 0.60 = 1.68 -> 0.252; h high = 2.50 - 0.60 = 1.90 -> 0.285 m3 (BOUND).
  N2 lift neck, section 0.18 m2, generic HELD 0.09 .. 0.45, pit raft depth by the supplier: AT_LEAST 0.18 x 1.55 =
      0.279 m3 beside, blank (LOWER_ONLY); the generic bound set aside with its reason.
  B1 beam piece 0.30 x 0.60, round 0.15 x 0.15 on the outer top corner, face to face 2.40 (HELD 0.30 .. 0.45):
      2.40 x (0.30 x 0.60 - 0.15^2 x (1 - pi/4)) = 0.432 - 0.0115885 = 0.420412 m3 (VALUE, re-measured).
  B2 strip 0.20 x 3.00 = 0.60 m2, no mark / bars / depth, HELD 0.10 .. 0.30 (schedule envelope): HELD BLANK, plan
      0.60 m2 beside, the envelope set aside 'not drawn'.  B3 strip 0.15 m2, blank: HELD BLANK, plan beside.
  B4 width conflict HELD 0.40 .. 0.50, P1 lift wall blank: CONFIRM (unchanged).  C1 column 1.20 MEASURED, a plaster
      line: not named, byte-identical.
Code totals: STR.CONC.NECK|m3 held 0.165 .. 0.825 (2 bounded) -> 0.252 .. 0.285 (1 bounded, 1 blocked);
STR.CONC.BEAM|m3 released 0 -> 0.420412, held 0.80 .. 1.25 (3 bounded, 1 blocked) -> 0.40 .. 0.50 (1 bounded,
2 blocked). Adverse: stale binding, a code / unit outside STR.CONC m3, HELD as 0, low > high, mm slip, a value with
no re-measure, a blank line with a figure, a retired bound with no / a wrong set-aside record, lower only without its
floor, CONFIRM with an after, a released line restated, a line named twice, applied twice, a stray line, totals
moved outside STR.CONC, a state tampered after integration, reordered villa (same result)."""
from __future__ import annotations

import copy
import json
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v30 as A30  # noqa: E402
from engine.source import arch_v304 as A304  # noqa: E402
from engine.source import arch_v3062 as A  # noqa: E402
from engine.source import boq_line as BL  # noqa: E402

PID, REV = "V661-SYNTHETIC", "e" * 64
B1_VALUE = round(2.40 * (0.30 * 0.60 - 0.15 ** 2 * (1 - math.pi / 4)), 6)


def _ln(code, eid, state, net=None, rng=None, unit="m3"):
    return BL.make_line(project_id=PID, revision_set_sha256=REV, item_code=code, unit=unit, evidence_state=state,
                        measured_net=net, gross=net, element_id=eid, floor="GF", room_id=None, bounded_range=rng,
                        formula=f"synthetic {code} {eid}", rule_id="R-SYN", rule_version="1",
                        geometry_source="SYNTHETIC_FIXTURE", material_state="BY_SPEC",
                        rfi={"question": "detail", "unlocks": eid} if state in ("BLOCKED_RFI", "BOUNDED_EXPOSURE")
                        else None, notes="synthetic")


def lines():
    return [
        _ln("STR.CONC.NECK", "N1", "BOUNDED_EXPOSURE", rng={"low": 0.075, "high": 0.375}),
        _ln("STR.CONC.NECK", "N2", "BOUNDED_EXPOSURE", rng={"low": 0.09, "high": 0.45}),
        _ln("STR.CONC.BEAM", "B1", "BOUNDED_EXPOSURE", rng={"low": 0.30, "high": 0.45}),
        _ln("STR.CONC.BEAM", "B2", "BOUNDED_EXPOSURE", rng={"low": 0.10, "high": 0.30}),
        _ln("STR.CONC.BEAM", "B3", "BLOCKED_RFI"),
        _ln("STR.CONC.BEAM", "B4", "BOUNDED_EXPOSURE", rng={"low": 0.40, "high": 0.50}),
        _ln("STR.CONC.LIFT", "P1", "BLOCKED_RFI"),
        _ln("STR.CONC.COLUMN", "C1", "MEASURED", net=1.20),
        _ln("FIN.PLASTER", "R1:PLASTER", "PROVISIONAL", net=44.31, unit="m2"),
    ]


LN = lines()
ID = {ln["location"]["element_id"]: ln["line_id"] for ln in LN}


def _src(t):
    return {"task": t, "file": f"research/v661/{t}.json", "sha256": t[-1] * 64, "merge_commit": "d" * 40,
            "checker_run": f"checker {t} Gate A PASS"}


def _x(eid, code, rng):
    return {"item_code": code, "element_id": eid, "unit": "m3", "class": "HELD",
            "low": rng[0] if rng else None, "high": rng[1] if rng else None}


def entries():
    return [
        {"action": "BOUND", "line_id": ID["N1"], "source_tasks": ["T-N"], "member": "neck N1",
         "expect": _x("N1", "STR.CONC.NECK", (0.075, 0.375)), "after": {"low": 0.252, "high": 0.285},
         "basis": "0.15 x (0.95 + 1.50 - 0.17 - 0.60) .. 0.15 x (2.50 - 0.60)", "why_held": "founding level",
         "question": "print the footing underside level"},
        {"action": "LOWER_ONLY", "line_id": ID["N2"], "source_tasks": ["T-N"], "member": "lift neck N2",
         "expect": _x("N2", "STR.CONC.NECK", (0.09, 0.45)), "after": {}, "basis": "0.18 x 1.55",
         "why_held": "pit depth by the supplier", "question": "pit raft depth",
         "beside": {"kind": "AT_LEAST_M3", "value": 0.279, "basis": "0.18 x 1.55"},
         "set_aside": {"low": 0.09, "high": 0.45, "why": "generic neck height, no drawn upper end"}},
        {"action": "VALUE", "line_id": ID["B1"], "source_tasks": ["T-B"], "member": "beam piece B1",
         "expect": _x("B1", "STR.CONC.BEAM", (0.30, 0.45)), "after": {"value": B1_VALUE},
         "basis": "2.40 x (0.30 x 0.60 - 0.15^2 x (1 - pi/4))", "remeasure": "checker own 0.420412 AGREE"},
        {"action": "HELD_BLANK", "line_id": ID["B2"], "source_tasks": ["T-B"], "member": "strip B2",
         "expect": _x("B2", "STR.CONC.BEAM", (0.10, 0.30)), "after": {}, "basis": "no mark, bars or depth",
         "why_held": "no drawn depth", "question": "the architect's detail",
         "beside": {"kind": "PLAN_AREA_M2", "value": 0.60, "basis": "0.20 x 3.00"},
         "set_aside": {"low": 0.10, "high": 0.30, "why": "schedule envelope, not drawn"}},
        {"action": "HELD_BLANK", "line_id": ID["B3"], "source_tasks": ["T-B"], "member": "strip B3",
         "expect": _x("B3", "STR.CONC.BEAM", None), "after": {}, "basis": "no depth", "why_held": "no drawn depth",
         "question": "the architect's detail", "beside": {"kind": "PLAN_AREA_M2", "value": 0.15, "basis": "0.10 x 1.50"}},
        {"action": "CONFIRM", "line_id": ID["B4"], "source_tasks": ["T-B"], "member": "beam B4",
         "expect": _x("B4", "STR.CONC.BEAM", (0.40, 0.50)), "basis": "two widths"},
        {"action": "CONFIRM", "line_id": ID["P1"], "source_tasks": ["T-S"], "member": "lift wall P1",
         "expect": _x("P1", "STR.CONC.LIFT", None), "basis": "designer item"},
    ]


def doc(ents=None, tot=None):
    d = {"schema": A.INPUTS_SCHEMA, "project_id": PID, "sources": [_src("T-N"), _src("T-B"), _src("T-S")],
         "entries": entries() if ents is None else ents}
    if tot:
        d["expect_totals"] = tot
    return d


def run(d=None, prev=None):
    prev = prev if prev is not None else copy.deepcopy(LN)
    ch, log = A.changes_for(A.load_inputs(d or doc(), PID), prev)
    return prev, ch, log


def _by(out, eid):
    return next(x for x in out if x["location"]["element_id"] == eid)


def _mut(i, **kw):
    es = entries()
    for k, v in kw.items():
        if v is None:
            es[i].pop(k, None)
        else:
            es[i][k] = v
    return doc(es)


# ------------------------------------------------------------------------------------------------ normal
def test_hand_values_and_states():
    assert B1_VALUE == 0.420412
    prev, ch, log = run()
    assert log["by_action"] == {"BOUND": 1, "LOWER_ONLY": 1, "VALUE": 1, "HELD_BLANK": 2, "CONFIRM": 2}
    assert log["lines"] == 5 and set(log["confirmed"]) == {ID["B4"], ID["P1"]}
    new, ident = A.integrate(prev, ch)
    n1, n2, b1, b2, b3 = (_by(new, e) for e in ("N1", "N2", "B1", "B2", "B3"))
    assert n1["evidence_state"] == "BOUNDED_EXPOSURE" and (n1["bounded_range"]["low"], n1["bounded_range"]["high"]) \
        == (0.252, 0.285)
    assert n2["evidence_state"] == "BLOCKED_RFI" and n2["measured_net"] is None and n2["bounded_range"] is None
    rec2 = n2["calculation"]["inputs"][A.REC_KEY]
    assert rec2["beside"]["value"] == 0.279 and rec2["set_aside"]["low"] == 0.09 and rec2["was"]["bounded_range"]
    assert b1["evidence_state"] == "MEASURED" and b1["measured_net"] == 0.420412 and b1["rfi"] is None
    assert b2["evidence_state"] == "BLOCKED_RFI" and b2["calculation"]["inputs"][A.REC_KEY]["beside"]["value"] == 0.6
    assert "0.6 m2 plan" in b2["calculation"]["formula"] or "0.60 m2 plan" in b2["calculation"]["formula"]
    assert b3["evidence_state"] == "BLOCKED_RFI" and b3["calculation"]["inputs"][A.REC_KEY]["set_aside"] is None
    assert ident["concrete"] == {"BOUND": 1, "VALUE": 1, "HELD_BLANK": 2, "LOWER_ONLY": 1}
    assert ident["replaced"] == 5 and ident["outside_rows"] == 4
    for e in ("B4", "P1", "C1", "R1:PLASTER"):
        assert A30.line_sha(_by(new, e)) == A30.line_sha(_by(prev, e)), e


def test_code_totals_hand(tmp_path):
    prev, ch, log = run()
    new, _ = A.integrate(prev, ch)
    t0, t1 = A304.code_totals(prev), A304.code_totals(new)
    nk, bm = t1["STR.CONC.NECK|m3"], t1["STR.CONC.BEAM|m3"]
    assert (nk["held_low"], nk["held_high"], nk["bounded_lines"], nk["blocked_lines"]) == (0.252, 0.285, 1, 1)
    assert t0["STR.CONC.NECK|m3"]["held_low"] == 0.165 and t0["STR.CONC.NECK|m3"]["held_high"] == 0.825
    assert (bm["released"], bm["held_low"], bm["held_high"], bm["bounded_lines"], bm["blocked_lines"]) == \
        (0.420412, 0.4, 0.5, 1, 2)
    assert (t0["STR.CONC.BEAM|m3"]["held_low"], t0["STR.CONC.BEAM|m3"]["held_high"]) == (0.8, 1.25)
    for k in ("STR.CONC.COLUMN|m3", "STR.CONC.LIFT|m3", "FIN.PLASTER|m2"):
        assert t0[k] == t1[k], k
    moved = A.check_totals(t0, t1, ch, {"STR.CONC.BEAM|m3": {"released": 0.420412}})
    assert set(moved) == {"STR.CONC.NECK|m3", "STR.CONC.BEAM|m3"}
    names, ident, led = A.write(tmp_path, prev, ch, log)
    assert "V3_0_62_BOQ_LINES.json" in names and led["integration_package"] is True
    r = json.loads((tmp_path / "V3_0_62_RUN.json").read_text(encoding="utf-8"))
    assert r["identity"]["diff"]["vs_base"] == {"SAME": 4, "CHANGED": 4, "CHANGED_TEXT_ONLY": 1} and r["identity"]["confirmed"] == 2
    assert r["released_default"] is False
    rows = {x["member"]: x for x in led["rows"]}
    assert rows["strip B2"]["set_aside"]["why"].startswith("schedule envelope") and \
        rows["beam piece B1"]["class"] == ["HELD", "RELEASED"]


def test_reordered_villa_same_result():
    prev, ch, _ = run()
    new = A.integrate(prev, ch)[0]
    rp = list(reversed(copy.deepcopy(LN)))
    d = doc(list(reversed(entries())))
    p2, ch2, _ = run(d, rp)
    new2 = A.integrate(p2, ch2)[0]
    assert sorted(A30.line_sha(x) for x in new) == sorted(A30.line_sha(x) for x in new2)


# ------------------------------------------------------------------------------------------------ adverse
@pytest.mark.parametrize("i,kw,msg", [
    (0, {"expect": _x("N1", "STR.CONC.NECK", (0.075, 0.376))}, "stale"),                    # stale range
    (0, {"expect": dict(_x("N1", "STR.CONC.NECK", (0.075, 0.375)), element_id="N9")}, "stale"),
    (0, {"expect": dict(_x("N1", "STR.CONC.NECK", (0.075, 0.375)), item_code="FIN.PLASTER")}, "STR.CONC"),
    (0, {"expect": dict(_x("N1", "STR.CONC.NECK", (0.075, 0.375)), unit="lm")}, "STR.CONC"),
    (0, {"expect": dict(_x("N1", "STR.CONC.NECK", (0.075, 0.375)), **{"class": "RELEASED"})}, "released"),
    (0, {"after": {"low": 0.0, "high": 0.285}}, "HELD-as-0"),
    (0, {"after": {"low": 0.285, "high": 0.252}}, "low"),
    (0, {"after": {"low": 252.0, "high": 285.0}}, "unit slip"),
    (2, {"remeasure": None}, "remeasure"),
    (2, {"after": {"value": 0.0}}, "HELD-as-0"),
    (2, {"after": {"value": 0.42, "low": 0.3}}, "no range"),
    (3, {"after": {"value": 0.2}}, "no quantity"),
    (3, {"set_aside": None}, "set_aside"),
    (3, {"set_aside": {"low": 0.1, "high": 0.29, "why": "x"}}, "set_aside"),
    (3, {"beside": None}, "beside"),
    (3, {"beside": {"kind": "PLAN_AREA_M2", "value": 0}}, "HELD-as-0"),
    (1, {"beside": {"kind": "PLAN_AREA_M2", "value": 0.6, "basis": "x"}}, "AT_LEAST"),
    (5, {"after": {"low": 0.4, "high": 0.5}}, "CONFIRM"),
    (0, {"source_tasks": ["T-X"]}, "no merged source"),
])
def test_adverse_inputs(i, kw, msg):
    with pytest.raises(A.InputsError, match=msg):
        run(_mut(i, **kw))


def test_adverse_line_named_twice_and_applied_twice():
    es = entries()
    es.append(dict(es[0]))
    with pytest.raises(A.InputsError, match="named twice"):
        run(doc(es))
    prev, ch, _ = run()
    new = A.integrate(prev, ch)[0]
    with pytest.raises(A.InputsError, match="applied once"):
        run(prev=new)


def test_adverse_confirm_that_disagrees_and_a_missing_line():
    es = entries()
    es[5]["expect"] = _x("B4", "STR.CONC.BEAM", (0.40, 0.55))
    with pytest.raises(A.InputsError, match="stale"):
        run(doc(es))
    es = entries()
    es[0]["line_id"] = "L-" + "0" * 20
    with pytest.raises(A.InputsError, match="not in the candidate"):
        run(doc(es))


def test_adverse_stray_line_and_totals_outside():
    prev, ch, _ = run()
    new = A.integrate(prev, ch)[0]
    t0 = A304.code_totals(prev)
    stray = [dict(x, measured_net=1.30, gross=1.30) if x["location"]["element_id"] == "C1" else x for x in new]
    with pytest.raises(ValueError, match="no change on it|not the restatement"):
        A.check_totals(t0, A304.code_totals(stray), ch)
    plaster = [dict(x, measured_net=40.0) if x["item_code"] == "FIN.PLASTER" else x for x in new]
    with pytest.raises(ValueError, match="outside STR.CONC"):
        A.check_totals(t0, A304.code_totals(plaster), ch)
    with pytest.raises(ValueError, match="not the inputs'"):
        A.check_totals(t0, A304.code_totals(new), ch, {"STR.CONC.BEAM|m3": {"released": 0.5}})
    bad = copy.deepcopy(ch)
    bad[0]["after"] = dict(bad[0]["after"], item_code="FIN.PLASTER")
    with pytest.raises(ValueError, match="not a change this version may make"):
        A.integrate(prev, bad)


def test_adverse_state_tampered_after_integration():
    prev, ch, _ = run()
    new = A.integrate(prev, ch)[0]
    t = copy.deepcopy(new)
    n1 = _by(t, "N1")
    n1["evidence_state"], n1["bounded_range"] = "BLOCKED_RFI", None
    with pytest.raises(ValueError, match="not in its state"):
        A.check_concrete(t)
    t = copy.deepcopy(new)
    b2 = _by(t, "B2")
    b2["evidence_state"], b2["bounded_range"] = "BOUNDED_EXPOSURE", {"low": 0.0, "high": 0.3}
    with pytest.raises(ValueError, match="not in its state"):
        A.check_concrete(t)
    # a held concrete line released without a V3.0.62 VALUE record
    t = copy.deepcopy(new)
    b4 = _by(t, "B4")
    b4["evidence_state"], b4["measured_net"], b4["bounded_range"] = "MEASURED", 0.45, None
    with pytest.raises(ValueError, match="without a re-measure"):
        A.check_concrete(t, prev)
