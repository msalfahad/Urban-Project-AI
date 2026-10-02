"""R8.15 §33: a duct as source-bound owner PHYSICAL obstacle authority - never a shape rule, never topology."""

from __future__ import annotations

import json
from pathlib import Path

from engine.source import obstacle_authority as OA, owner_claims as OC, owner_facts as OF, room_topology as RT
from engine.source import topology as T, topology_closures as TC, wall_contact_path as WC
from tests.r8_8 import helpers as H
from tests.r8_13.test_r8_13_wall_band_v4 import box, rect

ROOT = Path(__file__).resolve().parents[2]
RAW = {f["fact_id"]: f for f in json.loads((ROOT / "data/registry/OWNER_PHYSICAL_FACTS.json").read_text())["facts"]}
DUCT = RAW["QORTUBA-NEW-BED-ROOM-DUCT-OWNER-001"]
UNIT2 = (10.0 / 1000) ** 2                       # helper unit: 10 mm per native unit


def duct_room(with_x=False):
    parts = box(500, 400) + rect(50, 200, 150, 300, 190)
    if with_x:
        parts += [H.seg(60, 200, 150, 300, 190, layer="HIDDEN"), H.seg(61, 200, 190, 300, 150, layer="HIDDEN")]
    inp = H.inp(parts, texts=[H.text(5, "BED", 100, 100)])
    return inp, RT.run(inp, frame_insert=None, closure_policy=TC.POLICY_ID)


def fact_for(inp, keys, kind="BUILT_OBSTACLE", rid=H.REV):
    by = {p.identity.key: p for p in inp.parts}
    return OF.from_record({
        "fact_id": "TEST-DUCT", "version": 1, "kind": kind, "authority": ["PROJECT_OWNER"],
        "scope": {"source_revision_id": rid, "source_anchor_sha256": "a" * 64, "region_id": H.REGION,
                  "frame_id": "MF:" + H.REGION},
        "parts": [{"key": k, "fingerprint": OC.part_fingerprint(by[k]), "physical_reading": "DUCT_FACE"} for k in keys],
        "statement": dict(DUCT["statement"])})


def loops(r):
    return r["wall_bands"]["isolated_loops"]


def bed(r):
    sid, _ = T.locate(r["_arr"], r["sites"], (100, 100), 0.0)
    return next(s for s in r["sites"] if s["site_id"] == sid)


def test_the_exact_source_bound_duct_fact_applies():
    inp, r = duct_room()
    lp = loops(r)
    f = fact_for(inp, lp[0]["segments"])
    b = OF.bind(f, inp)
    assert b["binding"] == OC.APPLIES
    a = OA.entity_authority(lp, [(f, b)])
    assert a[lp[0]["entity"]]["state"] == OA.OWNER_PHYSICAL_OBSTACLE and a[lp[0]["entity"]]["fact"] == "TEST-DUCT@v1"


def test_the_same_geometry_without_the_owner_fact_stays_unresolved():
    inp, r = duct_room()
    a = OA.entity_authority(loops(r), [])
    assert {v["state"] for v in a.values()} == {OA.UNPROVEN_OBSTACLE}
    h = OA.site_holes(bed(r), loops(r), a, UNIT2)
    assert h["authorised"] is False and abs(h["hole_area_m2"] - 1.0 * 0.4) < 1e-9


def test_the_fact_does_not_transfer_to_another_revision_or_project():
    inp, r = duct_room()
    f = fact_for(inp, loops(r)[0]["segments"], rid="REV_OTHER")
    assert OF.bind(f, inp)["binding"] == OF.REJECTED_SCOPE
    real = OF.from_record(DUCT)                                     # the Qortuba fact on a non-Qortuba input
    assert OF.bind(real, inp)["binding"] == OF.REJECTED_SCOPE
    assert OA.entity_authority(loops(r), [(real, OF.bind(real, inp))])[loops(r)[0]["entity"]]["state"] == \
        OA.UNPROVEN_OBSTACLE
    assert {"P7757", "Al Rashed"} <= set(DUCT["transfer_forbidden"])


def test_the_duct_removes_its_floor_and_ceiling_footprint_from_source_geometry():
    inp, r = duct_room()
    lp = loops(r)
    f = fact_for(inp, lp[0]["segments"])
    a = OA.entity_authority(lp, [(f, OF.bind(f, inp))])
    h = OA.site_holes(bed(r), lp, a, UNIT2)
    assert h["authorised"] and h["holes_only_isolated_loops"]
    assert abs(h["hole_area_m2"] - OA.shoelace([(200, 150), (300, 150), (300, 190), (200, 190)]) * UNIT2) < 1e-12
    assert f.statement["floor_effect"] == "EXCLUDED_FROM_ROOM_FLOOR"
    assert f.statement["ceiling_effect"] == "EXCLUDED_FROM_NORMAL_CEILING"


def test_the_duct_role_implies_no_material():
    assert DUCT["statement"]["material"].startswith("NOT STATED")
    inp, r = duct_room()
    f = fact_for(inp, loops(r)[0]["segments"])
    rec = OA.entity_authority(loops(r), [(f, OF.bind(f, inp))])[loops(r)[0]["entity"]]
    assert "material" not in rec and rec["physical_class"] == "DUCT"


def test_the_duct_reaches_skirting_only_through_wall_contact_logic():
    inp, r = duct_room()
    lp = loops(r)
    f = fact_for(inp, lp[0]["segments"])
    auth = {k: v["state"] for k, v in OA.entity_authority(lp, [(f, OF.bind(f, inp))]).items()}
    edges = WC.site_edges(r["_arr"], bed(r))
    m = WC.SkirtingMethod("T", 1, {})
    on = WC.measure(edges, m, obstacle_authority=auth)
    assert on["state"] == WC.COMPUTED and abs(on["components"][WC.OBSTACLE_FACE] - 280.0) < 1e-9
    off = WC.measure(edges, WC.SkirtingMethod("T", 1, {}, obstacle_faces=WC.EXCLUDED), obstacle_authority=auth)
    assert off["components"].get(WC.OBSTACLE_FACE) is None and abs(off["excluded"][WC.OBSTACLE_FACE] - 280.0) < 1e-9
    none = WC.measure(edges, m, obstacle_authority={k: OA.UNPROVEN_OBSTACLE for k in auth})
    assert none["state"] == WC.INCOMPLETE and none["length"] is None        # unproven -> withheld, no number


def test_a_dashed_x_alone_never_establishes_a_duct():
    inp, r = duct_room(with_x=True)
    xkeys = [p.identity.key for p in inp.parts if p.layer == "HIDDEN"]
    f = fact_for(inp, xkeys)                                         # a fact that binds only the X
    a = OA.entity_authority(loops(r), [(f, OF.bind(f, inp))])
    assert {v["state"] for v in a.values()} == {OA.UNPROVEN_OBSTACLE}
    bound = {p["key"] for p in DUCT["parts"]}
    assert not bound & set(DUCT["statement"]["corroborating_presentation"]["parts"])
    assert "closed rectangle + X = duct" in DUCT["never"]


def test_the_physical_fact_policy_v2_never_reaches_topology_role():
    for kind in ("BUILT_OBSTACLE", "PASSAGE_HEAD_CONDITION", "THRESHOLD_FINISH_CONSTRUCTION"):
        assert OF.TOPOLOGY_ROLE not in OF.KIND_DOMAINS[kind]
    assert OF.POLICY_ID == "OWNER_PHYSICAL_FACT_POLICY_V2" and "never" in OA.policy_record()
