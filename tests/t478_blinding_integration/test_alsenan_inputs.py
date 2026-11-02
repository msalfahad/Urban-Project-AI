"""T-478 development-villa pins (committed merged files only; the candidate lines are private-run outputs, their
result is pinned through research/agents_t478/summary_t478.json)."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t478"))

import t478_inputs as IN  # noqa: E402
from engine.source import arch_v3045 as M  # noqa: E402

PID = "development-villa-t131"


def test_inputs_load_and_split_re_adds():
    d = M.load_inputs(IN.build(PID), PID)
    s = d["_splits"][0]
    assert s["_v"] == 12.734438 and s["_expect"] == 15.179437
    assert abs(s["_v"] + sum(h["former"] for h in s["_held"]) - 15.179437) <= M.TOL
    r = d["_ranges"][0]
    assert (r["_lo"], r["_hi"]) == (0.435, 0.59)            # F10 alone at the plot corner, clipped .. F10 + F rows


def test_summary_pins():
    s = json.loads((ROOT / "research/agents_t478/summary_t478.json").read_text(encoding="utf-8"))
    assert s["extends"] == "ARCH_TAKEOFF_V3.0.44"              # rebased on the merged V3.0.44 (T-422)
    assert s["base_v3_0_44_lines_sha256"].startswith("8b2fe2b6")   # the candidate of record before this version
    assert s["identity"]["v3_0_45_lines"] == s["identity"]["base_lines"] + 3 == 4861
    assert s["identity"]["outside_rows_identical_to_base"] == 4855
    assert s["identity"]["skirting"]["released_lines"] == 4          # V3.0.44 skirting passes through unchanged
    t = s["totals_moved_by_code"]
    assert list(t) == ["STR.CONC.BLINDING|m3"]
    assert t["STR.CONC.BLINDING|m3"]["v3_0_45"]["released"] == 12.734438
    p = s["plate"]
    assert p["closes_low"] and p["closes_high"] and p["engine_vs_plate_m3"] == -34.320562
    assert {r["action"] for r in s["rows"]} == {"SPLIT_VALUE", "SPLIT_ADD", "RANGE_FIX", "NETTING", "ADD_HELD"}
    held = [r for r in s["rows"] if r["action"] in ("SPLIT_ADD", "ADD_HELD")]
    assert all(r["v3_0_45"]["value"] is None for r in held)          # held is never a value, never 0
