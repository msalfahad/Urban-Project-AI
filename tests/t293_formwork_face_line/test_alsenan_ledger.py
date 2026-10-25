"""T-293 Alsenan formwork face-to-line ledger (part 1) from committed inputs only: own ARCH_TAKEOFF_V3.0.16 run on the
Drive copies (research/agents_t293/t293_extract.py), merged formwork r4 (T-264), T-282 r3, T-289 pairing / basis,
T-248 column register, T-253 boundary runs, T-220 planted columns. Re-builds without writing; pins the engineering
results (development villa; not an accuracy claim)."""
from __future__ import annotations

import collections
import csv
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t293"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "research" / "agents_t264"))
import face_line_ledger as F  # noqa: E402
import t293_alsenan as A  # noqa: E402

CAND, LINES, BIND, OUT = A.build()
ROWS = OUT["rows"]


def _sum(pred, k="m2"):
    return round(sum((r[k] or 0.0) for r in ROWS if pred(r)), 6)


def test_the_source_is_formwork_r4_exactly():
    import formwork_r4 as W
    f = lambda v: None if v == "" else float(v)  # noqa: E731
    rows = [dict(x, m2=f(x["m2"]), held_lo=f(x["held_lo"]), held_hi=f(x["held_hi"])) for x in A.r4_rows()]
    assert len(rows) == 361
    t = W.totals(rows)
    assert (t["G_CALCULATED"], t["BELOW_CALCULATED"], t["OQ10_FORMED"], t["OQ10_EARTH_CAST"]) == \
        (1015.963, 47.663, 209.112, 0.0)


def test_candidate_identity_and_no_formwork_line_in_it():
    assert CAND["candidate"] == "ARCH_TAKEOFF_V3.0.16" and CAND["lines_in_candidate"] == 3699
    assert CAND["project"]["route"]["revision_set_sha256"].startswith("297e913d")
    assert CAND["formwork_lines_in_candidate"] == []
    assert CAND["candidate_lines_csv_sha256"].startswith("a4dc01dd")      # = the T-270 / T-289 lines csv


def test_every_face_once_and_closure_residual_zero_per_status_alternative_method():
    ids = [r["face_id"] for r in ROWS]
    assert len(ids) == len(set(ids))
    assert sum(c["rows"] for c in OUT["closure"]) == 361 + 21 + 2          # every r4 row + every changing T-282 row
    assert all(abs(c["residual_m2"]) < 5e-4 and abs(c["residual_lo"]) < 5e-4 and abs(c["residual_hi"]) < 5e-4
               for c in OUT["closure"])


def test_part1_members_each_on_one_line():
    tied = collections.Counter(r["element"] for r in ROWS if r["tie"] == F.TIED)
    assert tied == {"GROUND_BEAM": 155, "FOOTING": 59, "COLUMN": 59, "STRAP": 9, "POOL": 2, "BOUNDARY": 1}
    gb = {r["line_id"] for r in ROWS if r["tie"] == F.TIED and r["element"] == "GROUND_BEAM"}
    assert len(gb) == 56 and all(LINES[i]["item_code"] == "STR.CONC.GROUND_BEAM" for i in gb)
    assert len({r["line_id"] for r in ROWS if r["tie"] == F.TIED and r["element"] == "COLUMN"}) == 59
    assert len({r["line_id"] for r in ROWS if r["tie"] == F.TIED and r["element"] == "FOOTING"}) == 26
    for r in ROWS:                                      # no tied face on a superseded / undrawn line
        if r["tie"] == F.TIED:
            assert LINES[r["line_id"]]["evidence_state"] != "NOT_APPLICABLE_WITH_EVIDENCE"


def test_ground_beam_totals_on_their_lines():
    gb = lambda st, alt="": (lambda r: r["element"] == "GROUND_BEAM" and r["tie"] == F.TIED and  # noqa: E731
                             r["status"] == st and (r.get("alternative") or "") == alt)
    assert _sum(gb("CALCULATED")) == pytest.approx(47.948, abs=5e-4)            # r4 47.663 + T-282 170+7C3#4 B 0.285
    assert _sum(gb("ALTERNATIVE", "OQ10_FORMED")) == pytest.approx(74.360, abs=5e-4)
    assert _sum(gb("HELD", "OQ10_FORMED"), "lo") == pytest.approx(65.762, abs=5e-3)


def test_the_three_oblique_bands_and_the_main_exterior_faces_on_the_t289_basis():
    ob = json.loads((HERE / "OBLIQUE_BAND_PAIRING_T293.json").read_text())["bands"]
    assert {b: v["run"] for b, v in ob.items()} == {"BAND0037.1": "17E+17F#1", "BAND0038": "180+181#1",
                                                    "BAND0039": "182+183#1"}
    assert all(v["centroid_distance_mm"] < 30 and v["next_distance_mm"] > 1300 for v in ob.values())
    ext = [r for r in ROWS if r["element"] == "GROUND_BEAM" and r["status"] == "CALCULATED"]
    assert all(r["basis"] == "DEPTH_PRINTED" for r in ext)
    assert {r.get("concrete_basis_t289", "").split()[0] for r in ext} == {"DRAWING-CONFIRMED"}


def test_footing_type_rows_split_per_footing_and_handles_bind_by_mark():
    f4 = [r for r in ROWS if r.get("split_of") == "R4-000"]                     # F x4 sides FORMED 4.08
    assert len(f4) == 4 and all(r["m2"] == pytest.approx(1.02) for r in f4)
    h = CAND["footing_handles"]
    assert {k: v["mark"] for k, v in h.items()} == {"166B": "F3", "1B2A": "F15", "1B07": "F11", "1B19": "F6",
                                                    "1B24": "F8", "180C": "FN"}
    notch = {r["face_id"]: r for r in ROWS if r.get("split_of") == "R4-031"}
    assert {r["line_id"] for r in notch.values()} == {h["180C"]["line_id"],
                                                     next(i for i, l in LINES.items() if "F9@" in l["element_id"])}
    f10 = [r for r in ROWS if r["face_id"] in ("R4-030", "R4-036")]
    assert {r["line_id"] for r in f10} == {"L-164ae9d338976be9e582"}               # the 1B1B CONFLICT line


def test_columns_and_planted_columns():
    c = {r["members"][0]: r["line_id"] for r in ROWS if r["element"] == "COLUMN" and r["tie"] == F.TIED}
    assert c["COLUMN:COL-1F-57"] == "L-2ac3c9b3b4c2221a0299"                    # PC-1F-A (T-220)
    assert BIND["_column_offset"] == {"dx": 75968, "dy": 14448, "votes": 32}
    assert _sum(lambda r: r["element"] == "COLUMN" and r["status"] == "CALCULATED") == pytest.approx(117.461, abs=5e-4)


def test_named_gaps_are_kept_never_zeroed():
    nl = {r["face_id"]: r for r in ROWS if r["tie"] == F.NO_LINE}
    assert sum(1 for r in nl.values() if r["members"][0].startswith("BOUNDARY_GB:")) == 11
    assert _sum(lambda r: r["tie"] == F.NO_LINE and r.get("alternative") == "OQ10_FORMED") == pytest.approx(35.256)
    assert {r["members"][0] for r in nl.values() if not r["members"][0].startswith("BOUNDARY_GB:")} == \
        {"BOUNDARY_PADS", "LIFT"}
    sp = [r for r in ROWS if r["tie"] == F.SPLIT]
    assert [r["members"][0] for r in sp] == ["GB:ARC:139+13A"] and sp[0]["status"] == "HELD"
    s1 = [r for r in ROWS if r["tie"] == F.SCENARIO]
    assert len(s1) == 7
    cons = json.loads((HERE / "T199_FORMWORK_BY_LINE_T293.json").read_text())
    assert not any(f["status"] == "S1_NOT_RELEASED" for l in cons["lines"] for f in l["faces"])


def test_t290_drawn_readings_enter_as_deltas_after_its_merge():
    d = {r["face_id"]: r for r in ROWS if r["face_id"].startswith("T290-")}
    assert {k: v["m2"] for k, v in d.items()} == {"T290-MS2-LD": -0.065, "T290-RS-A": -0.040}
    assert all(r["tie"] == F.NAMED and r["status"] == "CALCULATED" for r in d.values())
    e1 = next(r for r in ROWS if r["item"].startswith("E1 waist soffit"))
    assert e1["tie"] == F.NAMED and "CONFLICT" in e1["basis_note"]


def test_committed_outputs_equal_a_fresh_build(tmp_path):
    A.write(tmp_path)
    for n in ("FORMWORK_FACE_TO_LINE_T293.csv", "T199_FORMWORK_BY_LINE_T293.json", "summary_t293.json"):
        assert (tmp_path / n).read_bytes() == (HERE / n).read_bytes(), n
