"""T-367 on the development villa: the committed ledgers reproduce from the pinned V3.0.26 inputs (T-279 / T-333 r2
merged); the black walls close to the candidate's black share; the mortar per m2 agrees with the merged T-176 module
(an independent implementation of the same joint geometry); white walls carry no mortar; held walls stay blank."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t367"
sys.path.insert(0, str(HERE))
sys.path.insert(1, str(ROOT / "research" / "agents_t176"))

import alsenan_t367 as A                                                   # noqa: E402
import block_procurement_v1 as P176                                        # noqa: E402
import masonry_mortar_v1 as M                                              # noqa: E402


def _csv(name):
    return list(csv.DictReader((HERE / name).open(encoding="utf-8")))


def test_committed_files_reproduce():
    assert A.main(["--check"]) == 0


def test_black_closes_to_candidate_share():
    s = json.loads((HERE / "summary.json").read_text(encoding="utf-8"))
    assert s["black_established_m2"] == pytest.approx(312.6661, abs=5e-4)
    assert s["black_by_t"]["0.15"]["area"] == pytest.approx(201.1421, abs=5e-4)
    assert s["black_by_t"]["0.2"]["area"] == pytest.approx(111.524, abs=5e-4)
    assert s["black_established_m2"] + s["white_established_m2"] == pytest.approx(579.1011, abs=5e-4)
    # hand: 201.1421 x 0.0110625 + 111.524 x 0.01475
    assert s["black_mortar_m3"] == pytest.approx(201.1421 * 0.0110625 + 111.524 * 0.01475, abs=1e-6)
    assert s["black_mortar_bed_m3"] + s["black_mortar_head_m3"] == pytest.approx(s["black_mortar_m3"], abs=2e-6)


def test_agrees_with_merged_t176_joint_geometry():
    for t in (0.15, 0.20):
        assert M.per_m2(M.MODULE_BLACK, t)["total"] == pytest.approx(
            P176.mortar_per_m2("BLACK_40x20", t)["m3_per_m2"], abs=1e-12)


def test_every_wall_once_and_statuses():
    rows = _csv("MORTAR_BY_WALL_T367.csv")
    ids = [r["wall_id"] for r in rows]
    assert len(ids) == len(set(ids))
    for r in rows:
        if r["block_type"] == "BLACK" and r["mortar_installed_m3"]:
            assert r["mortar_status"] == M.AOA and r["part_line_id_v3026"].startswith("L-")
        if r["block_type"] == "WHITE":
            assert r["mortar_installed_m3"] == "" and r["adhesive"] == "HELD"
        if r["area_status"] == "HELD":
            assert r["area_m2"] == "" and r["mortar_installed_m3"] == ""


def test_part_line_groups_match_the_candidate():
    groups = {(r["parent_line_id"], r["part_line_id_v3026"]) for r in _csv("MORTAR_BY_WALL_T367.csv")
              if r["part_line_id_v3026"]}
    assert len(groups) == 19                      # T-279 s.2 parts: GF 3 + 4, 1F 3 + 3, 2F 2 + 4
    blk = {g for g in groups if any(r["part_line_id_v3026"] == g[1] and r["block_type"] == "BLACK"
                                    for r in _csv("MORTAR_BY_WALL_T367.csv"))}
    assert len(blk) == 11                         # black parts: GF 3 + 1, 1F 3 + 1, 2F 1 + 2
