"""T-419 development-villa inputs (no private data needed): research/agents_t419/t419_inputs.py builds the V3.0.46
inputs from the merged T-408 / T-407 summaries only (sha-pinned), carries their figures unchanged, and the module
accepts them. Pins: tie 5.500 m on three sheets; MAIN_S AT_LEAST 11.389 m2 net (16.270 x 0.70), gross 13.4897;
ANNEX_S no bound (D-35); E / W register items only; band partition 44.37 + 44.07 + 3.50 = 91.94 m."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT / "research" / "agents_t419"):
    sys.path.insert(0, str(p))

import t419_inputs as T  # noqa: E402
from engine.source import arch_v3046 as M  # noqa: E402

PID = "development-villa"


def test_builds_and_loads():
    d = T.build(PID)
    v = M.load_inputs(d, PID)
    assert len(v["_adds"]) == 6 and len(v["_restate"]) == 5 and len(v["_binds"]) == 7
    assert {s["task"] for s in d["sources"]} == {"T-408", "T-407"}


def test_tie_components():
    d = T.build(PID)
    tie = [x for x in d["add"] if x["piece"] == "LIFT_TIE_BEAM"]
    assert sorted(x["item_code"] for x in tie) == ["STR.CONC.LIFT", "STR.FORMWORK", "STR.FORMWORK", "STR.REBAR"]
    assert all(x["beside"]["length_m"] == 5.5 and len(x["beside"]["sheets"]) == 3 for x in tie)
    assert all(x["tied_to"] == "TIE" for x in tie if x["key"] != "TIE")
    assert all(any("D-43" in f for f in x["missing_facts"]) for x in tie)


def test_house_masonry_runs():
    d = T.build(PID)
    m = {x["key"]: x for x in d["add"] if x["piece"] == "HOUSE_BELOW_NG_MASONRY"}
    assert set(m) == {"MAIN_S", "ANNEX_S"}
    b = m["MAIN_S"]["beside"]
    assert (b["run_m"], b["height_at_least_m"], b["area_m2"], b["gross_area_m2"]) == (16.27, 0.7, 11.389, 13.4897)
    assert m["ANNEX_S"]["beside"]["kind"] == "NO_BOUND" and "D-35" in m["ANNEX_S"]["beside"]["why"]
    assert {x["key"] for x in d["register_only"]} == {"MAIN_E_SEA", "ANNEX_W_STREET"}
    p = d["partition"]
    assert (p["house_m"], p["fence_m"], p["pool_m"], p["band_m"]) == (44.37, 44.07, 3.5, 91.94)


def test_restated_lines_name_both_facts():
    d = T.build(PID)
    assert {x["line_id"] for x in d["restate"]} == {T.L_PIT_WALL, T.L_PIT_MEMB, T.L_PIT_BOARD, *T.L_PIT_FORM}
    assert all(x["facts"] == [T.PIT_DEPTH, T.BUILD_UP] for x in d["restate"])
    assert all(x["tie_to"] == T.L_PIT_WALL for x in d["restate"] if x["line_id"] in T.L_PIT_FORM)


def test_binds_carry_merged_totals():
    d = T.build(PID)
    b = {x["what"]: x for x in d["bind"]}
    assert b["12 lift ring beams GF / 1F / 2F roof"]["expect"]["total"] == 1.764
    assert len(b["12 lift ring beams GF / 1F / 2F roof"]["line_ids"]) == 12
