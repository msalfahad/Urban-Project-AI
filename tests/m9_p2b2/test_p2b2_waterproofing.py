"""Phase 2B-2 (Part 3): the waterproofing membrane system - net area, installed membrane and procurement rolls kept
apart; the 0.20 m upturn on eligible wall boundaries only; doorways as transitions with alternatives; penetrations and
corners counted from the drawing and never invented; project rules overriding the 0.20 m upturn and the 0.10 m lap
within their scope; the cutting plan per membrane system. Synthetic geometry; every expected value derived by hand."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import p2b2_fixtures as F                                     # noqa: E402
from engine.source import arch_measure as AM                  # noqa: E402
from engine.source import knowledge as K                      # noqa: E402
from engine.source import waterproofing_system as WS          # noqa: E402

RECT = [(0.0, 0.0), (2.0, 0.0), (2.0, 1.5), (0.0, 1.5)]            # a 2.00 x 1.50 m bathroom (finished faces)
DOOR = [(0, 0.6, 1.4, "DOOR", "D1")]                              # a 0.80 m door in the south wall
PIECE = [{"opening_id": "D1", "width_m": 0.8, "depth_m": 0.2}]
DOORWAY = [{"opening_id": "D1", "width_m": 0.8, "depth_m": 0.2, "other_side": "DRY"}]
CTX = {"project_id": "SYNTHETIC P2B2", "revision_set_sha256": "0" * 64, "documents": []}


def bath(**kw):
    kw.setdefault("gaps", DOOR)
    kw.setdefault("pieces", PIECE)
    kw.setdefault("doorways", DOORWAY)
    return F.area(RECT, **kw)


def lines_of(*areas):
    with K.using("1.1.0"):
        return WS.boq_lines(CTX, list(areas), WS.wp_line)


def test_rectangular_bathroom_hand_calculation():
    """2.00 x 1.50 m, 0.80 m door, wall 0.20 m, roll 1.00 x 10.00 m, lap 0.10 m, upturn 0.20 m.
    A net 3.00 m2. Upturn: perimeter 7.00 - door 0.80 = 6.20 m x 0.20 = 1.24 m2. Doorway continuation 0.80 x 0.20 =
    0.16 m2. Strips along the 2.00 m wall across 1.50 m: 2 (1.00 + 0.90 >= 1.50), the last 0.60 m wide (trim 0.40 m:
    one 0.30 m band lane 2.00 m long + 0.10 m residue). Band 0.20 + 0.10 = 0.30 m wide, 3 lanes per roll width.
    Doorway piece 0.80 x 0.30 m from the 2.00 m lane (1.20 m left). Upturn run 6.20 m (open at the door): 1.20 m
    lane, then a 1.87 m segment (V2.4's own sizing, frozen: the 5.00 m left / 3 lanes + 2 x 0.10, to the cm) in three
    lanes: 1.77 + 1.77 + 1.46 m covered (+0.10 laps), 0.31 m left. Band laid 0.30 x (1.20 + 1.87 + 1.87 + 1.56) =
    1.95 m2. Laps 0.20 (floor) + 0.71 (band) + 0.08 (doorway) = 0.99 m2. Installed B = 3.00 + 0.16 + 1.24 + 0.99 = 5.39
    m2. Consumed 2.00 + 2.00 + 1.87 = 5.87 m2; cutting waste 5.87 - 5.39 = 0.48 m2 (0.20 + 0.187 + 0.093). One roll.
    This test pins the frozen ARCH_TAKEOFF_V2.4 behaviour; its segment follows the engine's formula, not an independent
    derivation. The independent minimum is 1.77 m (3 x 1.67 >= 5.00): consumed 5.77 m2, waste 0.38 m2 - proven in
    tests/m9_p2b3 and used by ARCH_TAKEOFF_V2.5 (defect D-V25-06)."""
    a = bath()
    r = a["row"]
    assert r["A_net_horizontal_m2"] == 3.0
    assert r["upturn"]["eligible_lm"] == 6.2 and r["upturn"]["height_m"] == 0.2 and r["upturn"]["area_m2"] == 1.24
    assert r["doorway_continuation_m2"] == 0.16
    lay = a["layout"]["layout"]
    assert (lay["floor_strips"], lay["last_strip_width_m"], lay["band_width_m"], lay["lanes_per_roll_width"]) == \
        (2, 0.6, 0.3, 3)
    assert [s["length_m"] for s in lay["rolls"][0]["segments"]] == [2.0, 2.0, 1.87]
    assert r["laps_m2"] == 0.99 and r["B_installed_m2"] == 5.39
    assert r["consumed_m2"] == 5.87 and r["cutting_waste_m2"] == 0.48 and r["rolls_if_installed_alone"] == 1
    assert r["direction"] == "ALONG_X"
    with K.using("1.1.0"):
        plan = WS.cutting_plan([a])[0]
    assert plan["rolls"] == 1 and plan["gross_roll_area_m2"] == 10.0 and plan["untouched_roll_tails_m2"] == 4.13
    assert plan["consumed_m2"] == 5.87 and plan["installed_m2"] == 5.39
    # the procurement quantity is never net / roll area: 3.00 / 10 would give one roll by luck, not by the plan
    assert plan["consumed_m2"] > r["A_net_horizontal_m2"] + r["upturn"]["area_m2"]


def test_doorways_are_transitions_not_wall_upturns():
    """V2.3 (rule store UP-WP-002 2.0.0) released 7.00 m x 0.20 = 1.40 m2 including the door; V2.4 releases the
    6.20 m wall upturn and lists the door's transition alternatives, withheld until the detail is known."""
    a = bath()
    tr = [x for x in a["transitions"] if x["kind"] == "DOORWAY"]
    assert len(tr) == 1 and tr[0]["type"] == "DOOR_THRESHOLD_TRANSITION" and tr[0]["state"] == "UNRESOLVED"
    assert {k: v["m2"] for k, v in tr[0]["alternatives"].items()} == {
        "UPTURN_ACROSS_THRESHOLD": 0.16, "CONTINUATION_TERMINATED": 0.0, "JAMB_RETURNS": 0.08}
    lines, unres = lines_of(a)
    codes = {ln["item_code"]: ln for ln in lines}
    assert "FIN.WP.UPTURN" not in codes
    up = codes["FIN.WP.WALL_UPTURN"]
    assert up["measured_net"] == 1.24 and up["evidence_state"] == "SOURCE_DERIVED"
    assert up["rule"]["rule_id"] == "UP-WP-003" and up["rule"]["rule_set"] == "URBAN_KB_1.1.0"
    t = codes["FIN.WP.DOORWAY_TRANSITION"]
    assert t["measured_net"] is None and t["evidence_state"] == "BOUNDED_EXPOSURE"
    assert (t["bounded_range"]["low"], t["bounded_range"]["high"]) == (0.0, 0.16)
    assert any(u["reason"].startswith("DOORWAY_WP_TRANSITION_DETAIL_REQUIRED") for u in unres)
    # with the project detail the transition is released at the selected alternative
    a2 = bath(res=F.resolver(F.rule("PR-1", "UP-WP-DOOR-001", "doorway_detail", "JAMB_RETURNS")))
    t2 = next(ln for ln in lines_of(a2)[0] if ln["item_code"] == "FIN.WP.DOORWAY_TRANSITION")
    assert t2["measured_net"] == 0.08 and t2["evidence_state"] == "SOURCE_DERIVED"
    # a door between two waterproofed areas is a continuation: no transition line at all
    a3 = bath(doorways=[dict(DOORWAY[0], other_side="WATERPROOFED")])
    assert not [ln for ln in lines_of(a3)[0] if ln["item_code"] == "FIN.WP.DOORWAY_TRANSITION"]


def test_l_shaped_bathroom_corners_and_upturn():
    """3.00 x 1.00 + 1.50 x 1.50 L (5.25 m2), perimeter 11.00 m, a 0.80 m door on the west wall: upturn 10.20 m x 0.20
    = 2.04 m2; 5 internal corners and 1 external (the re-entrant corner); 2 upturn ends at the door jambs. The
    membrane engine's generic count (4 + 2 per doorway = 6, all treated alike) is replaced."""
    ring = [(0.0, 0.0), (3.0, 0.0), (3.0, 1.0), (1.5, 1.0), (1.5, 2.5), (0.0, 2.5)]
    a = F.area(ring, gaps=[(5, 0.5, 1.3, "DOOR", "D1")], pieces=PIECE, doorways=DOORWAY)
    assert a["row"]["A_net_horizontal_m2"] == 5.25
    assert a["row"]["upturn"]["eligible_lm"] == 10.2 and a["row"]["upturn"]["area_m2"] == 2.04
    c = a["details"]["corners"]
    assert (c["internal"], c["external"], c["count"], c["state"]) == (5, 1, 6, "WITHHELD")
    assert a["details"]["upturn_ends"] == 2
    assert a["layout"]["layout"]["details"]["corners"]["external"] == 1


def test_internal_columns():
    """a 4.00 x 3.00 m wet room with a 0.40 x 0.40 m column inside: net 12.00 - 0.16 = 11.84 m2; upturn around the room
    (14.00 m) and the column (1.60 m) = 15.60 m; 4 internal + 4 external corners."""
    ring = [(0.0, 0.0), (4.0, 0.0), (4.0, 3.0), (0.0, 3.0)]
    col = [(1.8, 1.3), (2.2, 1.3), (2.2, 1.7), (1.8, 1.7)]
    a = F.area(ring, holes=[col])
    assert a["row"]["A_net_horizontal_m2"] == 11.84 and a["row"]["upturn"]["eligible_lm"] == 15.6
    c = a["details"]["corners"]
    assert (c["internal"], c["external"]) == (4, 4)
    assert len(a["boundary"]["runs"]) == 2 and all(r["closed"] for r in a["boundary"]["runs"])


def test_kitchen_and_pantry_get_membrane_material():
    """the owner wet scope (UP-WET-001) waterproofs kitchens and pantries; V2.3 laid no membrane for them (its
    material step only reads FIN.FLOOR.WET_TILE rooms). V2.4 lays every waterproofed area; a door between two
    waterproofed areas is a continuation, the door to the dry living room a transition."""
    S, M, ents, areas = F.kitchen_plan()
    old = AM.materials(M, None)
    old_rooms = {(m.get("location") or {}).get("room_id") for m in old["materials"]
                 if m["method"].startswith("MEMBRANE")}
    kit, pan, bth = (F.room_named(M, c)["room_id"] for c in ("KITCHEN", "PANTRY", "BATHROOM"))
    assert kit not in old_rooms and pan not in old_rooms and bth in old_rooms
    with K.using("1.1.0"):
        built = {a["room_id"]: WS.build_area(a, F.resolver()) for a in areas}
    assert {kit, pan, bth} <= set(built)
    for rid in (kit, pan, bth):
        assert built[rid]["layout"]["state"] != "BLOCKED", rid
        assert built[rid]["row"]["B_installed_m2"] > built[rid]["row"]["A_net_horizontal_m2"]
    kt = {x["opening_id"]: x["type"] for x in built[kit]["transitions"] if x["kind"] == "DOORWAY"}
    assert sorted(kt.values()) == ["DOORWAY_CONTINUATION", "DOORWAY_CONTINUATION", "DOOR_THRESHOLD_TRANSITION"]
    assert all(x["type"] == "DOORWAY_CONTINUATION" for x in built[pan]["transitions"] if x["kind"] == "DOORWAY")
    # the kitchen's upturn excludes its three door widths (0.90 + 0.80 + 0.80) from its 13.20 m perimeter
    assert built[kit]["row"]["upturn"]["eligible_lm"] == pytest.approx(13.2 - 2.5, abs=1e-6)


def test_balcony_upturn_on_walls_and_open_edge_termination():
    """a 3.00 x 1.50 m balcony: the building wall with a 0.90 m door (south), two side walls, an open north edge.
    UP-WP-003: 0.20 m on the walls only (3.00 - 0.90 + 1.50 + 1.50 = 5.10 m -> 1.02 m2, PROVISIONAL: exterior
    system by specification); the open edge is a 3.00 m termination by detail (withheld); V2.3 asked an RFI."""
    ring = [(0.0, 0.0), (3.0, 0.0), (3.0, 1.5), (0.0, 1.5)]
    a = F.area(ring, gaps=[(0, 1.0, 1.9, "DOOR", "B1"), (2, 0.0, 3.0, "OTHER", None)], codes=("BALCONY",),
               scope="EXTERIOR", doorways=[{"opening_id": "B1", "width_m": 0.9, "depth_m": 0.2, "other_side": "DRY"}])
    assert a["row"]["upturn"]["eligible_lm"] == 5.1 and a["row"]["upturn"]["area_m2"] == 1.02
    lines, unres = lines_of(a)
    up = next(ln for ln in lines if ln["item_code"] == "FIN.WP.WALL_UPTURN")
    assert up["measured_net"] == 1.02 and up["evidence_state"] == "PROVISIONAL"
    term = [ln for ln in lines if ln["item_code"] == "FIN.WP.TERMINATION"]
    assert len(term) == 1 and term[0]["calculation"]["inputs"]["length_m"] == 3.0 and term[0]["measured_net"] is None
    assert any(u["reason"].startswith("WP_TERMINATION_DETAIL_REQUIRED") for u in unres)
    assert not any("EXTERIOR_WP_UPTURN_BY_SPECIFICATION" in u["reason"] for u in unres)
    assert a["system"]["system_id"] == "URBAN_DEFAULT_EXTERIOR"


def test_irregular_roof():
    """a seven-sided roof with parapet walls on six edges and an open edge (no parapet): upturn on the parapets only;
    two roof drains labelled R.D. counted; their treatment withheld."""
    ring = [(0.0, 0.0), (6.0, 0.0), (6.0, 2.0), (8.0, 2.0), (8.0, 5.0), (3.0, 7.0), (0.0, 5.0)]
    ents = {"inserts": [], "texts": [{"id": "T1", "x": 1000.0, "y": 1000.0, "value": "R.D."},
                                     {"id": "T2", "x": 6500.0, "y": 4000.0, "value": "R.D."},
                                     {"id": "T3", "x": 20000.0, "y": 1000.0, "value": "R.D."}]}       # outside
    a = F.area(ring, gaps=[(5, 0.0, (3.0 ** 2 + 2.0 ** 2) ** 0.5, "OTHER", None)], codes=("ROOF",), scope="EXTERIOR",
               ents=ents)
    per = 6 + 2 + 2 + 3 + (5 ** 2 + 2 ** 2) ** 0.5 + (3 ** 2 + 2 ** 2) ** 0.5 + 5
    assert a["row"]["upturn"]["eligible_lm"] == pytest.approx(per - (3 ** 2 + 2 ** 2) ** 0.5, abs=1e-6)
    p = a["details"]["penetrations"]
    assert (p["state"], p["count"], p["by_kind"]) == ("COUNTED_FROM_DRAWING", 2, {"ROOF_DRAIN": 2})
    assert a["layout"]["state"] != "BLOCKED"
    assert a["row"]["A_net_horizontal_m2"] == pytest.approx(44.0, abs=1e-6)          # shoelace: 88 / 2
    c = a["details"]["corners"]
    assert (c["internal"], c["external"], a["details"]["upturn_ends"]) == (4, 1, 2)


def test_multiple_floor_drains_are_counted_and_their_treatment_withheld():
    ents = {"inserts": [{"id": "I1", "name": "FLOOR DRAIN", "x": 500.0, "y": 500.0},
                        {"id": "I2", "name": "FD-100", "x": 1500.0, "y": 1000.0},
                        {"id": "I3", "name": "FLOOR DRAIN", "x": 9000.0, "y": 9000.0}],              # outside
            "texts": [{"id": "T1", "x": 520.0, "y": 560.0, "value": "F.D."}]}                     # its label
    a = bath(ents=ents)
    p = a["details"]["penetrations"]
    assert (p["state"], p["count"], p["by_kind"]) == ("COUNTED_FROM_DRAWING", 2, {"FLOOR_DRAIN": 2})
    lines, unres = lines_of(a)
    pen = next(ln for ln in lines if ln["item_code"] == "FIN.WP.PENETRATION")
    assert pen["measured_net"] == 2 and pen["calculation"]["inputs"]["treatment_quantity"] is None
    assert any(u["reason"].startswith("WP_PENETRATION_DETAIL_REQUIRED") for u in unres)
    # a project detail gives the treatment: 2 patches of 0.50 x 0.50 m
    a2 = bath(ents=ents, res=F.resolver(F.rule("PR-1", "UP-WP-004", "penetration_treatment",
                                               {"kind": "PATCH", "size_m": [0.5, 0.5]})))
    assert a2["details"]["penetrations"]["quantity"] == {"pcs": 2, "m2": 0.5}
    # nothing drawn: never zero
    a3 = bath()
    assert a3["details"]["penetrations"]["count"] is None
    pen3 = next(ln for ln in lines_of(a3)[0] if ln["item_code"] == "FIN.WP.PENETRATION")
    assert pen3["measured_net"] is None and pen3["evidence_state"] == "BLOCKED_RFI"


def test_pipe_penetrations():
    ents = {"inserts": [{"id": "I1", "name": "PIPE SLEEVE 110", "x": 800.0, "y": 700.0}],
            "texts": [{"id": "T1", "x": 1700.0, "y": 300.0, "value": "S.V.P"}]}
    a = bath(ents=ents)
    assert a["details"]["penetrations"]["by_kind"] == {"PIPE_PENETRATION": 2}


def test_project_upturn_overrides_the_standard():
    a = bath(res=F.resolver(F.rule("PR-1", "UP-WP-003", "upturn_h_m", 0.30)))
    r = a["row"]
    assert r["upturn"]["height_m"] == 0.3 and r["upturn"]["height_state"] == "PROJECT_SPECIFIED"
    assert r["upturn"]["height_urban_m"] == 0.2 and r["upturn"]["area_m2"] == pytest.approx(1.86)
    assert a["layout"]["layout"]["band_width_m"] == 0.4 and a["layout"]["layout"]["lanes_per_roll_width"] == 2
    up = next(ln for ln in lines_of(a)[0] if ln["item_code"] == "FIN.WP.WALL_UPTURN")
    assert up["measured_net"] == pytest.approx(1.86) and up["calculation"]["inputs"]["project_rule_ids"] == ["PR-1"]


def test_project_overlap_overrides_the_standard():
    """lap 0.15 m: strips across 1.50 m: 1.00 + 0.85 >= 1.50 -> 2, the last 0.65 m; floor lap 0.15 x 2.00 = 0.30 m2."""
    base = bath()
    a = bath(res=F.resolver(F.rule("PR-1", "UP-WP-002", "lap_m", 0.15)))
    assert a["layout"]["layout"]["last_strip_width_m"] == 0.65 and a["layout"]["layout"]["band_width_m"] == 0.35
    assert a["row"]["laps_m2"] > base["row"]["laps_m2"]
    assert a["basis"]["lap_m"]["state"] == "PROJECT_SPECIFIED" and a["basis"]["lap_m"]["urban_value"] == 0.1


def test_both_strip_orientations_are_evaluated_and_the_choice_is_deterministic():
    """2.40 x 2.50 m (6.00 m2): strips along 2.40 m use one roll (9.90 m cut), along 2.50 m they need 10.17 m: two
    rolls. The selection takes the one-roll layout, every time, whatever the room's orientation."""
    ring = [(0.0, 0.0), (2.4, 0.0), (2.4, 2.5), (0.0, 2.5)]
    a = F.area(ring)
    alts = {x["direction"]: x for x in a["layout"]["layout"]["alternatives"]}
    assert len(alts) == 2
    assert sorted(x["rolls"] for x in alts.values()) == [1, 2]
    assert a["row"]["rolls_if_installed_alone"] == 1 and a["row"]["consumed_m2"] == 9.9
    turned = F.area([(0.0, 0.0), (2.5, 0.0), (2.5, 2.4), (0.0, 2.4)])
    assert turned["row"]["rolls_if_installed_alone"] == 1 and turned["row"]["consumed_m2"] == 9.9
    assert json.dumps(F.area(ring)["row"], sort_keys=True) == json.dumps(a["row"], sort_keys=True)


def test_same_area_different_shape_changes_material_and_rolls():
    """6.00 m2 each: 2.40 x 2.50 m -> 1 roll; 3.00 x 2.00 m and 6.00 x 1.00 m -> 2 rolls; the installed membrane
    differs with the perimeter (9.80 / 10.00 / 14.00 m of upturn)."""
    rows = {}
    for name, (x, y) in {"A": (2.4, 2.5), "B": (3.0, 2.0), "C": (6.0, 1.0)}.items():
        rows[name] = F.area([(0.0, 0.0), (x, 0.0), (x, y), (0.0, y)], room_id=f"GF-{name}")["row"]
    assert {k: round(v["A_net_horizontal_m2"], 6) for k, v in rows.items()} == {"A": 6.0, "B": 6.0, "C": 6.0}
    assert {k: v["upturn"]["eligible_lm"] for k, v in rows.items()} == {"A": 9.8, "B": 10.0, "C": 14.0}
    assert {k: v["rolls_if_installed_alone"] for k, v in rows.items()} == {"A": 1, "B": 2, "C": 2}
    assert len({v["B_installed_m2"] for v in rows.values()}) == 3


def test_partial_roll_reuse_only_with_a_cutting_plan():
    """two 1.20 x 1.00 m WCs of one system: each alone uses one roll and leaves most of it untouched; the project plan
    cuts both from one roll - the reuse is shown piece by piece."""
    a1 = F.area([(0.0, 0.0), (1.2, 0.0), (1.2, 1.0), (0.0, 1.0)], room_id="GF-W1")
    a2 = F.area([(5.0, 0.0), (6.2, 0.0), (6.2, 1.0), (5.0, 1.0)], room_id="GF-W2")
    with K.using("1.1.0"):
        plan = WS.cutting_plan([a1, a2])
    assert len(plan) == 1
    p = plan[0]
    assert p["rolls_if_each_area_alone"] == 2 and p["rolls"] == 1
    assert p["cutting_plan"][0]["areas"] == ["GF-W1", "GF-W2"]
    assert p["consumed_m2"] == pytest.approx(a1["row"]["consumed_m2"] + a2["row"]["consumed_m2"])
    # narrow offcuts are not retained without a project minimum (no reuse the plan does not show)
    assert a1["row"]["reusable_offcuts_m2"] == 0.0


def test_missing_detail_blocks_the_quantity():
    """two project upturn heights that disagree: the upturn is CONFLICT_REVIEW, its line BLOCKED_RFI, the layout and
    the procurement of the area withheld - never one of the two values silently."""
    a = bath(res=F.resolver(F.rule("PR-1", "UP-WP-003", "upturn_h_m", 0.30),
                            F.rule("PR-2", "UP-WP-003", "upturn_h_m", 0.25, kind="SPECIFICATION")))
    assert a["basis"]["upturn_h_m"]["state"] == "CONFLICT_REVIEW" and a["basis"]["upturn_h_m"]["value"] is None
    assert a["layout"]["state"] == "BLOCKED" and a["layout"]["blocked_by"].startswith("WP_LAYOUT_BLOCKED")
    lines, unres = lines_of(a)
    up = next(ln for ln in lines if ln["item_code"] == "FIN.WP.WALL_UPTURN")
    assert up["measured_net"] is None and up["evidence_state"] == "BLOCKED_RFI"
    assert any(u["reason"].startswith("PROJECT_RULE_CONFLICT") for u in unres)
    with K.using("1.1.0"):
        assert WS.cutting_plan([a]) == []


def test_separate_systems_are_never_combined():
    wet = bath()
    bal = F.area([(0.0, 0.0), (3.0, 0.0), (3.0, 1.5), (0.0, 1.5)], codes=("BALCONY",), scope="EXTERIOR",
                 room_id="1F-B1", floor="1F")
    with K.using("1.1.0"):
        plans = WS.cutting_plan([wet, bal])
        sched = WS.schedule([wet, bal], plans)
    assert sorted(p["system_id"] for p in plans) == ["URBAN_DEFAULT_EXTERIOR", "URBAN_DEFAULT_WET_AREA"]
    assert all(len(p["areas"]) == 1 for p in plans)
    assert set(sched["project"]["C_procurement_rolls_by_system"]) == {"URBAN_DEFAULT_EXTERIOR",
                                                                       "URBAN_DEFAULT_WET_AREA"}
    assert "total" not in json.dumps(sched["project"]["C_procurement_rolls_by_system"])


def test_roll_count_never_confirmed_without_a_valid_basis():
    with K.using("1.1.0"):
        plan = WS.cutting_plan([bath()])[0]
    assert plan["roll_count_state"] == "PROVISIONAL" and plan["why_not_confirmed"]
    ents = {"inserts": [{"id": "I1", "name": "FLOOR DRAIN", "x": 500.0, "y": 500.0}], "texts": []}
    res = F.resolver(F.rule("PR-1", "UP-WP-MAT-001", "system", {"system_id": "SYS-A", "name": "sheet membrane A"},
                            kind="SPECIFICATION", ref="spec 07 13 00"),
                     F.rule("PR-2", "UP-WP-DOOR-001", "doorway_detail", "UPTURN_ACROSS_THRESHOLD"),
                     F.rule("PR-3", "UP-WP-004", "penetration_treatment", {"kind": "PATCH", "size_m": [0.5, 0.5]}),
                     F.rule("PR-4", "UP-WP-004", "corner_treatment", {"kind": "PATCH", "size_m": [0.3, 0.3]}))
    a = bath(ents=ents, res=res)
    assert a["withheld"] == [] and a["row"]["state"] == "CONFIRMED_BASIS"
    with K.using("1.1.0"):
        p = WS.cutting_plan([a])[0]
    assert p["system_id"] == "SYS-A" and p["roll_count_state"] == "CONFIRMED" and p["why_not_confirmed"] == []
    # the resolved threshold upturn joins the band: 7.00 m of upturn (6.20 + 0.80)
    assert a["layout"]["components"][-1]["net_m2"] == pytest.approx(7.0 * 0.2)


def test_the_three_quantities_balance():
    a = bath()
    lay = a["layout"]
    assert lay["consumed_m2"] == pytest.approx(lay["placed_m2"] + lay["overlap_m2"] + lay["cutting_waste_m2"] +
                                               lay["reusable_offcuts_m2"], abs=1e-6)
    assert lay["placed_m2"] == pytest.approx(3.0 + 0.16 + 1.24)
    assert lay["packaging"]["pack_total_m2"] == pytest.approx(lay["consumed_m2"] + lay["packaging"]
                                                              ["packaging_surplus_m2"])


def test_a_window_frame_line_on_the_wall_face_is_a_sill_upturn_not_glazing():
    """a 0.60 m bathroom window (a band opening: the sill wall below it takes the upturn) whose frame line on the
    window layer lies on the room's inner face: the window threshold stays upturn-eligible - the glazing line is not
    evidence of floor-level glazing - so no termination is asked for and the segmentation matches the boundary roles."""
    win = [(1, 0.4, 1.0, "WINDOW_THRESHOLD", "W1")]
    frame = [{"role": "GLAZING", "id": "G1", "a": (2.0, 0.4), "b": (2.0, 1.0)}]
    a = bath(gaps=DOOR + win, extra_feats=frame)
    r = a["row"]
    assert r["upturn"]["eligible_lm"] == pytest.approx(6.2)
    assert r["upturn"]["by_role_lm"].get("WINDOW_THRESHOLD") == pytest.approx(0.6)
    assert "GLAZING" not in r["upturn"]["by_role_lm"]
    assert r["terminations"]["unresolved_lm"] == pytest.approx(0.8)    # the door's own alternative only
    lines, unres = lines_of(a)
    assert not [ln for ln in lines if ln["item_code"] == "FIN.WP.TERMINATION"]
    # glazing that no opening explains (a glazed screen drawn on the face) still breaks the upturn
    s = bath(extra_feats=[{"role": "GLAZING", "id": "G2", "a": (2.0, 0.4), "b": (2.0, 1.0)}])
    assert s["row"]["upturn"]["eligible_lm"] == pytest.approx(5.6)
    assert s["row"]["terminations"]["unresolved_lm"] == pytest.approx(0.8 + 0.6)
    (t,) = [ln for ln in lines_of(s)[0] if ln["item_code"] == "FIN.WP.TERMINATION"]
    assert t["calculation"]["inputs"]["length_m"] == pytest.approx(0.6) and t["measured_net"] is None


def test_the_segmentation_check_accepts_window_frames_and_flags_anything_else():
    """the ring segmentation is checked against the plan's boundary roles: a window whose sash line the roles called
    half glazing edge (6.20 m segmented, 5.90 m + 0.30 m glazing edge) agrees and is recorded; a disagreement outside
    that band keeps the roles' value, flags WP_BOUNDARY_SEGMENTATION_REVIEW and never releases the corners."""
    win = [(1, 0.4, 1.0, "WINDOW_THRESHOLD", "W1")]
    ok = bath(gaps=DOOR + win, agg=5.9, agg_glazing=0.3)
    assert not ok["boundary"].get("approximate") and ok["boundary"]["window_frame_lm"] == pytest.approx(0.3)
    assert ok["row"]["upturn"]["eligible_lm"] == pytest.approx(6.2)
    bad = bath(gaps=DOOR + win, agg=5.0, agg_glazing=0.3)
    assert bad["boundary"]["approximate"] and bad["boundary"]["corners_unreliable"]
    assert bad["row"]["upturn"]["eligible_lm"] == pytest.approx(5.0)
    _, unres = lines_of(bad)
    assert any(u["reason"].startswith("WP_BOUNDARY_SEGMENTATION_REVIEW") for u in unres)
