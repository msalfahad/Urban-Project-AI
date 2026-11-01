"""T-429: ARCH_TAKEOFF_V3.0.39 (stair tread / step binding: one physical flight, one valued tread and step line) on a
hand-calculated NON-Alsenan villa (K429).

Villa K429, by hand (own figures; nothing from the development villa). Straight goings 0.280 m, width 1.000 m.
  A  GF flight +0.15 -> +1.80, 10 drawn fronts (2 hidden above the cut); the GF reading carries 8 treads:
     tread 8 x 0.28 x 1.0 = 2.240 m2 -> 10 x 0.28 = 2.800 m2; step 8.000 -> 10.000 lm (CORRECT).
  B  1F flight +1.80 -> +3.45, 9 drawn fronts: 1F reading 2.520 m2 / 9.000 lm (KEEP, carrier); the 2F plan draws the
     same treads at the same run positions and levels (SEEN_THROUGH): 2F reading 2.520 / 9.000 -> SUPERSEDED, its riser
     line too (DOUBLE_COUNT, owned by the 1F lines).
  C  2F flight +3.45 -> +5.10 drawn at B's plan position on 2F's east lane, a different level span (STACKED): 6 drawn
     fronts, the last going undrawn: tread 5 x 0.28 = 1.400 m2 valued + 0.280 HELD beside; step 6.000 lm
     (CORRECT from 5.000).
  W  winder turn +1.62 -> +1.80 read from 1F: 1.100 m2 / 3.900 lm valued -> HOLD (winders never generated), blank,
     beside 1.100 m2 / 3.900 lm.
Valued B7-02: 2.240 + 2.520 + 2.520 + 1.400 + 1.100 = 9.780 -> 2.800 + 2.520 + 1.400 = 6.720 m2 (-3.060).
Valued B7-06: 8 + 9 + 9 + 5 + 3.9 = 34.900 -> 10 + 9 + 6 = 25.000 lm (-9.900).
"""
from __future__ import annotations

import copy
import random
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v30 as A30  # noqa: E402
from engine.source import arch_v304 as A304  # noqa: E402
from engine.source import arch_v3039 as A  # noqa: E402
from engine.source import boq_line as BL  # noqa: E402

PID, REV = "villa-k429", "f" * 64
DOCS = [{"file": "k429_plan.dxf", "sha256": "d" * 64}]
DC = "DRAWING-CONFIRMED"
TREAD, STEP, RISER = A.TREAD, A.STEP, A.RISER


def _src(t):
    return {"task": t, "file": f"research/k429/{t}.csv", "sha256": t[-1] * 64, "merge_commit": "a" * 40,
            "checker_run": f"checker {t} Gate A PASS"}


def _line(code, unit, floor, k, flight_id, net=None, ev="PROVISIONAL", rfi=None):
    return BL.make_line(project_id=PID, revision_set_sha256=REV, item_code=code, unit=unit, evidence_state=ev,
                        measured_net=net, element_id=f"{floor}-STAIR:flight {k}", floor=floor,
                        room_id=f"{floor}-STAIR", physical_element=f"flight {k}", gross=net, formula="engine reading",
                        inputs={"flight_id": flight_id}, documents=DOCS, rule_id="UP-STAIR-003", rule_version="1",
                        rfi=rfi, notes="k")


def lines_3038():
    q = {"question": "riser height", "unlocks": "x"}
    return [
        _line(TREAD, "m2", "GF", 1, "GF:F1", 2.24), _line(STEP, "lm", "GF", 1, "GF:F1", 8.0),
        _line(TREAD, "m2", "1F", 1, "1F:F1", 2.52), _line(STEP, "lm", "1F", 1, "1F:F1", 9.0),
        _line(RISER, "m2", "1F", 1, "1F:F1", ev="BLOCKED_RFI", rfi=q),
        _line(TREAD, "m2", "2F", 1, "2F:F1", 2.52), _line(STEP, "lm", "2F", 1, "2F:F1", 9.0),
        _line(RISER, "m2", "2F", 1, "2F:F1", ev="BLOCKED_RFI", rfi=q),
        _line(TREAD, "m2", "2F", 2, "2F:F2", 1.4), _line(STEP, "lm", "2F", 2, "2F:F2", 5.0),
        _line(TREAD, "m2", "1F", 2, "1F:F2", 1.1), _line(STEP, "lm", "1F", 2, "1F:F2", 3.9),
        _line(RISER, "m2", "1F", 2, "1F:F2", ev="BLOCKED_RFI", rfi=q),
        _line("FIN.FLOOR.PORCELAIN", "m2", "GF", 9, "-", 40.0, ev="SOURCE_DERIVED"),
    ]


def _id(lines, code, floor, k):
    return next(x["line_id"] for x in lines if x["item_code"] == code and x["location"]["floor"] == floor
                and x["location"]["element_id"].endswith(f"flight {k}"))


def _r(lid, fam, reading, flight, role, plan, action, before, after, ev=DC, **kw):
    return dict({"line_id": lid, "family": fam, "reading": reading, "flight": flight, "role": role, "plan": plan,
                 "action": action, "before": before, "after": after, "supersede": None, "held_beside": None,
                 "beside": [], "cause": "k429", "evidence_status": ev, "source_tasks": ["T-425"]}, **kw)


def inputs(lines, **over):
    i = lambda c, f, k: _id(lines, c, f, k)  # noqa: E731
    held = {"cause": "WINDER_SUBDIVISION_NOT_DRAWN: winders never generated", "count": 4, "source": "S-9"}
    doc = {"schema": A.INPUTS_SCHEMA, "project_id": PID, "sources": [_src("T-425"), _src("T-434")],
           "flights": [
               {"flight": "A", "stair": "S1", "levels": [0.15, 1.80], "drawn_treads": 10, "width": 1.0, "going": 0.28,
                "held": None, "source_tasks": ["T-425"]},
               {"flight": "B", "stair": "S1", "levels": [1.80, 3.45], "drawn_treads": 9, "width": 1.0, "going": 0.28,
                "held": None, "source_tasks": ["T-425"]},
               {"flight": "C", "stair": "S1", "levels": [3.45, 5.10], "drawn_treads": 6, "width": 1.0, "going": 0.28,
                "held": None, "source_tasks": ["T-425"]},
               {"flight": "W", "stair": "S1", "levels": [1.62, 1.80], "drawn_treads": 4, "width": 1.0, "going": None,
                "held": held, "source_tasks": ["T-425", "T-434"]}],
           "readings": [
               _r(i(TREAD, "GF", 1), "B7-02", "GF:F1", "A", "OWN", "GF", "CORRECT", 2.24, 2.8),
               _r(i(STEP, "GF", 1), "B7-06", "GF:F1", "A", "OWN", "GF", "CORRECT", 8.0, 10.0),
               _r(i(TREAD, "1F", 1), "B7-02", "1F:F1", "B", "OWN", "1F", "KEEP", 2.52, 2.52, ev="VERIFIED"),
               _r(i(STEP, "1F", 1), "B7-06", "1F:F1", "B", "OWN", "1F", "KEEP", 9.0, 9.0, ev="VERIFIED"),
               _r(i(RISER, "1F", 1), "B7-03", "1F:F1", "B", "OWN", "1F", "KEEP", None, None),
               _r(i(TREAD, "2F", 1), "B7-02", "2F:F1", "B", "SEEN_THROUGH", "2F", "SUPERSEDE", 2.52, None,
                  ev="NOT_APPLICABLE", supersede={"kind": "DOUBLE_COUNT", "carrier_line": i(TREAD, "1F", 1)}),
               _r(i(STEP, "2F", 1), "B7-06", "2F:F1", "B", "SEEN_THROUGH", "2F", "SUPERSEDE", 9.0, None,
                  ev="NOT_APPLICABLE", supersede={"kind": "DOUBLE_COUNT", "carrier_line": i(STEP, "1F", 1)}),
               _r(i(RISER, "2F", 1), "B7-03", "2F:F1", "B", "SEEN_THROUGH", "2F", "SUPERSEDE", None, None,
                  ev="NOT_APPLICABLE", supersede={"kind": "DOUBLE_COUNT", "carrier_line": i(RISER, "1F", 1)}),
               _r(i(TREAD, "2F", 2), "B7-02", "2F:F2", "C", "OWN", "2F", "CORRECT", 1.4, 1.4,
                  held_beside={"value": 0.28, "why": "TREAD_GOING_NOT_DRAWN: last going"}),
               _r(i(STEP, "2F", 2), "B7-06", "2F:F2", "C", "OWN", "2F", "CORRECT", 5.0, 6.0),
               _r(i(TREAD, "1F", 2), "B7-02", "1F:F2", "W", "SEEN_THROUGH", "1F", "HOLD", 1.1, None, ev="HELD",
                  beside=[{"value": 1.1, "unit": "m2", "basis": "candidate figure"}]),
               _r(i(STEP, "1F", 2), "B7-06", "1F:F2", "W", "SEEN_THROUGH", "1F", "HOLD", 3.9, None, ev="HELD",
                  beside=[{"value": 3.9, "unit": "lm", "basis": "candidate figure"}]),
               _r(i(RISER, "1F", 2), "B7-03", "1F:F2", "W", "SEEN_THROUGH", "1F", "HOLD", None, None, ev="HELD")]}
    doc.update(over)
    return doc


def run(lines=None, doc=None):
    lines = lines or lines_3038()
    d = A.load_inputs(doc or inputs(lines), PID)
    ch, log = A.changes_for(d, lines)
    out, ident = A.integrate(lines, ch, (), d)
    return lines, ch, log, out, ident


def _get(out, code, floor, k):
    return next(x for x in out if x["item_code"] == code and x["location"]["floor"] == floor
                and x["location"]["element_id"].endswith(f"flight {k}"))


def _valued(out, code):
    return round(sum(x["measured_net"] for x in out if x["item_code"] == code
                     and x["evidence_state"] in A.VALUED), 6)


# ------------------------------------------------------------------------------------------------ normal cases
def test_hand_figures():
    lines, ch, log, out, ident = run()
    assert _valued(lines, TREAD) == 9.78 and _valued(lines, STEP) == 34.9
    assert _valued(out, TREAD) == 6.72 and _valued(out, STEP) == 25.0
    assert _get(out, TREAD, "GF", 1)["measured_net"] == 2.8 and _get(out, STEP, "GF", 1)["measured_net"] == 10.0
    assert _get(out, STEP, "2F", 2)["measured_net"] == 6.0 and _get(out, TREAD, "2F", 2)["measured_net"] == 1.4
    assert log["by_action"] == {"CORRECT": 4, "HOLD": 3, "KEEP": 3, "SUPERSEDE": 3}
    assert ident["replaced"] == 10 and ident["added"] == 0 and ident["v3_0_39_lines"] == len(lines)
    assert ident["flights"]["corrected"] == 4 and ident["flights"]["superseded"] == 3 and ident["flights"]["held"] == 3


def test_seen_through_listed_without_quantity_owned_by_carrier():
    lines, _ch, _log, out, _i = run()
    for code in (TREAD, STEP, RISER):
        s = _get(out, code, "2F", 1)
        rec = s["calculation"]["inputs"][A.REC_KEY]
        assert s["evidence_state"] == "NOT_APPLICABLE_WITH_EVIDENCE" and s["measured_net"] is None
        assert rec["owned_by"] == _get(out, code, "1F", 1)["line_id"] and rec["kind"] == "DOUBLE_COUNT"
        assert s["line_id"] == _get(lines, code, "2F", 1)["line_id"]          # never deleted, same id


def test_held_flight_blank_with_figure_beside_never_zero():
    _l, _ch, _log, out, _i = run()
    for code, v in ((TREAD, 1.1), (STEP, 3.9)):
        h = _get(out, code, "1F", 2)
        rec = h["calculation"]["inputs"][A.REC_KEY]
        assert h["evidence_state"] == "BLOCKED_RFI" and h["measured_net"] is None and h["bounded_range"] is None
        assert "WINDER_SUBDIVISION_NOT_DRAWN" in h["rfi"]["question"] and rec["held_count"] == 4
        assert [x["value"] for x in rec["beside"]] == [v]
    r = _get(out, RISER, "1F", 2)
    assert r["evidence_state"] == "BLOCKED_RFI" and "WINDER" in r["rfi"]["question"]


def test_undrawn_going_held_beside_valued_line():
    _l, ch, _log, out, _i = run()
    t = _get(out, TREAD, "2F", 2)
    assert t["measured_net"] == 1.4 and t["calculation"]["inputs"][A.REC_KEY]["held_beside"]["value"] == 0.28
    c = next(c for c in ch if c["after"]["line_id"] == t["line_id"])
    assert c["held"][0]["beside"] == 0.28 and c["held"][0]["range"] is None


def test_level_test_seen_through_vs_stacked():
    assert A.level_class((1.80, 3.45), (1.80, 3.45), "1F", "2F") == "SEEN_THROUGH"
    assert A.level_class((1.80, 3.45), (3.45, 5.10), "1F", "2F") == "STACKED"
    assert A.level_class((1.80, 3.45), (1.80, 3.45), "1F", "1F") == "SAME_PLAN"


def test_only_named_lines_change_and_totals_only_own_codes():
    lines, ch, _log, out, ident = run()
    named = {c["after"]["line_id"] for c in ch}
    for a, b in zip(lines, out):
        if a["line_id"] not in named:
            assert A30.line_sha(a) == A30.line_sha(b)
    t0, t1 = A304.code_totals(lines), A304.code_totals(out)
    moved = {k for k in set(t0) | set(t1) if t0.get(k) != t1.get(k)}
    assert moved and all(k.split("|")[0] in A.OWN_CODES for k in moved)
    assert ident["outside_rows"] == len(lines) - 10


def test_order_invariance():
    lines = lines_3038()
    _l, _c, _g, out, _i = run(lines)
    sh = copy.deepcopy(lines)
    random.Random(7).shuffle(sh)
    doc = inputs(lines)
    random.Random(3).shuffle(doc["readings"])
    _l2, _c2, _g2, out2, _i2 = run(sh, doc)
    a = {x["line_id"]: A30.line_sha(x) for x in out}
    b = {x["line_id"]: A30.line_sha(x) for x in out2}
    assert a == b


def test_write_files(tmp_path):
    lines = lines_3038()
    d = A.load_inputs(inputs(lines), PID)
    ch, log = A.changes_for(d, lines)
    names, ident, led = A.write(tmp_path, lines, ch, log, None, (), d)
    assert "V3_0_39_BOQ_LINES.json" in names and led["integration_package"] is True
    assert ident["diff"]["vs_v3_0_38"] == {"SAME": len(lines) - 10, "CHANGED": 10}


# ------------------------------------------------------------------------------------------------ adverse cases
def test_same_flight_valued_on_two_plans_refused():
    lines = lines_3038()
    doc = inputs(lines)
    r = next(x for x in doc["readings"] if x["action"] == "SUPERSEDE" and x["family"] == "B7-02")
    r.update(action="KEEP", after=2.52, supersede=None, evidence_status=DC, role="OWN")
    with pytest.raises(A.InputsError, match="DOUBLE_COUNT"):
        A.load_inputs(doc, PID)


def test_seen_through_as_carrier_refused():
    lines = lines_3038()
    doc = inputs(lines)
    r = next(x for x in doc["readings"] if x["action"] == "SUPERSEDE" and x["family"] == "B7-06")
    r.update(action="CORRECT", after=9.0, supersede=None, evidence_status=DC)
    with pytest.raises(A.InputsError, match="never the carrier"):
        A.load_inputs(doc, PID)


def test_held_as_zero_refused():
    lines = lines_3038()
    doc = inputs(lines)
    next(x for x in doc["readings"] if x["action"] == "HOLD")["after"] = 0.0
    with pytest.raises(A.InputsError, match="HELD_AS_ZERO"):
        A.load_inputs(doc, PID)


def test_held_flight_valued_refused():
    lines = lines_3038()
    doc = inputs(lines)
    r = next(x for x in doc["readings"] if x["action"] == "HOLD" and x["family"] == "B7-06")
    r.update(action="KEEP", after=3.9, evidence_status=DC, beside=[])
    with pytest.raises(A.InputsError, match="HELD"):
        A.load_inputs(doc, PID)


def test_width_in_mm_refused():
    lines = lines_3038()
    doc = inputs(lines)
    doc["flights"][0]["width"] = 1000
    with pytest.raises(A.InputsError, match="mm refused"):
        A.load_inputs(doc, PID)


def test_levels_in_mm_refused():
    lines = lines_3038()
    doc = inputs(lines)
    doc["flights"][0]["levels"] = [150, 1800]
    with pytest.raises(A.InputsError, match="mm refused"):
        A.load_inputs(doc, PID)


def test_step_not_drawn_count_times_width_refused():
    lines = lines_3038()
    doc = inputs(lines)
    next(x for x in doc["readings"] if x["family"] == "B7-06" and x["action"] == "CORRECT")["after"] = 9.0
    with pytest.raises(A.InputsError, match="R-T425-2"):
        A.load_inputs(doc, PID)


def test_lines_minus_one_tread_count_refused():
    lines = lines_3038()
    doc = inputs(lines)
    next(x for x in doc["readings"] if x["family"] == "B7-02" and x["action"] == "CORRECT")["after"] = 2.52
    with pytest.raises(A.InputsError, match="R-T425-2"):
        A.load_inputs(doc, PID)


def test_unknown_flight_refused():
    lines = lines_3038()
    doc = inputs(lines)
    doc["readings"][0]["flight"] = "GHOST"
    with pytest.raises(A.InputsError, match="UNBOUND"):
        A.load_inputs(doc, PID)


def test_zero_drawn_treads_refused():
    lines = lines_3038()
    doc = inputs(lines)
    doc["flights"][1]["drawn_treads"] = 0
    with pytest.raises(A.InputsError, match="never 0"):
        A.load_inputs(doc, PID)


def test_stale_binding_refused():
    lines = lines_3038()
    doc = inputs(lines)
    doc["readings"][0]["before"] = 2.0
    with pytest.raises(A.InputsError, match="stale binding"):
        A.changes_for(A.load_inputs(doc, PID), lines)


def test_wrong_flight_id_refused():
    lines = lines_3038()
    doc = inputs(lines)
    doc["readings"][0]["reading"] = "GF:F9"
    with pytest.raises(A.InputsError, match="stale binding"):
        A.changes_for(A.load_inputs(doc, PID), lines)


def test_applied_twice_refused():
    lines, _ch, _log, out, _i = run()
    with pytest.raises(A.InputsError, match="applied once"):
        A.changes_for(A.load_inputs(inputs(lines), PID), out)


def test_carrier_of_other_flight_refused():
    lines = lines_3038()
    doc = inputs(lines)
    r = next(x for x in doc["readings"] if x["action"] == "SUPERSEDE" and x["family"] == "B7-02")
    r["supersede"]["carrier_line"] = _id(lines, TREAD, "GF", 1)
    with pytest.raises(A.InputsError, match="carrier"):
        A.load_inputs(doc, PID)


def test_superseded_line_with_quantity_caught_by_check():
    _l, _ch, _log, out, _i = run()
    bad = copy.deepcopy(out)
    s = _get(bad, TREAD, "2F", 1)
    s["evidence_state"], s["measured_net"] = "PROVISIONAL", 2.52
    with pytest.raises(ValueError, match="double count"):
        A.check_flights(bad)


def test_two_valued_readings_caught_by_check():
    lines, _ch, _log, out, _i = run()
    d = A.load_inputs(inputs(lines), PID)
    bad = copy.deepcopy(out)
    i = next(k for k, x in enumerate(bad) if x["line_id"] == _get(out, TREAD, "2F", 1)["line_id"])
    bad[i] = copy.deepcopy(_get(lines, TREAD, "2F", 1))       # the original seen-through reading, valued again
    with pytest.raises(ValueError, match="DOUBLE_COUNT"):
        A.check_flights(bad, d)


def test_change_outside_own_codes_refused():
    lines, ch, _log, _o, _i = run()
    bad = copy.deepcopy(ch)
    bad[0]["after"]["item_code"] = "FIN.FLOOR.PORCELAIN"
    with pytest.raises(ValueError, match="not a code this version may change"):
        A.integrate(lines, bad)
