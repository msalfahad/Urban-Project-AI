"""T-749: ARCH_TAKEOFF_V3.0.77 (PAINT_GATE_B_V1 + PAINT_EDGE_GATE_B_V1 + EXT_PAINT_EDGE_GATE_B_V1, R-T749-1) on the
hand-calculated NON-Alsenan villa W749 (own figures, no drawing; every figure below by hand):
  P1  room R1: plaster HELD 50.000 .. 56.000 m2, false-ceiling band 6.000 .. 6.400 m2, tiled 0 -> rule paint 44.000 ..
      49.600 m2 (the engine paint line read 43.500 .. 50.000: its own opening ledger) -> restated HELD 44.000 .. 49.600.
  D1  door 0.900 x 2.100 in a 0.200 wall, frame posts over the full depth at both jambs (jambs 0), head not printed
      (0 .. 0.900): the return paint m2 line HELD 0 .. 0.200 x (2 x 2.100 + 0.900) = 0 .. 1.020 m2 -> EXCLUDED EDGE_AS_LM,
      edge line HELD 0 .. 0.900 lm.
  A1  arch, springing not printed: return paint HELD blank -> EXCLUDED, edge line HELD blank (never 0).
  W1  window 1.200 x 1.500 outside: jambs 2 x 1.500 + head 1.200 = 4.200 lm (a point) on the GF facade line (HELD blank)
      -> HELD 4.200 .. 4.200 lm; W2 arched: jambs 2 x 1.000 + half-circle head pi x 0.600 = 2.000 + 1.884956 = 3.884956
      lm (developed, never the rectangle 2 x 1.600 + 1.200 = 4.400); W3 curved frame unprinted -> HELD blank.
  C1  outside corners of the GF facade 4 x 3.300 = 13.200 lm; C2 two parapet-end corners: one drawn to its top 0.400 m,
      the other's top unprinted 0 .. 0.800 -> HELD 0.400 .. 1.200 lm (the unprinted part stays a bound).
  R*  released paint 30.000 m2 and released column 2.000 m3: byte-identical.
Totals by hand: FIN.PAINT held low 43.500 + 0 -> 44.000 (+0.500), high 50.000 + 1.020 -> 49.600 (-1.420), lines
unchanged 4 (2 excluded now: bounded -1, blocked -1), released 30.000 unchanged; FIN.PAINT.EDGE lm new: lines 2, bounded
1 (0 .. 0.900), blocked 1; FIN.EXT.PAINT.EDGE lm new: lines 5, bounded 4 (4.200 + 3.884956 + 13.200 + 0.400 = 21.684956
.. 4.200 + 3.884956 + 13.200 + 1.200 = 22.484956), blocked 1; nothing else.
Adverse: paint above its plaster face, a released paint line restated, a stale range, a blank edge numbered, an edge of
0 .. 0, an exterior DOOR line (its reveal is the return line), the same opening on the return and the exterior codes, an
exterior door that is not its return's reveal, an exterior host that is released or not the facade code, VERIFIED, applied
twice, mirror order gives the same lines, held never 0."""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v304 as A304  # noqa: E402
from engine.source import arch_v3077 as A  # noqa: E402
from engine.source import boq_line as BL  # noqa: E402

PID, REV = "W749-SYNTHETIC", "e" * 64


def _ln(code, eid, state, net=None, unit="m2", rng=None, floor="GF"):
    ln = BL.make_line(project_id=PID, revision_set_sha256=REV, item_code=code, unit=unit, evidence_state=state,
                      measured_net=net, gross=net, element_id=eid, floor=floor, room_id=None,
                      bounded_range=None if rng is None else {"low": rng[0], "high": rng[1], "basis": "synthetic"},
                      formula=f"synthetic {code} {eid}", inputs={}, rule_id="R-SYN", rule_version="1",
                      geometry_source="SYNTHETIC_FIXTURE", material_state="BY_SPEC",
                      rfi={"question": f"not printed: {eid}", "unlocks": eid} if state in (
                          "BLOCKED_RFI", "BOUNDED_EXPOSURE") else None, notes="synthetic",
                      **({} if code in BL.ITEMS else {"item_en": code, "item_ar": code, "trade": "FACADE"}))
    return BL.validate(ln)


def base():
    return [
        _ln("FIN.PLASTER", "HL:WALL_FINISH:R1:PLASTER", "BOUNDED_EXPOSURE", rng=(50.0, 56.0)),
        _ln("FIN.PAINT", "HL:WALL_FINISH:R1:PAINT", "BOUNDED_EXPOSURE", rng=(43.5, 50.0)),
        _ln("FIN.PLASTER", "OP-D1:door jambs and head:RETURN", "MEASURED", net=1.02),
        _ln("FIN.PAINT", "OP-D1:door jambs and head:RETURN_PAINT", "BOUNDED_EXPOSURE", rng=(0.0, 1.02)),
        _ln("FIN.PLASTER", "OP-A1:arch:RETURN", "BLOCKED_RFI"),
        _ln("FIN.PAINT", "OP-A1:arch:RETURN_PAINT", "BLOCKED_RFI"),
        _ln("FIN.EXT.FINISH", "GF-FACADE:facade", "BLOCKED_RFI"),
        _ln("FIN.EXT.FINISH", "1F-FACADE:facade", "MEASURED", net=80.0, floor="1F"),
        _ln("FIN.PAINT", "HL:WALL_FINISH:R9:PAINT", "MEASURED", net=30.0),
        _ln("STR.CONC.COLUMN", "COL:R1", "MEASURED", net=2.0, unit="m3"),
    ]


LN = base()
ID = {ln["location"]["element_id"]: ln["line_id"] for ln in LN}
BY = {ln["line_id"]: ln for ln in LN}
SRC = [{"task": t, "file": f"research/w749/{t}.json", "sha256": "a" * 64, "merge_commit": "b" * 40,
        "checker_run": f"checker {t}"} for t in ("T-P", "T-E", "T-X", "T-M")]


def ex(eid, lo=None, hi=None):
    ln = BY[ID[eid]]
    from engine.source import arch_v3063 as A3063
    r = A3063._range(ln)
    return {"item_code": ln["item_code"], "element_id": eid, "unit": ln["unit"], "class": A.line_class(ln),
            "low": None if r is None else r[0], "high": None if r is None else r[1]}


def restate(lo=44.0, hi=49.6, plaster=(50.0, 56.0)):
    return {"piece": A.P_RS, "action": "RANGE", "line_id": ID["HL:WALL_FINISH:R1:PAINT"], "source_tasks": ["T-P", "T-M"],
            "rule": "UP-FIN-PAINT-002", "status": "HELD", "low": lo, "high": hi, "plaster": list(plaster),
            "why": "paint = plaster - band - tiled", "expect": ex("HL:WALL_FINISH:R1:PAINT")}


def ret(op, paint_eid, plaster_eid, lo=None, hi=None, blank=False):
    return {"piece": A.P_RET, "action": "EDGE_BLANK" if blank else "EDGE", "line_id": ID[paint_eid], "opening": op,
            "kind": "DOOR", "floor": "GF", "element_id": paint_eid.replace(":RETURN_PAINT", ":PAINT_EDGE"),
            "host_line_id": ID[plaster_eid], "source_tasks": ["T-E", "T-M"], "rule": "R-T746-1",
            "status": "HELD" if blank else "DRAWING-CONFIRMED", "low": lo, "high": hi,
            "why": f"{op} edge", "expect": ex(paint_eid), "host_expect": ex(plaster_eid)}


def ext(op, lo, hi, action="OPENING", host="GF-FACADE:facade", kind="WINDOW"):
    e = {"piece": A.P_EXT, "action": action, "floor": "GF", "face_id": f"GF/{op}", "host_line_id": ID[host],
         "element_id": f"GF-FACADE:PAINT_EDGE:{op}", "source_tasks": ["T-X", "T-M"], "rule": "R-T751-2",
         "status": "HELD" if action == "OPENING_BLANK" else "DRAWING-CONFIRMED", "low": lo, "high": hi,
         "why": f"{op} edge", "host_expect": ex(host)}
    if action == "CORNER":
        e.update(corner_group=op, element_id=f"GF-FACADE:CORNER_EDGE:{op}")
    else:
        e.update(opening=op, kind=kind)
    return e


def entries():
    return [
        restate(),
        ret("D1", "OP-D1:door jambs and head:RETURN_PAINT", "OP-D1:door jambs and head:RETURN", 0.0, 0.9),
        ret("A1", "OP-A1:arch:RETURN_PAINT", "OP-A1:arch:RETURN", blank=True),
        ext("W1", 4.2, 4.2),
        ext("W2", 3.884956, 3.884956),
        ext("W3", None, None, action="OPENING_BLANK"),
        ext("C1", 13.2, 13.2, action="CORNER"),
        ext("C2", 0.4, 1.2, action="CORNER"),
    ]


def doc(ents=None, doors=()):
    return {"schema": A.INPUTS_SCHEMA, "project_id": PID, "sources": SRC,
            "entries": entries() if ents is None else ents, "exterior_doors_counted_once": list(doors)}


def run(ents=None, lines=None, doors=()):
    lines = base() if lines is None else lines
    d = A.load_inputs(doc(ents, doors), PID)
    ch, log = A.changes_for(d, lines)
    out, ident = A.integrate(lines, ch)
    return out, ident, ch, lines


def _by_eid(out):
    return {ln["location"]["element_id"]: ln for ln in out}


def test_lines_by_hand():
    out, ident, ch, _ = run()
    e = _by_eid(out)
    p = e["HL:WALL_FINISH:R1:PAINT"]
    assert p["evidence_state"] == "BOUNDED_EXPOSURE" and p["measured_net"] is None
    assert (p["bounded_range"]["low"], p["bounded_range"]["high"]) == (44.0, 49.6)
    d1 = e["OP-D1:door jambs and head:PAINT_EDGE"]
    assert d1["item_code"] == A.EDGE and d1["unit"] == "lm"
    assert (d1["bounded_range"]["low"], d1["bounded_range"]["high"]) == (0.0, 0.9)
    r1 = e["OP-D1:door jambs and head:RETURN_PAINT"]
    assert r1["evidence_state"] == "EXCLUDED_WITH_REASON" and r1["measured_net"] is None
    assert r1["calculation"]["inputs"][A.REC_KEY]["edge_line_id"] == d1["line_id"]
    a1 = e["OP-A1:arch:PAINT_EDGE"]
    assert a1["evidence_state"] == "BLOCKED_RFI" and a1["bounded_range"] is None and a1["measured_net"] is None
    assert e["OP-A1:arch:RETURN_PAINT"]["evidence_state"] == "EXCLUDED_WITH_REASON"
    w2 = e["GF-FACADE:PAINT_EDGE:W2"]
    assert w2["item_code"] == A.EXT_EDGE and w2["bounded_range"]["low"] == pytest.approx(2 * 1.0 + 3.141592653589793 * 0.6,
                                                                                          abs=1e-6)
    assert e["GF-FACADE:PAINT_EDGE:W3"]["evidence_state"] == "BLOCKED_RFI"
    assert ident["added"] == 7 and ident["replaced"] == 3 and ident["outside_rows"] == 7
    assert ident["paint_rule"] == {"PAINT_RESTATE:RANGE": 1, "RETURN_LM:EDGE": 1, "RETURN_LM:EDGE_BLANK": 1,
                                   "RETURN_LM:EXCLUDE": 2, "EXT_EDGE:OPENING": 2, "EXT_EDGE:OPENING_BLANK": 1,
                                   "EXT_EDGE:CORNER": 2}
    assert ident["older_checks_view_substituted"] == 2


def test_totals_by_hand():
    out, _i, ch, lines = run()
    t0, t1 = A304.code_totals(lines), A304.code_totals(out)
    moved = A.check_totals(t0, t1, ch)
    assert set(moved) == {"FIN.PAINT|m2", "FIN.PAINT.EDGE|lm", "FIN.EXT.PAINT.EDGE|lm"}
    p0, p1 = t0["FIN.PAINT|m2"], t1["FIN.PAINT|m2"]
    assert p1["released"] == pytest.approx(30.0) == p0["released"]
    assert p0["held_low"] == pytest.approx(43.5) and p0["held_high"] == pytest.approx(51.02)
    assert p1["held_low"] == pytest.approx(44.0) and p1["held_high"] == pytest.approx(49.6)
    e = t1["FIN.PAINT.EDGE|lm"]
    assert (e["lines"], e["bounded_lines"], e["blocked_lines"]) == (2, 1, 1)
    assert e["held_low"] == pytest.approx(0.0) and e["held_high"] == pytest.approx(0.9)
    x = t1["FIN.EXT.PAINT.EDGE|lm"]
    assert (x["lines"], x["bounded_lines"], x["blocked_lines"]) == (5, 4, 1)
    assert x["held_low"] == pytest.approx(4.2 + 3.884956 + 13.2 + 0.4)
    assert x["held_high"] == pytest.approx(4.2 + 3.884956 + 13.2 + 1.2)
    assert x["released"] == 0 and e["released"] == 0
    assert "STR.CONC.COLUMN|m3" not in moved and "FIN.PLASTER|m2" not in moved and "FIN.EXT.FINISH|m2" not in moved


def test_outside_identical_and_mirror():
    out, _i, _c, lines = run()
    out2, _i2, _c2, _l = run(list(reversed(entries())))
    assert sorted(BL.dumps([x]) for x in out) == sorted(BL.dumps([x]) for x in out2)
    by = {x["line_id"]: x for x in out}
    for eid in ("HL:WALL_FINISH:R9:PAINT", "COL:R1", "HL:WALL_FINISH:R1:PLASTER", "GF-FACADE:facade"):
        assert BL.dumps([by[ID[eid]]]) == BL.dumps([BY[ID[eid]]])


def test_held_never_zero():
    out, *_ = run()
    for ln in out:
        if ln["item_code"] in (A.EDGE, A.EXT_EDGE):
            assert ln["measured_net"] is None and A.line_class(ln) == "HELD"
            assert ln["bounded_range"] is None or ln["bounded_range"]["high"] > 0


def test_exterior_door_counted_once():
    out, *_ = run(doors=[{"opening": "D1", "lm": ["0.000000", "0.900000"], "under": ID[
        "OP-D1:door jambs and head:RETURN_PAINT"]}])
    assert sum(1 for ln in out if ln["item_code"] in (A.EDGE, A.EXT_EDGE) and "D1" in ln["location"]["element_id"]) == 1


@pytest.mark.parametrize("mut, msg", [
    (lambda E: E[0].update(high=56.5), "above its plaster"),
    (lambda E: E[0]["expect"].update(low=43.0), "stale"),
    (lambda E: E[2].update(low=0.0, high=1.0), "blank edge carries a figure"),
    (lambda E: E[1].update(low=0.0, high=0.0), "never 0"),
    (lambda E: E[3].update(kind="DOOR"), "a door reveal is its return line"),
    (lambda E: E[3].update(opening="D1"), "one reveal, one line"),
    (lambda E: E[0].update(status="VERIFIED"), "never VERIFIED"),
    (lambda E: E[4].update(low=None, high=None), "carries low and high"),
    (lambda E: E[3].update(host_line_id=ID["1F-FACADE:facade"], host_expect=ex("1F-FACADE:facade")),
     "HELD FIN.EXT.FINISH"),
    (lambda E: E[3].update(host_line_id=ID["HL:WALL_FINISH:R1:PLASTER"],
                           host_expect=ex("HL:WALL_FINISH:R1:PLASTER")), "FIN.EXT.FINISH"),
    (lambda E: E.append(copy.deepcopy(E[0])), "named twice"),
    (lambda E: E[5].update(low=2.0, high=1.0), "blank edge carries a figure"),
    (lambda E: E[6].update(low=2.0, high=1.0), "low 2.0 > high 1.0"),
])
def test_adverse(mut, msg):
    E = entries()
    mut(E)
    with pytest.raises(A.InputsError, match=msg):
        run(E)


def test_released_paint_never_restated():
    E = entries()
    E[0].update(line_id=ID["HL:WALL_FINISH:R9:PAINT"], expect=dict(ex("HL:WALL_FINISH:R9:PAINT")))
    with pytest.raises(A.InputsError, match="HELD bounded FIN.PAINT"):
        run(E)


def test_exterior_door_not_its_reveal_refused():
    with pytest.raises(A.InputsError, match="not the reveal"):
        run(doors=[{"opening": "D1", "lm": ["0.000000", "1.000000"],
                    "under": ID["OP-D1:door jambs and head:RETURN_PAINT"]}])


def test_applied_twice_refused():
    out, *_ = run()
    with pytest.raises(A.InputsError, match="applied once|already carries"):
        A.changes_for(A.load_inputs(doc(), PID), out)


def test_two_codes_for_one_opening_caught_on_lines():
    out, *_ = run()
    bad = copy.deepcopy(out)
    w1 = next(ln for ln in bad if ln["location"]["element_id"] == "GF-FACADE:PAINT_EDGE:W1")
    w1["calculation"]["inputs"][A.REC_KEY]["opening"] = "D1"
    with pytest.raises(ValueError, match="two edge codes"):
        A.check_lines(bad)
