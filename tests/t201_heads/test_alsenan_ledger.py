"""T-201: the development villa's head ledger reproduces from repository files, and its invariants hold: the census r3
and the merged T-175 files are untouched, 26 / 29 windows carry a drawing-confirmed height, W02 / W11 / W12 / P-GF-01 /
P-1F-01 stay HELD (never 0), every bound opening's drawn width matches its plan width, and the like-for-like freelancer
comparison is restated with n."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t201"
sys.path.insert(0, str(HERE))

import alsenan_t201 as A                                               # noqa: E402


def _heads():
    return {r["ID"]: r for r in csv.DictReader(open(HERE / "HEADS_T201.csv", encoding="utf-8"))}


def test_committed_files_reproduce():
    assert A.main(["--check"]) == 0


def test_inputs_untouched():
    r3 = {r["ID"]: r for r in csv.DictReader(open(ROOT / "research/agents_t198/OPENINGS_T198.csv", encoding="utf-8"))}
    assert r3["W05"]["HEIGHT_M"] == "" and r3["W05"]["HEIGHT_STATUS"] == "HELD"        # r3 never edited
    t175 = {r["opening"]: r for r in csv.DictReader(open(ROOT / "research/agents_t175/T175_OPENING_CONSEQUENCES.csv",
                                                          encoding="utf-8"))}
    assert t175["W24"]["opening_status"] == "HELD"                                       # T-175 never edited


def test_counts_and_held_items():
    s = json.loads((HERE / "summary.json").read_text(encoding="utf-8"))
    assert s["windows_height_DRAWING_CONFIRMED_before"] == 8
    assert s["windows_height_DRAWING_CONFIRMED_after"] == 26
    assert s["windows_still_held"] == ["W02", "W11", "W12"]
    h = _heads()
    for oid in ("W02", "W11", "W12", "P-GF-01", "P-1F-01"):
        assert h[oid]["STATUS"] == "HELD" and h[oid]["AREA_M2"] == ""                    # held, never 0
    assert h["W02"]["HEIGHT_M"] == "2.200"                                               # read at the cut, area held
    assert s["like_for_like_after"]["n"] == 26


def test_known_values_and_redatum():
    h = _heads()
    assert (h["W24"]["SILL_ABOVE_FFL_M"], h["W24"]["HEAD_ABOVE_FFL_M"], h["W24"]["AREA_M2"]) == ("1.000", "2.500", "2.325")
    assert (h["W08"]["SILL_ABOVE_FFL_M"], h["W08"]["HEAD_ABOVE_FFL_M"]) == ("1.000", "2.500")        # annex +0.30
    assert (h["W25"]["SILL_ABOVE_FFL_M"], h["W25"]["HEIGHT_M"]) == ("0.000", "1.500")
    assert h["W16"]["AREA_M2"] == "4.805" and h["W16"]["HEIGHT_M"] == "3.100"
    assert h["W05"]["SILL_ABOVE_FFL_M"] == "" and h["W05"]["AREA_M2"] == "0.480"       # room floor held, area not
    assert h["P-GF-05"]["HEAD_ABOVE_FFL_M"] == "2.500" and h["P-GF-05"]["KIND"] == "OPENING"
    for r in h.values():
        if r["BINDING"] == "BOUND":
            assert r["STATUS"] == "DRAWING-CONFIRMED" and r["ISSUE_CHECK"].startswith("AGREES")


def test_downstream_never_turns_held_into_zero():
    rows = list(csv.DictReader(open(HERE / "DOWNSTREAM_T201.csv", encoding="utf-8")))
    for r in rows:
        if r["after_status"] == "HELD" and r["unit"] != "status":
            assert r["after"] == ""
    net = {r["row_id"]: r for r in csv.DictReader(open(HERE / "NET_BLOCK_T201.csv", encoding="utf-8"))}
    assert net["1F-W06"]["net_m2_on_t143_gross"] == "54.487" and net["1F-W06"]["s5_status"] == "DRAWING-CONFIRMED"
