"""Phase 2B-0 P1, finding F-21: the V2.2 surface ledger conserves the BOQ lines - every emitted line is in exactly one
ledger record or in a documented out-of-scope category; engine limits, missing emitters and missing sources are
separate statuses; coverage is reported by trade and floor; completeness is never claimed from CONFIRMED_MISSING = 0.
The V2.1 ledger is frozen (characterization)."""

from __future__ import annotations

import os
import sys
from collections import Counter
from pathlib import Path

import pytest

pytest.importorskip("ezdxf")
sys.path.insert(0, str(Path(__file__).resolve().parent))

import p2b0_fixtures as FX                                    # noqa: E402
from tools import arch_synth as AS                            # noqa: E402
from tools import urban_boq_m9 as M9                          # noqa: E402

LR = {"A-WALL": "WALL", "A-GLAZ": "WINDOW", "A-DOOR": "DOOR", "A-THIN": "OTHER"}


def _run(path, method, facts=None, layer_roles=None):
    try:
        room, arch, _E = M9.arch_compute(str(path), method=method, facts=facts, layer_roles=layer_roles)
    except M9.CompletenessFailed as ex:
        room, arch = ex.room_boq, ex.arch
    return room, arch


def _placement(room, ledger):
    seen = Counter(i for r in ledger["records"] for i in r["line_ids"])
    ids = [ln["line_id"] for ln in room["lines"]]
    return seen, ids


@pytest.fixture(scope="module")
def villa(tmp_path_factory):
    p = tmp_path_factory.mktemp("f21") / "villa.dxf"
    AS.villa(str(p))
    return p


def test_v2_1_ledger_is_frozen_and_leaves_lines_out(villa):
    """characterization: V2.1 has no conservation (some lines are in no record) and labels engine stops NO_EMITTER."""
    room, arch = _run(villa, "ARCH_TAKEOFF_V2.1")
    seen, ids = _placement(room, arch["ledger"])
    assert "conservation" not in arch["ledger"]["summary"]
    assert any(i not in seen for i in ids)


@pytest.mark.parametrize("facts", [None, FX.HEIGHT_FACTS])
def test_v2_2_places_every_line_exactly_once(villa, facts):
    room, arch = _run(villa, "ARCH_TAKEOFF_V2.2", facts=facts)
    L = arch["ledger"]
    seen, ids = _placement(room, L)
    assert sorted(seen) == sorted(ids) and all(n == 1 for n in seen.values())
    c = L["summary"]["conservation"]
    assert c["lines"] == len(ids) and c["in_records"] == len(ids) and c["duplicates"] == [] and c["ok"]


def test_out_of_scope_lines_are_named_with_a_reason(villa):
    room, arch = _run(villa, "ARCH_TAKEOFF_V2.2")
    for r in arch["ledger"]["records"]:
        if r["status"] == "OUT_OF_LEDGER_SCOPE":
            assert r["line_ids"] and r["blocker"]


def test_engine_limits_are_not_reported_as_missing_emitters():
    from engine.source import surface_ledger as SL
    ln = {"line_id": "L1", "item_code": "ARCH.THRESHOLD", "unit": "m2", "evidence_state": "BLOCKED_RFI",
          "measured_net": None, "location": {"floor": "GF", "room_id": "GF-STRIP-X", "element_id": "GF:OP-001 strip"},
          "physical_element": "threshold strip", "rfi": {"question": "STRIP_NOT_ATTRIBUTED: a strip ..."}}
    v21 = SL._record("e", "OPENING:DOOR", "GF", ("THRESHOLD", "THRESHOLD_FINISH", ("ARCH.THRESHOLD",), None,
                                                  "OWNER_DECISION_OPEN: Q-S6-1", True), [ln])
    v22 = SL._record("e", "OPENING:DOOR", "GF", ("THRESHOLD", "THRESHOLD_FINISH", ("ARCH.THRESHOLD",), None,
                                                  "OWNER_DECISION_OPEN: Q-S6-1", True), [ln], engine_status="ENGINE_LIMIT")
    assert v21["status"] == "NO_EMITTER" and v22["status"] == "ENGINE_LIMIT"


def test_coverage_is_reported_by_trade_and_floor_and_completeness_is_never_claimed(villa):
    room, arch = _run(villa, "ARCH_TAKEOFF_V2.2")
    s = arch["ledger"]["summary"]
    assert set(s["coverage_by_floor_trade"]) == {"GF", "1F"}
    for fl, trades in s["coverage_by_floor_trade"].items():
        for trade, by in trades.items():
            assert sum(by["by_status"].values()) == by["records"]
    assert s["confirmed_missing"] == 0 and s["boq_completeness"]["state"] == "NOT_ESTABLISHED"
    assert s["boq_completeness"]["why"]


REAL = os.environ.get("URBAN_REAL_PLAN_DXF")


@pytest.mark.skipif(not (REAL and Path(REAL).exists()), reason="the reference plan is private (URBAN_REAL_PLAN_DXF)")
def test_the_reference_plan_ledger_conserves_every_line():
    """acceptance review SE-09: 102 of 427 lines were outside the V2.1 ledger."""
    room, arch = _run(REAL, "ARCH_TAKEOFF_V2.2")
    seen, ids = _placement(room, arch["ledger"])
    assert sorted(seen) == sorted(ids) and all(n == 1 for n in seen.values())
    st = arch["ledger"]["summary"]["by_status"]
    assert st.get("NO_EMITTER", 0) == 0 or all(r["conditions"] for r in arch["ledger"]["records"]
                                               if r["status"] == "NO_EMITTER")
    assert st.get("ENGINE_LIMIT", 0) >= 1
