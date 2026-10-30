"""T-327: ARCH_TAKEOFF_V3.0.29 (sills and thresholds as their own item, from a checker-merged ledger) on a
hand-calculated NON-Alsenan villa (V327), normal and adverse.

Villa V327, by hand (UP-THR-001: threshold = clear door width x wall thickness; wet doorway marble, dry doorway the
floor porcelain continued once; external entrance by specification):
  D1 bath door, clear width 0.80 (drawn jamb gap), wall t 0.15, WET: the candidate carries a BLOCKED ARCH.THRESHOLD
     closure strip whose polygon is 0.165 m2 = 0.80 x 0.15 + (wall-end nib 0.05 + cross wall 0.25) x 0.15
     = 0.120 + 0.045 -> RETYPE to FIN.MARBLE.THRESHOLD 0.120 m2, 0.800 m.l, 1 pc (never 0.165)
  D2 bedroom door 0.90 x t 0.20, DRY, closure polygon 0.198 = 0.180 + nib 0.09 x 0.20 -> FIN.FLOOR.PORCELAIN 0.180 m2
  D3 garden gate: width not established -> ONE BLANK ARCH.THRESHOLD line by name (never 0)
  D5 WC door already in its FIN.MARBLE.THRESHOLD line 0.120 (= 0.80 x 0.15): carried, never booked again
  W1 stair window at floor level over air: outside strip 1.00 x 0.08 = 0.080 m2 (1.000 m.l, 1 pc), material UNKNOWN
  W2 raised window: external sill 1.20 x 0.10 = 0.120 m2 (1.200 m.l, 1 pc), material UNKNOWN
  totals moved: FIN.MARBLE.THRESHOLD +0.120, FIN.FLOOR.PORCELAIN +0.180, ARCH.WINDOW_REVEAL +0.200; ARCH.THRESHOLD
  unchanged in value (two closure lines retired, one held line added).
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v30 as A30  # noqa: E402
from engine.source import arch_v304 as A304  # noqa: E402
from engine.source import arch_v3029 as A  # noqa: E402
from engine.source import boq_line as BL  # noqa: E402

PID, REV = "villa-v327", "f" * 64
DOCS = [{"file": "v327_plan.dxf", "sha256": "d" * 64}]
SRC = {"T-325": {"task": "T-325", "file": "research/v327/sills.csv", "sha256": "4" * 64, "merge_commit": "d" * 40,
                 "checker_run": "checker run 10 (Gate A PASS)"},
       "T-340": {"task": "T-340", "file": "research/v327/fill.csv", "sha256": "5" * 64, "merge_commit": "e" * 40,
                 "checker_run": "checker run 11 (Gate A PASS)"}}


def _line(code, eid, phys, ev="BLOCKED_RFI", net=None, floor="GF"):
    kw = {"rfi": {"question": "finish / floor status"}} if ev == "BLOCKED_RFI" else {}
    return BL.make_line(project_id=PID, revision_set_sha256=REV, item_code=code, unit="m2", evidence_state=ev,
                        measured_net=net, element_id=eid, floor=floor, physical_element=phys,
                        formula=f"{phys} {net}", documents=DOCS, rule_id="R", rule_version="1", notes="v327", **kw)


def lines_3028():
    return [_line("FIN.FLOOR.PORCELAIN", "GF-01:floor", "floor", "MEASURED", 20.0),
            _line("ARCH.THRESHOLD", "GF-STRIP-CLOSURE_D1:threshold strip", "threshold strip"),
            _line("ARCH.THRESHOLD", "GF-STRIP-CLOSURE_D2:threshold strip", "threshold strip"),
            _line("FIN.MARBLE.THRESHOLD", "GF-STRIP-OP-5:marble threshold", "marble threshold", "SOURCE_DERIVED", 0.12),
            _line("ARCH.WINDOW_REVEAL", "GF-STRIP-W1:window reveal strip", "window reveal strip"),
            _line("ARCH.WINDOW_REVEAL", "GF-STRIP-W2:window reveal strip", "window reveal strip")]


def _id(lines, eid):
    return next(ln["line_id"] for ln in lines if ln["location"]["element_id"] == eid)


def _retype(lines, op, eid, cls, w, d, poly, excess, residual=0.0, **kw):
    code, mat = ("FIN.MARBLE.THRESHOLD", "MARBLE") if cls == "WET" else ("FIN.FLOOR.PORCELAIN", "FLOOR PORCELAIN")
    r = {"opening": op, "kind": "DOOR", "floor": "GF", "line_id": _id(lines, eid), "doorway": cls, "external": False,
         "target_item": code, "material": mat,
         "material_source": "UP-THR-001 + URBAN-WET-SERVICE-MARBLE-THRESHOLD v1" if cls == "WET"
         else "UP-THR-001 (dry doorway: once, as its own line)",
         "width_m": w, "depth_m": d, "m2": round(w * d, 6), "ml": w, "pcs": 1, "closure_polygon_m2": poly,
         "trace": {"polygon_minus_clear_m2": excess, "residual_m2": residual, "cause": "nib + cross wall"},
         "floor_overlap_m2": 0.00004, "source_task": "T-340"}
    r.update(kw)
    return r


def doc(lines=None):
    lines = lines or lines_3028()
    return {
        "schema": A.INPUTS_SCHEMA, "project_id": PID, "unit": "m2", "sources": list(SRC.values()),
        "retype": [_retype(lines, "D1", "GF-STRIP-CLOSURE_D1:threshold strip", "WET", 0.8, 0.15, 0.165, 0.045),
                   _retype(lines, "D2", "GF-STRIP-CLOSURE_D2:threshold strip", "DRY", 0.9, 0.2, 0.198, 0.018)],
        "sills": [{"opening": "W1", "line_id": _id(lines, "GF-STRIP-W1:window reveal strip"),
                   "component": "THRESHOLD_OUT", "outside": "AIR", "width_m": 1.0, "depth_m": 0.08, "m2": 0.08,
                   "ml": 1.0, "pcs": 1, "material": "UNKNOWN", "source_task": "T-325"},
                  {"opening": "W2", "line_id": _id(lines, "GF-STRIP-W2:window reveal strip"),
                   "component": "SILL_OUT", "outside": "AIR", "width_m": 1.2, "depth_m": 0.1, "m2": 0.12,
                   "ml": 1.2, "pcs": 1, "material": "UNKNOWN", "source_task": "T-325"}],
        "held": [{"opening": "D3", "floor": "GF", "item_code": "ARCH.THRESHOLD", "component": "THRESHOLD",
                  "state": "UNRESOLVED", "basis": "gate width not established", "source_task": "T-325"}],
        "carried": [{"opening": "D5", "component": "THRESHOLD", "item_code": "FIN.MARBLE.THRESHOLD",
                     "line_id": _id(lines, "GF-STRIP-OP-5:marble threshold"), "m2": 0.12, "source_task": "T-340"}]}


def run(d=None, lines=None):
    lines = lines or lines_3028()
    inp = A.load_inputs(d or doc(lines), PID)
    ch, log = A.changes_for(inp, lines)
    out, ident = A.integrate(lines, ch)
    return lines, out, ident, ch, log


def _by_code(out, code):
    return [ln for ln in out if ln["item_code"] == code]


# ------------------------------------------------------------------------------------------------ normal
def test_hand_values_v327():
    lines, out, ident, ch, log = run()
    marble = [ln for ln in _by_code(out, "FIN.MARBLE.THRESHOLD") if "D1" in ln["location"]["element_id"]]
    assert len(marble) == 1 and marble[0]["measured_net"] == 0.12 and marble[0]["evidence_state"] == "MEASURED"
    rec = marble[0]["calculation"]["inputs"][A.REC_KEY]
    assert rec["faces"] == [{"component": "THRESHOLD", "m2": 0.12, "ml": 0.8, "pcs": 1, "width_m": 0.8,
                             "depth_m": 0.15}]
    assert rec["material"] == "MARBLE" and rec["superseded_polygon_m2"] == 0.165
    porc = [ln for ln in _by_code(out, "FIN.FLOOR.PORCELAIN") if "D2" in ln["location"]["element_id"]]
    assert len(porc) == 1 and porc[0]["measured_net"] == 0.18 and porc[0]["physical_element"] == "doorway strip"
    w = {ln["location"]["element_id"]: ln for ln in _by_code(out, "ARCH.WINDOW_REVEAL")}
    assert w["GF-STRIP-W1:window reveal strip"]["measured_net"] == 0.08
    assert w["GF-STRIP-W2:window reveal strip"]["measured_net"] == 0.12
    s = ident["sills_thresholds"]
    assert s["m2"] == {"ARCH.WINDOW_REVEAL": 0.2, "FIN.FLOOR.PORCELAIN": 0.18, "FIN.MARBLE.THRESHOLD": 0.12}
    assert s["ml"] == {"ARCH.WINDOW_REVEAL": 2.2, "FIN.FLOOR.PORCELAIN": 0.9, "FIN.MARBLE.THRESHOLD": 0.8}
    assert s["pcs"] == {"ARCH.WINDOW_REVEAL": 2, "FIN.FLOOR.PORCELAIN": 1, "FIN.MARBLE.THRESHOLD": 1}
    assert (s["retyped"], s["retired"], s["filled"], s["held_added"], s["openings"]) == (2, 2, 2, 1, 5)


def test_closure_lines_retired_with_successor_and_no_figure():
    lines, out, *_ = run()
    by = {ln["line_id"]: ln for ln in out}
    for eid in ("GF-STRIP-CLOSURE_D1:threshold strip", "GF-STRIP-CLOSURE_D2:threshold strip"):
        ln = by[_id(lines, eid)]
        assert ln["evidence_state"] == "NOT_APPLICABLE_WITH_EVIDENCE" and ln["measured_net"] is None
        rec = ln["calculation"]["inputs"][A.REC_KEY]
        assert by[rec["successor"]]["evidence_state"] == "MEASURED"
        assert ln["item_code"] == "ARCH.THRESHOLD"          # the retired line keeps its identity for the audit


def test_held_line_blank_by_name():
    _, out, *_ = run()
    h = [ln for ln in out if ln["location"]["element_id"].endswith(":HELD")]
    assert len(h) == 1 and h[0]["evidence_state"] == "BLOCKED_RFI" and h[0]["measured_net"] is None
    assert "D3" in h[0]["rfi"]["question"] and "never 0" in h[0]["rfi"]["question"]


def test_outside_lines_byte_identical_and_totals_only_in_strip_items():
    lines, out, ident, ch, _ = run()
    by = {ln["line_id"]: ln for ln in out}
    for ln in lines:
        if ln["location"]["element_id"] in ("GF-01:floor", "GF-STRIP-OP-5:marble threshold"):
            assert A30.line_sha(ln) == A30.line_sha(by[ln["line_id"]])
    t0, t1 = A304.code_totals(lines), A304.code_totals(out)
    moved = {k for k in set(t0) | set(t1) if t0.get(k) != t1.get(k)}
    assert moved and all(k.split("|")[0] in A.ITEMS for k in moved)
    assert t0.get("FIN.FLOOR.PORCELAIN|m2") != t1.get("FIN.FLOOR.PORCELAIN|m2")
    assert ident["outside_rows"] == 2


def test_order_invariance():
    lines = lines_3028()
    d = doc(lines)
    d2 = copy.deepcopy(d)
    for k in ("retype", "sills"):
        d2[k] = list(reversed(d2[k]))
    o1 = run(d, lines)[1]
    o2 = run(d2, lines)[1]
    assert sorted(A30.line_sha(x) for x in o1) == sorted(A30.line_sha(x) for x in o2)


def test_floor_level_window_onto_a_floor_accepted_only_outside_that_floor():
    lines = lines_3028()
    d = doc(lines)
    d["sills"][0].update(outside="FLOOR", outdoor_line_excludes_strip=True, material="the outdoor floor's finish",
                         material_source="UP-REVEAL-001 + the outdoor floor line")
    out = run(d, lines)[1]
    assert {ln["location"]["element_id"]: ln for ln in out}["GF-STRIP-W1:window reveal strip"]["measured_net"] == 0.08


def test_untraced_closure_residual_stays_blank_with_residual_named():
    lines = lines_3028()
    d = doc(lines)
    d["retype"][0]["trace"] = {"polygon_minus_clear_m2": 0.045, "residual_m2": 0.01, "cause": "partly traced"}
    _, out, ident, *_ = run(d, lines)
    ln = {x["line_id"]: x for x in out}[_id(lines, "GF-STRIP-CLOSURE_D1:threshold strip")]
    assert ln["evidence_state"] == "BLOCKED_RFI" and ln["measured_net"] is None
    assert "0.045" in ln["rfi"]["question"]
    assert not [x for x in out if x["item_code"] == "FIN.MARBLE.THRESHOLD" and "D1" in x["location"]["element_id"]]
    assert ident["sills_thresholds"]["trace_held"] == 1


# ------------------------------------------------------------------------------------------------ adverse
def _bad(mut, match):
    lines = lines_3028()
    d = doc(lines)
    mut(d, lines)
    with pytest.raises((A.InputsError, ValueError), match=match):
        inp = A.load_inputs(d, PID)
        ch, _ = A.changes_for(inp, lines)
        A.integrate(lines, ch)


def test_adverse_wet_marble_on_a_dry_door_refused():
    def m(d, _):
        d["retype"][1].update(target_item="FIN.MARBLE.THRESHOLD", material="MARBLE")
    _bad(m, "DRY doorway is FIN.FLOOR.PORCELAIN")


def test_adverse_porcelain_on_a_wet_door_refused():
    def m(d, _):
        d["retype"][0].update(target_item="FIN.FLOOR.PORCELAIN", material="FLOOR PORCELAIN")
    _bad(m, "WET doorway is FIN.MARBLE.THRESHOLD")


def test_adverse_marble_without_the_wet_rule_refused():
    def m(d, _):
        d["retype"][0]["material_source"] = "the neighbouring room"
    _bad(m, "wet-doorway rule")


def test_adverse_external_entrance_never_retyped():
    def m(d, _):
        d["retype"][0]["external"] = True
    _bad(m, "external entrance")


def test_adverse_closure_polygon_as_the_threshold_refused():
    def m(d, _):
        d["retype"][0].update(m2=0.165)
    _bad(m, "is not width")


def test_adverse_polygon_offered_with_matching_dims_refused():
    def m(d, _):
        d["retype"][0].update(width_m=1.1, ml=1.1, m2=0.165)
    _bad(m, "superseded figure")


def test_adverse_strip_inside_a_floor_tile_line_refused():
    def m(d, _):
        d["retype"][1]["floor_overlap_m2"] = 0.05
    _bad(m, "already counted in the floor")


def test_adverse_missing_overlap_refused():
    def m(d, _):
        d["retype"][1].pop("floor_overlap_m2")
    _bad(m, "overlap")


def test_adverse_ml_relabelled_from_m2_refused():
    def m(d, _):
        d["retype"][0]["ml"] = 0.12
    _bad(m, "three measures")


def test_adverse_two_pieces_refused():
    def m(d, _):
        d["retype"][0]["pcs"] = 2
    _bad(m, "one strip per opening")


def test_adverse_millimetres_refused():
    def m(d, _):
        d["sills"][1].update(width_m=1200, depth_m=100, m2=120000, ml=1200)
    _bad(m, "not a wall")


def test_adverse_floor_level_window_counted_as_terrace_and_sill_refused():
    def m(d, _):
        d["sills"][0].update(outside="FLOOR")
    _bad(m, "both terrace and sill")


def test_adverse_outside_not_established_refused():
    def m(d, _):
        d["sills"][0]["outside"] = None
    _bad(m, "not established")


def test_adverse_marble_on_a_window_by_the_wet_rule_refused():
    def m(d, _):
        d["sills"][1].update(material="MARBLE", material_source="URBAN-WET-SERVICE-MARBLE-THRESHOLD v1")
    _bad(m, "does not set a window sill")


def test_adverse_sill_material_without_source_refused():
    def m(d, _):
        d["sills"][1].update(material="GRANITE")
    _bad(m, "print or an owner rule")


def test_adverse_held_as_zero_refused():
    def m(d, _):
        d["held"][0]["m2"] = 0
    _bad(m, "held strip given a figure")


def test_adverse_second_carrier_refused():
    def m(d, lines):
        d["carried"].append({"opening": "D1", "component": "THRESHOLD", "item_code": "FIN.MARBLE.THRESHOLD",
                             "line_id": _id(lines, "GF-STRIP-OP-5:marble threshold"), "m2": 0.12,
                             "source_task": "T-340"})
    _bad(m, "one strip, one line|one line, one opening")


def test_adverse_one_line_two_openings_refused():
    def m(d, lines):
        d["sills"][1]["line_id"] = d["sills"][0]["line_id"]
    _bad(m, "one line, one opening")


def test_adverse_carried_line_differs_refused():
    def m(d, _):
        d["carried"][0]["m2"] = 0.135
    _bad(m, "line differs")


def test_adverse_stale_line_refused():
    def m(d, _):
        d["retype"][0]["line_id"] = "L-00000000000000000000"
    _bad(m, "stale ledger")


def test_adverse_line_not_blank_refused():
    def m(d, lines):
        d["retype"][0]["line_id"] = _id(lines, "GF-STRIP-OP-5:marble threshold")
        d["carried"] = []
    _bad(m, "not a blank threshold")


def test_adverse_source_without_checker_run_refused():
    def m(d, _):
        d["sources"][0] = dict(d["sources"][0], checker_run="")
    _bad(m, "checker_run missing")


def test_adverse_applied_twice_refused():
    lines = lines_3028()
    inp = A.load_inputs(doc(lines), PID)
    ch, _ = A.changes_for(inp, lines)
    out, _ = A.integrate(lines, ch)
    with pytest.raises(A.InputsError, match="applied once|not a blank|already"):
        A.changes_for(A.load_inputs(doc(lines), PID), out)


def test_adverse_outside_line_changed_refused():
    lines = lines_3028()
    inp = A.load_inputs(doc(lines), PID)
    ch, _ = A.changes_for(inp, lines)
    bad = copy.deepcopy(ch)
    rep = next(c for c in bad if c["action"] == "REPLACE")
    rep["after"]["physical_element"] = "room floor"          # a change outside quantity / state / basis
    with pytest.raises(ValueError, match="changed outside quantity"):
        A.integrate(lines, bad)


def test_adverse_double_booking_on_finished_lines_refused():
    lines, out, *_ = run()
    dup = copy.deepcopy(next(ln for ln in out if ln["item_code"] == "FIN.MARBLE.THRESHOLD" and
                             A.REC_KEY in ln["calculation"]["inputs"]))
    dup["line_id"] = "L-dup000000000000000a"
    with pytest.raises(ValueError, match="double count"):
        A.check_strips(out + [dup])


def test_adverse_unit_refused():
    def m(d, _):
        d["unit"] = "m"
    _bad(m, "m2")
