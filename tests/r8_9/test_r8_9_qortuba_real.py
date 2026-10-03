"""R8.9 on the declared Qortuba fixtures (old revision: pinned K1 decode + LibreDWG's DXF of the same DWG) and the
consistency of the committed R8.9 registers (the new revision is diagnosed in the lab; its registers are checked)."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = json.loads((ROOT / "tests/r8_8/FIXTURE_MANIFEST.json").read_text())
REG = Path(__file__).parent / "registers"


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
def old(lab):
    k1 = lab.C.old_input()
    return k1, lab.run(k1, lab.k1_unrealised())


def test_old_rows_are_unchanged_by_r8_9(lab, old):
    rows = lab.six_rows(old[1], "QORTUBA_REV_OLD")
    assert {r: (v["state"], v["value"]) for r, v in rows.items()} == {
        "Q-03": ("COMPUTED_SHADOW", 17.7425), "Q-03P": ("COMPUTED_SHADOW", 11.685), "Q-11": ("COMPUTED_SHADOW", 17.7425),
        "Q-12": ("COMPUTED_SHADOW", 11.685), "Q-13": ("BLOCKED", None), "Q-14": ("BLOCKED", None)}


def test_the_office_name_entities_are_excluded_by_their_own_placement_not_by_absence(old):
    u = old[1]["unrealised"]
    assert u["blocking_input"] == []
    placed = [x for x in u["recorded"] if x.get("layer") == "OFFICE NAME"]
    assert len(placed) == 38 and {x["disposition"] for x in placed} == {"NOT_IN_ANY_BOUNDED_SITE_BY_PLACEMENT"}
    assert all(x["extent"][3] < 14000 for x in placed)          # the title / logo strip, below every room


def test_effective_layer_is_derived_and_latent_in_qortuba(old):
    from engine.source import canonical_input as CI
    k1, _ = old
    assert all(CI.effective_layer(p)[1] in (CI.EFFECTIVE_SOURCE_LAYER, CI.EFFECTIVE_BYLAYER_INSERT_CHAIN)
               for p in k1.parts)
    assert sum(1 for p in k1.parts if p.layer == "0" and p.identity.instance_handles) == 0


def test_paintry_is_a_room_tag_by_family_not_by_vocabulary(old):
    from engine.source import text_role as TX
    k1, r = old
    t = [t for t in k1.texts if t.value == "PAINTRY"]
    assert t and r["roles"]["text_roles"][t[0].identity.key].rule_id == "TR-04"
    assert "PAINTRY" not in TX.ROOM_WORDS


def test_doors_need_one_fifteenth_of_the_radius_and_the_rejected_leaf_never_closes(old):
    au = old[1]["roles"]["door_audit"]
    assert len(au) == 8 and {round(a["accepted_ratio_needed"], 6) for a in au.values()} == {0.066667}
    assert all(a["rejected_ratio_needed"] is None for a in au.values())


def test_every_old_site_agrees_in_every_grid_phase(old):
    from engine.source import topology_crosscheck as XC
    assert old[1]["crosscheck"]["counts"][XC.ALL_PHASES_AGREE] == len(old[1]["sites"])


# ------------------------------------------------------------------------------- committed registers
def _r(name):
    return json.loads((REG / f"{name}.json").read_text())


def test_committed_new_revision_status_is_consistent():
    q = _r("QORTUBA_R8_9_STATUS")
    rows = q["rows"]["NEW_K2"]
    assert all("BLOCKED" in v["state"] for v in rows.values())
    assert all("BLOCKED_SOURCE_COMPLETENESS" in v["state"] for v in rows.values())
    hyp = q["if_xrefs_confirmed_outside_the_plan"]
    assert hyp["state"] == "HYPOTHESIS_NOT_RELEASED" and hyp["rows"]["Q-03P"]["state"] == "COMPUTED_SHADOW"
    dim = q["dim_layer_separators"]["dim_lines_on_removed_wall_faces"]
    assert {(d["new_dim_line"], d["on_old_wall_face"][0]["old_wall"]) for d in dim} == {
        ("H7116", "H467"), ("H7117", "H465"), ("H7118", "H817"), ("H7119", "H513")}
    assert q["multi_label_investigation"]["A_HALL_BED_BATH"]["semantic_state"] == \
        "TOPOLOGY_BOUNDARY_MISSING_FROM_ROLE_ADMISSION"
    assert q["multi_label_investigation"]["B_MB_ROOM_DRESS"]["semantic_state"] == \
        "ONE_PHYSICAL_SPACE_MULTIPLE_SEMANTIC_ZONES_UNRESOLVED"
    assert q["sf3"]["exact_duplicate_placements"] == ["700047~700051"]


def test_committed_claims_are_source_scoped_candidates_not_applied():
    c = _r("SOURCE_LAYER_ROLE_CLAIMS")
    assert all(x["review_state"] == "SOURCE_EVIDENCE_CANDIDATE" and x["applied"] is False for x in c["claims"])
    assert all(x["source_revision_id"] == "QORTUBA_REV_NEW" for x in c["claims"])


def test_committed_owner_register_asks_two_yes_no_reviews_and_no_quantity():
    o = _r("OWNER_ACTION_REGISTER")
    assert o["required_now"] == []
    assert o["owner_review_open"] == ["CONFIRM_QORTUBA_NEW_ATTACHED_XREFS_OUTSIDE_PLAN",
                                      "CONFIRM_QORTUBA_NEW_DIM_LINES_ARE_WALLS"]
    ids = {a["action_id"]: a for a in o["actions"]}
    assert ids["SUPPLY_QORTUBA_NEW_REVISION_DWG"]["status"] == "FILE_RECEIVED"
    for k in o["owner_review_open"]:
        assert len(ids[k]["choices"]) == 3 and ids[k]["never"] == "an expected quantity"


def test_committed_decision_register_gates():
    d = _r("R8_9_DECISION_REGISTER")
    assert (d["gates"]["MIGRATION_PLANNING_READY"], d["gates"]["MIGRATION_EXECUTION_READY"],
            d["gates"]["PRODUCTION_MIGRATION"]) == ("YES", "NO", "NO")
    assert d["gates"]["P7757_TS01_CERTIFICATE"] == "UNIT_UNRESOLVED"
    p = _r("P7757_R8_9_SHADOW")
    assert p["unit"]["state"] == "UNIT_UNRESOLVED" and p["ts01_certificate"] == "UNIT_UNRESOLVED"
