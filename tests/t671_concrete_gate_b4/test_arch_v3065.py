"""T-671: ARCH_TAKEOFF_V3.0.65 (CONCRETE_GATE_B_V4, R-T671-1) on the hand-calculated NON-Alsenan villa V671 (own
figures, no drawing). Printed: roof storey on an APPROVED base datum +6.00, finished roof +9.40, the highest opening
under the one roof slab has its top at +8.40, slab 'T 20'; schedule row K (30 x 30) 'FOUNDATION' only, GF / 1F / 2F
cells struck; a beam strip 0.20 x 0.40 m in plan whose faces carry mark B4 (0.50 deep), the arc mark B7 (0.70 deep)
next to it.

  R1 roof column 20x50 (0.10 m2): carried UPPER_ONLY blank (AT_MOST 0.10 x 3.40 = 0.34) by an earlier version.
     Drawn lower end: 8.40 + 0.20 - 6.00 = 2.60 m -> 0.26 .. 0.34 m3 (BOUND, the earlier record superseded, kept).
  R2 annex column: no opening top or slab thickness printed: CONFIRM (low open by name), byte-identical.
  K2 / K3 column K above the neck: K2 HELD 0.09 x 3.0 .. 9.0 = 0.27 .. 0.81, K3 blank: the schedule strikes every
     level above the neck -> NOT_APPLICABLE_WITH_EVIDENCE (K2's bound set aside by name), never 0.
  S1 strip HELD 0.08 x 0.40 .. 1.20 = 0.032 .. 0.096: VALUE 0.08 x 0.50 = 0.04 (B4 faces) + NEW companion HELD
     0 .. 0.08 x (0.70 - 0.50) = 0.016 (the B7 alternative), 0.04 + 0.016 = 0.056 <= 0.096.
  A plaster line: not named, byte-identical.
Code totals (m3): COLUMN lines 4 -> 2 (bounded 0.27 .. 0.81 -> 0.26 .. 0.34; blocked 3 -> 1); BEAM lines 1 -> 2
(released 0 -> 0.04, held 0.032 .. 0.096 -> 0 .. 0.016).
Adverse: an absence that is only ASSUMED, a not-applicable line with a quantity / on a released line / without its
bound set aside / with a stale set-aside, a companion with a floor / past the old range / without its VALUE entry /
for an element already carried, two companions for one value, tampered states, applied twice."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v30 as A30  # noqa: E402
from engine.source import arch_v304 as A304  # noqa: E402
from engine.source import arch_v3063 as A3063  # noqa: E402
from engine.source import arch_v3065 as A  # noqa: E402
from engine.source import boq_line as BL  # noqa: E402

PID, REV = "V671-SYNTHETIC", "f" * 64
R1 = (round(0.10 * (8.40 + 0.20 - 6.00), 6), round(0.10 * (9.40 - 6.00), 6))
K2 = (round(0.09 * 3.0, 6), round(0.09 * 9.0, 6))
S1_OLD = (round(0.08 * 0.40, 6), round(0.08 * 1.20, 6))
S1_VAL = round(0.08 * 0.50, 6)
S1_COMP = round(0.08 * (0.70 - 0.50), 6)


def _ln(code, eid, state, net=None, rng=None, unit="m3", rec=None):
    ln = BL.make_line(project_id=PID, revision_set_sha256=REV, item_code=code, unit=unit, evidence_state=state,
                      measured_net=net, gross=net, element_id=eid, floor="2F", room_id=None, bounded_range=rng,
                      formula=f"synthetic {code} {eid}", rule_id="R-SYN", rule_version="1",
                      geometry_source="SYNTHETIC_FIXTURE", material_state="BY_SPEC",
                      inputs=rec, rfi={"question": "detail", "unlocks": eid}
                      if state in ("BLOCKED_RFI", "BOUNDED_EXPOSURE") else None, notes="synthetic")
    return BL.validate(ln)


UPPER = {"concrete_ledger_v3063": {"action": "UPPER_ONLY", "beside": {"kind": "AT_MOST_M3", "value": 0.34,
                                                                      "basis": "0.10 x 3.40"}}}


def lines():
    return [
        _ln("STR.CONC.COLUMN", "K:R1|2F", "BLOCKED_RFI", rec=copy.deepcopy(UPPER)),
        _ln("STR.CONC.COLUMN", "K:R2|GF", "BLOCKED_RFI"),
        _ln("STR.CONC.COLUMN", "K:CN@1", "BOUNDED_EXPOSURE", rng={"low": K2[0], "high": K2[1]}),
        _ln("STR.CONC.COLUMN", "K:CN@2", "BLOCKED_RFI"),
        _ln("STR.CONC.BEAM", "S1", "BOUNDED_EXPOSURE", rng={"low": S1_OLD[0], "high": S1_OLD[1]}),
        _ln("FIN.PLASTER", "R1:PLASTER", "PROVISIONAL", net=44.31, unit="m2"),
    ]


LN = lines()
ID = {ln["location"]["element_id"]: ln["line_id"] for ln in LN}


def _src(t):
    return {"task": t, "file": f"research/v671/{t}.json", "sha256": t[-1] * 64, "merge_commit": "c" * 40,
            "checker_run": f"checker {t} Gate A PASS"}


def _x(eid, code, rng, cls="HELD"):
    return {"item_code": code, "element_id": eid, "unit": "m3", "class": cls,
            "low": rng[0] if rng else None, "high": rng[1] if rng else None}


EV = {"status": "DRAWING-CONFIRMED", "drawing": "V671 structural p.9", "reading": "row K GF / 1F / 2F struck",
      "checker_run": "checker T-C"}


def entries():
    return [
        {"action": "BOUND", "line_id": ID["K:R1|2F"], "source_tasks": ["T-R"], "member": "column R1 2F 20x50",
         "expect": _x("K:R1|2F", "STR.CONC.COLUMN", None), "after": {"low": R1[0], "high": R1[1]},
         "basis": "0.10 x (8.40 + 0.20 - 6.00) .. 0.10 x (9.40 - 6.00)", "why_held": "slab top not printed",
         "question": "slab-top level"},
        {"action": "CONFIRM", "line_id": ID["K:R2|GF"], "source_tasks": ["T-R"], "member": "annex column R2",
         "expect": _x("K:R2|GF", "STR.CONC.COLUMN", None), "basis": "no lower end printed"},
        {"action": "NOT_APPLICABLE", "line_id": ID["K:CN@1"], "source_tasks": ["T-C"], "member": "column K above neck",
         "expect": _x("K:CN@1", "STR.CONC.COLUMN", K2), "basis": "0 storeys printed above the neck",
         "evidence": dict(EV), "set_aside": {"low": K2[0], "high": K2[1], "why": "heights for an absent member"}},
        {"action": "NOT_APPLICABLE", "line_id": ID["K:CN@2"], "source_tasks": ["T-C"], "member": "column K above neck",
         "expect": _x("K:CN@2", "STR.CONC.COLUMN", None), "basis": "0 storeys printed above the neck",
         "evidence": dict(EV)},
        {"action": "VALUE", "line_id": ID["S1"], "source_tasks": ["T-S"], "member": "strip S1 (B4)",
         "expect": _x("S1", "STR.CONC.BEAM", S1_OLD), "after": {"value": S1_VAL}, "basis": "0.08 x 0.50",
         "remeasure": "checker own faces 0.08 m2 x 0.50 AGREE"},
        {"action": "ADD_COMPANION", "key": "S1-DEPTH", "source_tasks": ["T-S"], "companion_of": ID["S1"],
         "template_line": ID["S1"],
         "add": {"item_code": "STR.CONC.BEAM", "unit": "m3", "element_id": "S1~DEPTH", "floor": "GF",
                 "physical_element": "S1 depth remainder if B7"},
         "after": {"low": 0.0, "high": S1_COMP}, "basis": "0.08 x (0.70 - 0.50)", "why_held": "no mark on the strip",
         "question": "B4 or B7"},
    ]


def doc(ents=None):
    return {"schema": A.INPUTS_SCHEMA, "project_id": PID, "sources": [_src("T-R"), _src("T-C"), _src("T-S")],
            "entries": entries() if ents is None else ents}


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
def test_hand_figures():
    assert R1 == (0.26, 0.34) and K2 == (0.27, 0.81) and S1_OLD == (0.032, 0.096)
    assert S1_VAL == 0.04 and S1_COMP == 0.016 and S1_VAL + S1_COMP <= S1_OLD[1]


def test_states_and_records():
    prev, ch, log = run()
    assert log["by_action"] == {"BOUND": 1, "CONFIRM": 1, "NOT_APPLICABLE": 2, "VALUE": 1, "ADD_COMPANION": 1}
    assert log["lines"] == 5 and log["added"] == 1 and log["confirmed"] == [ID["K:R2|GF"]]
    new, ident = A.integrate(prev, ch)
    r1 = _by(new, "K:R1|2F")
    assert r1["evidence_state"] == "BOUNDED_EXPOSURE" and (r1["bounded_range"]["low"], r1["bounded_range"]["high"]) == R1
    rec = r1["calculation"]["inputs"]
    assert "concrete_ledger_v3063" not in rec                                       # R-T671-1 (l)
    assert rec[A.REC_KEY]["superseded"] == UPPER and rec[A.REC_KEY]["was"]["class"] == "HELD"
    for eid in ("K:CN@1", "K:CN@2"):
        k = _by(new, eid)
        assert k["evidence_state"] == "NOT_APPLICABLE_WITH_EVIDENCE" and k["measured_net"] is None
        assert k["bounded_range"] is None and k["line_id"] == ID[eid] and "NOT APPLICABLE" in k["notes"]
        assert k["calculation"]["inputs"][A.REC_KEY]["evidence"]["status"] == "DRAWING-CONFIRMED"
    assert _by(new, "K:CN@1")["calculation"]["inputs"][A.REC_KEY]["set_aside"]["high"] == 0.81
    s1, c = _by(new, "S1"), _by(new, "S1~DEPTH")
    assert s1["evidence_state"] == "MEASURED" and s1["measured_net"] == 0.04
    assert c["evidence_state"] == "BOUNDED_EXPOSURE" and c["bounded_range"]["low"] == 0.0
    assert c["bounded_range"]["high"] == 0.016 and c["line_id"] not in {x["line_id"] for x in prev}
    assert c["calculation"]["inputs"][A.REC_KEY]["companion"] == {"of": ID["S1"], "value_m3": 0.04}
    assert c["item_en"] == s1["item_en"]
    assert ident["concrete"] == {"BOUND": 1, "VALUE": 1, "HELD_BLANK": 0, "LOWER_ONLY": 0, "UPPER_ONLY": 0,
                                 "NOT_APPLICABLE": 2, "ADD_COMPANION": 1}
    assert ident["replaced"] == 4 and ident["added"] == 1 and ident["outside_rows"] == 2
    for e in ("K:R2|GF", "R1:PLASTER"):
        assert A30.line_sha(_by(new, e)) == A30.line_sha(_by(prev, e)), e
    A3063.check_concrete(new)                # the superseded UPPER_ONLY record no longer governs the line


def test_code_totals_hand(tmp_path):
    prev, ch, log = run()
    new, _ = A.integrate(prev, ch)
    t0, t1 = A304.code_totals(prev), A304.code_totals(new)
    c0, c1 = t0["STR.CONC.COLUMN|m3"], t1["STR.CONC.COLUMN|m3"]
    assert (c0["lines"], c0["held_low"], c0["held_high"], c0["blocked_lines"]) == (4, 0.27, 0.81, 3)
    assert (c1["lines"], c1["held_low"], c1["held_high"], c1["blocked_lines"]) == (2, 0.26, 0.34, 1)
    b0, b1 = t0["STR.CONC.BEAM|m3"], t1["STR.CONC.BEAM|m3"]
    assert (b0["lines"], b0["released"], b0["held_low"], b0["held_high"]) == (1, 0.0, 0.032, 0.096)
    assert (b1["lines"], b1["released"], b1["held_low"], b1["held_high"]) == (2, 0.04, 0.0, 0.016)
    assert t0["FIN.PLASTER|m2"] == t1["FIN.PLASTER|m2"]
    moved = A.check_totals(t0, t1, ch, {"STR.CONC.COLUMN|m3": {"held_low": 0.26}, "STR.CONC.BEAM|m3": {"released": 0.04}})
    assert set(moved) == {"STR.CONC.COLUMN|m3", "STR.CONC.BEAM|m3"}
    names, ident, led = A.write(tmp_path, prev, ch, log)
    assert "V3_0_65_BOQ_LINES.json" in names and led["integration_package"] is True
    r = json.loads((tmp_path / "V3_0_65_RUN.json").read_text(encoding="utf-8"))
    assert r["identity"]["diff"]["vs_base"] == {"SAME": 2, "CHANGED": 4, "ADDED": 1}
    assert r["identity"]["confirmed"] == 1 and r["identity"]["not_applicable"] == 2 and r["released_default"] is False
    assert "T668_ROOF_COLUMN_LOWER_ENDS" not in r["waiting_pieces"] and "T671_ANNEX_C3_LOW" in r["waiting_pieces"]
    rows = {x["line_id"]: x for x in led["rows"]}
    assert rows[ID["K:CN@1"]]["class"] == ["HELD", "EXCLUDED"]
    assert rows[ID["K:R1|2F"]]["superseded_record_keys"] == ["concrete_ledger_v3063"]
    csv = (tmp_path / "V3_0_65_INTEGRATION_LEDGER.csv").read_text(encoding="utf-8")
    assert "DRAWING-CONFIRMED" in csv and "companion of" in csv


def test_reordered_villa_same_result():
    prev, ch, _ = run()
    new = A.integrate(prev, ch)[0]
    p2, ch2, _ = run(doc(list(reversed(entries()))), list(reversed(copy.deepcopy(LN))))
    new2 = A.integrate(p2, ch2)[0]
    assert sorted(A30.line_sha(x) for x in new) == sorted(A30.line_sha(x) for x in new2)


# ------------------------------------------------------------------------------------------------ adverse
@pytest.mark.parametrize("i,kw,msg", [
    (2, {"evidence": dict(EV, status="ASSUMED")}, "not DRAWING-CONFIRMED"),
    (2, {"evidence": None}, "missing evidence"),
    (2, {"after": {"value": 0.0}}, "no quantity"),
    (2, {"set_aside": None}, "set_aside"),
    (2, {"expect": _x("K:CN@1", "STR.CONC.COLUMN", K2, "RELEASED")}, "only a HELD"),
    (2, {"expect": _x("K:CN@1", "FIN.PLASTER", K2)}, "only a HELD"),
    (5, {"after": {"low": 0.005, "high": S1_COMP}}, "runs from 0"),
    (5, {"after": {"low": 0.0, "high": 0.07}}, "leaves the line's own range"),
    (5, {"companion_of": ID["K:CN@2"]}, "not one VALUE entry"),
    (5, {"add": {"item_code": "FIN.PLASTER", "unit": "m2", "element_id": "X", "physical_element": "x"}}, "STR.CONC"),
    (5, {"source_tasks": ["T-X"]}, "no merged source"),
    (4, {"downgrade": {"downgrade_id": "DG-1"}}, "no released line"),
])
def test_adverse_inputs(i, kw, msg):
    with pytest.raises(A.InputsError, match=msg):
        run(_mut(i, **kw))


def test_adverse_stale_bindings():
    es = entries()
    es[2]["set_aside"] = dict(es[2]["set_aside"], high=0.9)
    with pytest.raises(A.InputsError, match="stale binding"):
        run(doc(es))
    es = entries()
    es[3]["expect"] = _x("K:CN@2", "STR.CONC.COLUMN", (0.1, 0.2))
    es[3]["set_aside"] = {"low": 0.1, "high": 0.2, "why": "x"}
    with pytest.raises(A.InputsError, match="stale binding"):
        run(doc(es))
    es = entries()
    es[4]["expect"] = _x("S1", "STR.CONC.BEAM", (0.03, 0.096))
    with pytest.raises(A.InputsError, match="stale binding"):
        run(doc(es))


def test_adverse_two_companions_and_already_carried():
    es = entries()
    es.append(dict(es[5], key="S1-DEPTH-2", add=dict(es[5]["add"], element_id="S1~DEPTH2")))
    with pytest.raises(A.InputsError, match="not one VALUE entry"):
        run(doc(es))
    es = entries()
    es[5]["add"] = dict(es[5]["add"], element_id="S1")
    with pytest.raises(A.InputsError, match="already carried"):
        run(doc(es))


def test_adverse_tampered_and_applied_twice():
    prev, ch, _ = run()
    new = A.integrate(prev, ch)[0]
    with pytest.raises(A.InputsError, match="applied once"):
        run(prev=new)
    t = copy.deepcopy(new)
    k = _by(t, "K:CN@1")
    k["evidence_state"], k["measured_net"], k["gross"] = "MEASURED", 0.0, 0.0     # an absence turned into a 0
    with pytest.raises(ValueError, match="not in its state"):
        A.check_concrete(t)
    t = copy.deepcopy(new)
    c = _by(t, "S1~DEPTH")
    c["bounded_range"] = dict(c["bounded_range"], low=0.01)
    with pytest.raises(ValueError, match="not in its state"):
        A.check_concrete(t)
    t = copy.deepcopy(new)
    s = _by(t, "S1")
    s["evidence_state"], s["measured_net"], s["gross"] = "BLOCKED_RFI", None, None
    with pytest.raises(ValueError, match="not in its state"):
        A.check_concrete(t)
    with pytest.raises(ValueError, match="already a candidate line"):
        A.check_concrete(new, new)


def test_struck_row_is_never_zero_and_no_lower_end_stays_open():
    """a struck schedule row leaves the totals as a state, not as 0 m3; the column with no printed lower end keeps its
    line byte-identical (CONFIRM) and a BOUND for it without a printed low would need a positive low (refused)"""
    prev, ch, _ = run()
    new = A.integrate(prev, ch)[0]
    t1 = A304.code_totals(new)["STR.CONC.COLUMN|m3"]
    assert t1["released"] == 0.0 and t1["lines"] == 2
    es = entries()
    es[1] = dict(es[0], line_id=ID["K:R2|GF"], expect=_x("K:R2|GF", "STR.CONC.COLUMN", None),
                 after={"low": 0.0, "high": 0.50625})
    with pytest.raises(A.InputsError, match="outside 0"):
        run(doc(es))


def test_base_carrying_an_earlier_added_line_integrates():
    """regression (own chain run, 2026-11-10): the V3.0.64 base carries a line V3.0.64 ADDED; re-running the earlier
    checks must not take these lines as their own base (A3064.integrate(out, []) refuses its own added line as
    'already a candidate line'); the earlier state check still runs on it"""
    from engine.source import arch_v3064 as A64
    pit = _ln("STR.CONC.BLINDING", "PIT", "MEASURED", net=3.0)
    prev0 = copy.deepcopy(LN) + [pit]
    d64 = {"schema": A64.INPUTS_SCHEMA, "project_id": PID, "sources": [_src("T-P")], "entries": [
        {"action": "ADD_LOWER_ONLY", "key": "POOL", "source_tasks": ["T-P"], "template_line": pit["line_id"],
         "add": {"item_code": "STR.CONC.BLINDING", "unit": "m3", "element_id": "POOL:BLINDING", "floor": None,
                 "physical_element": "pool blinding"},
         "basis": "x", "why_held": "x", "question": "x", "beside": {"kind": "AT_LEAST_M3", "value": 1.0, "basis": "x"},
         "netted_against": [{"line_id": pit["line_id"], "item_code": "STR.CONC.BLINDING", "class": "RELEASED",
                             "value": 3.0, "overlap_m2": 2.0, "why": "one layer"}]}]}
    ch64, _ = A64.changes_for(A64.load_inputs(d64, PID), prev0)
    base = A64.integrate(prev0, ch64)[0]
    with pytest.raises(ValueError, match="already a candidate line"):
        A64.integrate(base, [])                        # why V3.0.65 does not re-run it this way
    prev, ch, _ = run(prev=copy.deepcopy(base))
    new, ident = A.integrate(prev, ch)
    assert ident["checks_v3_0_64"]["concrete"]["ADD_LOWER_ONLY"] == 1 and ident["added"] == 1
    t = copy.deepcopy(new)
    p = _by(t, "POOL:BLINDING")
    p["evidence_state"], p["measured_net"], p["gross"] = "MEASURED", 1.0, 1.0
    with pytest.raises(ValueError, match="not in its state"):
        A64.check_concrete(t)                          # the earlier state check still governs its line
