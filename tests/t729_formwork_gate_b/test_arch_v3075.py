"""T-729: ARCH_TAKEOFF_V3.0.75 (FORMWORK_GATE_B_V1 + CONCRETE_GATE_B_V10, R-T729-1) on the hand-calculated NON-Alsenan
villa F729 (own figures, no drawing; every figure below by hand):
  F1  beam side, fix row (split face measured CALCULATED, held only for the per-line split): RELEASE 4.000 m2.
  F2  column shaft, fix row RELEASE_LOW_END: 0.25 x 0.50 perimeter 1.50 x (4.50 - 0.75) = 5.625 m2 released; its
      joint faces stay HELD 0.300 .. 0.300 beside (companion, never summed).
  F3  beam with a width conflict (schedule 0.20 vs drawn 0.25), span 4.00 m: side 2 x 4.00 x 0.30 = 2.400 (no width in
      it) + soffit 0.20 x 4.00 = 0.800 .. 0.25 x 4.00 = 1.000 -> BOUND 3.200 .. 3.400 m2.
  F4  parapet RC height unknown above the 0.30 upstand: 2 x 0.30 x 10.00 = AT_LEAST 6.000 m2 (upper end open).
  F5  joint strip 0 .. 0.250 decided by a neighbour: CAP 0.250 beside (never a quantity).
  F6  ground beam face below natural ground (formed or earth-cast not printed): NAMED, blank.
  S1  stair well side two readings: BOUND 1.904 .. 2.380 m2; S2 stair west wall 0 .. 0.800: CAP 0.800.
  G1  boundary ground beam 20.00 m x 0.20 x 0.40 = 1.600 m3 gross, columns inside not counted: carried 0 .. 1.600 ->
      CAP 1.600 (a 0 low is no floor), blank.
  T1  stair flight lower figure 1.000001 printed half-up; exact sum 1.0000004 floors to 1.000000: AT_LEAST restated.
  B1  projection band beam (blank) + a strip piece no line carries: ADD_NAMED child 0.16 m3 per m of depth (information).
  R*  released column 2.000 m3, released formwork 10.000 m2, released plaster 50.000 m2: byte-identical.
Totals by hand: STR.FORMWORK released +9.625 (4.000 + 5.625), bounded +1 (3.200 .. 3.400), blocked -3 (6 blank -> 3);
STR.FORMWORK.STAIR bounded +1 (1.904 .. 2.380), blocked -1; STR.CONC.GROUND_BEAM bounded -1, high -1.600, blocked +1;
STR.CONC.BEAM lines +1, blocked +1; G2 (a BLOCKED_RFI line with a 0 .. 0.800 record, counted blocked) capped 0.800
with no total moving; STR.CONC.STAIR, released lines and FIN.PLASTER unchanged.
Adverse: a cap of 0, VERIFIED status, a stale element / range, applied twice, low above high, a unit slip, an AT_LEAST
restating a figure the line does not carry, the same figure restated, a low-end release without its companion, a line
named twice, a child with a figure, a formwork action on a concrete line, a cap that is not the range's high."""
from __future__ import annotations

import copy
import random
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v304 as A304  # noqa: E402
from engine.source import arch_v3073 as A3073  # noqa: E402
from engine.source import arch_v3075 as A  # noqa: E402
from engine.source import boq_line as BL  # noqa: E402

PID, REV = "F729-SYNTHETIC", "e" * 64
FW, FWS = "STR.FORMWORK", "STR.FORMWORK.STAIR"


def _ln(code, eid, state, net=None, unit="m2", rng=None, floor="GF", rec=None):
    ln = BL.make_line(project_id=PID, revision_set_sha256=REV, item_code=code, unit=unit, evidence_state=state,
                      measured_net=net, gross=net, element_id=eid, floor=floor, room_id=None,
                      bounded_range=None if rng is None else {"low": rng[0], "high": rng[1], "basis": "synthetic"},
                      formula=f"synthetic {code} {eid}", inputs=rec, rule_id="R-SYN", rule_version="1",
                      geometry_source="SYNTHETIC_FIXTURE", material_state="BY_SPEC",
                      rfi={"question": "not printed", "unlocks": eid} if state in ("BLOCKED_RFI",
                                                                                   "BOUNDED_EXPOSURE") else None,
                      notes="synthetic", **({} if code in BL.ITEMS else
                                            {"item_en": code, "item_ar": code, "trade": "CONCRETE"}))
    return BL.validate(ln)


def base():
    t1 = {A3073.REC_KEY: {"beside": {"kind": "AT_LEAST_M3", "value": 1.000001, "basis": "synthetic"}}}
    return [
        _ln(FW, "FW:FACE:F1", "BLOCKED_RFI"),
        _ln(FW, "FW:COL-F2:FACES:HELD", "BLOCKED_RFI"),
        _ln(FW, "FW:FACE:F3", "BLOCKED_RFI"),
        _ln(FW, "FW:FACE:F4", "BLOCKED_RFI"),
        _ln(FW, "FW:FACE:F5", "BLOCKED_RFI"),
        _ln(FW, "FW:GB-F6:FACES:HELD:OQ10", "BLOCKED_RFI"),
        _ln(FWS, "FW:S1:SIDE", "BLOCKED_RFI"),
        _ln(FWS, "FW:S2:SIDE", "BLOCKED_RFI"),
        _ln("STR.CONC.GROUND_BEAM", "GB:G1:BOUNDARY", "BOUNDED_EXPOSURE", unit="m3", rng=(0.0, 1.6)),
        _ln("STR.CONC.GROUND_BEAM", "GB:G2:RECORD", "BLOCKED_RFI", unit="m3", rng=(0.0, 0.8)),
        _ln("STR.CONC.STAIR", "ST:T1", "BLOCKED_RFI", unit="m3", rec=t1),
        _ln("STR.CONC.BEAM", "HL:BEAM_LEDGER:GF:BM-B1#BAND1.1", "BLOCKED_RFI", unit="m3"),
        _ln("STR.CONC.COLUMN", "COL:R1", "MEASURED", net=2.0, unit="m3"),
        _ln(FW, "FW:R1:FACES", "MEASURED", net=10.0),
        _ln("FIN.PLASTER", "R1:PLASTER", "MEASURED", net=50.0),
    ]


LN = base()
ID = {ln["location"]["element_id"]: ln["line_id"] for ln in LN}
SRC = [{"task": t, "file": f"research/f729/{t}.json", "sha256": "a" * 64, "merge_commit": "b" * 40,
        "checker_run": f"checker {t} Gate A PASS"} for t in ("T-A", "T-B", "T-M")]


def _e(eid, action, code=FW, unit="m2", elow=None, ehigh=None, **kw):
    piece = A.P_FW if code in (FW, FWS) else A.P_C10
    return dict({"piece": piece, "action": action, "line_id": ID[eid], "source_tasks": ["T-A", "T-M"],
                 "rule": "R-SYN", "status": "HELD", "why": f"synthetic cause {eid}",
                 "expect": {"item_code": code, "element_id": eid, "unit": unit, "class": "HELD", "low": elow,
                            "high": ehigh}}, **kw)


def doc():
    return {"schema": A.INPUTS_SCHEMA, "project_id": PID, "sources": copy.deepcopy(SRC), "entries": [
        _e("FW:FACE:F1", "RELEASE", fix="FR-1", kind="RELEASE", value="4.000", basis="face F1 4.000 m2 CALCULATED"),
        _e("FW:COL-F2:FACES:HELD", "RELEASE", fix="FR-2", kind="RELEASE_LOW_END", value="5.625",
           basis="1.50 x (4.50 - 0.75) = 5.625", companion={"low": "0.300", "high": "0.300", "why": "joint faces"}),
        _e("FW:FACE:F3", "BOUND", low="3.200", high="3.400"),
        _e("FW:FACE:F4", "AT_LEAST", low="6.000"),
        _e("FW:FACE:F5", "CAP", cap="0.250"),
        _e("FW:GB-F6:FACES:HELD:OQ10", "NAMED"),
        _e("FW:S1:SIDE", "BOUND", code=FWS, low="1.904", high="2.380"),
        _e("FW:S2:SIDE", "CAP", code=FWS, cap="0.800"),
        _e("GB:G1:BOUNDARY", "CAP", code="STR.CONC.GROUND_BEAM", unit="m3", elow=0.0, ehigh=1.6, cap="1.600"),
        _e("GB:G2:RECORD", "CAP", code="STR.CONC.GROUND_BEAM", unit="m3", elow=0.0, ehigh=0.8, cap="0.800"),
        dict(_e("ST:T1", "AT_LEAST", code="STR.CONC.STAIR", unit="m3", low="1.000000",
                restates={"value": "1.000001", "why": "half-up print; exact sum floors (R-T696-1)"}),
             expect={"item_code": "STR.CONC.STAIR", "element_id": "ST:T1", "unit": "m3", "class": "HELD",
                     "low": None, "high": None, "beside": {"kind": "AT_LEAST_M3", "value": 1.000001}}),
        {"piece": A.P_C10, "action": "ADD_NAMED", "line_id": None, "child_key": "B1-STRIP",
         "host_line_id": ID["HL:BEAM_LEDGER:GF:BM-B1#BAND1.1"], "source_tasks": ["T-B", "T-M"], "rule": "R-SYN-4",
         "status": "HELD", "item": "D-X projection section not printed", "member": "BM-B1 projection",
         "per_unit": "0.160000 m3 per m of depth (plan 0.16 m2)", "why": "depth not printed"},
    ]}


def run(d=None, lines=None):
    lines = copy.deepcopy(LN) if lines is None else lines
    inp = A.load_inputs(d or doc(), PID)
    ch, log = A.changes_for(inp, lines)
    new, ident = A.integrate(lines, ch)
    return lines, ch, new, ident


def by_eid(lines):
    return {ln["location"]["element_id"]: ln for ln in lines}


# ------------------------------------------------------------------------------------------------- normal
def test_states_by_hand():
    _p, ch, new, ident = run()
    L = by_eid(new)
    assert L["FW:FACE:F1"]["measured_net"] == 4.0 and A.line_class(L["FW:FACE:F1"]) == "RELEASED"
    f2 = L["FW:COL-F2:FACES:HELD"]
    assert f2["measured_net"] == 5.625
    assert f2["calculation"]["inputs"][A.REC_KEY]["companion"]["low"] == 0.3
    assert L["FW:FACE:F3"]["bounded_range"]["low"] == 3.2 and L["FW:FACE:F3"]["bounded_range"]["high"] == 3.4
    assert A.fw_beside(L["FW:FACE:F4"]) == [("AT_LEAST_M2", 6.0)] and L["FW:FACE:F4"]["measured_net"] is None
    assert A.fw_beside(L["FW:FACE:F5"]) == [("AT_MOST_M2", 0.25)] and L["FW:FACE:F5"]["bounded_range"] is None
    f6 = L["FW:GB-F6:FACES:HELD:OQ10"]
    assert f6["measured_net"] is None and f6["bounded_range"] is None and not A.fw_beside(f6)
    assert f6["rfi"]["question"].startswith("open:")
    assert L["FW:S1:SIDE"]["bounded_range"]["low"] == 1.904
    g1 = L["GB:G1:BOUNDARY"]
    assert g1["bounded_range"] is None and A.conc_figures(g1) == [(A.REC_KEY, "AT_MOST_M3", 1.6)]
    t1 = L["ST:T1"]
    assert A.conc_figures(t1) == [(A.REC_KEY, "AT_LEAST_M3", 1.0)]
    assert A3073.REC_KEY in t1["calculation"]["inputs"][A.REC_KEY]["superseded"]
    child = [ln for ln in new if ln["location"]["element_id"].endswith("#B1-STRIP")]
    assert len(child) == 1 and child[0]["item_code"] == "STR.CONC.BEAM" and child[0]["measured_net"] is None
    g2 = L["GB:G2:RECORD"]          # a BLOCKED_RFI line carrying a 0 .. x record (counted blocked): capped the same
    assert g2["bounded_range"] is None and A.conc_figures(g2) == [(A.REC_KEY, "AT_MOST_M3", 0.8)]
    assert L["FW:FACE:F1"]["evidence_state"] == "PROVISIONAL"
    assert ident["added"] == 1 and ident["replaced"] == 11
    assert ident["formwork_concrete"] == {"FW_WIRE:RELEASE": 2, "FW_WIRE:BOUND": 2, "FW_WIRE:AT_LEAST": 1,
                                          "FW_WIRE:CAP": 2, "FW_WIRE:NAMED": 1, "CONC_C10:CAP": 2,
                                          "CONC_C10:AT_LEAST": 1, "CONC_C10:ADD_NAMED": 1}


def test_totals_by_hand():
    p, ch, new, _i = run()
    t0, t1 = A304.code_totals(p), A304.code_totals(new)
    moved = A.check_totals(t0, t1, ch)

    def d(k, f):
        return round(t1[k][f] - t0[k][f], 6)
    assert d("STR.FORMWORK|m2", "released") == 9.625
    assert (d("STR.FORMWORK|m2", "held_low"), d("STR.FORMWORK|m2", "held_high")) == (3.2, 3.4)
    assert (d("STR.FORMWORK|m2", "bounded_lines"), d("STR.FORMWORK|m2", "blocked_lines")) == (1, -3)
    assert (d("STR.FORMWORK.STAIR|m2", "held_low"), d("STR.FORMWORK.STAIR|m2", "held_high")) == (1.904, 2.38)
    assert (d("STR.CONC.GROUND_BEAM|m3", "held_high"), d("STR.CONC.GROUND_BEAM|m3", "bounded_lines"),
            d("STR.CONC.GROUND_BEAM|m3", "blocked_lines")) == (-1.6, -1, 1)
    assert (d("STR.CONC.BEAM|m3", "lines"), d("STR.CONC.BEAM|m3", "blocked_lines")) == (1, 1)
    assert set(moved) == {"STR.FORMWORK|m2", "STR.FORMWORK.STAIR|m2", "STR.CONC.GROUND_BEAM|m3", "STR.CONC.BEAM|m3"}
    for k in ("STR.CONC.COLUMN|m3", "FIN.PLASTER|m2", "STR.CONC.STAIR|m3"):
        assert t0[k] == t1[k]


def test_beside_figures_never_in_totals_and_census():
    p, _ch, new, _i = run()
    c = A.census(new)
    assert c[FW]["beside_sum_run_record_only"] == {"AT_LEAST_M2": 6.0, "AT_MOST_M2": 0.25}
    assert c[FW]["released_q"] == 19.625 and c[FW]["bounded"] == 1 and c[FW]["blank"] == 3
    assert A304.code_totals(new)["STR.FORMWORK|m2"]["held_high"] == 3.4     # neither 6.0 nor 0.25 entered


def test_outside_lines_byte_identical_and_mirror_order():
    p, _ch, new, _i = run()
    L0, L1 = by_eid(p), by_eid(new)
    for eid in ("COL:R1", "FW:R1:FACES", "R1:PLASTER"):
        assert BL.dumps([L0[eid]]) == BL.dumps([L1[eid]])
    d = doc()
    random.Random(7).shuffle(d["entries"])
    _p2, _c2, new2, _i2 = run(d)
    assert BL.dumps(sorted(new, key=lambda x: x["line_id"])) == BL.dumps(sorted(new2, key=lambda x: x["line_id"]))


def test_written_files(tmp_path):
    p, ch, _new, _i = run()
    names, ident, led = A.write(tmp_path, p, ch, {"piece": "T729"})
    assert "V3_0_75_BOQ_LINES.json" in names and led["integration_package"] is True
    assert ident["diff"]["vs_base"] == {"CHANGED": 11, "ADDED": 1, "SAME": 4}
    assert all(r["release_status"] == "NOT RELEASED" for r in led["rows"])


# ------------------------------------------------------------------------------------------------- adverse
def _bad(mut, match):
    d = doc()
    mut(d)
    with pytest.raises((A.InputsError, ValueError), match=match):
        run(d)


def _ent(d, eid):
    return [e for e in d["entries"] if e.get("line_id") == ID.get(eid)][0]


def test_cap_zero_refused():
    _bad(lambda d: _ent(d, "FW:FACE:F5").update(cap="0"), "cap of 0")


def test_verified_status_refused():
    _bad(lambda d: _ent(d, "FW:FACE:F3").update(status="VERIFIED"), "never VERIFIED")


def test_stale_element_and_range():
    _bad(lambda d: _ent(d, "FW:FACE:F3")["expect"].update(element_id="FW:FACE:OTHER"), "stale binding")
    _bad(lambda d: _ent(d, "GB:G1:BOUNDARY")["expect"].update(high=1.7), "stale binding")


def test_low_above_high_and_unit_slip():
    _bad(lambda d: _ent(d, "FW:FACE:F3").update(low="3.500"), "low")
    _bad(lambda d: _ent(d, "FW:FACE:F4").update(low="6000"), "unit slip")
    _bad(lambda d: _ent(d, "FW:FACE:F3")["expect"].update(unit="m3"), "not a HELD line")


def test_applied_twice():
    p, _ch, new, _i = run()
    with pytest.raises(A.InputsError, match="applied once"):
        A.changes_for(A.load_inputs(doc(), PID), new)


def test_restate_figure_mismatch_and_same_figure():
    _bad(lambda d: _ent(d, "ST:T1")["restates"].update(value="1.000002"), "one live statement")
    _bad(lambda d: _ent(d, "ST:T1").update(low="1.000001"), "same figure")


def test_low_end_release_needs_companion():
    _bad(lambda d: _ent(d, "FW:COL-F2:FACES:HELD").update(companion=None), "companion")
    _bad(lambda d: _ent(d, "FW:FACE:F1").update(fix=None), "fix row")


def test_line_named_twice():
    _bad(lambda d: d["entries"].append(copy.deepcopy(_ent(d, "FW:FACE:F4"))), "named twice")


def test_child_with_figure_and_cap_not_high():
    _bad(lambda d: d["entries"][-1].update(low="0.1"), "no figure")
    _bad(lambda d: _ent(d, "GB:G1:BOUNDARY").update(cap="1.500"), "not the range's high")


def test_formwork_action_on_concrete_line():
    def m(d):
        e = _ent(d, "GB:G1:BOUNDARY")
        e["piece"] = A.P_FW
    _bad(m, "not a HELD line")


def test_named_line_blank_never_zero():
    _p, _ch, new, _i = run()
    for ln in new:
        rec = ln["calculation"]["inputs"].get(A.REC_KEY)
        if rec and rec["action"] in ("NAMED", "ADD_NAMED", "CAP", "AT_LEAST"):
            assert ln["measured_net"] is None and ln["gross"] is None
