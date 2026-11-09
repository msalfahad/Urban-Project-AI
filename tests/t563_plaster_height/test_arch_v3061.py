"""T-563: ARCH_TAKEOFF_V3.0.61 (PLASTER_HEIGHT_V1_WIRING) on the hand-calculated NON-Alsenan villa V563 (own figures,
no drawing). Storey interval 3.60, floor build-up above 0.05, slab 0.15 -> plaster H = 3.40 m; finished ceiling (paint
height G1) 3.00 m.

  R1 bedroom, RELEASED at the paint height: face 16.000 lm x 3.00 = 48.000 - door 0.90 x 2.10 = 1.890 - window
      1.50 x 1.20 = 1.800 -> 44.310 m2 (= its paint line 44.310). At its own height: 16.000 x 3.40 = 54.400 - 1.890 -
      1.800 = 50.710 m2; 4.000 lm of the face sits under a roof whose build-up is not printed -> HELD 50.710 .. 50.710
      (+6.400 m2 = 16.000 x 0.40, +14.44 %); the released plaster total falls by 44.310.
  R2 lobby, HELD blank -> HELD 30.000 .. 32.500 (a door of unknown height 0 .. 2.500 m2).
  R3 hall, HELD 20.000 .. 22.000 at the paint height -> 24.000 .. 27.000.
  R4 store, RELEASED 10.000, not in the method table: untouched (byte-identical).
  Paint: R1 44.310 PROVISIONAL, R2 blank, R3 20.000 .. 22.000: every paint line byte-identical.
Code totals FIN.PLASTER|m2: released 54.310 -> 10.000; held 20.000 .. 22.000 -> 104.710 .. 110.210; 4 lines.
Mortar bound beside (T-454 rule: held range x 0.020 m): R1 1.0142, R2 0.6 .. 0.65, R3 0.48 .. 0.54 m3.
Adverse: paint named as a change, a HELD line released, stale binding (net / range / element / class), low > high,
HELD-as-0, millimetre slip, more than double, paint line of another room, line named twice, applied twice, a paint line
moved inside the package, a stray line changed, reordered villa (same result).
"""
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
from engine.source import arch_v3061 as A  # noqa: E402
from engine.source import boq_line as BL  # noqa: E402

PID, REV = "V563-SYNTHETIC", "f" * 64
Q = "roof build-up over the room not printed (designer)"


def _ln(code, eid, state, net=None, room=None, rng=None, gross=None):
    return BL.make_line(project_id=PID, revision_set_sha256=REV, item_code=code, unit="m2", evidence_state=state,
                        measured_net=net, gross=gross if gross is not None else net, element_id=eid, floor="GF",
                        room_id=room, bounded_range=rng, formula=f"synthetic {code} {eid}", rule_id="R-SYN",
                        rule_version="1", geometry_source="SYNTHETIC_FIXTURE", material_state="BY_SPEC",
                        rfi={"question": "detail", "unlocks": eid} if state == "BLOCKED_RFI" else None,
                        notes="synthetic",
                        deductions=[{"id": "D1", "qty": 1.89, "unit": "m2"}, {"id": "W1", "qty": 1.8, "unit": "m2"}]
                        if eid == "R1:PLASTER" else ())


def _r1():
    ln = _ln("FIN.PLASTER", "R1:PLASTER", "PROVISIONAL", 44.31, "R1", gross=48.0)
    ln["calculation"]["inputs"] = {"deduction_listing_v3036": {"action": "LIST_FILL", "deductions_sum": 3.69}}
    return ln


def lines():
    return [
        _r1(),
        _ln("FIN.PLASTER", "R2:PLASTER", "BLOCKED_RFI", None, "R2"),
        _ln("FIN.PLASTER", "R3:PLASTER", "BOUNDED_EXPOSURE", None, "R3", rng={"low": 20.0, "high": 22.0}),
        _ln("FIN.PLASTER", "R4:PLASTER", "PROVISIONAL", 10.0, "R4"),
        _ln("FIN.PAINT", "R1:PAINT", "PROVISIONAL", 44.31, "R1", gross=48.0),
        _ln("FIN.PAINT", "R2:PAINT", "BLOCKED_RFI", None, "R2"),
        _ln("FIN.PAINT", "R3:PAINT", "BOUNDED_EXPOSURE", None, "R3", rng={"low": 20.0, "high": 22.0}),
        _ln("FIN.CEILING", "R1:CEILING", "PROVISIONAL", 16.0, "R1"),
    ]


LN = lines()
ID = {ln["location"]["element_id"]: ln["line_id"] for ln in LN}


def _src(t):
    return {"task": t, "file": f"research/v563/{t}.json", "sha256": t[-1] * 64, "merge_commit": "d" * 40,
            "checker_run": f"checker {t} Gate A PASS"}


def _e(room, cls, after, net=None, rng=None):
    x = {"item_code": "FIN.PLASTER", "element_id": f"{room}:PLASTER", "unit": "m2", "class": cls,
         "measured_net": net}
    if cls == "HELD":
        x.update(low=rng[0] if rng else None, high=rng[1] if rng else None)
    return {"action": "PLASTER_HEIGHT", "line_id": ID[f"{room}:PLASTER"], "source_tasks": ["T-M", "T-W"],
            "expect": x, "room": room, "after": {"low": after[0], "high": after[1]},
            "basis": {"H_floor_m": "3.40", "H_roof_scenario_m": "3.40", "face_lm": "16.000", "face_floor_lm": "12.000",
                      "face_roof_lm": "4.000", "gross_m2": "54.400", "openings_m2": ["3.690", "3.690"],
                      "beam_ends_m2": ["0", "0"]},
            "why_held": f"HELD on the roof build-up over the {room} roof face", "question": Q,
            "paint_line_id": ID[f"{room}:PAINT"]}


def entries():
    return [_e("R1", "RELEASED", (50.71, 50.71), net=44.31),
            _e("R2", "HELD", (30.0, 32.5), rng=None),
            _e("R3", "HELD", (24.0, 27.0), rng=(20.0, 22.0))]


def doc(ents=None, tot=None):
    d = {"schema": A.INPUTS_SCHEMA, "project_id": PID, "sources": [_src("T-M"), _src("T-W")],
         "entries": entries() if ents is None else ents}
    if tot:
        d["expect_totals"] = tot
    return d


def run(d=None, prev=None):
    prev = prev if prev is not None else copy.deepcopy(LN)
    ch, log = A.changes_for(A.load_inputs(d or doc(), PID), prev)
    return prev, ch, log


def _by(out, eid):
    return next(x for x in out if x["location"]["element_id"] == eid)


# ------------------------------------------------------------------------------------------------ normal
def test_hand_values():
    prev, ch, log = run(doc(tot={"released_before_m2": 44.31, "released_after_bound_m2": [50.71, 50.71],
                                 "all_11_after_bound_m2": [104.71, 110.21]}))
    assert log["lines"] == 3
    a = {c["after"]["location"]["element_id"]: c["after"] for c in ch}
    r1 = a["R1:PLASTER"]
    assert r1["evidence_state"] == "BOUNDED_EXPOSURE" and r1["measured_net"] is None and r1["gross"] is None
    assert (r1["bounded_range"]["low"], r1["bounded_range"]["high"]) == (50.71, 50.71)
    assert abs(16.0 * 3.40 - 1.89 - 1.8 - 50.71) < 1e-9 and abs(50.71 - 44.31 - 16.0 * 0.40) < 1e-9
    assert r1["rfi"]["question"] == Q and r1["deductions"] == []
    rec = r1["calculation"]["inputs"][A.REC_KEY]
    assert rec["was"]["measured_net"] == 44.31 and rec["was"]["gross"] == 48.0 and len(rec["was"]["deductions"]) == 2
    assert rec["paint_line_id"] == ID["R1:PAINT"] and rec["was"]["class"] == "RELEASED"
    # the V3.0.36 list record presupposes a valued net: kept in 'was', off the live inputs (its check would fail)
    assert "deduction_listing_v3036" not in r1["calculation"]["inputs"]
    assert rec["was"]["records"]["deduction_listing_v3036"]["deductions_sum"] == 3.69
    assert (a["R2:PLASTER"]["bounded_range"]["low"], a["R2:PLASTER"]["bounded_range"]["high"]) == (30.0, 32.5)
    assert (a["R3:PLASTER"]["bounded_range"]["low"], a["R3:PLASTER"]["bounded_range"]["high"]) == (24.0, 27.0)
    s = A.restated_sums(ch)
    assert s["released_before_m2"] == 44.31 and s["all_after_bound_m2"] == [104.71, 110.21]


def test_integrate_and_totals(tmp_path):
    prev, ch, log = run()
    new, ident = A.integrate(prev, ch)
    assert ident["replaced"] == 3 and ident["outside_rows"] == 5 and ident["outside_rows_identical_to_base"] == 5
    assert ident["plaster_height"] == {"restated": 3, "released_before": 1, "paint_pairs_unchanged": 3}
    for eid in ("R1:PAINT", "R2:PAINT", "R3:PAINT", "R4:PLASTER", "R1:CEILING"):
        assert A30.line_sha(_by(prev, eid)) == A30.line_sha(_by(new, eid))
    t0, t1 = A304.code_totals(prev), A304.code_totals(new)
    assert t0["FIN.PLASTER|m2"]["released"] == 54.31 and t1["FIN.PLASTER|m2"]["released"] == 10.0
    assert (t0["FIN.PLASTER|m2"]["held_low"], t1["FIN.PLASTER|m2"]["held_low"]) == (20.0, 104.71)
    assert (t0["FIN.PLASTER|m2"]["held_high"], t1["FIN.PLASTER|m2"]["held_high"]) == (22.0, 110.21)
    assert t0["FIN.PAINT|m2"] == t1["FIN.PAINT|m2"]
    names, ident2, led = A.write(tmp_path, prev, ch, log)
    run_ = json.loads((tmp_path / "V3_0_61_RUN.json").read_text(encoding="utf-8"))
    assert set(run_["totals_moved_by_code"]) == {"FIN.PLASTER|m2"} and led["integration_package"] is True
    assert ident2["diff"]["vs_base"] == {"SAME": 5, "CHANGED": 3}
    assert "V3_0_61_BOQ_LINES.json" in names and len(led["rows"]) == 3


def test_mortar_bound_beside_rule():
    """the T-454 bound beside a HELD plaster line = held range x 0.020 m (rounded 9): hand figures."""
    prev, ch, _ = run()
    b = {c["after"]["location"]["element_id"]: c["after"]["bounded_range"] for c in ch}
    assert [round(b["R1:PLASTER"][k] * 0.02, 9) for k in ("low", "high")] == [1.0142, 1.0142]
    assert [round(b["R2:PLASTER"][k] * 0.02, 9) for k in ("low", "high")] == [0.6, 0.65]
    assert [round(b["R3:PLASTER"][k] * 0.02, 9) for k in ("low", "high")] == [0.48, 0.54]


def test_reordered_villa_same_result():
    prev, ch, _ = run()
    p2 = list(reversed(copy.deepcopy(LN)))
    _, ch2, _ = run(doc(list(reversed(entries()))), p2)
    k = sorted((c["after"]["line_id"], A30.line_sha(c["after"])) for c in ch)
    assert k == sorted((c["after"]["line_id"], A30.line_sha(c["after"])) for c in ch2)


# ------------------------------------------------------------------------------------------------ adverse
def _bad(mut, match):
    e = entries()
    mut(e)
    with pytest.raises(A.InputsError, match=match):
        run(doc(e))


def test_paint_named_as_a_change_refused():
    def m(e):
        e[0]["expect"]["item_code"] = "FIN.PAINT"
    _bad(m, "not a code this version may change")


def test_released_after_state_refused():
    def m(e):
        e[0]["after"]["state"] = "PROVISIONAL"
    _bad(m, "never released")


@pytest.mark.parametrize("field,value,match", [
    ("measured_net", 44.0, "stale binding"),
    ("element_id", "R9:PLASTER", "stale binding"),
    ("class", "HELD", "stale binding"),
])
def test_stale_binding_refused(field, value, match):
    def m(e):
        e[0]["expect"][field] = value
    _bad(m, match)


def test_stale_held_range_refused():
    def m(e):
        e[2]["expect"]["low"] = 19.0
    _bad(m, "stale binding")


@pytest.mark.parametrize("after,match", [((27.0, 24.0), "low"), ((0.0, 27.0), "HELD-as-0"),
                                         ((50710.0, 50710.0), "unit slip"), ((95.0, 95.0), "more than doubles")])
def test_bad_ranges_refused(after, match):
    def m(e):
        e[0 if after[0] > 30 else 2]["after"] = {"low": after[0], "high": after[1]}
    _bad(m, match)


def test_paint_of_another_room_refused():
    def m(e):
        e[0]["paint_line_id"] = ID["R1:CEILING"]
    _bad(m, "not the room's FIN.PAINT")

    def m2(e):
        e[0]["paint_line_id"] = ID["R2:PAINT"]
        e[1]["paint_line_id"] = ID["R1:PAINT"]
    _bad(m2, "not the room's FIN.PAINT")


def test_named_twice_and_applied_twice_refused():
    def m(e):
        e.append(copy.deepcopy(e[0]))
    _bad(m, "named twice")
    prev, ch, _ = run()
    new, _ = A.integrate(prev, ch)
    with pytest.raises(A.InputsError, match="applied once"):
        A.changes_for(A.load_inputs(doc(), PID), new)


def test_paint_moved_inside_the_package_refused():
    prev, ch, _ = run()
    p = copy.deepcopy(_by(prev, "R1:PAINT"))
    p["notes"] = "moved with the plaster"
    bad = copy.deepcopy(ch) + [{"piece": "X", "action": "CHANGE", "before": _by(prev, "R1:PAINT"), "after": p}]
    with pytest.raises(ValueError, match="not a change this version may make"):
        A.integrate(prev, bad)
    new, _ = A.integrate(prev, ch)
    new = [p if x["line_id"] == p["line_id"] else x for x in new]
    with pytest.raises(ValueError, match="paint line"):
        A.check_plaster_height(new, prev)


def test_held_line_released_refused():
    prev, ch, _ = run()
    new, _ = A.integrate(prev, ch)
    r2 = copy.deepcopy(_by(new, "R2:PLASTER"))
    r2.update(evidence_state="PROVISIONAL", measured_net=31.0, bounded_range=None)
    with pytest.raises(ValueError, match="not HELD"):
        A.check_plaster_height([r2 if x["line_id"] == r2["line_id"] else x for x in new], prev)
    # a HELD plaster line outside the package released next to it is refused too
    r4 = copy.deepcopy(_by(prev, "R2:PLASTER"))
    lines2 = [x for x in prev]
    with pytest.raises(ValueError, match="released"):
        A.check_plaster_height([dict(r4, evidence_state="PROVISIONAL", measured_net=31.0, rfi=None)
                                if x["line_id"] == r4["line_id"] else x for x in lines2], prev)


def test_expect_totals_mismatch_refused():
    with pytest.raises(A.InputsError, match="released_before_m2"):
        run(doc(tot={"released_before_m2": 45.0}))


def test_stray_change_refused(tmp_path):
    prev, ch, log = run()
    new, _ = A.integrate(prev, ch)
    c = copy.deepcopy(_by(prev, "R1:CEILING"))
    c["notes"] = "stray"
    with pytest.raises(ValueError, match="totals moved|differ outside"):
        A.check_totals(A304.code_totals(prev), A304.code_totals([dict(c, measured_net=17.0) if x["line_id"] ==
                                                                  c["line_id"] else x for x in new]), ch)
