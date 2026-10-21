"""R8.10 on the declared Qortuba fixtures (old revision) and the consistency of the committed R8.10 registers (the
new revision is rebuilt in the lab from the committed owner claims; its registers are checked here)."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = json.loads((ROOT / "tests/r8_8/FIXTURE_MANIFEST.json").read_text())
REG = Path(__file__).parent / "registers"
CLAIMS = ROOT / "data/registry/OWNER_SOURCE_CLAIMS.json"


def _r(name):
    return json.loads((REG / f"{name}.json").read_text())


@pytest.fixture(scope="module")
def lab():
    for path, want in MANIFEST["fixtures"].items():
        if not (ROOT / path).exists():
            pytest.skip(f"declared fixture not present in this checkout: {path}")
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == want, f"FIXTURE DRIFT: {path}"
    sys.path.insert(0, str(ROOT / "research/external_engine_lab"))
    import r8_10_claims as CL
    import r8_8_topology as m
    return m, CL


@pytest.fixture(scope="module")
def old(lab):
    m, CL = lab
    pc, xc, _ = CL.load()
    k1 = m.C.old_input()
    return k1, m.run(k1, m.k1_unrealised(), part_claims=pc, xref_claims=xc), pc


def test_old_rows_are_unchanged_by_r8_10(lab, old):
    m, _ = lab
    rows = m.six_rows(old[1], "QORTUBA_REV_OLD")
    assert {r: (v["state"], v["value"]) for r, v in rows.items() if r != "Q-13" and r != "Q-14"} == {
        "Q-03": ("COMPUTED_SHADOW", 17.7425), "Q-03P": ("COMPUTED_SHADOW", 11.685),
        "Q-11": ("COMPUTED_SHADOW", 17.7425), "Q-12": ("COMPUTED_SHADOW", 11.685)}


def test_the_new_revision_wall_claim_never_applies_to_the_old_revision(old):
    from engine.source import owner_claims as OC
    st = old[1]["owner_claims"]["part_claims"][0]
    assert st["state"] == OC.SOURCE_SCOPE_MISMATCH and st["applied_parts"] == []
    assert all(not str(a.rule_id).startswith("CLAIM:") for a in old[1]["roles"]["roles"].values())


def test_no_old_revision_wall_is_a_network_conflict_or_a_near_miss(old):
    from engine.source import role_authority as RA
    assert not [v for v in old[1]["network_review"].values() if v["state"] == RA.NETWORK_ROLE_CONFLICT]
    assert old[1]["near_misses"]["near_misses"] == []


def test_same_fixtures_give_a_deterministic_first_run(lab, old):
    m, CL = lab
    pc, xc, _ = CL.load()
    again = m.run(m.C.old_input(), m.k1_unrealised(), part_claims=pc, xref_claims=xc)
    assert again["owner_claims"]["evidence_version"] == old[1]["owner_claims"]["evidence_version"]
    assert [(s["site_id"], round(s["area"], 9)) for s in again["sites"]] == \
        [(s["site_id"], round(s["area"], 9)) for s in old[1]["sites"]]


# ------------------------------------------------------------------------------- the committed evidence version
def test_the_owner_claims_are_a_new_evidence_version_and_keep_the_previous_one():
    raw = json.loads(CLAIMS.read_text())
    prev = ROOT / raw["previous_evidence_version"]["file"]
    assert raw["evidence_version"] == 2 and prev.exists()
    assert hashlib.sha256(prev.read_bytes()).hexdigest() == raw["previous_evidence_version"]["sha256"]
    kinds = {c["kind"] for c in raw["claims"]}
    assert kinds == {"PART_ROLE", "XREF_NONCONTRIBUTING_TO_SELECTED_REGION"}
    for c in raw["claims"]:
        assert c["scope"]["plan"] == "PLAN_VARIANT_4_SELECTED" and c["scope"]["region_id"] == \
            "RC:MODEL_SPACE:4267:540:1649" and c["scope"]["source_anchor_sha256"].startswith("df0e1d69")
        assert not {"value", "quantity", "area", "area_m2"} & set(c)              # a claim carries no quantity
        assert "any quantity" in c["never_changes"]


def test_the_dim_wall_claim_names_exactly_four_parts_on_the_dim_layer():
    c = next(x for x in json.loads(CLAIMS.read_text())["claims"] if x["kind"] == "PART_ROLE")
    assert [p["handle"] for p in c["parts"]] == ["7116", "7117", "7118", "7119"]
    assert {p["source_layer"] for p in c["parts"]} == {"DIM"} and all(len(p["fingerprint"]) == 64 for p in c["parts"])


def test_the_xref_claim_names_exactly_the_two_verified_occurrences():
    c = next(x for x in json.loads(CLAIMS.read_text())["claims"] if x["kind"] != "PART_ROLE")
    assert [o["handle"] for o in c["occurrences"]] == ["16783", "17716"] and c["verification"]["all_claimed"]


# ------------------------------------------------------------------------------- committed registers
def test_new_revision_six_rows():
    rows = _r("QORTUBA_R8_10_STATUS")["rows"]["NEW_K2_R8_10"]
    assert {r: (v["state"], v["value"]) for r, v in rows.items() if v["state"] == "COMPUTED_SHADOW"} == {
        "Q-03": ("COMPUTED_SHADOW", 17.7425), "Q-03P": ("COMPUTED_SHADOW", 11.685),
        "Q-11": ("COMPUTED_SHADOW", 17.7425), "Q-12": ("COMPUTED_SHADOW", 11.685)}
    assert rows["Q-13"]["blocker_classes"] == ["PHYSICAL_TOPOLOGY", "ROLE_AUTHORITY", "TRADE_RULE"]
    assert rows["Q-14"]["blocker_classes"] == ["PHYSICAL_TOPOLOGY", "ROLE_AUTHORITY"]
    assert [b["zones"] for b in rows["Q-14"]["blockers"]] == [["HALL", "whgm"]]     # the HALL caps only
    assert all(v["migration_blockers"] for v in rows.values())                   # source anchor stays open


def test_dim_walls_separate_bath_and_bed_room_from_the_hall_and_no_other_dim_line_is_a_wall():
    e = _r("DIM_WALL_CLAIMS")["effect"]
    after = {a["stamps"][0][0]: a["area_m2"] for a in e["after"] if a["stamps"]}
    assert after == {"HALL": 43.83, "BED.ROOM": 19.2725, "BATH": 5.1}
    assert e["before_r8_9"][0]["area_m2"] == 68.66
    assert e["other_dim_parts_admitted"] == 0
    assert {p["source_layer"] for p in e["parts"]} == {"DIM"} and {p["role_now"] for p in e["parts"]} == \
        {"TOPOLOGY_BOUNDARY"}


def test_the_hall_lobby_caps_are_a_role_conflict_and_a_near_miss_not_silence():
    c = _r("DIM_WALL_CLAIMS")["hall_lobby_caps"]
    assert {x["handle"]: x["role"] for x in c["caps"]} == {"2430": "DIMENSION_GRAPHICS", "2431": "DIMENSION_GRAPHICS"}
    assert "NEAR_MISS_BOUNDARY_GAP" in c["hall_issues"] and "ROLE_CONFLICT_SEPARATOR" in c["hall_issues"]
    assert c["leak_areas"]["h2431_near_miss_pockets_m2"] and 0.3813 in c["leak_areas"]["exclusion_group_pockets_m2"]


def test_master_bedroom_and_dress_one_site_same_treatment_trade_by_trade():
    q = _r("QORTUBA_R8_10_STATUS")
    mb = q["m_b_room_dress"]
    assert mb["semantic_state"] == "ONE_PHYSICAL_SPACE_MULTIPLE_SEMANTIC_ZONES_UNRESOLVED"
    assert mb["passage"]["width_mm"] == 1200.0 and mb["passage"]["wall_thickness_mm"] == 150.0
    assert set(mb["Q-13"]["A_same_authoritative_treatment"].values()) == {"PORCELAIN_DRY_FLOOR"}
    assert mb["Q-13"]["D_unknown_geometry_material_to_floor"]["state"] == "ROLE_MATERIAL_TO_TRADE"
    assert mb["Q-14"]["object_materiality"]["state"] == "ROLE_UNRESOLVED_BUT_NON_MATERIAL_TO_TRADE"
    used = {u["site"]: u for u in q["rows"]["NEW_K2_R8_10"]["Q-14"]["sites_used"]}
    assert used[mb["site"]]["decision"] == "SEMANTIC_SUBDIVISION_NOT_REQUIRED_FOR_TRADE"


def test_trade_authority_is_the_owner_rule_store_and_the_q14_claim_never_a_quantity():
    t = _r("TRADE_SEMANTIC_EQUIVALENCE")
    refs = " ".join(t["rules"]["QORTUBA-FLOOR-TREATMENT"]["refs"])
    assert "QP-07" in refs and "QP-14" in refs and "US-01" in refs
    assert t["rules"]["QORTUBA-Q14-CEILING-TREATMENT"]["refs"] == ["QORTUBA-Q14-CEILING-FOOTPRINT-OWNER-001"]
    assert "historical BOQ quantities (LEGACY values are not evidence)" in t["never_used"]


def test_threshold_strips_stay_physically_separate():
    th = _r("THRESHOLD_SITE_REGISTER")
    o = th["old_revision_wet_rows"]
    assert (o["ROOM_FOOTPRINT_m2"], o["legacy_minus_room_m2"]) == (17.7425, 0.12)
    assert {t["allocation"] for t in th["all_new_thresholds"]} == {"TRADE_RULE_REQUIRED"}


def test_sf3_duplicate_is_explicit_and_kept():
    d = _r("DUPLICATE_OCCURRENCE_REGISTER")["sf3"]
    assert [g["occurrences"] for g in d] == [["700047", "700051"]] and d[0]["kept"].startswith("ALL")


def test_xref_inventory_continues_only_with_the_claimed_occurrences():
    x = _r("XREF_SCOPE_CLAIMS")
    assert {h: v["state"] for h, v in x["inventory_new_revision"].items()} == {
        "16783": "XREF_MISSING_OWNER_CONFIRMED_NONCONTRIBUTING", "17716": "XREF_MISSING_OWNER_CONFIRMED_NONCONTRIBUTING"}
    assert x["blocking_unrealised_after_claim"] == [] and x["source_complete"].startswith("NOT DECLARED")


def test_owner_register_asks_nothing_and_never_an_expected_quantity():
    o = _r("OWNER_ACTION_REGISTER")
    assert o["required_now"] == [] and o["owner_review_open"] == []
    assert o["headline"] == "NO OWNER ACTION REQUIRED FOR THE NEXT ROUND"
    assert all(a.get("never", "an expected quantity") == "an expected quantity" for a in o["prepared_not_asked"])


def test_gates():
    g = _r("R8_10_DECISION_REGISTER")["gates"]
    assert (g["MIGRATION_PLANNING_READY"], g["MIGRATION_EXECUTION_READY"], g["PRODUCTION_MIGRATION"]) == \
        ("YES", "NO", "NO")
    assert _r("P7757_R8_10_SHADOW")["ts01_certificate"] == "UNIT_UNRESOLVED"
