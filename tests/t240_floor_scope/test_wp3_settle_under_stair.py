"""T-240 WP3: ARCH_TAKEOFF_V3.0.14 kinds SETTLE_RANGE (a bounded floor line whose held stair strips a checker verdict
settled from the drawings, with a part of another finish split out by a binding decision) and UNDER_STAIR (the tread
union a lowest-storey face deducts, placed flight by flight). Synthetic data only (no client drawing).

VILLA K-240 (not the development villa), hand values:
  1F hall face 1F-RHALL porcelain carried as the range 30.000 .. 30.600 m2 on two held strips:
     foot of the arriving flight 1.20 x 0.40 = 0.480 -> the last tread 1.20 x 0.35 = 0.420 (stair) + the landing nosing
     band 1.20 x 0.05 = 0.060 (floor); a band beside a flight 0.05 x 2.40 = 0.120 (floor, slab edge on its flight side).
     Settled: 30.000 + 0.060 + 0.120 = 30.180 m2.
     The arrival landing is marble by decision K-66 B: printed 2.40 x 2.00 = 4.800, less a well end 0.20 x 0.10 = 0.020,
     plus the nosing band 0.060 = 4.840 m2 -> its own internal space line; porcelain keeps 30.180 - 4.840 = 25.340.
  GF hall face GF-RHALL porcelain 50.000 m2 = face 56.000 less the tread union 6.000 of a stair rising from it (lowest
     storey): F1 2.500 drawn below the cut -> HELD; F2 1.500 and F3 2.000 drawn overhead only, nothing closed under ->
     floor 3.500 (a new porcelain line; the face line stays 50.000).
  Internal floor line: before GF 50.000 + bath 4.200 (the 1F range is in no internal figure); after GF 53.500 + 4.200,
     1F 25.340 + 4.840 = 30.180; held under the stair 2.500, apart.
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v3014 as A                      # noqa: E402
from engine.source import boq_line as BL                       # noqa: E402

AP = pytest.approx
PID = "synthetic-v3014-villa-k240-wp3"
DOCS = [{"file": "K-ARCH.dxf", "sha256": "5" * 64}]
POR, WET, SP = "FIN.FLOOR.PORCELAIN", "FIN.FLOOR.WET_TILE", "ARCH.SPACE"
DEC = "owner decision K-66 B (the arrival landing is marble with the stair, once)"


def line(eid, item, floor, q=1.0, ev="SOURCE_DERIVED", rng=None):
    held = ev in ("BOUNDED_EXPOSURE", "BLOCKED_RFI")
    return BL.make_line(project_id=PID, revision_set_sha256="0" * 64, item_code=item, unit="m2", evidence_state=ev,
                        measured_net=None if held else q, bounded_range=rng, element_id=eid, floor=floor,
                        physical_element=eid, formula="route", documents=DOCS, rule_id="SV", rule_version="1",
                        rfi={"question": "q", "unlocks": eid} if held else None)


def lines():
    return [line("1F-RHALL:floor", POR, "1F", ev="BOUNDED_EXPOSURE",
                 rng={"low": 30.0, "high": 30.6, "basis": "two stair strips held"}),
            line("GF-RHALL:floor", POR, "GF", 50.0, "PROVISIONAL"),
            line("GF-RBATH:floor", WET, "GF", 4.2)]


def src():
    return {"file": "research/T-SR/LEDGER.csv", "sha256": "e" * 64, "task": "T-SR", "merge_commit": "abc1234",
            "checker_run": "verifier run for T-SR"}


def ref(eid, item, floor, carried, why="moves"):
    return {"item_code": item, "floor": floor, "element_id": eid, "unit": "m2", "carried": carried, "why": why}


def settle():
    return {"id": "HALL-1F", "kind": "SETTLE_RANGE", "floor": "1F", "area_status": "VERIFIED", "value_m2": 30.18,
            "evidence": "structural sheet draws the last riser on the landing edge; slab edge on the band's flight side",
            "drawing_reference": "lines R1 .. R12, S9", "verified_by": "checker own",
            "line": ref("1F-RHALL:floor", POR, "1F", [30.0, 30.6], "a face carried as a range on two held strips"),
            "pieces": [
                {"piece": "foot tread", "dims": [[1.20, 0.35]], "area_m2": 0.42, "to": "NOT_FLOOR",
                 "why": "the last tread: stair", "evidence": "12 risers on the structural sheet"},
                {"piece": "foot nosing", "dims": [[1.20, 0.05]], "area_m2": 0.06, "to": "FLOOR",
                 "why": "nosing band of the landing", "evidence": "top riser on the landing edge"},
                {"piece": "band", "dims": [[0.05, 2.40]], "area_m2": 0.12, "to": "FLOOR",
                 "why": "balustrade on the slab edge", "evidence": "slab edge S9 on the flight side"}],
            "split_out": {"part": "landing", "decision": DEC, "material": "marble", "area_status": "VERIFIED",
                          "material_status": "ASSUMED - OWNER-APPROVED", "material_source": "K-66 B",
                          "area_m2": 4.84, "kept_m2": 25.34,
                          "terms": {"printed 2.40 x 2.00": 4.8, "well end 0.20 x 0.10": -0.02, "nosing band": 0.06}}}


def under():
    return {"id": "HALL-GF", "kind": "UNDER_STAIR", "floor": "GF", "lowest_storey": True,
            "area_status": "DRAWING-CONFIRMED", "deducted_m2": 6.0, "evidence": "flights by how the plan draws them",
            "drawing_reference": "cut symbol C1", "verified_by": "checker own",
            "face": ref("GF-RHALL:floor", POR, "GF", 50.0, "face net of the tread union"),
            "flights": [
                {"flight": "F1", "area_m2": 2.5, "drawn": "BELOW_CUT", "to": "HELD", "why": "structure undrawn",
                 "evidence": "solid lines inside"},
                {"flight": "F2", "area_m2": 1.5, "drawn": "OVERHEAD_ONLY", "closed_under": False, "to": "FLOOR",
                 "evidence": "dashed only"},
                {"flight": "F3", "area_m2": 2.0, "drawn": "OVERHEAD_ONLY", "closed_under": False, "to": "FLOOR",
                 "evidence": "dashed only"}]}


def records():
    return [settle(), under()]


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
    ls, out, ch, logs, ident = run(declared={"floor_internal_in_m2": 30.18 + 3.5, "settled_m2": 30.18,
                                             "under_stair_floor_m2": 3.5, "under_stair_held_m2": 2.5,
                                             "floor_internal_delta_m2": 33.68})
    b = by_eid(out)
    h1 = b[("1F-RHALL:floor", POR)]
    assert h1["evidence_state"] == "SOURCE_DERIVED" and h1["measured_net"] == AP(25.34) and h1["bounded_range"] is None
    land = b[("HL:FLOOR_SCOPE:SPLIT_OUT:1F:HALL-1F:landing", SP)]
    assert land["measured_net"] == AP(4.84)
    assert land["calculation"]["inputs"]["floor_scope_v3014"]["floor_key"] == "FLOOR.INTERNAL"
    assert b[("GF-RHALL:floor", POR)]["measured_net"] == AP(50.0)          # the face line is not changed
    assert b[("HL:FLOOR_SCOPE:UNDER_STAIR:GF:HALL-GF", POR)]["measured_net"] == AP(3.5)
    hs = b[("HL:FLOOR_SCOPE:UNDER_STAIR_HELD:GF:HALL-GF", SP)]
    assert hs["evidence_state"] == "BOUNDED_EXPOSURE" and hs["bounded_range"]["low"] == AP(2.5)
    f0, f1 = A.floor_line(ls), A.floor_line(out)
    assert f0["internal"]["total"] == AP(54.2)
    assert f1["internal"]["GF"] == AP(57.7) and f1["internal"]["1F"] == AP(30.18)
    assert f1["space_held"]["total"] == AP(2.5)
    assert A.check_floor_scope(out) == {"SETTLE_RANGE": 2, "UNDER_STAIR": 2}
    assert ident["outside_rows"] == 2 and ident["replaced"] == 1 and ident["added"] == 3


def test_every_piece_placed_once():
    """0.600 range width = 0.420 stair + 0.060 + 0.120 floor; 6.000 union = 2.500 held + 3.500 floor."""
    _ls, _out, _ch, logs, _i = run()
    t = logs[0]["totals"]
    assert t["settled_m2"] == AP(30.18)
    assert t["under_stair_floor_m2"] + t["under_stair_held_m2"] == AP(6.0)


def test_settle_without_split_keeps_the_face_whole():
    r = settle()
    r.pop("split_out")
    _ls, out, *_ = run([r])
    assert by_eid(out)[("1F-RHALL:floor", POR)]["measured_net"] == AP(30.18)


# ------------------------------------------------------------------------------------------------ adverse cases
def _s(**kw):
    return [dict(settle(), **kw), under()]


def _sp(**kw):
    r = settle()
    r["pieces"] = [dict(p, **kw.get(p["piece"], {})) for p in r["pieces"]]
    return [r, under()]


def _so(**kw):
    r = settle()
    r["split_out"] = dict(r["split_out"], **kw)
    return [r, under()]


def _u(**kw):
    return [settle(), dict(under(), **kw)]


def _uf(**kw):
    r = under()
    r["flights"] = [dict(f, **kw.get(f["flight"], {})) for f in r["flights"]]
    return [settle(), r]


@pytest.mark.parametrize("recs, msg", [
    (_sp(band={"to": "HELD"}), "to one of"),                                           # a piece still open
    (_sp(band={"dims": [[0.05, 2.00]], "area_m2": 0.1}), "range width"),             # 0.020 lost
    (_s(value_m2=30.6), "value_m2"),                                                   # the larger end, not settled
    (_s(line=ref("1F-RHALL:floor", POR, "1F", 30.18)), "carries a range"),             # a live figure
    (_s(area_status="ASSUMED"), "area_status"),
    (_sp(band={"evidence": None}), "drawn evidence"),
    (_sp(band={"dims": [[50, 2400]], "area_m2": 120000.0}), "unit slip"),               # mm as m
    (_so(decision=None), "decision is required"),
    (_so(kept_m2=25.33), "never absorbed"),                                            # residual 0.010
    (_so(area_m2=4.9), "its terms"),
    (_so(terms={"printed 2400 x 2000": 4800000.0}), "unit slip"),
    (_so(material_status="GUESSED"), "material_status"),
    (_u(lowest_storey=False), "lowest storey"),
    (_uf(F1={"to": "FLOOR"}), "drawn overhead only"),                                 # below the cut released
    (_uf(F2={"closed_under": True}), "drawn overhead only"),                          # a closed thing under it
    (_uf(F2={"closed_under": None}), "drawn overhead only"),                          # not stated is not False
    (_uf(F3={"area_m2": 1.9}), "every tread placed once"),
    (_uf(F1={"why": None}), "never 0"),
    (_uf(F1={"drawn": "SOMEHOW"}), "drawn one of"),
    (_u(material_from_neighbour=True), "D-C3"),
    (_u(face=ref("GF-RHALL:floor", SP, "GF", 50.0)), "is not one of"),
])
def test_inputs_refused(recs, msg):
    with pytest.raises(A.InputsError, match=msg):
        A.load_inputs(inputs(recs), PID)


def test_line_named_twice_refused():
    wet = {"id": "AGAIN", "kind": "TO_WET", "floor": "1F", "decision": DEC, "whole": True, "move_m2": 30.0,
           "area_status": "DRAWING-CONFIRMED", "evidence": "x", "drawing_reference": "x",
           "line": ref("1F-RHALL:floor", POR, "1F", 30.0)}
    with pytest.raises(A.InputsError, match="named by two records"):
        A.load_inputs(inputs(records() + [wet]), PID)


def test_carried_range_must_be_the_lines():
    with pytest.raises(A.InputsError, match="carries"):
        run(_s(line=ref("1F-RHALL:floor", POR, "1F", [30.0, 30.7]), pieces=settle()["pieces"] + [
            {"piece": "extra", "dims": [[1.0, 0.1]], "area_m2": 0.1, "to": "NOT_FLOOR", "why": "x", "evidence": "y"}]))


def test_live_line_not_settled():
    ls = lines()
    ls[0].update(evidence_state="SOURCE_DERIVED", measured_net=30.0, bounded_range=None, rfi=None)
    with pytest.raises(A.InputsError, match="carries"):
        run(ls=ls)


def test_under_stair_face_must_carry_the_stated_figure():
    with pytest.raises(A.InputsError, match="carries"):
        run(_u(face=ref("GF-RHALL:floor", POR, "GF", 56.0)))       # the face before the deduction


def test_held_under_stair_released_or_zero_refused():
    _ls, out, *_ = run()
    for mutate in ({"evidence_state": "SOURCE_DERIVED", "measured_net": 2.5, "bounded_range": None, "rfi": None},
                   {"bounded_range": {"low": 0.0, "high": 0.0, "basis": "x"}}):
        bad = copy.deepcopy(out)
        for ln in bad:
            if ln["location"]["element_id"] == "HL:FLOOR_SCOPE:UNDER_STAIR_HELD:GF:HALL-GF":
                ln.update(**mutate)
        with pytest.raises(A.InputsError, match="keeps its area"):
            A.check_floor_scope(bad)


def test_split_part_left_on_the_finish_line_refused():
    _ls, out, *_ = run()
    bad = copy.deepcopy(out)
    for ln in bad:
        if ln["location"]["element_id"] == "1F-RHALL:floor":
            ln["measured_net"] = 30.18                                # the landing counted in porcelain too
    with pytest.raises(A.InputsError, match="settled figure"):
        A.check_floor_scope(bad)


def test_declared_mismatch_refused():
    with pytest.raises(ValueError, match="declared"):
        run(declared={"floor_internal_in_m2": 30.18 + 6.0})          # the held flight counted as floor
