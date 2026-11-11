"""T-704: ARCH_TAKEOFF_V3.0.71 (CONCRETE_GATE_B_V8, R-T704-1) on the hand-calculated NON-Alsenan villa K704 (own
figures, no drawing). Lintels are RC cast, depth from a printed schedule, schedule bearing b = 0.40 m.
  W1  w 1.20, 0.20 x 0.20, START column 0.55, END column 0.60 (both >= 0.40: CEILING), existence OPEN (head not
      printed): AT_MOST 0.04 x (1.20 + 0.55 + 0.60 = 2.35) = 0.094; if REQUIRED 0.04 x (1.20 + 2 x 0.40) = 0.080.
  D1  w 0.90, 0.15 x 0.20, START column 0.25 (deficit), END end of masonry 1.10 (MIN_BEARING): 0.03 x (0.90 + 0.25 +
      0.40 = 1.55) = 0.0465; if REQUIRED 0.03 x (0.90 + 0.40) = 0.039; CONDITIONAL EXCLUSION (beam BX may serve it).
  W2  w 1.00, 0.20 x 0.20, START column 0.50, END pier to W3 0.8004 (1 mm up 0.801, taken whole): 0.04 x 2.301 =
      0.09204; W3 w 1.00, START pier to W2 0.801, END column 0.45: 0.04 x 2.251 = 0.09004.
  W4  w 0.80, 0.15 x 0.25, ends column 0.40 / column 0.4011: 0.0375 x 1.6011 = 0.06004125 -> CEILING 0.060042
      (half-up would print 0.060041 < exact: refused, R-T696-1).
  A1  curved head: DATUM_NAMED, no figure.
  D9  REQUIRED, one end open: AT_LEAST 0.050 beside from V3.0.67 (LOWER_ONLY): confirmed, never restated.
Family AT_MOST: 0.094 + 0.0465 + 0.09204 + 0.09004 + 0.06004125 - 0.04 x 0.801 (pier once) = 0.35058125 -> 0.350582.
Every line stays HELD blank; no code total moves; a released lintel 0.072 and a plaster line stay byte-identical."""
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
from engine.source import arch_v3071 as A  # noqa: E402
from engine.source import boq_line as BL  # noqa: E402

PID, REV = "K704-SYNTHETIC", "f" * 64
LIN = "STR.CONC.LINTEL"


def _ln(code, eid, state, net=None, unit="m3", rec=None, floor="GF"):
    ln = BL.make_line(project_id=PID, revision_set_sha256=REV, item_code=code, unit=unit, evidence_state=state,
                      measured_net=net, gross=net, element_id=eid, floor=floor, room_id=None, bounded_range=None,
                      formula=f"synthetic {code} {eid}", rule_id="R-SYN", rule_version="1",
                      geometry_source="SYNTHETIC_FIXTURE", material_state="BY_SPEC", inputs=rec,
                      rfi={"question": "head not printed", "unlocks": eid} if state == "BLOCKED_RFI" else None,
                      notes="synthetic")
    return BL.validate(ln)


def _v53(o, decision="HELD"):
    return {"lintel_v3053": {"opening_id": o, "decision": decision}}


D9_REC = {"concrete_ledger_v3067": {"action": "LOWER_ONLY", "was": {"class": "HELD"},
                                    "beside": {"kind": "AT_LEAST_M3", "value": 0.05, "basis": "w + one bearing"},
                                    "existence": {"status": "ASSUMED - OWNER-APPROVED"},
                                    "assumption": {"rerun_trigger": "a head above 2.30 m"},
                                    "superseded": _v53("D9")}}


def base():
    return [
        _ln(LIN, "LINTEL:W1", "BLOCKED_RFI", rec=_v53("W1")),
        _ln(LIN, "LINTEL:D1", "BLOCKED_RFI", rec=_v53("D1")),
        _ln(LIN, "LINTEL:W2", "BLOCKED_RFI", rec=_v53("W2")),
        _ln(LIN, "LINTEL:W3", "BLOCKED_RFI", rec=_v53("W3")),
        _ln(LIN, "LINTEL:W4", "BLOCKED_RFI", rec=_v53("W4"), floor="1F"),
        _ln(LIN, "LINTEL:A1", "BLOCKED_RFI", rec=_v53("A1")),
        _ln(LIN, "LINTEL:D9", "BLOCKED_RFI", rec=copy.deepcopy(D9_REC)),
        _ln(LIN, "LINTEL:R1", "MEASURED", net=0.072, rec=_v53("R1", "REQUIRED")),
        _ln("FIN.PLASTER", "R1:PLASTER", "PROVISIONAL", net=44.31, unit="m2"),
    ]


LN = base()
ID = {ln["location"]["element_id"].split(":")[1]: ln["line_id"] for ln in LN if ln["item_code"] == LIN}
SRC = {"task": "T-P", "file": "research/k704/T-P.json", "sha256": "a" * 64, "merge_commit": "b" * 40,
       "checker_run": "checker T-P Gate A PASS"}


def _x(o):
    return {"item_code": LIN, "element_id": f"LINTEL:{o}", "unit": "m3", "class": "HELD", "low": None, "high": None}


def _t(side, stop, avail, taken, sid=None):
    return {"side": side, "stopper": stop, "stopper_id": sid, "available_m": avail, "taken_m": taken, "why": "hand"}


def _am(o, B, D, w, ends, length, hi, conv, lo=None, existence="OPEN", excl=None):
    e = {"action": "AT_MOST", "line_id": ID[o], "source_tasks": ["T-P"], "opening": o, "member": f"lintel {o}",
         "expect": _x(o), "existence": existence, "excluded_by": excl,
         "cause": {"class": "DESIGNER ITEM", "ref": "head not printed", "deciding_datum": f"the {o} head level"},
         "section": {"B_m": B, "D_m": D, "source": "schedule"}, "width_m": w, "end_terms": ends, "length_m": length,
         "convention": conv, "at_most_m3": hi, "basis": f"{o} hand", "if_required": lo}
    return e


def _lo(v, w, n):
    return {"value_m3": v, "width_m": w, "bounded_ends": n, "b_min_m": 0.40, "meaning": "if REQUIRED"}


def doc():
    return {"schema": "URBAN_V3071_INPUTS_V1", "project_id": PID, "sources": [dict(SRC)], "entries": [
        _am("W1", 0.20, 0.20, 1.20, [_t("START", "COLUMN", 0.55, 0.55), _t("END", "COLUMN", 0.60, 0.60)], 2.35,
            0.094, "CEILING", _lo(0.08, 1.20, 2)),
        _am("D1", 0.15, 0.20, 0.90, [_t("START", "COLUMN", 0.25, 0.25), _t("END", "END_OF_MASONRY", 1.10, 0.40)], 1.55,
            0.0465, "MIN_BEARING", _lo(0.039, 0.90, 1), "CONDITIONAL_EXCLUSION", "beam BX over the head"),
        _am("W2", 0.20, 0.20, 1.00, [_t("START", "COLUMN", 0.50, 0.50), _t("END", "OPENING", 0.801, 0.801, "W3")],
            2.301, 0.09204, "CEILING"),
        _am("W3", 0.20, 0.20, 1.00, [_t("START", "OPENING", 0.801, 0.801, "W2"), _t("END", "COLUMN", 0.45, 0.45)],
            2.251, 0.09004, "CEILING"),
        _am("W4", 0.15, 0.25, 0.80, [_t("START", "COLUMN", 0.40, 0.40), _t("END", "COLUMN", 0.4011, 0.4011)], 1.6011,
            0.060042, "CEILING"),
        {"action": "DATUM_NAMED", "line_id": ID["A1"], "source_tasks": ["T-P"], "opening": "A1", "member": "arch A1",
         "expect": _x("A1"), "existence": "OPEN", "excluded_by": None,
         "cause": {"class": "DESIGNER ITEM", "ref": "arch not dimensioned", "deciding_datum": "crown level"},
         "why_no_bound": "curved head: never a straight-lintel m3", "basis": "A1", "if_required": None}],
        "confirm": [{"line_id": ID["D9"], "opening": "D9", "kind": "AT_LEAST_M3", "value": 0.05,
                     "carried_by": "V3.0.67 LOWER_ONLY"}],
        "family": {"at_most_m3": 0.350582, "lines": 5,
                   "shared_piers": [{"lines": [ID["W2"], ID["W3"]], "pier_m": 0.801, "double_counted_m3": 0.03204}]}}


def run(d=None, lines=None):
    lines = copy.deepcopy(LN if lines is None else lines)
    inp = A.load_inputs(d or doc(), PID)
    ch, log = A.changes_for(inp, lines)
    new, ident = A.integrate(lines, ch)
    return lines, new, ident, ch, log


def _by(lines, o):
    return next(x for x in lines if x["location"]["element_id"] == f"LINTEL:{o}")


def _rec(ln):
    return ln["calculation"]["inputs"][A.REC_KEY]


# ------------------------------------------------------------------------------------------------ normal
def test_normal_hand_figures():
    _, new, ident, ch, log = run()
    want = {"W1": (0.094, 0.08), "D1": (0.0465, 0.039), "W2": (0.09204, None), "W3": (0.09004, None),
            "W4": (0.060042, None)}
    for o, (hi, lo) in want.items():
        r = _rec(_by(new, o))
        assert r["action"] == "AT_MOST" and r["beside"]["value"] == hi, o
        assert (r["if_required"] or {}).get("value_m3") == lo, o
    assert _rec(_by(new, "A1"))["beside"] is None
    assert ident["lintels"] == {"AT_MOST": 5, "DATUM_NAMED": 1}
    assert log["family_at_most"]["at_most_m3"] == 0.350582
    assert [c["line_id"] for c in log["confirmed_unchanged"]] == [ID["D9"]]
    assert ident["replaced"] == 6 and ident["added"] == 0


def test_lines_stay_held_blank_and_no_total_moves():
    old, new, ident, ch, log = run()
    for o in ("W1", "D1", "W2", "W3", "W4", "A1"):
        ln = _by(new, o)
        assert ln["evidence_state"] == "BLOCKED_RFI" and ln["measured_net"] is None and ln["bounded_range"] is None
        assert A.line_class(ln) == "HELD" and ln["rfi"]["question"]
        assert not A.A3043.FORMULA_END_RE.search(ln["calculation"]["formula"])
    assert A304.code_totals(old) == A304.code_totals(new)
    assert A.check_totals(A304.code_totals(old), A304.code_totals(new), ch) == {}


def test_outside_lines_byte_identical():
    old, new, *_ = run()
    for o in ("D9", "R1"):
        assert A30.line_sha(_by(old, o)) == A30.line_sha(_by(new, o))
    pl = [x for x in new if x["item_code"] == "FIN.PLASTER"][0]
    assert A30.line_sha(pl) == A30.line_sha([x for x in old if x["item_code"] == "FIN.PLASTER"][0])


def test_conditional_exclusion_and_question():
    _, new, *_ = run()
    d1 = _by(new, "D1")
    assert "beam BX" in d1["rfi"]["question"] and _rec(d1)["excluded_by"] == "beam BX over the head"
    assert "if REQUIRED (never a bound)" in d1["calculation"]["formula"]


def test_directed_rounding_ceiling():
    e = doc()["entries"][4]
    exact, hi, length = A.at_most(e)
    assert str(exact) == "0.06004125" and str(hi) == "0.060042"


def test_mirror_order():
    d = doc()
    d["entries"] = list(reversed(d["entries"]))
    for e in d["entries"]:
        if e.get("end_terms"):
            e["end_terms"] = list(reversed(e["end_terms"]))
    _, new, ident, *_ = run(d)
    assert _rec(_by(new, "W1"))["beside"]["value"] == 0.094 and ident["lintels"]["AT_MOST"] == 5


def test_write_files(tmp_path):
    old, new, ident, ch, log = run()
    names, ident2, led = A.write(tmp_path, old, ch, log)
    assert "V3_0_71_BOQ_LINES.json" in names and led["integration_package"] is True
    rj = json.loads((tmp_path / "V3_0_71_RUN.json").read_text(encoding="utf-8"))
    assert rj["totals_moved_by_code"] == {} and rj["released_default"] is False
    assert ident2["diff"]["vs_base"].get("SAME") == len(old) - 6


# ------------------------------------------------------------------------------------------------ adverse
def _bad(mut, msg):
    d = doc()
    mut(d)
    with pytest.raises(A.InputsError, match=msg):
        run(d)


def test_adverse_half_up_rounded_ledger_refused():
    _bad(lambda d: d["entries"][4].update(at_most_m3=0.060041), "not the recomputed")


def test_adverse_taken_beyond_available():
    _bad(lambda d: d["entries"][0]["end_terms"][0].update(taken_m=0.60, available_m=0.55), "beyond the drawn")


def test_adverse_open_end_no_at_most():
    _bad(lambda d: d["entries"][0]["end_terms"][1].update(stopper="CROSSING_WALL"), "not recorded")


def test_adverse_one_end_only():
    _bad(lambda d: d["entries"][0].update(end_terms=d["entries"][0]["end_terms"][:1]), "two ends")


def test_adverse_section_in_cm():
    _bad(lambda d: d["entries"][0]["section"].update(B_m=20), "not in metres")


def test_adverse_missing_depth_never_zero():
    _bad(lambda d: d["entries"][0]["section"].update(D_m=None), "never 0")


def test_adverse_length_not_the_terms():
    _bad(lambda d: d["entries"][0].update(length_m=2.40), "length")


def test_adverse_conditional_lo_above_at_most():
    def m(d):
        d["entries"][4]["if_required"] = _lo(0.0675, 1.00, 2)      # 0.0375 x 1.80 > 0.060042
    _bad(m, "above the AT_MOST")


def test_adverse_required_existence_refused():
    _bad(lambda d: d["entries"][0].update(existence="REQUIRED"), "existence")


def test_adverse_exclusion_without_member():
    _bad(lambda d: d["entries"][1].update(excluded_by=None), "names the member")


def test_adverse_datum_named_with_figure():
    _bad(lambda d: d["entries"][5].update(at_most_m3=0.05), "no one-sided figure")


def test_adverse_family_pier_not_once():
    _bad(lambda d: d["family"].update(at_most_m3=0.382622), "family AT_MOST")


def test_adverse_family_pier_not_taken_whole():
    def m(d):
        d["family"]["shared_piers"][0]["pier_m"] = 0.70
    _bad(m, "whole")


def test_adverse_bounded_line_not_this_piece():
    lines = copy.deepcopy(LN)
    w1 = _by(lines, "W1")
    w1.update(evidence_state="BOUNDED_EXPOSURE", bounded_range={"low": 0.08, "high": 0.094, "basis": "x"})
    with pytest.raises(A.InputsError, match="stale binding"):
        run(lines=lines)


def test_adverse_line_with_a_figure_beside_already():
    lines = copy.deepcopy(LN)
    _by(lines, "W1")["calculation"]["inputs"]["concrete_ledger_v3067"] = copy.deepcopy(D9_REC["concrete_ledger_v3067"])
    with pytest.raises(A.InputsError, match="already carries a figure"):
        run(lines=lines)


def test_adverse_confirm_stale():
    _bad(lambda d: d["confirm"][0].update(value=0.06), "stale binding")


def test_adverse_applied_twice():
    old, new, ident, ch, log = run()
    with pytest.raises(A.InputsError, match="applied once"):
        A.changes_for(A.load_inputs(doc(), PID), new)


def test_adverse_line_named_twice():
    _bad(lambda d: d["entries"].append(copy.deepcopy(d["entries"][0])), "named twice")


def test_adverse_other_project():
    with pytest.raises(A.InputsError, match="the run is"):
        A.load_inputs(doc(), "OTHER")


def test_adverse_not_a_lintel_code():
    _bad(lambda d: d["entries"][0]["expect"].update(item_code="STR.CONC.BEAM"), "HELD blank")


def test_check_lintels_refuses_a_valued_restated_line():
    old, new, *_ = run()
    t = copy.deepcopy(new)
    w1 = _by(t, "W1")
    w1.update(evidence_state="MEASURED", measured_net=0.094, rfi=None)
    with pytest.raises(ValueError, match="HELD blank lintel"):
        A.check_lintels(t)


def test_check_totals_refuses_a_moved_total():
    t0 = {"STR.CONC.LINTEL|m3": {"released": 0.072}}
    with pytest.raises(ValueError, match="never summed"):
        A.check_totals(t0, {"STR.CONC.LINTEL|m3": {"released": 0.166}}, [])
