"""T-296 development-villa pin: the committed ledger rebuilds byte for byte from committed inputs, every candidate
skirting line and every room appears once, the 13.569 lm closes per line to named window ids, and no HELD / NOT_APPLICABLE
quantity is written as 0."""
from __future__ import annotations

import csv
import io
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t296"
sys.path.insert(0, str(HERE))

import t296_alsenan as A  # noqa: E402


@pytest.fixture(scope="module")
def outs():
    return A.outputs()


def rows(outs, name):
    return list(csv.DictReader(io.StringIO(outs[name])))


def test_committed_files_rebuild_byte_for_byte(outs):
    for k, v in outs.items():
        assert (HERE / k).read_text(encoding="utf-8") == v, k


def test_every_candidate_skirting_line_once(outs):
    C = A.candidate()
    ids = [l["line_id"] for l in C["skirting_lines"]]
    assert len(ids) == len(set(ids)) == 39
    trail = {r["line_id"] for r in rows(outs, "LINE_TRAIL_T296.csv")}
    ranges = {l["line_id"] for l in C["skirting_lines"] if l["evidence_state"] == "BOUNDED_EXPOSURE"}
    others = {l["line_id"] for l in C["skirting_lines"] if l["net"] is None and l["evidence_state"] != "BOUNDED_EXPOSURE"}
    # every quantity line has a trail; every range line is named by the trail of its room; the rest carry no figure
    assert trail | ranges | others == set(ids)
    assert not (trail & ranges) and not (trail & others) and not (ranges & others)
    named_ranges = {r["range_line"] for r in rows(outs, "LINE_TRAIL_T296.csv") if r["range_line"]}
    assert named_ranges == ranges


def test_unlisted_13569_closes_to_window_ids(outs):
    s = json.loads(outs["summary.json"])
    assert s["trail"]["lines_with_unlisted"] == 9
    assert s["trail"]["unlisted_lm"] == pytest.approx(13.568825, abs=2e-6)
    assert s["trail"]["readds_with_named"] == s["trail"]["quantity_lines"] == 11
    assert s["trail"]["max_abs_residual_lm"] <= 2e-6
    halves = [r for r in rows(outs, "DEDUCTIONS_BY_OPENING_T296.csv")
              if r["kind"] == "WINDOW_EDGE_HALF" and r["listed"] == "False"]
    assert sum(float(r["length_m"]) for r in halves) == pytest.approx(13.568825, abs=2e-6)
    assert all(r["census_id"] for r in halves)                       # every credit names its census window


def test_each_room_once_and_reasons(outs):
    R = rows(outs, "ROOMS_T296.csv")
    names = [r["room"] for r in R]
    assert len(names) == len(set(names))
    assert sum(1 for n in names if not n.startswith("(")) == 32
    assert all(r["reason"] for r in R)


def test_no_held_or_not_applicable_as_zero(outs):
    for r in rows(outs, "LINE_LEDGER_T296.csv"):
        if r["ledger_status"] == "NOT_APPLICABLE":
            assert r["ledger_lo"] == "" and r["ledger_hi"] == ""
        else:
            assert float(r["ledger_lo"]) > 0
    for r in rows(outs, "ROOMS_T296.csv"):
        if r["status"] in ("HELD", "NOT_APPLICABLE") and r["certain_lm"] != "":
            assert float(r["certain_lm"]) > 0


def test_independent_walk_joins_within_named_causes(outs):
    J = [r for r in rows(outs, "LINE_ROOM_JOIN_T296.csv") if r["comparable"] == "YES"]
    assert len(J) == 9
    for r in J:
        assert abs(float(r["residual_lm"])) <= 0.003, r["line_id"]   # 3-decimal rounding of the walk columns
        assert abs(float(r["diff_lm"])) <= 0.035, r["line_id"]


def test_window_readings_follow_the_merged_sills(outs):
    W = {r["census_id"]: r for r in rows(outs, "WINDOW_CAUSES_T296.csv")}
    assert W["W04"]["reading"] == W["W14"]["reading"] == W["W24"]["reading"] == W["W29"]["reading"] == "SKIRTED"
    assert W["W15"]["reading"] == W["W16"]["reading"] == "NOT_SKIRTED"            # floor glazing (T-238)
    assert W["W02"]["reading"] == W["W11"]["reading"] == W["W17"]["reading"] == "HELD"
    assert W["W09"]["reading"] == W["W10"]["reading"] == "NOT_SKIRTED"            # wet pantry base
    assert W["W13"]["reading"] == W["W25"]["reading"] == "HELD"                   # stair shaft
