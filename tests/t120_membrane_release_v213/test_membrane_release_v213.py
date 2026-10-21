"""T-120: ARCH_TAKEOFF_V2.13 = V2.12 + owner Q-58 A (conditional) released only on a proven physical cutting plan, and a
held open-plan wet zone measured from its printed size typed into the project data file (owner Q-37 A, Q-17 A).
Synthetic, hand-calculated outlines only (none is the development villa). Roll 1.00 x 10.00 m, lap 0.10 m, upturn
0.20 m (UP-WP-001 / 002 / 003).

Fixture R (m): a 10.00 x 6.00 roof less a 7.50 x 3.15 corner notch: (0,0) (10,0) (10,6) (7.5,6) (7.5,2.85) (0,2.85).
Layout ACROSS / OPPOSITE (strips along y, laid from the x = 10 wall): the span x -0.20 .. 10.20 = 10.40 m gives
n = ceil((10.40 - 1.00) / 0.90) + 1 = 12 strips, the last 10.40 - 10.00 + 0.10 = 0.50 m wide. Strip k's sheet covers
x 9.20 - 0.90 (k-1) .. 10.20 - 0.90 (k-1); strips 1-3 reach floor at x >= 7.50 (full height: 6.00 + 0.40 = 6.40 m),
strips 4-12 only the low part (2.85 + 0.40 = 3.25 m). The step edge x = 7.50, y 2.85 .. 6.00 runs along the strips:
its upturn x 7.30 .. 7.50 is covered by strip 3 down to x 7.40 only; x 7.30 .. 7.40 lies in strip 4's slab, which runs
only to y 3.05: uncovered 0.10 x 3.15 = 0.315 m2 (with the mitred corner). Upturn-only strip in band 4: 3.15 + 0.10 end
lap = 3.25 m, need width 0.10 + 0.10 lap = 0.20 m. Main strips 3 x 6.40 + 9 x 3.25 = 48.45 m: 3 rolls 6.40 + 3.25
(0.35 m left each) + 2 rolls 3 x 3.25 (0.25 m left each) = 5 rolls (lower bound ceil(48.45 / 10) = 5). Q-58 B: + 3.25 m
from a roll = 51.70 m > 50 -> 6; Q-58 C (no patch, the strip from a roll) 6; Q-58 A: the 0.20 x 3.25 piece from the
0.50 m strip's 0.50 x 3.25 side trim -> 5 rolls, trim left 0.30 x 3.25. Every other layout needs 6 under every
reading (ALONG 50.70 m, ACROSS / LOWER 51.60 m). V2.12: HELD 5 / 6; V2.13: RELEASED 5, proven, B 6 beside it.

Fixture H (T-096, m): 9.00 x 4.60 less a 2.00 x 2.00 notch: A 5 (0.20 x 2.10 from the 0.40 strip's 0.60 x 3.00 side
trim on roll 5: 3.00 + 3.00 + 3.00 = 9.00 m, 1.00 m left), B 6, C 6 -> V2.13 RELEASED 5.

Fixture X (m): 11.00 x 5.50 less a 1.00 x 3.00 notch, layout ALONG / LOWER: main strips 7 x 10.00 + 3 x 1.50 + 4 x 0.50
= 76.50 m (the 0.50 m wide last strip: 10.00 + 0.50). MEMBRANE_FOLD_V3 counts 8 under Q-58 A with four 1.00 x 1.00
patch pieces: three placed in roll leftovers of the main strips alone (3.50 + 2.50 + 1.50 m) and the fourth packed into
the same rolls. Physically 8 rolls = 80.00 m leave 3.50 m of full-width roll end and the side trim 0.50 x 10.50 (too
narrow for 1.00): the four pieces need 4.00 m -> 8 is NOT possible (the V3 count uses one leftover twice); the proof
refuses it.

Wet zone (m): a dining face with a PANTRY label and a dry one (WET_ZONE_EXTENT_NOT_DRAWN, held in V2.11 / V2.12); the
printed size 2.00 x 1.60 typed (DRAWING-VERIFIED): floor 3.20 m2; membrane 2.40 x 2.00 (0.20 m all round, Q-35 C /
Q-37 A); across the 2.00 m wall: span 2.40 -> 3 strips (1.00, 1.00, 0.60) x 2.00 m = 6.00 m in 1 roll, 4.00 m left;
along: 3 strips x 2.40 = 7.20 m, 1 roll; fewest 1 roll, the shorter 6.00 m layout. The owner's 4.50 x 3.00 pantry size:
13.50 m2, 4 strips x 4.90 m = 19.60 m in 2 rolls (0.40 m left; side trim 0.30 x 4.90 = 1.47 m2); across 6 x 3.40 =
20.40 m, 3 rolls."""

from __future__ import annotations

import copy
import importlib.util
import math
import sys
from pathlib import Path
from unittest import mock

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v212 as AV12                   # noqa: E402
from engine.source import arch_v213 as AV                     # noqa: E402
from engine.source import membrane_cutting_plan_v2 as CP      # noqa: E402
from engine.source import membrane_fold_v3 as F3              # noqa: E402

ROOF_R = [(0, 0), (10, 0), (10, 6), (7.5, 6), (7.5, 2.85), (0, 2.85)]
HELD9 = [(0, 0), (9, 0), (9, 4.6), (2, 4.6), (2, 2.6), (0, 2.6)]
ROOF_X = [(0, 0), (11, 0), (11, 5.5), (1, 5.5), (1, 2.5), (0, 2.5)]
CTX = {"project_id": "synthetic", "revision_set_sha256": "0" * 64, "documents": [{"file": "x.dxf", "sha256": "0"}]}
PID = "synthetic-villa"


def _xf(pts, *, scale=1.0, mirror=False, deg=0.0):
    a = math.radians(deg)
    out = []
    for x, y in pts:
        if mirror:
            x = -x
        out.append(((x * math.cos(a) - y * math.sin(a)) * scale, (x * math.sin(a) + y * math.cos(a)) * scale))
    return out


def _lay(f, direction, start):
    return [x for x in f["layouts_v3"] if x["direction"] == direction and x["start"] == start][0]


def _record(key="WET_ZONE_SIZE_GF_PANTRY", *, value=None, status="DRAWING-VERIFIED", floors=("GF",),
            members=("PANTRY",), project=PID, **extra):
    r = {"key": key, "project": project, "kind": "table", "unit": "none",
         "value": {"length_m": 2.00, "width_m": 1.60} if value is None else value, "status": status,
         "drawing_file": "synthetic.dxf", "drawing_number": "S-01", "revision": "no revision printed",
         "sheet": "ground floor plan", "reference": "printed 200 x 160 beside the label PANTRY",
         "applies_to": {"floors": list(floors), "members": list(members)}, "reviewer_or_source": "test hand reading",
         "entered_by": "TYPED"}
    r.update(extra)
    return r


def _pdf(*records, project=PID):
    return {"schema": "URBAN_PROJECT_DATA_FILE_V1", "project": project, "records": list(records)}


# ------------------------------------------------------------------------------------------------ Q-58 A proof
@pytest.mark.parametrize("variant", [{}, {"mirror": True}, {"deg": 90.0}, {"scale": 1000.0}])
def test_roof_with_step_band_released_on_the_proven_trim(variant):
    """fixture R: V2.12 holds 5 / 6; V2.13 releases 5 (owner Q-58 A) because the 0.20 x 3.25 band piece is placed in
    the 0.50 m strip's own side trim on its own roll, B 6 shown beside; mirrored, turned 90 deg and in millimetres."""
    unit = 0.001 if variant.get("scale") else 1.0
    f = F3.fold(_xf(ROOF_R, **variant), unit_m=unit)
    p12 = CP.purchase(f)
    assert p12["state"] == "HELD_Q58" and p12["rolls_bounded"] == {"low": 5, "high": 6}
    p = AV.purchase(f)
    assert p["state"] == AV.RELEASED_A and p["rolls"] == 5 and p["rolls_bounded"] is None
    assert {k: v["rolls"] for k, v in p["rolls_by_reading"].items()} == {"Q58_A": 5, "Q58_B": 6, "Q58_C": 6}
    pr = p["proof_q58_a"]
    assert pr["proven"] and pr["failures"] == [] and pr["rolls"] == 5 and pr["lower_bound"] == 5
    assert p["direction"] == F3.ACROSS          # the start wall is named in the room frame (a mirror swaps it)
    lens = sorted(q["l"] for r in pr["plan"] for q in r["pieces"] if q["source"] == "ROLL")
    assert lens == [3.25] * 9 + [6.4] * 3
    [o] = pr["offcut_pieces"]
    assert (o["w"], o["l"]) == (0.2, 3.25) and o["source"].startswith("OWN_SIDE_TRIM") and o["y0"] == 0.5
    host = [q for q in pr["plan"][o["roll"] - 1]["pieces"] if q["source"] == "ROLL" and q["w"] == 0.5]
    assert len(host) == 1 and host[0]["x0"] <= o["x0"] and o["x1"] <= host[0]["x1"] + 1e-9
    assert sorted(r["left_m"] for r in pr["plan"]) == [0.25, 0.25, 0.35, 0.35, 0.35]
    assert {(x["kind"], x["width_m"], x["length_m"]) for x in pr["offcuts_left"] if x["kind"] == "SIDE_TRIM"} == {
        ("SIDE_TRIM", 0.3, 3.25)}
    assert abs(p["leftover_m"] - 1.55) < 1e-9 and p["residual_after_m2"] == 0.0
    assert p["cutting_plan_q58_b"] and sum(1 for _r in p["cutting_plan_q58_b"]) == 6


def test_t096_held_fixture_released_on_its_proof():
    f = F3.fold(HELD9)
    p = AV.purchase(f)
    assert p["state"] == AV.RELEASED_A and p["rolls"] == 5
    pr = p["proof_q58_a"]
    [o] = pr["offcut_pieces"]
    assert (o["w"], o["l"], o["roll"]) == (0.2, 2.1, 5) and o["y0"] == 0.4
    assert pr["plan"][4]["used_m"] == 9.0 and pr["plan"][4]["left_m"] == 1.0


def test_v3_count_that_uses_a_leftover_twice_is_refused():
    """fixture X: V3 says 8 under Q-58 A on ALONG / LOWER; by hand 8 rolls leave 3.50 m of roll end and a 0.50 m trim,
    four 1.00 x 1.00 pieces need 4.00 m: not possible -> the proof fails with the piece it cannot place."""
    f = F3.fold(ROOF_X)
    x = _lay(f, F3.ALONG_LONG, F3.LOWER)
    assert x["rolls_by_basis"]["Q58_A"] == 8 and len(x["counts"]["Q58_A"]["pieces_from_own_offcuts"]) == 3
    assert abs(x["main_strip_metres"] - 76.5) < 1e-9
    pr = AV.prove_q58_a(x, f["spec"])
    assert not pr["proven"] and pr["rolls"] == 8
    assert any(m.startswith("OFFCUT:") and "1.000 x 1.000" in m for m in pr["failures"])
    # the area itself is released by V2.12 at 8 on another layout (no piece outside the strips): unchanged
    assert AV.purchase(f) == CP.purchase(f) and CP.purchase(f)["state"] == "RELEASED"


def test_unproven_a_count_stays_held_bounded_never_zero():
    """the fixture H fold with its A piece made 0.20 x 3.50 (longer than every offcut of its rolls: trims 0.60 x 3.00,
    end 1.00 x 1.00): the A count is not proven, the area stays HELD 5 / 6 with the failure named."""
    f = copy.deepcopy(F3.fold(HELD9))
    x = _lay(f, F3.ACROSS, F3.OPPOSITE)
    x["counts"]["Q58_A"]["pieces_from_own_offcuts"][0]["l"] = 3.5
    p = AV.purchase(f)
    assert p["state"] == "HELD_Q58" and p["rolls"] is None and p["rolls_bounded"] == {"low": 5, "high": 6}
    assert "no layout with 5 rolls is proven" in p["reason"] and "0.200 x 3.500" in p["reason"]
    assert p["layouts_tried_q58_a"] and not any(t["proven"] for t in p["layouts_tried_q58_a"])
    # through the lines: a bounded line, never 0
    row = F3.area(floor="RF", room_id="R1", polygon=HELD9, name="ROOF")
    row["fold"] = f
    row.update(system="ROOFS", line_room_id="RF-ROOF-R1")
    t = AV.membrane_table([], [{"fold": row, "code": "ROOF", "floor": "RF", "membrane_m2": 1.0}])
    [ln] = AV.rolls_lines(CTX, t)
    assert ln["evidence_state"] == "BOUNDED_EXPOSURE" and ln["measured_net"] is None
    assert (ln["bounded_range"]["low"], ln["bounded_range"]["high"]) == (5, 6)


def test_a_equal_b_above_c_is_released_at_the_owner_reading():
    """a 10.00 x 6.00 roof less a 1.00 x 4.45 notch: the fewest rolls are A 8 = B 8 and C 7 (C buys corner pieces
    ready-made); V2.12 holds 7 / 8; the owner answered A, so V2.13 releases 8 with its proof and shows C 7."""
    f = F3.fold([(0, 0), (10, 0), (10, 6), (1, 6), (1, 1.55), (0, 1.55)])
    assert CP.purchase(f)["state"] == "HELD_Q58"
    p = AV.purchase(f)
    assert p["state"] == AV.RELEASED_A and p["rolls"] == 8 and p["proof_q58_a"]["proven"]
    assert {k: v["rolls"] for k, v in p["rolls_by_reading"].items()} == {"Q58_A": 8, "Q58_B": 8, "Q58_C": 7}


def test_released_areas_unchanged_and_every_proof_on_v3_fixtures():
    """an area V2.12 releases is returned as V2.12 returns it (the owner's 3 x 4 kitchen, a 12.00 x 5.00 roof); every
    layout of the T-096 fixtures whose A count places pieces in offcuts is either proven or refused with a reason."""
    for poly in ([(0, 0), (4, 0), (4, 3), (0, 3)], [(0, 0), (12, 0), (12, 5), (0, 5)],
                 [(0, 0), (12, 0), (12, 4.6), (4, 4.6), (4, 2.5), (0, 2.5)]):
        f = F3.fold(poly)
        assert AV.purchase(f) == CP.purchase(f)
    for poly in (ROOF_R, HELD9, ROOF_X):
        f = F3.fold(poly)
        for x in f["layouts_v3"]:
            pr = AV.prove_q58_a(x, f["spec"])
            assert pr["proven"] == (not pr["failures"]) and pr["rolls"] == x["rolls_by_basis"]["Q58_A"]


def test_released_line_carries_the_proof_and_the_b_count():
    row = F3.area(floor="RF", room_id="R1", polygon=ROOF_R, name="ROOF")
    row.update(system="ROOFS", line_room_id="RF-ROOF-R1")
    kit = F3.area(floor="GF", room_id="K", polygon=[(0, 0), (4, 0), (4, 3), (0, 3)], roles_lm={"wall": 14.0})
    kit.update(system="WET_AREAS", name_en="Kitchen", name_ar=None)
    roofs = [{"fold": row, "code": "ROOF", "floor": "RF", "membrane_m2": 1.0}]
    t = AV.membrane_table([kit], roofs)
    t12 = AV12.membrane_table([kit], roofs)
    tot = t["systems"]["ROOFS"]["purchase_total"]
    assert tot["rolls_to_buy"] == 5 and tot["complete"] and tot["released_on_q58_a_proof"] == 1
    assert tot["rolls_if_q58_b"] == 6
    assert t12["systems"]["ROOFS"]["purchase_total"]["rolls_to_buy"] is None
    lines, l12 = AV.rolls_lines(CTX, t), AV12.rolls_lines(CTX, t12)
    assert [ln["line_id"] for ln in lines] == [ln["line_id"] for ln in l12]
    k = [ln for ln in lines if ln["location"]["room_id"] == "K"]
    assert k == [ln for ln in l12 if ln["location"]["room_id"] == "K"]
    [r] = [ln for ln in lines if ln["location"]["room_id"] == "RF-ROOF-R1"]
    assert r["evidence_state"] == "SOURCE_DERIVED" and r["measured_net"] == 5
    inp = r["calculation"]["inputs"]
    assert inp["proof_q58_a"]["proven"] and inp["rolls_by_reading"]["Q58_B"]["rolls"] == 6
    assert "Q-58 A" in r["calculation"]["formula"] and "needs 6" in r["calculation"]["formula"]
    rows = AV.purchase_rows(t)
    [pr] = [x for x in rows if x["room_id"] == "R1"]
    assert pr["state"] == "RELEASED" and pr["rolls"] == 5 and pr["rolls_q58_b"] == 6 and "0.20x3.25*" in pr["cutting_plan"]
    assert [x for x in rows if x["room_id"] == "K"] == [x for x in AV12.purchase_rows(t12) if x["room_id"] == "K"]


# ------------------------------------------------------------------------------------------------ typed wet zone
def _held(code="PANTRY", floor="GF", rid="GF-Z1", other="DINING"):
    return {"floor": floor, "room_id": rid, "name_en": None, "name_ar": None, "codes": [other, code],
            "reason": "WET_ZONE_EXTENT_NOT_DRAWN", "basis": "test", "area_of_whole_face_m2": 20.0}


@pytest.mark.parametrize("size,rolls,metres", [((2.0, 1.6), 1, 6.0), ((4.5, 3.0), 2, 19.6), ((3.0, 4.5), 2, 19.6)])
def test_typed_zone_cut_by_the_owner_strip_method(size, rolls, metres):
    zones, left, log = AV.typed_zones([_held()], _pdf(_record(value={"length_m": size[0], "width_m": size[1]})), PID)
    assert left == [] and len(zones) == 1 and log[0]["state"] == "TYPED"
    z = zones[0]
    p = AV.purchase(z["fold"])
    assert p["state"] == "RELEASED" and p["rolls"] == rolls and abs(p["strip_length_m"] - metres) < 1e-9
    assert abs(z["zone_floor_m2"] - size[0] * size[1]) < 1e-9 and z["evidence"] == "WET_ZONE_TYPED_PRINTED_SIZE"
    if size == (4.5, 3.0):
        assert abs(p["leftover_m"] - 0.40) < 1e-9 and abs(p["side_trim_m2"] - 1.47) < 1e-9


@pytest.mark.parametrize("pdf,why", [
    (None, "NO_PROJECT_DATA_FILE"),
    (_pdf(_record(status="ASSUMED")), "ASSUMED"),
    (_pdf(_record(status="HELD", value=None, hold_reason="door width not settled")), "door width not settled"),
    (_pdf(_record(floors=("1F",))), "0 WET_ZONE_SIZE records"),
    (_pdf(_record(members=("KITCHEN",))), "0 WET_ZONE_SIZE records"),
    (_pdf(_record(), _record(key="WET_ZONE_SIZE_2")), "2 WET_ZONE_SIZE records"),
    (_pdf(_record(value={"length_m": 2.0, "width_m": 0.0})), "positive"),
    (_pdf(_record(value={"length_m": "2.00", "width_m": 1.6})), "positive"),
    (_pdf(_record(project="another"), project="another"), "PROJECT_DATA_OTHER_PROJECT"),
    ({"schema": "URBAN_PROJECT_DATA_FILE_V1", "project": PID, "records": [{"key": "x"}]}, "PROJECT_DATA_FILE_INVALID")])
def test_zone_without_one_usable_record_stays_held(pdf, why):
    zones, left, log = AV.typed_zones([_held()], pdf, PID)
    assert zones == [] and left == [_held()] and why in log[0]["reason"] and log[0]["state"] == "HELD"


def test_two_held_zones_with_the_label_on_one_floor_are_not_guessed():
    zones, left, log = AV.typed_zones([_held(), _held(rid="GF-Z2")], _pdf(_record()), PID)
    assert zones == [] and len(left) == 2 and all("ZONE_NOT_IDENTIFIED_ONCE" in x["reason"] for x in log)


def test_zone_lines_floor_released_upturn_held_or_typed():
    [z], _l, _g = AV.typed_zones([_held()], _pdf(_record()), PID)
    fl, up = AV.zone_lines(CTX, [z])
    assert fl["item_code"] == "FIN.WP.FLOOR" and fl["evidence_state"] == "SOURCE_DERIVED" and abs(fl["measured_net"] - 3.2) < 1e-9
    assert fl["source"]["geometry_source"] == "OWNER_FACT" and fl["calculation"]["inputs"]["basis"] == "TYPED_PROJECT_DATA"
    held = AV12.held_wet_lines(CTX, [_held()], set())
    assert [fl["line_id"]] == [ln["line_id"] for ln in held]               # replaces V2.12's held line in place
    assert up["item_code"] == "FIN.WP.WALL_UPTURN" and up["evidence_state"] == "BLOCKED_RFI" and up["measured_net"] is None
    # typed runs: two doorways 0.80 on the 1.60 m sides, the 2.00 m side open, the back wall 2.00: walls 3.60 m
    v = {"length_m": 2.0, "width_m": 1.6, "roles_lm": {"wall": 3.6, "door": 1.6, "other": 2.0}}
    [z2], _l, _g = AV.typed_zones([_held()], _pdf(_record(value=v)), PID)
    lines = AV.zone_lines(CTX, [z2])
    up2 = [ln for ln in lines if ln["item_code"] == "FIN.WP.WALL_UPTURN"][0]
    assert up2["evidence_state"] == "SOURCE_DERIVED" and abs(up2["measured_net"] - 0.72) < 1e-9
    assert up2["line_id"] == up["line_id"]
    # its two doorways have no opening id in the census: the transition count is held, never 0
    tr = AV.door_transition_lines(CTX, [z2], lambda x: {"name_en": None, "name_ar": None})
    assert len(tr) == 1 and tr[0]["evidence_state"] == "BLOCKED_RFI"


# ------------------------------------------------------------------------------------------------ end to end
def _t079():
    spec = importlib.util.spec_from_file_location("t079_helpers", ROOT / "tests" / "t079_arch_v211" / "test_arch_v211.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _pantry_villa(path, *, mirror=False, quarter_turns=0, metres=False):
    """the synthetic villa with its GF BATH face labelled DINING and a second label PANTRY in the same face."""
    import ezdxf
    T = _t079()
    AS = T.AS
    mm = path.with_suffix(".mm.dxf")
    with mock.patch.dict(AS.GF_WORDS, {"BATH": "DINING"}):
        AS.villa(mm, mirror=mirror, quarter_turns=quarter_turns)
    doc = ezdxf.readfile(str(mm))
    xs, ys = [p[0] for p in AS.GF_OUTER], [p[1] for p in AS.GF_OUTER]
    centre = ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2)
    p = AS._xf((10000, 1000), AS.FRAMES["GF"][2], 0, 0, mirror, quarter_turns, centre)
    doc.modelspace().add_text("PANTRY", dxfattribs={"layer": "A-TEXT", "height": 200}).set_placement(p)
    doc.saveas(str(mm))
    return (T._metres(mm, path) if metres else mm), T


def _facts(pdf=None):
    from engine.source import arch_measure as AM
    f = {"schema": AM.FACTS_SCHEMA}
    if pdf is not None:
        f["project_data"] = pdf
    return f


@pytest.mark.parametrize("variant", [{}, {"mirror": True}, {"quarter_turns": 1}, {"metres": True}])
def test_v2_13_pantry_released_from_its_typed_size(tmp_path, variant):
    """the held dining / pantry face: V2.12 holds its floor and rolls; V2.13 with the typed 2.00 x 1.60 releases the
    floor 3.20 m2 and 1 roll on the same line ids, adds the walls-only upturn as held, and changes nothing else."""
    dxf, T = _pantry_villa(tmp_path / "p.dxf", **variant)
    r12, a12 = T._run(dxf, "ARCH_TAKEOFF_V2.12", project_id=PID, facts=_facts())
    r13, a13 = T._run(dxf, "ARCH_TAKEOFF_V2.13", project_id=PID, facts=_facts(_pdf(_record())))
    [h] = a12["v211"]["wet_zones_held"]
    rid = h["room_id"]
    assert a13["v211"]["wet_zones_held"] == [] and a13["v211"]["typed_wet_zones"][0]["state"] == "TYPED"
    q12 = {ln["line_id"]: ln for ln in r12["lines"]}
    q13 = {ln["line_id"]: ln for ln in r13["lines"]}
    changed = sorted(k for k in q12 if k in q13 and q12[k] != q13[k])
    added = sorted(set(q13) - set(q12))
    assert set(q12) <= set(q13)
    assert {q13[k]["item_code"] for k in changed} == {"FIN.WP.FLOOR", "FIN.WP.MEMBRANE_ROLLS"}
    assert all(q13[k]["location"]["room_id"] == rid for k in changed + added)
    assert [q13[k]["item_code"] for k in added] == ["FIN.WP.WALL_UPTURN"]
    fl = [q13[k] for k in changed if q13[k]["item_code"] == "FIN.WP.FLOOR"][0]
    ro = [q13[k] for k in changed if q13[k]["item_code"] == "FIN.WP.MEMBRANE_ROLLS"][0]
    assert abs(fl["measured_net"] - 3.20) < 1e-9 and ro["measured_net"] == 1 and ro["evidence_state"] == "SOURCE_DERIVED"
    assert q12[ro["line_id"]]["evidence_state"] == "BLOCKED_RFI"
    tot = a13["v211"]["membrane_table"]["systems"]["WET_AREAS"]["purchase_total"]
    t12 = a12["v211"]["membrane_table"]["systems"]["WET_AREAS"]["purchase_total"]
    assert tot["rolls_to_buy"] == t12["rolls_to_buy"] + 1 and tot["complete"] and not t12["complete"]
    assert a13["release_report"]["conservation"]["every_line_once"]
    assert a13["run"]["policy"] == "URBAN_BOQ_T120_ARCH_V2_13" and a13["run"]["v2_13"]["released_default"] is False


def test_v2_13_without_project_data_equals_v2_12(tmp_path):
    dxf, T = _pantry_villa(tmp_path / "p.dxf")
    r12, _a12 = T._run(dxf, "ARCH_TAKEOFF_V2.12", project_id=PID, facts=_facts())
    r13, a13 = T._run(dxf, "ARCH_TAKEOFF_V2.13", project_id=PID, facts=_facts())
    assert r12["lines"] == r13["lines"]
    assert a13["v211"]["typed_wet_zones"][0]["reason"] == "NO_PROJECT_DATA_FILE"


@pytest.mark.parametrize("variant", [{}, {"deg": 30.0, "mirror": True, "scale": 0.001}])
def test_v2_13_on_the_drawn_roof_equals_v2_12(tmp_path, variant):
    """the T-079 synthetic roof (released 7 rolls under every reading): V2.12 and V2.13 lines identical."""
    T = _t079()
    dxf = T._roof_plan(tmp_path / "roof.dxf", **variant)
    r12, _a12 = T._run(dxf, "ARCH_TAKEOFF_V2.12", layer_roles=T.ROLES)
    r13, a13 = T._run(dxf, "ARCH_TAKEOFF_V2.13", layer_roles=T.ROLES)
    assert r12["lines"] == r13["lines"]
    from tools import urban_boq_m9 as M9
    files = M9.v21_files(a13)
    assert "MEMBRANE_TABLE_V2_13.json" in files and "MEMBRANE_PURCHASE_V2_13.csv" in files
    assert "MEMBRANE_TABLE_V2_12.json" not in files


def test_v2_13_policy_and_v2_12_untouched():
    pr = AV.policy_record()
    assert pr["method"] == "ARCH_TAKEOFF_V2.13" and pr["knowledge"] == "1.7.0" and pr["builds_on"] == "ARCH_TAKEOFF_V2.12"
    assert pr["released_default"] is False and "Q-58 A conditional (proof)" in pr["owner_answers"]
    assert AV12.METHOD == "ARCH_TAKEOFF_V2.12" and AV12.purchase is CP.purchase and AV.purchase is not CP.purchase
    from tools import urban_boq_m9 as M9
    assert M9.ARCH_METHODS[-1] == "ARCH_TAKEOFF_V2.13" and M9.V213_KNOWLEDGE == "1.7.0"
