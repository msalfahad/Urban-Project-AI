"""Migration round 1 is a design: its scope register says what it needs and that none of it is met."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REG = Path(__file__).parent / "registers" / "R8_MIGRATION_ROUND1_SCOPE.json"
DOC = ROOT / "docs" / "R8_MIGRATION_ROUND1_DESIGN.md"


def reg():
    return json.loads(REG.read_text())


def test_round1_is_design_only_and_not_execution_ready():
    r = reg()
    assert r["status"] == "DESIGN_ONLY_NOT_EXECUTED" and r["execution_ready"] is False
    g = r["current_gate_state"]
    assert g["independent_real_reconciliation"] == "BLOCKED_EXTERNAL_INPUT"
    assert g["qualified_required_signatures"] == 0
    assert g["designation_review"] == "PENDING_REVIEW"
    assert g["unit"] != "CONFIRMED" and g["release"] == "PREVIEW"
    text = DOC.read_text()
    assert "PRODUCTION_MIGRATION = NO" in text and "MIGRATION_EXECUTION_READY = NO" in text


def test_scope_is_exactly_the_exact_match_floor_area_rows():
    r = reg()
    assert [x["row_id"].split("|")[0] for x in r["rows"]] == ["Q-03", "Q-03P", "Q-11", "Q-12", "Q-13", "Q-14"]
    assert all(abs(x["canonical_preview_value"] - x["current_value"]) < 1e-9 for x in r["rows"])
    assert r["rows_excluded_by_class"] == {"VALUE_METHOD_NOT_MIGRATED": 15, "VALUE_NOT_COMPUTABLE": 6,
                                           "VALUE_TRADE_RULE_UNDECIDED": 1}
    assert len(r["rooms"]) == 10 and {x["room_id"] for x in r["rooms"]} == {i for x in r["rows"] for i in x["room_ids"]}


def test_required_signatures_cover_every_observation_including_reflected_instances():
    r = reg()
    assert r["source_observations_without_signature"] == []
    assert r["required_signature_count"] == len(r["required_signatures"]) == 10
    reflected = [s for s in r["required_signatures"] if "NET=NET_REFLECTED" in s["signature"]]
    assert sum(s["observations"] for s in reflected) == 7
