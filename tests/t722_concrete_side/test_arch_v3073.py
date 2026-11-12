"""T-722: ARCH_TAKEOFF_V3.0.73 (CONCRETE_GATE_B_V9, R-T722-1) on the hand-calculated NON-Alsenan villa C722 (own
figures, no drawing; every figure below by hand):
  C1  2F column, held 0.300 .. 0.450 m3 (section readings 0.10 / 0.12 m2, height 3.00 .. 3.75 m); a one-plane slab top
      raises the least height to 3.25 m: NARROW low = 0.10 x 3.25 = 0.325000, high 0.450 kept; COLUMN held_low +0.025.
  C2  2F column 0.25 x 0.40 = 0.10 m2, held 0.280 .. 0.390; plate h 2.8051 m: 0.10 x 2.8051 = 0.28051 -> 0.280510.
  T1  tank column, blank (high open: up / down stand): AT_LEAST 0.10 x 3.30 = 0.330 beside, never a range, never 0.
  G1  ground beam, blank, V3.0.63 AT_LEAST 0.135473 beside; the ledger re-measured 0.541924 m2 x 0.25 = 0.135481:
      RESTATED (named), the old record kept under `superseded`, one live statement.
  G2  ground beam, blank, V3.0.63 AT_LEAST 0.400 beside; the ledger says the same 0.400: CONFIRMED, never restated.
  B1  beam projection, blank, no figure: NAMED (D-26 analogue), 0.435 m3 per m of depth (information only).
  B9  beam, blank, V3.0.63 AT_LEAST 0.200 beside: a NAMED entry on it is refused (text never removes a figure).
  P1  RC parapet, blank, its V3.0.23 record prints the floor 5.592956 m2 x 0.30 = 1.6778868 rounded half-UP to
      1.677887 (above the exact lower end): RESTATED to 1.677886 (R-T696-1), the V3.0.23 record kept as history.
  P2  RC parapet, blank, V3.0.23 floor 1.6245 = the ledger's 5.415 x 0.30: CONFIRMED, never restated.
  R1  released column 2.000 m3 and a plaster line: byte-identical; released never moves; no code total but COLUMN moves.
Adverse: mirror order of entries, units (cm2 / mm), a range from 0, a moved high, a widened low, a stale binding, a
released line, a non-concrete code, applied twice, an undeclared second figure, a restatement of the same figure."""
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
from engine.source import arch_v3073 as A  # noqa: E402
from engine.source import boq_line as BL  # noqa: E402

PID, REV = "C722-SYNTHETIC", "e" * 64
COL, GB, BM, PP = "STR.CONC.COLUMN", "STR.CONC.GROUND_BEAM", "STR.CONC.BEAM", "STR.CONC.PARAPET"
V63, V23 = "concrete_ledger_v3063", "parapet_rc_v3023"


def _ln(code, eid, state, net=None, unit="m3", rec=None, rng=None, floor="2F"):
    ln = BL.make_line(project_id=PID, revision_set_sha256=REV, item_code=code, unit=unit, evidence_state=state,
                      measured_net=net, gross=net, element_id=eid, floor=floor, room_id=None,
                      bounded_range=None if rng is None else {"low": rng[0], "high": rng[1], "basis": "synthetic"},
                      formula=f"synthetic {code} {eid}", rule_id="R-SYN", rule_version="1",
                      geometry_source="SYNTHETIC_FIXTURE", material_state="BY_SPEC", inputs=rec,
                      rfi={"question": "datum not printed", "unlocks": eid} if state in ("BLOCKED_RFI",
                                                                                         "BOUNDED_EXPOSURE") else None,
                      notes="synthetic")
    return BL.validate(ln)


def _v63(v):
    return {V63: {"action": "LOWER_ONLY", "was": {"class": "HELD"},
                  "beside": {"kind": "AT_LEAST_M3", "value": v, "basis": "drawn area x least depth"}}}


def _v23(v):
    return {V23: {"bound": {"floor_at_least_m3": v, "all_rc_printed_part_m3": [2.8, 2.84]}}}


def base():
    return [
        _ln(COL, "COL:C1", "BOUNDED_EXPOSURE", rng=(0.30, 0.45)),
        _ln(COL, "COL:C2", "BOUNDED_EXPOSURE", rng=(0.28, 0.39)),
        _ln(COL, "COL:T1", "BLOCKED_RFI"),
        _ln(GB, "GB:G1", "BLOCKED_RFI", rec=_v63(0.135473), floor="GROUND"),
        _ln(GB, "GB:G2", "BLOCKED_RFI", rec=_v63(0.4), floor="GROUND"),
        _ln(BM, "BM:B1", "BLOCKED_RFI", floor="1F"),
        _ln(BM, "BM:B9", "BLOCKED_RFI", rec=_v63(0.2), floor="1F"),
        _ln(PP, "PP:P1", "BLOCKED_RFI", rec=_v23(1.677887), floor="GF"),
        _ln(PP, "PP:P2", "BLOCKED_RFI", rec=_v23(1.6245), floor="2F"),
        _ln(COL, "COL:R1", "MEASURED", net=2.0),
        _ln("FIN.PLASTER", "R1:PLASTER", "PROVISIONAL", net=44.31, unit="m2"),
    ]


LN = base()
ID = {ln["location"]["element_id"].split(":")[1]: ln["line_id"] for ln in LN}
SRC = {"task": "T-P", "file": "research/c722/T-P.json", "sha256": "a" * 64, "merge_commit": "b" * 40,
       "checker_run": "checker T-P Gate A PASS"}


def _x(k, code, rng=None):
    pre = {COL: "COL", GB: "GB", BM: "BM", PP: "PP"}.get(code, code.split(".")[-1])
    return {"item_code": code, "element_id": f"{pre}:{k}",
            "unit": "m3", "class": "HELD", "low": None if rng is None else rng[0],
            "high": None if rng is None else rng[1]}


def _e(action, k, code, **kw):
    e = {"action": action, "line_id": ID[k], "source_tasks": ["T-P"], "member": f"member {k}",
         "item": f"D-{k} (datum not printed)", "basis": f"{k} by hand", "question": f"DESIGNER ITEM D-{k}",
         "expect": _x(k, code, kw.pop("rng", None))}
    e.update(kw)
    return e


def entries():
    return [
        _e("NARROW", "C1", COL, rng=(0.30, 0.45), terms={"kind": "PLATE", "areas_m2": ["0.10", "0.12"],
                                                          "h_lo_m": "3.25", "top_lo_m": "12.90"},
           after={"low": "0.325000", "high": "0.450000"}),
        _e("NARROW", "C2", COL, rng=(0.28, 0.39), terms={"kind": "PLATE", "areas_m2": ["0.10"], "h_lo_m": "2.8051",
                                                          "top_lo_m": "12.90"},
           after={"low": "0.280510", "high": "0.39"}),
        _e("AT_LEAST", "T1", COL, beside={"value": "0.330000", "basis": "tank column lower end",
                                          "hand": "0.10 x 3.30"}),
        _e("AT_LEAST", "G1", GB, beside={"value": "0.135481", "basis": "re-measured area x 0.25",
                                         "hand": "0.541924 x 0.25"},
           restates={"record": V63, "value": "0.135473", "why": "re-measured area"}),
        _e("NAMED", "B1", BM, why="no section printed", per_unit="0.435 m3 per m of depth"),
        _e("AT_LEAST", "P1", PP, beside={"value": "1.677886", "basis": "tops x upstand", "hand": "5.592956 x 0.30"},
           restates={"record": V23, "value": "1.677887", "why": "half-up floor above the exact lower end"}),
    ]


def doc(ents=None, confirm=None):
    return {"schema": A.INPUTS_SCHEMA, "project_id": PID, "sources": [dict(SRC)],
            "entries": entries() if ents is None else ents,
            "confirm": [{"line_id": ID["G2"], "kind": "AT_LEAST_M3", "value": 0.4},
                        {"line_id": ID["P2"], "kind": "AT_LEAST_M3", "value": 1.6245, "record": V23}]
            if confirm is None else confirm}


def run(d=None, prev=None):
    prev = copy.deepcopy(LN) if prev is None else prev
    inp = A.load_inputs(d or doc(), PID)
    ch, log = A.changes_for(inp, prev)
    new, ident = A.integrate(prev, ch)
    return prev, ch, log, new, ident


def _by(lines):
    return {ln["line_id"]: ln for ln in lines}


# ---------------------------------------------------------------- normal case (hand figures)
def test_normal_hand_figures():
    prev, ch, log, new, ident = run()
    n = _by(new)
    assert n[ID["C1"]]["bounded_range"]["low"] == pytest.approx(0.325, abs=1e-12)
    assert n[ID["C1"]]["bounded_range"]["high"] == pytest.approx(0.45, abs=1e-12)
    assert n[ID["C2"]]["bounded_range"]["low"] == pytest.approx(0.28051, abs=1e-12)
    t1 = n[ID["T1"]]
    assert t1["evidence_state"] == "BLOCKED_RFI" and t1["bounded_range"] is None and t1["measured_net"] is None
    assert t1["calculation"]["inputs"][A.REC_KEY]["beside"]["value"] == pytest.approx(0.33)
    g1 = n[ID["G1"]]
    rec = g1["calculation"]["inputs"][A.REC_KEY]
    assert rec["beside"]["value"] == pytest.approx(0.135481) and V63 in rec["superseded"]
    assert A.figures_beside(g1) == [(A.REC_KEY, "AT_LEAST_M3", 0.135481)]   # one live statement (the new record)
    assert rec["was"]["beside"] == [{"record": V63, "kind": "AT_LEAST_M3", "value": 0.135473}]
    b1 = n[ID["B1"]]
    assert b1["calculation"]["inputs"][A.REC_KEY]["beside"] is None and b1["bounded_range"] is None
    assert "information, never a bound" in b1["calculation"]["formula"]
    p1 = n[ID["P1"]]["calculation"]["inputs"]
    assert V23 in p1 and A.figures_beside(n[ID["P1"]]) == [(A.REC_KEY, "AT_LEAST_M3", 1.677886)]
    assert p1[V23]["bound"]["all_rc_printed_part_m3"] == [2.8, 2.84]        # its other readings stay
    assert ident["concrete"] == {"NARROW": 2, "AT_LEAST": 3, "NAMED": 1}
    assert ident["replaced"] == 6 and ident["outside_rows"] == 5
    assert [c["record"] for c in log["confirmed_unchanged"]] == [V63, V23] and log["restated"][0]["from"] == 0.135473


def test_totals_move_only_column_low():
    prev, ch, _log, new, _i = run()
    t0, t1 = A304.code_totals(prev), A304.code_totals(new)
    moved = A.check_totals(t0, t1, ch)
    assert sorted(moved) == [f"{COL}|m3"]
    z0, z1 = t0[f"{COL}|m3"], t1[f"{COL}|m3"]
    assert z1["held_low"] - z0["held_low"] == pytest.approx(0.025 + 0.00051, abs=1e-9)
    assert z1["held_high"] == pytest.approx(z0["held_high"]) and z1["released"] == pytest.approx(2.0)
    assert z1["blocked_lines"] == z0["blocked_lines"] and z1["bounded_lines"] == z0["bounded_lines"]
    assert t1[f"{GB}|m3"] == t0[f"{GB}|m3"] and t1[f"{BM}|m3"] == t0[f"{BM}|m3"] and t1[f"{PP}|m3"] == t0[f"{PP}|m3"]


def test_outside_lines_byte_identical_and_mirror_order():
    prev, _c, _l, new, _i = run()
    for k in ("R1", "PLASTER", "G2", "B9", "P2"):
        lid = ID[k]
        assert A30.line_sha(_by(prev)[lid]) == A30.line_sha(_by(new)[lid])
    _p, _c2, _l2, new2, _i2 = run(doc(list(reversed(entries()))))
    assert [A30.line_sha(x) for x in new] == [A30.line_sha(x) for x in new2]


def test_census_counts_beside_never_summed():
    prev, _c, _l, new, _i = run()
    c0, c1 = A.census(prev), A.census(new)
    assert c1[COL]["bounded_low_m3"] == pytest.approx(c0[COL]["bounded_low_m3"] + 0.02551)
    assert c1[COL]["released_m3"] == c0[COL]["released_m3"] == 2.0
    assert c1[COL]["blank_with_beside"] == {"AT_LEAST": 1} and c0[COL]["blank_with_beside"] == {}
    assert c1[GB]["beside_sum_m3_run_record_only"]["AT_LEAST"] == pytest.approx(0.135481 + 0.4)
    assert c1[GB]["blank_with_beside"] == {"AT_LEAST": 2}               # restated, not a second figure
    assert c1[BM]["blank"] == 2 and c1[BM]["blank_with_beside"] == {"AT_LEAST": 1}
    assert c0[PP]["beside_sum_m3_run_record_only"]["AT_LEAST"] == pytest.approx(1.677887 + 1.6245)
    assert c1[PP]["beside_sum_m3_run_record_only"]["AT_LEAST"] == pytest.approx(1.677886 + 1.6245)


def test_write_files(tmp_path):
    prev = copy.deepcopy(LN)
    inp = A.load_inputs(doc(), PID)
    ch, log = A.changes_for(inp, prev)
    names, ident, led = A.write(tmp_path, prev, ch, log)
    assert "V3_0_73_BOQ_LINES.json" in names and len(led["rows"]) == 6
    assert ident["diff"]["vs_base"] == {"CHANGED": 6, "SAME": 5}
    run_doc = json.loads((tmp_path / "V3_0_73_RUN.json").read_text())
    assert sorted(run_doc["totals_moved_by_code"]) == [f"{COL}|m3"]
    assert run_doc["identity"]["conc_census_after"][COL]["bounded_low_m3"] == pytest.approx(0.30 + 0.28 + 0.02551)


# ---------------------------------------------------------------- adverse: NARROW
@pytest.mark.parametrize("terms, after, msg", [
    ({"areas_m2": ["0.10"], "h_lo_m": "3.25"}, {"low": "0.325001", "high": "0.45"}, "recomputed"),
    ({"areas_m2": ["0.10", "0.12"], "h_lo_m": "3.25"}, {"low": "0.325", "high": "0.46"}, "high end"),
    ({"areas_m2": ["1000"], "h_lo_m": "3.25"}, {"low": "3250", "high": "0.45"}, "unit slip"),
    ({"areas_m2": ["0.10"], "h_lo_m": "3250"}, {"low": "325", "high": "0.45"}, "unit slip"),
    ({"areas_m2": ["0.10"], "h_lo_m": "2.0"}, {"low": "0.2", "high": "0.45"}, "never widened"),
    ({"areas_m2": ["0.10"], "h_lo_m": "3.0"}, {"low": "0.3", "high": "0.45"}, "did not move"),
    ({"areas_m2": [], "h_lo_m": "3.0"}, {"low": "0.3", "high": "0.45"}, "areas_m2"),
])
def test_narrow_refusals(terms, after, msg):
    e = entries()
    e[0] = dict(e[0], terms=terms, after=after)
    with pytest.raises(A.InputsError, match=msg):
        A.load_inputs(doc(e), PID)


def test_range_from_zero_is_refused():
    e = entries()
    e[0] = dict(e[0], expect=dict(e[0]["expect"], low=0.0), terms={"areas_m2": ["0.10"], "h_lo_m": "0.0000001"},
                after={"low": "0.000000", "high": "0.45"})
    with pytest.raises(A.InputsError):
        A.load_inputs(doc(e), PID)


def test_narrow_on_stale_or_blank_line_refused():
    e = entries()
    e[0] = dict(e[0], expect=dict(e[0]["expect"], low=0.31))     # the candidate carries 0.30
    with pytest.raises(A.InputsError, match="stale binding"):
        run(doc(e))
    e = entries()
    e[0] = dict(e[0], line_id=ID["T1"])                          # a blank line is not narrowed
    del e[2]
    with pytest.raises(A.InputsError, match="stale binding"):
        run(doc(e))


# ---------------------------------------------------------------- adverse: AT_LEAST
@pytest.mark.parametrize("value", ["0", "-0.1", "250"])
def test_at_least_never_zero_or_slip(value):
    e = entries()
    e[2] = dict(e[2], beside={"value": value, "basis": "x"})
    with pytest.raises(A.InputsError, match="never 0"):
        A.load_inputs(doc(e), PID)


def test_at_least_is_never_a_range():
    e = entries()
    e[2] = dict(e[2], after={"low": "0.33", "high": "0.40"})
    with pytest.raises(A.InputsError, match="no range"):
        A.load_inputs(doc(e), PID)
    e = entries()
    e[2] = dict(e[2], expect=dict(e[2]["expect"], low=0.3, high=0.4))
    with pytest.raises(A.InputsError, match="beside a blank line"):
        A.load_inputs(doc(e), PID)


def test_undeclared_second_figure_refused():
    e = entries()
    e[3] = {k: v for k, v in e[3].items() if k != "restates"}
    with pytest.raises(A.InputsError, match="one live statement"):
        run(doc(e))


def test_restatement_must_name_the_live_figure():
    e = entries()
    e[3] = dict(e[3], restates={"record": V63, "value": "0.135400", "why": "x"})
    with pytest.raises(A.InputsError, match="one live statement"):
        run(doc(e))
    e = entries()
    e[2] = dict(e[2], restates={"record": V63, "value": "0.3", "why": "x"})   # T1 carries no figure
    with pytest.raises(A.InputsError, match="no figure is beside"):
        run(doc(e))


def test_same_figure_is_confirmed_never_restated():
    e = entries() + [_e("AT_LEAST", "G2", GB, beside={"value": "0.4", "basis": "same"})]
    with pytest.raises(A.InputsError, match="named twice"):
        A.load_inputs(doc(e), PID)
    with pytest.raises(A.InputsError, match="confirm it, never restate it"):
        run(doc(e, confirm=[]))


def test_confirm_wrong_value_refused():
    with pytest.raises(A.InputsError, match="does not carry"):
        run(doc(confirm=[{"line_id": ID["G2"], "kind": "AT_LEAST_M3", "value": 0.41}]))


# ---------------------------------------------------------------- adverse: NAMED / binding / scope
def test_named_never_removes_a_figure():
    e = entries() + [_e("NAMED", "B9", BM, why="no section printed")]
    with pytest.raises(A.InputsError, match="name never removes it"):
        run(doc(e))
    e = entries()
    e[4] = dict(e[4], beside={"value": "0.1", "basis": "x"})
    with pytest.raises(A.InputsError, match="carries no figure"):
        A.load_inputs(doc(e), PID)


def test_released_and_non_concrete_refused():
    e = entries() + [dict(_e("AT_LEAST", "R1", COL, beside={"value": "1", "basis": "x"}),
                          expect=dict(_x("R1", COL), **{"class": "RELEASED"}))]
    with pytest.raises(A.InputsError, match="HELD STR.CONC"):
        A.load_inputs(doc(e), PID)
    e = entries() + [dict(_e("NAMED", "PLASTER", "FIN.PLASTER", why="x"),
                          expect={"item_code": "FIN.PLASTER", "element_id": "R1:PLASTER", "unit": "m2",
                                  "class": "HELD"})]
    with pytest.raises(A.InputsError, match="HELD STR.CONC"):
        A.load_inputs(doc(e), PID)


def test_unknown_action_and_schema_and_project():
    e = entries()
    e[0] = dict(e[0], action="VALUE")
    with pytest.raises(A.InputsError, match="released m3 never"):
        A.load_inputs(doc(e), PID)
    with pytest.raises(A.InputsError, match="schema"):
        A.load_inputs(dict(doc(), schema="URBAN_V3072_INPUTS_V1"), PID)
    with pytest.raises(A.InputsError, match="for"):
        A.load_inputs(doc(), "OTHER")


def test_applied_twice_refused():
    _p, _c, _l, new, _i = run()
    with pytest.raises(A.InputsError, match="applied once"):
        A.changes_for(A.load_inputs(doc(), PID), new)


def test_check_concrete_catches_a_tampered_line():
    _p, _c, _l, new, _i = run()
    bad = copy.deepcopy(new)
    for ln in bad:
        if ln["line_id"] == ID["T1"]:
            ln["bounded_range"] = {"low": 0.33, "high": 0.5, "basis": "x"}
            ln["evidence_state"] = "BOUNDED_EXPOSURE"
    with pytest.raises(ValueError, match="not in its state"):
        A.check_concrete(bad)


def test_v3023_figure_restated_only_when_named():
    e = entries()
    e[5] = {k: v for k, v in e[5].items() if k != "restates"}
    with pytest.raises(A.InputsError, match="one live statement"):
        run(doc(e))
    e = entries() + [_e("AT_LEAST", "P2", PP, beside={"value": "1.6245", "basis": "same"})]
    with pytest.raises(A.InputsError, match="confirm it, never restate it"):
        run(doc(e, confirm=[{"line_id": ID["G2"], "kind": "AT_LEAST_M3", "value": 0.4}]))


def test_later_concrete_record_is_the_live_one():
    ln = copy.deepcopy(LN[[x["line_id"] for x in LN].index(ID["G1"])])
    ln["calculation"]["inputs"]["concrete_ledger_v3064"] = {"action": "LOWER_ONLY",
                                                            "beside": {"kind": "AT_LEAST_M3", "value": 0.1125}}
    assert A.figures_beside(ln) == [("concrete_ledger_v3064", "AT_LEAST_M3", 0.1125)]
    ln["calculation"]["inputs"]["concrete_ledger_v3070"] = {"action": "BOUND"}      # a later range clears it
    assert A.figures_beside(ln) == []
