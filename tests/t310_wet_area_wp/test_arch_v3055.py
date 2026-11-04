"""T-310: ARCH_TAKEOFF_V3.0.55 (wet-area waterproofing fixes + pool layer lines) on the hand-calculated NON-Alsenan
villa W310 (own figures, no drawing):

  Bath B1 3.00 x 2.00 m, one door 0.80 m (wall 0.20), one window W1 0.60 m wide, sill 1.10 m: boundary 10.000 lm incl.
      the door crossing; walls-only upturn (10.000 - 0.800) x 0.20 = 1.840 m2; the engine line deducted the window
      (10.0 - 0.8 - 0.6) x 0.2 = 1.720 -> 1.840 (+0.120); the doorway segment 0.80 x 0.20 = 0.160 stays HELD beside.
      Its glazing termination line on W1 -> NOT APPLICABLE (the membrane runs on under the window).
  Utility U1 box 2.50 x 2.00 = 5.000 m2, a column 0.40 x 0.10 inside it -> 5.000 - 0.040 = 4.960 m2.
  Doors: D-GF-01 (B1 / L1) and D-GF-02 (B2 / B3, two wet rooms) each one transition line; D-GF-02 booked twice
      (a second line from the B3 side) -> NOT APPLICABLE naming the first; D-GF-03 (B4) has none -> HELD BLANK.
  Pool P1 membrane 12.000 m2 + upstand 0 .. 0.600 HELD beside; screed 0.600 m3 + 0 .. 0.030 HELD beside.
Adverse: a window at the upturn, stale before value, a stated value off the policy, a held door line with a value,
a door keyed twice, a duplicate whose door is not keyed to its carrier, a pool layer on a water-side face, a bound
low > high, a value 0, a value in mm, VERIFIED as an input, applied twice, an unknown code, a mirrored / rotated room.
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v30 as A30  # noqa: E402
from engine.source import arch_v3055 as A  # noqa: E402
from engine.source import boq_line as BL  # noqa: E402

PID, REV = "W310-SYNTHETIC", "f" * 64


def _ln(code, eid, state, net=None, rng=None, room=None, unit="m2", floor="GF"):
    return BL.make_line(project_id=PID, revision_set_sha256=REV, item_code=code, unit=unit, evidence_state=state,
                        measured_net=net, bounded_range=rng, element_id=eid, floor=floor, room_id=room,
                        formula=f"synthetic {code} {eid}", rule_id="R-SYN", rule_version="1",
                        geometry_source="SYNTHETIC_FIXTURE", material_state="SOURCE",
                        rfi={"question": "detail", "unlocks": eid} if state == "BLOCKED_RFI" else None,
                        notes="synthetic", **({} if code in BL.ITEMS else
                                              {"item_en": "membrane", "item_ar": "عازل", "trade": "WATERPROOFING"}))


B = {"low": 0.10, "high": 0.20, "basis": "door width x depth range"}
LINES = [
    _ln("FIN.WP.WALL_UPTURN", "B1:UPTURN", "SOURCE_DERIVED", 1.72, room="B1"),
    _ln("FIN.WP.TERMINATION", "B1:W1:GLAZING", "BOUNDED_EXPOSURE", rng={"low": 0.0, "high": 0.6, "basis": "w"},
        room="B1", unit="lm"),
    _ln("FIN.WP.FLOOR", "U1:FLOOR", "SOURCE_DERIVED", 5.0, room="U1"),
    _ln("FIN.WP.DOORWAY_TRANSITION", "B1:D1", "BOUNDED_EXPOSURE", rng=B, room="B1"),
    _ln("FIN.WP.DOORWAY_TRANSITION", "B2:D2", "BOUNDED_EXPOSURE", rng=B, room="B2"),
    _ln("FIN.WP.DOORWAY_TRANSITION", "B3:D2", "BOUNDED_EXPOSURE", rng=B, room="B3"),
    _ln("FIN.WP.DOORWAY", "B4:doorway D3", "SOURCE_DERIVED", 0.16, room="B4"),
    _ln("WP.FOUNDATION.FOOTING_MEMBRANE", "F1:MEMBRANE", "SOURCE_DERIVED", 20.0),
    _ln("FIN.FLOOR.CERAMIC", "B1:FLOOR", "SOURCE_DERIVED", 6.0, room="B1"),
]
ID = {ln["location"]["element_id"]: ln["line_id"] for ln in LINES}


def _src(t):
    return {"task": t, "file": f"research/w310/{t}.csv", "sha256": t[-1] * 64, "merge_commit": "c" * 40,
            "checker_run": f"checker {t} Gate A PASS"}


def entries():
    return [
        {"action": "REVALUE_UPTURN", "line_id": ID["B1:UPTURN"], "before": 1.72, "boundary_lm": 10.0,
         "door_widths_m": [0.8], "openings_not_deducted": [{"kind": "WINDOW", "id": "W1", "sill_m": 1.10}],
         "value": 1.84, "evidence_status": "DRAWING-CONFIRMED", "basis": "walls only", "source_tasks": ["T-A"]},
        {"action": "NOT_APPLICABLE", "line_id": ID["B1:W1:GLAZING"], "item_code": "FIN.WP.TERMINATION",
         "evidence": "window above the upturn", "basis": "inventory", "source_tasks": ["T-A"]},
        {"action": "REVALUE_FLOOR", "line_id": ID["U1:FLOOR"], "before": 5.0, "gross_m2": 5.0,
         "deductions": [{"what": "column C1 0.40 x 0.10", "m2": 0.04, "evidence": "column outline"}],
         "value": 4.96, "evidence_status": "DRAWING-CONFIRMED", "basis": "box less column", "source_tasks": ["T-B"]},
        {"action": "KEY_DOOR", "line_id": ID["B1:D1"], "door_id": "D-GF-01", "basis": "inv", "source_tasks": ["T-A"]},
        {"action": "KEY_DOOR", "line_id": ID["B2:D2"], "door_id": "D-GF-02", "basis": "inv", "source_tasks": ["T-A"]},
        {"action": "NOT_APPLICABLE", "line_id": ID["B3:D2"], "item_code": "FIN.WP.DOORWAY_TRANSITION",
         "door_id": "D-GF-02", "carried_by": ID["B2:D2"], "evidence": "second side", "basis": "inv",
         "source_tasks": ["T-A"]},
        {"action": "ADD_HELD_DOOR", "door_id": "D-GF-03", "rooms": ["B4"], "floor": "GF",
         "template_line": ID["B1:D1"], "doorway_line": ID["B4:doorway D3"], "held_items": "detail not printed",
         "basis": "inv", "source_tasks": ["T-A"]},
        {"action": "ADD_POOL_LAYER", "item_code": "WP.POOL.MEMBRANE", "unit": "m2", "element_id": "P1:MEMBRANE",
         "value": 12.0, "evidence_status": "DRAWING-CONFIRMED", "template_code": "WP.FOUNDATION.FOOTING_MEMBRANE",
         "faces": [{"face": "BASE_UNDERSIDE"}, {"face": "OUTER_WALLS"}],
         "held_part": {"what": "upstand", "low": 0.0, "high": 0.6, "cause": "end not settled"},
         "function_held": "function HELD", "basis": "face ledger", "source_tasks": ["T-C"]},
        {"action": "ADD_POOL_LAYER", "item_code": "WP.POOL.PROTECTION_SCREED", "unit": "m3",
         "element_id": "P1:SCREED", "value": 0.6, "evidence_status": "DRAWING-CONFIRMED",
         "template_code": "WP.FOUNDATION.FOOTING_MEMBRANE",
         "held_part": {"what": "upstand", "low": 0.0, "high": 0.03, "cause": "end not settled"},
         "basis": "0.05 on the faces", "source_tasks": ["T-C"]},
    ]


def doc(ents=None):
    return {"schema": A.INPUTS_SCHEMA, "project_id": PID, "sources": [_src("T-A"), _src("T-B"), _src("T-C")],
            "entries": entries() if ents is None else ents}


def run(d=None, prev=None):
    prev = prev or copy.deepcopy(LINES)
    ch, log = A.changes_for(A.load_inputs(d or doc(), PID), prev)
    return prev, ch, log


def _new():
    prev, ch, _ = run()
    out = [next((c["after"] for c in ch if c["after"]["line_id"] == ln["line_id"]), ln) for ln in prev]
    out += [c["after"] for c in ch if c["action"] == "ADD"]
    return prev, ch, out


def _by(out, eid):
    return next(x for x in out if x["location"]["element_id"] == eid)


# ------------------------------------------------------------------------------------------------- normal case
def test_hand_values():
    prev, ch, out = _new()
    up = _by(out, "B1:UPTURN")
    assert up["measured_net"] == pytest.approx(1.84) and up["evidence_state"] == "SOURCE_DERIVED"
    rec = up["calculation"]["inputs"][A.REC_KEY]
    assert rec["doorway_segments"][0]["state"] == "HELD" and rec["doorway_segments"][0]["if_billed_m2"] == 0.16
    assert _by(out, "U1:FLOOR")["measured_net"] == pytest.approx(4.96)
    t = _by(out, "B1:W1:GLAZING")
    assert t["evidence_state"] == "NOT_APPLICABLE_WITH_EVIDENCE" and t["bounded_range"] is None
    dup = _by(out, "B3:D2")
    assert dup["evidence_state"] == "NOT_APPLICABLE_WITH_EVIDENCE" and ID["B2:D2"] in dup["notes"]
    held = _by(out, "B4:doorway transition D3")
    assert held["evidence_state"] == "BLOCKED_RFI" and held["measured_net"] is None and held["bounded_range"] is None
    mem, scr = _by(out, "P1:MEMBRANE"), _by(out, "P1:SCREED")
    assert (mem["unit"], mem["measured_net"], scr["unit"], scr["measured_net"]) == ("m2", 12.0, "m3", 0.6)
    assert mem["calculation"]["inputs"][A.REC_KEY]["held_part"]["high"] == 0.6
    assert mem["trade"] == "WATERPROOFING" and mem["item_ar"]


def test_one_transition_per_door_and_check():
    prev, ch, out = _new()
    s = A.check_wet_area_wp(out, prev)
    assert s["doors"] == {"D-GF-01": ID["B1:D1"], "D-GF-02": ID["B2:D2"],
                          "D-GF-03": _by(out, "B4:doorway transition D3")["line_id"]}
    assert (s["revalued"], s["not_applicable"], s["keyed_doors"], s["added_held_doors"], s["pool_lines"]) == \
        (2, 2, 2, 1, 2)


def test_keyed_line_quantity_unchanged_and_others_identical():
    prev, ch, out = _new()
    for eid in ("B1:D1", "B2:D2"):
        assert A30._qty(_by(prev, eid)) == A30._qty(_by(out, eid))
    for eid in ("WP.FOUNDATION.FOOTING_MEMBRANE", "B1:FLOOR", "F1:MEMBRANE"):
        if any(x["location"]["element_id"] == eid for x in prev):
            assert A30.line_sha(_by(prev, eid)) == A30.line_sha(_by(out, eid))
    assert len(out) == len(prev) + 3


def test_mirror_rotation_same_run():
    # the run is a length: a mirrored or rotated room gives the same boundary and door widths, so the same value
    for b in (10.0, 2 * (2.0 + 3.0)):
        e = entries()
        e[0]["boundary_lm"] = b
        _, ch, _ = run(doc(e))
        assert ch[0]["after"]["measured_net"] == pytest.approx(1.84)


# ------------------------------------------------------------------------------------------------- adverse cases
def _refused(mut, match):
    e = entries()
    mut(e)
    with pytest.raises(A.InputsError, match=match):
        run(doc(e))


def test_window_at_the_upturn_refused():
    _refused(lambda e: e[0]["openings_not_deducted"][0].update(sill_m=0.15), "cuts the run")


def test_stale_before_refused():
    _refused(lambda e: e[0].update(before=1.70), "stale binding")


def test_value_off_policy_refused():
    _refused(lambda e: e[0].update(value=1.72), "not the policy run")


def test_floor_value_off_closure_refused():
    _refused(lambda e: e[2].update(value=5.0), "not gross - deductions")


def test_held_door_with_value_refused():
    _refused(lambda e: e[6].update(value=0.16), "HELD_WITH_VALUE")


def test_held_door_on_wrong_floor_or_with_a_twin_refused():
    _refused(lambda e: e[6].update(floor="1F"), "is on GF, not 1F")
    e = entries()
    prev = copy.deepcopy(LINES) + [_ln("FIN.WP.DOORWAY_TRANSITION", "B4:doorway transition D3", "BOUNDED_EXPOSURE",
                                       rng=B, room="B4")]
    with pytest.raises(A.InputsError, match="already has transition line"):
        run(doc(e), prev)


def test_door_keyed_twice_refused():
    _refused(lambda e: e[6].update(door_id="D-GF-01"), "two transition lines")


def test_duplicate_without_keyed_carrier_refused():
    _refused(lambda e: e[5].update(carried_by=ID["B1:D1"]), "not keyed to the carrying line")


def test_na_with_value_refused():
    _refused(lambda e: e[1].update(value=0.6), "carries no figure")


def test_pool_on_water_face_refused():
    _refused(lambda e: e[7]["faces"].append({"face": "WATER_WALLS"}), "water-side")


def test_pool_bound_reversed_refused():
    _refused(lambda e: e[7]["held_part"].update(low=0.7), "held low")


def test_zero_and_mm_refused():
    _refused(lambda e: e[7].update(value=0), "never 0")
    _refused(lambda e: e[7].update(value=12000.0), "mm / cm refused")


def test_verified_as_input_refused():
    _refused(lambda e: e[0].update(evidence_status="VERIFIED"), "Checker's word")


def test_wrong_code_and_stale_line_refused():
    _refused(lambda e: e[1].update(item_code="FIN.WP.FLOOR"), "not a code this version")
    _refused(lambda e: e[3].update(line_id="L-" + "0" * 20), "not a candidate line")


def test_applied_twice_refused():
    prev, ch, out = _new()
    with pytest.raises(A.InputsError, match="applied once"):
        A.changes_for(A.load_inputs(doc(), PID), out)


def test_held_door_line_never_zero_in_check():
    prev, ch, out = _new()
    bad = copy.deepcopy(out)
    h = _by(bad, "B4:doorway transition D3")
    h["evidence_state"], h["measured_net"] = "SOURCE_DERIVED", 0.0
    with pytest.raises(ValueError, match="HELD BLANK"):
        A.check_wet_area_wp(bad, prev)


def test_record_on_another_code_refused_in_check():
    prev, ch, out = _new()
    bad = copy.deepcopy(out)
    x = _by(bad, "B1:FLOOR")
    x["calculation"]["inputs"][A.REC_KEY] = {"action": "KEY_DOOR"}
    with pytest.raises(ValueError, match="V3.0.55 record on FIN.FLOOR.CERAMIC"):
        A.check_wet_area_wp(bad, prev)


def test_integrate_identity_and_totals(tmp_path):
    prev, ch, log = run()
    out, ident = A.integrate(prev, ch)
    assert (ident["replaced"], ident["added"], ident["outside_rows"]) == (6, 3, 3)
    names, ident2, led = A.write(tmp_path, prev, ch, log)
    assert "V3_0_55_BOQ_LINES.json" in names and led["released_default"] is False
    import json
    moved = json.loads((tmp_path / "V3_0_55_RUN.json").read_text(encoding="utf-8"))["totals_moved_by_code"]
    assert {k.split("|")[0] for k in moved} <= set(A.WP_CODES)
