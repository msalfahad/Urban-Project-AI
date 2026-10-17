"""Phase A3 frozen registers (built from the delivered drawings by research/external_engine_lab/alsenan_phase_a3.py).
Checks: the firewall held and the freeze validates; every footing tag is accounted for exactly once (computed or
blocked) and type totals are derived from the occurrence rows; F = 0.90 x 0.80 x 0.30 and no 0.60 m H exists; the
combined F / F10 outline is a blocked SOURCE_CONFLICT; column / beam / slab volumes stay blocked with no volume from a
count; rebar has no weight; the owner-derived salon height is scoped to the salon only; curved glazing is hosted by
the master bedroom and its height stays blocked; Qortuba did not change."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from engine.source import freeze_schema as FS

REG = Path(__file__).parent / "registers_a3"
LAB = Path(__file__).resolve().parents[2] / "research/external_engine_lab"
FREEZE = "ALSENAN_P7757_ST7757_PHASE_A3_FREEZE"
NAMES = ("ALSENAN_P7757_ST7757_PHASE_A3_FREEZE", "ALUMINIUM_GLAZING_REGISTER", "ARCH_BOQ", "BEAM_REGISTER",
         "BENCHMARK_FIREWALL", "BLOCKWORK_REGISTER", "COLUMN_REGISTER", "CONCRETE_REGISTER", "DONOR_REUSE_REGISTER",
         "DOUBLE_HEIGHT_ZONE_REGISTER", "ENTITY_ROLE_REGISTER", "FLOOR_CEILING_REGISTER", "FOOTING_REGISTER",
         "JOINERY_REGISTER", "OPENING_REGISTER", "OWNER_FACT_REGISTER", "OWNER_QUESTION_REGISTER",
         "PDF_VERTICAL_EVIDENCE_REGISTER", "PLAN_REGION_REGISTER", "QA_RECONCILIATION", "QORTUBA_REGRESSION",
         "REBAR_EVIDENCE_REGISTER", "ROOM_REGISTER", "ROOM_TOPOLOGY_REGISTER", "SKIRTING_REGISTER", "SLAB_REGISTER",
         "SOURCE_AUTHORITY_REGISTER", "SOURCE_MANIFEST", "STAIR_REGISTER", "STRAP_BEAM_REGISTER",
         "STRUCTURAL_RECONCILIATION", "STRUCT_TYPE_LIBRARY", "TEST_RESULTS", "WALL_BAND_REGISTER",
         "WALL_SURFACE_REGISTER", "WET_ROOM_REGISTER")
COMPLETE, BLOCKED = "COMPUTED_SHADOW_COMPLETE", "BLOCKED"


def R(n):
    p = REG / f"{n}.json"
    if not p.exists():
        pytest.skip(f"{n} not generated")
    return json.loads(p.read_text())


def test_all_registers_exist():
    assert sorted(p.stem for p in REG.glob("*.json")) == sorted(NAMES)


def test_firewall_held_and_freeze_validates():
    fw = R("BENCHMARK_FIREWALL")
    assert fw["audit_verdict"]["state"] == "PASS" and not fw["audit_verdict"]["violations"]
    assert fw["statements"]["FREELANCER_BOQ_SEEN"] == "NO" and fw["statements"]["WEB_APP_QUANTITIES_SEEN"] == "NO"
    fz = R(FREEZE)
    sys.path.insert(0, str(LAB))
    import alsenan_a3_registers as AR3
    assert FS.validate({k: v for k, v in fz.items() if k != "schema_validation"}, AR3.FREEZE_SCHEMA)["state"] == "PASS"
    assert fz["schema_validation"]["state"] == "PASS"
    assert fz["FREELANCER_BOQ_SEEN"] is False and fz["WEB_APP_QUANTITIES_SEEN"] is False
    assert fz["EXPECTED_TOTALS_USED"] is False and fz["comparison"].startswith("NOT STARTED")


def test_every_footing_tag_exactly_once_and_totals_derived():
    f = R("FOOTING_REGISTER")
    occ = f["occurrences"]
    keys = [o["mark_key"] for o in occ]
    assert len(keys) == len(set(keys)) == f["marks"]
    assert f["reconciliation"]["state"] == "PASS"
    for s in f["type_summary"]:
        mine = [o for o in occ if o["type"] == s["type"]]
        done = [o for o in mine if o["status"] == COMPLETE]
        assert s["count_tagged"] == len(mine) and s["count_computed"] == len(done)
        assert s["count_computed"] + s["count_conflict"] + s["count_blocked_other"] == s["count_tagged"]
        if done:
            assert abs(s["m3_total_computed"] - sum(o["qty"] for o in done)) < 1e-9
    for o in occ:
        assert o["schedule_row"]["type"] == o["type"]
        if o["status"] == COMPLETE:
            L, W, H = (o["dims"][k]["m"] for k in ("L", "W", "H"))
            assert abs(o["qty"] - L * W * H) < 1e-9
        else:
            assert o["qty"] is None and o["blockers"]


def test_F_schedule_size_and_no_0_60_height():
    f = R("FOOTING_REGISTER")
    s = next(x for x in f["type_summary"] if x["type"] == "F")
    assert (s["L_m"], s["W_m"], s["H_m"]) == (0.9, 0.8, 0.3) and abs(s["m3_each"] - 0.216) < 1e-12
    assert f["h_audit"]["state"] == "PASS" and not f["h_audit"]["rows_with_non_schedule_H"]
    for o in f["occurrences"]:
        if o.get("dims"):
            assert o["dims"]["H"]["m"] != 0.6


def test_combined_outline_is_a_blocked_source_conflict():
    f = R("FOOTING_REGISTER")
    assert len(f["forensic"]) == 1
    fx = f["forensic"][0]
    assert sorted(m["type"] for m in fx["marks_inside"]) == ["F", "F10"]
    assert fx["drawn_mm"] == [3250.0, 1400.0] and fx["explicit_local_dimensions"] == []
    inside = {m["key"] for m in fx["marks_inside"]}
    for o in f["occurrences"]:
        if o["mark_key"] in inside:
            assert o["geometry_state"] == "SOURCE_CONFLICT_COMBINED_OUTLINE" and o["status"] == BLOCKED
    # a strap measured to a face of that outline says so
    for s in R("STRAP_BEAM_REGISTER")["rows"]:
        if fx["outline"] in (s.get("clear") or []):
            assert s["support_outline_conflicts"] == [fx["outline"]] and s.get("dependency")


def test_concrete_total_is_footings_plus_measured_straps():
    c = R("CONCRETE_REGISTER")
    t = c["totals"]
    straps = [s for s in R("STRAP_BEAM_REGISTER")["rows"] if s["status"] == COMPLETE]
    assert abs(t["straps_m3"] - round(sum(s["volume_m3"] for s in straps), 6)) < 1e-9
    assert abs(t["deterministic_total_m3"] - round(t["footings_m3"] + t["straps_m3"], 6)) < 1e-9
    for r in c["boq_rows"]:
        if r["status"] == BLOCKED:
            assert r["qty"] is None and r["blockers"] and r["class"].startswith("BLOCKED")


def test_column_beam_slab_volumes_blocked_and_never_from_count():
    rows = {r["item"]: r for r in R("CONCRETE_REGISTER")["boq_rows"]}
    for k in ("S3-COL-VOL", "S3-BM-VOL", "S3-GB-VOL", "S3-STR-VOL"):
        assert rows[k]["qty"] is None and rows[k]["status"] == BLOCKED
    assert "floor-to-floor is NOT a column concrete height" in R("COLUMN_REGISTER")["height"]
    for b in R("BEAM_REGISTER")["rows"]:
        assert b["volume_m3"] is None
    for s in R("SLAB_REGISTER")["slabs"].values():
        assert s["volume_m3"] is None and s["area_m2"] is None
    assert R("STRUCTURAL_RECONCILIATION")["state"] == "PASS"


def test_rebar_definitions_only():
    rb = R("REBAR_EVIDENCE_REGISTER")
    assert rb["tonnage_kg"] is None and rb["never"] == "kg/m3"
    assert all(d["weight_kg"] is None for d in rb["definitions"])
    for r in R("CONCRETE_REGISTER")["boq_rows"]:
        if r["item"].startswith("S3-RBR"):
            assert r["qty"] is None


def test_owner_derived_height_scoped_to_the_salon():
    facts = {f["id"]: f for f in R("OWNER_FACT_REGISTER")["facts"]}
    h = facts["OF-A3-SALON-HEIGHT"]
    assert h["authority"] == "PROJECT_OWNER_DERIVED_DIMENSION" and h["fact"]["finished_aluminium_height_m"] == 3.65
    assert "a source-measured height" in h["not"]
    g = R("ALUMINIUM_GLAZING_REGISTER")
    assert g["salon"]["binding"] == "UNIQUE_WIDTH_MATCH" and g["salon"]["width_m"] == 6.33
    assert abs(g["salon"]["area_m2"] - 6.33 * 3.65) < 1e-9
    users = [r["item"] for r in R("ARCH_BOQ")["rows"] if r["qty"] is not None and "3.65" in json.dumps(r)]
    assert users == ["A3-ALU-SALON"]


def test_curved_glazing_hosted_by_master_bedroom_height_blocked():
    g = R("ALUMINIUM_GLAZING_REGISTER")["curved"]
    mb = g["master_bedroom"]
    assert mb["binding"] == "UNIQUE_CURVED_GLAZING_ON_GF" and mb["height_m"] is None and mb["area_m2"] is None
    item = next(c for c in g["items"] if c["id"] == mb["item"])
    assert "MASTER BED ROOM" in item["host_labels"]
    assert sum(1 for c in g["items"] if c["floor"] == "GF") == 1
    rows = {r["item"]: r for r in R("ARCH_BOQ")["rows"]}
    assert rows["A3-CGL-MB-A"]["qty"] is None and rows["A3-CGL-MB-A"]["class"] == "BLOCKED_HEIGHT"


def test_double_height_zone_corroborated_extent_blocked():
    z = R("DOUBLE_HEIGHT_ZONE_REGISTER")["zones"]
    assert len(z) == 1 and z[0]["state"] == "DOUBLE_HEIGHT_ZONE_CORROBORATED"
    assert z[0]["wall_heights"].startswith("BLOCKED")


def test_rows_classified_and_qa_clean():
    for r in R("ARCH_BOQ")["rows"] + R("CONCRETE_REGISTER")["boq_rows"]:
        assert r["class"]
        if r["status"] == BLOCKED:
            assert r["qty"] is None and r["blockers"]
    q = R("QA_RECONCILIATION")
    assert q["silent_critical_errors"] == 0 and q["xlsx"]["readback"]["state"] == "PASS"


def test_qortuba_unchanged():
    assert R("QORTUBA_REGRESSION")["state"] in ("UNCHANGED", "PROVENANCE_ONLY")


def test_owner_questions_never_ask_for_quantities():
    oq = R("OWNER_QUESTION_REGISTER")
    assert [q["id"] for q in oq["questions"]] == ["OQ3-S1", "OQ3-A1", "OQ3-A2"]
    assert "expected quantities" in oq["never_asked"]
    for q in oq["questions"]:
        assert "quantity" not in q["question"].lower() and "boq" not in q["question"].lower()
