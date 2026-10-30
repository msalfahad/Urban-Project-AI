"""T-326: ARCH_TAKEOFF_V3.0.28 (opening reveal faces booked once each from a checker-merged reveal ledger) on a
hand-calculated NON-Alsenan villa (V326), normal and adverse.

Villa V326, by hand (wall t 0.20 m, window frames drawn flush with the room face -> room side NONE; outside depth
0.20 - 0.12 frame band = 0.08 m; doors one reveal through the wall, UP-FIN-PLASTER-001 2 x t x h + t x w):
  W1 1.20 x 1.50, has a blank ARCH.WINDOW_REVEAL strip line (w x 0.20 = 0.240 m2 plan strip, frame bed included):
     outside sill 0.08 x 1.20 = 0.096 m2 -> FILL (never 0.240: the 0.12 frame bed is not a finish surface)
     outside jambs 2 x 0.08 x 1.50 = 0.240 + head 0.08 x 1.20 = 0.096 -> ADD ARCH.WINDOW_REVEAL (jambs + head) 0.336
  W2 0.60 x 0.60, NO strip line: sill 0.08 x 0.60 = 0.048 -> ADD ARCH.WINDOW_REVEAL (sill) 0.048;
     jambs 2 x 0.08 x 0.60 = 0.096 + head 0.048 -> ADD ARCH.WINDOW_REVEAL (jambs + head) 0.144
  W3 curved: outside jambs / head UNRESOLVED -> ADD one BLANK line naming both (never 0)
  D1 0.90 x 2.20 (Q-55 C), t 0.15, no plaster line: 2 x 0.15 x 2.20 + 0.15 x 0.90 = 0.660 + 0.135 = 0.795 m2
     -> ADD FIN.PLASTER 'door jambs and head' (PROVISIONAL)
  D2 0.80, t 0.15, already in a FIN.PLASTER 'door jambs and head' line 0.780: carried, never added again
  D3 2.00 wide, t 0.20, FIN.PLASTER bound 1.28 .. 1.40 (h class 2.20 / 2.50 pending), h 2.50 PRINTED:
     2 x 0.20 x 2.50 + 0.20 x 2.00 = 1.000 + 0.400 = 1.400 m2 -> NARROW
  totals moved: ARCH.WINDOW_REVEAL +0.096 +0.048 +0.480 (B4-08, no new item code); FIN.PLASTER +0.795 + 1.400
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
from engine.source import arch_v3028 as A  # noqa: E402
from engine.source import boq_line as BL  # noqa: E402

PID, REV = "villa-v326", "e" * 64
DOCS = [{"file": "v326_plan.dxf", "sha256": "d" * 64}]
SRC = {"T-313": {"task": "T-313", "file": "research/v326/reveal.csv", "sha256": "3" * 64, "merge_commit": "c" * 40,
                 "checker_run": "checker run 9 (Gate A PASS)"},
       "T-325": {"task": "T-325", "file": "research/v326/sills.csv", "sha256": "4" * 64, "merge_commit": "d" * 40,
                 "checker_run": "checker run 10 (Gate A PASS)"}}


def _strip(op, w):
    return BL.make_line(project_id=PID, revision_set_sha256=REV, item_code="ARCH.WINDOW_REVEAL", unit="m2",
                        evidence_state="BLOCKED_RFI", element_id=f"GF-STRIP-{op}:window reveal strip", floor="GF",
                        physical_element="window reveal strip", formula=f"strip {w} x 0.20 (floor status open)",
                        documents=DOCS, rule_id="R", rule_version="1",
                        rfi={"question": "WINDOW_REVEAL_FLOOR_STATUS_NOT_ESTABLISHED"}, notes="v326")


def _door(op, **kw):
    return BL.make_line(project_id=PID, revision_set_sha256=REV, item_code="FIN.PLASTER", unit="m2",
                        element_id=f"GF-{op}:door jambs and head", floor="GF", physical_element="door jambs and head",
                        documents=DOCS, rule_id="UP-FIN-PLASTER-001", rule_version="1", notes="v326", **kw)


def lines_3027():
    room = BL.make_line(project_id=PID, revision_set_sha256=REV, item_code="FIN.PLASTER", unit="m2",
                        evidence_state="MEASURED", measured_net=30.0, element_id="GF-01:walls", floor="GF",
                        physical_element="room walls", formula="room walls = 30 m2", documents=DOCS, rule_id="R",
                        rule_version="1")
    return [room, _strip("W1", 1.2),
            _door("D2", evidence_state="PROVISIONAL", measured_net=0.78, formula="2 x 0.15 x 2.20 + 0.15 x 0.80 = 0.78 m2"),
            _door("D3", evidence_state="BOUNDED_EXPOSURE", bounded_range={"basis": "h class", "low": 1.28, "high": 1.4},
                  formula="door class pending", rfi={"question": "h 2.20 or 2.50"}),
            BL.make_line(project_id=PID, revision_set_sha256=REV, item_code="ARCH.THRESHOLD", unit="m2",
                         evidence_state="BLOCKED_RFI", element_id="GF-CLOSURE:D1", floor="GF",
                         physical_element="threshold strip", formula="closure strip", documents=DOCS, rule_id="R",
                         rule_version="1", rfi={"question": "finish"}, notes="v326")]


def _id(lines, eid):
    return next(ln["line_id"] for ln in lines if ln["location"]["element_id"] == eid)


def _c(comp, m2, basis, state="MEASURED", ev="DRAWING-CONFIRMED"):
    return {"component": comp, "m2": m2, "ml": None, "depth_m": 0.08, "basis": basis, "state": state, "evidence": ev,
            "height_status": "PRINTED"}


def doc(lines=None):
    lines = lines or lines_3027()
    return {
        "schema": A.INPUTS_SCHEMA, "project_id": PID, "unit": "m2", "sources": list(SRC.values()),
        "fills": [{"line_id": _id(lines, "GF-STRIP-W1:window reveal strip"), "opening": "W1", "kind": "WINDOW",
                   "floor": "GF", "component": "SILL", "side": "OUT", "m2": 0.096, "ml": 1.2, "depth_m": 0.08,
                   "basis": "external sill 0.080 x 1.200", "evidence": "DRAWING-CONFIRMED", "material": "UNKNOWN",
                   "source_task": "T-313", "cross_check": "T-325 equal"}],
        "narrow": [{"line_id": _id(lines, "GF-D3:door jambs and head"), "opening": "D3",
                    "before": {"low": 1.28, "high": 1.4}, "m2": 1.4,
                    "components": [{"component": "JAMBS", "m2": 1.0, "basis": "2 x 0.200 x 2.500",
                                    "evidence": "DRAWING-CONFIRMED"},
                                   {"component": "HEAD", "m2": 0.4, "basis": "0.200 x 2.000",
                                    "evidence": "DRAWING-CONFIRMED"}],
                    "basis": "h 2.50 printed: 2 x 0.20 x 2.50 + 0.20 x 2.00", "source_task": "T-313"}],
        "adds": [
            {"opening": "W1", "kind": "WINDOW", "floor": "GF", "side": "OUT", "item_code": "ARCH.WINDOW_REVEAL",
             "group": "JAMBS_HEAD", "status": "VALUED", "rooms": "GF-01", "source_task": "T-313",
             "components": [_c("JAMBS", 0.24, "2 x 0.080 x 1.500"), _c("HEAD", 0.096, "0.080 x 1.200")]},
            {"opening": "W2", "kind": "WINDOW", "floor": "GF", "side": "OUT", "item_code": "ARCH.WINDOW_REVEAL",
             "group": "SILL", "status": "VALUED", "rooms": "GF-01", "source_task": "T-313",
             "components": [_c("SILL", 0.048, "external sill 0.080 x 0.600")]},
            {"opening": "W2", "kind": "WINDOW", "floor": "GF", "side": "OUT", "item_code": "ARCH.WINDOW_REVEAL",
             "group": "JAMBS_HEAD", "status": "VALUED", "rooms": "GF-01", "source_task": "T-313",
             "components": [_c("JAMBS", 0.096, "2 x 0.080 x 0.600"), _c("HEAD", 0.048, "0.080 x 0.600")]},
            {"opening": "W3", "kind": "WINDOW", "floor": "GF", "side": "OUT", "item_code": "ARCH.WINDOW_REVEAL",
             "group": "JAMBS_HEAD", "status": "HELD", "rooms": "GF-02", "source_task": "T-313",
             "components": [_c("JAMBS", None, "curved wall: developed depth = 0.3 m2 not established", "UNRESOLVED",
                               "UNKNOWN"), _c("HEAD", None, "curved head", "UNRESOLVED", "UNKNOWN")]},
            {"opening": "D1", "kind": "DOOR", "floor": "GF", "side": "THROUGH", "item_code": "FIN.PLASTER",
             "group": "JAMBS_HEAD", "status": "VALUED", "rooms": "GF-01;GF-02", "source_task": "T-313",
             "components": [_c("JAMBS", 0.66, "2 x 0.150 x 2.200", ev="ASSUMED — OWNER-APPROVED (Q-55 C)"),
                            _c("HEAD", 0.135, "0.150 x 0.900")]}],
        "carried": [{"opening": "D2", "side": "THROUGH", "component": c, "line_id": _id(lines, "GF-D2:door jambs and head"),
                     "item_code": "FIN.PLASTER", "source_task": "T-313", "role": "door reveal"} for c in ("JAMBS", "HEAD")]
                   + [{"opening": "D1", "side": "THROUGH", "component": "THRESHOLD",
                       "line_id": _id(lines, "GF-CLOSURE:D1"), "item_code": "ARCH.THRESHOLD", "source_task": "T-325",
                       "role": "the door's floor face"}]}


def run(d=None, lines=None):
    lines = lines or lines_3027()
    d = d or doc(lines)
    inp = A.load_inputs(d, PID)
    ch, log = A.changes_for(inp, lines)
    out, ident = A.integrate(lines, ch)
    return lines, out, ident, ch, log


def _by(out, code, eid_part):
    return [ln for ln in out if ln["item_code"] == code and eid_part in ln["location"]["element_id"]]


# ------------------------------------------------------------------------------------------------ normal
def test_hand_figures():
    lines, out, ident, ch, log = run()
    w1 = _by(out, "ARCH.WINDOW_REVEAL", "STRIP-W1")[0]
    assert (w1["evidence_state"], w1["measured_net"]) == ("MEASURED", 0.096)      # never 0.240 (frame bed)
    assert _by(out, "ARCH.WINDOW_REVEAL", "W1:OUT:JAMBS_HEAD")[0]["measured_net"] == pytest.approx(0.336)
    assert _by(out, "ARCH.WINDOW_REVEAL", "W2:OUT:SILL")[0]["measured_net"] == pytest.approx(0.048)
    w2 = _by(out, "ARCH.WINDOW_REVEAL", "W2:OUT:JAMBS_HEAD")[0]
    assert w2["measured_net"] == pytest.approx(0.144) and "jambs and head" in w2["physical_element"]
    d1 = _by(out, "FIN.PLASTER", "D1:THROUGH")[0]
    assert (d1["evidence_state"], d1["measured_net"], d1["physical_element"]) == \
        ("PROVISIONAL", pytest.approx(0.795), "door jambs and head")
    d3 = _by(out, "FIN.PLASTER", "GF-D3")[0]
    assert (d3["evidence_state"], d3["measured_net"], d3["bounded_range"]) == ("PROVISIONAL", 1.4, None)
    w3 = _by(out, "ARCH.WINDOW_REVEAL", "W3:OUT")[0]
    assert w3["evidence_state"] == "BLOCKED_RFI" and w3["measured_net"] is None and "jambs" in w3["rfi"]["question"]
    rev = ident["opening_reveals"]
    assert (rev["filled"], rev["narrowed"], rev["added_valued"], rev["added_held"]) == (1, 1, 4, 1)
    assert rev["m2"] == {"ARCH.WINDOW_REVEAL": pytest.approx(0.624), "FIN.PLASTER": pytest.approx(2.195)}


def test_outside_lines_byte_identical_and_d2_not_added():
    lines, out, ident, ch, log = run()
    by = {ln["line_id"]: ln for ln in out}
    for ln in lines:
        if ln["location"]["element_id"] in ("GF-01:walls", "GF-D2:door jambs and head", "GF-CLOSURE:D1"):
            assert A30.line_sha(by[ln["line_id"]]) == A30.line_sha(ln)
    assert not _by(out, "FIN.PLASTER", "D2:THROUGH")
    assert ident["replaced"] == 2 and ident["added"] == 5 and ident["v3_0_28_lines"] == len(lines) + 5


def test_order_invariance():
    lines = lines_3027()
    d = doc(lines)
    d2 = copy.deepcopy(d)
    d2["adds"] = list(reversed(d2["adds"]))
    d2["carried"] = list(reversed(d2["carried"]))
    a = {ln["line_id"]: A30.line_sha(ln) for ln in run(d, lines)[1]}
    b = {ln["line_id"]: A30.line_sha(ln) for ln in run(d2, lines)[1]}
    assert a == b


def test_held_line_states_no_figure_in_its_text():
    from engine.source import arch_v3024 as A3024
    _l, out, *_ = run()
    w3 = _by(out, "ARCH.WINDOW_REVEAL", "W3:OUT")[0]
    assert A3024.scan([w3]) == {}                      # the '= 0.3 m2' of the basis is not stated as a result


def test_write_files(tmp_path):
    lines, out, ident, ch, log = run()
    names, ident2, led = A.write(tmp_path, lines, ch, log, None, released_lines=[])
    assert "V3_0_28_DIFF.csv" in names and led["integration_package"] is True
    run_doc = json.loads((tmp_path / "V3_0_28_RUN.json").read_text(encoding="utf-8"))
    assert set(run_doc["totals_moved_by_code"]) <= {"ARCH.WINDOW_REVEAL|m2", "FIN.PLASTER|m2"}
    assert ident2["diff"]["vs_v3_0_27"] == {"SAME": 3, "CHANGED": 2, "ADDED": 5}


# ------------------------------------------------------------------------------------------------ adverse
def _bad(mut, match):
    lines = lines_3027()
    d = doc(lines)
    mut(d, lines)
    with pytest.raises((A.InputsError, ValueError), match=match):
        run(d, lines)


def test_shared_jamb_counted_twice_refused():
    def m(d, lines):
        d["adds"].append({"opening": "D2", "kind": "DOOR", "floor": "GF", "side": "THROUGH", "item_code": "FIN.PLASTER",
                          "group": "JAMBS_HEAD", "status": "VALUED", "source_task": "T-313",
                          "components": [_c("JAMBS", 0.66, "2 x 0.150 x 2.200")]})
    _bad(m, "already carried")


def test_door_floor_face_in_a_reveal_line_refused():
    def m(d, lines):        # T-325: the door's floor face is its closure / threshold line, never a reveal face
        d["adds"][4]["components"].append(_c("THRESHOLD", 0.135, "0.15 x 0.90"))
    _bad(m, "not a JAMBS_HEAD face")


def test_door_floor_face_carried_by_its_closure_line_refused():
    def m(d, lines):        # the same face booked as a fill of a strip line: refused as a second carrier
        d["carried"].append({"opening": "W1", "side": "OUT", "component": "SILL", "line_id": d["carried"][-1]["line_id"],
                             "item_code": "ARCH.THRESHOLD", "source_task": "T-325", "role": "closure"})
    _bad(m, "already carried")


def test_reveal_with_no_depth_held_never_zero():
    def m(d, lines):
        d["adds"][3]["components"][0]["m2"] = 0.0
    _bad(m, "held face JAMBS given a figure")


def test_valued_face_at_zero_refused():
    def m(d, lines):
        d["adds"][0]["components"][0]["m2"] = 0.0
    _bad(m, "> 0 m2")


def test_fill_with_the_plan_strip_not_a_blank_line_refused():
    def m(d, lines):
        d["fills"][0]["line_id"] = _id(lines, "GF-D2:door jambs and head")
    _bad(m, "not a blank reveal strip")


def test_fill_with_jambs_refused():
    def m(d, lines):
        d["fills"][0]["component"] = "JAMBS"
    _bad(m, "external sill / threshold only")


def test_two_windows_on_one_line_refused():
    def m(d, lines):
        d["fills"].append(dict(d["fills"][0], opening="W9"))
    _bad(m, "second window")


def test_narrow_outside_bound_refused():
    def m(d, lines):
        d["narrow"][0]["m2"] = 1.5
        d["narrow"][0]["components"][0]["m2"] = 1.1
    _bad(m, "outside the line's bound")


def test_narrow_faces_not_summing_refused():
    def m(d, lines):
        d["narrow"][0]["components"][1]["m2"] = 0.3
    _bad(m, "do not sum")


def test_stale_line_refused():
    def m(d, lines):
        d["fills"][0]["line_id"] = "L-00000000000000000000"
    _bad(m, "does not carry this line")


def test_stale_bound_refused():
    def m(d, lines):
        d["narrow"][0]["before"] = {"low": 1.20, "high": 1.40}
        d["narrow"][0]["m2"] = 1.4
    _bad(m, "is not the door bound")


def test_units_refused():
    def m(d, lines):
        d["unit"] = "mm2"
    _bad(m, "m2")


def test_missing_source_refused():
    def m(d, lines):
        d["sources"] = [s for s in d["sources"] if s["task"] != "T-325"]
    _bad(m, "no merged source")


def test_source_without_checker_run_refused():
    def m(d, lines):
        d["sources"][0] = dict(d["sources"][0], checker_run="")
    _bad(m, "checker_run missing")


def test_unknown_face_refused():
    def m(d, lines):
        d["adds"][0]["components"][0]["component"] = "RETURN"
    _bad(m, "not a JAMBS_HEAD face")


def test_sill_and_jambs_mixed_in_one_line_refused():
    def m(d, lines):
        d["adds"][0]["components"].append(_c("SILL", 0.096, "0.080 x 1.200"))
    _bad(m, "not a JAMBS_HEAD face")


def test_plaster_reveal_on_a_window_refused():
    def m(d, lines):
        d["adds"][0]["item_code"] = "FIN.PLASTER"
    _bad(m, "through the wall")


def test_no_new_item_code():
    _l, out, *_ = run()
    assert {ln["item_code"] for ln in out} <= {"FIN.PLASTER", "ARCH.WINDOW_REVEAL", "ARCH.THRESHOLD"}


def test_applied_twice_refused():
    lines = lines_3027()
    _l, out, *_ = run(doc(lines), lines)
    with pytest.raises(A.InputsError, match="applied once|repeats|not a blank"):
        inp = A.load_inputs(doc(lines), PID)
        A.changes_for(inp, out)


def test_outside_line_changed_refused():
    lines = lines_3027()
    inp = A.load_inputs(doc(lines), PID)
    ch, _ = A.changes_for(inp, lines)
    bad = copy.deepcopy(ch)
    bad[0]["after"]["location"]["floor"] = "1F"
    with pytest.raises(ValueError):
        A.integrate(lines, bad)


def test_double_booking_on_finished_lines_refused():
    lines = lines_3027()
    inp = A.load_inputs(doc(lines), PID)
    ch, _ = A.changes_for(inp, lines)
    out, _ = A.integrate(lines, ch)
    dup = copy.deepcopy(next(ln for ln in out if "W1:OUT:JAMBS_HEAD" in ln["location"]["element_id"]))
    dup["line_id"] = "L-ffffffffffffffffffff"
    with pytest.raises(ValueError, match="double count"):
        A.check_reveals(out + [dup])
