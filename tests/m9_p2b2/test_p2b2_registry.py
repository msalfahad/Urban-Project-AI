"""Phase 2B-2 (Part 6): the engineering knowledge registry 1.1.0 - the newly approved waterproofing, project-rule and
door-feasibility standards are machine-readable records with their authority, code and tests; superseded values keep
their history; registry 1.0.0 (read by ARCH_TAKEOFF_V2.3) is unchanged; the approved values cannot be reverted
silently."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import knowledge as K          # noqa: E402
from engine.source import rule_store as RS        # noqa: E402

# the frozen 1.0.0 registry (Phase 2B-1, commit 811c10e): ARCH_TAKEOFF_V2.3 reads exactly these bytes
V1_0_SHA256 = hashlib.sha256((ROOT / "knowledge" / "URBAN_ENGINEERING_KNOWLEDGE_1.0.0.json").read_bytes()).hexdigest()


def reg11():
    with K.using("1.1.0"):
        return K.registry()


def ids11():
    return {r["rule_id"]: r for r in reg11()["rules"]}


def test_registry_1_1_is_the_builder_output():
    p = subprocess.run([sys.executable, "-I", str(ROOT / "tools" / "kb_build_1_1.py"), "--check"], capture_output=True,
                       text=True)
    assert p.returncode == 0, p.stdout + p.stderr


def test_registry_1_1_validates_with_every_code_and_test_link():
    assert K.validate(reg11(), links=True) == []


def test_registry_1_0_is_unchanged_and_stays_the_default():
    reg = json.loads((ROOT / "knowledge" / "URBAN_ENGINEERING_KNOWLEDGE_1.1.0.json").read_text(encoding="utf-8"))
    assert reg["base"] == {"version": "1.0.0", "sha256": V1_0_SHA256}
    assert K.version() == "1.0.0" and K.rule_set() == "URBAN_KB_1.0.0" and K.RULE_SET == "URBAN_KB_1.0.0"
    with K.using("1.1.0"):
        assert K.version() == "1.1.0" and K.RULE_SET == "URBAN_KB_1.1.0"
        assert K.digest() == hashlib.sha256((ROOT / "knowledge" / "URBAN_ENGINEERING_KNOWLEDGE_1.1.0.json")
                                            .read_bytes()).hexdigest()
    assert K.version() == "1.0.0" and K.digest() == V1_0_SHA256
    old = {r["rule_id"] for r in K.registry()["rules"]}
    assert old <= set(ids11()), "1.1.0 drops a 1.0.0 rule"


def test_the_approved_waterproofing_values_cannot_silently_change():
    """the owner's 2026-10-16 values: a future change must be a new record version with its history entry."""
    r = ids11()
    assert r["UP-WP-001"]["logic"]["roll_width_m"] == 1.00 and r["UP-WP-001"]["logic"]["roll_length_m"] == 10.00
    assert r["UP-WP-001"]["logic"]["gross_roll_area_m2"] == 10.00
    assert r["UP-WP-002"]["logic"]["lap_m"] == 0.10
    assert "flat" in " ".join(r["UP-WP-002"]["logic"]["never"]).lower()
    assert r["UP-WP-003"]["logic"]["upturn_h_m"] == 0.20
    for i in ("UP-WP-001", "UP-WP-002", "UP-WP-003", "UP-WP-004", "UP-WP-MAT-001", "UP-WP-LAY-001",
              "UP-WP-DOOR-001", "UP-RULES-001", "UP-DOOR-FEAS-001"):
        assert r[i]["status"] == "OWNER_APPROVED", i
        assert "2026-10-16" in r[i]["authority"]["received"], i
        assert r[i]["tests"] and r[i]["code"], i
    with K.using("1.1.0"):
        assert K.wp_standard() == {"roll_width_m": 1.0, "roll_length_m": 10.0, "gross_roll_area_m2": 10.0,
                                   "lap_m": 0.1, "upturn_h_m": 0.2}


def test_the_superseded_upturn_keeps_its_history():
    """'These replace the earlier general 0.15 m upturn rule. Preserve the supersession history.'"""
    r = ids11()
    old = r["UP-WP-UPTURN-015"]
    assert old["status"] == "DEPRECATED" and old["superseded_by"] == "UP-WP-003"
    assert old["logic"]["upturn_h_m"] == 0.15
    assert "UP-WP-UPTURN-015" in r["UP-WP-003"]["supersedes"]
    assert any(h["version"] == "1.1.0" for h in r["UP-WP-003"]["history"])
    # the rule store keeps its own history (frozen): 0.15 m at 1.0.0, 0.20 m at 2.0.0
    assert RS.rule("UP-WP-002", "1.5.0")["value"] == 0.2


def test_the_approved_door_values_cannot_silently_change():
    r = ids11()
    t = r["UP-DOOR-OPEN-002"]["logic"]["table"]
    assert (t["INTERNAL_PVC"], t["BATHROOM_PVC"], t["EXTERNAL_ALUMINIUM"]) == (
        {"required_nominal_door_m": 1.0, "required_wall_opening_m": 1.1},
        {"required_nominal_door_m": 0.9, "required_wall_opening_m": 1.0},
        {"required_nominal_door_m": 1.0, "required_wall_opening_m": 1.1})
    assert r["UP-DOOR-OPEN-002"]["logic"]["allowance_m"] == 0.1
    assert r["UP-DOOR-HGT-001"]["logic"]["owner_reference_height_m"] == {
        "BATHROOM_PVC": 2.2, "EXTERNAL_ALUMINIUM": 2.2, "INTERNAL_PVC": 2.2, "MAIN_ENTRANCE": 2.5}
    assert r["UP-DOOR-HGT-001"]["logic"]["state_label"] == "OWNER_STANDARD_ASSUMED"
    ex = r["UP-DOOR-OPEN-002"]["logic"]["available_nominal_example"]
    assert (ex["cad_wall_opening_m"], ex["available_nominal_m"], ex["required_enlargement_m"]) == (0.8, 0.7, 0.2)


def test_the_rule_store_ids_are_never_resolved_as_registry_ids():
    """CF-13: the rule store and the registry both use UP-WP-001 .. -004 with different meanings; a reference always
    carries its rule set, and the registry record names the rule-store record it relates to."""
    with K.using("1.1.0"):
        ref = K.ref("UP-WP-002")
        assert ref["rule_set"] == "URBAN_KB_1.1.0" and K.rule("UP-WP-002")["logic"]["lap_m"] == 0.1
    assert RS.rule("UP-WP-002", "1.5.0")["rule_name"].startswith("The wet-room membrane turns up")
    r = ids11()
    cw = {c["registry"]: c["rule_store"] for c in reg11()["rule_store_crosswalk"]}
    assert cw["UP-WP-002"].startswith("UP-WP-005") and cw["UP-WP-003"].startswith("UP-WP-002")
    assert any(c["id"] == "CF-13" for c in reg11()["conflicts"])
    assert r["UP-WET-001"]["logic"]["scope"]["waterproofing"].count("rules/") >= 1


def test_every_new_conflict_is_recorded_with_a_resolution():
    cf = {c["id"]: c for c in reg11()["conflicts"]}
    for i in ("CF-12", "CF-13", "CF-14"):
        assert cf[i]["resolution"] and cf[i]["state"] in ("RESOLVED", "OPEN", "CONFLICTED"), i
    assert cf["CF-11"]["state"] == "OPEN"                                    # the head allowance stays an owner question


def test_unsupported_historical_notes_stay_reference_only():
    """Part 6: owner method records found in data/registry are kept as REFERENCE_ONLY, never promoted."""
    r = ids11()
    for i in ("UP-REF-REVEAL-001", "UP-REF-COLUMN-001", "UP-REF-DUCT-001", "UP-REF-CABINET-001"):
        assert r[i]["status"] == "REFERENCE_ONLY", i
        assert r[i]["authority"]["source"].startswith("data/registry/URBAN_OWNER_METHOD_RULES.json"), i


def test_every_new_catalogue_entry_is_reached_by_its_example():
    with K.using("1.1.0"):
        for q in K.registry()["question_catalogue"]:
            got = K.classify_question(q["example"])
            assert got is not None and (got["pattern"], got.get("item")) == (q["pattern"], q.get("item")), q["pattern"]
