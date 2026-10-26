"""T-255: ARCH_TAKEOFF_V3.0.19 on a hand-calculated NON-Alsenan villa (K255), normal and adverse.

Villa K255 (the ring of test_arc_band_rule.py, hand calculation):
  ring ground beam line carried on a chord reading 1.874326 m2 x D 0.80 = 1.499461 m3 (DRAWING-CONFIRMED);
  closed on its drawn faces: chord 1.874326 + north triangle 0.067082 = 1.941408 m2 x 0.80 = 1.553126 m3 (+0.053665 m3,
  +3.58 %); crown column C3 0.040000 m2 deducted in both readings.
  window K-W1 1.20 x 1.50 = 1.8000 m2 carried once in the GF window line (its formula names K-W1); its masonry line is
  HELD blank (register not integrated); the room plaster line carries 20.0000 m2 and its record names K-W1 deducted.
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v3019 as A  # noqa: E402
from engine.source import boq_line as BL  # noqa: E402

PID, REV = "villa-k255", "e" * 64
DC = A.DC
D = 0.80
CHORD, TRI, DRAWN = 1.874326, 0.067082, 1.941408
BEFORE, AFTER = round(CHORD * D, 6), round(DRAWN * D, 6)      # 1.499461 -> 1.553126


def _ln(code, eid, ev, net=None, floor="GF", formula="engine", rfi=None):
    return BL.make_line(project_id=PID, revision_set_sha256=REV, item_code=code, unit=BL.ITEMS[code][3],
                        evidence_state=ev, measured_net=net, element_id=eid, floor=floor, physical_element=eid,
                        formula=formula, rfi=rfi, documents=[{"file": "k255.dxf"}], rule_id="R-K", rule_version="1",
                        notes="k255")


def lines():
    q = {"question": "held", "unlocks": "x"}
    return [_ln("STR.CONC.GROUND_BEAM", "K:GB:RING", "SOURCE_DERIVED", BEFORE, floor="GROUND",
                formula="chord-closed net plan 1.874326 x 0.80"),
            _ln("STR.CONC.GROUND_BEAM", "K:GB:STRAIGHT", "SOURCE_DERIVED", 2.4, floor="GROUND"),
            _ln("ARCH.WINDOW", "K:WIN:GF", "SOURCE_DERIVED", 1, formula="K-W1 1.20 x 1.50 = 1.8000 m2"),
            _ln("MAS.BLOCK", "K:MAS:GF", "BLOCKED_RFI", rfi=q),
            _ln("FIN.PLASTER", "K:PL:R1", "SOURCE_DERIVED", 20.0, formula="run x h - K-W1 1.8000"),
            _ln("FIN.PLASTER", "K:PL:R2", "SOURCE_DERIVED", 12.0, formula="run x h")]


def ids(ls):
    return {ln["location"]["element_id"]: ln["line_id"] for ln in ls}


def ring(i, **kw):
    r = {"kind": "END_CLOSURE", "line_id": i["K:GB:RING"], "item_code": "STR.CONC.GROUND_BEAM",
         "element_id": "K:GB:RING", "task": "T-K", "physical_element": "ring ground beam",
         "before": {"evidence_state": "SOURCE_DERIVED", "measured_net": BEFORE}, "status": DC, "value": AFTER,
         "pieces": [{"id": "K-RING", "value": AFTER, "status": DC}],
         "retired": {"reading": "CHORD", "value": BEFORE},
         "arc_band": {"end_a": {"reading": "DRAWN_FACES", "closing_faces": ["beam face", "C1 west"]},
                      "end_b": {"reading": "DRAWN_FACES", "closing_faces": ["C2 west"]},
                      "drawn_net_m2": DRAWN, "retired_net_m2": CHORD, "depth_m": D,
                      "closing_pieces": [{"id": "K-N-TRI", "m2": TRI, "owned_by": i["K:GB:RING"]}],
                      "columns_in_band": [{"id": "C3", "m2": 0.04, "deducted": True}]}}
    r.update(kw)
    return r


def trace(i, **kw):
    t = {"opening": "K-W1", "floor": "GF", "kind": "WINDOW", "physical_element": "window K-W1", "task": "T-K",
         "trades": {"WINDOW_SUPPLY": {"state": "CARRIED_ONCE", "line_ids": [i["K:WIN:GF"]], "evidence": "formula"},
                    "MASONRY": {"state": "HELD", "line_ids": [i["K:MAS:GF"]], "held_item": "register not integrated",
                                "named_task": "T-K2"},
                    "FINISH_ROOM_SIDE": {"state": "CARRIED_ONCE", "line_ids": [i["K:PL:R1"]],
                                         "evidence": "deducted in the room line's formula"}}}
    t.update(kw)
    return t


def doc(ls=None, rec=None, tr=None):
    i = ids(ls or lines())
    src = {"file": "k255_ledger.csv", "sha256": "b" * 64, "task": "T-K", "merge_commit": "abc1234",
           "checker_run": "Checker K 1"}
    return {"schema": A.INPUTS_SCHEMA, "project": PID, "sources": [src],
            "records": [rec or ring(i)], "opening_trace": [tr or trace(i)]}


def run(d=None, ls=None):
    ls = ls or lines()
    d = d or doc(ls)
    A.load_inputs(d, PID)
    ch, log, tr = A.changes_for(d, ls)
    out, ident = A.integrate(ls, ch)
    return ls, out, ident, log, tr


# ------------------------------------------------------------------ normal
def test_normal_ring_rebased_on_drawn_faces_everything_else_identical():
    ls, out, ident, log, tr = run()
    i = ids(ls)
    by = {ln["line_id"]: ln for ln in out}
    rg = by[i["K:GB:RING"]]
    assert rg["measured_net"] == pytest.approx(1.553126, abs=1e-6)
    assert rg["evidence_state"] == "SOURCE_DERIVED"
    rec = rg["calculation"]["inputs"]["end_closure_v3019"]
    assert rec["evidence_status"] == DC and rec["retired"]["value"] == BEFORE
    assert ident["replaced"] == 1 and ident["outside_rows"] == len(ls) - 1 and ident["added"] == 0
    assert AFTER - BEFORE == pytest.approx(0.053665, abs=1e-6)
    assert {t["trade"]: t["state"] for t in tr} == {"WINDOW_SUPPLY": "CARRIED_ONCE", "MASONRY": "HELD",
                                                    "FINISH_ROOM_SIDE": "CARRIED_ONCE"}


def test_normal_write_files(tmp_path):
    ls, out, ident, log, tr = run()
    d = doc(ls)
    ch, log, tr = A.changes_for(d, ls)
    names, ident, led = A.write(tmp_path, ls, ch, log, tr, d)
    assert "V3_0_19_OPENING_TRACE.csv" in names and "V3_0_19_DIFF.csv" in names
    diff = (tmp_path / "V3_0_19_DIFF.csv").read_text(encoding="utf-8").splitlines()
    assert sum(",CHANGED," in r for r in diff) == 1 and sum(",SAME," in r for r in diff) == len(ls) - 1


def test_order_invariance_of_lines():
    ls = lines()
    a = run(ls=ls)[1]
    b = run(ls=list(reversed(ls)))[1]
    assert sorted(A.A30.line_sha(x) for x in a) == sorted(A.A30.line_sha(x) for x in b)


# ------------------------------------------------------------------ adverse: the ring record
def _refused(mut, match):
    ls = lines()
    i = ids(ls)
    r = ring(i)
    mut(r, i)
    with pytest.raises(A.InputsError, match=match):
        run(doc(ls, rec=r), ls)


def test_adverse_chord_reading_refused():
    _refused(lambda r, i: r["arc_band"]["end_a"].update(reading="CHORD"), "refused: drawn faces")


def test_adverse_end_without_drawn_face_refused():
    _refused(lambda r, i: r["arc_band"]["end_b"].update(closing_faces=[]), "not established")


def test_adverse_triangle_owned_by_the_straight_beam_refused():
    _refused(lambda r, i: r["arc_band"]["closing_pieces"][0].update(owned_by=i["K:GB:STRAIGHT"]), "one owner")


def test_adverse_triangle_also_in_another_line_refused():
    _refused(lambda r, i: r["arc_band"]["closing_pieces"][0].update(also_in=[i["K:GB:STRAIGHT"]]), "double count")


def test_adverse_triangle_booked_on_another_line_in_the_run_refused():
    ls = lines()
    i = ids(ls)
    st = ls[1]
    st["calculation"]["inputs"] = {"pieces": ["K-N-TRI"]}
    with pytest.raises(A.InputsError, match="also booked"):
        run(doc(ls), ls)


def test_adverse_column_left_in_refused():
    _refused(lambda r, i: r["arc_band"]["columns_in_band"][0].update(deducted=False), "not deducted")


def test_adverse_reconciliation_not_closing_refused():
    _refused(lambda r, i: r["arc_band"]["closing_pieces"][0].update(m2=0.05), "does not close")


def test_adverse_value_not_net_times_depth_refused():
    def m(r, i):
        r["value"] = 1.56
        r["pieces"][0]["value"] = 1.56
    _refused(m, "not drawn net")


def test_adverse_depth_in_mm_refused():
    def m(r, i):
        r["arc_band"]["depth_m"] = 800.0
    _refused(m, "not drawn net")


def test_adverse_stale_before_refused():
    def m(r, i):
        r["before"]["measured_net"] = 1.4994      # the ledger read an older line (1.499461 now)
        r["retired"]["value"] = 1.4994
    _refused(m, "stale ledger")


def test_adverse_unnamed_residual_of_the_retired_reading_refused():
    def m(r, i):
        r["arc_band"]["retired_net_m2"] = CHORD - 0.001
        r["arc_band"]["closing_pieces"][0]["m2"] = TRI + 0.001
    _refused(m, "name the residual")


def test_named_residual_is_accepted_and_carried():
    ls = lines()
    i = ids(ls)
    r = ring(i)
    r["arc_band"]["retired_net_m2"] = CHORD - 0.001
    r["arc_band"]["closing_pieces"][0]["m2"] = TRI + 0.001
    r["arc_band"]["retired_residual"] = {"m2": 0.001, "cause": "the carried polygon rounded"}
    out = run(doc(ls, rec=r), ls)[1]
    rec = {ln["line_id"]: ln for ln in out}[i["K:GB:RING"]]["calculation"]["inputs"]["end_closure_v3019"]
    assert rec["arc_band"]["retired_residual"]["m2"] == 0.001


def test_adverse_held_value_zero_refused():
    def m(r, i):
        r["value"] = 0
        r["pieces"][0]["value"] = 0
    _refused(m, "value > 0")


def test_adverse_line_not_in_the_run_refused():
    def m(r, i):
        r["line_id"] = "L-0000"
        r["arc_band"]["closing_pieces"][0]["owned_by"] = "L-0000"
    _refused(m, "does not carry")


# ------------------------------------------------------------------ adverse: the opening trace
def _trace_refused(mut, match):
    ls = lines()
    i = ids(ls)
    t = trace(i)
    mut(t, i)
    with pytest.raises(A.InputsError, match=match):
        run(doc(ls, tr=t), ls)


def test_adverse_opening_deducted_in_two_lines_of_one_side_refused():
    _trace_refused(lambda t, i: t["trades"]["FINISH_ROOM_SIDE"].update(line_ids=[i["K:PL:R1"], i["K:PL:R2"]]),
                   "double count")


def test_adverse_carried_line_that_does_not_name_the_opening_refused():
    _trace_refused(lambda t, i: t["trades"]["FINISH_ROOM_SIDE"].update(line_ids=[i["K:PL:R2"]]), "does not name")


def test_adverse_carried_in_a_held_line_refused():
    _trace_refused(lambda t, i: t["trades"]["MASONRY"].update(state="CARRIED_ONCE", evidence="x"), "carries no quantity")


def test_adverse_held_without_named_task_refused():
    _trace_refused(lambda t, i: t["trades"]["MASONRY"].pop("named_task"), "package / task")


def test_adverse_held_trade_on_a_quantity_line_must_say_what_the_line_covers():
    _trace_refused(lambda t, i: t["trades"]["MASONRY"].update(line_ids=[i["K:PL:R2"]]), "includes the opening")


def test_adverse_not_applicable_with_a_line_refused():
    _trace_refused(lambda t, i: t["trades"]["MASONRY"].update(state="NOT_APPLICABLE", why="glazed host"),
                   "NOT_APPLICABLE")


def test_adverse_unknown_line_in_trace_refused():
    _trace_refused(lambda t, i: t["trades"]["WINDOW_SUPPLY"].update(line_ids=["L-0000"]), "not a line of the run")


def test_adverse_supply_or_masonry_missing_refused():
    _trace_refused(lambda t, i: t["trades"].pop("MASONRY"), "at least")


def test_adverse_trace_value_differs_from_the_line_refused():
    def m(t, i):
        t["trades"]["WINDOW_SUPPLY"].update(value=1.9, value_field=["window", "m2"])
    _trace_refused(m, "carries")
