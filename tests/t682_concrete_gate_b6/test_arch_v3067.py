"""T-682: ARCH_TAKEOFF_V3.0.67 (CONCRETE_GATE_B_V6, R-T682-2) on the hand-calculated NON-Alsenan villa V682 (own
figures, no drawing). Printed: lintel schedule band B = wall width x D 0.20, MIN 40 cm bearing; a 0.20 wall window
W1 w 1.00 (head 2.40 PRINTED) between a column 0.60 away and a column 0.30 away; an annex door D1 w 0.90 in a 0.15
wall, head NOT printed (owner fallback 2.20, Q-55 C), jambs 0.50 / 0.70 to the masonry ends (CEILING); a door D2 w
0.80 in a 0.15 wall, START 0.45 to a column, END on a crossing wall 0.05 (no stopper: OPEN); a planted column PC drawn
0.20 x 0.30, printed 'P.C 20x40', height 2.50 .. 3.00; an annex column C 0.30 x 0.30 from base +0.20 to the annex
slab top, which is not printed: a drawn head +2.60 (tol 0.01) under a printed 0.60 beam on one plane gives s_lo 3.19,
the finished mark +3.60; a lintel L9 V3.0.66 already bounded; a lintel L5 left blank; a released column CR 0.36; a
plaster line.

  W1 blank -> BOUND 0.04 x (1.00 + 0.40) = 0.056 .. 0.04 x (1.00 + 0.40 + 0.30) = 0.068   (DRAWING-CONFIRMED)
  D1 blank -> BOUND 0.03 x (0.90 + 0.80) = 0.051 .. 0.03 x (0.90 + 1.20) = 0.063
       existence: slab piece soffit >= 3.19 - D_max 0.60 = 2.59; spare 2.59 - 2.20 - (0.20 + 0.02) = 0.17 -> REQUIRED,
       ASSUMED - OWNER-APPROVED (Q-55 C), re-run trigger 2.20 + 0.17 = 2.370 m; plane record ONE_PLANE
  D2 blank -> LOWER_ONLY, AT_LEAST 0.03 x (0.80 + 0.40) = 0.036 beside (the END is OPEN: no high)
  PC blank -> BOUND 0.06 x 2.50 = 0.15 .. 0.08 x 3.00 = 0.24
  C  blank -> BOUND 0.09 x (3.19 - 0.20) = 0.2691 .. 0.09 x (3.60 - 0.20) = 0.306 (plane record)
Code totals (m3): LINTEL held 0.010 .. 0.020 (L9) -> 0.117 .. 0.151, bounded 1 -> 3,
blocked 4 -> 2; COLUMN released 0.36 unchanged, held 0 .. 0 -> 0.4191 .. 0.546, bounded 0 -> 2. Released m3 never moves.
Adverse: a VALUE / REVALUE entry, a released or bounded expect, an owner-fallback existence without its assumption,
a wrong trigger, a trigger text without its number, an assumption on a drawing-confirmed line, a stepped / unchecked /
section-less plane, a line V3.0.66 restated, a stale binding, applied twice, a tampered state, two lines on one
opening, a released line moved."""
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
from engine.source import arch_v3066 as A66  # noqa: E402
from engine.source import arch_v3067 as A  # noqa: E402
from engine.source import boq_line as BL  # noqa: E402

PID, REV = "V682-SYNTHETIC", "f" * 64
OA = "ASSUMED - OWNER-APPROVED"
W1 = (round(0.04 * (1.00 + 0.40), 6), round(0.04 * (1.00 + 0.40 + 0.30), 6))
D1 = (round(0.03 * (0.90 + 0.80), 6), round(0.03 * (0.90 + 1.20), 6))
D2_LO = round(0.03 * (0.80 + 0.40), 6)
PC = (round(0.20 * 0.30 * 2.50, 6), round(0.20 * 0.40 * 3.00, 6))
S_LO = round(2.60 - 0.01 + 0.60, 6)
C = (round(0.09 * (S_LO - 0.20), 6), round(0.09 * (3.60 - 0.20), 6))
SPARE = round(S_LO - 0.60 - 2.20 - (0.20 + 0.02), 6)
L9 = (0.010, 0.020)


def _ln(code, eid, state, net=None, rng=None, unit="m3", rec=None, floor="GF"):
    ln = BL.make_line(project_id=PID, revision_set_sha256=REV, item_code=code, unit=unit, evidence_state=state,
                      measured_net=net, gross=net, element_id=eid, floor=floor, room_id=None, bounded_range=rng,
                      formula=f"synthetic {code} {eid}", rule_id="R-SYN", rule_version="1",
                      geometry_source="SYNTHETIC_FIXTURE", material_state="BY_SPEC",
                      inputs=rec, rfi={"question": "detail", "unlocks": eid}
                      if state in ("BLOCKED_RFI", "BOUNDED_EXPOSURE") else None, notes="synthetic")
    return BL.validate(ln)


def _lr(o, d="HELD"):
    return {"lintel_v3053": {"opening_id": o, "decision": d, "why": "synthetic", "host_line": None}}


V65 = {"concrete_ledger_v3065": {"action": "UPPER_ONLY", "member": "earlier",
                                  "beside": {"kind": "AT_MOST_M3", "value": 0.306, "basis": "finished mark"}}}


def base_v66():
    """the V3.0.66 candidate of V682: the V3.0.65 lines + L9 restated by V3.0.66 (its own code path)"""
    b = [
        _ln("STR.CONC.LINTEL", "LINTEL:W1", "BLOCKED_RFI", rec=_lr("W1")),
        _ln("STR.CONC.LINTEL", "LINTEL:D1", "BLOCKED_RFI", rec=_lr("D1")),
        _ln("STR.CONC.LINTEL", "LINTEL:D2", "BLOCKED_RFI", rec=_lr("D2")),
        _ln("STR.CONC.LINTEL", "LINTEL:L9", "BLOCKED_RFI", rec=_lr("L9")),
        _ln("STR.CONC.LINTEL", "LINTEL:L5", "BLOCKED_RFI", rec=_lr("L5")),
        _ln("STR.CONC.COLUMN", "CR", "MEASURED", net=0.36),
        _ln("STR.CONC.COLUMN", "PC", "BLOCKED_RFI"),
        _ln("STR.CONC.COLUMN", "C", "BLOCKED_RFI", rec=copy.deepcopy(V65)),
        _ln("FIN.PLASTER", "R1:PLASTER", "PROVISIONAL", net=44.31, unit="m2"),
    ]
    l9 = next(x for x in b if x["location"]["element_id"] == "LINTEL:L9")
    d66 = {"schema": A66.INPUTS_SCHEMA, "project_id": PID, "sources": [_src("T-P")], "entries": [
        {"action": "BOUND", "line_id": l9["line_id"], "source_tasks": ["T-P"], "member": "lintel L9",
         "expect": _x("LINTEL:L9", "STR.CONC.LINTEL"), "after": {"low": L9[0], "high": L9[1]}, "basis": "earlier",
         "why_held": "bearings", "question": "bearings"}]}
    ch, _ = A66.changes_for(A66.load_inputs(d66, PID), b)
    return A66.integrate(b, ch)[0]


def _src(t):
    return {"task": t, "file": f"research/v682/{t}.json", "sha256": t[-1] * 64, "merge_commit": "a" * 40,
            "checker_run": f"checker {t} Gate A PASS"}


def _x(eid, code, rng=None, cls="HELD"):
    return {"item_code": code, "element_id": eid, "unit": "m3", "class": cls,
            "low": rng[0] if rng else None, "high": rng[1] if rng else None}


LN = base_v66()
ID = {ln["location"]["element_id"]: ln["line_id"] for ln in LN}
PLANE = {"rule": "R-T682-1 1.0.0", "state": "ONE_PLANE", "outline": "annex roof", "sections_checked": ["A-A"],
         "steps_outside": [{"section": "A-A", "step_m": "0.200000", "evidence": "step drawn outside the annex"}],
         "section_steps": [{"section": "A-A", "step_m": "0.20", "inside_plane": False, "evidence": "outside"}],
         "s_lo_m": S_LO}
DC = {"status": "DRAWING-CONFIRMED", "basis": "head printed"}


def _assume():
    t = round(2.20 + SPARE, 6)
    return {"status": OA, "source": "Q-55 C", "what": "door head 2.20 m (not printed)", "assumed_m": 2.20,
            "spare_m": SPARE, "trigger_m": t,
            "rerun_trigger": f"a drawn or printed head above {t:.3f} m over FFL reverses existence"}


def entries():
    return [
        {"action": "BOUND", "line_id": ID["LINTEL:W1"], "source_tasks": ["T-P"], "member": "lintel W1",
         "expect": _x("LINTEL:W1", "STR.CONC.LINTEL"), "after": {"low": W1[0], "high": W1[1]},
         "basis": "0.04 x 1.40 .. 1.70", "why_held": "bearings", "question": "bearings", "existence": dict(DC)},
        {"action": "BOUND", "line_id": ID["LINTEL:D1"], "source_tasks": ["T-P"], "member": "lintel D1",
         "expect": _x("LINTEL:D1", "STR.CONC.LINTEL"), "after": {"low": D1[0], "high": D1[1]},
         "basis": "0.03 x 1.70 .. 2.10", "why_held": "bearings", "question": "door heads",
         "existence": {"status": OA, "basis": "Q-55 C fallback"}, "assumption": _assume(), "plane": dict(PLANE)},
        {"action": "LOWER_ONLY", "line_id": ID["LINTEL:D2"], "source_tasks": ["T-P"], "member": "lintel D2",
         "expect": _x("LINTEL:D2", "STR.CONC.LINTEL"), "basis": "0.03 x 1.20, END open",
         "beside": {"kind": "AT_LEAST_M3", "value": D2_LO, "basis": "bounded end 0.40"},
         "why_held": "END open", "question": "end", "existence": dict(DC)},
        {"action": "BOUND", "line_id": ID["PC"], "source_tasks": ["T-P"], "member": "planted column PC",
         "expect": _x("PC", "STR.CONC.COLUMN"), "after": {"low": PC[0], "high": PC[1]},
         "basis": "0.06 x 2.50 .. 0.08 x 3.00", "why_held": "section conflict", "question": "section",
         "existence": dict(DC)},
        {"action": "BOUND", "line_id": ID["C"], "source_tasks": ["T-P"], "member": "annex column C",
         "expect": _x("C", "STR.CONC.COLUMN"), "after": {"low": C[0], "high": C[1]},
         "basis": "0.09 x 2.99 .. 3.40", "why_held": "slab top", "question": "slab top", "existence": dict(DC),
         "plane": dict(PLANE)},
    ]


def doc(ents=None):
    return {"schema": A.INPUTS_SCHEMA, "project_id": PID, "sources": [_src("T-P")],
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
    assert W1 == (0.056, 0.068) and D1 == (0.051, 0.063) and D2_LO == 0.036
    assert PC == (0.15, 0.24) and S_LO == 3.19 and C == (0.2691, 0.306) and SPARE == 0.17
    assert round(W1[0] + D1[0] + D2_LO, 6) == 0.143                # the lintel low incl. the open line's beside


def test_states_and_records():
    prev, ch, log = run()
    assert log["by_action"] == {"BOUND": 4, "LOWER_ONLY": 1} and log["lines"] == 5
    assert log["assumed_owner_approved"] == [{"line_id": ID["LINTEL:D1"], "trigger_m": 2.37}]
    assert log["plane_transferred"] == [ID["LINTEL:D1"], ID["C"]]
    new, ident = A.integrate(prev, ch)
    d1 = _by(new, "LINTEL:D1")
    r = d1["calculation"]["inputs"][A.REC_KEY]
    assert d1["evidence_state"] == "BOUNDED_EXPOSURE" and (d1["bounded_range"]["low"], d1["bounded_range"]["high"]) == D1
    assert r["existence"]["status"] == OA and r["assumption"]["trigger_m"] == 2.37
    assert "2.370" in d1["calculation"]["formula"] and "Q-55 C" in d1["calculation"]["formula"]
    assert r["plane"]["state"] == "ONE_PLANE" and r["superseded"]["lintel_v3053"]["opening_id"] == "D1"
    assert "lintel_v3053" not in d1["calculation"]["inputs"]
    d2 = _by(new, "LINTEL:D2")
    assert d2["evidence_state"] == "BLOCKED_RFI" and d2["measured_net"] is None and d2["bounded_range"] is None
    assert "0.036" in d2["calculation"]["formula"]
    c = _by(new, "C")
    assert "concrete_ledger_v3065" not in c["calculation"]["inputs"]
    assert c["calculation"]["inputs"][A.REC_KEY]["superseded"] == V65
    assert ident["concrete"] == {"BOUND": 4, "LOWER_ONLY": 1, "assumed": 1, "plane": 2}
    assert ident["lintels"] == {"restated_v3_0_67": 3, "other": 2}
    assert ident["checks_v3_0_66"]["lintels_v3_0_66"] == {"restated": 1, "shared": 0, "v3_0_53": 1}
    assert ident["replaced"] == 5 and ident["added"] == 0 and ident["outside_rows"] == 4
    for e in ("LINTEL:L9", "LINTEL:L5", "CR", "R1:PLASTER"):
        assert A30.line_sha(_by(new, e)) == A30.line_sha(_by(prev, e)), e


def test_code_totals_hand(tmp_path):
    prev, ch, log = run()
    new, _ = A.integrate(prev, ch)
    t0, t1 = A304.code_totals(prev), A304.code_totals(new)
    a0, a1 = t0["STR.CONC.LINTEL|m3"], t1["STR.CONC.LINTEL|m3"]
    assert (a0["bounded_lines"], a0["blocked_lines"]) == (1, 4) and (a1["bounded_lines"], a1["blocked_lines"]) == (3, 2)
    assert abs(a1["held_low"] - 0.117) < 1e-9 and abs(a1["held_high"] - 0.151) < 1e-9
    c1 = t1["STR.CONC.COLUMN|m3"]
    assert abs(c1["released"] - 0.36) < 1e-9 and abs(t0["STR.CONC.COLUMN|m3"]["released"] - 0.36) < 1e-9
    assert abs(c1["held_low"] - 0.4191) < 1e-9 and abs(c1["held_high"] - 0.546) < 1e-9 and c1["bounded_lines"] == 2
    moved = A.check_totals(t0, t1, ch, {"STR.CONC.LINTEL|m3": {"held_low": 0.117}})
    assert set(moved) == {"STR.CONC.LINTEL|m3", "STR.CONC.COLUMN|m3"}
    names, ident, led = A.write(tmp_path, prev, ch, log)
    assert "V3_0_67_BOQ_LINES.json" in names and led["integration_package"] is True
    r = json.loads((tmp_path / "V3_0_67_RUN.json").read_text(encoding="utf-8"))
    assert r["identity"]["diff"]["vs_base"] == {"SAME": 4, "CHANGED": 4, "CHANGED_TEXT_ONLY": 1}       # D2 blank
    assert r["released_default"] is False and "T677_LINTEL_DESIGNER_OPEN" not in r["waiting_pieces"]
    assert "T682_OWNER_FALLBACK" in r["waiting_pieces"]
    rows = {x["line_id"]: x for x in led["rows"]}
    assert rows[ID["LINTEL:D1"]]["existence"]["status"] == OA
    csv = (tmp_path / "V3_0_67_INTEGRATION_LEDGER.csv").read_text(encoding="utf-8")
    assert "trigger 2.370 m" in csv and "plane ONE_PLANE" in csv


def test_reordered_villa_same_result():
    prev, ch, _ = run()
    new = A.integrate(prev, ch)[0]
    p2, ch2, _ = run(doc(list(reversed(entries()))), list(reversed(copy.deepcopy(LN))))
    new2 = A.integrate(p2, ch2)[0]
    assert sorted(A30.line_sha(x) for x in new) == sorted(A30.line_sha(x) for x in new2)


# ------------------------------------------------------------------------------------------------ adverse
@pytest.mark.parametrize("i,kw,msg", [
    (0, {"action": "VALUE", "after": {"value": 0.06}, "remeasure": "x"}, "BOUND or LOWER_ONLY only"),
    (0, {"action": "REVALUE"}, "BOUND or LOWER_ONLY only"),
    (0, {"expect": _x("LINTEL:W1", "STR.CONC.LINTEL", cls="RELEASED")}, "HELD blank"),
    (0, {"expect": _x("LINTEL:W1", "STR.CONC.LINTEL", (0.01, 0.02))}, "HELD blank"),
    (0, {"existence": None}, "existence status"),
    (0, {"existence": {"status": "VERIFIED", "basis": "x"}}, "existence status"),
    (0, {"assumption": "x"}, "belongs to an"),
    (1, {"assumption": None}, "assumption must be a record"),
    (1, {"assumption": dict(_assume(), trigger_m=2.40)}, "is not assumed"),
    (1, {"assumption": dict(_assume(), rerun_trigger="a higher head reverses existence")}, "does not state 2.370"),
    (1, {"assumption": dict(_assume(), status="DRAWING-CONFIRMED")}, "an assumption is"),
    (1, {"plane": dict(PLANE, state="STEPPED")}, "transfers nothing"),
    (1, {"plane": dict(PLANE, sections_checked=[])}, "no section read"),
    (1, {"plane": dict(PLANE, section_steps=[{"section": "B-B", "step_m": "0.20", "inside_plane": True,
                                               "evidence": "x"}])}, "inside the plane or unplaced"),
    (1, {"plane": dict(PLANE, section_steps=[{"section": "B-B", "step_m": "0.20", "evidence": "x"}])},
     "inside the plane or unplaced"),
    (1, {"plane": dict(PLANE, rule="R-T678-2 1.0.0")}, "plane record"),
    (2, {"beside": {"kind": "AT_MOST_M3", "value": 0.05, "basis": "x"}}, "AT_LEAST"),
    (0, {"after": {"low": 0.0, "high": 0.068}}, "outside 0"),
    (0, {"source_tasks": ["T-X"]}, "no merged source"),
])
def test_adverse_inputs(i, kw, msg):
    with pytest.raises(A.InputsError, match=msg):
        run(_mut(i, **kw))


def test_stale_binding_and_v66_line_refused():
    es = entries()
    es[0]["line_id"] = ID["LINTEL:L9"]
    es[0]["expect"] = _x("LINTEL:L9", "STR.CONC.LINTEL")
    with pytest.raises(A.InputsError, match="stale binding"):           # L9 is bounded now
        run(doc(es))
    prev = copy.deepcopy(LN)
    l9 = _by(prev, "LINTEL:L9")
    l9["evidence_state"], l9["bounded_range"] = "BLOCKED_RFI", None       # a blank line V3.0.66 restated
    es[0]["expect"] = _x("LINTEL:L9", "STR.CONC.LINTEL")
    with pytest.raises(A.InputsError, match="V3.0.53 HELD record"):
        run(doc(es), prev)


def test_applied_twice_and_named_twice():
    prev, ch, _ = run()
    new = A.integrate(prev, ch)[0]
    with pytest.raises(A.InputsError, match="applied once"):
        run(prev=new)
    with pytest.raises(A.InputsError, match="named twice"):
        run(doc(entries() + [entries()[0]]))


def test_tampered_states_refused():
    prev, ch, _ = run()
    new = A.integrate(prev, ch)[0]
    bad = copy.deepcopy(new)
    _by(bad, "LINTEL:W1")["calculation"]["inputs"][A.REC_KEY]["existence"] = {"status": "UNKNOWN"}
    with pytest.raises(ValueError, match="not in its state"):
        A.check_concrete(bad)
    bad = copy.deepcopy(new)
    _by(bad, "LINTEL:D1")["calculation"]["inputs"][A.REC_KEY]["plane"]["state"] = "STEPPED"
    with pytest.raises(ValueError, match="not in its state"):
        A.check_concrete(bad)
    bad = copy.deepcopy(new)
    x = _by(bad, "LINTEL:W1")["calculation"]["inputs"][A.REC_KEY]["superseded"]["lintel_v3053"]
    x["opening_id"] = "D2"
    with pytest.raises(ValueError, match="two lintel lines"):
        A.check_lintels(bad)
    bad = copy.deepcopy(new)
    r1 = _by(bad, "CR")
    r1["measured_net"] = r1["gross"] = 0.06
    with pytest.raises(ValueError, match="released concrete moved"):
        A.check_concrete(bad, prev)


def test_integrate_refuses_outside_change_and_add():
    prev, ch, _ = run()
    c = copy.deepcopy(ch[0])
    c["action"] = "ADD"
    with pytest.raises(ValueError, match="adds no line"):
        A.integrate(prev, [c])
    c = copy.deepcopy(ch[0])
    c["after"] = dict(c["after"], item_code="FIN.PLASTER")
    with pytest.raises(ValueError, match="may touch"):
        A.integrate(prev, [c])
