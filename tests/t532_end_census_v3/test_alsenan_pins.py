"""T-532 pins on the development villa (committed numbers and ids only; no drawing read): V3 on the merged T-274 kinds."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t532"))
import t532_alsenan as B  # noqa: E402

S = json.loads((B.OUT / "SUMMARY_T532.json").read_text(encoding="utf-8"))


def test_builder_reproduces_committed_outputs():
    T = B.texts()
    for k, v in T.items():
        assert (B.OUT / k).read_text(encoding="utf-8") == v, k


def test_v2_raises_on_raw_kinds_v3_does_not():
    assert S["runs"] == 70 and S["piece_kinds_on_census_runs"] == {"BEAM": 212, "COLUMN": 86, "FACE": 50, "NONE": 1}
    assert S["v2_on_raw_kinds"]["RAISES"] == 11 and S["v2_on_raw_kinds"]["RUNS"] == 59


def test_the_12_t526_ends_reproduced_exactly():
    r = S["reconcile_t526"]
    assert r["listed_equal"] and r["held_equal"] and (r["listed_n"], r["held_n"]) == (12, 1)
    assert S["end_junctions_by_class"] == {"BEAM-END_COLUMN": 11, "BEAM-PARTIAL_COLUMN": 1, "FACE-END_COLUMN": 1}
    d = r["carried_deltas"]
    assert (d["d_length_m"], d["d_blockwork_m2"], d["d_blocks_nr"]) == (0.0, 0.0, 0.0)
    assert d["d_perimeter_m3_1F-W09"] == 0.007021
    assert (d["d_mesh_owner_ml"], d["d_mesh_drawing_ml"], d["d_ties_nr"]) == (40.9, 44.1, 30.0)


def test_interior_junctions_match_the_merged_ledgers_one_to_one():
    assert S["interior_listed_by_class"] == {"BEAM-COLUMN": 57, "COLUMN-BEAM": 52, "COLUMN-FACE": 5,
                                             "COLUMN-NONE": 1, "FACE-COLUMN": 3}
    assert S["interior_held"] == [] and S["interior_not_in_ledger_named"] == []
    assert S["interior_vs_t355"] == {"RUN NOT IN LEDGER": 1, "YES": 117}
    assert S["interior_vs_t317_v"] == {"RUN NOT IN LEDGER": 1, "YES": 117}
    assert S["v2_on_raw_kinds"]["t355_rows_not_in_v3"] == 0 and S["v2_on_raw_kinds"]["t317_v_columns_not_in_v3"] == 0
