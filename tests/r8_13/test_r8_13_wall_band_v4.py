"""R8.13 §30: WALL_BAND_POLICY_V4 - supporting-line chain identity (V3-D1), structural support of the LOCAL run
(V3-D2) and structural passage sides. Synthetic only: written and frozen BEFORE the V4 Qortuba run (anti-calibration).
The V3-D2 fixture is a synthetic replica of the recorded structure (two outer faces of opposite walls that are
locally mutual nearest only across the core of the perpendicular end wall), in local coordinates and generic handles."""

from __future__ import annotations

import math
import random

from engine.source import room_topology as RT, topology_closures as TC, wall_bands as WB
from tests.r8_8 import helpers as H

POL = TC.POLICY_ID
LAB = [H.text(5, "HALL", 500, 100), H.text(6, "LOBBY", 500, 700)]


def run(parts, texts=LAB):
    return RT.run(H.inp(parts, texts=texts), frame_insert=None, closure_policy=POL)


def box(w=1000, h=800):
    return [H.seg(1, 0, 0, w, 0), H.seg(2, w, 0, w, h), H.seg(3, w, h, 0, h), H.seg(4, 0, h, 0, 0)]


def wall(lower=((0, 600),), upper=((0, 600),), cap=0.0, y=(400, 420), cap_x=None, h0=10):
    p, h = [], h0
    for x0, x1 in lower:
        p.append(H.seg(h, x0, y[0], x1, y[0]))
        h += 1
    for x0, x1 in upper:
        p.append(H.seg(h, x0, y[1], x1, y[1]))
        h += 1
    end = max(x for _, x in lower)
    if cap is not None:
        p.append(H.seg(90, cap_x if cap_x is not None else end, y[0] + cap, cap_x if cap_x is not None else end, y[1],
                       layer="DIM"))
    return p


def est(r):
    return [b for b in r["wall_bands"]["bands"] if b["state"] == WB.ESTABLISHED]


def authorised(r):
    return [c for c in r["topology_closures"]["closures"] if c["release"] == TC.AUTHORISED_FOR_SHADOW]


def handles(b):
    return sorted({f.split("|")[1] for f in b["faces"]})


def rect(h, x0, y0, x1, y1, layer="WALL"):
    """One closed polyline: ONE entity, four sub-parts (the V3-D1 shape)."""
    pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    return [H.part(h, "SEGMENT", (*pts[i], *pts[(i + 1) % 4]), layer=layer, idx=i) for i in range(4)]


def ids(r):
    wb = r["wall_bands"]
    return (sorted(c["chain_id"] for c in wb["chains"]), sorted(b["band_id"] for b in wb["bands"]),
            sorted(s["span_id"] for s in wb["spans"]), sorted(c["closure_id"] for c in r["topology_closures"]["closures"]))


# ------------------------------------------------------------------------------- D1: identity
def test_parallel_opposite_sides_of_one_polyline_with_the_same_extent_have_distinct_ids():
    r = run(box() + rect(50, 300, 300, 700, 340))
    wb = r["wall_bands"]
    sides = [c for c in wb["chains"] if any("|H50|" in f["source"] for f in c["fragments"])]
    assert len(sides) == 4 and len({c["chain_id"] for c in sides}) == 4
    assert wb["chain_id_collisions"] == []
    by_part = {c["fragments"][0]["source"].rsplit("|", 1)[1]: c for c in sides}
    assert by_part["0"]["identity_basis"] == by_part["2"]["identity_basis"] == WB.IDENTITY_LINE
    assert by_part["1"]["identity_basis"] == by_part["3"]["identity_basis"] == WB.IDENTITY_LINE
    assert len({b["band_id"] for b in wb["bands"]}) == len(wb["bands"])                 # no duplicate band id


def test_closed_polyline_sides_never_collide_and_a_unique_face_keeps_the_v3_identity_basis():
    r = run(box() + wall() + rect(50, 800, 100, 900, 200) + rect(60, 100, 600, 160, 640))
    wb = r["wall_bands"]
    assert len({c["chain_id"] for c in wb["chains"]}) == len(wb["chains"]) and wb["chain_id_collisions"] == []
    lone = [c for c in wb["chains"] if any("|H11|" in f["source"] for f in c["fragments"])]
    assert lone and lone[0]["identity_basis"] == WB.IDENTITY_EXTENT


def test_identity_is_stable_under_shuffle_reversal_and_unrelated_insertion():
    base = box() + wall(lower=((0, 300), (300, 600))) + rect(50, 300, 600, 700, 640)
    want = ids(run(base))
    for seed in range(3):
        p = list(base)
        random.Random(seed).shuffle(p)
        assert ids(run(p)) == want
    rev = [x if not (x.identity.source_handle == "50" and x.identity.part_index == 0) else
           H.part(50, "SEGMENT", (700, 600, 300, 600), idx=0) for x in base]
    assert ids(run(rev)) == want                                                      # reversed side 0 of the polyline
    more = ids(run(base + [H.seg(77, 850, 150, 950, 150)]))
    assert more[1] == want[1] and set(want[0]) <= set(more[0])


def test_a_nudged_face_keeps_its_band_id_and_a_resegmented_entity_keeps_chain_and_band_ids():
    a = run(box() + wall())
    moved = [x if x.identity.source_handle != "11" else H.seg(11, 0, 421, 600, 421) for x in box() + wall()]
    assert [b["band_id"] for b in est(run(moved))] == [b["band_id"] for b in est(a)]
    split = [H.part(10, "SEGMENT", (0, 400, 300, 400), idx=0), H.part(10, "SEGMENT", (300, 400, 600, 400), idx=1)]
    b = run(box() + split + [x for x in wall() if x.identity.source_handle != "10"])
    assert ids(a)[:2] == ids(b)[:2]


# ------------------------------------------------------------------------------- D2: structural support
def d2_replica(target_layer="WALL"):
    """Two outer faces (H1 top, H2 bottom) of opposite walls of an enclosure 180 apart; their inner faces stop at the
    inner face of the end wall (H6), so H1 / H2 are locally mutual nearest only across the end wall's core (15 long,
    180 wide). An enclosed single-line room (H20-H23) lies 600 beyond the capped end."""
    S = [(1, 0, 180, 265, 180), (2, 50, 0, 265, 0), (3, 265, 0, 265, 180), (4, 50, 165, 250, 165), (5, 50, 15, 250, 15),
         (6, 250, 15, 250, 165), (7, 50, -400, 50, 0), (8, 50, 15, 50, 55), (9, 50, 145, 50, 165), (10, 35, -400, 35, 55),
         (11, 35, 145, 35, 165), (12, 35, 55, 50, 55), (13, 35, 145, 50, 145), (14, 0, 165, 35, 165), (15, 0, 165, 0, 180)]
    return [H.seg(h, *g) for h, *g in S] + [H.seg(20, 865, -50, 865, 230, layer=target_layer),
                                            H.seg(21, 865, -50, 1000, -50), H.seg(22, 1000, -50, 1000, 230),
                                            H.seg(23, 1000, 230, 865, 230)]


D2_TEXT = [H.text(90, "A", 600, 600)]


def test_v3_d2_regression_no_band_and_no_passage_from_another_walls_core():
    r = run(d2_replica(), D2_TEXT)
    assert not [b for b in r["wall_bands"]["bands"] if handles(b) == ["H1", "H2"]]
    (u,) = [x for x in r["wall_bands"]["unsupported_runs"] if x["separation"] == 180]
    assert u["state"] == WB.UNSUPPORTED and u["local_run"] == 15 and u["raw_chain_overlap"] > u["separation"]
    assert not [p for p in r["passages"] if p["width"] > 500]                         # no 600-long false passage
    assert not any("H20" in p["target"] for p in r["passages"])


def test_the_real_walls_around_the_false_pair_stay_bands():
    r = run(d2_replica(), D2_TEXT)
    got = {tuple(handles(b)) for b in est(r)}
    assert {("H1", "H4"), ("H2", "H5"), ("H3", "H6")} <= got
    assert all(b["evidence"]["structural_support"]["state"] == WB.SELF_SUPPORTED for b in est(r))


def test_an_isolated_short_pairing_is_rejected_even_when_the_raw_overlap_is_long():
    """Two long faces 100 apart are mutual nearest only over a 30 window between two intervening faces."""
    p = box() + [H.seg(10, 0, 300, 700, 300), H.seg(11, 0, 400, 700, 400), H.seg(12, 0, 320, 380, 320),
                 H.seg(13, 410, 320, 700, 320), H.seg(14, 700, 300, 700, 400)]
    r = run(p, [H.text(5, "A", 500, 100), H.text(6, "B", 500, 700)])
    assert not [b for b in r["wall_bands"]["bands"] if handles(b) == ["H10", "H11"] or
                set(handles(b)) == {"H11", "H12", "H13", "H10"}]
    assert any(abs(u["local_run"] - 30) < 1e-6 for u in r["wall_bands"]["unsupported_runs"])


def test_a_long_assembly_keeps_a_short_column_local_span():
    """A short span (10 < 20 separation) next to a column interval is part of ONE supported run."""
    col = [H.part(50, "SEGMENT", g, layer="COLUMN", idx=i) for i, g in
           enumerate([(10, 400, 110, 400), (110, 400, 110, 420), (110, 420, 10, 420), (10, 420, 10, 400)])]
    r = run(box() + wall(lower=((0, 300), (300, 600))) + col)
    (b,) = est(r)
    classes = [(iv["class"], round(iv["s"][0]), round(iv["s"][1])) for iv in b["evidence"]["intervals"]]
    assert classes[0] == (WB.SPAN, 0, 10) and (WB.OBSTACLE_OVERLAP, 10, 110) in classes
    assert b["evidence"]["structural_support"]["state"] == WB.SELF_SUPPORTED
    (c,) = authorised(r)
    assert c["geometry"] == (600, 400, 600, 420)


def wide_column(x0, x1, h=50):
    """A column drawn on the WALL layer, wider than the wall: its sides break local mutual nearest over its interval."""
    pts = [(x0, 395), (x1, 395), (x1, 425), (x0, 425)]
    return [H.part(h, "SEGMENT", (*pts[i], *pts[(i + 1) % 4]), idx=i) for i in range(4)]


def test_a_short_run_inherits_support_across_a_full_width_column_from_the_long_run():
    r = run(box() + wall() + wide_column(10, 110))
    runs = [b for b in est(r) if handles(b) == ["H10", "H11"]]
    st = {(round(b["interval"][0]), round(b["interval"][1])): b["evidence"]["structural_support"] for b in runs}
    assert st[(0, 10)]["state"] == WB.INHERITED_SUPPORT and st[(0, 10)]["across"] == ["REV_A|H50||SEGMENT"]
    assert st[(110, 600)]["state"] == WB.SELF_SUPPORTED


def test_short_runs_with_no_self_supported_neighbour_are_rejected():
    p = box() + [H.seg(10, 0, 400, 120, 400), H.seg(11, 0, 420, 120, 420)] + wide_column(10, 110)
    r = run(p)
    assert not [b for b in r["wall_bands"]["bands"] if handles(b) == ["H10", "H11"]]
    assert len([u for u in r["wall_bands"]["unsupported_runs"] if u["separation"] == 20]) == 2


def test_support_needs_one_closed_structural_entity_a_furniture_loop_never_carries_it():
    """The same wide column drawn as four separate wall lines (no closed entity), with a furniture rectangle drawn
    over it: the short run beside it is UNSUPPORTED; the long run stays a band."""
    pts = [(10, 395), (110, 395), (110, 425), (10, 425)]
    loose = [H.seg(50 + i, *pts[i], *pts[(i + 1) % 4]) for i in range(4)]
    furn = [H.part(60, "SEGMENT", (*pts[i], *pts[(i + 1) % 4]), layer="FURNITURE", idx=i) for i in range(4)]
    r = run(box() + wall() + loose + furn)
    runs = {(round(b["interval"][0]), round(b["interval"][1])) for b in est(r) if handles(b) == ["H10", "H11"]}
    assert (110, 600) in runs and (0, 10) not in runs
    assert any(abs(u["local_run"] - 10) < 1e-6 for u in r["wall_bands"]["unsupported_runs"])


def test_an_unsupported_run_is_never_an_ambiguity_source():
    """A face with a real band on one side and only an unsupported sliver pairing on the other stays ESTABLISHED."""
    p = box() + wall() + [H.seg(30, 200, 300, 600, 300), H.seg(31, 210, 380, 230, 380), H.seg(32, 250, 380, 600, 380)]
    r = run(p, [H.text(5, "A", 500, 100), H.text(6, "B", 500, 700), H.text(7, "C", 100, 350)])
    real = [b for b in r["wall_bands"]["bands"] if handles(b) == ["H10", "H11"]]
    assert real and all(b["state"] == WB.ESTABLISHED for b in real)


# ------------------------------------------------------------------------------- passages
def test_an_open_passage_needs_two_structural_sides():
    p = box() + wall(lower=((0, 300), (300, 600))) + \
        [H.seg(20, 720, 400, 1000, 400), H.seg(21, 720, 420, 1000, 420), H.seg(91, 720, 400, 720, 420, layer="DIM")]
    assert 120 in sorted(round(x["width"]) for x in run(p)["passages"])              # band end -> band end: open
    f = box() + wall() + [H.seg(40, 720, 380, 720, 440, layer="FURNITURE")]
    assert not [x for x in run(f)["passages"] if "H40" in x["target"]]                # furniture is no jamb
    w = box() + wall() + [H.seg(41, 720, 380, 720, 800)]
    assert [x for x in run(w)["passages"] if "H41" in x["target"]]                     # a wall face is


def test_a_false_band_cannot_bootstrap_a_passage_even_to_a_real_wall():
    r = run(d2_replica(), D2_TEXT)
    assert all(p["band_id"] in {b["band_id"] for b in est(r)} for p in r["passages"])
    assert not [p for p in r["passages"] if p["wall_thickness"] == 180]


def test_door_and_window_openings_are_preserved():
    walls = [H.seg(1, 0, 0, 1000, 0), H.seg(2, 1000, 0, 1000, 400), H.seg(3, 1000, 400, 0, 400), H.seg(4, 0, 400, 0, 0),
             H.seg(5, 495, 0, 495, 150), H.seg(6, 505, 0, 505, 150), H.seg(7, 495, 150, 505, 150),
             H.seg(8, 495, 250, 495, 400), H.seg(9, 505, 250, 505, 400), H.seg(10, 495, 250, 505, 250)]
    door = [H.part(20, "ARC", (495, 150, 100, 0.0, math.pi / 2), layer="DOOR", path=("70",)),
            H.seg(21, 495, 150, 495, 250, layer="DOOR", path=("70",))]
    r = run(walls + door, [H.text(5, "A", 250, 200), H.text(6, "B", 750, 200)])
    assert r["openings"]["I70"]["state"] == "CLOSED" and r["passages"] == []
    p = [H.seg(1, 0, 0, 400, 0), H.seg(2, 600, 0, 1000, 0), H.seg(3, 0, 20, 400, 20), H.seg(4, 600, 20, 1000, 20),
         H.seg(5, 400, 0, 400, 20), H.seg(6, 600, 0, 600, 20),
         H.seg(7, 400, 7, 600, 7, layer="GLAZING"), H.seg(8, 400, 13, 600, 13, layer="GLAZING"),
         H.seg(9, 1000, 0, 1000, 800), H.seg(11, 1000, 800, 0, 800), H.seg(12, 0, 800, 0, 0)]
    w = run(p, [H.text(5, "A", 500, 400)])
    assert not [c for c in w["topology_closures"]["closures"] if 400 < c["geometry"][0] < 600]
    assert not [x for x in w["passages"] if 400 <= x["polygon"][0][0] <= 600]


# ------------------------------------------------------------------------------- controls
def test_h2430_class_positive_control_fragmented_face_column_and_proven_cap():
    col = [H.part(50, "SEGMENT", g, layer="COLUMN", idx=i) for i, g in
           enumerate([(100, 400, 200, 400), (200, 400, 200, 420), (200, 420, 100, 420), (100, 420, 100, 400)])]
    r = run(box() + wall(lower=((0, 300), (300, 600))) + col)
    (b,) = est(r)
    assert [e["kind"] for e in b["ends"]] == [WB.RECEIVING_FACE_JUNCTION, WB.ALIGNED_FREE_END]
    (c,) = authorised(r)
    assert c["geometry"] == (600, 400, 600, 420) and c["physical_material"] == "NONE"
    assert c["corroboration"][0]["grade"] == WB.CAP_PROVEN
    (piece,) = c["safety"]["separated_pieces"]
    assert piece["pure_band_interior"]


def test_h2431_class_drafting_disconnect_closes_from_the_face_end_points():
    r = run(box() + wall(lower=((0, 300), (300, 600)), cap=0.92, cap_x=600.05))
    (c,) = authorised(r)
    assert c["corroboration"][0]["grade"] == WB.CAP_CANDIDATE and c["geometry"] == (600, 400, 600, 420)
    assert c["physical_material"] == "NONE" and not c["affects_wall_quantity"]


def test_h1316_class_window_jamb_is_never_a_wall_end():
    p = box() + [H.seg(20, 300, 0.14, 300, 19.86)] + \
        [H.seg(21 + k, 300, y, 500, y, layer="GLAZING") for k, y in enumerate((0.0, 7.0, 13.0, 20.0))]
    assert run(p, [H.text(5, "A", 500, 400)])["topology_closures"]["closures"] == []


def test_a_single_line_wall_is_unaffected():
    r = run(H.two_rooms(), [H.text(5, "A", 250, 200), H.text(6, "B", 750, 200)])
    assert r["wall_bands"]["bands"] == [] and r["wall_bands"]["unsupported_runs"] == []


def test_dimension_and_furniture_rectangles_make_no_band():
    for layer in ("DIM", "FURNITURE"):
        r = run(box() + rect(50, 300, 300, 700, 320, layer=layer))
        assert r["wall_bands"]["bands"] == []


def test_a_column_overlap_blocks_only_its_interval():
    col = [H.part(50, "SEGMENT", g, layer="COLUMN", idx=i) for i, g in
           enumerate([(250, 400, 350, 400), (350, 400, 350, 420), (350, 420, 250, 420), (250, 420, 250, 400)])]
    (b,) = est(run(box() + wall() + col))
    classes = [(iv["class"], round(iv["s"][0]), round(iv["s"][1])) for iv in b["evidence"]["intervals"]]
    assert classes == [(WB.SPAN, 0, 250), (WB.OBSTACLE_OVERLAP, 250, 350), (WB.SPAN, 350, 600)]


def test_a_duplicate_fragment_stays_an_ambiguity():
    r = run(box() + wall(lower=((0, 600), (200, 400))))
    assert not est(r) and not authorised(r)
    assert r["wall_bands"]["bands"] and all(b["state"] == WB.AMBIGUOUS for b in r["wall_bands"]["bands"])


# ------------------------------------------------------------------------------- policy
def test_v4_policy_record():
    rec = WB.policy_record()
    assert WB.POLICY_ID == "WALL_BAND_POLICY_V4" and rec["params"] == WB.PARAMS
    assert rec["support"] == [WB.SELF_SUPPORTED, WB.INHERITED_SUPPORT, WB.UNSUPPORTED]
    assert rec["history"][-1].startswith("V4 (R8.13)") and len(rec["history"]) == 4
    assert "elongation on the raw chain overlap" in rec["never"]
    assert WB.PARAMS["elongation_ratio"] == 1.0 and WB.PARAMS["support_loop_roles"] == ["TOPOLOGY_BOUNDARY",
                                                                                      "STRUCTURAL_OBSTACLE"]
    assert TC.policy_record()["digest"] == "46742c570b4d8a036fd6b7446f28055bfd4e1adbff51966e800e5986ca99ccb2"


def test_a_band_still_carries_no_material():
    r = run(box() + wall())
    assert not any(k in b for b in r["wall_bands"]["bands"] for k in ("wall_length", "area", "material", "plaster"))
    assert WB.policy_record()["means"] == "TOPOLOGY_OBSTACLE_GEOMETRY, not MASONRY_CONFIRMED"
