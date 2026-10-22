"""T-194: the development villa's committed opening-consistency ledger reproduces from repository files, and the four
known cases are found by the check itself (not typed into the ledger): the two openings missing from the T-150 census
(P-GF-01, P-1F-01; T-175), the mixed sill basis at W01 (T-175), the windows that print no head (T-144: 21 incl. W16),
W16 width only (D-45). Every elevation feature binds, unmirrored, to the plan opening the earlier ledgers name."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t194"))
sys.path.insert(0, str(ROOT))

import alsenan_t194 as A                                        # noqa: E402

HERE = ROOT / "research" / "agents_t194"


def _issues():
    return list(csv.DictReader(open(HERE / "ISSUES_T194.csv", encoding="utf-8")))


def _rows():
    return {r["opening_id"]: r for r in csv.DictReader(open(HERE / "CONSISTENCY_T194.csv", encoding="utf-8"))}


def test_committed_files_reproduce():
    assert A.main(["--check"]) == 0


def test_two_census_omissions_found():
    missing = sorted(r["opening_id"] for r in _issues() if r["code"] == "MISSING_FROM_LIST")
    assert {"P-GF-01", "P-1F-01"} <= set(missing)
    # the open sides T-175 classed as not building openings are not reported
    assert not {"P-GF-02", "P-GF-03", "P-GF-04"} & set(missing)


def test_w01_mixed_sill_basis_found():
    codes = {(r["opening_id"], r["code"]) for r in _issues()}
    assert ("W01", "SILL_LIST_DIFFERS") in codes and ("W01", "HEAD_LIST_DIFFERS") in codes
    w01 = _rows()["W01"]
    assert "1.850" in w01["SILL_VALUES"] and "1.000" in w01["SILL_VALUES"]


def test_windows_without_head_and_w16_width_only():
    rows = _rows()
    no_head = sorted(r["opening_id"] for r in _issues() if r["code"] == "HEAD_NOT_PRINTED"
                     and r["opening_id"].startswith("W"))
    assert len(no_head) == 21 and "W16" in no_head
    w16 = rows["W16"]
    assert w16["WIDTH_VERDICT"] == "AGREES" and w16["HEAD_VERDICT"] == "NOT_SHOWN"
    assert "OPENING_M2" in w16["HELD_LINES"]
    # the eight windows that print a head (T-150 measured set) are not reported as headless
    for w in ("W01", "W03", "W13", "W14", "W15", "W17", "W18", "W26"):
        assert w not in no_head


def test_binding_unmirrored_and_complete():
    s = json.loads((HERE / "summary.json").read_text(encoding="utf-8"))
    orient = [b for b in s["binding"] if b["code"] == "ORIENTATION" and b["facade"] != "SE-FENCE"]
    assert len(orient) == 4 and all("mirrored=False" in b["detail"] for b in orient)
    bound = {b["detail"].split("-> ")[1] for b in s["binding"] if b["code"] == "BOUND"}
    assert {"W15", "W16", "W17", "W18", "W01", "W13", "W26", "W14", "SX-03", "D-2F-01"} <= bound
    # the only features on no plan: three 100 x 100 squares above W14 (SE) and six on the fence elevation
    assert s["issue_codes"]["ELEVATION_ONLY"] == 9
    only = [r for r in _issues() if r["code"] == "ELEVATION_ONLY"]
    assert sum("SE (P7757.dxf" in r["detail"] for r in only) == 3
    assert sum("FENCE ELEVATION" in r["detail"] for r in only) == 6


def test_findings_are_never_quantities():
    for r in _rows().values():
        assert not any(k.lower().endswith("m2") for k in r)
