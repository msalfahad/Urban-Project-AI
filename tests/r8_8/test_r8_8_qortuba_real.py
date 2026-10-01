"""R8.8 on the declared Qortuba fixtures (OLD revision: pinned K1 decode + LibreDWG's DXF of the same DWG).

H584 permanent cross-route test: the same source read by two routes gives the same certified topology, the same
label ownership, the same areas within the frozen policy and the same six rows. Plus: the eight ellipses, the title
block, furniture, determinism, and the consistency of the committed R8.8 registers."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).parent
MANIFEST = json.loads((HERE / "FIXTURE_MANIFEST.json").read_text())
REG = HERE / "registers"


@pytest.fixture(scope="module")
def lab():
    for path, want in MANIFEST["fixtures"].items():
        if not (ROOT / path).exists():
            pytest.skip(f"declared fixture not present in this checkout: {path}")
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == want, f"FIXTURE DRIFT: {path}"
    sys.path.insert(0, str(ROOT / "research/external_engine_lab"))
    import r8_8_topology as m
    return m


@pytest.fixture(scope="module")
def old(lab, tmp_path_factory):
    C = lab.C
    k1 = C.old_input()
    pkl = tmp_path_factory.mktemp("k2") / "old_k2.pkl"
    blob = C.build_k2_records(lab.OLD_DXF, C.REV_OLD_ID, pkl)
    k2 = C.input_from_pickle(pkl, C.rev_old())[0]
    r1, r2 = lab.run(k1, lab.k1_unrealised()), lab.run(k2, blob["unrealised"])
    return {"k1": k1, "k2": k2, "r1": r1, "r2": r2}


def test_H584_old_k1_vs_k2_same_topology_under_the_frozen_policy(lab, old):
    xr = lab.cross_route(old["r1"], old["r2"])
    assert xr["same_topology"], xr["differences"][:3]
    assert xr["only_K1"] == [] == xr["only_K2"] and xr["common_site_ids"] == len(old["r1"]["sites"])
    assert xr["H584"]["sites_bounded_by_H584"]                      # the wall line H584 bounds sites in both routes
    for a, b in xr["H584"]["areas_m2"].values():
        assert abs(a - b) < 1e-9
    h1 = next(p for p in old["k1"].parts if p.identity.source_handle == "584").geometry
    h2 = next(p for p in old["k2"].parts if p.identity.source_handle == "584").geometry
    assert h1 != h2 and max(abs(x - y) for x, y in zip(h1, h2)) < 1e-10          # the routes really differ
    def rows(r):
        return {k: (v["state"], v["value"], [u["site"] for u in v["sites_used"]])
                for k, v in lab.six_rows(r, "QORTUBA_REV_OLD").items()}
    assert rows(old["r1"]) == rows(old["r2"])


def test_old_revision_rows_are_computed_or_blocked_never_unstable(lab, old):
    rows = lab.six_rows(old["r1"], "QORTUBA_REV_OLD")
    assert (rows["Q-03"]["state"], rows["Q-03"]["value"]) == ("COMPUTED_SHADOW", 17.7425) == \
           (rows["Q-11"]["state"], rows["Q-11"]["value"])
    assert (rows["Q-03P"]["state"], rows["Q-03P"]["value"]) == ("COMPUTED_SHADOW", 11.685)
    assert rows["Q-13"]["state"] == "BLOCKED" and rows["Q-13"]["value"] is None
    assert any("OWNER_SCOPE_MISMATCH" in str(b["why"]) for b in rows["Q-14"]["blockers"])   # the claim is REV_NEW only


def test_the_eight_old_ellipses_are_proven_topology_irrelevant(lab, old):
    a = lab.ellipse_audit(old["k1"], old["r1"])
    assert a["count"] == 8 and a["classification_counts"] == {"TOPOLOGY_IRRELEVANT_PROVEN": 8}
    assert all(r["rule"] == "GR-02" and r["door_closure"] == "CLOSED" for r in a["records"])


def test_title_block_and_sheet_frame_never_become_rooms_on_real_data(lab, old):
    frame_texts = {t.identity.key for t in old["k1"].texts if t.layer == "FRAME"}
    for s in old["r1"]["sites"]:
        assert not frame_texts & {x["text"] for x in s["label_texts"]}
    roles = old["r1"]["roles"]["roles"]
    frame_parts = {k for k, a in roles.items() if a.role in ("SHEET_FRAME", "TITLE_BLOCK")}
    assert frame_parts and not frame_parts & {x for s in old["r1"]["sites"] for x in s["boundary_source_ids"]}
    C = lab.C
    clipped = C.old_input(bounds=C.BOUNDS)                          # the R8.7 candidate bounds cut the frame
    assert lab.run(clipped, lab.k1_unrealised())["sites"] is None


def test_furniture_and_door_symbols_never_bound_a_site(old):
    roles = old["r1"]["roles"]["roles"]
    excluded = {k for k, a in roles.items() if a.role in ("FURNITURE", "OPENING_SYMBOL", "DIMENSION_GRAPHICS",
                                                          "SANITARY_FIXTURE", "STAIR_GEOMETRY")}
    used = {x for s in old["r1"]["sites"] for x in s["boundary_source_ids"]}
    assert excluded and not excluded & used


def test_same_fixture_same_first_run(lab, old):
    again = lab.run(lab.C.old_input(), lab.k1_unrealised())
    def dig(r):
        return hashlib.sha256(json.dumps([lab.T.public(s) for s in r["sites"]], sort_keys=True, default=str)
                              .encode()).hexdigest()
    assert dig(again) == dig(old["r1"])


def test_committed_registers_are_consistent():
    six = json.loads((REG / "QORTUBA_SIX_ROW_STATUS.json").read_text())
    new = six["rows"]["NEW_K2"]
    assert (new["Q-03P"]["state"], new["Q-03P"]["value"]) == ("COMPUTED_SHADOW", 11.685)
    assert all(new[r]["state"] == "BLOCKED" for r in ("Q-03", "Q-11", "Q-13", "Q-14"))
    topo = json.loads((REG / "NEW_QORTUBA_TOPOLOGY.json").read_text())
    assert topo["variant_isolation"]["isolated"] is True
    owner = json.loads((REG / "OWNER_ACTION_REGISTER.json").read_text())
    ids = {a["action_id"]: a for a in owner["actions"]}
    assert ids["SUPPLY_QORTUBA_NEW_REVISION_DWG"]["status"] == "FILE_RECEIVED"
    assert not {"ALLOW_DECODER_INSTALL_IN_ENVIRONMENT", "ESTABLISH_NEW_DWG_SOURCE_IDENTITY"} & set(ids)
    assert owner["required_now"] == [] and ids["APPROVE_QORTUBA_NEW_ROUND1_BASELINE"]["status"] == "NOT_REQUESTED_YET"
    eng = json.loads((REG / "ENGINEERING_ACTION_REGISTER.json").read_text())
    assert {"ESTABLISH_NEW_DWG_SOURCE_IDENTITY", "OBTAIN_PINNED_AC1032_DECODER"} <= {a["action_id"] for a in eng["actions"]}
    dec = json.loads((REG / "R8_8_DECISION_REGISTER.json").read_text())
    assert dec["gates"]["PRODUCTION_MIGRATION"] == "NO" and dec["gates"]["MIGRATION_EXECUTION_READY"] == "NO"
    assert dec["gates"]["NEW_DWG_SOURCE_IDENTITY"] == "NOT_ESTABLISHED"
