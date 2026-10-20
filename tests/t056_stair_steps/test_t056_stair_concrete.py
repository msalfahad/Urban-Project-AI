"""T-056: STAIR_CONCRETE_V1 - stair concrete as separate lines (engine.source.stair_steps_concrete).

Synthetic stairs (not a client drawing). Hand truth worked on paper from the stated census, never from engine output:

  SV dog-leg stair, census in mm, levels +0.00 / +3.20 printed, section S1 counts 20 risers; plan A counts 20, plan B 21.
    riser = 3.20 / 20 = 0.16 m (inside 0.155 - 0.165: no sanity note)
    F1  10 risers, 9 goings, tread 0.28, width 1.10, waist 150 printed in the stair detail
        steps 10 x 1/2 x 0.16 x 0.28 x 1.10 = 10 x 0.02464 = 0.2464 m3
        waist sloped length hypot(9 x 0.28, 10 x 0.16) = hypot(2.52, 1.60) = 2.985029 m
              1.10 x 2.985029 x 0.15 = 0.492530 m3
    L1  intermediate landing 1.20 x 2.30, 150 printed: 1.20 x 2.30 x 0.15 = 0.414 m3
    F2  10 risers, 9 goings, tread 0.28, width 1.10, no thickness printed
        steps 0.2464 m3 (both flights: 20 x 1/2 x 0.16 x 0.28 x 1.10 = 0.4928 m3, the task's acceptance figure)
        waist HELD STAIR_WAIST_NOT_PRINTED (no quantity, never 0)
    FL  floor landing: the floor slab line owns it (no volume here)
    measured = 0.4928 + 0.492530 + 0.414 = 1.399330 m3
    RFI: plan B 21 risers -> riser 3.20 / 21 = 0.152381 m (listed; section wins, owner Q-46 A)
    double-count check: F1's last-riser wedge inside L1 (150 thick): triangle 1/2 x 0.16 x 0.28 = 0.0224 m2 less the part
        below the landing soffit 1/2 x 0.01 x (0.01 x 0.28 / 0.16) = 0.0000875 m2 -> 0.0223125 x 1.10 = 0.02454375 m3
    F2 arrives on the floor: wedge 1/2 x 0.16 x 0.28 x 1.10 = 0.02464 m3 shown (upper bound), never deducted.

  W stair with a winder turn, census in m, levels 0.00 / 3.00, section 18 risers; slab tag "T 16" inside the stair panel.
    riser = 3.00 / 18 = 0.166667 m -> RISER_SANITY note (above 0.165), the value is still the drawing's
    F1 8 risers, 7 goings, tread 0.27, width 1.00: steps 8 x 1/2 x 0.166667 x 0.27 x 1.00 = 0.18 m3
       waist hypot(1.89, 1.333333) = 2.312980 x 1.00 x 0.16 = 0.370077 m3
    W1 3 winder risers, corner 1.00 x 1.00 drawn: HELD (owner Q-51), candidate 1/2 x 0.166667 x 1.00 = 0.083333 shown
    F2 7 risers, 6 goings: steps 7 x 0.0225 = 0.1575 m3; waist hypot(1.62, 1.166667) = 1.996374 x 0.16 = 0.319420 m3
    beams: SB1 0.20 x 0.40 x 3.00 printed = 0.24 m3; SB2 section printed, length / levels not -> HELD

  Adversarial: the same SV stair in metres, a stair with no section (owner Q-50), no printed top level, parts that do not
  add up to the section count, a missing tread and a missing width, a census in an unknown unit, plan riser lines rotated
  37 degrees and mirrored.
"""

import math

import pytest

from engine.source import stair_steps_concrete as SC

def _v(v, src="S1"):
    return {"value": v, "source": src}


def sv(unit="mm"):
    k = 1.0 if unit == "mm" else 0.001
    return {"id": "SV", "unit": unit, "runs": [{
        "id": "GF-1F", "bottom_level": _v(0.0, "section S1 +0.00"), "top_level": _v(3200 * k, "section S1 +3.20"),
        "section_risers": _v(20, "section S1"), "plan_risers": [_v(20, "plan A"), _v(21, "plan B")],
        "parts": [
            {"id": "F1", "kind": "FLIGHT", "risers": 10, "goings": 9, "tread": _v(280 * k, "plan A"),
             "width": _v(1100 * k, "plan A '110'"),
             "thickness": {"value": 150 * k, "source": "stair detail D1 '150'", "basis": "DETAIL"}},
            {"id": "L1", "kind": "LANDING", "length": _v(1200 * k, "plan A '120'"), "width": _v(2300 * k, "plan A"),
             "thickness": {"value": 150 * k, "source": "stair detail D1 '150'", "basis": "DETAIL"}},
            {"id": "F2", "kind": "FLIGHT", "risers": 10, "goings": 9, "tread": _v(280 * k, "plan A"),
             "width": _v(1100 * k, "plan A")},
            {"id": "FL", "kind": "FLOOR_LANDING"}]}]}


def wst():
    tag = {"value": 0.16, "source": "slab plan 'T 16' in the stair panel", "basis": "PANEL_TAG"}
    return {"id": "W", "unit": "m", "runs": [{
        "id": "R", "bottom_level": _v(0.0), "top_level": _v(3.0), "section_risers": _v(18),
        "parts": [
            {"id": "F1", "kind": "FLIGHT", "risers": 8, "goings": 7, "tread": _v(0.27), "width": _v(1.0),
             "thickness": tag},
            {"id": "W1", "kind": "WINDER", "risers": 3, "plan_area": _v(1.0, "plan corner 1.00 x 1.00")},
            {"id": "F2", "kind": "FLIGHT", "risers": 7, "goings": 6, "tread": _v(0.27), "width": _v(1.0),
             "thickness": tag}]}],
        "beams": [{"id": "SB1", "width": 0.20, "depth": 0.40, "length": 3.00, "source": "beam detail"},
                  {"id": "SB2", "width": 0.20, "depth": 0.40, "source": "beam schedule"}],
        "not_present": [{"id": "R2", "evidence": "the section draws no flight above the top floor"}]}


def _one(res, part, element):
    got = [ln for ln in res["lines"] if ln["part"] == part and ln["element"] == element]
    assert len(got) == 1, (part, element, got)
    return got[0]


def test_sv_hand_truth_mm():
    res = SC.measure(sv("mm"))
    assert _one(res, "F1", "STEPS")["quantity_m3"] == pytest.approx(0.2464, abs=1e-9)
    assert _one(res, "F2", "STEPS")["quantity_m3"] == pytest.approx(0.2464, abs=1e-9)
    assert _one(res, "F1", "STEPS")["riser_m"] == pytest.approx(0.16)
    w1 = _one(res, "F1", "WAIST")
    assert w1["status"] == "MEASURED" and w1["sloped_length_m"] == pytest.approx(2.985029, abs=1e-6)
    assert w1["quantity_m3"] == pytest.approx(0.492530, abs=1e-6)
    assert _one(res, "L1", "LANDING")["quantity_m3"] == pytest.approx(0.414, abs=1e-9)
    w2 = _one(res, "F2", "WAIST")
    assert w2["status"] == "HELD" and w2["reason"] == "STAIR_WAIST_NOT_PRINTED" and w2["quantity_m3"] is None
    assert _one(res, "FL", "FLOOR_LANDING")["status"] == "COUNTED_IN_FLOOR_SLAB"
    t = res["totals"]
    assert t["measured_m3"] == pytest.approx(1.399330, abs=1e-6)
    assert t["measured_by_element_m3"]["STEPS"] == pytest.approx(0.4928, abs=1e-9)
    assert t["held"] == ["F2:WAIST:STAIR_WAIST_NOT_PRINTED"]
    assert t["counted_elsewhere"] == ["FL"]
    assert set(t["later_items"]) == {"FORMWORK", "REINFORCEMENT", "MARBLE_TREAD_AND_RISER", "HANDRAILS"}


def test_sv_checks_rfi_and_double_count():
    res = SC.measure(sv("mm"))
    rfi = [c for c in res["checks"] if c["check"] == "RFI_RISER_COUNT"]
    assert len(rfi) == 1 and rfi[0]["plan_risers"] == 21 and rfi[0]["section_risers"] == 20
    assert rfi[0]["riser_plan_m"] == pytest.approx(0.152381, abs=1e-6)
    assert not [c for c in res["checks"] if c["check"] == "RISER_SANITY"]
    wl = [c for c in res["checks"] if c["check"] == "ARRIVAL_WEDGE_IN_LANDING"]
    assert len(wl) == 1 and wl[0]["flight"] == "F1" and wl[0]["landing"] == "L1"
    assert wl[0]["overlap_m3"] == pytest.approx(0.02454375, abs=1e-6)
    wf = [c for c in res["checks"] if c["check"] == "ARRIVAL_WEDGE_AT_FLOOR_SLAB"]
    assert len(wf) == 1 and wf[0]["flight"] == "F2" and wf[0]["wedge_m3"] == pytest.approx(0.02464, abs=1e-9)
    # checks never enter the total
    assert res["totals"]["measured_m3"] == pytest.approx(1.399330, abs=1e-6)


def test_units_mm_and_m_agree():
    a, b = SC.measure(sv("mm")), SC.measure(sv("m"))
    qa = [(ln["part"], ln["element"], ln["status"], ln["quantity_m3"]) for ln in a["lines"]]
    qb = [(ln["part"], ln["element"], ln["status"], ln["quantity_m3"]) for ln in b["lines"]]
    assert len(qa) == len(qb)
    for x, y in zip(qa, qb):
        assert x[:3] == y[:3]
        assert (x[3] is None and y[3] is None) or x[3] == pytest.approx(y[3], abs=1e-9)


def test_winder_stair_beams_and_not_present():
    res = SC.measure(wst())
    assert _one(res, "F1", "STEPS")["quantity_m3"] == pytest.approx(0.18, abs=1e-9)
    assert _one(res, "F2", "STEPS")["quantity_m3"] == pytest.approx(0.1575, abs=1e-9)
    assert _one(res, "F1", "WAIST")["quantity_m3"] == pytest.approx(0.370077, abs=1e-6)
    assert _one(res, "F2", "WAIST")["quantity_m3"] == pytest.approx(0.319420, abs=1e-6)
    assert _one(res, "F1", "WAIST")["rules"][1] == "OWNER-Q-47" and "OWNER-Q-47" in _one(res, "F1", "WAIST")["rules"]
    w = _one(res, "W1", "TURNING_STEPS")
    assert w["status"] == "HELD" and w["reason"] == "WINDER_STEP_RULE_NOT_ANSWERED" and w["quantity_m3"] is None
    assert w["candidate_m3_option_A"] == pytest.approx(0.083333, abs=1e-6)
    assert _one(res, "W1", "TURNING_STEPS_SOFFIT")["status"] == "HELD"
    assert _one(res, "SB1", "STAIR_BEAM")["quantity_m3"] == pytest.approx(0.24, abs=1e-9)
    sb2 = _one(res, "SB2", "STAIR_BEAM")
    assert sb2["status"] == "HELD" and sb2["reason"] == "STAIR_BEAM_LENGTH_OR_LEVELS_NOT_PRINTED"
    assert _one(res, "R2", "STAIR_RUN")["status"] == "NOT_APPLICABLE_WITH_EVIDENCE"
    san = [c for c in res["checks"] if c["check"] == "RISER_SANITY"]
    assert len(san) == 1 and san[0]["riser_m"] == pytest.approx(0.166667, abs=1e-6)
    t = res["totals"]
    assert t["measured_m3"] == pytest.approx(0.18 + 0.1575 + 0.370077 + 0.319420 + 0.24, abs=2e-6)
    assert "W1:TURNING_STEPS:WINDER_STEP_RULE_NOT_ANSWERED" in t["held"]
    assert t["not_present"] == ["R2"]


def test_no_section_holds_steps_and_waists():
    c = wst()
    c["runs"][0]["section_risers"] = None
    c["runs"][0]["plan_risers"] = [_v(18, "plan")]
    res = SC.measure(c)
    for p in ("F1", "F2"):
        for e in ("STEPS", "WAIST"):
            ln = _one(res, p, e)
            assert ln["status"] == "HELD" and ln["reason"] == "RISERS_NOT_COUNTED_ON_A_SECTION"
            assert ln["quantity_m3"] is None and ln["reason_class"] == "REQUIRES_OWNER_DECISION"
    w = _one(res, "W1", "TURNING_STEPS")
    assert w["reason"] == "RISERS_NOT_COUNTED_ON_A_SECTION+WINDER_STEP_RULE_NOT_ANSWERED"
    assert w["candidate_m3_option_A"] is None
    assert not [c for c in res["checks"] if c["check"] == "RFI_RISER_COUNT"]
    # only the beam remains measured: nothing is filled from the plan count
    assert res["totals"]["measured_m3"] == pytest.approx(0.24, abs=1e-9)
    # without the beams nothing is measured: the total is None (held), never 0
    c["beams"] = []
    res = SC.measure(c)
    assert res["totals"]["measured_m3"] is None
    assert SC.measure_all([c, sv()])["totals"]["measured_m3"] == pytest.approx(1.399330, abs=1e-6)


def test_no_printed_top_level_holds_the_run():
    c = sv("mm")
    c["runs"][0]["top_level"] = None
    res = SC.measure(c)
    for p in ("F1", "F2"):
        assert _one(res, p, "STEPS")["reason"] == "RISER_HEIGHT_NOT_ESTABLISHED"
        assert _one(res, p, "STEPS")["quantity_m3"] is None
    # the landing does not depend on the riser: still measured from its printed size and thickness
    assert _one(res, "L1", "LANDING")["quantity_m3"] == pytest.approx(0.414, abs=1e-9)
    assert res["totals"]["measured_m3"] == pytest.approx(0.414, abs=1e-9)


def test_parts_that_do_not_add_up_are_held():
    c = sv("mm")
    c["runs"][0]["parts"][2]["risers"] = 9
    res = SC.measure(c)
    assert _one(res, "F1", "STEPS")["reason"] == "RISER_COUNT_INCONSISTENT"
    assert _one(res, "F2", "STEPS")["reason"] == "RISER_COUNT_INCONSISTENT"


def test_missing_tread_or_width_holds_only_that_flight():
    c = sv("mm")
    c["runs"][0]["parts"][0]["tread"] = None
    c["runs"][0]["parts"][2]["width"] = None
    res = SC.measure(c)
    assert _one(res, "F1", "STEPS")["reason"] == "TREAD_NOT_ESTABLISHED"
    assert _one(res, "F1", "WAIST")["reason"] == "TREAD_NOT_ESTABLISHED"
    assert _one(res, "F2", "STEPS")["reason"] == "WIDTH_NOT_PRINTED"
    assert res["totals"]["measured_m3"] == pytest.approx(0.414, abs=1e-9)
    assert len(res["totals"]["held"]) == 4


def test_thickness_without_source_or_basis_is_not_used():
    c = sv("mm")
    c["runs"][0]["parts"][2]["thickness"] = {"value": 150, "basis": "DETAIL"}          # no source
    c["runs"][0]["parts"][1]["thickness"] = {"value": 150, "source": "usual", "basis": "TYPICAL"}
    res = SC.measure(c)
    assert _one(res, "F2", "WAIST")["reason"] == "STAIR_WAIST_NOT_PRINTED"
    assert _one(res, "L1", "LANDING")["reason"] == "LANDING_NOT_PRINTED"
    assert _one(res, "L1", "LANDING")["plan_area_m2"] == pytest.approx(2.76)


def test_turn_riser_held_and_bad_input():
    c = wst()
    c["runs"][0]["parts"][1] = {"id": "T1", "kind": "TURN_RISER", "risers": 3}
    res = SC.measure(c)
    assert _one(res, "T1", "TURN_RISER")["reason"] == "LANDING_LEVELS_NOT_PRINTED"
    assert _one(res, "F1", "STEPS")["status"] == "MEASURED"
    with pytest.raises(SC.StairCensusError):
        SC.measure(dict(sv(), unit="ft"))
    bad = sv()
    bad["runs"][0]["parts"][0]["risers"] = 9.5
    with pytest.raises(SC.StairCensusError):
        SC.measure(bad)
    with pytest.raises(SC.StairCensusError):
        SC.measure_all([sv(), sv("m")])


def _riser_lines(n, pitch, length, angle_deg, mirror, scale):
    th = math.radians(angle_deg)
    u, v = (math.cos(th), math.sin(th)), (-math.sin(th), math.cos(th))
    segs = []
    for i in range(n):
        a = (i * pitch * v[0], i * pitch * v[1])
        b = (a[0] + length * u[0], a[1] + length * u[1])
        if mirror:
            a, b = (-a[0], a[1]), (-b[0], b[1])
        segs.append((f"L{i}", (a[0] * scale + 7.0 * scale, a[1] * scale), (b[0] * scale + 7.0 * scale, b[1] * scale)))
    return segs


@pytest.mark.parametrize("angle,mirror,unit,scale", [(0, False, "m", 1.0), (37, False, "m", 1.0),
                                                     (37, True, "mm", 1000.0), (90, True, "mm", 1000.0)])
def test_plan_check_rotation_mirror_units(angle, mirror, unit, scale):
    segs = _riser_lines(10, 0.28, 1.10, angle, mirror, scale)
    segs.append(("X", (0.0, 0.0), (5.0 * scale, 0.3 * scale)))        # one stray line, not a riser
    runs = SC.plan_check_from_lines(segs, unit)
    assert len(runs) == 1
    assert runs[0]["lines"] == 10
    assert runs[0]["tread_m"] == pytest.approx(0.28, abs=1e-6)
    assert runs[0]["line_length_m"] == pytest.approx(1.10, abs=1e-6)


def test_arrival_wedge_overlap_cases():
    assert SC.arrival_wedge_overlap(0.16, 0.28, 0.20) == pytest.approx(0.0224)       # plate thicker than the riser
    assert SC.arrival_wedge_overlap(0.16, 0.28, 0.15) == pytest.approx(0.0223125)
    with pytest.raises(SC.StairCensusError):
        SC.arrival_wedge_overlap(0.16, 0.0, 0.15)
