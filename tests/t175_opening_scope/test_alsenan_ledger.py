"""T-175: the development villa's committed opening ledger reproduces from repository files, and its invariants hold
(one host per opening, HELD never 0, no provisional gross shown as drawing-confirmed, glazed lines never deducted)."""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t175"))
sys.path.insert(0, str(ROOT))

import alsenan_t175 as A                                        # noqa: E402

HERE = ROOT / "research" / "agents_t175"


def _rows(name):
    return list(csv.DictReader(open(HERE / name, encoding="utf-8")))


def test_committed_files_reproduce():
    assert A.main(["--check"]) == 0


def test_one_host_per_opening_and_census_complete():
    ops = _rows("T175_OPENING_CONSEQUENCES.csv")
    ids = [r["opening"] for r in ops]
    assert len(ids) == len(set(ids))
    deducted = [r for r in ops if r["block_status"] not in ("NOT_APPLICABLE",)]
    assert all(r["host_row"] for r in deducted)


def test_held_never_zero_and_statuses():
    for r in _rows("T175_OPENING_CONSEQUENCES.csv"):
        if r["block_status"] == "HELD":
            assert r["block_deduction_m2"] == ""
        assert r["block_status"] in ("DRAWING-CONFIRMED", "ASSUMED — OWNER-APPROVED", "HELD", "NOT_APPLICABLE")
    for r in _rows("T175_NET_BLOCK_BY_WALL.csv"):
        if r["t143_status"] in ("PROVISIONAL", "PARTLY HELD", "HELD"):
            assert r["s5_status"] == "HELD"
        if r["held_openings"]:
            assert r["net_m2_on_t143_gross"] == ""


def test_glazed_lines_not_deducted_again():
    ops = {r["opening"]: r for r in _rows("T175_OPENING_CONSEQUENCES.csv")}
    for i in ("W02", "W03", "W17"):
        assert ops[i]["construction"] == "GLAZED" and ops[i]["block_status"] == "NOT_APPLICABLE"
