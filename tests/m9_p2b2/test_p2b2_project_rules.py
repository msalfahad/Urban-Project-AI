"""Phase 2B-2 (Parts 2 and 5): Level A Urban master standards and Level B project rules - a project rule overrides the
Urban standard only within its scope, the most specific scope wins, a disagreement is a conflict (never discarded),
both values are kept, and the Project Engineering Rules Sheet (15 sections, 7 states) carries a hash that changes
when a rule changes. Synthetic inputs only."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import knowledge as K          # noqa: E402
from engine.source import project_rules as PR     # noqa: E402


def doc(*rules, revision="REV-A"):
    return {"schema": PR.SCHEMA, "project_id": "SYNTHETIC P2B2", "drawing_revision": revision, "rules": list(rules)}


def rule(rid, rule_id, parameter, value, scope, kind="DETAIL", ref="detail 3 / A-501"):
    return {"id": rid, "rule_id": rule_id, "parameter": parameter, "value": value, "scope": scope,
            "source": {"kind": kind, "ref": ref}}


BATH_1F = {"floor": "1F", "room_id": "1F-R1", "codes": ["BATHROOM"]}
BATH_GF = {"floor": "GF", "room_id": "GF-R2", "codes": ["BATHROOM"]}
BALCONY_1F = {"floor": "1F", "room_id": "1F-R3", "codes": ["BALCONY"]}


def resolver(*rules, rooms=()):
    with K.using("1.1.0"):
        d = PR.load(doc(*rules))
        return PR.Resolver(d, bindings=PR.bind(d, rooms=list(rooms)))


def test_a_project_upturn_overrides_the_urban_standard_only_in_its_scope():
    """'Urban Project standard waterproofing upturn = 0.20 m. Approved project detail specifies 0.30 m. Applied rule
    = 0.30 m for the applicable area. Retain both values and cite the governing source.'"""
    r = resolver(rule("PR-1", "UP-WP-003", "upturn_h_m", 0.30, {"kind": "FLOOR", "floor": "1F", "types": ["BATHROOM"]}))
    with K.using("1.1.0"):
        a = r.get("UP-WP-003", "upturn_h_m", BATH_1F)
        b = r.get("UP-WP-003", "upturn_h_m", BATH_GF)
        c = r.get("UP-WP-003", "upturn_h_m", BALCONY_1F)
    assert (a["value"], a["state"], a["urban_value"], a["project_rule_ids"]) == (0.30, "PROJECT_SPECIFIED", 0.20,
                                                                                 ["PR-1"])
    assert a["source"] == "DETAIL: detail 3 / A-501"
    for x in (b, c):                                            # outside the scope: the Urban standard, labelled
        assert (x["value"], x["state"], x["project_rule_ids"]) == (0.20, "OWNER_STANDARD_ASSUMED", [])


def test_the_most_specific_scope_wins():
    rooms = [{"room_id": "1F-R1", "floor": "1F", "polygon_m": [(0, 0), (3, 0), (3, 2), (0, 2)], "codes": ["BATHROOM"]}]
    r = resolver(rule("PR-1", "UP-WP-003", "upturn_h_m", 0.25, {"kind": "PROJECT"}),
                 rule("PR-2", "UP-WP-003", "upturn_h_m", 0.30, {"kind": "FLOOR", "floor": "1F"}),
                 rule("PR-3", "UP-WP-003", "upturn_h_m", 0.40, {"kind": "ROOM", "floor": "1F", "point_m": [1.0, 1.0]}),
                 rooms=rooms)
    with K.using("1.1.0"):
        a = r.get("UP-WP-003", "upturn_h_m", BATH_1F)
        b = r.get("UP-WP-003", "upturn_h_m", BATH_GF)
        c = r.get("UP-WP-003", "upturn_h_m", dict(BATH_1F, room_id="1F-R9"))
    assert (a["value"], a["project_rule_ids"], sorted(a["overridden"])) == (0.40, ["PR-3"], ["PR-1", "PR-2"])
    assert (b["value"], b["project_rule_ids"]) == (0.25, ["PR-1"])
    assert (c["value"], c["project_rule_ids"]) == (0.30, ["PR-2"])


def test_two_project_rules_that_disagree_are_a_conflict_never_discarded():
    r = resolver(rule("PR-1", "UP-WP-002", "lap_m", 0.15, {"kind": "PROJECT"}),
                 rule("PR-2", "UP-WP-002", "lap_m", 0.12, {"kind": "PROJECT"}, kind="SPECIFICATION", ref="spec 07 10"))
    with K.using("1.1.0"):
        a = r.get("UP-WP-002", "lap_m", BATH_GF)
    assert a["state"] == "CONFLICT_REVIEW" and a["value"] is None
    assert sorted(x["id"] for x in a["conflict"]) == ["PR-1", "PR-2"] and a["urban_value"] == 0.10
    assert sorted(x["value"] for x in a["conflict"]) == [0.12, 0.15]
    # the same value from two sources is not a conflict
    r2 = resolver(rule("PR-1", "UP-WP-002", "lap_m", 0.15, {"kind": "PROJECT"}),
                  rule("PR-2", "UP-WP-002", "lap_m", 0.15, {"kind": "PROJECT"}, kind="SPECIFICATION", ref="spec"))
    with K.using("1.1.0"):
        assert r2.get("UP-WP-002", "lap_m", BATH_GF)["value"] == 0.15


def test_a_conflicting_project_rule_is_never_shown_as_applied():
    """on the rules sheet both rules of a conflict are CONFLICT_REVIEW with no applied value (their own rows and the
    section-14 row), the standard row has no applied value, and both project values are kept."""
    with K.using("1.1.0"):
        d = PR.load(doc(rule("PR-1", "UP-WP-002", "lap_m", 0.15, {"kind": "PROJECT"}),
                        rule("PR-2", "UP-WP-002", "lap_m", 0.12, {"kind": "PROJECT"}, kind="SPECIFICATION",
                             ref="spec 07 10")))
        sheet = PR.rules_sheet(d, bindings=PR.bind(d), project_id="SYNTHETIC P2B2",
                               drawing={"file": "x.dxf", "sha256": "0" * 64})
    rows = {r["row_id"]: r for r in sheet["rows"]}
    for rid in ("P-PR-1", "P-PR-2", "C-PR-1-PR-2", "S-UP-WP-002-lap_m-WET"):
        assert rows[rid]["status"] == "CONFLICT_REVIEW" and rows[rid]["applied_rule"]["value"] is None, rid
    assert rows["P-PR-1"]["notes"].startswith("PROJECT_RULE_CONFLICT") and "PR-2" in rows["P-PR-1"]["notes"]
    assert sorted(p["value"] for p in rows["C-PR-1-PR-2"]["drawing_specification"]) == [0.12, 0.15]


def test_an_unbound_point_scope_is_reported_not_applied():
    rooms = [{"room_id": "GF-R2", "floor": "GF", "polygon_m": [(0, 0), (3, 0), (3, 2), (0, 2)], "codes": ["BATHROOM"]}]
    with K.using("1.1.0"):
        d = PR.load(doc(rule("PR-9", "UP-WP-003", "upturn_h_m", 0.30, {"kind": "ROOM", "floor": "GF",
                                                                         "point_m": [50.0, 50.0]})))
        b = PR.bind(d, rooms=rooms)
        r = PR.Resolver(d, bindings=b)
        assert b["PR-9"]["state"] == "UNBOUND"
        assert r.get("UP-WP-003", "upturn_h_m", BATH_GF)["value"] == 0.20
        sheet = PR.rules_sheet(d, bindings=b, project_id="SYNTHETIC P2B2", drawing={"file": "x.dxf", "sha256": "0"})
    row = next(x for x in sheet["rows"] if x.get("project_rule_id") == "PR-9")
    assert row["status"] == "CONFLICT_REVIEW" and "PROJECT_RULE_UNBOUND" in row["notes"]


def test_an_unsupported_parameter_is_listed_never_applied():
    with K.using("1.1.0"):
        d = PR.load(doc(rule("PR-1", "UP-WP-003", "colour", "blue", {"kind": "PROJECT"})))
        sheet = PR.rules_sheet(d, bindings=PR.bind(d, rooms=[]), project_id="P", drawing={"file": "x", "sha256": "0"})
    row = next(x for x in sheet["rows"] if x.get("project_rule_id") == "PR-1")
    assert row["status"] == "ENGINE_LIMITATION"


def test_an_invalid_value_is_refused():
    with K.using("1.1.0"):
        for bad in (rule("PR-1", "UP-WP-003", "upturn_h_m", 3.0, {"kind": "PROJECT"}),
                    rule("PR-1", "UP-WP-002", "lap_m", "wide", {"kind": "PROJECT"}),
                    rule("PR-1", "UP-WP-003", "upturn_h_m", 0.3, {"kind": "GALAXY"}),
                    dict(rule("PR-1", "UP-WP-003", "upturn_h_m", 0.3, {"kind": "PROJECT"}), source={})):
            with pytest.raises(PR.ProjectRulesError):
                PR.load(doc(bad))
        with pytest.raises(PR.ProjectRulesError):
            PR.load({"schema": "SOMETHING_ELSE", "rules": []})


def test_the_rules_sheet_has_every_section_and_state():
    with K.using("1.1.0"):
        d = PR.load(doc(rule("PR-1", "UP-WP-003", "upturn_h_m", 0.30, {"kind": "LOCATION_TYPE", "types": ["BALCONY"]}),
                        rule("PR-2", "UP-DOOR-OPEN-002", "required_nominal_door_m", 0.80,
                             {"kind": "DOOR_CATEGORY", "categories": ["BATHROOM_PVC"]}, kind="OWNER_PROJECT_APPROVAL",
                             ref="owner approval 2026-10-16")))
        sheet = PR.rules_sheet(d, bindings=PR.bind(d, rooms=[]), project_id="SYNTHETIC P2B2",
                               drawing={"file": "x.dxf", "sha256": "0" * 64},
                               facts={"schema": "URBAN_ARCH_FACTS_V1",
                                      "opening_heights": {"WINDOW": {"value_m": 1.5, "authority": "SOURCE: schedule"}}})
    assert [s["id"] for s in sheet["sections"]] == list(PR.SECTIONS)
    assert len(PR.SECTIONS) == 15
    for row in sheet["rows"]:
        assert set(PR.ROW_FIELDS) <= set(row), row["row_id"]
        assert row["status"] in PR.STATES
    states = {r["status"] for r in sheet["rows"]}
    assert {"PROJECT_SPECIFIED", "OWNER_STANDARD_ASSUMED", "OWNER_PROJECT_APPROVED", "MISSING_DOCUMENT",
            "ENGINE_LIMITATION", "DRAWING_CONFIRMED"} <= states
    up = next(r for r in sheet["rows"] if r.get("project_rule_id") == "PR-1")
    assert up["urban_standard"]["value"] == 0.20 and up["applied_rule"]["value"] == 0.30
    assert up["section"] == "08_WATERPROOFING" and "FIN.WP.WALL_UPTURN" in up["impact"]["items"]
    door = next(r for r in sheet["rows"] if r.get("project_rule_id") == "PR-2")
    assert door["urban_standard"]["value"] == 0.90 and door["applied_rule"]["value"] == 0.80
    assert door["status"] == "OWNER_PROJECT_APPROVED"
    assert len(sheet["rules_sha256"]) == 64 and len(sheet["sheet_sha256"]) == 64


def test_a_changed_rules_sheet_invalidates_earlier_outputs():
    def sheet(v):
        with K.using("1.1.0"):
            d = PR.load(doc(rule("PR-1", "UP-WP-003", "upturn_h_m", v, {"kind": "PROJECT"})))
            return PR.rules_sheet(d, bindings=PR.bind(d, rooms=[]), project_id="P", drawing={"file": "x", "sha256": "0"})
    a, a2, b = sheet(0.30), sheet(0.30), sheet(0.25)
    assert a["rules_sha256"] == a2["rules_sha256"] and a["rules_sha256"] != b["rules_sha256"]
    inv = PR.invalidation(a, b)
    assert inv["state"] == "RULES_CHANGED" and "FIN.WP.WALL_UPTURN" in inv["affected_items"]
    assert any(c["project_rule_id"] == "PR-1" for c in inv["changed"])
    assert "WATERPROOFING" in inv["affected_trades"]
    assert PR.invalidation(a, a2)["state"] == "UNCHANGED"
    assert PR.invalidation(None, a)["state"] == "FIRST_RUN"
