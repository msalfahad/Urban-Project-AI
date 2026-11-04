"""T-487: the development-villa run record (research/agents_t487/summary_t487.json, own chain T-167 -> v3053_run on the
Drive drawings: V3_0_51 c0b6d664 reproduced -> V3_0_53 36863f6c) is internally consistent and agrees with the pinned inputs: 60
lintel lines added, 0 replaced, every V3.0.51 line byte-identical, REQUIRED lines recomputed by hand from the record."""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t487"))

import t487_inputs as T  # noqa: E402

S = json.loads((ROOT / "research/agents_t487/summary_t487.json").read_text(encoding="utf-8"))


def test_chain_and_identity():
    assert S["chain"]["V3_0_50"].startswith("d40c4ec5")
    assert S["chain"]["V3_0_51"].startswith("c0b6d664")                    # the candidate of record (T-483 Gate B)
    assert S["chain"]["V3_0_53"].startswith("36863f6c") and S["extends"] == "ARCH_TAKEOFF_V3.0.51"
    i = S["identity"]
    assert (i["base_lines"], i["v3_0_53_lines"], i["replaced"], i["added"]) == (4876, 4936, 0, 60)
    assert i["outside_rows"] == i["outside_rows_identical_to_base"] == 4876
    assert list(S["totals_moved_by_code"]) == ["STR.CONC.LINTEL|m3"]
    t = S["totals_moved_by_code"]["STR.CONC.LINTEL|m3"]
    assert t["base"] is None and t["v3_0_53"]["released"] == 1.016 and t["v3_0_53"]["blocked_lines"] == 44


def test_required_lines_by_hand():
    req = [r for r in S["lintels"] if r["decision"] == "REQUIRED"]
    assert len(req) == 16 and all(r["pieces"] == 1 and r["state"] == "PROVISIONAL" for r in req)
    for r in req:
        L = round(r["width_m"] + 2 * 0.40, 6)
        assert r["length_m"] == pytest.approx(L)
        assert r["m3"] == pytest.approx(r["section_m"][0] * r["section_m"][1] * L, abs=1e-9)
        assert r["formwork_m2_beside"] == pytest.approx(2 * r["section_m"][1] * L + r["wall_t_m"] * r["width_m"])
    assert round(sum(r["m3"] for r in req), 6) == 1.016
    assert round(sum(r["formwork_m2_beside"] for r in req), 6) == 14.845
    assert round(sum(r["host_face_m2"] for r in req), 6) == 6.085                  # 5.445 on lines + 0.64 held wall
    assert round(sum(r["host_face_m2"] for r in req if r["host_line"]), 6) == 5.445   # T-453 r2 named deductions


def test_held_and_flagged_blank():
    other = [r for r in S["lintels"] if r["decision"] != "REQUIRED"]
    assert Counter(r["decision"] for r in other) == {"HELD": 42, "FLAGGED": 2}
    assert all(r["m3"] is None and r["state"] == "BLOCKED_RFI" and r["why"] for r in other)


def test_same_openings_and_decisions_as_the_pinned_inputs():
    doc = T.build("p")
    a = {x["opening_id"]: x["decision"] for x in doc["lintels"]}
    b = {r["opening_id"]: r["decision"] for r in S["lintels"]}
    assert a == b
