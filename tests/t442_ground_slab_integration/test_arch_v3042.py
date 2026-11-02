"""T-442: ARCH_TAKEOFF_V3.0.42 (a held slab-on-grade cell valued at its re-measured panels x T; a slab panel dropped as a
'stair zone' added as one ground-slab line; cause texts naming the right designer item, no figure moving) on a
hand-calculated NON-Alsenan villa (G442).

Villa G442, by hand (own figures; nothing from the development villa). Printed slab on grade 'T=12cm' (0.12 m).
  Cell C1 around a lift pit: engine net 30.89 m2, held BOUNDED 0 .. 3.24 m3. Panels closed on drawn band faces:
     P1 4.50 x 3.00 = 13.50, P2 3.00 x 4.00 - ring corner 0.60 x 0.50 = 11.70, P3 1.20 x 1.00 = 1.20  -> 26.40 m2
     x 0.12 = 3.168 m3 (VALUED). Not slab: shaft 1.60 x 1.60 = 2.56 (pit floor = raft top), ring 1.93 (pit wall).
     26.40 + 2.56 + 1.93 = 30.89 = the engine net (re-adds).
  Cell C2 under a flight drawn HIDDEN, closed by four band faces, nothing below but a column footing:
     2.80 x 2.25 = 6.30 m2 x 0.12 = 0.756 m3 (one NEW line).
  Column line K1: CONFLICT range 0.54 .. 0.72 m3 citing 'D-9' where the designer item is 'D-12'; cause text only.
  Ground slab total: valued 5.000 (other cell) -> 5.000 + 3.168 + 0.756 = 8.924 m3.
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
from engine.source import arch_v3033 as A3033  # noqa: E402
from engine.source import arch_v3042 as A  # noqa: E402
from engine.source import boq_line as BL  # noqa: E402

PID, REV = "villa-g442", "e" * 64
DOCS = [{"file": "g442_struct.dxf", "sha256": "c" * 64}]
GS = "STR.CONC.GROUND_SLAB"


def _src(t):
    return {"task": t, "file": f"research/g442/{t}.json", "sha256": t[-1] * 64, "merge_commit": "b" * 40,
            "checker_run": f"checker {t} Gate A PASS"}


def _ln(code, eid, ev, net=None, br=None, rfi=None, formula=None, inputs=None, unit="m3"):
    return BL.make_line(project_id=PID, revision_set_sha256=REV, item_code=code, unit=unit, evidence_state=ev,
                        measured_net=net, gross=net, bounded_range=br, element_id=eid, floor="GROUND",
                        formula=formula or f"{code} {eid}", inputs=inputs, documents=DOCS, rule_id="G",
                        rule_version="1", rfi=rfi, notes="g")


def lines_3041():
    held = _ln(GS, "U-C:GROUND_SLAB:GROUND:C1", "BOUNDED_EXPOSURE",
               br={"low": 0.0, "high": 3.24, "basis": "held bound 0 .. 3.24 m3 = 0 .. the cell"},
               rfi={"question": "cell C1: free column inside the cell", "unlocks": "C1"},
               formula="HELD (never a value): bound 0 .. 3.24 m3 (was .. 3.7068): free column",
               inputs={A3033.REC_KEY: {"action": "HELD_BOUND", "evidence_status": "HELD"}})
    other = _ln(GS, "GS:GROUND_SLAB:GROUND:C9", "SOURCE_DERIVED", net=5.0, formula="41.6667 m2 x 0.12 = 5.0 m3")
    col = _ln("STR.CONC.COLUMN", "COL:K1", "BOUNDED_EXPOSURE",
              br={"low": 0.54, "high": 0.72, "basis": "CONFLICT printed-vs-drawn section: schedule 0.54 | drawn 0.72 "
                                                      "m3 (column-band item; D-9)"},
              rfi={"question": "K1: which section is built? (column-band item; D-9)", "unlocks": "COL:K1"},
              formula="CONFLICT (held, never one reading): schedule 0.54 | drawn 0.72 -> range 0.54 .. 0.72 m3",
              inputs={"evidence_status": "HELD"})
    valued_col = _ln("STR.CONC.COLUMN", "COL:K2", "SOURCE_DERIVED", net=0.5, formula="0.25 x 0.5 x 4.0 = 0.5 m3 (D-9)")
    floor = _ln("FIN.FLOOR.PORCELAIN", "R1:floor", "PROVISIONAL", net=40.0, unit="m2", formula="R1 = 40.0 m2")
    return [held, other, col, valued_col, floor]


def _id(lines, eid):
    return next(x["line_id"] for x in lines if x["location"]["element_id"] == eid)


def inputs(lines, cell=None, panel=None, texts=None):
    c = {"line_id": _id(lines, "U-C:GROUND_SLAB:GROUND:C1"), "cell": "C1", "floor": "GROUND",
         "expect": {"evidence_state": "BOUNDED_EXPOSURE", "high": 3.24}, "t": 0.12, "t_status": "VERIFIED",
         "area_status": "VERIFIED",
         "panels": [{"id": "P1", "area": 13.5}, {"id": "P2", "area": 11.7}, {"id": "P3", "area": 1.2}],
         "declared_m2": 26.4, "declared_m3": 3.168,
         "beside": [{"kind": "SHAFT", "area": 2.56, "owner": "LIFT_PIT_FLOOR=RAFT_TOP", "why": "pit floor = raft top"},
                    {"kind": "RING", "area": 1.93, "owner": "LIFT_PIT_WALLS", "why": "pit wall"}],
         "source_tasks": ["T-A"]}
    p = {"cell": "C2", "element_id": "GS-T442:GROUND_SLAB:GROUND:C2", "floor": "GROUND", "t": 0.12,
         "t_status": "VERIFIED", "area_status": "DRAWING-CONFIRMED", "template_line": c["line_id"],
         "exclusion_retired": "not counted: the cell is a stair zone", "panels": [{"id": "P4", "area": 6.3}],
         "declared_m3": 0.756, "physical_element": "slab on grade under a flight drawn hidden",
         "source_tasks": ["T-B"]}
    t = [{"line_id": _id(lines, "COL:K1"), "item_code": "STR.CONC.COLUMN", "old": "D-9", "new": "D-12 (RFI-7)",
          "why": "the designer list item is D-12", "source_tasks": ["T-C"]}]
    for d, o in ((c, cell), (p, panel)):
        d.update(o if isinstance(o, dict) else {})
    return {"schema": A.INPUTS_SCHEMA, "project_id": PID, "sources": [_src("T-A"), _src("T-B"), _src("T-C")],
            "cells": [c] if cell != "none" else [], "panels": [p] if panel != "none" else [],
            "texts": t if texts is None else texts}


def run(lines=None, doc=None):
    lines = lines or lines_3041()
    d = A.load_inputs(doc if doc is not None else inputs(lines), PID)
    ch, log = A.changes_for(d, lines)
    out, ident = A.integrate(lines, ch)
    return lines, out, ident, ch, log


def _e(out, eid):
    return next(x for x in out if x["location"]["element_id"] == eid)


def _gs(lines):
    return round(sum(x["measured_net"] for x in lines if x["item_code"] == GS and x["evidence_state"] in A.VALUED), 6)


# ------------------------------------------------------------------------------------------------ normal
def test_hand_figures_g442():
    lines, out, ident, ch, log = run()
    c1 = _e(out, "U-C:GROUND_SLAB:GROUND:C1")
    assert c1["evidence_state"] == "SOURCE_DERIVED" and c1["measured_net"] == pytest.approx(3.168, abs=1e-12)
    assert c1["bounded_range"] is None and c1["rfi"] is None
    assert c1["calculation"]["inputs"]["evidence_status"] == "VERIFIED"
    c2 = _e(out, "GS-T442:GROUND_SLAB:GROUND:C2")
    assert c2["measured_net"] == pytest.approx(0.756, abs=1e-12) and c2["evidence_state"] == "SOURCE_DERIVED"
    assert c2["calculation"]["inputs"]["evidence_status"] == "DRAWING-CONFIRMED"
    assert _gs(lines) == 5.0 and _gs(out) == pytest.approx(8.924, abs=1e-9)
    assert ident["added"] == 1 and ident["replaced"] == 2 and ident["outside_rows_identical_to_v3_0_41"] == 3
    assert ident["slab"] == {"cells_valued": 1, "panels_added": 1, "texts": 1, "m3_valued": 3.924}
    assert log["exclusions_retired"] == [{"cell": "C2", "reason": "not counted: the cell is a stair zone",
                                          "line": c2["line_id"]}]


def test_cell_reconciles_to_engine_net_with_named_parts():
    lines, out, *_ = run()
    rec = _e(out, "U-C:GROUND_SLAB:GROUND:C1")["calculation"]["inputs"][A.REC_KEY]
    assert rec["area_m2"] + sum(b["area"] for b in rec["beside"]) == pytest.approx(30.89, abs=1e-9)
    assert {b["kind"]: b["owner"] for b in rec["beside"]} == {"SHAFT": "LIFT_PIT_FLOOR=RAFT_TOP",
                                                             "RING": "LIFT_PIT_WALLS"}


def test_old_held_record_superseded_not_lost():
    lines, out, *_ = run()
    inp = _e(out, "U-C:GROUND_SLAB:GROUND:C1")["calculation"]["inputs"]
    assert A3033.REC_KEY not in inp
    assert inp[A.SUPERSEDED_KEY]["records"][A3033.REC_KEY]["action"] == "HELD_BOUND"
    assert "0 .. 3.24" in inp[A.REC_KEY]["formula_before"]


def test_cause_text_moves_no_figure():
    lines, out, *_ = run()
    o, n = _e(lines, "COL:K1"), _e(out, "COL:K1")
    assert "D-12 (RFI-7)" in n["rfi"]["question"] and "D-9" not in n["rfi"]["question"]
    assert "D-12 (RFI-7)" in n["bounded_range"]["basis"]
    assert (n["bounded_range"]["low"], n["bounded_range"]["high"]) == (0.54, 0.72)
    assert n["evidence_state"] == o["evidence_state"] and n["measured_net"] is None
    assert n["rfi"]["unlocks"] == o["rfi"]["unlocks"]
    assert n["calculation"]["inputs"][A.REC_KEY]["hits"] == {"formula": 0, "notes": 0, "rfi_question": 1,
                                                              "range_basis": 1}


def test_every_other_line_byte_identical_and_totals_only_ground_slab(tmp_path):
    lines, out, ident, ch, log = run()
    for x in lines:
        if x["location"]["element_id"] in ("GS:GROUND_SLAB:GROUND:C9", "COL:K2", "R1:floor"):
            assert A30.line_sha(x) == A30.line_sha(_e(out, x["location"]["element_id"]))
    t0, t1 = A304.code_totals(lines), A304.code_totals(out)
    assert {k.split("|")[0] for k in set(t0) | set(t1) if t0.get(k) != t1.get(k)} == {GS}
    names, ident2, led = A.write(tmp_path, lines, ch, log)
    assert "V3_0_42_BOQ_LINES.json" in names and led["integration_package"] is True
    assert ident2["diff"]["vs_v3_0_41"] == {"SAME": 3, "CHANGED": 2, "ADDED": 1}


def test_held_never_zero_and_value_within_old_bound():
    lines, out, *_ = run()
    for x in out:
        if x["evidence_state"] in ("BLOCKED_RFI", "BOUNDED_EXPOSURE"):
            assert x["measured_net"] is None
    assert _e(out, "U-C:GROUND_SLAB:GROUND:C1")["measured_net"] <= 3.24


def test_units_mm_refused_and_mirror_order_same():
    lines = lines_3041()
    with pytest.raises(A.InputsError, match="mm"):
        A.load_inputs(inputs(lines, cell={"t": 120.0, "declared_m3": None}), PID)
    with pytest.raises(A.InputsError, match="mm2"):
        A.load_inputs(inputs(lines, panel={"panels": [{"id": "P4", "area": 6300000.0}], "declared_m3": None}), PID)
    rev = inputs(lines, cell={"panels": [{"id": "P3", "area": 1.2}, {"id": "P2", "area": 11.7},
                                         {"id": "P1", "area": 13.5}]})
    _, out_r, *_ = run(lines, rev)
    assert _e(out_r, "U-C:GROUND_SLAB:GROUND:C1")["measured_net"] == pytest.approx(3.168, abs=1e-12)


# ------------------------------------------------------------------------------------------------ adverse
def test_adverse_slab_cell_dropped_because_a_flight_is_drawn_hidden():
    """the engine's 'stair zone' cell has no GS line: the panel line is added, never a 0 line, never left out."""
    lines, out, *_ = run()
    c2 = [x for x in out if x["item_code"] == GS and x["location"]["element_id"].endswith(":C2")]
    assert len(c2) == 1 and c2[0]["measured_net"] > 0
    with pytest.raises(A.InputsError, match="HELD_AS_ZERO"):
        A.load_inputs(inputs(lines, panel={"panels": [{"id": "P4", "area": 0.0}], "declared_m3": None}), PID)


def test_adverse_panel_added_twice_or_cell_already_lined():
    lines = lines_3041()
    with pytest.raises(A.InputsError, match="already carries a ground-slab line"):
        run(lines, inputs(lines, panel={"cell": "C9", "element_id": "GS-T442:GROUND_SLAB:GROUND:C9b"}))
    with pytest.raises(A.InputsError, match="named twice"):
        A.load_inputs(inputs(lines, panel={"panels": [{"id": "P1", "area": 6.3}]}), PID)


def test_adverse_pit_raft_counted_again_as_slab():
    """a panel list that sneaks the shaft in (pit floor = raft top) no longer re-adds to the merged figure."""
    lines = lines_3041()
    with pytest.raises(A.InputsError, match="not the merged"):
        A.load_inputs(inputs(lines, cell={"panels": [{"id": "P1", "area": 13.5}, {"id": "P2", "area": 11.7},
                                                     {"id": "P3", "area": 1.2}, {"id": "SHAFT", "area": 2.56}]}), PID)


def test_adverse_value_above_old_bound_and_stale_binding():
    lines = lines_3041()
    with pytest.raises(A.InputsError, match="stale binding"):
        run(lines, inputs(lines, cell={"expect": {"evidence_state": "BOUNDED_EXPOSURE", "high": 3.3}}))
    big = copy.deepcopy(lines)
    big[0]["bounded_range"]["high"] = 3.0
    with pytest.raises(A.InputsError, match="exceeds the line's own held bound"):
        run(big, inputs(big, cell={"expect": {"evidence_state": "BOUNDED_EXPOSURE", "high": None}}))
    with pytest.raises(A.InputsError, match="not the held line"):
        run(lines, inputs(lines, cell={"line_id": _id(lines, "GS:GROUND_SLAB:GROUND:C9"), "cell": "C9"}))


def test_adverse_unverified_status_stays_held():
    lines = lines_3041()
    for k in ("area_status", "t_status"):
        with pytest.raises(A.InputsError, match="status"):
            A.load_inputs(inputs(lines, cell={k: "ASSUMED"}), PID)
        with pytest.raises(A.InputsError, match="status"):
            A.load_inputs(inputs(lines, panel={k: "UNKNOWN"}), PID)


def test_adverse_missing_data():
    lines = lines_3041()
    with pytest.raises(A.InputsError, match="no panel"):
        A.load_inputs(inputs(lines, cell={"panels": []}), PID)
    with pytest.raises(A.InputsError, match="not a number"):
        A.load_inputs(inputs(lines, panel={"t": None}), PID)
    with pytest.raises(A.InputsError, match="no merged source"):
        A.load_inputs(inputs(lines, cell={"source_tasks": ["T-X"]}), PID)
    with pytest.raises(A.InputsError, match="no cell, panel or cause text"):
        A.load_inputs(inputs(lines, cell="none", panel="none", texts=[]), PID)


def test_adverse_cause_text():
    lines = lines_3041()
    t = {"line_id": _id(lines, "COL:K1"), "item_code": "STR.CONC.COLUMN", "old": "D-77", "new": "D-12",
         "why": "x", "source_tasks": ["T-C"]}
    with pytest.raises(A.InputsError, match="stale binding"):
        run(lines, inputs(lines, texts=[t]))
    with pytest.raises(A.InputsError, match="a valued line"):
        run(lines, inputs(lines, texts=[dict(t, line_id=_id(lines, "COL:K2"), old="D-9")]))
    with pytest.raises(A.InputsError, match="replace the old item"):
        A.load_inputs(inputs(lines, texts=[dict(t, old="D-9", new="D-9 / D-12")]), PID)


def test_adverse_applied_once_and_check_catches_tamper():
    lines, out, ident, ch, log = run()
    with pytest.raises(A.InputsError, match="applied once"):
        A.changes_for(A.load_inputs(inputs(out), PID), out)
    bad = copy.deepcopy(out)
    x = _e(bad, "GS-T442:GROUND_SLAB:GROUND:C2")
    x["measured_net"] = 0.8
    with pytest.raises(ValueError, match="panels x T"):
        A.check_slab(bad)
    bad = copy.deepcopy(out)
    k = _e(bad, "COL:K1")
    k["bounded_range"]["high"] = 0.8
    with pytest.raises(ValueError, match="moved a figure"):
        A.check_slab(bad, lines)


def test_no_project_input_changes_nothing():
    lines = lines_3041()
    ch, log = A.changes_for(None, lines)
    assert ch == [] and log["state"] == "NO_PROJECT_INPUT"
    out, ident = A.integrate(lines, ch)
    assert [A30.line_sha(x) for x in out] == [A30.line_sha(x) for x in lines]
