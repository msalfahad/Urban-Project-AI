"""T-208: the development villa's floor-area ledger reproduces from committed files; the three wet / dry review sets
of the released run are the basin-only hand-wash spaces and bind WET by Q-06 A; the hand-wash lobby cut by a drawn
line stays HELD without its boundary confirmation; the floor key is scored like for like."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t208"
sys.path.insert(0, str(HERE))

import alsenan_t208 as A                                               # noqa: E402


def test_committed_files_reproduce():
    assert A.main(["--check"]) == 0


def test_summary_figures():
    s = json.loads((HERE / "summary.json").read_text(encoding="utf-8"))
    assert s["review_sets"]["count"] == 3 and s["review_sets"]["bound"] == 3 and s["review_sets"]["held"] == []
    assert s["engine_released_m2"] == 376.2857 and s["engine_assumed_owner_approved_m2"] == 9.6782
    assert s["engine_total_m2"] == 385.9639 and s["reference_m2"] == 409.58
    assert s["raw"]["diff_m2"] == -23.6161 and s["scope_items_m2"]["net"] == -23.9904
    assert s["like_for_like"]["diff_m2"] == 0.3743
    assert s["without_boundary_confirmation_total_m2"] is None          # held, never a partial sum
    assert s["wet"]["diff_after_kitchen_class_m2"] == 0.1107


def test_every_engine_floor_line_is_paired_once():
    sets, rows, summary = A.build()
    ids = [i for r in rows for i in r["engine_ids"].split()]
    assert len(ids) == len(set(ids))
    assert abs(summary["engine_rows_sum_check_m2"]) < 0.001
