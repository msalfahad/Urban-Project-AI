"""T-207: the development villa's closure ledger reproduces from repository files; W11 / W12 established, W02 HELD on
the render (drawn count 1), the leafless heads stay HELD (never 0), head soffits are reveal head terms, and the
re-run of the merged T-175 builder changes no other opening."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t207"
sys.path.insert(0, str(HERE))

import alsenan_t207 as A                                               # noqa: E402


def _rows(name):
    return list(csv.DictReader(open(HERE / name, encoding="utf-8")))


def test_committed_files_reproduce():
    assert A.main(["--check"]) == 0


def test_summary():
    s = json.loads((HERE / "summary.json").read_text(encoding="utf-8"))
    assert s["windows_height_DRAWING_CONFIRMED_after"] == 28 and s["windows_still_held"] == ["W02"]
    assert s["like_for_like_W11_W12"] == {"n": 2, "engine_m2": 8.58, "freelancer_m2": 7.8, "diff_m2": 0.78,
                                          "diff_pct_of_freelancer": 10.0}
    assert s["like_for_like_after"]["n"] == 28 and s["like_for_like_after"]["diff_m2"] == -1.6
    assert s["W02"]["drawn_count"] == 1 and s["W02"]["status"] == "HELD"
    assert s["other_T175_openings_changed_by_this_rerun"] == []
    assert s["W11_W12_current_issue"].startswith("AGREES")


def test_held_items_have_no_value():
    for r in _rows("CLOSURE_T207.csv"):
        if r["AFTER_STATUS"] == "HELD" and r["ID"] in ("P-GF-01", "P-1F-01"):
            assert r["AFTER_VALUE"] == ""                                     # held, never 0


def test_downstream():
    d = {(r["opening"], r["line"][:12]): r for r in _rows("DOWNSTREAM_T207.csv")}
    assert d[("W11", "opening m2 (")]["after"] == "4.290"
    assert d[("W12", "reveal (2 ja")]["after"] == "8.300"
    assert d[("W11", "lintel need")]["after_status"] == "HELD"
    g = d[("GF-W18", "net block m2")]
    assert g["after"] == "11.245" and g["after_status"] == "HELD"            # gross PROVISIONAL (Q-54 B)


def test_inputs_untouched():
    h = {r["ID"]: r for r in csv.DictReader(open(ROOT / "research/agents_t201/HEADS_T201.csv", encoding="utf-8"))}
    assert h["W11"]["STATUS"] == "HELD" and h["W11"]["AREA_M2"] == ""          # T-201 never edited
