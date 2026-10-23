"""T-198: the development villa's committed census r3 and downstream ledger reproduce from repository files, the merged
census r2 stays untouched, and the invariants of the revision hold (three additions, two re-datums, windows pcs HELD,
no released quantity moves, held never 0)."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t198"))

import alsenan_t198 as A                                        # noqa: E402

HERE = ROOT / "research" / "agents_t198"


def _r3():
    return {r["ID"]: r for r in csv.DictReader(open(HERE / "OPENINGS_T198.csv", encoding="utf-8"))}


def _d():
    return list(csv.DictReader(open(HERE / "DOWNSTREAM_T198.csv", encoding="utf-8")))


def test_committed_files_reproduce():
    assert A.main(["--check"]) == 0


def test_r2_untouched_and_r3_complete():
    r2 = list(csv.DictReader(open(ROOT / "research/agents_t150/OPENINGS_T150.csv", encoding="utf-8")))
    r3 = _r3()
    assert len(r2) == 65 and len(r3) == 68
    assert {"P-GF-01", "P-1F-01", "P-GF-05"} <= set(r3) and not {"P-GF-01", "P-1F-01", "P-GF-05"} & {r["ID"] for r in r2}
    w01 = next(r for r in r2 if r["ID"] == "W01")
    assert w01["SILL_M"] == "1.85"                              # the merged file is never edited
    for oid in ("P-GF-01", "P-1F-01", "P-GF-05"):
        assert r3[oid]["HEIGHT_M"] == "" and r3[oid]["HEIGHT_STATUS"] == "HELD"
        assert r3[oid]["BOQ_LINE"] == "OPENING.PASSAGE_NO_LEAF" and r3[oid]["PCS_STATUS"] == "NOT_A_SUPPLY_ITEM"
    # open sides stay out of the census (T-175 / T-194: not building openings)
    assert not {"P-GF-02", "P-GF-03", "P-GF-04"} & set(r3)


def test_redatum_w01_w03():
    r3 = _r3()
    assert (r3["W01"]["SILL_M"], r3["W01"]["HEAD_ABOVE_FFL_M"]) == ("1.00", "3.00")
    assert (r3["W01"]["SILL_LEVEL_M"], r3["W01"]["HEAD_LEVEL_M"], r3["W01"]["FFL_M"]) == ("+2.00", "+4.00", "+1.00")
    assert r3["W01"]["LEVEL_BASIS"] == "LEVEL+CHAIN"
    assert (r3["W03"]["SILL_M"], r3["W03"]["HEAD_ABOVE_FFL_M"]) == ("0.00", "4.30")
    assert r3["W01"]["HEIGHT_M"] == "2.00" and r3["W03"]["HEIGHT_M"] == "4.30"


def test_windows_pcs_held():
    s = json.loads((HERE / "summary.json").read_text(encoding="utf-8"))
    assert s["windows_pcs"] == {"settled": 28, "held": ["W02"], "range": [29, 30], "freelancer": 29, "status": "HELD"}
    assert _r3()["W02"]["PCS_STATUS"] == "HELD"


def test_no_released_quantity_moves_and_held_never_zero():
    s = json.loads((HERE / "summary.json").read_text(encoding="utf-8"))
    assert s["released_quantity_moved"] is False and s["block_m2_established_delta"] == 0.0
    for r in _d():
        if r["AFTER_STATUS"] in ("HELD", "UNKNOWN"):
            assert r["AFTER"] in ("",) or r["UNIT"] == "pcs", r
        if r["BOQ_LINE"].startswith(("block deduction", "opening m2")) and r["CHANGE"].startswith("C4"):
            assert r["DELTA"] == "+0.000"
    lintel = [r for r in _d() if r["OPENING"] == "P-1F-01" and r["BOQ_LINE"].startswith("lintel")][0]
    assert (lintel["BEFORE"], lintel["AFTER"]) == ("2.100", "2.100")      # reproduces S8.6's released length


def test_scope_gaps_and_threshold():
    s = json.loads((HERE / "summary.json").read_text(encoding="utf-8"))
    assert s["new_scope_gaps"]["P-1F-01 masonry above lintel m2 bounds"] == [0.0, 4.992]
    assert s["thresholds_m_l"]["t175_established"] == 42.22 and s["thresholds_m_l"]["after"] == 41.02
    assert s["head_soffits_m2_drawing_confirmed"] == {"P-GF-01": 0.18, "P-1F-01": 0.195, "P-GF-05": 0.24}
