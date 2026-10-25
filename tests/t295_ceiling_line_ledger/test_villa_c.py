"""R-T295-1 on a hand-calculated NON-Alsenan fixture (villa C, one storey, invented dimensions).

Villa C pieces under the roof slab (hand truth):
  R1 hall 6.000 x 5.000 = 30.000 m2: stair under the slab 2.400 x 1.500 = 3.600 (flight, riser 0.150 / going 0.300:
     true soffit 3.600 x hypot(0.300, 0.150) / 0.300 = 4.024922 by both methods), light well outline 1.000 x 2.000 =
     2.000 (no ceiling), decor 30.000 - 3.600 - 2.000 = 24.400; beam B1 bulkhead (owner method) 5.000 x 0.150 = 0.750.
     Engine line L-R1 = 30.000 - 2.000 (its void deduction) = 28.000.
  R2 bed 4.000 x 3.500 = 14.000: open dome disc r 1.000 = pi = 3.141593 (HELD), decor 14.000 - pi = 10.858407.
     Engine line L-R2 = 14.000.
  R3 lounge 5.000 x 4.000 = 20.000 with a double-height void 2.000 x 2.000: engine lines L-R3a 16.000 (less its own
     void, re-measured in L-R3b) + L-R3b 4.000; decor 20.000, per-line split not established (line group).
  R4 store 3.000 x 2.000 = 6.000: ceiling type not decidable (HELD), no engine line.
Totals: decor DC 24.400 + 10.858407 + 20.000 = 55.258407; owner bulkhead 0.750; void 2.000; stair soffit 4.024922.
"""
from __future__ import annotations

import math
import random
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t295"))
import ceiling_line_ledger as R  # noqa: E402

PI = round(math.pi, 6)
TRUE = round(3.600 * math.hypot(0.300, 0.150) / 0.300, 6)
OWN = "owner rule (fixture): bulkhead 0.150 x free edge"


def F(fid, piece, room, owner, plan, status, carried="plan", **kw):
    f = {"face_id": fid, "physical_id": fid, "piece": piece, "room_id": room, "floor": "GF", "owner": owner,
         "unit": "m2", "plan_m2": plan, "status": status, "source": kw.pop("source", "villa C hand"),
         "held_item": None, "verified_by": None, "range": None, "alternative_of": None}
    f.update(kw)
    f["carried"] = (plan if carried == "plan" else carried) if status in R.DETERMINATE else None
    return f


def faces():
    return [
        F("R1|decor", "R1", "R1", R.DECOR, 24.400, R.DC),
        F("R1|stair", "R1", "R1", R.STAIR_SOFFIT, 3.600, R.DC, carried=TRUE),
        F("R1|well", "R1", "R1", R.VOID, 2.000, R.DC),
        F("R1|B1", None, "R1", R.BULKHEAD, 0.750, R.AOA, source=OWN),
        F("R2|decor", "R2", "R2", R.DECOR, round(14.0 - PI, 6), R.DC),
        F("R2|dome", "R2", "R2", R.DOME, PI, R.HELD, held_item="open dome (designer)"),
        F("R3|decor", "R3", "R3", R.DECOR, 20.000, R.DC),
        F("R4|class", "R4", "R4", R.HELD_CEILING, 6.000, R.HELD, held_item="ceiling type not decidable"),
    ]


LINES = [
    {"line_id": "L-R1", "item_code": "FIN.CEILING", "room_id": "R1", "evidence_state": "PROVISIONAL",
     "measured_net": 28.000, "deductions": [{"m2": 2.000, "what": "void"}]},
    {"line_id": "L-R2", "item_code": "FIN.CEILING", "room_id": "R2", "evidence_state": "PROVISIONAL",
     "measured_net": 14.000, "deductions": []},
    {"line_id": "L-R3a", "item_code": "FIN.CEILING", "room_id": "R3", "evidence_state": "PROVISIONAL",
     "measured_net": 16.000, "deductions": [{"m2": 4.000, "what": "own void (own line)"}]},
    {"line_id": "L-R3b", "item_code": "FIN.CEILING", "room_id": "R3", "evidence_state": "PROVISIONAL",
     "measured_net": 4.000, "deductions": []},
]
PLAN = {"R1|decor": "L-R1", "R1|stair": None, "R1|well": None, "R1|B1": "L-R1", "R2|decor": "L-R2",
        "R2|dome": None, "R3|decor": ["L-R3a", "L-R3b"], "R4|class": None}
BOOKS = {"R1|decor": "L-R1", "R1|stair": "L-R1", "R1|well": "L-R1", "R1|B1": "L-R1", "R2|decor": "L-R2",
         "R2|dome": "L-R2", "R3|decor": "L-R3a + L-R3b", "R4|class": None}
PIECES = {"R1": (30.000, None), "R2": (14.000, None), "R3": (20.000, None), "R4": (6.000, None)}


def ledger(fs=None, plan=None):
    fs = faces() if fs is None else fs
    for f in fs:
        R.check_face(f)
    R.one_owner(fs)
    rows, un = R.bind(fs, LINES, PLAN if plan is None else plan)
    for r in rows:
        r["engine_books_in"] = BOOKS[r["face_id"]]
    return rows, un


def excluded(key):
    ls = [l for l in LINES if l["line_id"] in key.split(" + ")]
    nets = [l["measured_net"] for l in ls]
    return sum(d["m2"] for l in ls for d in l["deductions"] if not any(abs(d["m2"] - n) <= R.TOL for n in nets))


# --- normal -------------------------------------------------------------------------------------------------
def test_hand_truth_totals_by_status():
    rows, un = ledger()
    assert un == []
    assert R.total([r for r in rows if r["owner"] == R.DECOR], R.DC) == pytest.approx(55.258407, abs=1e-6)
    assert R.total([r for r in rows if r["owner"] == R.BULKHEAD], R.AOA) == pytest.approx(0.750, abs=1e-9)
    assert R.total([r for r in rows if r["owner"] == R.STAIR_SOFFIT], R.DC) == pytest.approx(4.024922, abs=1e-6)
    assert R.total([r for r in rows if r["owner"] == R.VOID], R.DC) == pytest.approx(2.000, abs=1e-9)


def test_room_ceiling_in_one_line_and_bulkhead_in_its_room_line():
    rows, _ = ledger()
    r1 = [r for r in rows if r.get("line_id") == "L-R1"]
    assert sorted(r["face_id"] for r in r1) == ["R1|B1", "R1|decor"]
    c = R.line_compare(rows, LINES, "L-R1")
    assert c["engine_m2"] == pytest.approx(28.000)
    # booked plan: decor 24.400 + stair 3.600 + well 2.000 (the bulkhead is vertical, not booked in a plan line)
    assert c["booked_total_m2"] == pytest.approx(30.000, abs=1e-9)
    assert c["engine_m2"] + excluded("L-R1") - c["booked_total_m2"] == pytest.approx(0.0, abs=1e-9)
    assert c["carried_m2"] == {"BULKHEAD / ASSUMED — OWNER-APPROVED": 0.75, "DECOR / DRAWING-CONFIRMED": 24.4}


def test_double_height_room_is_a_line_group_never_a_pro_rata_split():
    rows, _ = ledger()
    g = [r for r in rows if r.get("line_group")]
    assert [r["face_id"] for r in g] == ["R3|decor"] and g[0]["binding"].startswith("LINE GROUP")
    c = R.line_compare(rows, LINES, "L-R3a + L-R3b")
    assert c["engine_m2"] == pytest.approx(20.000) and excluded("L-R3a + L-R3b") == 0  # own void re-measured
    assert c["engine_m2"] - c["booked_total_m2"] == pytest.approx(0.0, abs=1e-9)
    with pytest.raises(R.LedgerError, match="^PRO_RATA"):
        R.pro_rata(g[0], LINES[2:])


def test_piece_closure_zero_and_held_blank_with_plan_shown():
    fs = faces()
    assert all(v == 0 for v in R.piece_closure(fs, PIECES).values())
    rows, _ = ledger()
    for r in rows:
        if r["status"] == R.HELD:
            assert r["carried"] is None and r["plan_m2"] > 0 and r["held_item"]
    assert next(r for r in rows if r["face_id"] == "R4|class")["binding"].startswith("NO_LINE")


def test_order_invariant():
    rows, _ = ledger()
    fs = faces()
    random.Random(7).shuffle(fs)
    rows2, _ = ledger(fs)
    key = lambda r: (r["face_id"], r.get("line_id") or "", r.get("line_group") or "")  # noqa: E731
    assert sorted(rows, key=key) == sorted(rows2, key=key)


def test_declared_shares_split_one_face_over_two_lines():
    fs = faces()
    plan = dict(PLAN, **{"R3|decor": {"L-R3a": 0.8, "L-R3b": 0.2}})
    rows, _ = ledger(fs, plan)
    rr = [r for r in rows if r["face_id"] == "R3|decor"]
    assert sorted((r["line_id"], r["carried"]) for r in rr) == [("L-R3a", 16.0), ("L-R3b", 4.0)]


# --- adverse ------------------------------------------------------------------------------------------------
def test_one_face_in_two_lines_refused():
    with pytest.raises(R.LedgerError, match="^FACE_TWICE"):
        ledger(plan=dict(PLAN, **{"R3|decor": {"L-R3a": 1.0, "L-R3b": 1.0}}))
    fs = faces() + [dict(faces()[0])]
    with pytest.raises(R.LedgerError, match="^(TWO_OWNERS|FACE_TWICE)"):
        R.one_owner(fs)


def test_void_booked_as_ceiling_refused():
    with pytest.raises(R.LedgerError, match="^VOID_AS_CEILING"):
        ledger(plan=dict(PLAN, **{"R1|well": "L-R1"}))


def test_dome_booked_as_ceiling_refused():
    with pytest.raises(R.LedgerError, match="^DOME_AS_CEILING"):
        ledger(plan=dict(PLAN, **{"R2|dome": "L-R2"}))


def test_held_face_as_zero_refused():
    f = F("R4|class", "R4", "R4", R.HELD_CEILING, 6.000, R.HELD, held_item="x")
    f["carried"] = 0.0
    with pytest.raises(R.LedgerError, match="^HELD_AS_ZERO"):
        R.check_face(f)
    with pytest.raises(R.LedgerError, match="^HELD_AS_ZERO"):
        R.total(ledger()[0], R.HELD)


def test_one_stair_soffit_piece_booked_to_decor_and_soffit_refused():
    fs = faces()
    fs.append(F("R1|stair-as-decor", "R1", "R1", R.DECOR, 3.600, R.DC, physical_id="R1|stair"))
    with pytest.raises(R.LedgerError, match="^TWO_OWNERS"):
        R.one_owner(fs)
    # declared as an alternative measurement it is listed, bound to no line and in no total
    fs[-1]["alternative_of"] = "R1|stair"
    R.one_owner(fs)
    plan = dict(PLAN, **{"R1|stair-as-decor": None})
    BOOKS["R1|stair-as-decor"] = None
    try:
        rows, _ = ledger(fs, plan)
    finally:
        BOOKS.pop("R1|stair-as-decor")
    alt = next(r for r in rows if r["face_id"] == "R1|stair-as-decor")
    assert alt["binding"].startswith("ALTERNATIVE") and alt.get("line_id") is None
    assert R.total([r for r in rows if r["owner"] == R.DECOR], R.DC) == pytest.approx(55.258407, abs=1e-6)


def test_range_never_summed_and_conflict_needs_both_readings():
    f = F("R1|stair", "R1", "R1", R.STAIR_SOFFIT, 3.600, R.HELD, held_item="two readings", range=(3.9, 4.1))
    R.check_face(f)
    with pytest.raises(R.LedgerError, match="^RANGE_SUMMED"):
        R.total([f], R.CONFLICT)
    g = F("R1|stair", "R1", "R1", R.STAIR_SOFFIT, 3.600, R.CONFLICT, range=None)
    with pytest.raises(R.LedgerError, match="^CONFLICT_UNSTATED"):
        R.check_face(g)


def test_formwork_line_owns_no_finish_face():
    lines = LINES + [{"line_id": "L-FORM", "item_code": "STR.FORM.SLAB_SOFFIT", "room_id": "R1",
                      "evidence_state": "PROVISIONAL", "measured_net": 30.0, "deductions": []}]
    with pytest.raises(R.LedgerError, match="^FORMWORK_AS_FINISH"):
        R.bind(faces(), lines, dict(PLAN, **{"R1|decor": "L-FORM"}))


def test_unnamed_residual_and_lost_face_refused():
    fs = [f for f in faces() if f["face_id"] != "R1|well"]
    with pytest.raises(R.LedgerError, match="^UNNAMED_RESIDUAL"):
        R.piece_closure(fs, PIECES)
    assert R.piece_closure(fs, dict(PIECES, R1=(30.0, 2.0)))["R1"] == 0


def test_unmatched_line_listed_not_dropped():
    lines = LINES + [{"line_id": "L-R9", "item_code": "FIN.CEILING", "room_id": "R9", "evidence_state": "PROVISIONAL",
                      "measured_net": 9.0, "deductions": []}]
    rows, un = R.bind(faces(), lines, PLAN)
    assert [l["line_id"] for l in un] == ["L-R9"]


def test_units_status_source_and_run_guards():
    with pytest.raises(R.LedgerError, match="^BAD_UNITS"):
        R.check_face(F("x", "R1", "R1", R.DECOR, 24400000.0, R.DC))           # mm2 read as m2
    with pytest.raises(R.LedgerError, match="^BAD_UNITS"):
        R.check_face(dict(F("x", "R1", "R1", R.DECOR, 24.4, R.DC), unit="mm2"))
    with pytest.raises(R.LedgerError, match="^NO_SOURCE"):
        R.check_face(F("x", None, "R1", R.BULKHEAD, 0.75, R.AOA, source=None))
    with pytest.raises(R.LedgerError, match="^NO_CHECKER_RUN"):
        R.check_face(F("x", "R1", "R1", R.DECOR, 24.4, R.VERIFIED))
    with pytest.raises(R.LedgerError, match="^UNPLANNED_FACE"):
        R.bind(faces(), LINES, {k: v for k, v in PLAN.items() if k != "R2|decor"})
