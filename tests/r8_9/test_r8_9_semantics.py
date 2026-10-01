"""R8.9 §9-§16, §25: unrealised entities on positive evidence only, text role authority, physical space vs
semantic zone vs trade region, threshold sites, obstacle interiors."""

from __future__ import annotations

import sys
from pathlib import Path

from engine.source import geometry_role as GR, role_authority as RA, room_topology as RT, semantic_zones as SZ
from engine.source import text_role as TX, topology as T
from tests.r8_8 import helpers as H

ROOT = Path(__file__).resolve().parents[2]


def run(parts, texts=(), **kw):
    return RT.run(H.inp(parts, texts=texts), frame_insert=None, **kw)


def outer(h0=100):
    return [H.seg(h0, 0, 0, 1000, 0), H.seg(h0 + 1, 1000, 0, 1000, 400), H.seg(h0 + 2, 1000, 400, 0, 400),
            H.seg(h0 + 3, 0, 400, 0, 0)]


# ------------------------------------------------------------------------------- §9-§10 unrealised entities
def test_absence_of_realised_peers_never_clears_an_unrealised_entity():
    parts = H.box(1, 0, 0, 500, 400) + [H.seg(60, 900, 900, 950, 900, layer="LOGO")]   # LOGO peer far away
    u = [{"code": "UNHANDLED", "obs_id": "D1:97", "layer": "LOGO", "path": []}]
    r = run(parts, [H.text(5, "A", 100, 100)], unrealised=u)
    assert r["unrealised"]["blocking_input"][0]["disposition"] == RT.UNREALISED_REVIEW_REGION
    assert r["sites"][0]["status"] == T.REVIEW_REQUIRED and "REGION_REVIEW_REQUIRED" in r["sites"][0]["issues"]


def test_a_positively_placed_title_logo_object_is_excluded():
    parts = H.box(1, 0, 0, 500, 400)
    u = [{"code": "UNHANDLED", "obs_id": "D1:97", "layer": "LOGO", "path": [], "extent": [600.0, 0.0, 700.0, 50.0],
          "extent_basis": "ACIS"}]
    r = run(parts, [H.text(5, "A", 100, 100)], unrealised=u)
    assert r["unrealised"]["blocking_input"] == [] and r["sites"][0]["status"] == T.CERTIFIED
    assert r["unrealised"]["recorded"][0]["disposition"] == "NOT_IN_ANY_BOUNDED_SITE_BY_PLACEMENT"


def test_unrealised_in_a_localised_occurrence_blocks_only_where_that_occurrence_is():
    sofa = H.box(1, 50, 50, 100, 80, layer="FURNITURE", path=("30",))
    parts = H.two_rooms() + sofa
    u = [{"code": "PROXY", "obs_id": "D1:96", "layer": "FURNITURE", "path": ["30"]}]
    r = run(parts, [H.text(5, "A", 250, 200), H.text(6, "B", 750, 200)], unrealised=u)
    by = {tuple(s["labels"]): s for s in r["sites"]}
    assert "UNREALISED_ENTITY_POSSIBLY_IN_SITE" in by[("E5",)]["issues"]
    assert by[("E6",)]["status"] == T.CERTIFIED


def test_acis_placement_evidence_bounds_the_body_rigorously():
    sys.path.insert(0, str(ROOT / "research/external_engine_lab"))
    import r8_9_evidence as EV
    assert EV.spline_extent([(0, 0), (10, 5), (20, 0)], [1.0, 2.0, 1.0]) == (0.0, 0.0, 20.0, 5.0)
    assert EV.spline_extent([(0, 0), (10, 5)], [1.0, -1.0]) is None          # a negative weight: no hull bound
    assert EV.acis_extent(b"") is None and EV.acis_extent(b"garbage") is None


# ------------------------------------------------------------------------------- §11 text roles
def test_an_ordinary_note_inside_a_room_is_not_a_room_label():
    r = run(H.box(1, 0, 0, 500, 400), [H.text(5, "SEE DETAIL 4", 100, 100, layer="NOTES")])
    (s,) = r["sites"]
    assert s["labels"] == [] and s["status"] == T.CERTIFIED
    assert r["roles"]["text_roles"][H.text(5, "x", 0, 0, layer="NOTES").identity.key].role == TX.GENERAL_NOTE


def test_an_established_room_tag_names_the_room():
    tag = [H.text(5, "BEDROOM", 100, 100, path=("40",), layer="TEXT"), H.text(6, "2", 100, 80, path=("40",), layer="TEXT")]
    r = run(H.box(1, 0, 0, 500, 400), tag)
    (s,) = r["sites"]
    assert s["labels"] == ["I40"] and s["status"] == T.CERTIFIED
    assert {r["roles"]["text_roles"][t.identity.key].rule_id for t in tag} == {"TR-03"}


def test_a_tag_of_the_same_source_family_is_established_without_vocabulary():
    a = [H.text(5, "HALL", 100, 100, path=("40",), layer="TEXT"), H.text(6, "xyz", 100, 80, path=("40",), layer="TEXT")]
    b = [H.text(7, "PAINTRYY", 700, 100, path=("41",), layer="TEXT"), H.text(8, "abc", 700, 80, path=("41",), layer="TEXT")]
    r = run(H.two_rooms(), a + b)
    assert {r["roles"]["text_roles"][t.identity.key].rule_id for t in b} == {"TR-04"}
    assert all(s["status"] == T.CERTIFIED and len(s["labels"]) == 1 for s in r["sites"])


def test_an_unknown_text_role_inside_a_room_is_semantic_review_not_identity():
    r = run(H.box(1, 0, 0, 500, 400), [H.text(5, "BEDROOM", 100, 100, layer="TEXT")])   # loose, room word only
    (s,) = r["sites"]
    assert s["labels"] == [] and TX.TEXT_ROLE_UNRESOLVED_IN_SITE in s["semantic_issues"]
    assert s["physical_status"] == T.CERTIFIED


# ------------------------------------------------------------------------------- §12-§15 zones
def test_one_physical_site_may_carry_two_semantic_zones_and_two_labels_alone_do_not_subdivide():
    r = run(H.box(1, 0, 0, 1000, 400), [H.text(5, "M.B.ROOM", 250, 200), H.text(6, "DRESS", 750, 200)])
    (s,) = r["sites"]
    assert s["physical_status"] == T.CERTIFIED and len(r["sites"]) == 1          # TS01 never splits it
    assert r["semantic"]["sites"][s["site_id"]]["state"] == SZ.MULTI_UNRESOLVED
    zs = [z for z in r["semantic"]["zones"] if z["physical_site_id"] == s["site_id"]]
    assert len(zs) == 2 and all(z["state"] == "UNRESOLVED" and z["area"] is None for z in zs)
    tr = SZ.trade_regions(r["semantic"], r, "FLOOR_FINISH")
    assert all(t["state"] == "BLOCKED" and "BLOCKED_SEMANTIC_ZONE" in [b["class"] for b in t["blockers"]] for t in tr)


def test_an_authored_finish_boundary_establishes_the_subdivision():
    finish = H.seg(60, 500, 0, 500, 400, layer="FLOOR-FINISH")
    r = run(H.box(1, 0, 0, 1000, 400) + [finish], [H.text(5, "M.B.ROOM", 250, 200), H.text(6, "DRESS", 750, 200)])
    (s,) = r["sites"]
    assert r["roles"]["roles"][finish.identity.key].role == GR.SEMANTIC_BOUNDARY
    assert s["physical_status"] == T.CERTIFIED and RA.ROLE_CONFLICT_SEPARATOR not in s["issues"]
    assert r["semantic"]["sites"][s["site_id"]]["state"] == SZ.MULTI_ESTABLISHED
    areas = sorted(z["area"] for z in r["semantic"]["zones"])
    assert areas == [500 * 400, 500 * 400]


def test_a_missing_wall_on_a_dimension_layer_is_a_role_question_not_a_semantic_one():
    r = run(outer() + [H.seg(104, 500, 0, 500, 400, layer="DIM")], [H.text(5, "A", 250, 200), H.text(6, "B", 750, 200)])
    (s,) = r["sites"]
    assert r["semantic"]["sites"][s["site_id"]]["state"] == SZ.BOUNDARY_MISSING


def test_open_plan_with_one_label_is_one_zone():
    r = run(H.box(1, 0, 0, 1000, 400), [H.text(5, "LIVING", 250, 200)])
    (s,) = r["sites"]
    assert r["semantic"]["sites"][s["site_id"]]["state"] == SZ.ONE_ZONE and s["status"] == T.CERTIFIED


# ------------------------------------------------------------------------------- §16 thresholds
def _door_rooms():
    """Two rooms (double-line walls 10 thick) joined by a proven door: a hinged swing in a DOOR symbol occurrence."""
    walls = [H.seg(1, 0, 0, 1000, 0), H.seg(2, 1000, 0, 1000, 400), H.seg(3, 1000, 400, 0, 400), H.seg(4, 0, 400, 0, 0),
             H.seg(5, 495, 0, 495, 150), H.seg(6, 505, 0, 505, 150), H.seg(7, 495, 150, 505, 150),
             H.seg(8, 495, 250, 495, 400), H.seg(9, 505, 250, 505, 400), H.seg(10, 495, 250, 505, 250)]
    import math
    door = [H.part(20, "ARC", (495, 150, 100, 0.0, math.pi / 2), layer="DOOR", path=("70",)),
            H.seg(21, 495, 150, 495, 250, layer="DOOR", path=("70",))]
    return walls + door


def test_the_threshold_strip_is_its_own_site_and_its_allocation_is_a_trade_rule():
    r = run(_door_rooms(), [H.text(30, "A", 250, 200), H.text(31, "B", 750, 200)])
    th = r["semantic"]["thresholds"]
    assert len(th) == 1 and th[0]["allocation"] == SZ.TRADE_RULE_REQUIRED and abs(th[0]["area"] - 10 * 100) < 1e-6
    rooms = [s for s in r["sites"] if s["labels"]]
    assert all(s["kind"] != T.OPENING_SITE for s in rooms)
    assert not any(z["physical_site_id"] == th[0]["physical_site_id"] for z in r["semantic"]["zones"])


# ------------------------------------------------------------------------------- §25 obstacle interior
def test_a_column_interior_is_an_obstacle_interior_from_role_evidence_only():
    col = H.box(50, 200, 150, 240, 190, layer="COLUMN")
    r = run(H.box(1, 0, 0, 500, 400) + col, [H.text(5, "A", 100, 100)])
    kinds = {s["kind"] for s in r["sites"]}
    assert "OBSTACLE_INTERIOR" in kinds
    oi = next(s for s in r["sites"] if s["kind"] == "OBSTACLE_INTERIOR")
    assert set(oi["obstacle"]["obstacle_sources"]) == {p.identity.key for p in col}
    core = H.box(60, 200, 150, 240, 190)                    # same outline on a WALL layer: not proven, stays unlabelled
    r = run(H.box(1, 0, 0, 500, 400) + core, [H.text(5, "A", 100, 100)])
    assert "OBSTACLE_INTERIOR" not in {s["kind"] for s in r["sites"]}
