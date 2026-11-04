"""T-480: the development-villa run record (research/agents_t480/summary_t480.json, own chain T-167 -> v3053_run on the
Drive drawings: V3_0_51 c0b6d664 and V3_0_53 36863f6c reproduced -> v3054_apply V3_0_54) is internally consistent: RL-07
valued from its pieces by hand, 2 held turns + 1 unknown band blank, 14 reader lines retired, every other line
byte-identical, totals move only in FIN.RAILING (17.366 -> 33.319174 lm)."""
from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
S = json.loads((ROOT / "research/agents_t480/summary_t480.json").read_text(encoding="utf-8"))


def lines():
    return {r["element_id"]: r for r in S["railing_lines"]}


def test_chain_and_identity():
    assert S["chain"]["V3_0_51"].startswith("c0b6d664") and S["chain"]["V3_0_53"].startswith("36863f6c")
    assert S["extends"] == "ARCH_TAKEOFF_V3.0.53"
    i = S["identity"]
    assert (i["base_lines"], i["v3_0_54_lines"], i["replaced"], i["added"]) == (4936, 4939, 15, 3)
    assert i["outside_rows"] == i["outside_rows_identical_to_base"] == 4921
    assert list(S["totals_moved_by_code"]) == ["FIN.RAILING|lm"]
    t = S["totals_moved_by_code"]["FIN.RAILING|lm"]
    assert t["base"]["released"] == 17.366 and t["v3_0_54"]["released"] == 33.319174
    assert t["v3_0_54"]["blocked_lines"] == 5                  # RL-09, RL-11, T-MS1-N, T-MS2-LD, F-T476-1


def test_rl07_by_hand():
    r = lines()["RAIL:RL-07"]
    assert r["state"] == "PROVISIONAL" and r["before"]["state"] == "BLOCKED_RFI" and r["before"]["lm"] is None
    conf = [p for p in r["pieces"] if p["status"] == "DRAWING-CONFIRMED"]
    own = round(sum(math.hypot(p["plan_m"], p["rise_m"]) for p in conf), 6)
    assert own == r["lm"] == 15.953174
    ms2l = [p for p in conf if p["piece_id"] == "ST-01:MS2-L"][0]
    assert math.hypot(3.3, 1.848) == pytest.approx(ms2l["length_lm"], abs=1e-6) == pytest.approx(3.782209, abs=1e-6)
    assert {p["piece_id"] for p in r["pieces"] if p["status"] == "HELD"} == {"ST-01:T-MS1-N", "ST-01:T-MS2-LD"}


def test_held_unknown_blank_and_retired():
    L = lines()
    for e in ("RAIL:RL-07:ST-01:T-MS1-N", "RAIL:RL-07:ST-01:T-MS2-LD", "RAIL:ST-01b:GF east-lane band beyond D1",
              "RAIL:RL-09", "RAIL:RL-11"):
        assert L[e]["state"] == "BLOCKED_RFI" and L[e]["lm"] is None
    ret = [r for r in S["railing_lines"] if r["action"] == "RETIRE_READER"]
    assert len(ret) == 14 and all(r["state"] == "NOT_APPLICABLE_WITH_EVIDENCE" and r["lm"] is None for r in ret)
    assert all(r["home_lines"] for r in ret)
    for e, v in (("RAIL:RL-05", 16.324), ("RAIL:RL-08", 1.042), ("RAIL:RL-06", 2.4)):
        assert L[e]["lm"] == L[e]["before"]["lm"] == v           # confirmed by the census, unchanged
    c = S["piece_log"]["confirmed"]
    assert c["RL-05"]["difference_lm"] == 0.000287 and abs(c["RL-08"]["difference_lm"]) <= 0.0005
