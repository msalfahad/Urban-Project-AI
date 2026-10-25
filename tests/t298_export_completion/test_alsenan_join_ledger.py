"""T-298 part (2) on the development villa (committed ledger, no private input): the slab panel join of the candidate
ARCH_TAKEOFF_V3.0.16 (canonical lines 3181cf12, own run on the Drive copies) closes every T-234 panel once."""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
JOIN = ROOT / "research/agents_t298/SLAB_PANEL_JOIN_V3016.csv"
T234 = ROOT / "research/agents_t234/LEDGER_T234.csv"


def rows(p):
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_every_panel_once_every_line_once():
    j, led = rows(JOIN), rows(T234)
    assert sorted((r["floor"], r["panel"]) for r in j) == sorted((r["storey"], r["panel"]) for r in led)
    assert len({r["line_id"] for r in j}) == len(j) == 62
    assert Counter(r["join"] for r in j) == {"EXACT": 52, "INTERCHANGEABLE": 10}


def test_volumes_close_per_storey_to_the_ledger():
    j = rows(JOIN)
    assert max(abs(float(r["diff_m3"])) for r in j) <= 0.0002
    res = {fl: round(sum(float(r["line_m3"]) - float(r["panel_m3"]) for r in j if r["floor"] == fl), 6)
           for fl in ("GF", "1F", "2F")}
    assert abs(res["GF"]) <= 0.00001 and abs(res["2F"]) <= 0.00001
    assert abs(res["1F"] - -0.000242) <= 0.000002        # T-234's own residual (panel areas rounded to 4 dp)


def test_interchangeable_pairs_carry_equal_line_volumes():
    by = {}
    for r in rows(JOIN):
        if r["join"] == "INTERCHANGEABLE":
            by.setdefault(r["group"], set()).add(r["line_m3"])
    assert len(by) == 5 and all(len(v) == 1 for v in by.values())
