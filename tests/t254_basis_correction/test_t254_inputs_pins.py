"""T-254: the development villa's V3.0.17 inputs, built only from merged files (T-289 ledger, T-287, T-253, T-256 /
T-248), pinned. No private drawing is read: these are values-only research files already on the head.

Pins (by hand from the merged ledgers):
  main-house exterior, 13 + 3 lines: 12.4296 - 0.002470 (stub inside neck 17BD) + 3.5304 = 15.957512 m3 released
  (DRAWING-CONFIRMED), before 8.164161 m3 at the interior depths (13 lines 6.333538 + 3 lines 1.830623);
  annex 8 CONFLICT + court 3 HELD blank; 2F columns 8 HELD blank (3.528 before); annex columns 5 HELD blank + CB5
  C3 0.650 + C5 0.780 = 1.430 rebased (T-287); 5 NOT_PRESENT upper columns (T-256, 2.268 m3 on route G, blocked in the
  candidate); the boundary ground beam added HELD (band 3.5256 m3 only in the scenario); ST-03 left to T-266.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t254"))

from engine.source import arch_v3017 as A  # noqa: E402

import t254_inputs as L  # noqa: E402


@pytest.fixture(scope="module")
def doc():
    return A.load_inputs(L.build())


def test_inputs_load_and_groups(doc):
    g = doc["groups"]
    assert g["GB_EXTERIOR_24"] == {"lines": 24, "before": 11.934579, "released_after": 12.427112, "held_lines": 11}
    assert g["GB_MAIN_EXTERIOR_IN_INTERIOR_LINES"] == {"lines": 3, "before": 1.830623, "released_after": 3.5304,
                                                       "held_lines": 0}
    assert g["COL_2F"] == {"lines": 8, "before": 3.528, "released_after": 0.0, "held_lines": 8}
    assert g["COL_ANNEX_7"] == {"lines": 7, "before": 3.7125, "released_after": 1.43, "held_lines": 5}
    assert g["COL_NOT_PRESENT"] == {"lines": 5, "before": 0.0, "released_after": 0.0, "held_lines": 0}


def test_main_house_exterior_total(doc):
    main = [r for r in doc["records"] if r["action"] == "REBASE" and r["item_code"] == L.GB]
    assert len(main) == 16
    assert sum(r["value"] for r in main) == pytest.approx(15.957512, abs=1e-6)
    assert all(r["support"]["kind"] == "TWO_PRINTED_LEVELS" and r["status"] == "DRAWING-CONFIRMED" for r in main)


def test_stub_dropped_by_handle(doc):
    r = [x for x in doc["records"] if x["line_id"] == "L-ff727b2a52e39509a659"][0]
    assert r["value"] == pytest.approx(0.3639 * 0.30 * 0.95, abs=1e-6)


def test_cb5_from_t287_and_holds_blank(doc):
    cb5 = {r["line_id"]: r for r in doc["records"] if r["task"] == "T-287"}
    assert {k: v["value"] for k, v in cb5.items()} == {"L-7d70692d03102a2dc306": 0.65, "L-84bf7fb482a98fdbe482": 0.78}
    for r in doc["records"]:
        if r["action"] in ("HOLD", "CONFLICT", "NOT_PRESENT"):
            assert r.get("value") is None
        if r["action"] == "CONFLICT":
            assert len(r["readings_named"]) == 2


def test_not_present_binding_is_unique():
    got = {r["line_id"]: r["element_id"] for r in L.not_present(L.NOT_DRAWN_IDS)}
    assert got == L.NOT_DRAWN_IDS


def test_adverse_binding_outside_tolerance_stops():
    moved = {k: v.replace("243102,55481", "243105,55481") for k, v in L.NOT_DRAWN_IDS.items()}
    with pytest.raises(SystemExit, match="NOT_DRAWN:10BD:2F"):
        L.not_present(moved)


def test_st03_left_and_boundary_added_held(doc):
    assert [x["line_id"] for x in doc["not_in_this_package"]] == ["L-061e18cf35a4b6b33d68"]
    a = doc["adds"][0]
    assert a["state"] == "HELD" and a.get("value") is None
    assert a["scenario"]["readings"] == {"band_upper_bound": pytest.approx(3.5256, abs=1e-9)}


def test_every_source_is_merged(doc):
    assert {s["task"] for s in doc["sources"]} == {"T-289", "T-287", "T-256", "T-253"}
    assert all(len(s["merge_commit"]) == 40 for s in doc["sources"])
