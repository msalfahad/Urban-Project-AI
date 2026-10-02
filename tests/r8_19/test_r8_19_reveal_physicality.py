"""R8.19 §31: REVEAL_PHYSICALITY_POLICY_V1 - a reveal surface must be physically established (an admitted wall /
structural part, or the OPENING_JAMB end of an established wall band for that opening) BEFORE any finish. Fixture,
glazing and frame lines never prove it. Synthetic only: frozen BEFORE any Qortuba R8.19 run."""

from __future__ import annotations

from engine.source import reveal_finish as RF, reveal_physicality as RP, wall_faces_v2 as WF

A, B = (0.0, 0.0), (5.0, 0.0)                        # a 5-unit reveal face from the room face to the track
OP = "GLAZED|P|H33||SEGMENT|0"
EPS = 1e-6


def band_end(**kw):
    e = {"band_id": "WB-1", "state": RP.BAND_ESTABLISHED, "kind": RP.BAND_END_JAMB,
         "opening": [f"CLOSURE|{OP}|F1"], "segment": (0.0, 0.0, 15.0, 0.0)}
    return dict(e, **kw)


def phys(walls=(), ends=(), others=(), depth=0.05, opening=OP):
    return RP.physicality(A, B, depth_m=depth, opening=opening, wall_parts=list(walls), band_ends=list(ends),
                          other_parts=list(others), eps=EPS)


def finish(p, painted_dry, explicit=None):
    return RF.finish_state(ownership_established=p["state"] == RP.ESTABLISHED, owner_painted_dry=painted_dry,
                           explicit=explicit)


def test_r1_a_fixture_layer_line_cannot_prove_a_reveal():
    p = phys(others=[("P|H48||SEGMENT|0", "FIXTURE", (0.0, 0.0, 5.0, 0.0))])
    assert p["state"] == RP.UNRESOLVED and p["rejected"][0]["layer"] == "FIXTURE" and finish(p, True) == RF.UNRESOLVED


def test_r2_an_aluminium_glazing_line_cannot_prove_plasterable_masonry():
    p = phys(walls=[("P|H33||SEGMENT|0", {"GLAZING_BOUNDARY", "OPENING_BOUNDARY"}, (0.0, 0.0, 5.0, 0.0))])
    assert p["state"] == RP.UNRESOLVED and not p["evidence"]


def test_r3_physical_reveal_with_the_default_is_plaster():
    p = phys(walls=[("P|H15||SEGMENT|0", {"TOPOLOGY_BOUNDARY"}, (0.0, 0.0, 15.0, 0.0))])
    assert p["state"] == RP.ESTABLISHED and p["evidence"][0]["kind"] == "ADMITTED_WALL_PART"
    assert finish(p, False) == RF.PLASTER_DEFAULT and RF.TRADES[RF.PLASTER_DEFAULT] == ("PLASTER",)


def test_r4_physical_reveal_owned_by_a_painted_dry_room_is_plaster_and_paint():
    p = phys(walls=[("P|H15||SEGMENT|0", {"TOPOLOGY_BOUNDARY"}, (0.0, 0.0, 15.0, 0.0))])
    assert finish(p, True) == RF.PLASTER_AND_PAINT


def test_r5_physical_reveal_with_explicit_porcelain_is_porcelain():
    p = phys(ends=[band_end()])
    assert p["evidence"][0]["kind"] == "ESTABLISHED_WALL_BAND_END" and finish(p, True, "PORCELAIN") == \
        RF.PORCELAIN_EXPLICIT


def test_r6_no_physical_reveal_is_zero_surface():
    p = phys(walls=[("P|H15||SEGMENT|0", {"TOPOLOGY_BOUNDARY"}, (0.0, 0.0, 15.0, 0.0))], depth=0.0)
    assert p["state"] == RP.NONE and not p["evidence"]
    split = RF.frame_split(0.15, [0.0, 0.10], side_a="HALL", side_b="PAINTRY")
    assert split["HALL"] == 0.0 and abs(split["PAINTRY"] - 0.05) < 1e-9


def test_r7_unresolved_physicality_blocks_and_foreign_band_ends_do_not_count():
    assert phys()["state"] == RP.UNRESOLVED
    assert phys(ends=[band_end(opening=["CLOSURE|GLAZED|P|H99||SEGMENT|0|F1"])])["state"] == RP.UNRESOLVED
    assert phys(ends=[band_end(state="WALL_BAND_CANDIDATE")])["state"] == RP.UNRESOLVED
    assert phys(ends=[band_end(kind="RECEIVING_FACE_JUNCTION")])["state"] == RP.UNRESOLVED
    assert phys(ends=[band_end(segment=(10.0, 0.0, 15.0, 0.0))])["state"] == RP.UNRESOLVED   # does not cover


def test_r8_no_surface_gets_two_finish_owners():
    split = RF.frame_split(0.15, [0.05, 0.15], side_a="PAINTRY", side_b="HALL")
    assert abs(split["PAINTRY"] + split["HALL"] - 0.05) < 1e-9                  # depth outside the frame, once
    rv = [{"opening": OP, "owner_site": "PAINTRY", "surface": "LEFT_JAMB"}]
    assert WF.double_count_guard({}, rv)["state"] == "PASS"
    assert WF.double_count_guard({}, rv + [dict(rv[0])])["state"] == "FAIL"
    assert "symmetry with the opposite jamb" in RP.policy_record()["never"]
