"""Qortuba RC1 on the committed registers: one canonical line per payable item (Q-03 / Q-03P are aliases, never
lines), room-by-room breakdowns that reconcile, the floor partition, the opening schedules with attribute bases, the
PAINTRY counter footprint resolved by the owner method + object identity, no quantity change, the workbook view and
the freeze with real digests only."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from engine.source import boq_canonical as BC, freeze_schema as FS, opening_register as OR

REG = Path(__file__).parent / "registers"


def _r(n):
    return json.loads((REG / f"{n}.json").read_text())


def test_canonical_boq_has_one_line_per_item_and_legacy_ids_only_as_attributes():
    c = _r("CANONICAL_BOQ")
    assert BC.validate(c, tol=5e-5)["state"] == "PASS" and len(c["items"]) == 21
    ids = [i["canonical_item_id"] for i in c["items"]]
    assert not {"Q-03", "Q-03P", "Q-11", "Q-12", "QOR-R819-Q-03", "QOR-R819-Q-03P"} & set(ids)
    al = {a["alias"]: a for a in _r("BOQ_ALIAS_REGISTER")["aliases"]}
    assert al["QOR-R819-Q-03"]["canonical"] == "FLR-02" and al["QOR-R819-Q-03"]["relation"] == BC.MISLABELLED
    assert al["QOR-R819-Q-03P"]["canonical"] == "FLR-03" and al["OWNER-RULES-V1:Q-03"]["canonical"] == "WPF-01"
    assert _r("BOQ_ALIAS_REGISTER")["aliases_in_summary"] == []
    pairs = BC.validate(c, tol=5e-5)["measure_pairs"]
    assert ["MRB-01", "MRB-02"] in pairs and ["WIN-01", "WIN-02"] in pairs


def test_every_quantity_is_unchanged_from_r8_20():
    q = _r("QA_RECONCILIATION")["regression_vs_r8_20"]
    assert q["all_unchanged"] and q["covers_all_17_r8_20_rows"]
    it = {i["canonical_item_id"]: i["qty"] for i in _r("CANONICAL_BOQ")["items"]}
    assert (it["FLR-01"], it["FLR-02"], it["FLR-03"], it["CLG-01"]) == (111.8988, 17.7425, 11.685, 140.637)
    assert (it["SKT-01"], it["HPR-01"], it["WPF-01"], it["WPU-01"]) == (94.13682, 94.13682, 29.4275, 44.2)
    assert (it["MRB-01"], it["MRB-02"]) == (0.51, 3.4)


def test_rooms_reconcile_and_the_floor_is_one_partition():
    m = _r("ROOM_QUANTITY_MATRIX")
    assert m["state"] == "PASS" and not m["not_reconciled"] and not m["unplaced"]
    p = _r("QA_RECONCILIATION")["floor_partition"]
    assert p["state"] == "PASS" and not p["in_two_items"] and not p["in_no_item"] and p["keys"] == 15
    assert p["physical_floor_m2"] == pytest.approx(141.836289) and p["finish_items_sum_m2"] == 141.8363
    rr = _r("ROOM_REGISTER")
    assert rr["counts"] == {"rooms": 8, "door_strips": 7}
    assert len({r["display"] for r in rr["rooms"]}) == 8      # equal labels never merged


def test_physical_identity_audit_and_reconciliation_pass():
    q = _r("QA_RECONCILIATION")
    assert q["state"] == "PASS" and q["physical_surface_identity"]["state"] == "PASS"
    assert set(q["physical_surface_identity"]["checks"].values()) == {"PASS"}
    assert q["door_count_cross_check"]["consistent"] and q["per_room_wall_conservation"] is True
    for v in q["trade_breakdowns"].values():
        assert v["breakdown_sum"] == pytest.approx(v["qty"], abs=5e-5)


def test_opening_schedules_with_attribute_bases():
    o = _r("OPENING_REGISTER")
    assert OR.validate(o["records"])["state"] == "PASS"
    s = o["schedules"]
    assert s["internal_door_count"] == 6 and s["entrance_doors"] == ["I677"] and s["out_of_scope"] == ["I1028"]
    assert s["window_count"] == 6 and s["sliding_glazed_doors"] == ["SGD-H533"] and len(s["open_passages"]) == 2
    rec = {r["opening_id"]: r for r in o["records"]}
    for d in s["internal_doors"]:
        assert rec[d]["width_basis"] == "SOURCE" and rec[d]["height_basis"] == "OWNER_PROJECT_PARAMETER"
        assert rec[d]["material"] == "PVC" and rec[d]["material_basis"] == "URBAN_STANDARD"
    assert rec["I677"]["material"] is None and "height_note" in rec["I677"]
    g = rec["SGD-H533"]
    assert (g["clear_width_m"], g["height_m"], g["area_m2"], g["material"]) == (2.75, 2.2, 6.05, None)
    assert all(not rec[p]["door_present"] for p in s["open_passages"])
    assert _r("DOOR_REGISTER")["width_fallback_used"] is False
    gl = _r("GLAZING_REGISTER")
    assert len(gl["aluminium_windows"]) == 4 and sorted(gl["material_not_established"]) == [
        "SGD-H533", "W-H1325", "W-H1518"]


def test_the_paintry_counter_footprint_is_resolved_by_the_owner_method_and_object_identity():
    f = _r("OBJECT_FOOTPRINT_REGISTER")
    assert f["unresolved"] == [] and len(f["resolved"]) == 3
    u = f["sites"]["Q-12|SITE-8c1c7563d5252c50"]
    assert sorted(o["key"].split("|")[1] for o in u["objects"]) == ["H478", "H482", "H532", "H536", "H541"]
    assert {o["observed_class"] for o in u["objects"]} == {"SANITARY_FIXTURE"}
    assert {o["object_class"] for o in u["objects"]} == {"LATER_INSTALLED_CABINETRY"}
    assert u["policy"] == ["URBAN-FLOOR-FINISH-BEFORE-CABINETRY-METHOD@v1"] and u["treatment"] == "FOOTPRINT_INCLUDED"
    assert u["identity_facts"] == ["QORTUBA-NEW-PAINTRY-COUNTER-CABINETRY-OWNER-001@v1"]
    assert all(b["binding"] == "APPLIES" for b in u["identity_bindings"])
    assert u["outline_faces"]["faces_m2"] == [0.6, 5.44, 5.645]          # diagnostic only, nothing deducted
    it = {i["canonical_item_id"]: i for i in _r("CANONICAL_BOQ")["items"]}
    assert it["FLR-03"]["qty"] == 11.685 and all(i["status"] == BC.COMPLETE for i in it.values())
    assert it["FLR-03"]["resolved_blockers"][0]["blocker"].startswith("OBJECT_FOOTPRINT_IMPLICIT")
    p = _r("PAINTRY_FLOOR_RESOLUTION")
    assert p["state"] == "RESOLVED" and p["site_area_m2"] == 11.685 and p["trail"][-1]["deducted_m2"] == 0.0
    assert p["geometry_changed"] is False and p["hardcoded_value"] is False
    m = _r("URBAN_FLOOR_CABINET_METHOD")
    assert m["rule"]["rule_id"] == "URBAN-FLOOR-FINISH-BEFORE-CABINETRY-METHOD" and m["geometry_changed"] is False
    assert "BUILT_PLINTH" in m["rule"]["excluded_object_classes"] and f["assumed"].startswith("NOTHING")
    dry = [v for k, v in f["sites"].items() if k.startswith("Q-13|")]
    assert all(v["policy"] == ["QORTUBA-NEW-FLOOR-OBJECT-FOOTPRINT-OWNER-001@v1"] for v in dry)


def test_workbook_view_validates_and_rebuilds_byte_identical():
    x = _r("BOQ_XLSX_STATUS")
    v = x["readback_validation"]
    assert v["state"] == "PASS" and not x["formulas"] and x["second_write_identical_bytes"]
    assert v["quantity_cells_checked"] > 300 and not v["register_mismatches"] and not v["alias_lines_in_summary"]
    assert [k for k, r in x["roles"].items() if r == "ADDITIVE_SUMMARY"] == ["01_BOQ_SUMMARY"]
    assert len(x["sheets"]) == 14 and x["summary_lines"] == 21


def test_freeze_gates_and_blind_villa_preparation():
    f = _r("QORTUBA_RC1_FREEZE")
    assert f["frozen"] is True and f["release_status"] == "SHADOW / RC1_REFERENCE" and not f["contractual_approval"]
    assert f["dwg_dxf_anchor"] == "NOT_ESTABLISHED" and f["open_items"] == [] and f["open_owner_question"] == "NONE"
    assert f["xlsx_content_digest"] == _r("BOQ_XLSX_STATUS")["content_digest"]
    assert f["canonical_boq_digest"] == _r("CANONICAL_BOQ")["digest"]
    s = _r("SOURCE_ANCHOR_STATUS")
    assert s["blocks_rc1_reference_freeze"] is False and s["blocks_release_authority"] is True
    d = _r("RC1_DECISION_REGISTER")
    assert d["gates"]["PRODUCTION_MIGRATION"] == "NO" and d["gates"]["QORTUBA_RC1_REFERENCE_READY"] == "YES"
    assert len(d["answers"]) == 59 and "54" not in {k.split("_")[0] for k in d["answers"]}
    assert not any(a["id"] == "PAINTRY_COUNTER_FOOTPRINT" for a in d["owner_actions"])
    p = _r("BLIND_VALIDATION_PLAN")
    assert len(p["metrics"]) == 19 and "NO single global accuracy" in p["reporting"]
    assert "expected quantities" in _r("BLIND_VILLA_INTAKE_SCHEMA")["never_before_freeze"]
    assert _r("DONOR_REUSE_REGISTER")["duplicating_full_engines"] is False


def test_every_freeze_identity_is_a_real_digest_and_the_schema_validates():
    f, a = _r("QORTUBA_RC1_FREEZE"), _r("FREEZE_DIGEST_AUDIT")
    assert FS.validate(f, a["schema"])["state"] == "PASS" and a["validation"]["state"] == "PASS"
    assert "topology_digest" not in f and "dwg_known_sha256_prefix" not in f
    assert re.fullmatch(r"[0-9a-f]{64}", f["topology_result_digest"]) and re.fullmatch(r"[0-9a-f]{64}",
                                                                                         f["dwg_sha256"])
    assert f["topology_input_digest"] == f["run_id"] and f["topology_result_digest"] != f["topology_input_digest"]
    assert all(re.fullmatch(r"[0-9a-f]{64}", v) for r in f["row_digests"].values() for v in r.values())
    assert a["old_values"]["topology_digest"] is False
    t = _r("TOPOLOGY_FREEZE")
    assert t["topology_result_digest"]["value"] == f["topology_result_digest"]
    assert t["topology_result_digest"]["counts"]["sites"] == 72
