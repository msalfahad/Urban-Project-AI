"""T-526 on the development villa: the committed end census and per-end effects reproduce from the merged inputs; the
4 F-T520-1 ends and every further missed end by structural id; held ends blank by name (never 0); hand pins."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t526"
sys.path.insert(0, str(HERE))
import t526_alsenan as A  # noqa: E402

F20 = 0.92625 * 0.20 * 0.010


def _csv(name):
    return list(csv.DictReader((HERE / "out" / name).open(encoding="utf-8")))


def _ends():
    return {(r["wall_id"], r["end"]): r for r in _csv("MISSED_ENDS_T526.csv")}


def test_committed_files_reproduce():
    assert A.main(["--check"]) == 0


def test_f_t520_1_four_ends_confirmed_with_structural_ids():
    e = _ends()
    want = {("1F-W09", "0"): ("COL-1F-37", "C1"), ("1F-W23", "0"): ("COL-1F-57", "P.C 20x70"),
            ("2F-W01", "0"): ("COL-2F-53", "C1"), ("2F-W08", "0"): ("COL-2F-54", "C2")}
    for k, (cid, mark) in want.items():
        r = e[k]
        assert (r["class_v2"], r["gap_mm"], r["column_t119"], r["mark"]) == ("COLUMN", "0.0", cid, mark)
        assert r["st_handle"] and r["arch_column"]          # drawn on BOTH sheets (S-COL.BON + architectural outline)


def test_full_census_further_missed_ends():
    e = _ends()
    computed = sorted(k for k, r in e.items() if r["state"] == "COMPUTED")
    assert computed == sorted([("1F-W09", "0"), ("1F-W23", "0"), ("2F-W00", "1"), ("2F-W01", "0"), ("2F-W08", "0"),
                               ("GF-W03", "0"), ("GF-W03", "1"), ("GF-W09", "0"), ("GF-W10", "1"), ("GF-W16", "0"),
                               ("GF-W25", "0"), ("GF-W18", "0")])
    h = e[("GF-W20", "1")]
    assert h["state"] == "HELD" and h["class_v2"] == "PARTIAL_COLUMN" and "0.0195" in h["held"]
    assert h["d_ties_nr"] == "" and h["d_perimeter_m3"] == "" and h["d_mesh_owner_ml"] == ""
    s = json.loads((HERE / "out" / "SUMMARY_T526.json").read_text(encoding="utf-8"))
    assert s["classes"] == {"COLUMN": 12, "COLUMN_PIECE_IN_RUN": 54, "NO_COLUMN": 73, "PARTIAL_COLUMN": 1}
    assert s["census_ends"] == 140 and len(s["runs_not_probed"]) == 2
    # the one structural-only outline touching a run lies inside the architectural column piece: no masonry moved
    assert s["structural_only_contacts"] == ["GF-W07 end 1: INSIDE_ARCH_COLUMN_PIECE 31B 0.400..0.600"]


def test_every_end_found_is_at_the_column_face():
    for r in _ends().values():
        if r["state"] == "COMPUTED":
            assert r["gap_mm"] == "0.0"
            assert (r["d_length_m"], r["d_blockwork_m2"], r["d_blocks_nr"]) == ("0.0000", "0.0000", "0.0")


def test_hand_pins_1f_w09():
    r = _ends()[("1F-W09", "0")]
    # perimeter (T-520 builder): F -> C on the 1.80 m segment under B1, block top 3.80: + 3.80 m vertical, - 1 corner
    assert float(r["d_perimeter_m3"]) == pytest.approx(F20 * (3.80 - 0.010), abs=1e-6)
    assert (r["perimeter_before_m3"], r["perimeter_after_m3"]) == ("0.003334", "0.010355")
    # ties: levels 0.6 .. 3.6 under a 3.80 top (3.6 + 0.01 < 3.80): 6; mesh drawing band 3.80 - 0.10 per side
    assert r["d_ties_nr"] == "6" and float(r["d_mesh_drawing_ml"]) == pytest.approx(2 * 3.70, abs=1e-9)


def test_held_effects_are_blank_by_name_never_zero():
    for r in _ends().values():
        if r["state"] != "COMPUTED":
            continue
        if r["ties_state"] != "MEASURED":
            assert r["d_ties_nr"] == "" and r["ties_held"]
        if int(r["mesh_owner_held"]) == int(r["mesh_owner_sides"]):
            assert r["d_mesh_owner_ml"] == "" and r["mesh_held_why"]
        if r["perimeter_state"] == "HELD":
            assert r["d_perimeter_m3"] == "" or r["perimeter_held"]
            assert r["perimeter_held"]
    w = _ends()[("GF-W10", "1")]
    assert "Q-60" in w["perimeter_held"]                   # white block: thin-bed, not R-T520-1


def test_census_has_no_drawing_coordinates():
    rows = _csv("END_CENSUS_V2_T526.csv")
    assert not any(k in rows[0] for k in ("x", "y", "segment", "point"))
    assert len(rows) == 142
