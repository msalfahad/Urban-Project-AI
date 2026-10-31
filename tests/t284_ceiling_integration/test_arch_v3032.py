"""T-284: ARCH_TAKEOFF_V3.0.32 (the ceiling line family filled from the checker-merged ceiling ledger and its line
binding) on a hand-calculated NON-Alsenan villa (V284), normal and adverse.

Villa V284, by hand (horizontal gypsum decor 0.15 below the slab; owner bulkhead = free beam edge x 0.15; paint =
decor + bulkhead faces; stair soffit and dome intrados are not ceilings):
  H   GF hall 8.00 x 6.00 = 48.000 m2 line (PROVISIONAL); a flight under the slab 2.40 x 1.50 = 3.600 m2 is stair
      soffit (HELD) -> decor 44.400; beam B1 free edge 6.00 m, decor on the open side -> 6.00 x 0.15 = 0.900 m2
      bulkhead; paint 44.400 + 0.900 = 45.300 m2
  L   1F living 6.00 x 4.00 = 24.000: two lines, normal 20.000 + over the 2.00 x 2.00 void 4.000; dome disc r 1.00 =
      3.141593 = 3.000 over the room + 0.141593 over walls -> decor 24.000 - 3.000 = 21.000 (one surface over both
      lines, split not drawn: one group line, both parents blank); paint 21.000
  S   2F stair hall, BLOCKED line: stair box top held, determinate decor 3.00 x 1.50 = 4.500 (part line); paint 4.500
  D   1F dressing 1.50 x 2.00 = 3.000, no line in the candidate (missing scope): added; paint 3.000
  X   GF exterior soffit 5.000 SOURCE_DERIVED: unchanged; a wall FIN.PAINT line 30.000: unchanged
  dome D1 intrados and stair ST-A soffit (true 3.900 .. 4.100 by two methods): BLANK lines, figures beside
  totals: FIN.CEILING valued 44.400 + 21.000 + 4.500 + 3.000 + 5.000 = 77.900 m2; FIN.CEILING.BULKHEAD 0.900;
  FIN.PAINT.CEILING 45.300 + 21.000 + 4.500 + 3.000 = 73.800; 4 lines restated, 10 added (group + stair-hall part, dressing, 1 bulkhead, 4 paint, dome, stair); every other line identical.
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
from engine.source import arch_v3032 as A  # noqa: E402
from engine.source import boq_line as BL  # noqa: E402

PID, REV = "villa-v284", "e" * 64
DOCS = [{"file": "v284_plans.dxf", "sha256": "c" * 64}]
SRC = [{"task": "T-335", "file": "research/v284/fill.csv", "sha256": "1" * 64, "merge_commit": "a" * 40,
        "checker_run": "checker run 40 (Gate A PASS)"},
       {"task": "T-283", "file": "research/v284/ledger.json", "sha256": "2" * 64, "merge_commit": "b" * 40,
        "checker_run": "checker run 39 (Gate A PASS)"},
       {"task": "T-281", "file": "research/v284/stairs.json", "sha256": "3" * 64, "merge_commit": "c" * 40,
        "checker_run": "checker run 38 (Gate A PASS)"}]
OA_B, OA_P = "owner Q-48 A + Q-43 (bulkhead faces)", "owner Q-57 A mod (6) (paintable surface)"


def _line(code, eid, ev, net=None, room=None, floor="GF", unit="m2"):
    kw = {"rfi": {"question": "held: stair box top"}} if ev == "BLOCKED_RFI" else {}
    return BL.make_line(project_id=PID, revision_set_sha256=REV, item_code=code, unit=unit, evidence_state=ev,
                        measured_net=net, element_id=eid, floor=floor, room_id=room, physical_element=eid,
                        gross=net, formula=f"{eid} {net}", documents=DOCS, rule_id="R", rule_version="1",
                        notes="v284", **kw)


def lines_3031():
    return [_line("FIN.CEILING", "GF-H:ceiling", "PROVISIONAL", 48.0, "GF-H"),
            _line("FIN.CEILING", "1F-L:ceiling", "PROVISIONAL", 20.0, "1F-L", "1F"),
            _line("FIN.CEILING", "1F-L:ceiling over void", "PROVISIONAL", 4.0, "1F-L", "1F"),
            _line("FIN.CEILING", "2F-S:stairwell ceiling", "BLOCKED_RFI", None, "2F-S", "2F"),
            _line("FIN.CEILING", "SOFFIT:GF:X", "SOURCE_DERIVED", 5.0),
            _line("FIN.PAINT", "GF-H:wall paint", "PROVISIONAL", 30.0, "GF-H")]


def _b(lines, eid):
    ln = next(x for x in lines if x["location"]["element_id"] == eid)
    return {"line_id": ln["line_id"], "element_id": eid, "evidence_state": ln["evidence_state"],
            "measured_net": ln["measured_net"]}


def _row(lines, room, floor, eids, decor, bulk=None, role="CEILING", **kw):
    ids = [_b(lines, e) for e in eids]
    r = {"role": role, "line_ids": [b["line_id"] for b in ids], "elements": eids or [f"{room}:ceiling"],
         "room_id": room, "floor": floor, "before_m2": kw.pop("before", None), "bound": ids, "decor_m2": decor,
         "decor_status": "DRAWING-CONFIRMED", "bulkhead_m2": bulk, "bulkhead_source": OA_B if bulk else None,
         "paint_m2": round((decor or 0.0) + (bulk or 0.0), 6) if decor else None, "paint_source": OA_P,
         "held": [{"what": "cove at the wall", "why": "no detail drawn", "beside": None, "status": "HELD"}],
         "source_task": "T-335", "held_source_task": "T-283"}
    r.update(kw)
    return r


def doc(lines=None):
    lines = lines or lines_3031()
    return {"schema": A.INPUTS_SCHEMA, "project_id": PID, "sources": copy.deepcopy(SRC),
            "rows": [_row(lines, "GF-H", "GF", ["GF-H:ceiling"], 44.4, 0.9, before=48.0,
                          held=[{"what": "stair zone", "why": "flight under the slab: stair soffit", "beside": 3.6}]),
                     _row(lines, "1F-L", "1F", ["1F-L:ceiling over void", "1F-L:ceiling"], 21.0, before=24.0,
                          group_cause="one decor surface over the normal and the double-height part; split not drawn"),
                     _row(lines, "2F-S", "2F", ["2F-S:stairwell ceiling"], 4.5, role="STAIRWELL",
                          held=[{"what": "stair box top", "why": "under investigation", "beside": 2.25}]),
                     _row(lines, "1F-D", "1F", [], 3.0),
                     {"role": "EXTERIOR", "line_ids": [_b(lines, "SOFFIT:GF:X")["line_id"]], "action": "UNCHANGED"}],
            "domes": [{"dome": "d1", "element_id": "DOME:D1:intrados", "floor": "1F", "disc_m2": 3.141593,
                       "over_pieces_m2": 3.0, "over_walls_m2": 0.141593, "rooms": "1F-L 3.000",
                       "intrados_s0_beside": "6.283 (hemisphere, scenario only)", "held_reason": "designer: closure",
                       "source_task": "T-283"}],
            "stairs": [{"stair": "ST-A", "element_id": "STAIR:ST-A:soffit", "floor": "GF", "true_lo_m2": 3.9,
                        "true_hi_m2": 4.1, "range_cause": "method O vs D (no owner rule)", "held_rows": 1,
                        "held_plan_m2": 0.3, "held_reason": "not verified whole", "source_task": "T-281"}]}


def run(d=None, lines=None):
    lines = lines or lines_3031()
    inp = A.load_inputs(d or doc(lines), PID)
    ch, log = A.changes_for(inp, lines)
    out, ident = A.integrate(lines, ch)
    return lines, ch, log, out, ident


def _valued(out, code):
    return round(sum(x["measured_net"] for x in out if x["item_code"] == code and x["measured_net"] is not None), 6)


# ------------------------------------------------------------------------------------------------ normal
def test_hand_totals():
    lines, ch, log, out, ident = run()
    assert _valued(out, "FIN.CEILING") == 77.9
    assert _valued(out, "FIN.CEILING.BULKHEAD") == 0.9
    assert _valued(out, "FIN.PAINT.CEILING") == 73.8
    assert ident["replaced"] == 4 and ident["added"] == 10
    assert ident["outside_rows"] == 2          # the exterior soffit and the wall paint line
    assert ident["ceilings"]["rooms"] == 4


def test_room_lines_by_hand():
    lines, ch, log, out, ident = run()
    by = {x["location"]["element_id"]: x for x in out}
    assert by["GF-H:ceiling"]["measured_net"] == 44.4 and by["GF-H:ceiling"]["evidence_state"] == "PROVISIONAL"
    assert by["GF-H:bulkhead"]["measured_net"] == 0.9
    assert by["GF-H:ceiling paint"]["measured_net"] == 45.3
    assert by["1F-D:ceiling"]["measured_net"] == 3.0       # missing scope added
    assert by["2F-S:ceiling#DECOR_PART"]["measured_net"] == 4.5


def test_group_carried_once_parents_blank():
    lines, ch, log, out, ident = run()
    by = {x["location"]["element_id"]: x for x in out}
    g = by["1F-L:ceiling#DECOR_GROUP"]
    assert g["measured_net"] == 21.0
    for e in ("1F-L:ceiling", "1F-L:ceiling over void"):
        p = by[e]
        assert p["evidence_state"] == "BLOCKED_RFI" and p["measured_net"] is None
        assert g["line_id"] in p["rfi"]["question"]
        assert p["line_id"] in g["calculation"]["inputs"][A.REC_KEY]["parents"]


def test_held_lines_blank_never_zero():
    lines, ch, log, out, ident = run()
    by = {x["location"]["element_id"]: x for x in out}
    for e in ("DOME:D1:intrados", "STAIR:ST-A:soffit", "2F-S:stairwell ceiling"):
        assert by[e]["evidence_state"] == "BLOCKED_RFI" and by[e]["measured_net"] is None
        assert by[e]["bounded_range"] is None
        assert " = " not in by[e]["calculation"]["formula"]     # a figure beside reads '->', never '='
    assert "3.9 .. 4.1" in by["STAIR:ST-A:soffit"]["rfi"]["question"]


def test_outside_lines_byte_identical_and_totals_move_only_in_family():
    lines, ch, log, out, ident = run()
    old = {x["line_id"]: x for x in lines}
    for x in out:
        if x["item_code"] in ("FIN.PAINT",) or x["location"]["element_id"] == "SOFFIT:GF:X":
            assert A30.line_sha(x) == A30.line_sha(old[x["line_id"]])
    t0, t1 = A304.code_totals(lines), A304.code_totals(out)
    moved = {k for k in set(t0) | set(t1) if t0.get(k) != t1.get(k)}
    assert all(k.split("|")[0] in A.ITEMS for k in moved)


def test_restated_line_changes_only_quantity_state_basis():
    lines, ch, log, out, ident = run()
    old = {x["line_id"]: x for x in lines}
    for c in ch:
        if c["action"] == "REPLACE":
            a, b = copy.deepcopy(old[c["before"]["line_id"]]), copy.deepcopy(c["after"])
            for x in (a, b):
                for k in A.ROW_KEYS:
                    x.pop(k, None)
            assert a == b


def test_ledger_and_diff(tmp_path):
    lines = lines_3031()
    inp = A.load_inputs(doc(lines), PID)
    ch, log = A.changes_for(inp, lines)
    names, ident, led = A.write(tmp_path, lines, ch, log, inp)
    assert "V3_0_32_BOQ_LINES.json" in names and led["integration_package"] is True
    d = (tmp_path / "V3_0_32_DIFF.csv").read_text(encoding="utf-8")
    assert d.count("ADDED") == 10 and d.count("SAME") == 2


# ------------------------------------------------------------------------------------------------ adverse
def _bad(mut, msg):
    lines = lines_3031()
    d = doc(lines)
    mut(d, lines)
    with pytest.raises((A.InputsError, ValueError), match=msg):
        A.changes_for(A.load_inputs(d, PID), lines)


def test_decor_zero_refused():
    _bad(lambda d, l: d["rows"][0].update(decor_m2=0.0, paint_m2=0.9), "never 0")


def test_held_item_as_zero_refused():
    _bad(lambda d, l: d["rows"][0]["held"].append({"what": "dome", "why": "x", "beside": 0}), "never 0")


def test_paint_not_decor_plus_bulkhead_refused():
    _bad(lambda d, l: d["rows"][0].update(paint_m2=44.4), "not decor")


def test_decor_without_paint_refused():
    _bad(lambda d, l: d["rows"][0].update(paint_m2=None), "without its paint")


def test_bulkhead_without_owner_rule_refused():
    _bad(lambda d, l: d["rows"][0].update(bulkhead_source=None), "owner rule")


def test_group_without_cause_refused():
    _bad(lambda d, l: d["rows"][1].pop("group_cause"), "named cause")


def test_line_in_two_rows_refused():
    def m(d, l):
        d["rows"][3]["line_ids"] = list(d["rows"][0]["line_ids"])
        d["rows"][3]["bound"] = copy.deepcopy(d["rows"][0]["bound"])
    _bad(m, "two rows")


def test_room_in_two_rows_refused():
    _bad(lambda d, l: d["rows"][3].update(room_id="GF-H"), "two rows")


def test_stale_binding_refused():
    _bad(lambda d, l: d["rows"][0]["bound"][0].update(measured_net=47.0), "stale binding")


def test_dome_closure_refused():
    _bad(lambda d, l: d["domes"][0].update(over_walls_m2=0.5), "closure")


def test_stair_range_reversed_refused():
    _bad(lambda d, l: d["stairs"][0].update(true_lo_m2=4.2), "above high")


def test_applied_twice_refused():
    lines, ch, log, out, ident = run()
    with pytest.raises(A.InputsError, match="applied once"):
        A.changes_for(A.load_inputs(doc(lines), PID), out)


def test_valued_stair_soffit_refused():
    lines, ch, log, out, ident = run()
    bad = copy.deepcopy(out)
    s = next(x for x in bad if x["item_code"] == A.STAIR_SOFFIT)
    s["evidence_state"], s["measured_net"], s["rfi"] = "PROVISIONAL", 4.0, None
    with pytest.raises(ValueError, match="stay HELD"):
        A.check_ceilings(bad)


def test_paint_drift_refused():
    lines, ch, log, out, ident = run()
    bad = copy.deepcopy(out)
    next(x for x in bad if x["item_code"] == A.PAINT and x["location"]["room_id"] == "GF-H")["measured_net"] = 44.4
    with pytest.raises(ValueError, match="not its decor"):
        A.check_ceilings(bad)


def test_ceiling_on_stair_element_refused():
    lines, ch, log, out, ident = run()
    bad = copy.deepcopy(out) + [_line("FIN.CEILING", "STAIR:ST-A:soffit", "PROVISIONAL", 4.0)]
    with pytest.raises(ValueError, match="stair / dome soffit"):
        A.check_ceilings(bad)


def test_wrong_unit_added_line_refused():
    lines = lines_3031()
    inp = A.load_inputs(doc(lines), PID)
    ch, log = A.changes_for(inp, lines)
    c = next(c for c in ch if c["after"]["item_code"] == A.BULKHEAD)
    c["after"] = dict(c["after"], unit="lm")
    with pytest.raises(ValueError, match="not a ceiling-family line"):
        A.integrate(lines, ch)


def test_missing_decor_refused():
    _bad(lambda d, l: d["rows"][0].update(decor_m2=None, paint_m2=None), "not a positive figure")
