"""T-717: ARCH_TAKEOFF_V3.0.74 (FINISH_GATE_B_V2, R-T717-1) on the hand-calculated NON-Alsenan villa F717 (own figures,
no drawing; every figure below by hand):
  A2   annex room plaster, HELD 30.000 .. 32.000 m2 (a narrow range inside a datum bound): the merged ledger's datum bound
       25.000 .. 36.000 with a named deduction correction F-X (window 1.50 x 2.20 = 3.300 vs 3.290 in the ledger: both
       ends -0.010) -> 24.990 .. 35.990 (widened: ENGINE_WRONG, bound too narrow; never a value).
  W5   wet-room band, HELD 2.000 .. 3.000: a beam fills 1.00 m of the band and a sunken panel holds 0 .. full: ledger
       0.500 .. 2.800.
  D1   door return plaster RELEASED 0.800 m2 (0.20 x (2 x 2.20 + 0.90) = 1.060? no: 0.15 x (2 x 2.20 + 0.93) = 0.7995 ->
       the fixture states 0.800): return paint HELD 0 .. 0.800 (frame-covered depth not printed).
  D2   door return between two wet rooms, plaster RELEASED 0.780: paint HELD 0 .. 0.780 with the NOT_ESTABLISHED flag.
  A9   arch reveal plaster HELD blank: return paint HELD blank (never 0).
  H8   stairwell room: plaster HELD 100 .. 120, paint HELD 80 .. 95; the wall runs on through a slab-free well:
       plaster band run 2.50 m x (4.40 - 4.20) = 0.500, + returns 0.10 lm x 0.20 = 0.020 -> 0.500 .. 0.520;
       paint band 2.50 x (4.40 - 3.60) = 2.000, - landing <= 0.040 -> 1.960 .. 2.000 + 0.10 x 0.80 = 2.080.
  R1   released plaster 44.310 and paint 40.000 and a released concrete column 2.000 m3: byte-identical.
Totals by hand: FIN.PLASTER held_low (24.99 - 30) + (0.5 - 2) + 0.5 = -6.010, held_high (35.99 - 32) + (2.8 - 3) +
0.52 = +4.310, lines +1, bounded +1; FIN.PAINT lines +4, bounded +3 (0 .. 0.8, 0 .. 0.78, band), blocked +1,
held_low +1.960, held_high 0.8 + 0.78 + 2.08 = +3.660; released never moves.
Adverse: stale binding, a return low above 0, a return high not the face, a figure on a blank face, a band in mm, an
inverted band, a band figure off its terms, a VERIFIED / owner-approved status, applied twice, two returns on one face,
a non-plaster restatement, a released host restated, a correction with no finding or a unit slip, mirror order."""
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
from engine.source import arch_v3074 as A  # noqa: E402
from engine.source import boq_line as BL  # noqa: E402

PID, REV = "F717-SYNTHETIC", "f" * 64
PL, PA = "FIN.PLASTER", "FIN.PAINT"


def _ln(code, eid, state, net=None, unit="m2", rng=None, floor="GF"):
    ln = BL.make_line(project_id=PID, revision_set_sha256=REV, item_code=code, unit=unit, evidence_state=state,
                      measured_net=net, gross=net, element_id=eid, floor=floor, room_id=None,
                      bounded_range=None if rng is None else {"low": rng[0], "high": rng[1], "basis": "synthetic"},
                      formula=f"synthetic {code} {eid}", rule_id="R-SYN", rule_version="1",
                      geometry_source="SYNTHETIC_FIXTURE", material_state="BY_SPEC",
                      rfi={"question": "datum not printed", "unlocks": eid} if state in ("BLOCKED_RFI",
                                                                                         "BOUNDED_EXPOSURE") else None,
                      notes="synthetic")
    return BL.validate(ln)


def base():
    return [
        _ln(PL, "HL:WALL_FINISH:GF_A2:PLASTER", "BOUNDED_EXPOSURE", rng=(30.0, 32.0)),
        _ln(PL, "GF-W5:WET_BAND", "BOUNDED_EXPOSURE", rng=(2.0, 3.0)),
        _ln(PL, "GF-OPENING-D1:door jambs and head", "MEASURED", net=0.8),
        _ln(PL, "GF-OPENING-D2:door jambs and head", "MEASURED", net=0.78),
        _ln(PL, "GF-REVEAL-A9:THROUGH:JAMBS_HEAD:HELD", "BLOCKED_RFI"),
        _ln(PL, "HL:WALL_FINISH:GF_H8:PLASTER", "BOUNDED_EXPOSURE", rng=(100.0, 120.0)),
        _ln(PA, "HL:WALL_FINISH:GF_H8:PAINT", "BOUNDED_EXPOSURE", rng=(80.0, 95.0)),
        _ln(PL, "R1:PLASTER", "PROVISIONAL", net=44.31),
        _ln(PA, "R1:PAINT", "PROVISIONAL", net=40.0),
        _ln("STR.CONC.COLUMN", "COL:R1", "MEASURED", net=2.0, unit="m3"),
    ]


LN = base()
ID = {ln["location"]["element_id"]: ln["line_id"] for ln in LN}
SRC = [{"task": t, "file": f"research/f717/{t}.json", "sha256": "a" * 64, "merge_commit": "b" * 40,
        "checker_run": f"checker {t} Gate A PASS"} for t in ("T-P", "T-Q", "T-M")]
HELD = {"status": "HELD", "basis": "synthetic bound"}


def _restate(eid, before, ledger, cor=None):
    return {"line_id": ID[eid], "item_code": PL, "action": "BOUND",
            "expect": {"class": "HELD", "low": before[0], "high": before[1], "element_id": eid},
            "ledger_after": list(ledger), "correction": cor,
            "after": dict(zip(("low", "high"), A.corrected(ledger, cor))), "basis": "synthetic ledger bound",
            "status": dict(HELD), "still_open": "datum held", "source_tasks": ["T-P", "T-M"], "map_row": f"T-P:{eid}"}


def _ret(face, value, flag=None):
    blank = value is None
    return {"host_line_id": ID[face], "face_id": face, "element_id": face + ":RETURN_PAINT",
            "expect_host": {"item_code": PL, "class": "HELD" if blank else "RELEASED", "value": value},
            "after": {"kind": "BLANK"} if blank else {"kind": "BOUND", "low": 0.0, "high": value}, "flag": flag,
            "basis": "return paint per face", "status": dict(HELD),
            "still_open": "frame-covered depth not printed", "source_tasks": ["T-Q", "T-M"], "map_row": f"T-Q:{face}"}


def _band(code, levels, ded, lo, hi, run="2.50", ret="0.10"):
    host = "HL:WALL_FINISH:GF_H8:" + ("PLASTER" if code == PL else "PAINT")
    rng = (100.0, 120.0) if code == PL else (80.0, 95.0)
    return {"host_line_id": ID[host], "expect_host": {"item_code": code, "class": "HELD", "low": rng[0],
                                                      "high": rng[1], "element_id": host},
            "item_code": code, "element_id": f"{code.split('.')[1]}-BAND@{ID[host]}", "run_m": run,
            "levels_m": list(levels), "returns_lm": ret, "low_deduction_max_m2": ded, "low": lo, "high": hi,
            "status": dict(HELD), "still_open": "beam faces held", "source_tasks": ["T-Q", "T-M"],
            "map_row": f"T-Q:band:{code}"}


def doc():
    return {"schema": A.INPUTS_SCHEMA, "project_id": PID, "sources": copy.deepcopy(SRC),
            "restate": [_restate("HL:WALL_FINISH:GF_A2:PLASTER", (30.0, 32.0), (25.0, 36.0),
                                 {"finding": "F-X", "delta_m2": -0.01, "why": "window 3.300 vs 3.290"}),
                        _restate("GF-W5:WET_BAND", (2.0, 3.0), (0.5, 2.8))],
            "returns": [_ret("GF-OPENING-D1:door jambs and head", 0.8),
                        _ret("GF-OPENING-D2:door jambs and head", 0.78, "NOT_ESTABLISHED (wet rooms both sides)"),
                        _ret("GF-REVEAL-A9:THROUGH:JAMBS_HEAD:HELD", None, "HELD by name (plaster return blank)")],
            "bands": [_band(PL, ("4.20", "4.40"), None, 0.5, 0.52),
                      _band(PA, ("3.60", "4.40"), "0.04", 1.96, 2.08)]}


def run(d=None, lines=None):
    lines = copy.deepcopy(LN) if lines is None else lines
    inp = A.load_inputs(d or doc(), PID)
    ch, log = A.changes_for(inp, lines)
    new, ident = A.integrate(lines, ch)
    return lines, ch, log, new, ident


def _by(lines):
    return {ln["location"]["element_id"]: ln for ln in lines}


# ------------------------------------------------------------------------------------------------ normal
def test_restated_bounds_by_hand():
    _, ch, log, new, ident = run()
    b = _by(new)
    assert A30._qty(b["HL:WALL_FINISH:GF_A2:PLASTER"])["low"] == 24.99
    assert A30._qty(b["HL:WALL_FINISH:GF_A2:PLASTER"])["high"] == 35.99
    assert b["HL:WALL_FINISH:GF_A2:PLASTER"]["measured_net"] is None          # a downgrade never keeps a value
    q = A30._qty(b["GF-W5:WET_BAND"])
    assert (q["low"], q["high"]) == (0.5, 2.8)
    assert log["restated"] == 2 and ident["replaced"] == 2 and ident["added"] == 5


def test_return_paint_lines():
    _, ch, log, new, ident = run()
    b = _by(new)
    r1 = b["GF-OPENING-D1:door jambs and head:RETURN_PAINT"]
    assert r1["item_code"] == PA and A30._qty(r1)["low"] == 0.0 and A30._qty(r1)["high"] == 0.8
    assert A.line_class(r1) == "HELD" and r1["measured_net"] is None
    r2 = b["GF-OPENING-D2:door jambs and head:RETURN_PAINT"]
    assert "NOT_ESTABLISHED" in r2["calculation"]["inputs"][A.REC_KEY]["flag"]
    r9 = b["GF-REVEAL-A9:THROUGH:JAMBS_HEAD:HELD:RETURN_PAINT"]
    assert r9["evidence_state"] == "BLOCKED_RFI" and A30._qty(r9)["low"] is None and r9["measured_net"] is None
    assert log["returns"] == {"BOUND": 2, "BLANK": 1, "flagged": 2}
    assert ident["finishes"]["return_bound"] == 2 and ident["finishes"]["return_blank"] == 1


def test_band_by_hand():
    assert A.band_figure({"element_id": "x", "run_m": "2.50", "levels_m": ["4.20", "4.40"], "returns_lm": "0.10"}) \
        == (0.5, 0.52)
    assert A.band_figure({"element_id": "x", "run_m": "2.50", "levels_m": ["3.60", "4.40"], "returns_lm": "0.10",
                          "low_deduction_max_m2": "0.04"}) == (1.96, 2.08)
    _, _, _, new, ident = run()
    b = [x for x in new if x["location"]["element_id"].startswith("PAINT-BAND@")][0]
    assert (A30._qty(b)["low"], A30._qty(b)["high"]) == (1.96, 2.08) and ident["finishes"]["band"] == 2


def test_totals_by_hand_and_released_unchanged():
    lines, ch, _, new, _ = run()
    t0, t1 = A304.code_totals(lines), A304.code_totals(new)
    moved = A.check_totals(t0, t1, ch)
    p0, p1 = t0["FIN.PLASTER|m2"], t1["FIN.PLASTER|m2"]
    assert round(p1["held_low"] - p0["held_low"], 6) == -6.01 and round(p1["held_high"] - p0["held_high"], 6) == 4.31
    assert p1["lines"] - p0["lines"] == 1 and p1["bounded_lines"] - p0["bounded_lines"] == 1
    a0, a1 = t0["FIN.PAINT|m2"], t1["FIN.PAINT|m2"]
    assert a1["lines"] - a0["lines"] == 4 and a1["bounded_lines"] - a0["bounded_lines"] == 3
    assert a1["blocked_lines"] - a0["blocked_lines"] == 1
    assert round(a1["held_low"] - a0["held_low"], 6) == 1.96 and round(a1["held_high"] - a0["held_high"], 6) == 3.66
    assert p1["released"] == p0["released"] and a1["released"] == a0["released"]
    assert set(moved) == {"FIN.PLASTER|m2", "FIN.PAINT|m2"}


def test_outside_lines_byte_identical():
    lines, ch, _, new, ident = run()
    named = {c["after"]["line_id"] for c in ch}
    for ln in lines:
        if ln["line_id"] not in named:
            assert A30.line_sha(ln) == A30.line_sha(_by(new)[ln["location"]["element_id"]])
    assert ident["outside_rows"] == len(lines) - 2


def test_mirror_order_same_result():
    d = doc()
    for k in ("restate", "returns", "bands"):
        d[k] = list(reversed(d[k]))
    _, _, _, new1, _ = run()
    _, _, _, new2, _ = run(d)
    assert {A30.line_sha(x) for x in new1} == {A30.line_sha(x) for x in new2}


def test_census_and_write(tmp_path):
    lines = copy.deepcopy(LN)
    inp = A.load_inputs(doc(), PID)
    ch, log = A.changes_for(inp, lines)
    names, ident, led = A.write(tmp_path, lines, ch, log)
    assert "V3_0_74_BOQ_LINES.json" in names and led["integration_package"] is True
    c0, c1 = ident["fin_census_before"]["FIN.PAINT"], ident["fin_census_after"]["FIN.PAINT"]
    assert c1["bounded"] - c0["bounded"] == 3 and c1["blank"] - c0["blank"] == 1 and c1["released"] == c0["released"]
    assert ident["diff"]["vs_base"] == {"SAME": 8, "CHANGED": 2, "ADDED": 5}


# ------------------------------------------------------------------------------------------------ adverse
def _bad(mut, match):
    d = doc()
    mut(d)
    with pytest.raises((A.InputsError, ValueError), match=match):
        run(d)


def test_adverse_stale_binding():
    _bad(lambda d: d["restate"][0]["expect"].update(low=29.0), "started from")


def test_adverse_return_low_above_zero():
    _bad(lambda d: d["returns"][0]["after"].update(low=0.1), "frame-covered extreme 0")


def test_adverse_return_high_not_face():
    _bad(lambda d: (d["returns"][0]["after"].update(high=0.9), d["returns"][0]["expect_host"].update(value=0.9)),
         "the ledger read 0.9")


def test_adverse_figure_on_blank_face():
    def m(d):
        d["returns"][2]["after"] = {"kind": "BOUND", "low": 0.0, "high": 0.5}
        d["returns"][2]["expect_host"]["value"] = 0.5
    _bad(m, "the ledger read")


def test_adverse_band_in_mm():
    _bad(lambda d: d["bands"][0].update(run_m="2500"), "unit slip")


def test_adverse_band_inverted():
    _bad(lambda d: d["bands"][0].update(levels_m=["4.40", "4.20"]), "not above")


def test_adverse_band_figure_off_terms():
    _bad(lambda d: d["bands"][1].update(high=2.2), "not the recomputed")


def test_adverse_verified_status():
    _bad(lambda d: d["restate"][0]["status"].update(status="VERIFIED"), "evidence status")
    _bad(lambda d: d["returns"][0]["status"].update(status="ASSUMED - OWNER-APPROVED"), "evidence status")


def test_adverse_applied_twice():
    _, _, _, new, _ = run()
    with pytest.raises(A.InputsError, match="applied once"):
        A.changes_for(A.load_inputs(doc(), PID), new)


def test_adverse_two_returns_one_face():
    _bad(lambda d: d["returns"].append(copy.deepcopy(d["returns"][0])), "two return-paint lines")


def test_adverse_non_plaster_restatement():
    _bad(lambda d: d["restate"][0].update(item_code=PA), "not FIN.PLASTER")


def test_adverse_released_host_restated():
    def m(d):
        d["restate"][0]["line_id"] = ID["R1:PLASTER"]
        d["restate"][0]["expect"].update(element_id="R1:PLASTER")
    _bad(m, "not a HELD")


def test_adverse_correction_without_finding_or_slip():
    _bad(lambda d: d["restate"][0]["correction"].update(finding=""), "names its finding")
    _bad(lambda d: d["restate"][0]["correction"].update(delta_m2=-10.824), "unit slip")


def test_adverse_after_not_ledger_plus_correction():
    _bad(lambda d: d["restate"][0].update(after={"low": 25.0, "high": 36.0}), "not the ledger bound")


def test_adverse_band_on_wrong_code_host():
    _bad(lambda d: d["bands"][0]["expect_host"].update(item_code=PA), "own code")


def test_adverse_stale_host_missing():
    _bad(lambda d: d["returns"][0].update(host_line_id="L-" + "0" * 20), "not a candidate line")


def test_adverse_shuffled_line_order_still_identical():
    lines = copy.deepcopy(LN)
    random.Random(7).shuffle(lines)
    _, ch, _, new, ident = run(lines=lines)
    assert ident["replaced"] == 2 and ident["added"] == 5
