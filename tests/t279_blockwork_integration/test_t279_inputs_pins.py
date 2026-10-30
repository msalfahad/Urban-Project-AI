"""T-279: the V3.0.26 inputs are built only from the merged T-333 r2 fill (pinned by sha256) and reproduce its
per-line figures wall by wall; no drawing is needed (the merged CSVs are in the repository). Normal: the 21 lines,
the totals (MAS.BLOCK VERIFIED 297.847 on 18 walls, determinate 422.5314, established parts 156.5697, drop 46.8019 -
7.9131 d, 28 HELD walls), every OWNER-APPROVED wall resting on its Q-55 doors, the Checker-corrected walls at the
Checker's values. Adverse: an edited ledger stops the build; a HELD wall given a figure is refused by the engine."""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t279"))

import t279_inputs as T  # noqa: E402
from engine.source import arch_v3026 as A  # noqa: E402


@pytest.fixture(scope="module")
def doc():
    return A.load_inputs(T.build())


def _blk(doc):
    return [ln for ln in doc["lines"] if ln["item_code"] == "MAS.BLOCK"]


def test_lines_and_ids(doc):
    assert len(doc["lines"]) == 21
    assert sorted({ln["item_code"] for ln in doc["lines"]}) == ["ARCH.WALL_PANEL", "ARCH.WALL_VOLUME", "MAS.BLOCK"]
    assert all(ln["before"] == {"evidence_state": "BLOCKED_RFI", "measured_net": None} for ln in doc["lines"])
    assert sum(len(ln["walls"]) for ln in _blk(doc)) == 76


def test_mas_block_totals(doc):
    tot = {}
    for ln in _blk(doc):
        for p in A.parts_of(ln).values():
            tot[p["status"]] = tot.get(p["status"], 0.0) + p["value"]
    assert {k: round(v, 4) for k, v in tot.items()} == {"VERIFIED": 297.847, "DRAWING-CONFIRMED": 157.6488,
                                                        "ASSUMED - OWNER-APPROVED": 123.6053}
    assert round(sum(tot.values()), 4) == 579.1011           # basis B: determinate 422.5314 + parts 156.5697
    whole = sum(w["carried"] for ln in _blk(doc) for w in ln["walls"] if w["status"] in A.CLOSABLE)
    parts = sum(w["carried"] for ln in _blk(doc) for w in ln["walls"] if w["status"] == A.PART)
    assert (round(whole, 4), round(parts, 4)) == (422.5314, 156.5697)
    ver = [w for ln in _blk(doc) for w in ln["walls"] if w["status"] == "VERIFIED"]
    assert len(ver) == 18 and all(w["verified_by"].startswith("Checker 2026-10-2") for w in ver)
    drop = [w for ln in _blk(doc) for w in ln["walls"] if w["status"] == A.DROP]
    assert len(drop) == 6 and all(w["carried"] is None for w in drop)
    assert (round(sum(w["upper_at_d0"] for w in drop), 4), round(sum(w["drop_coefficient"] for w in drop), 4)) == (
        46.8019, 7.9131)
    assert sum(1 for ln in _blk(doc) for w in ln["walls"] if w["status"] == A.HELD) == 28


def test_owner_approved_rests_on_q55_doors(doc):
    oa = [w for ln in _blk(doc) for w in ln["walls"]
          if (w["part_status"] if w["status"] == A.PART else w["status"]) == A.OA]
    assert len(oa) == 10
    assert all(w["owner_source"].startswith("OWNER_QUESTIONS_ANSWERED Q-55 C") for w in oa)


def test_checker_corrected_walls(doc):
    w = {x["wall_id"]: x for ln in _blk(doc) for x in ln["walls"]}
    assert (w["1F-W20"]["carried"], w["1F-W22"]["carried"]) == (24.507, 20.401)
    assert (w["GF-W16"]["status"], w["GF-W16"]["upper_at_d0"], w["GF-W16"]["drop_coefficient"]) == (A.DROP, 15.436,
                                                                                                 2.95)
    assert w["1F-W00"]["carried"] == 12.935 and w["GF-W12"]["status"] == A.DROP


def test_edited_ledger_stops_the_build(monkeypatch):
    monkeypatch.setitem(T.PINS, T.FILL, "0" * 64)
    with pytest.raises(T.PinError):
        T.build()


def test_held_wall_with_a_figure_refused(doc):
    bad = copy.deepcopy(doc)
    ln = next(x for x in _blk(bad) if any(w["status"] == A.HELD for w in x["walls"]))
    next(w for w in ln["walls"] if w["status"] == A.HELD)["carried"] = 0.0
    with pytest.raises(A.InputsError, match="never 0"):
        A.load_inputs(bad)
