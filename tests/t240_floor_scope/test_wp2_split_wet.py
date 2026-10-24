"""T-240 WP2: ARCH_TAKEOFF_V3.0.13 kinds TO_WET and NO_OPENING_SPLIT (+ TO_THRESHOLD on ground-floor exterior sills).
Synthetic data only (no client drawing).

VILLA K-240 ground floor (not the development villa), hand values:
  open room GF-ROPEN (dining / living / scullery, one face) porcelain 60.000 m2; scullery cell GF-RSCU porcelain 3.000.
  The scullery is WET by owner decision K-37 A within its printed box 2.50 x 4.00 = 10.000 m2. Inside the box (as the
  checker measured them): GF-RSCU 3.000 (whole), the strip part 2.50 x 0.20 = 0.500, a column notch 0.100, a doorway zone
  0.900 (RFI, stays as carried) -> the open room's part = 10.000 - 4.500 = 5.500 m2 -> wet; dry rest 54.500.
  'strip' GF OP-061: 10.00 x 0.20 = 2.000 m2 porcelain (+ a threshold twin BLOCKED): an edge line across an open zone, no
      opening. West to east: side passage 1.30 (0.260, the piece the passage line adds as missing), its east wall 0.20
      (0.040, no floor), scullery 2.50 (0.500 wet), garden band 6.00 (1.200 HELD with the band).
  side passage: drawn 1.30 x 5.00 = 6.500 m2 exterior (decision K-67 A); space pieces 2.400 + 3.840; missing 0.260 carried
      by the OP-061 strip -> one outdoor line 6.500.
  exterior sill GF OP-062 1.20 x 0.20 = 0.240 porcelain -> ARCH.THRESHOLD HELD 0.240.
  Internal floor line: before 60 + 3 + 2 + 0.24 = 65.240; after 54.5 + 5.5 + 3.0 + 0.5 = 63.500 (-1.740 = -2.000 + 0.500
  - 0.240); wet 9.000 of it (5.5 + 3.0 + 0.5); held with the band 1.200; thresholds 0.240; outdoor 6.500.
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v3013 as A                      # noqa: E402
from engine.source import boq_line as BL                       # noqa: E402

AP = pytest.approx
PID = "synthetic-v3013-villa-k240-gf"
DOCS = [{"file": "K-ARCH.dxf", "sha256": "4" * 64}]
POR, WET, SP, THR = "FIN.FLOOR.PORCELAIN", "FIN.FLOOR.WET_TILE", "ARCH.SPACE", "ARCH.THRESHOLD"
DEC = "owner decision K-37 A (scullery wet within its printed box)"


def line(eid, item, floor, q=1.0, ev="SOURCE_DERIVED", unit="m2"):
    held = ev in ("BOUNDED_EXPOSURE", "BLOCKED_RFI")
    return BL.make_line(project_id=PID, revision_set_sha256="0" * 64, item_code=item, unit=unit, evidence_state=ev,
                        measured_net=None if held else q, element_id=eid, floor=floor, physical_element=eid,
                        formula="route", documents=DOCS, rule_id="SV", rule_version="1",
                        rfi={"question": "q", "unlocks": eid} if held else None)


def lines():
    return [line("GF-ROPEN:floor", POR, "GF", 60.0, "PROVISIONAL"),
            line("GF-RSCU:floor", POR, "GF", 3.0, "PROVISIONAL"),
            line("GF-STRIP-OP-061:doorway strip", POR, "GF", 2.0),
            line("GF-STRIP-OP-061:unattributed strip", THR, "GF", ev="BLOCKED_RFI"),
            line("GF-RSPA:space", SP, "GF", 2.4, "PROVISIONAL"),
            line("GF-RSPB:space", SP, "GF", 3.84, "PROVISIONAL"),
            line("GF-STRIP-OP-062:doorway strip", POR, "GF", 0.24, "PROVISIONAL"),
            line("GF-RBATH:floor", WET, "GF", 4.2)]


def src():
    return {"file": "research/T-FT/LEDGER.csv", "sha256": "f" * 64, "task": "T-FT", "merge_commit": "def5678",
            "checker_run": "verifier run for T-FT"}


def ref(eid, item, carried, why="moves"):
    return {"item_code": item, "floor": "GF", "element_id": eid, "unit": "m2", "carried": carried, "why": why}


def records():
    return [
        {"id": "PASSAGE", "kind": "TO_OUTDOOR", "floor": "GF", "dims": [[1.30, 5.00]], "area_m2": 6.5,
         "decision": "owner decision K-67 A", "material_status": "ASSUMED - OWNER-APPROVED",
         "material_source": "owner sides rule", "area_status": "VERIFIED", "evidence": "nothing across the mouth",
         "drawing_reference": "walls W1..W5",
         "lines": [ref("GF-RSPA:space", SP, 2.4), ref("GF-RSPB:space", SP, 3.84)],
         "missing": {"m2": 0.26, "carried_by": "EDGE", "why": "carried inside the OP-061 strip"}},
        {"id": "SILL", "kind": "TO_THRESHOLD", "floor": "GF", "opening": "OP-062", "class": "EXTERIOR_SILL",
         "rule": "UP-THR-001", "dims": [[1.20, 0.20]], "area_m2": 0.24, "evidence": "one side exterior",
         "drawing_reference": "jambs J7 / J8", "line": ref("GF-STRIP-OP-062:doorway strip", POR, 0.24, "sill")},
        {"id": "EDGE", "kind": "NO_OPENING_SPLIT", "floor": "GF", "evidence": "edge line across an open zone",
         "drawing_reference": "lines E1 / E2",
         "line": ref("GF-STRIP-OP-061:doorway strip", POR, 2.0, "an edge line carried as a doorway strip"),
         "twin": ref("GF-STRIP-OP-061:unattributed strip", THR, None, "its threshold twin"),
         "parts": [{"part": "passage", "dims": [[1.30, 0.20]], "area_m2": 0.26, "to": "COUNTED_IN",
                    "record": "PASSAGE"},
                   {"part": "wall", "dims": [[0.20, 0.20]], "area_m2": 0.04, "to": "NO_FLOOR", "why": "wall body"},
                   {"part": "scullery", "dims": [[2.50, 0.20]], "area_m2": 0.5, "to": "TO_WET", "decision": DEC},
                   {"part": "band", "dims": [[6.00, 0.20]], "area_m2": 1.2, "to": "HELD_WITH",
                    "held_with": "the garden band (HELD)", "why": "inside the printed band"}]},
        {"id": "SCU-WHOLE", "kind": "TO_WET", "floor": "GF", "decision": DEC, "whole": True, "move_m2": 3.0,
         "area_status": "DRAWING-CONFIRMED", "evidence": "inside the box", "drawing_reference": "box 250 / 400",
         "line": ref("GF-RSCU:floor", POR, 3.0, "a scullery cell carried as dry porcelain")},
        {"id": "OPEN-PART", "kind": "TO_WET", "floor": "GF", "decision": DEC, "move_m2": 5.5,
         "area_status": "DRAWING-CONFIRMED", "evidence": "the open face clipped to the box",
         "drawing_reference": "box 250 / 400",
         "closure": {"box_m2": 10.0, "terms": {"GF-RSCU": 3.0, "strip part": 0.5, "column": 0.1, "doorway zone": 0.9}},
         "line": ref("GF-ROPEN:floor", POR, 60.0, "the scullery part of the open face")}]


def inputs(recs=None, declared=None):
    pc = {"piece": "FLOOR_SCOPE", "source": src(), "records": recs if recs is not None else records()}
    if declared is not None:
        pc["declared"] = declared
    return {"schema": A.INPUTS_SCHEMA, "project": PID, "pieces": [pc]}


def run(recs=None, ls=None, declared=None):
    ls = ls if ls is not None else lines()
    inp = A.load_inputs(inputs(recs, declared), PID)
    ch, logs = A.changes_for(inp, ls)
    out, ident = A.integrate(ls, ch)
    return ls, out, ch, logs, ident


def by_eid(ls):
    return {(ln["location"]["element_id"], ln["item_code"]): ln for ln in ls}


# ------------------------------------------------------------------------------------------------ normal case
def test_hand_values():
    ls, out, ch, logs, ident = run(declared={"floor_internal_in_m2": 0.5, "floor_internal_out_m2": 2.24,
                                             "floor_internal_delta_m2": -1.74, "dry_to_wet_m2": 8.5,
                                             "held_with_m2": 1.2, "counted_in_m2": 0.26, "no_floor_m2": 0.04,
                                             "threshold_m2": 0.24, "outdoor_m2": 6.5})
    b = by_eid(out)
    assert b[("GF-ROPEN:floor", POR)]["measured_net"] == AP(54.5)
    assert b[("GF-ROPEN:floor", POR)]["evidence_state"] == "PROVISIONAL"          # its evidence is not raised
    assert b[("GF-RSCU:floor", POR)]["evidence_state"] == "NOT_APPLICABLE_WITH_EVIDENCE"
    assert b[("HL:FLOOR_SCOPE:WET:GF:SCU-WHOLE", WET)]["measured_net"] == AP(3.0)
    assert b[("HL:FLOOR_SCOPE:WET:GF:OPEN-PART", WET)]["measured_net"] == AP(5.5)
    assert b[("HL:FLOOR_SCOPE:TO_WET:GF:EDGE:scullery", WET)]["measured_net"] == AP(0.5)
    held = b[("HL:FLOOR_SCOPE:HELD_WITH:GF:EDGE:band", SP)]
    assert held["evidence_state"] == "BOUNDED_EXPOSURE" and held["bounded_range"]["low"] == AP(1.2)
    for e, it in (("GF-STRIP-OP-061:doorway strip", POR), ("GF-STRIP-OP-061:unattributed strip", THR)):
        assert b[(e, it)]["evidence_state"] == "NOT_APPLICABLE_WITH_EVIDENCE"
    assert b[("HL:FLOOR_SCOPE:OUTDOOR:GF:PASSAGE", SP)]["measured_net"] == AP(6.5)   # the 0.26 counted once, here
    assert b[("HL:FLOOR_SCOPE:THRESHOLD:GF:OP-062", THR)]["bounded_range"]["high"] == AP(0.24)
    f0, f1 = A.floor_line(ls), A.floor_line(out)
    assert f0["internal"]["total"] == AP(65.24 + 4.2)
    assert f1["internal"]["total"] == AP(63.5 + 4.2)
    assert f1["space_held"]["total"] == AP(1.2) and f1["outdoor"]["total"] == AP(6.5)
    assert f1["threshold_held"]["total"] == AP(0.24)
    wet = sum(ln["measured_net"] for ln in out if ln["item_code"] == WET and A._live(ln))
    assert wet == AP(9.0 + 4.2)
    assert A.check_one_strip_one_line(out, {c["after"]["line_id"] for c in ch})["pre_existing_duplicates"] == []
    assert A.check_one_strip_one_line(ls)["pre_existing_duplicates"][0]["opening"] == "OP-061"
    assert ident["outside_rows"] == 1      # the bath only


def test_every_m2_of_the_strip_is_placed_once():
    """2.000 = 0.260 (counted in the outdoor line) + 0.040 (no floor) + 0.500 (wet) + 1.200 (held): nothing summed
    twice, nothing lost."""
    _ls, _out, _ch, logs, _i = run()
    rec = next(r for r in logs[0]["records"] if r["id"] == "EDGE")
    assert sum(p["area_m2"] for p in rec["parts"]) == AP(2.0)
    assert {p["to"] for p in rec["parts"]} == set(A.SPLIT_TO)


# ------------------------------------------------------------------------------------------------ adverse cases
def _with(rid, **kw):
    return [dict(r, **kw) if r["id"] == rid else r for r in records()]


def _parts(**kw):
    r = records()
    e = next(x for x in r if x["id"] == "EDGE")
    e["parts"] = [dict(p, **kw.get(p["part"], {})) for p in e["parts"]]
    return r


@pytest.mark.parametrize("recs, msg", [
    (_parts(band={"dims": [[5.00, 0.20]], "area_m2": 1.0}), "every part of the strip is placed"),   # 0.200 lost
    (_parts(passage={"record": "SILL"}), "names a TO_OUTDOOR record"),
    (_parts(passage={"dims": [[1.20, 0.20]], "area_m2": 0.24}, wall={"dims": [[0.30, 0.20]], "area_m2": 0.06}),
     "counted twice or lost"),                                                                        # 0.240 != 0.260
    (_with("PASSAGE", missing={"m2": 0.26, "why": "x"}), "carried_by"),                              # source unnamed
    (_parts(scullery={"decision": None}), "binding rule or decision"),
    (_parts(band={"why": None}), "never 0"),
    (_parts(wall={"why": None}), "says why"),
    (_parts(band={"dims": [[6000, 200]], "area_m2": 1200000.0}), "unit slip"),                      # mm as m
    (_parts(band={"to": "SOMEWHERE"}), "to one of"),
    (_with("SCU-WHOLE", decision=None), "binding rule or decision"),
    (_with("SCU-WHOLE", move_m2=2.5), "exactly the carried figure"),
    (_with("OPEN-PART", move_m2=5.6), "does not close"),                                            # residual 0.100
    (_with("OPEN-PART", closure=None), "with its closure"),
    (_with("OPEN-PART", move_m2=60.0, closure={"box_m2": 64.5, "terms": {"x": 4.5}}), "smaller than the line"),
    (_with("OPEN-PART", line=ref("GF-ROPEN:floor", WET, 60.0)), "is not one of"),                  # wet -> wet
    (_with("OPEN-PART", area_status="ASSUMED"), "area_status"),
])
def test_inputs_refused(recs, msg):
    with pytest.raises(A.InputsError, match=msg):
        A.load_inputs(inputs(recs), PID)


def test_held_line_not_reclassed():
    ls = lines()
    for ln in ls:
        if ln["location"]["element_id"] == "GF-RSCU:floor":
            ln.update(evidence_state="BOUNDED_EXPOSURE", measured_net=None,
                      bounded_range={"low": 2.9, "high": 3.0, "basis": "x"}, rfi={"question": "q", "unlocks": "x"})
    with pytest.raises(A.InputsError, match="not live|carries"):
        run(ls=ls)


def test_held_part_released_or_zero_refused():
    _ls, out, *_ = run()
    for mutate in ({"evidence_state": "SOURCE_DERIVED", "measured_net": 1.2, "bounded_range": None},
                   {"bounded_range": {"low": 0.0, "high": 0.0, "basis": "x"}}):
        bad = copy.deepcopy(out)
        for ln in bad:
            if ln["location"]["element_id"] == "HL:FLOOR_SCOPE:HELD_WITH:GF:EDGE:band":
                ln.update(**mutate)
        with pytest.raises(A.InputsError, match="keeps its area"):
            A.check_floor_scope(bad)


def test_wet_part_on_a_dry_line_refused():
    _ls, out, *_ = run()
    bad = copy.deepcopy(out)
    for ln in bad:
        if ln["location"]["element_id"] == "HL:FLOOR_SCOPE:WET:GF:OPEN-PART":
            ln["item_code"] = POR
    with pytest.raises(A.InputsError, match="on the wet floor line"):
        A.check_floor_scope(bad)


def test_declared_mismatch_refused():
    with pytest.raises(ValueError, match="declared"):
        run(declared={"dry_to_wet_m2": 9.0})      # the strip's 0.500 is a new wet line, not a dry -> wet move
