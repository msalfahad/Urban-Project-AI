"""T-310 r7: the development villa's V3.0.57 inputs (built from the sha-pinned merged T-303 / T-309 / T-286 files) and the
committed run summary (research/agents_t310/summary_t310.json, from research/agents_t310/v3057_run.py on the Drive
copies; no drawing needed here). Development villa, regression only: never an accuracy claim."""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t310"))

import t310_inputs as T  # noqa: E402
from engine.source import arch_v3057 as A  # noqa: E402

S = json.loads((ROOT / "research/agents_t310/summary_t310.json").read_text(encoding="utf-8"))


def test_inputs_validate_and_count():
    d = A.load_inputs(T.build("P"), "P")
    assert Counter(e["action"] for e in d["_entries"]) == {"KEY_DOOR": 11, "NOT_APPLICABLE": 5, "ADD_HELD_DOOR": 3,
                                                          "ADD_POOL_LAYER": 2, "REVALUE_UPTURN": 1,
                                                          "REVALUE_FLOOR": 1}
    v = {e.get("line_id") or e.get("item_code") or e["door_id"]: e.get("_value") for e in d["_entries"]}
    assert v["L-60f100105399a9bdfb08"] == pytest.approx(1.58)            # (8.700 - 0.800) x 0.20
    assert v["L-f32abcdb3b4db6877c64"] == pytest.approx(13.455)          # 13.500 - 0.900 x 0.050
    assert v["WP.POOL.MEMBRANE"] == pytest.approx(29.582355)
    assert v["WP.POOL.PROTECTION_SCREED"] == pytest.approx(1.524503)


def test_run_summary_pins():
    assert S["base_candidate"] == {"file": "V3_0_56_BOQ_LINES.json", "sha256_8": "4e25c54f", "lines": 4989}  # r7: V3.0.56 of record
    assert S["new_candidate"] == {"file": "V3_0_57_BOQ_LINES.json", "sha256_8": "25a8b406", "lines": 4994}
    i = S["identity"]
    assert (i["replaced"], i["added"], i["outside_rows_identical_to_base"]) == (18, 5, 4971)
    t = S["totals_moved_by_code"]
    assert {k.split("|")[0] for k in t} <= set(A.WP_CODES)
    assert t["FIN.WP.WALL_UPTURN|m2"]["v3_0_57"]["released"] - t["FIN.WP.WALL_UPTURN|m2"]["base"]["released"] == \
        pytest.approx(0.100)
    assert t["FIN.WP.FLOOR|m2"]["v3_0_57"]["released"] - t["FIN.WP.FLOOR|m2"]["base"]["released"] == \
        pytest.approx(-0.045)
    assert t["FIN.WP.DOORWAY_TRANSITION|m2"]["v3_0_57"]["blocked_lines"] == 3
    assert len(i["wet_area_wp"]["doors"]) == 14
