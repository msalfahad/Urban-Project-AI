"""T-677: ARCH_TAKEOFF_V3.0.66 (CONCRETE_GATE_B_V5, R-T677-1) on the hand-calculated NON-Alsenan villa V677 (own
figures, no drawing). Printed: lintel schedule band 0.20 x 0.20 (MIN 40 cm bearing), two windows L1 / L2 of 0.80 m
on one 0.20 wall with a 1.00 m pier between them, L1's other jamb 0.60 m to a wall end, L2's other end 0.50 m; a
three-riser entrance flight 3 x 1/2 x 0.30 x 0.15 x 2.00 with no waist drawn; slab on grade T 0.10; an oblique
0.30 ground beam G1 whose plan to its carriers is 0.50 m2 (a square-cut reading 0.40 m2) at the titles 0.30 .. 0.40.

  L1 blank -> BOUND 0.04 x (0.80 + 0.80) = 0.064 .. 0.04 x (0.80 + 0.40 + 0.60) = 0.072
  L2 blank -> BOUND 0.064 .. 0.04 x (0.80 + 0.40 + 0.50) = 0.068
  pier 1.00 - 2 x 0.40 = 0.20 m: ONE new line 0 .. 0.04 x 0.20 = 0.008 (owned by L1 or L2), in neither high
  E1 blank -> LOWER_ONLY, AT_LEAST 3 x 1/2 x 0.30 x 0.15 x 2.00 = 0.135 beside (waist not drawn)
  P1 released 1.20 (12.00 m2 - 0.40 m2 square cut deduction... the engine kept 12.00 m2 gross) -> REVALUE: the strip
     to the carriers is 0.50 m2: (12.40 - 0.50) x 0.10 = 1.19, delta -0.01 (the 0.10 m2 end triangles move to G1)
  G1 HELD 0.40 x 0.30 .. 0.50 x 0.40 = 0.12 .. 0.20 -> BOUND 0.50 x 0.30 .. 0.50 x 0.40 = 0.15 .. 0.20
  P2 released 0.80: re-derived equal -> CONFIRM, byte-identical
  A plaster line: not named, byte-identical.
Code totals (m3): LINTEL lines 2 -> 3, held 0 .. 0 -> 0.128 .. 0.148 (blocked 2 -> 0); STAIR blocked 1 -> 1;
GROUND_SLAB released 2.00 -> 1.99; GROUND_BEAM held 0.12 .. 0.20 -> 0.15 .. 0.20.
Adverse: a slab revalue without its beam (both or neither), a stated delta that is not the arithmetic, a no-change
revalue, a revalue of a HELD line, a released line moved by a stale value, a shared remainder from 0.001 / with one
sharer / with a sharer that is not bounded here / twice, tampered states, a released line moved without a revalue,
applied twice, the V3.0.65 added companion in the base."""
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
from engine.source import arch_v3065 as A65  # noqa: E402
from engine.source import arch_v3066 as A  # noqa: E402
from engine.source import boq_line as BL  # noqa: E402

PID, REV = "V677-SYNTHETIC", "e" * 64
BD = 0.20 * 0.20
L1 = (round(BD * (0.80 + 0.80), 6), round(BD * (0.80 + 0.40 + 0.60), 6))
L2 = (round(BD * (0.80 + 0.80), 6), round(BD * (0.80 + 0.40 + 0.50), 6))
PIER = round(BD * (1.00 - 2 * 0.40), 6)
E1 = round(3 * 0.5 * 0.30 * 0.15 * 2.00, 6)
P1_OLD, P1_NEW = 1.20, round((12.40 - 0.50) * 0.10, 6)
G1_OLD = (round(0.40 * 0.30, 6), round(0.50 * 0.40, 6))
G1_NEW = (round(0.50 * 0.30, 6), round(0.50 * 0.40, 6))


def _ln(code, eid, state, net=None, rng=None, unit="m3", rec=None, floor="GF"):
    ln = BL.make_line(project_id=PID, revision_set_sha256=REV, item_code=code, unit=unit, evidence_state=state,
                      measured_net=net, gross=net, element_id=eid, floor=floor, room_id=None, bounded_range=rng,
                      formula=f"synthetic {code} {eid}", rule_id="R-SYN", rule_version="1",
                      geometry_source="SYNTHETIC_FIXTURE", material_state="BY_SPEC",
                      inputs=rec, rfi={"question": "detail", "unlocks": eid}
                      if state in ("BLOCKED_RFI", "BOUNDED_EXPOSURE") else None, notes="synthetic")
    return BL.validate(ln)


V65 = {"concrete_ledger_v3065": {"action": "BOUND", "member": "earlier"}}


def _lr(o):
    return {"lintel_v3053": {"opening_id": o, "decision": "HELD", "why": "head not established", "host_line": None}}


def lines(v65=True):
    return [
        _ln("STR.CONC.LINTEL", "LINTEL:L1", "BLOCKED_RFI", rec=_lr("L1")),
        _ln("STR.CONC.LINTEL", "LINTEL:L2", "BLOCKED_RFI", rec=_lr("L2")),
        _ln("STR.CONC.LINTEL", "LINTEL:L3", "BLOCKED_RFI", rec=_lr("L3")),
        _ln("STR.CONC.STAIR", "E1:FLIGHTS", "BLOCKED_RFI"),
        _ln("STR.CONC.GROUND_SLAB", "P1", "MEASURED", net=P1_OLD),
        _ln("STR.CONC.GROUND_SLAB", "P2", "MEASURED", net=0.80),
        _ln("STR.CONC.GROUND_BEAM", "G1", "BOUNDED_EXPOSURE", rng={"low": G1_OLD[0], "high": G1_OLD[1]},
            rec=copy.deepcopy(V65) if v65 else None),
        _ln("FIN.PLASTER", "R1:PLASTER", "PROVISIONAL", net=44.31, unit="m2"),
    ]


LN = lines()
ID = {ln["location"]["element_id"]: ln["line_id"] for ln in LN}


def _src(t):
    return {"task": t, "file": f"research/v677/{t}.json", "sha256": t[-1] * 64, "merge_commit": "d" * 40,
            "checker_run": f"checker {t} Gate A PASS"}


def _x(eid, code, rng=None, cls="HELD", value=None):
    if cls == "RELEASED":
        return {"item_code": code, "element_id": eid, "unit": "m3", "class": cls, "value": value}
    return {"item_code": code, "element_id": eid, "unit": "m3", "class": cls,
            "low": rng[0] if rng else None, "high": rng[1] if rng else None}


def entries():
    return [
        {"action": "BOUND", "line_id": ID["LINTEL:L1"], "source_tasks": ["T-L"], "member": "lintel L1",
         "expect": _x("LINTEL:L1", "STR.CONC.LINTEL"), "after": {"low": L1[0], "high": L1[1]},
         "basis": "0.04 x 1.60 .. 1.80", "why_held": "end bearings not dimensioned", "question": "bearings"},
        {"action": "BOUND", "line_id": ID["LINTEL:L2"], "source_tasks": ["T-L"], "member": "lintel L2",
         "expect": _x("LINTEL:L2", "STR.CONC.LINTEL"), "after": {"low": L2[0], "high": L2[1]},
         "basis": "0.04 x 1.60 .. 1.70", "why_held": "end bearings not dimensioned", "question": "bearings"},
        {"action": "ADD_SHARED", "key": "PIER-L1-L2", "source_tasks": ["T-L"],
         "shared_by": [ID["LINTEL:L1"], ID["LINTEL:L2"]], "template_line": ID["LINTEL:L1"],
         "add": {"item_code": "STR.CONC.LINTEL", "unit": "m3", "element_id": "LINTEL:L1+L2:PIER_REMAINDER",
                 "floor": "GF", "physical_element": "pier remainder L1 / L2"},
         "after": {"low": 0.0, "high": PIER}, "basis": "0.04 x (1.00 - 0.80)", "why_held": "owner lintel not drawn",
         "question": "which lintel"},
        {"action": "LOWER_ONLY", "line_id": ID["E1:FLIGHTS"], "source_tasks": ["T-L"], "member": "flight E1",
         "expect": _x("E1:FLIGHTS", "STR.CONC.STAIR"), "basis": "3 x 1/2 x 0.30 x 0.15 x 2.00",
         "beside": {"kind": "AT_LEAST_M3", "value": E1, "basis": "steps part drawn"},
         "why_held": "waist not drawn", "question": "waist"},
        {"action": "REVALUE", "line_id": ID["P1"], "source_tasks": ["T-S"], "member": "slab P1",
         "expect": _x("P1", "STR.CONC.GROUND_SLAB", cls="RELEASED", value=P1_OLD), "after": {"value": P1_NEW},
         "delta": round(P1_NEW - P1_OLD, 6), "basis": "(12.40 - 0.50) x 0.10",
         "remeasure": "checker own faces 11.90 m2 AGREE",
         "moves_to": {"line_id": ID["G1"], "plan_m2": 0.10, "why": "end triangles of G1"}},
        {"action": "CONFIRM", "line_id": ID["P2"], "source_tasks": ["T-S"], "member": "slab P2",
         "expect": _x("P2", "STR.CONC.GROUND_SLAB", cls="RELEASED", value=0.80), "basis": "8.00 x 0.10 equal"},
        {"action": "BOUND", "line_id": ID["G1"], "source_tasks": ["T-S"], "member": "beam G1",
         "expect": _x("G1", "STR.CONC.GROUND_BEAM", G1_OLD), "after": {"low": G1_NEW[0], "high": G1_NEW[1]},
         "basis": "0.50 x 0.30 .. 0.40", "why_held": "titles", "question": "title"},
    ]


def doc(ents=None):
    return {"schema": A.INPUTS_SCHEMA, "project_id": PID, "sources": [_src("T-L"), _src("T-S")],
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
    assert L1 == (0.064, 0.072) and L2 == (0.064, 0.068) and PIER == 0.008 and E1 == 0.135
    assert P1_NEW == 1.19 and G1_OLD == (0.12, 0.2) and G1_NEW == (0.15, 0.2)
    assert round(L1[1] + L2[1] + PIER, 6) == 0.148           # the remainder once, in neither high


def test_states_and_records():
    prev, ch, log = run()
    assert log["by_action"] == {"BOUND": 3, "ADD_SHARED": 1, "LOWER_ONLY": 1, "REVALUE": 1, "CONFIRM": 1}
    assert log["lines"] == 6 and log["added"] == 1 and log["confirmed"] == [ID["P2"]]
    assert log["revalued"] == [ID["P1"]] and log["moved_plan"] == [{"from": ID["P1"], "to": ID["G1"], "plan_m2": 0.1}]
    new, ident = A.integrate(prev, ch)
    l1 = _by(new, "LINTEL:L1")
    assert l1["evidence_state"] == "BOUNDED_EXPOSURE" and (l1["bounded_range"]["low"], l1["bounded_range"]["high"]) == L1
    p = _by(new, "LINTEL:L1+L2:PIER_REMAINDER")
    assert p["bounded_range"]["low"] == 0.0 and p["bounded_range"]["high"] == PIER
    assert p["calculation"]["inputs"][A.REC_KEY]["shared"] == {"by": [ID["LINTEL:L1"], ID["LINTEL:L2"]],
                                                               "openings": ["L1", "L2"]}
    assert p["line_id"] not in {x["line_id"] for x in prev} and p["item_en"] == l1["item_en"]
    e1 = _by(new, "E1:FLIGHTS")
    assert e1["evidence_state"] == "BLOCKED_RFI" and e1["measured_net"] is None and "0.135" in e1["calculation"]["formula"]
    p1 = _by(new, "P1")
    assert p1["evidence_state"] == "MEASURED" and p1["measured_net"] == P1_NEW
    r1 = p1["calculation"]["inputs"][A.REC_KEY]
    assert r1["was"]["measured_net"] == P1_OLD and r1["after"] == {"value": P1_NEW, "delta": -0.01}
    assert r1["moves_to"]["line_id"] == ID["G1"] and "RELEASED (re-derived" in p1["notes"]
    g1 = _by(new, "G1")
    assert (g1["bounded_range"]["low"], g1["bounded_range"]["high"]) == G1_NEW
    gi = g1["calculation"]["inputs"]
    assert "concrete_ledger_v3065" not in gi and gi[A.REC_KEY]["superseded"] == V65          # R-T677-1 (p)
    assert ident["concrete"] == {"BOUND": 3, "VALUE": 0, "HELD_BLANK": 0, "LOWER_ONLY": 1, "UPPER_ONLY": 0,
                                 "NOT_APPLICABLE": 0, "ADD_COMPANION": 0, "REVALUE": 1, "ADD_SHARED": 1}
    assert ident["replaced"] == 5 and ident["added"] == 1 and ident["outside_rows"] == 3
    assert ident["lintels"] == {"restated": 2, "shared": 1, "v3_0_53": 1}
    assert ident["checks_v3_0_65"]["governed_lintels_outside_v3_0_53"] == 3
    assert l1["calculation"]["inputs"][A.REC_KEY]["superseded"]["lintel_v3053"]["opening_id"] == "L1"
    assert "lintel_v3053" not in l1["calculation"]["inputs"]
    assert p["calculation"]["inputs"][A.REC_KEY]["shared"]["openings"] == ["L1", "L2"]
    for e in ("P2", "R1:PLASTER", "LINTEL:L3"):
        assert A30.line_sha(_by(new, e)) == A30.line_sha(_by(prev, e)), e
    A65.check_concrete(new)                       # the superseded V3.0.65 record no longer governs G1


def test_code_totals_hand(tmp_path):
    prev, ch, log = run()
    new, _ = A.integrate(prev, ch)
    t0, t1 = A304.code_totals(prev), A304.code_totals(new)
    a0, a1 = t0["STR.CONC.LINTEL|m3"], t1["STR.CONC.LINTEL|m3"]
    assert (a0["lines"], a0["held_low"], a0["held_high"], a0["blocked_lines"]) == (3, 0.0, 0.0, 3)
    assert (a1["lines"], a1["bounded_lines"], a1["blocked_lines"]) == (4, 3, 1)
    assert abs(a1["held_low"] - 0.128) < 1e-9 and abs(a1["held_high"] - 0.148) < 1e-9
    s0, s1 = t0["STR.CONC.GROUND_SLAB|m3"], t1["STR.CONC.GROUND_SLAB|m3"]
    assert abs(s0["released"] - 2.00) < 1e-9 and abs(s1["released"] - 1.99) < 1e-9 and s1["lines"] == 2
    g1 = t1["STR.CONC.GROUND_BEAM|m3"]
    assert abs(g1["held_low"] - 0.15) < 1e-9 and abs(g1["held_high"] - 0.20) < 1e-9
    assert t0["STR.CONC.STAIR|m3"] == t1["STR.CONC.STAIR|m3"] and t0["FIN.PLASTER|m2"] == t1["FIN.PLASTER|m2"]
    moved = A.check_totals(t0, t1, ch, {"STR.CONC.GROUND_SLAB|m3": {"released": 1.99}})
    assert set(moved) == {"STR.CONC.LINTEL|m3", "STR.CONC.GROUND_SLAB|m3", "STR.CONC.GROUND_BEAM|m3",
                          "STR.CONC.STAIR|m3"}                      # every restated code, the stair's unchanged
    assert moved["STR.CONC.STAIR|m3"]["base"] == moved["STR.CONC.STAIR|m3"]["v3_0_66"]
    names, ident, led = A.write(tmp_path, prev, ch, log)
    assert "V3_0_66_BOQ_LINES.json" in names and led["integration_package"] is True
    r = json.loads((tmp_path / "V3_0_66_RUN.json").read_text(encoding="utf-8"))
    assert r["identity"]["diff"]["vs_base"] == {"SAME": 3, "CHANGED": 4, "CHANGED_TEXT_ONLY": 1, "ADDED": 1}  # E1
    assert r["identity"]["revalued"] == 1 and r["released_default"] is False
    assert "T671_GROUND_SLAB_T674" not in r["waiting_pieces"] and "T677_LINTEL_DESIGNER_OPEN" in r["waiting_pieces"]
    rows = {x["line_id"]: x for x in led["rows"]}
    assert rows[ID["P1"]]["class"] == ["RELEASED", "RELEASED"] and rows[ID["P1"]]["evidence_status"] == "VERIFIED"
    assert rows[ID["G1"]]["superseded_record_keys"] == ["concrete_ledger_v3065"]
    csv = (tmp_path / "V3_0_66_INTEGRATION_LEDGER.csv").read_text(encoding="utf-8")
    assert "remainder shared by" in csv and "m2 moves to" in csv


def test_reordered_villa_same_result():
    prev, ch, _ = run()
    new = A.integrate(prev, ch)[0]
    p2, ch2, _ = run(doc(list(reversed(entries()))), list(reversed(copy.deepcopy(LN))))
    new2 = A.integrate(p2, ch2)[0]
    assert sorted(A30.line_sha(x) for x in new) == sorted(A30.line_sha(x) for x in new2)


# ------------------------------------------------------------------------------------------------ adverse
@pytest.mark.parametrize("i,kw,msg", [
    (4, {"delta": -0.02}, "is not the value"),
    (4, {"delta": True}, "not a number"),
    (4, {"after": {"value": P1_OLD}, "delta": 0.0}, "is a CONFIRM"),
    (4, {"remeasure": None}, "missing remeasure"),
    (4, {"expect": _x("P1", "STR.CONC.GROUND_SLAB", (1.1, 1.3))}, "only a RELEASED"),
    (4, {"after": {"value": 0.0}, "delta": -1.2}, "outside 0"),
    (4, {"downgrade": {"downgrade_id": "DG-1"}}, "stays released"),
    (5, {"after": {"value": 0.81}}, "changes nothing"),
    (2, {"after": {"low": 0.001, "high": PIER}}, "runs from 0"),
    (2, {"shared_by": [ID["LINTEL:L1"]]}, "two or more"),
    (2, {"shared_by": [ID["LINTEL:L1"], ID["E1:FLIGHTS"]]}, "not a BOUND"),
    (2, {"template_line": ID["E1:FLIGHTS"]}, "template line is one of its sharers"),
    (2, {"add": {"item_code": "FIN.PLASTER", "unit": "m2", "element_id": "X", "physical_element": "x"}}, "STR.CONC"),
    (2, {"source_tasks": ["T-X"]}, "no merged source"),
])
def test_adverse_inputs(i, kw, msg):
    with pytest.raises(A.InputsError, match=msg):
        run(_mut(i, **kw))


def test_both_or_neither():
    """a plan area leaving the slab for the beam leaves only with the beam's restatement (R-T677-1 (n))"""
    es = [e for e in entries() if e.get("line_id") != ID["G1"]]
    with pytest.raises(A.InputsError, match="both or neither"):
        run(doc(es))
    es = entries()
    es[6] = {"action": "CONFIRM", "line_id": ID["G1"], "source_tasks": ["T-S"], "member": "beam G1",
             "expect": _x("G1", "STR.CONC.GROUND_BEAM", G1_OLD), "basis": "unchanged"}
    with pytest.raises(A.InputsError, match="both or neither"):
        run(doc(es))


def test_adverse_stale_bindings_and_twice():
    es = entries()
    es[4]["expect"] = _x("P1", "STR.CONC.GROUND_SLAB", cls="RELEASED", value=1.21)
    es[4]["delta"] = round(P1_NEW - 1.21, 6)
    with pytest.raises(A.InputsError, match="stale binding"):
        run(doc(es))
    es = entries()
    es[5]["expect"] = _x("P2", "STR.CONC.GROUND_SLAB", cls="RELEASED", value=0.79)
    with pytest.raises(A.InputsError, match="stale binding"):
        run(doc(es))
    es = entries()
    es.append(dict(es[2], key="PIER-L1-L2-B", add=dict(es[2]["add"], element_id="LINTEL:L1+L2:PIER2")))
    with pytest.raises(A.InputsError, match="second remainder"):
        run(doc(es))
    es = entries()
    es[2]["add"] = dict(es[2]["add"], element_id="LINTEL:L2")
    with pytest.raises(A.InputsError, match="already carried"):
        run(doc(es))


def test_adverse_tampered_and_applied_twice():
    prev, ch, _ = run()
    new = A.integrate(prev, ch)[0]
    with pytest.raises(A.InputsError, match="applied once"):
        run(prev=new)
    t = copy.deepcopy(new)
    p = _by(t, "P1")
    p["measured_net"] = p["gross"] = 1.18                 # a revalued line that is not its stated delta
    with pytest.raises(ValueError, match="not in its state"):
        A.check_concrete(t)
    t = copy.deepcopy(new)
    s = _by(t, "LINTEL:L1+L2:PIER_REMAINDER")
    s["bounded_range"] = dict(s["bounded_range"], low=0.002)
    with pytest.raises(ValueError, match="not in its state"):
        A.check_concrete(t)
    t = copy.deepcopy(new)
    l2 = _by(t, "LINTEL:L2")
    l2["evidence_state"], l2["bounded_range"] = "BLOCKED_RFI", None       # a sharer no longer bounded
    with pytest.raises(ValueError, match="not in its state"):
        A.check_concrete(t)
    with pytest.raises(ValueError, match="already a candidate line"):
        A.check_concrete(new, new)
    t = copy.deepcopy(new)
    q = _by(t, "P2")
    q["measured_net"] = q["gross"] = 0.81                 # a released line moved with no re-derivation
    with pytest.raises(ValueError, match="without a re-derivation"):
        A.check_concrete(t, prev)


def test_held_never_zero_and_released_never_from_held():
    prev, ch, _ = run()
    new = A.integrate(prev, ch)[0]
    for ln in new:
        if ln["item_code"].startswith("STR.CONC.") and A.line_class(ln) == "HELD":
            assert ln.get("measured_net") is None
    es = entries()
    es[0] = dict(es[0], after={"low": 0.0, "high": L1[1]})
    with pytest.raises(A.InputsError, match="outside 0"):
        run(doc(es))
    es = [e for e in entries() if e["action"] != "ADD_SHARED"]
    es[0] = {"action": "REVALUE", "line_id": ID["LINTEL:L1"], "source_tasks": ["T-L"], "member": "lintel L1",
             "expect": _x("LINTEL:L1", "STR.CONC.LINTEL", cls="RELEASED", value=0.07), "after": {"value": 0.068},
             "delta": -0.002, "basis": "x", "remeasure": "x"}
    with pytest.raises(A.InputsError, match="stale binding"):
        run(doc(es))                                       # a HELD line is never released by a revalue


def test_base_carrying_the_v3065_companion_integrates():
    """the V3.0.65 base carries a line V3.0.65 ADDED (its depth companion); the V3.0.65 state check re-runs on the
    result without these lines as their own base (T-671 lesson) and still governs its line"""
    strip = _ln("STR.CONC.BEAM", "S1", "BOUNDED_EXPOSURE", rng={"low": 0.032, "high": 0.096})
    prev0 = lines(v65=False) + [strip]
    d65 = {"schema": A65.INPUTS_SCHEMA, "project_id": PID, "sources": [_src("T-S")], "entries": [
        {"action": "VALUE", "line_id": strip["line_id"], "source_tasks": ["T-S"], "member": "strip S1",
         "expect": _x("S1", "STR.CONC.BEAM", (0.032, 0.096)), "after": {"value": 0.04}, "basis": "0.08 x 0.50",
         "remeasure": "checker AGREE"},
        {"action": "ADD_COMPANION", "key": "S1-DEPTH", "source_tasks": ["T-S"], "companion_of": strip["line_id"],
         "template_line": strip["line_id"], "add": {"item_code": "STR.CONC.BEAM", "unit": "m3",
                                                    "element_id": "S1~DEPTH", "floor": "GF",
                                                    "physical_element": "S1 depth remainder"},
         "after": {"low": 0.0, "high": 0.016}, "basis": "x", "why_held": "x", "question": "x"}]}
    ch65, _ = A65.changes_for(A65.load_inputs(d65, PID), prev0)
    base = A65.integrate(prev0, ch65)[0]
    prev, ch, _ = run(prev=copy.deepcopy(base))
    new, ident = A.integrate(prev, ch)
    assert ident["checks_v3_0_65"]["concrete_v3_0_65"]["ADD_COMPANION"] == 1 and ident["added"] == 1
    t = copy.deepcopy(new)
    c = _by(t, "S1~DEPTH")
    c["bounded_range"] = dict(c["bounded_range"], low=0.01)
    with pytest.raises(ValueError, match="not in its state"):
        A65.check_concrete(t)


def test_lintel_governance():
    """R-T677-1 (q): the V3.0.53 check still governs every lintel line this version does not touch, and this
    version's lintel check governs the ones it restated / added"""
    from engine.source import arch_v3053 as A53
    prev, ch, _ = run()
    new = A.integrate(prev, ch)[0]
    t = copy.deepcopy(new)
    l3 = _by(t, "LINTEL:L3")
    l3["calculation"]["inputs"].pop("lintel_v3053")                       # an untouched lintel losing its record
    with pytest.raises(ValueError, match="carries no V3.0.53 lintel record"):
        A.integrate(t, [])
    with pytest.raises(ValueError, match="carries no V3.0.53 lintel record"):
        A53.check_lintels([x for x in new if not A._governed(x)] + [l3])
    t = copy.deepcopy(new)
    l1 = _by(t, "LINTEL:L1")
    l1["calculation"]["inputs"]["lintel_v3053"] = _lr("L1")["lintel_v3053"]   # a live V3.0.53 record left behind
    with pytest.raises(ValueError, match="under superseded only"):
        A.check_lintels(t)
    t = copy.deepcopy(new)
    sup = _by(t, "LINTEL:L2")["calculation"]["inputs"][A.REC_KEY]["superseded"]["lintel_v3053"]
    sup["opening_id"] = "L3"                                              # two lines for one opening
    with pytest.raises(ValueError, match="two lintel lines|sharers' openings"):
        A.check_lintels(t)
    t = copy.deepcopy(new)
    _by(t, "LINTEL:L1+L2:PIER_REMAINDER")["calculation"]["inputs"][A.REC_KEY]["shared"]["openings"] = ["L1", "L3"]
    with pytest.raises(ValueError, match="sharers' openings"):
        A.check_lintels(t)
    req = copy.deepcopy(LN)
    _by(req, "LINTEL:L1")["calculation"]["inputs"]["lintel_v3053"]["decision"] = "REQUIRED"
    with pytest.raises(A.InputsError, match="V3.0.53 HELD record"):
        run(prev=req)                                                     # a released lintel is never restated
