"""T-443: pins of the development-villa run (research/agents_t443/summary_t443.json, from v3046_run.py on the Drive
copies): the base is the candidate of record V3.0.45, the split adds 13.550 lm in FIN.SKIRTING only, the two parents
carry no figure, and the inputs builder reproduces the hand figures of the merged T-441 tables without private data."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "research" / "agents_t443")]

from engine.source import arch_v3046 as A  # noqa: E402
import t443_inputs as I  # noqa: E402

S = json.loads((ROOT / "research/agents_t443/summary_t443.json").read_text(encoding="utf-8"))


def test_base_is_candidate_of_record_and_only_skirting_moves():
    assert S["base_sha256"].startswith("5972888b") and S["candidate_sha256"].startswith("0d44e033")
    assert (S["lines"]["added"], S["lines"]["replaced"]) == (7, 2)
    assert S["lines"]["outside_identical"] == S["lines"]["base"] - 2
    t = S["totals_moved_by_code"]
    assert list(t) == ["FIN.SKIRTING|lm"]
    assert t["FIN.SKIRTING|lm"]["v3_0_46"]["released"] - t["FIN.SKIRTING|lm"]["base"]["released"] == \
        pytest.approx(13.55, abs=1e-6)


def test_parents_and_children():
    p = S["parents"]
    assert p["L-47fa825d197d32754240"]["action"] == "PARENT_HELD" and len(p["L-47fa825d197d32754240"]["children"]) == 5
    assert p["L-b8d4a7f04277deb1b0b0"]["action"] == "PARENT_NA" and len(p["L-b8d4a7f04277deb1b0b0"]["children"]) == 2
    assert all(abs(x["residual_lm"]) < 1e-9 for x in p.values())
    vals = {r["element_id"]: r["after"].get("value") for r in S["rows"] if r["action"] == "SPLIT_PART"}
    assert vals == {"SKIRT-T443:GF-ST-HALL": 4.65, "SKIRT-T443:GF-ST-LOBBY030": 1.4, "SKIRT-T443:2F-ST-LOBBY": 3.35,
                    "SKIRT-T443:2F-ST-ARRIVAL": 4.15}


def test_inputs_reproduce_t441_hand_figures():
    d = A.load_inputs(I.build("pin"))
    nets = {p["part"]: p["_m"]["net"] for s in d["_splits"] for p in s["parts"]}
    assert nets == {"GF-ST-HALL": 4.65, "GF-ST-LOBBY030": 1.4, "2F-ST-LOBBY": 3.35, "2F-ST-ARRIVAL": 4.15}
    lift = [x for s in d["_splits"] for p in s["parts"] for x in p["_m"]["deductions"] if x["kind"] == "LIFT_OPENING"]
    assert [(x["opening_id"], x["qty"], x["jamb_skirting"]) for x in lift] == [("OP-002", 1.0, False)]
    assert [s["_closure"] - s["_run"] for s in d["_splits"]] == [pytest.approx(0.0), pytest.approx(0.0)]
