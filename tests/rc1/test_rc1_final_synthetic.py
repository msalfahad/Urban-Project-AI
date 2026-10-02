"""Qortuba RC1 final synthetic: the Urban floor-finish-before-cabinetry method resolves cabinetry / joinery only when
an object is CLASSED as such (cases A-F), never through built obstacles; the freeze schema refuses placeholders where
an identity is required; the topology result digest is order- and noise-independent."""

from __future__ import annotations

import json
import random
from pathlib import Path

from engine.source import footprint_authority as FA, freeze_schema as FS, topology_digest as TD

ROOT = Path(__file__).resolve().parents[2]
RULE = next(r for r in json.loads((ROOT / "data/registry/URBAN_OWNER_METHOD_RULES.json").read_text())["rules"]
            if r["rule_id"] == "URBAN-FLOOR-FINISH-BEFORE-CABINETRY-METHOD")
METHOD = {"policy_id": "URBAN-FLOOR-FINISH-BEFORE-CABINETRY-METHOD@v1", "trade": RULE["trade"],
          "space_classes": RULE["applicability"]["space_classes"],
          "object_classes": RULE["applicability"]["object_classes"], "treatment": RULE["treatment"],
          "excluded_object_classes": RULE["excluded_object_classes"]}


def res(cls, space="SERVICE_ROOM", ids=()):
    objs = FA.identify([{"key": f"K{n}", "object_class": c} for n, c in enumerate(cls)], list(ids))
    return FA.resolve(site="S", space_class=space, trade="FLOOR_FINISH", objects=objs, policies=[METHOD])


def test_case_a_later_installed_cabinet_floor_continues_beneath():
    r = res(["LATER_INSTALLED_CABINETRY"])
    assert r["state"] == FA.RESOLVED and r["treatment"] == "FOOTPRINT_INCLUDED"


def test_case_b_wardrobe_and_fixed_joinery_floor_continues_beneath():
    for cls, space in (("WARDROBE", "DRY_INTERNAL_ROOM"), ("FIXED_JOINERY", "DRY_INTERNAL_ROOM"),
                       ("VANITY_UNIT", "WET_SERVICE_ROOM")):
        assert res([cls], space)["state"] == FA.RESOLVED


def test_case_c_structural_column_is_never_carried_through():
    r = res(["STRUCTURAL_COLUMN"])
    assert r["state"] == FA.UNRESOLVED and "built obstacles" in r["rejected"][0]["why"][0]
    assert "STRUCTURAL_COLUMN" in RULE["excluded_object_classes"] and "STRUCTURAL_OBSTACLE" in \
        RULE["excluded_object_classes"]


def test_case_d_proven_masonry_plinth_blocks_even_beside_cabinetry():
    r = res(["LATER_INSTALLED_CABINETRY", "BUILT_PLINTH"])
    assert r["state"] == FA.UNRESOLVED and r["treatment"] is None


def test_case_e_unknown_object_role_is_not_cabinetry():
    assert res(["UNKNOWN_OBJECT"])["state"] == FA.UNRESOLVED


def test_case_f_fixture_layer_alone_does_not_make_cabinetry():
    assert res(["SANITARY_FIXTURE"])["state"] == FA.UNRESOLVED
    fact = {"fact_id": "F@v1", "object_keys": ["K0"], "accepts_roles": ["SANITARY_FIXTURE"],
            "object_class": "LATER_INSTALLED_CABINETRY"}
    ok = res(["SANITARY_FIXTURE"], ids=[fact])
    assert ok["state"] == FA.RESOLVED and ok["objects"][0]["observed_class"] == "SANITARY_FIXTURE"
    assert ok["objects"][0]["identity_authority"] == "F@v1"
    other = dict(fact, object_keys=["K9"])                          # names another object
    assert res(["SANITARY_FIXTURE"], ids=[other])["state"] == FA.UNRESOLVED
    wrong = dict(fact, accepts_roles=["FURNITURE"])                 # does not accept the observed role
    assert res(["SANITARY_FIXTURE"], ids=[wrong])["state"] == FA.UNRESOLVED


def test_the_method_never_claims_a_geometry_change_or_shape_inference():
    assert "never by shape" in RULE["object_class_authority"]
    assert any("change of any site" in n for n in RULE["never"])
    assert RULE["relations"][0]["relation"] == "GENERALISES"


# ------------------------------------------------------------------------------- freeze schema
SCHEMA = {"name": {"class": "TEXT"}, "topology": {"class": "SHA256"}, "rows": {"class": "SHA256_MAP"},
          "commit": {"class": "GIT_COMMIT"}, "frozen": {"class": "BOOLEAN", "why": "the decision"},
          "tests": {"class": "OPTIONAL", "why": "package-filled"}}
GOOD = {"name": "X", "topology": "a" * 64, "rows": {"Q": {"T": "b" * 64}}, "commit": "c4487e1", "frozen": True}


def test_freeze_schema_accepts_real_identities():
    assert FS.validate(GOOD, SCHEMA)["state"] == "PASS"


def test_freeze_schema_rejects_placeholders_where_an_identity_is_required():
    for bad in (False, True, None, "", "UNKNOWN", "SAME", "a" * 12, "Z" * 64):
        v = FS.validate(dict(GOOD, topology=bad), SCHEMA)
        assert v["state"] == "FAIL" and v["errors"][0]["field"] == "topology", bad
    assert FS.validate(dict(GOOD, rows={"Q": {"T": "SAME"}}), SCHEMA)["state"] == "FAIL"
    assert FS.validate(dict(GOOD, rows={}), SCHEMA)["state"] == "FAIL"


def test_freeze_schema_rejects_missing_undeclared_and_unexplained_optional_fields():
    assert FS.validate({k: v for k, v in GOOD.items() if k != "commit"}, SCHEMA)["errors"][0]["error"] == "MISSING"
    assert FS.validate(dict(GOOD, extra=1), SCHEMA)["errors"][0]["error"] == "UNDECLARED_FIELD"
    s2 = dict(SCHEMA, tests={"class": "OPTIONAL"})
    assert FS.validate(GOOD, s2)["errors"][0]["error"] == "NO_REASON_FOR_OPTIONAL_OR_BOOLEAN"


# ------------------------------------------------------------------------------- topology digest
class _B:
    def __init__(self, sid, g):
        self.source_id, self.kind, self.geometry, self.role, self.derived_from = sid, "SEGMENT", g, "R", ("x",)


def topo(eps=0.0, order=None):
    sites = [{"site_id": f"S{i}", "kind": "LABELLED_SITE", "status": "CERTIFIED", "area": 100.0 * i + eps,
              "outer_boundary_source_ids": [f"b{i}", f"a{i}"], "labels": [f"L{i}"]} for i in range(4)]
    bands = [{"band_id": f"WB{i}", "state": "WALL_BAND_ESTABLISHED", "face_a": "f", "face_b": "g",
              "width": 20.0 + eps, "interval": (0.0, 10.0)} for i in range(3)]
    if order is not None:
        random.Random(order).shuffle(sites)
        random.Random(order).shuffle(bands)
    return {"sites": sites, "wall_bands": {"bands": bands}, "closures": [_B("C1", (0.0, 0.0, 1.0, 0.0))],
            "openings": {"I1": {"state": "CLOSED", "width": 80.0}}, "passages": [], "topology_closures": []}


def test_topology_digest_is_order_and_noise_independent_but_sees_real_change():
    a = TD.digest(topo())
    assert a["sha256"] == TD.digest(topo(order=7))["sha256"] == TD.digest(topo(eps=1e-9))["sha256"]
    assert TD.digest(topo(eps=0.01))["sha256"] != a["sha256"]
    assert len(a["sha256"]) == 64 and a["counts"]["sites"] == 4
