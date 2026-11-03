"""T-422: ARCH_TAKEOFF_V3.0.44 (skirting threshold release, held-range narrowing, missing dry-room line) on a
hand-calculated NON-Alsenan villa (K422).

Villa K422, by hand (own figures; nothing from the development villa):
  R1 bedroom (GF): walls 4.50 x 3.50 -> perimeter 16.00 lm gross. Door D1 0.90 (deducted, UP-CER-003). Window WA edge
     1.20, sill printed 0.90 m above the floor -> the wall continues under it: skirted. The candidate (as the engine
     splits it) lists WA twice, glazing half 0.60 + threshold half 0.60:
        before: 16.00 - 0.90 - 0.60 - 0.60 = 14.50 - 1.20 = 13.90 lm; range line R1 held [0, 1.20] (WA).
        after:  16.00 - 0.90 = 15.10 lm (+1.20); the range line is carried by R1: NOT_APPLICABLE (no figure, never 0).
  R2 living (1F): range line held [0, 4.00] = WB 2.40 (sill 0.00 printed: floor glazing, no wall base) + WC 1.60 (sill
     not printed: held). after: [0, 1.60] (-2.40); the determinate R2 line 20.00 lm does not move.
  R4 study (2F): range line [0, 2.00] = WD 1.20 (sill 1.00: skirted) + WE 0.80 (sill not printed). Determinate R4
     16.00 - 0.80 door - 0.60 - 0.60 (WD halves) = 14.00 -> 15.20; its range [0, 2.00] -> [0, 0.80] (WE stays held).
  R3 dressing (1F): dry, no skirting line in the candidate -> one HELD BLANK line (engine boundary 7.20 m beside).
  Released total 1.20 + 1.20 = 2.40 lm; ranges: -1.20 (R1 absorbed) -1.20 (R4) -2.40 (R2) = -4.80 lm of held high.
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
from engine.source import arch_v304 as A304  # noqa: E402
from engine.source import arch_v3044 as A  # noqa: E402
from engine.source import boq_line as BL  # noqa: E402

PID, REV = "villa-k422", "e" * 64
DOCS = [{"file": "k422_arch.dxf", "sha256": "c" * 64}]


def _src(t):
    return {"task": t, "file": f"research/k422/{t}.csv", "sha256": t[-1] * 64, "merge_commit": "b" * 40,
            "checker_run": f"checker {t} Gate A PASS"}


def _ded(i, q, cid=None, chk=None):
    d = {"id": i, "qty": q, "unit": "lm"}
    if cid:
        d["census_id"] = cid
    if chk:
        d["physical_check"] = chk
    return d


def _skirt(room, floor, ev, net=None, gross=None, ded=(), br=None, eid=None, rfi=None):
    return BL.make_line(project_id=PID, revision_set_sha256=REV, item_code="FIN.SKIRTING", unit="lm", evidence_state=ev,
                        measured_net=net, gross=gross, deductions=list(ded), bounded_range=br,
                        element_id=eid or f"{room}:skirting", floor=floor, room_id=room,
                        formula=f"skirting {room}", documents=DOCS, rule_id="G", rule_version="1", rfi=rfi, notes="k")


def lines_3043():
    r1 = _skirt("R1", "GF", "SOURCE_DERIVED", net=13.9, gross=16.0,
                ded=[_ded("D1", 0.9), _ded("OP-1#glazing-half", 0.6, "WA", "UNRESOLVED"),
                     _ded("OP-1#threshold-half", 0.6, "WA", "UNRESOLVED")])
    r1r = _skirt("R1", "GF", "BOUNDED_EXPOSURE", br={"low": 0.0, "high": 1.2, "basis": "WA threshold"},
                 eid="R1:skirting:range", rfi={"question": "WA sill", "unlocks": "R1"})
    r2 = _skirt("R2", "1F", "SOURCE_DERIVED", net=20.0, gross=22.0,
                ded=[_ded("D2", 2.0)])
    r2r = _skirt("R2", "1F", "BOUNDED_EXPOSURE", br={"low": 0.0, "high": 4.0, "basis": "WB + WC thresholds"},
                 eid="R2:skirting:range", rfi={"question": "WB / WC sills", "unlocks": "R2"})
    r4 = _skirt("R4", "2F", "SOURCE_DERIVED", net=14.0, gross=16.0,
                ded=[_ded("D4", 0.8), _ded("OP-4#glazing-half", 0.6, "WD", "UNRESOLVED"),
                     _ded("OP-4#threshold-half", 0.6, "WD", "UNRESOLVED")])
    r4r = _skirt("R4", "2F", "BOUNDED_EXPOSURE", br={"low": 0.0, "high": 2.0, "basis": "WD + WE thresholds"},
                 eid="R4:skirting:range", rfi={"question": "WD / WE sills", "unlocks": "R4"})
    floor = BL.make_line(project_id=PID, revision_set_sha256=REV, item_code="FIN.FLOOR.PORCELAIN", unit="m2",
                         evidence_state="PROVISIONAL", measured_net=15.75, gross=15.75, element_id="R1:floor",
                         floor="GF", room_id="R1", formula="4.50 x 3.50 = 15.75 m2", documents=DOCS, rule_id="G",
                         rule_version="1", notes="k")
    return [r1, r1r, r2, r2r, r4, r4r, floor]


def _id(lines, eid):
    return next(x["line_id"] for x in lines if x["location"]["element_id"] == eid)


def _w(cid, edge, sill, status="DRAWING-CONFIRMED", **kw):
    return dict({"census_id": cid, "edge_lm": edge, "sill_m": sill, "status": status, "why": f"{cid} merged sill"},
                **kw)


def inputs(lines):
    return {"schema": A.INPUTS_SCHEMA, "project_id": PID, "sources": [_src("T-A")],
            "releases": [
                {"line_id": _id(lines, "R1:skirting"), "expect": {"gross": 16.0, "measured_net": 13.9},
                 "windows": [_w("WA", 1.2, 0.9, "PRINTED")],
                 "range_line": {"line_id": _id(lines, "R1:skirting:range"), "expect": {"low": 0.0, "high": 1.2}},
                 "source_tasks": ["T-A"]},
                {"line_id": _id(lines, "R4:skirting"), "expect": {"gross": 16.0, "measured_net": 14.0},
                 "windows": [_w("WD", 1.2, 1.0)],
                 "range_line": {"line_id": _id(lines, "R4:skirting:range"), "expect": {"low": 0.0, "high": 2.0}},
                 "source_tasks": ["T-A"]}],
            "narrows": [{"line_id": _id(lines, "R2:skirting:range"), "expect": {"low": 0.0, "high": 4.0},
                         "windows": [_w("WB", 2.4, 0.0, reason="FLOOR_GLAZING")], "source_tasks": ["T-A"]}],
            "missing": [{"engine_room": "R3", "floor": "1F", "template_line": _id(lines, "R2:skirting"),
                         "room_kind": "DRY", "engine_boundary_lm": 7.2, "why": "dry dressing, no line",
                         "source_tasks": ["T-A"]}]}


def run(lines=None, doc=None):
    lines = lines or lines_3043()
    d = A.load_inputs(doc or inputs(lines), PID)
    ch, log = A.changes_for(d, lines)
    out, ident = A.integrate(lines, ch)
    return lines, ch, log, out, ident


def _by(out, eid):
    return next(x for x in out if x["location"]["element_id"] == eid)


# ------------------------------------------------------------------------------------------------ normal
def test_release_hand_figures():
    lines, ch, log, out, ident = run()
    r1, r4 = _by(out, "R1:skirting"), _by(out, "R4:skirting")
    assert r1["measured_net"] == pytest.approx(15.1, abs=1e-9)          # 16.00 - 0.90
    assert r4["measured_net"] == pytest.approx(15.2, abs=1e-9)          # 16.00 - 0.80
    assert [x["id"] for x in r1["deductions"]] == ["D1"] and [x["id"] for x in r4["deductions"]] == ["D4"]
    assert r1["gross"] == 16.0 and r1["evidence_state"] == "SOURCE_DERIVED"
    assert log["released_lm"] == pytest.approx(2.4) and ident["skirting"]["released_lm"] == pytest.approx(2.4)
    rec = r1["calculation"]["inputs"][A.REC_KEY]
    assert rec["was"]["measured_net"] == 13.9 and [x["id"] for x in rec["removed_items"]] == [
        "OP-1#glazing-half", "OP-1#threshold-half"]


def test_range_absorbed_and_rest_kept():
    _, ch, log, out, ident = run()
    a = _by(out, "R1:skirting:range")
    assert a["evidence_state"] == "NOT_APPLICABLE_WITH_EVIDENCE" and a["measured_net"] is None
    assert a["bounded_range"] is None and a["calculation"]["inputs"][A.REC_KEY]["carried_by"] == _by(
        out, "R1:skirting")["line_id"]
    r4r = _by(out, "R4:skirting:range")                                   # WE 0.80 stays held
    assert r4r["evidence_state"] == "BOUNDED_EXPOSURE"
    assert (r4r["bounded_range"]["low"], r4r["bounded_range"]["high"]) == (0.0, pytest.approx(0.8))
    assert ident["skirting"]["absorbed"] == 1
    assert log["by_action"] == {"ABSORB_RANGE": 1, "ADD_MISSING": 1, "NARROW_RANGE": 2, "RELEASE": 2}


def test_floor_glazing_leaves_range_only():
    lines, ch, log, out, ident = run()
    r2r, r2 = _by(out, "R2:skirting:range"), _by(out, "R2:skirting")
    assert r2r["bounded_range"]["high"] == pytest.approx(1.6) and r2r["bounded_range"]["low"] == 0.0
    assert r2r["evidence_state"] == "BOUNDED_EXPOSURE" and r2r["rfi"] == _by(lines, "R2:skirting:range")["rfi"]
    assert A30.line_sha(r2) == A30.line_sha(_by(lines, "R2:skirting"))   # the valued line does not move
    assert log["range_out_lm"] == pytest.approx(2.4)


def test_missing_line_held_blank_never_zero():
    _, ch, log, out, ident = run()
    m = _by(out, "SKIRT-T422:R3")
    assert m["evidence_state"] == "BLOCKED_RFI" and m["measured_net"] is None and m["gross"] is None
    assert m["bounded_range"] is None and m["location"]["room_id"] == "R3" and "7.2" in m["calculation"]["formula"]
    assert log["missing_rooms"] == ["R3"] and ident["added"] == 1


def test_outside_lines_byte_identical_and_totals_only_skirting():
    lines, ch, log, out, ident = run()
    named = {c["after"]["line_id"] for c in ch}
    for ln in lines:
        if ln["line_id"] not in named:
            assert A30.line_sha(ln) == A30.line_sha(next(x for x in out if x["line_id"] == ln["line_id"]))
    t0, t1 = A304.code_totals(lines), A304.code_totals(out)
    assert {k.split("|")[0] for k in set(t0) | set(t1) if t0.get(k) != t1.get(k)} == {"FIN.SKIRTING"}


def test_mirrored_input_order_same_result():
    lines = lines_3043()
    doc = inputs(lines)
    doc["releases"] = list(reversed(doc["releases"]))
    out1 = run(lines)[3]
    out2 = run(lines, doc)[3]
    assert sorted(A30.line_sha(x) for x in out1) == sorted(A30.line_sha(x) for x in out2)


def test_write_files(tmp_path):
    lines, ch, log, out, ident = run()
    names, ident2, led = A.write(tmp_path, lines, ch, log)
    assert "V3_0_44_BOQ_LINES.json" in names and ident2["diff"]["vs_v3_0_43"] == {"ADDED": 1, "CHANGED": 5, "SAME": 2}
    run_doc = json.loads((tmp_path / "V3_0_44_RUN.json").read_text(encoding="utf-8"))
    assert set(k.split("|")[0] for k in run_doc["totals_moved_by_code"]) == {"FIN.SKIRTING"}
    assert led["released_default"] is False and all(r["release_status"] == "NOT RELEASED" for r in led["rows"])


# ------------------------------------------------------------------------------------------------ adverse
def _err(doc, lines=None, match=None):
    lines = lines or lines_3043()
    with pytest.raises(A.InputsError, match=match):
        A.changes_for(A.load_inputs(doc, PID), lines)


def test_sill_at_floor_is_not_released():
    lines = lines_3043()
    d = inputs(lines)
    d["releases"][0]["windows"][0]["sill_m"] = 0.0
    _err(d, lines, "not established above the floor")


def test_held_sill_is_not_released():
    lines = lines_3043()
    d = inputs(lines)
    d["releases"][0]["windows"][0].update(status="HELD", sill_m=None)
    _err(d, lines, "needs its sill")


def test_stale_binding_stops():
    lines = lines_3043()
    d = inputs(lines)
    d["releases"][0]["expect"]["measured_net"] = 13.8
    _err(d, lines, "stale binding")


def test_partial_listing_stops():
    lines = lines_3043()
    r1 = _by(lines, "R1:skirting")
    r1["deductions"] = r1["deductions"][:2]                                # only the glazing half listed
    r1["measured_net"] = 14.5                                              # 16.0 - 0.9 - 0.6
    d = inputs(lines)
    d["releases"][0]["expect"]["measured_net"] = 14.5
    _err(d, lines, "partial or doubled")


def test_window_not_in_list_stops():
    lines = lines_3043()
    d = inputs(lines)
    d["releases"][0]["windows"][0]["census_id"] = "WZ"
    _err(d, lines, "not in the line's list")


def test_consistent_listing_disagrees_stops():
    lines = lines_3043()
    for x in _by(lines, "R1:skirting")["deductions"][1:]:
        x["physical_check"] = "CONSISTENT"
    _err(inputs(lines), lines, "readings disagree")


def test_window_taken_twice_refused():
    lines = lines_3043()
    d = inputs(lines)
    d["releases"][0]["windows"].append(copy.deepcopy(d["releases"][0]["windows"][0]))
    with pytest.raises(A.InputsError, match="taken twice"):
        A.load_inputs(d, PID)


def test_mm_slip_refused():
    lines = lines_3043()
    d = inputs(lines)
    d["releases"][0]["windows"][0]["edge_lm"] = 1200
    with pytest.raises(A.InputsError, match="mm"):
        A.load_inputs(d, PID)
    d = inputs(lines)
    d["releases"][0]["windows"][0]["sill_m"] = 900
    with pytest.raises(A.InputsError, match="mm"):
        A.load_inputs(d, PID)


def test_narrow_of_a_valued_line_refused():
    lines = lines_3043()
    d = inputs(lines)
    d["narrows"][0]["line_id"] = _id(lines, "R2:skirting")
    _err(d, lines, "never narrowed")


def test_narrow_whole_range_refused():
    lines = lines_3043()
    d = inputs(lines)
    d["narrows"][0]["windows"][0]["edge_lm"] = 4.0
    _err(d, lines, "whole range")


def test_narrow_needs_floor_glazing_evidence():
    lines = lines_3043()
    d = inputs(lines)
    d["narrows"][0]["windows"][0]["sill_m"] = 0.9
    with pytest.raises(A.InputsError, match="floor glazing"):
        A.load_inputs(d, PID)


def test_missing_with_value_or_wet_or_present_refused():
    lines = lines_3043()
    d = inputs(lines)
    d["missing"][0]["value"] = 7.2
    with pytest.raises(A.InputsError, match="HELD_WITH_VALUE"):
        A.load_inputs(d, PID)
    d = inputs(lines)
    d["missing"][0]["room_kind"] = "WET_FULL_HEIGHT_TILE"
    with pytest.raises(A.InputsError, match="DRY"):
        A.load_inputs(d, PID)
    d = inputs(lines)
    d["missing"][0]["engine_room"] = "R2"
    _err(d, lines, "already carries skirting")


def test_applied_twice_refused():
    lines, ch, log, out, ident = run()
    with pytest.raises(A.InputsError, match="applied once"):
        A.changes_for(A.load_inputs(inputs(lines), PID), out)


def test_range_line_of_another_room_refused():
    lines = lines_3043()
    d = inputs(lines)
    d["releases"][0]["range_line"] = {"line_id": _id(lines, "R2:skirting:range"), "expect": {"low": 0.0, "high": 4.0}}
    d["narrows"] = []
    _err(d, lines, "not the range line of the released line's room")


def test_check_refuses_a_tampered_release():
    lines, ch, log, out, ident = run()
    bad = copy.deepcopy(out)
    r1 = next(x for x in bad if x["location"]["element_id"] == "R1:skirting")
    r1["measured_net"] = 16.0                                                # does not close
    with pytest.raises(ValueError, match="does not close"):
        A.check_skirting(bad, lines)
    bad = copy.deepcopy(out)
    a = next(x for x in bad if x["location"]["element_id"] == "R1:skirting:range")
    a["bounded_range"] = {"low": 0.0, "high": 0.0}                           # a held 0 sneaked back
    with pytest.raises(ValueError, match="carries a figure"):
        A.check_skirting(bad, lines)


def test_other_project_inputs_refused():
    lines = lines_3043()
    d = inputs(lines)
    d["project_id"] = "another-villa"
    with pytest.raises(A.InputsError, match="for 'another-villa'"):
        A.load_inputs(d, PID)
