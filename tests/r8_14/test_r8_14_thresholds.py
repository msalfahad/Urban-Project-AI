"""R8.14 §37: door threshold finish transition - one physical opening site, one or two trade regions."""

from __future__ import annotations

import json
import math
from pathlib import Path

from engine.source import door_transition as DT, owner_method_facts as MF, owner_facts as OF, room_topology as RT
from engine.source import topology_closures as TC, trade_strips as TS
from tests.r8_8 import helpers as H

ROOT = Path(__file__).resolve().parents[2]
FACTS = {f["fact_id"]: f for f in json.loads((ROOT / "data/registry/OWNER_METHOD_FACTS.json").read_text())["facts"]}
EPS = 0.1
A = ((495.0, 150.0), (495.0, 250.0))                     # face closure A (door leaf side)
B = ((505.0, 150.0), (505.0, 250.0))                     # face closure B
DRY = {"site": "S-DRY", "class": "DRY_INTERNAL_ROOM", "treatment": "PORCELAIN_DRY_FLOOR"}
WET = {"site": "S-WET", "class": "WET_SERVICE_ROOM", "treatment": "CERAMIC_WET_FLOOR"}
DRY2 = dict(DRY, site="S-DRY2")
AREA, PER = 100.0 * 10.0, 2 * (100.0 + 10.0)


def door_room(hinge_x=495.0):
    """The R8.12 door fixture: two rooms, a 10-thick partition with a door opening (y 150..250)."""
    walls = [H.seg(1, 0, 0, 1000, 0), H.seg(2, 1000, 0, 1000, 400), H.seg(3, 1000, 400, 0, 400), H.seg(4, 0, 400, 0, 0),
             H.seg(5, 495, 0, 495, 150), H.seg(6, 505, 0, 505, 150), H.seg(7, 495, 150, 505, 150),
             H.seg(8, 495, 250, 495, 400), H.seg(9, 505, 250, 505, 400), H.seg(10, 495, 250, 505, 250)]
    door = [H.part(20, "ARC", (hinge_x, 150, 100, 0.0, math.pi / 2), layer="DOOR", path=("70",)),
            H.seg(21, hinge_x, 150, hinge_x, 250, layer="DOOR", path=("70",))]
    return RT.run(H.inp(walls + door, texts=[H.text(5, "A", 250, 200), H.text(6, "B", 750, 200)]), frame_insert=None,
                  closure_policy=TC.POLICY_ID)


def test_dry_dry_threshold_is_one_continuous_region_counted_once():
    plane = DT.transition_plane(A, B, (495.0, 150.0), eps_r=EPS)
    a = DT.allocate(AREA, PER, plane, DRY, DRY2, eps_r=EPS)
    assert a["state"] == DT.CONTINUOUS and len(a["regions"]) == 1
    assert DT.contribution(a, "PORCELAIN_DRY_FLOOR") == AREA


def test_dry_wet_split_exactly_at_the_authored_door_plane_and_the_parts_sum_to_the_strip():
    plane = DT.transition_plane(A, B, (498.0, 150.0), eps_r=EPS)                   # hinge INSIDE the reveal
    assert plane["authority"] == DT.AUTHORED_LEAF_PLANE and abs(plane["offset"] - 3.0) < 1e-9
    a = DT.allocate(AREA, PER, plane, DRY, WET, eps_r=EPS)
    assert a["state"] == DT.SPLIT
    dry, wet = DT.contribution(a, "PORCELAIN_DRY_FLOOR"), DT.contribution(a, "CERAMIC_WET_FLOOR")
    assert abs(dry - 300.0) < 1e-9 and abs(wet - 700.0) < 1e-9 and dry + wet == AREA


def test_reverse_door_orientation_gives_the_same_physical_allocation():
    p1 = DT.transition_plane(A, B, (498.0, 150.0), eps_r=EPS)
    a1 = DT.allocate(AREA, PER, p1, DRY, WET, eps_r=EPS)
    p2 = DT.transition_plane((A[1], A[0]), (B[1], B[0]), (498.0, 250.0), eps_r=EPS)   # faces and hinge reversed
    a2 = DT.allocate(AREA, PER, p2, DRY, WET, eps_r=EPS)
    assert {r["site"]: round(r["area"], 9) for r in a1["regions"]} == {r["site"]: round(r["area"], 9) for r in a2["regions"]}


def test_wall_thickness_changes_but_the_authored_plane_controls_the_split():
    b20 = ((515.0, 150.0), (515.0, 250.0))
    plane = DT.transition_plane(A, b20, (500.0, 150.0), eps_r=EPS)
    a = DT.allocate(2000.0, 240.0, plane, DRY, WET, eps_r=EPS)
    assert abs(DT.contribution(a, "PORCELAIN_DRY_FLOOR") - 500.0) < 1e-9                # 5 of 20, not 10 of 20


def test_an_off_centre_or_face_anchored_door_never_assumes_the_centre():
    plane = DT.transition_plane(A, B, (495.0, 150.0), eps_r=EPS)                   # hinge ON face A
    assert plane["authority"] == DT.UNRESOLVED_PLANE and plane["symbol"] == DT.SYMBOL_AT_FACE
    a = DT.allocate(AREA, PER, plane, DRY, WET, eps_r=EPS)
    assert a["state"] == DT.UNRESOLVED_PLANE and a["regions"] == []
    au = TS.audit_v2({"id": "T", "kind": "THRESHOLD", "location": TS.SEPARATE_SITE, "sides": ["S-DRY", "S-WET"],
                      "area_m2": 0.1}, {"S-DRY"}, {}, "PORCELAIN_DRY_FLOOR", trade="FLOOR_FINISH", allocation=a)
    assert au["state"] in TS.BLOCKING_V2                                         # never silently dropped


def test_the_qortuba_centred_owner_method_splits_at_the_mid_plane_of_the_established_faces():
    fact = MF.from_record(FACTS["QORTUBA-NEW-DRY-WET-TRANSITION-AT-DOOR-PLANE-OWNER-001"])
    assert fact.statement["door_centred"] is True
    plane = DT.transition_plane(A, B, (495.0, 150.0), eps_r=EPS, owner_centred=fact.ref)
    assert plane["authority"] == DT.OWNER_CENTRED_DOOR and plane["offset"] == 5.0 and plane["fact"] == fact.ref
    a = DT.allocate(AREA, PER, plane, DRY, WET, eps_r=EPS)
    assert DT.contribution(a, "PORCELAIN_DRY_FLOOR") == DT.contribution(a, "CERAMIC_WET_FLOOR") == 500.0


def test_explicit_marble_overrides_and_no_marble_means_tile_continuity():
    plane = DT.transition_plane(A, B, (495.0, 150.0), eps_r=EPS, owner_centred="F@v1")
    m = DT.allocate(AREA, PER, plane, DRY, WET, eps_r=EPS, marble={"ref": "SCHEDULE-D1", "opening": "I70"})
    assert m["state"] == DT.MARBLE and DT.contribution(m, "PORCELAIN_DRY_FLOOR") == 0.0
    assert DT.contribution(m, DT.MARBLE) == AREA
    t = DT.allocate(AREA, PER, plane, DRY, WET, eps_r=EPS)
    assert t["state"] == DT.SPLIT and t["marble_evidence"] is None
    assert FACTS["QORTUBA-NEW-MARBLE-THRESHOLD-ONLY-IF-EXPLICIT-OWNER-001"]["statement"]["absent"].startswith("the continuous")


def test_a_threshold_is_never_counted_twice_and_never_disappears():
    for plane in (DT.transition_plane(A, B, (498.0, 150.0), eps_r=EPS),
                  DT.transition_plane(A, B, (495.0, 150.0), eps_r=EPS, owner_centred="F@v1")):
        for sides in ((DRY, WET), (DRY, DRY2), (WET, DRY)):
            a = DT.allocate(AREA, PER, plane, *sides, eps_r=EPS)
            total = sum(r["area"] for r in a["regions"])
            assert total == AREA and len({(r["side"], r["treatment"]) for r in a["regions"]}) == len(a["regions"])
    bad = DT.allocate(AREA * 1.5, PER, DT.transition_plane(A, B, None, eps_r=EPS, owner_centred="F"), DRY, WET, eps_r=EPS)
    assert bad["state"] == DT.UNRESOLVED_GEOMETRY                                # the site is not the strip


def test_the_ceiling_never_takes_a_door_threshold():
    au = TS.audit_v2({"id": "T", "kind": "THRESHOLD", "location": TS.SEPARATE_SITE, "sides": ["S-DRY", "S-WET"],
                      "area_m2": 0.1}, {"S-DRY"}, {}, "CEILING_BY_AREA", trade=TS.CEILING)
    assert au["state"] == TS.NOT_IN_TRADE and au["contribution_m2"] == 0.0


def test_the_real_door_fixture_has_one_threshold_site_between_the_two_face_closures():
    r = door_room()
    (t,) = r["semantic"]["thresholds"]
    st = r["openings"]["I70"]
    cl = {c.source_id: c.geometry for c in r["closures"] if c.source_id.startswith("CLOSURE|")}
    a, b = cl[st["closure_a"]], cl[st["closure_b"]]
    hinge = r["roles"]["doors"]["I70"]["hinge"]
    plane = DT.transition_plane((a[:2], a[2:]), (b[:2], b[2:]), hinge, eps_r=EPS)
    assert plane["symbol"] == DT.SYMBOL_AT_FACE and abs(plane["thickness"] - 10.0) < 1e-9
    al = DT.allocate(t["area"], 220.0, DT.transition_plane((a[:2], a[2:]), (b[:2], b[2:]), hinge, eps_r=EPS,
                                                           owner_centred="F@v1"), DRY, WET, eps_r=EPS)
    assert al["state"] == DT.SPLIT and sum(x["area"] for x in al["regions"]) == t["area"]


def test_an_authored_inside_leaf_makes_no_threshold_site_the_leaf_itself_splits_the_rooms():
    r = door_room(hinge_x=498.0)
    assert r["semantic"]["thresholds"] == [] and r["openings"]["I70"]["closure_b"] is None


def test_the_threshold_owner_rule_does_not_touch_the_topology_digest():
    a, b = door_room(), door_room()
    assert a["run_manifest"]["RUN_INPUT_DIGEST"] == b["run_manifest"]["RUN_INPUT_DIGEST"]
    f = MF.from_record(FACTS["QORTUBA-NEW-DOOR-THRESHOLD-CONTINUITY-OWNER-001"])
    assert set(f.allowed_domains) == {MF.TRADE_ALLOCATION} and not set(f.allowed_domains) & set(MF.FORBIDDEN_DOMAINS)
    assert MF.bind(f, H.inp([H.seg(1, 0, 0, 10, 0)]))["binding"] == OF.REJECTED_SCOPE
