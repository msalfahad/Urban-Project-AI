"""T-307 Alsenan pins (development villa; research ledger only). Read the committed census (numbers only, built from
the private faces by `t307_alsenan.py --geometry`) and the merged T-306 / T-152 research files; no drawing is read
here, no candidate or released kg is changed."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t307"
sys.path.insert(0, str(HERE))
import t307_alsenan as A  # noqa: E402


@pytest.fixture(scope="module")
def run():
    return A.run()


def test_census_agrees_with_t152_geometry():
    cen = list(csv.DictReader(open(HERE / "BAR_END_CENSUS_T307.csv", encoding="utf-8")))
    assert len(cen) == 98 and len({r["line_id"] for r in cen}) == 98
    assert sum(int(r["t152_continuity_mismatch"]) for r in cen) == 0      # every end's continuity = T-152's
    # T-306 end census: 1,947 continuous ends at count A, 2,060 at count B (T-152 probe)
    assert sum(int(r["probe_cont_A"]) for r in cen) == 1947 and sum(int(r["probe_cont_B"]) for r in cen) == 2060
    det = list(csv.DictReader(open(HERE / "BAR_END_DETAIL_T307.csv", encoding="utf-8")))
    assert len(det) == sum(sum(int(r[f"n{t}_{k}"]) for k in A.CLASSES) for r in cen for t in "AB")
    assert all(d["support"] in A.CLASSES for d in det)                     # no end without a class


def test_every_kg_of_the_development_line_reclassified(run):
    _c, s = run
    assert s["dev_lines"] == 98
    assert s["candidate_dev_kg"] == {"low": 939.794, "high": 1741.976}
    by = s["candidate_dev_by_class_kg"]
    lo = sum(v[0] for v in by.values()) - s["candidate_unbooked_kg"][0]
    hi = sum(v[1] for v in by.values()) - s["candidate_unbooked_kg"][1]
    assert lo == pytest.approx(939.794, abs=0.01) and hi == pytest.approx(1741.976, abs=0.01)
    assert abs(s["closure_rounding_kg"][0]) < 98 * 0.0015 and abs(s["closure_rounding_kg"][1]) < 98 * 0.0015
    assert by["CONTINUOUS"] == [468.304, 864.408]
    assert by["EDGE_BEAM"] == [298.75, 541.472]
    assert by["STEP_EDGE"] == [102.222, 188.827]
    assert by["IRREGULAR_SUPPORT"] == [70.031, 145.538]
    assert by["CONTINUOUS_WIDE_BEAM"] == [0.0, 0.0]          # no single square band wider than 0.80 m on this villa
    # T-306: 471.105 kg of the development spread lies on T-152-continuous ends (CONTINUOUS + probe STEP_EDGE)
    assert s["dev_spread_on_t152_continuous_ends_kg"] == pytest.approx(471.105, abs=0.002)


def test_end_classes_pinned(run):
    e = run[1]["ends_by_class_A_B"]
    assert e == {"CONTINUOUS": [1591, 1683], "CONTINUOUS_WIDE_BEAM": [0, 0], "EDGE_BEAM": [1004, 1044],
                 "STEP_EDGE": [414, 437], "OPENING_EDGE": [4, 12], "IRREGULAR_SUPPORT": [259, 298]}
    s = run[1]
    assert s["slab_beyond_wide_support_ends"] == {"bottom": [84, 93], "top": [79, 87]}


def test_rebased_development_and_findings(run):
    consumer, s = run
    assert s["new_dev_straight_kg"] == {"low": 136.573, "high": 150.696}
    assert [x["low"] for x in s["f02_tank_top_lines"]] == [0.0] * 4                  # F-02: low 0 on 4 T&B lines
    assert s["f03_skew_top_line"] == [{"line": "L-b10f318a155d5ee1b289", "low": 16.223, "high": 34.821}]
    f04 = {x["element"] + " " + x["direction"]: x for x in s["f04_label_lines"]}
    assert set(f04) == {"SLAB:GF-020 y", "SLAB:1F-041 y", "SLAB:GF-076 x"}
    assert all(x["old_basis_low_corrected"] == 2.469 for x in f04.values())
    sb = s["slab_bound_restated_kg"]
    assert (sb["low"], sb["high"]) == (3811.621, 5241.324)
    assert sb["spread_change_vs_t306"] == -758.857


def test_consumer_shape_every_line_once_nothing_zeroed(run):
    consumer, s = run
    assert len(consumer) == 294 and len({c["line_id"] for c in consumer}) == 294
    for c in consumer:
        if c["proposed_status"] in ("HELD", "BOUND_PART_WITH_HELD"):
            assert c["held_items"]                                    # every held part named
        if c["proposed_status"] == "HELD":
            assert c["valued_low_kg"] == "" and c["valued_high_kg"] == "" and "ends" in c["held_items"]
    dev = [c for c in consumer if c["population"] == A.DEV]
    assert {c["proposed_status"] for c in dev} == {"HELD", "BOUND_PART_WITH_HELD", "NOT_APPLICABLE_WITH_EVIDENCE"}


def test_committed_summary_reproduces(run):
    assert json.load(open(HERE / "BAR_END_SUMMARY_T307.json", encoding="utf-8")) == json.loads(json.dumps(run[1]))
