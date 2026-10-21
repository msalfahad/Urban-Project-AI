"""R8.8 §11-§15, §24: method exclusions need authority; ROOM TOPOLOGY consumes only positively admitted geometry."""

from __future__ import annotations

import math
from dataclasses import replace

from engine.source import canonical_build as CB, canonical_input as CI, geometry_role as GR, room_topology as RT
from engine.source import topology as T
from tests.r8_8 import helpers as H


def door(h0, hinge, closed_end, open_end, path=("80",), name="6"):
    """A door symbol occurrence: swing arc (hinge-centred, < pi) + leaf line, on layer DOOR."""
    r = math.hypot(closed_end[0] - hinge[0], closed_end[1] - hinge[1])
    a_open = math.atan2(open_end[1] - hinge[1], open_end[0] - hinge[0])
    a_closed = math.atan2(closed_end[1] - hinge[1], closed_end[0] - hinge[0])
    a0, a1 = sorted((a_open, a_closed))
    if a1 - a0 > math.pi:
        a0, a1 = a1, a0 + 2 * math.pi
    nm = {path[0]: name}
    return [H.part(h0, "ARC", (hinge[0], hinge[1], r, a0, a1), layer="DOOR", path=path, names=nm),
            H.seg(h0 + 1, hinge[0], hinge[1], open_end[0], open_end[1], layer="DOOR", path=path, names=nm)]


def labels(r):
    return sorted((round(s["area_m2"], 4), tuple(s["labels"]), tuple(s["issues"])) for s in r["sites"] if s["area_m2"] > 1)


def test_excluded_geometry_without_role_authority_fails_closed():
    ell = H.part(9, "ELLIPTICAL_ARC", (0, 0, 10, 0, 0, 10, 0, 1), layer="DOOR")
    ex = CI.MethodExclusion("ELLIPTICAL_ARC", "ROOM_TOPOLOGY", "unused", "GR-02", (GR.OPENING_SYMBOL,))
    c = CI.MethodContract("M", "1", part_fields=("source_part_id",), exclusions=(ex,))
    v = CI.validate(H.inp([H.seg(1, 0, 0, 1, 0), ell]), c)                       # no role authority supplied
    assert v["state"] == CI.METHOD_INPUT_INCOMPLETE and v["exclusion_without_authority"] == {"ELLIPTICAL_ARC:NO_ROLE": 1}
    roles = {ell.identity.key: GR.RoleAssignment(ell.identity.key, GR.UNKNOWN_PHYSICAL, GR.NONE, "GR-99")}
    v = CI.validate(H.inp([H.seg(1, 0, 0, 1, 0), ell]), c, roles=roles)
    assert v["state"] == CI.METHOD_INPUT_INCOMPLETE                              # wrong role: still no authority


def test_topology_irrelevant_proven_ellipse_is_safely_excluded():
    hinge, opened = (500.0, 100.0), (420.0, 100.0)
    sw = H.part(90, "ELLIPTICAL_ARC", (500.0, 100.0, 80.0, 0.0, 0.0, 80.0, math.pi / 2, math.pi), layer="DOOR",
                path=("81",), names={"81": "6"})
    leaf = H.seg(91, *hinge, *opened, layer="DOOR", path=("81",), names={"81": "6"})
    i = H.inp(H.two_rooms(gap=(100, 180)) + [sw, leaf])
    roles = GR.admit(i, frame_insert=None, eps=1e-6)["roles"]
    assert roles[sw.identity.key].role == GR.OPENING_SYMBOL and roles[sw.identity.key].rule_id == "GR-02"
    ex = CI.MethodExclusion("ELLIPTICAL_ARC", "ROOM_TOPOLOGY", "door swing", "GR-02", (GR.OPENING_SYMBOL,))
    c = CI.MethodContract("M", "1", part_fields=("source_part_id",), exclusions=(ex,))
    v = CI.validate(i, c, roles=roles)
    assert v["state"] == CI.COMPLETE and v["excluded_by_declaration"] == {"ELLIPTICAL_ARC": 1}
    r = RT.run(i, frame_insert=None)                                              # and the door closes the opening
    assert [x["state"] for x in r["openings"].values()] == ["CLOSED"]
    assert [round(s["area_m2"], 4) for s in r["sites"] if s["area_m2"] > 1] == [20.0, 20.0]


def test_unknown_ellipse_in_a_room_boundary_blocks_the_room():
    i = H.inp(H.box(1, 0, 0, 500, 400) + [H.part(9, "ELLIPTICAL_ARC", (500, 200, 0, 50, 30, 0, 0, math.pi), layer="WALL")])
    r = RT.run(i, frame_insert=None)
    roles = r["roles"]["roles"]
    assert roles[i.parts[-1].identity.key].role == GR.BOUNDARY_CURVE_UNSUPPORTED
    assert all(T.TOPOLOGY_ROLE_UNRESOLVED in s["issues"] for s in r["sites"])


def test_furniture_inside_a_room_never_becomes_a_boundary_when_its_role_is_proven():
    room = H.box(1, 0, 0, 500, 400)
    sofa = H.box(20, 100, 100, 300, 180, layer="FURN", path=("70",), names={"70": "SOFA_SET"})
    bed = H.box(30, 320, 100, 480, 300, layer="0", path=("71",), names={"71": "LIB$0$BED 3"})
    r = RT.run(H.inp(room + sofa + bed, texts=[H.text(5, "BEDROOM", 50, 50)]), frame_insert=None)
    roles = {GR.ROLES.index(a.role) for a in r["roles"]["roles"].values() if a.part_key.split("|")[2]}
    assert roles == {GR.ROLES.index(GR.FURNITURE)}
    assert labels(r) == [(20.0, ("E5",), ())]
    assert r["sites"][0]["status"] == T.CERTIFIED and r["sites"][0]["contents"] == {"FURNITURE": 8}


def test_unknown_furniture_like_geometry_blocks_the_room():
    room = H.box(1, 0, 0, 500, 400)
    thing = H.box(20, 100, 100, 300, 180, layer="PM", path=("70",), names={"70": "LIB$0$SF3"})
    r = RT.run(H.inp(room + thing, texts=[H.text(5, "HALL", 50, 50)]), frame_insert=None)
    big = [s for s in r["sites"] if s["area_m2"] > 1]
    assert len(big) == 1 and big[0]["area_m2"] == 20.0                          # never a boundary...
    assert big[0]["status"] == T.REVIEW_REQUIRED and T.TOPOLOGY_ROLE_UNRESOLVED in big[0]["issues"]   # ...and never ignored


def test_dimension_graphics_are_not_a_room_boundary():
    room = H.box(1, 0, 0, 500, 400)
    dim_lines = [H.seg(40, -20, 200, 520, 200, layer="DIM"), H.seg(41, 250, -20, 250, 420, layer="A-DIMS")]
    r = RT.run(H.inp(room + dim_lines, texts=[H.text(5, "HALL", 50, 50)]), frame_insert=None)
    assert labels(r) == [(20.0, ("E5",), ())]


def frame_and_title(path=("156",)):
    nm = {path[0]: "FRAM"}
    outer = H.box(200, -100, -300, 700, 500, layer="FRAME", path=path, names=nm)
    title = [H.seg(210, -100, -100, 700, -100, layer="FRAME", path=path, names=nm),
             H.seg(211, 300, -300, 300, -100, layer="FRAME", path=path, names=nm)]
    ms_title = H.box(220, 320, -280, 680, -120, layer="FRAME")                    # model-space title cell
    return outer + title + ms_title


def test_sheet_frame_and_title_block_are_never_rooms():
    room = H.box(1, 0, 0, 500, 400)
    i = H.inp(room + frame_and_title(), texts=[H.text(5, "HALL", 50, 50), H.text(6, "Drawing Name :", 400, -200)])
    r = RT.run(i, frame_insert="156")
    roles = {a.rule_id for k, a in r["roles"]["roles"].items() if "|H2" in k and int(k.split("|")[1][1:]) >= 200}
    assert roles == {"GR-01", "GR-15"}
    assert labels(r) == [(20.0, ("E5",), ())]                                     # one room, no title-block room
    assert any(f["code"] == "LABEL_OUTSIDE_EVERY_SITE" for f in r["findings"])


def test_incorrect_clipping_cannot_turn_the_title_block_into_a_room():
    """Permanent regression (R8.7 found a 90.33 m2 'room' made of the title block when the clip cut the frame)."""
    parts = H.box(1, 0, 0, 500, 400) + frame_and_title()
    bad_clip = (-50.0, -250.0, 650.0, 450.0)                                    # cuts the frame occurrence
    i = CB.assemble(H.rev(), H.REGION, bad_clip, "F", 10.0, "U", parts, [H.text(5, "HALL", 50, 50)], [])
    assert any("occurrence 156" in v for v in i.region_review.values())
    r = RT.run(i, frame_insert="156")
    assert r["state"] == CI.METHOD_INPUT_INCOMPLETE and r["sites"] is None          # blocked, never measured


def test_layer_alone_never_decides_a_role():
    # a FURNITURE layer name inside a symbol whose definition also carries wall geometry is not proven furniture
    mixed = H.box(20, 100, 100, 300, 180, layer="FURN", path=("70",)) + [H.seg(30, 0, 0, 10, 0, layer="WALL", path=("70",))]
    roles = GR.admit(H.inp(mixed), frame_insert=None, eps=1e-6)["roles"]
    assert {a.role for a in roles.values()} == {GR.UNKNOWN_PHYSICAL}
    # a block NAME alone (no layer, no definition context) never makes a model-space wall furniture
    assert GR.block_name_role("BED") == "FURNITURE" and GR.tokens("MY BLOCKS$0$BED 3") == ("BED",)
    assert GR.layer_role("FIRNTUR") is None and GR.layer_role("B-FURNI") == "FURNITURE"   # exact tokens, no fuzzing


def test_open_passage_is_never_closed_and_two_labels_in_one_space_need_review():
    i = H.inp(H.two_rooms(gap=(100, 300)), texts=[H.text(5, "BED.ROOM", 250, 200), H.text(6, "BATH", 750, 200)])
    r = RT.run(i, frame_insert=None)
    big = [s for s in r["sites"] if s["area_m2"] > 1]
    assert len(big) == 1 and big[0]["area_m2"] == 40.0
    assert T.MULTIPLE_SEMANTIC_LABELS in big[0]["issues"] and big[0]["status"] == T.REVIEW_REQUIRED


def test_door_closure_separates_rooms_and_keeps_the_opening_out_of_both():
    walls = []
    for k, (x0, x1) in enumerate(((0, 500), (515, 1015))):
        walls += H.box(10 * k + 1, x0, 0, x1, 400)
    # the 15 cm wall between the rooms has a 80 cm doorway with jamb caps (the boxes' sides are cut there)
    walls = [w for w in walls if not (w.geometry[0] == w.geometry[2] and w.geometry[0] in (500, 515))]
    walls += [H.seg(40, 500, 0, 500, 100), H.seg(41, 500, 180, 500, 400), H.seg(42, 515, 0, 515, 100),
              H.seg(43, 515, 180, 515, 400), H.seg(44, 500, 100, 515, 100), H.seg(45, 500, 180, 515, 180),
              H.seg(46, 500, 0, 515, 0), H.seg(47, 500, 400, 515, 400)]
    sym = door(60, (500.0, 104.0), (500.0, 176.0), (428.0, 104.0))
    i = H.inp(walls + sym, texts=[H.text(5, "BED.ROOM", 250, 200), H.text(6, "BATH", 750, 200)])
    r = RT.run(i, frame_insert=None)
    st = list(r["openings"].values())[0]
    assert st["state"] == "CLOSED" and st["closure_b"] is not None and abs(st["width"] - 80.0) < 1e-9
    assert labels(r) == [(20.0, ("E5",), ()), (20.0, ("E6",), ())]
    kinds = [s["kind"] for s in r["sites"]]
    assert kinds.count(T.OPENING_SITE) == 1
    assert r["opening_adjacency"][0]["sites"] == sorted(s["site_id"] for s in r["sites"] if s["labels"])


def test_unclosable_door_blocks_the_rooms_it_touches():
    i = H.inp(H.two_rooms(gap=(100, 180)) + door(60, (500.0, 100.0), (500.0, 150.0), (450.0, 100.0)),
              texts=[H.text(5, "A", 250, 200), H.text(6, "B", 750, 200)])
    r = RT.run(i, frame_insert=None)      # leaf 50 for an 80 opening: neither hypothesis reaches a wall at both ends
    assert list(r["openings"].values())[0]["state"] == T.OPENING_CLOSURE_UNRESOLVED
    assert all(T.OPENING_CLOSURE_UNRESOLVED in s["issues"] for s in r["sites"])


def test_mirrored_and_rotated_symbol_occurrences_keep_their_roles():
    for ang in (0.0, math.pi / 2, math.pi):
        c, s = math.cos(ang), math.sin(ang)
        rot = lambda p: (p[0] * c - p[1] * s, p[0] * s + p[1] * c)
        sym = door(60, rot((500.0, 100.0)), rot((500.0, 180.0)), rot((420.0, 100.0)))
        sym = [replace(sym[0], geometry=sym[0].geometry), sym[1]]
        roles = GR.admit(H.inp(sym), frame_insert=None, eps=1e-6)["roles"]
        assert {a.role for a in roles.values()} == {GR.OPENING_SYMBOL}
