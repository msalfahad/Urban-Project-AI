"""T-289 Alsenan basis ledger from committed inputs only (own ARCH_TAKEOFF_V3.0.15 run on the Drive copies, extracted
by research/agents_t289/t289_extract.py; merged ledgers T-242 / T-253 / T-248 / T-258). Re-builds without writing and
pins the engineering results (development villa; not an accuracy claim)."""
from __future__ import annotations

import csv
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t289"
sys.path.insert(0, str(HERE))
import basis_ledger as B  # noqa: E402
import t289_alsenan as A  # noqa: E402

CAND, ROWS, DETAIL = A.build()


def _g(name):
    return [r for r in ROWS if r["group"] == name]


def test_every_named_total_is_its_line_ids_to_0_000_m3():
    assert {g: len(_g(g)) for g in A.NAMED} == {"GB_EXTERIOR_24": 24, "COL_2F": 8, "COL_ANNEX_7": 7, "ST03": 1,
                                                "GB_MAIN_EXTERIOR_IN_INTERIOR_LINES": 3}
    assert all(abs(v) < 5e-4 for v in B.residuals(A.NAMED, ROWS).values())
    assert len({r["line_id"] for r in ROWS}) == len(ROWS) == 43
    assert {r["project_id"] for r in ROWS} == {CAND["project"]["project_id"]}
    assert {r["revision_set_sha256"] for r in ROWS} == {CAND["project"]["revision_set_sha256"]}


def test_exterior_beams_split_by_the_printed_class_of_each_run():
    gb = _g("GB_EXTERIOR_24")
    assert CAND["candidate_lines_csv_sha256"].startswith("a4dc01dd")      # = the T-270 r2 V3.0.15 csv
    by = {}
    for r in gb:
        by.setdefault(r["status"], []).append(r)
    assert sorted((k, len(v)) for k, v in by.items()) == [("CONFLICT", 8), ("DRAWING-CONFIRMED", 13), ("HELD", 3)]
    dc = by["DRAWING-CONFIRMED"]
    assert math.fsum(r["drawing_qty_m3"] for r in dc) == pytest.approx(12.4296, abs=1e-4)
    # the 13 main-house lines cover 14 of the 16 T-253 straight runs; the other 2 runs + the ring sit in no line of
    # the 24 (the engine saw no outside side): 12.4296 + 1.2540 + 0.5415 + 1.7349 = 15.9600 (T-253 s.2)
    runs = sorted(x for d in DETAIL if "EXTERIOR_MAIN" in d["classes"] and d.get("group") is None for x in d["runs"])
    assert len(runs) == 14 and "109+7CB#2" not in runs and "145+7CA#1" not in runs
    other = _g("GB_MAIN_EXTERIOR_IN_INTERIOR_LINES")
    assert sorted(x for d in DETAIL if d.get("group") for x in d["runs"]) == ["109+7CB#2", "145+7CA#1", "ARC:157+158"]
    assert [r["status"] for r in other] == ["DRAWING-CONFIRMED"] * 3
    assert math.fsum(r["drawing_qty_m3"] for r in other) == pytest.approx(1.2540 + 0.5415 + 1.7349, abs=1e-4)
    assert math.fsum(r["drawing_qty_m3"] for r in dc + other) == pytest.approx(15.9600, abs=1e-4)   # T-253 s.2
    assert math.fsum(r["engine_qty_m3"] for r in dc + other) == pytest.approx(6.333602 + 1.830623, abs=1e-6)
    for r in by["CONFLICT"] + by["HELD"]:
        assert r["drawing_qty_m3"] is None and r["held_item"]          # blank, named, never 0
    annex = sorted(x for d in DETAIL if "EXTERIOR_ANNEX" in d["classes"] for x in d["runs"])
    assert len(annex) == 9 and "ARC:139+13A" in annex
    court = sorted(x for d in DETAIL if "COURT" in d["classes"] for x in d["runs"])
    assert court == sorted(["1811+1812#1", "178+7DB#1", "185+7C7#1"])


def test_no_exterior_line_keeps_the_interior_class_depth():
    for r in _g("GB_EXTERIOR_24"):
        assert "interior class depth" in r["engine_basis"]
        assert r["status"] != B.DRAWING_DERIVED or r["drawing_qty_m3"] != pytest.approx(r["engine_qty_m3"])


def test_columns_never_topped_at_a_finished_level_and_cb5_not_carried_before_its_verdict():
    for r in _g("COL_2F") + _g("COL_ANNEX_7"):
        assert r["drawing_qty_m3"] is None and r["status"] in (B.HELD, B.PENDING)
    pend = [r for r in _g("COL_ANNEX_7") if r["status"] == B.PENDING]
    assert len(pend) == 2 and all("T-287" in r["held_item"] for r in pend)
    assert all("D-39" in r["held_item"] for r in _g("COL_2F"))
    assert all("Q-54B" in r["held_item"] for r in _g("COL_ANNEX_7") if r["status"] == B.HELD)


def test_st03_held_on_s9_with_its_drawn_steps_component():
    (r,) = _g("ST03")
    assert r["status"] == B.HELD and r["drawing_qty_m3"] is None and r["drawing_low_m3"] == pytest.approx(0.355017)
    assert "S-9" in r["held_item"]


def test_committed_ledger_csv_equals_a_rebuild(tmp_path):
    p = tmp_path / "L.csv"
    B.write_csv(p, ROWS)
    assert p.read_bytes() == (HERE / "BASIS_LEDGER_T289.csv").read_bytes()
    got = list(csv.DictReader((HERE / "BASIS_LEDGER_T289.csv").open(encoding="utf-8")))
    assert all(g["drawing_qty_m3"] == "" for g in got if g["status"] in ("HELD", "CONFLICT", "PENDING-VERIFICATION"))
