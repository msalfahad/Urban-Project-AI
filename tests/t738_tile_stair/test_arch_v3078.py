"""T-738: ARCH_TAKEOFF_V3.0.78 (TILE_GATE_B_V1 + STAIR_FINISH_GATE_B_V1, R-T738-1) on the hand-calculated NON-Alsenan
villa W738 (own figures, no drawing; every figure below by hand):
  T1  stair-core wall: run 5.000 m x tile top 2.400 .. 4.400 m = 12.000 .. 22.000 m2 less openings 2.000 m2 at both ends
      (one door each reading) -> HELD 10.000 .. 20.000 m2 (was HELD blank).
  F1  straight flight, 10 risers, rise 0.170, going 0.280, width 1.000, tread 0.020: risers 10 x 1.000 x (0.170 - 0.020)
      = 1.500 m2 (a HELD point); pitch line 10 x hypot(0.280, 0.170) = 10 x 0.327567 = 3.275668 lm (a HELD point);
      its tread 2.800 m2 is RELEASED (carrier).
  V1  the same flight read again from the upper floor through the void (riser blank, tread HELD 0 .. 2.800): one physical
      flight, one carrier -> both EXCLUDED DUPLICATE_READING naming the F1 line of the same code (tread counted once:
      2.800, never 5.600).
  W1  winder turn, 3 winders inside a 1.000 x 1.000 square: nosings 3 x 1.000 .. 3 x hypot(1, 1) = 3.000 .. 4.242641 lm
      (BOUND); its pitch line not drawn -> NAMED (blank, cause restated).
  S1  skirting piece, plan 0.750 + 1 riser 0.170 over going 0.280: zigzag 0.750 + 0.170 = 0.920 lm, sloped 0.750 /
      0.280 x 0.327567 ... both forms read by the ledger as 0.920 / 0.877412 lm: CONDITIONAL on ORR-007, siblings, never
      summed, never released; S2 open side: AT_MOST 1.200 lm; soffit AT_LEAST 5.000 m2.
  L1  landing line HELD 0 .. 2.000 m2 where the ledger finds no landing -> EXCLUDED NO_PHYSICAL_ELEMENT.
  C1  closing riser no line carries: 1 x 1.000 x 0.150 = 0.150 m2 ADDED as a HELD point beside F1's riser line.
Totals by hand: FIN.WALL.TILE blocked 1 -> bounded 1, 10.000 .. 20.000; FIN.MARBLE.RISER lines 2 -> 2 (V1 out, C1 in),
blocked 2 -> 0, bounded 0 -> 2, 1.650 .. 1.650; FIN.MARBLE.TREAD lines 2 -> 1, released 2.800 unchanged, bounded 1 -> 0
(0 .. 2.800 gone); FIN.STAIR.FLIGHT blocked 2 -> 1, bounded 3.275668; FIN.STAIR.STEP_LM blocked 1 -> bounded 3.000 ..
4.242641; FIN.MARBLE.LANDING lines 1 -> 0; skirting / soffit totals unchanged (blank -> blank, figures beside only);
released paint 30.000 m2 and concrete 2.000 m3 byte-identical.
Adverse: VERIFIED, stale range, released line restated, cap 0, conditional off ORR-007 / not a skirting line, a sibling
that is not the other form, a duplicate without carrier / carrier excluded too / carrier of another code, applied twice,
a point 0, an added line over a candidate id; mirror order gives the same lines."""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v304 as A304  # noqa: E402
from engine.source import arch_v3063 as A3063  # noqa: E402
from engine.source import arch_v3078 as A  # noqa: E402
from engine.source import boq_line as BL  # noqa: E402

PID, REV = "W738-SYNTHETIC", "d" * 64


def _ln(code, eid, state, net=None, unit="m2", rng=None, floor="GF"):
    ln = BL.make_line(project_id=PID, revision_set_sha256=REV, item_code=code, unit=unit, evidence_state=state,
                      measured_net=net, gross=net, element_id=eid, floor=floor, room_id=None,
                      bounded_range=None if rng is None else {"low": rng[0], "high": rng[1], "basis": "synthetic"},
                      formula=f"synthetic {code} {eid}", inputs={}, rule_id="R-SYN", rule_version="1",
                      geometry_source="SYNTHETIC_FIXTURE", material_state="BY_SPEC",
                      rfi={"question": f"not printed: {eid}", "unlocks": eid} if state in (
                          "BLOCKED_RFI", "BOUNDED_EXPOSURE") else None, notes="synthetic",
                      **({} if code in BL.ITEMS else {"item_en": code, "item_ar": code, "trade": "STAIR_FINISH"}))
    return BL.validate(ln)


SL, ZZ = "FIN.STAIR.SKIRTING.SLOPED", "FIN.STAIR.SKIRTING.ZIGZAG"


def base():
    return [
        _ln("FIN.WALL.TILE", "GF-CORE:wall_tile", "BLOCKED_RFI"),
        _ln("FIN.MARBLE.RISER", "GF-ST:flight 1", "BLOCKED_RFI"),
        _ln("FIN.MARBLE.RISER", "1F-ST:flight 1", "BLOCKED_RFI", floor="1F"),
        _ln("FIN.MARBLE.TREAD", "GF-ST:flight 1", "MEASURED", net=2.8),
        _ln("FIN.MARBLE.TREAD", "1F-ST:flight 1", "BOUNDED_EXPOSURE", rng=(0.0, 2.8), floor="1F"),
        _ln("FIN.STAIR.FLIGHT", "GF-ST:flight 1", "BLOCKED_RFI", unit="lm"),
        _ln("FIN.STAIR.FLIGHT", "GF-ST:winder", "BLOCKED_RFI", unit="lm"),
        _ln("FIN.STAIR.STEP_LM", "GF-ST:winder", "BLOCKED_RFI", unit="lm"),
        _ln(SL, "STAIR-SKIRT:S1", "BLOCKED_RFI", unit="lm"),
        _ln(ZZ, "STAIR-SKIRT:S1", "BLOCKED_RFI", unit="lm"),
        _ln(SL, "STAIR-SKIRT:S2", "BLOCKED_RFI", unit="lm"),
        _ln("FIN.STAIR.SOFFIT", "STAIR:ST:soffit", "BLOCKED_RFI"),
        _ln("FIN.MARBLE.LANDING", "GF-ST:landings", "BOUNDED_EXPOSURE", rng=(0.0, 2.0)),
        _ln("FIN.PAINT", "HL:WALL_FINISH:R9:PAINT", "MEASURED", net=30.0),
        _ln("STR.CONC.COLUMN", "COL:R1", "MEASURED", net=2.0, unit="m3"),
    ]


LN = base()
ID = {(ln["item_code"], ln["location"]["element_id"]): ln["line_id"] for ln in LN}
BY = {ln["line_id"]: ln for ln in LN}
SRC = [{"task": t, "file": f"research/w738/{t}.json", "sha256": "a" * 64, "merge_commit": "c" * 40,
        "checker_run": f"checker {t}"} for t in ("T-TILE", "T-STAIR", "T-MAP")]


def lid(code, eid):
    return ID[(code, eid)]


def ex(code, eid):
    ln = BY[lid(code, eid)]
    r = A3063._range(ln)
    return {"item_code": code, "element_id": eid, "unit": ln["unit"], "class": A.line_class(ln),
            "low": None if r is None else r[0], "high": None if r is None else r[1]}


def ent(piece, action, code, eid, **kw):
    e = {"piece": piece, "action": action, "line_id": lid(code, eid), "expect": ex(code, eid),
         "source_tasks": ["T-STAIR" if piece == A.P_STAIR else "T-TILE", "T-MAP"], "rule": "R-SYN",
         "status": "DRAWING-CONFIRMED", "why": f"synthetic {action}"}
    e.update(kw)
    return e


def entries():
    S, T = A.P_STAIR, A.P_TILE
    return [
        ent(T, "BOUND", "FIN.WALL.TILE", "GF-CORE:wall_tile", low=10.0, high=20.0,
            status="ASSUMED — OWNER-APPROVED"),
        ent(S, "POINT", "FIN.MARBLE.RISER", "GF-ST:flight 1", value=1.5),
        ent(S, "EXCLUDE", "FIN.MARBLE.RISER", "1F-ST:flight 1", cause="DUPLICATE_READING",
            carrier_line_id=lid("FIN.MARBLE.RISER", "GF-ST:flight 1"), carrier_element_id="GF-ST:flight 1"),
        ent(S, "EXCLUDE", "FIN.MARBLE.TREAD", "1F-ST:flight 1", cause="DUPLICATE_READING",
            carrier_line_id=lid("FIN.MARBLE.TREAD", "GF-ST:flight 1")),
        ent(S, "POINT", "FIN.STAIR.FLIGHT", "GF-ST:flight 1", value=3.275668),
        ent(S, "NAMED", "FIN.STAIR.FLIGHT", "GF-ST:winder", status="HELD", open="winder walking line not drawn"),
        ent(S, "BOUND", "FIN.STAIR.STEP_LM", "GF-ST:winder", low=3.0, high=4.242641),
        ent(S, "CONDITIONAL", SL, "STAIR-SKIRT:S1", value=0.877412, ruling="ORR-007",
            sibling_line_id=lid(ZZ, "STAIR-SKIRT:S1")),
        ent(S, "CONDITIONAL", ZZ, "STAIR-SKIRT:S1", value=0.92, ruling="ORR-007",
            sibling_line_id=lid(SL, "STAIR-SKIRT:S1")),
        ent(S, "AT_MOST", SL, "STAIR-SKIRT:S2", value=1.2, status="HELD"),
        ent(S, "AT_LEAST", "FIN.STAIR.SOFFIT", "STAIR:ST:soffit", value=5.0),
        ent(S, "EXCLUDE", "FIN.MARBLE.LANDING", "GF-ST:landings", cause="NO_PHYSICAL_ELEMENT"),
        {"piece": S, "action": "ADD_POINT", "add_key": "C1-closing-riser",
         "host_line_id": lid("FIN.MARBLE.RISER", "GF-ST:flight 1"), "item_code": "FIN.MARBLE.RISER", "unit": "m2",
         "value": 0.15, "item": "closing riser", "element": "C1 closing riser", "source_tasks": ["T-STAIR"],
         "rule": "R-SYN", "status": "DRAWING-CONFIRMED", "why": "1 x 1.000 x 0.150"},
    ]


def doc(ents=None):
    return {"schema": A.INPUTS_SCHEMA, "project_id": PID, "sources": copy.deepcopy(SRC),
            "entries": copy.deepcopy(entries() if ents is None else ents)}


def run(ents=None, prev=None):
    prev = base() if prev is None else prev
    d = A.load_inputs(doc(ents), PID)
    ch, log = A.changes_for(d, prev)
    out, ident = A.integrate(prev, ch)
    return prev, ch, out, ident


def _by(lines):
    return {(x["item_code"], x["location"]["element_id"]): x for x in lines}


# ------------------------------------------------------------------------------------------------ normal
def test_states_and_figures_by_hand():
    prev, ch, out, ident = run()
    b = _by(out)
    assert A3063._range(b[("FIN.WALL.TILE", "GF-CORE:wall_tile")]) == (10.0, 20.0)
    assert A3063._range(b[("FIN.MARBLE.RISER", "GF-ST:flight 1")]) == (1.5, 1.5)
    assert A3063._range(b[("FIN.STAIR.FLIGHT", "GF-ST:flight 1")]) == (3.275668, 3.275668)
    assert A3063._range(b[("FIN.STAIR.STEP_LM", "GF-ST:winder")]) == (3.0, 4.242641)
    for k in (("FIN.MARBLE.RISER", "1F-ST:flight 1"), ("FIN.MARBLE.TREAD", "1F-ST:flight 1"),
              ("FIN.MARBLE.LANDING", "GF-ST:landings")):
        assert A.line_class(b[k]) == "EXCLUDED" and b[k]["measured_net"] is None
    named = b[("FIN.STAIR.FLIGHT", "GF-ST:winder")]
    assert named["evidence_state"] == A.BLANK and "winder walking line" in named["rfi"]["question"]
    assert ident["replaced"] == 12 and ident["added"] == 1 and ident["outside_rows"] == 3


def test_hand_pitch_and_riser():
    import math
    assert round(10 * 1.0 * (0.17 - 0.02), 6) == 1.5
    assert round(10 * math.hypot(0.28, 0.17), 6) == 3.275668
    assert round(3 * math.hypot(1.0, 1.0), 6) == 4.242641


def test_totals_by_hand():
    prev, ch, out, ident = run()
    t0, t1 = A304.code_totals(prev), A304.code_totals(out)
    moved = A.check_totals(t0, t1, ch)
    assert t1["FIN.WALL.TILE|m2"]["held_low"] == 10.0 and t1["FIN.WALL.TILE|m2"]["held_high"] == 20.0
    r = t1["FIN.MARBLE.RISER|m2"]
    assert (r["lines"], r["bounded_lines"], r["blocked_lines"]) == (2, 2, 0)
    assert abs(r["held_low"] - 1.65) < 1e-9 and abs(r["held_high"] - 1.65) < 1e-9
    t = t1["FIN.MARBLE.TREAD|m2"]
    assert (t["lines"], t["released"], t["bounded_lines"], t["held_high"]) == (1, 2.8, 0, 0.0)
    assert t1["FIN.STAIR.STEP_LM|lm"]["held_high"] == 4.242641
    assert "FIN.MARBLE.LANDING|m2" not in t1
    assert set(moved) == {"FIN.WALL.TILE|m2", "FIN.MARBLE.RISER|m2", "FIN.MARBLE.TREAD|m2", "FIN.STAIR.FLIGHT|lm",
                          "FIN.STAIR.STEP_LM|lm", "FIN.MARBLE.LANDING|m2"}
    for k in ("FIN.PAINT|m2", "STR.CONC.COLUMN|m3", f"{SL}|lm", f"{ZZ}|lm", "FIN.STAIR.SOFFIT|m2"):
        assert t0[k] == t1[k]


def test_tread_counted_once():
    """a flight read on two floors (two readings) is counted once: its carrier's 2.800, never 5.600"""
    prev, ch, out, ident = run()
    live = [x for x in out if x["item_code"] == "FIN.MARBLE.TREAD" and A.line_class(x) != "EXCLUDED"]
    assert len(live) == 1 and live[0]["measured_net"] == 2.8
    before_high = sum((A3063._range(x) or (0, x["measured_net"] or 0))[1] for x in prev
                      if x["item_code"] == "FIN.MARBLE.TREAD")
    assert before_high == 5.6


def test_ruling_held_never_released_or_summed():
    prev, ch, out, ident = run()
    b = _by(out)
    for code in (SL, ZZ):
        ln = b[(code, "STAIR-SKIRT:S1")]
        assert A.line_class(ln) == "HELD" and ln["evidence_state"] == A.BLANK and ln["bounded_range"] is None
        kind, v, ruling = A.beside_of(ln)
        assert kind == "CONDITIONAL_ON_FORM" and ruling == "ORR-007" and v > 0
    t1 = A304.code_totals(out)
    assert t1[f"{SL}|lm"]["released"] == 0.0 and t1[f"{SL}|lm"]["held_high"] == 0.0
    c = A.census(out)
    assert c[SL]["beside_n"] == {"CONDITIONAL_ON_FORM": 1, "AT_MOST": 1} and c[SL]["released"] == 0


def test_outside_byte_identical_and_released_kept():
    prev, ch, out, ident = run()
    from engine.source import arch_v30 as A30
    o = _by(out)
    for k in (("FIN.PAINT", "HL:WALL_FINISH:R9:PAINT"), ("STR.CONC.COLUMN", "COL:R1"),
              ("FIN.MARBLE.TREAD", "GF-ST:flight 1")):
        assert A30.line_sha(o[k]) == A30.line_sha(_by(prev)[k])


def test_mirror_order_same_lines():
    from engine.source import arch_v30 as A30
    _p, _c, a, _i = run()
    _p, _c, b, _i = run(list(reversed(entries())))
    assert sorted(A30.line_sha(x) for x in a) == sorted(A30.line_sha(x) for x in b)


def test_census_and_held_never_zero():
    prev, ch, out, ident = run()
    for x in out:
        if A.line_class(x) == "HELD":
            r = A3063._range(x)
            assert r is None or r[0] > 0
    assert ident["tile_stair"]["STAIR_WIRE:EXCLUDE"] == 3 and ident["tile_stair"]["STAIR_WIRE:ADD_POINT"] == 1


# ------------------------------------------------------------------------------------------------ adverse
def _refused(ents, prev=None, match=None):
    with pytest.raises((A.InputsError, ValueError), match=match):
        run(ents, prev)


def _swap(i, **kw):
    e = entries()
    e[i] = dict(e[i], **kw)
    return e


def test_verified_refused():
    _refused(_swap(1, status="VERIFIED"), match="status")


def test_stale_range_refused():
    e = entries()
    e[3]["expect"] = dict(e[3]["expect"], high=2.9)
    _refused(e, match="stale")


def test_released_line_restated_refused():
    e = entries() + [ent(A.P_STAIR, "POINT", "FIN.MARBLE.TREAD", "GF-ST:flight 1", value=2.8)]
    e[-1]["expect"] = dict(e[-1]["expect"], **{"class": "HELD"})
    _refused(e, match="stale")


def test_cap_zero_refused():
    _refused(_swap(9, value=0), match="cap of 0")


def test_conditional_off_ruling_refused():
    _refused(_swap(7, ruling=None), match="ORR-007")
    e = entries() + [ent(A.P_STAIR, "CONDITIONAL", "FIN.STAIR.SOFFIT", "STAIR:ST:soffit", value=5.0,
                         ruling="ORR-007")]
    del e[10]
    _refused(e, match="skirting")


def test_sibling_not_other_form_refused():
    _refused(_swap(7, sibling_line_id=lid(SL, "STAIR-SKIRT:S2")), match="sibling")


def test_duplicate_without_carrier_refused():
    e = _swap(2, carrier_line_id=None)
    _refused(e, match="carrier")


def test_carrier_excluded_too_refused():
    e = entries()
    e[1] = ent(A.P_STAIR, "EXCLUDE", "FIN.MARBLE.RISER", "GF-ST:flight 1", cause="NO_PHYSICAL_ELEMENT")
    e = [x for x in e if x.get("action") != "ADD_POINT"]
    _refused(e, match="excluded here too")


def test_carrier_other_code_refused():
    _refused(_swap(3, carrier_line_id=lid("FIN.MARBLE.RISER", "GF-ST:flight 1")), match="carrier")


def test_carrier_element_mismatch_refused():
    _refused(_swap(2, carrier_element_id="GF-ST:flight 9"), match="element")


def test_applied_twice_refused():
    prev, ch, out, ident = run()
    with pytest.raises(A.InputsError, match="applied once"):
        A.changes_for(A.load_inputs(doc(), PID), out)


def test_point_zero_refused():
    _refused(_swap(1, value=0), match="never 0")
    e = entries()
    e[-1] = dict(e[-1], value=0)
    _refused(e, match="never 0")


def test_bound_low_above_high_refused():
    _refused(_swap(6, low=5.0, high=4.0), match="low")


def test_add_must_name_host_not_id():
    e = entries()
    e[-1] = dict(e[-1], line_id=lid("FIN.MARBLE.RISER", "GF-ST:flight 1"))
    _refused(e, match="host line")


def test_named_with_figure_refused():
    _refused(_swap(5, value=1.0), match="no figure")


def test_line_named_twice_refused():
    _refused(entries() + [entries()[1]], match="named twice")


def test_tile_piece_on_stair_code_refused():
    e = entries()
    e[1] = dict(e[1], piece=A.P_TILE, action="BOUND", low=1.0, high=2.0, value=None)
    _refused(e, match="not a HELD line of this piece")


def test_older_view_restores_v3077_return_lines():
    """a return paint line V3.0.77 EXCLUDED is shown to the V3.0.64 .. V3.0.76 checks in its V3.0.76 form (from the 'was'
    of its record); every other line is the same object"""
    from engine.source import arch_v3077 as A77
    ln = _ln("FIN.PAINT", "OP-D1:door:RETURN_PAINT", "BOUNDED_EXPOSURE", rng=(0.0, 1.02))
    was = {"evidence_state": ln["evidence_state"], "measured_net": None, "gross": None,
           "bounded_range": ln["bounded_range"], "rfi": ln["rfi"], "class": "HELD",
           "formula": ln["calculation"]["formula"]}
    ex_ = copy.deepcopy(ln)
    ex_.update(evidence_state="EXCLUDED_WITH_REASON", bounded_range=None, rfi=None)
    ex_["calculation"] = dict(ex_["calculation"], formula="excluded", inputs={A77.REC_KEY: {
        "piece": A77.P_RET, "was": was}})
    other = base()[0]
    v = A.older_view([ex_, other])
    assert v[1] is other
    assert v[0]["evidence_state"] == "BOUNDED_EXPOSURE" and v[0]["bounded_range"] == ln["bounded_range"]
    assert A77.REC_KEY not in v[0]["calculation"]["inputs"] and v[0]["calculation"]["formula"] == ln["calculation"]["formula"]
    assert ex_["evidence_state"] == "EXCLUDED_WITH_REASON"                 # the line itself is untouched
