"""T-293 part 2, Alsenan (development villa; not an accuracy claim): the 65 slab-level rows of formwork r4 tied piece by
piece to the candidate concrete lines, from committed inputs only (T293P2_WALK_RECORDS.json is the merged r3 walk
re-run on the Drive copy 'ST7757 dxf.dxf' 9f9d1179 and attributed per run; its r3 totals were asserted when it was
written). Re-builds without writing and pins the engineering results."""
from __future__ import annotations

import collections
import csv
import json
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t293"
sys.path.insert(0, str(HERE))
import face_line_ledger as F  # noqa: E402
import t293p2_ledger as L  # noqa: E402

CAND, SRC, OUT = L.build()
ROWS = OUT["rows"]
LINES = {x["line_id"]: x for x in CAND["lines"]}


def m2(r):
    return r["m2"] if r["m2"] is not None else (r.get("held_from") or 0.0)


def total(pred, k=m2):
    return round(sum(k(r) for r in ROWS if pred(r)), 6)


def test_every_slab_level_r4_row_is_a_source_row_once():
    want = [i for i, x in enumerate(L.r4_rows()) if x["element"] in L.SLAB_LEVEL]
    assert len(want) == 65
    assert sorted(int(s["face_id"][3:]) for s in SRC) == want


def test_closure_per_status_method_residual_zero():
    assert OUT["closure"]
    for c in OUT["closure"]:
        assert (c["residual_m2"], c["residual_lo"], c["residual_hi"]) == (0.0, 0.0, 0.0), c
    by = {(c["status"], c["method"]): c for c in OUT["closure"]}
    assert by[("CALCULATED", "E=G")]["m2"] == pytest.approx(375.0481 + 2.4, abs=1e-6)
    assert by[("CALCULATED", "G")]["m2"] == pytest.approx(428.220812, abs=1e-6)


def test_slab_soffits_one_piece_per_panel_on_its_own_line():
    s = [r for r in ROWS if r["members"][0].startswith("PANEL:")]
    assert len(s) == 62 and all(r["tie"] == F.TIED for r in s)
    assert len({r["line_id"] for r in s}) == 62
    assert all(LINES[r["line_id"]]["item_code"] == "STR.CONC.SLAB" for r in s)
    per = collections.defaultdict(float)
    for r in s:
        per[r["floor"]] += r["m2"]
    assert {k: round(v, 4) for k, v in per.items()} == {"GF": 206.6845, "1F": 123.4786, "2F": 44.885}
    inter = [r for r in s if "INTERCHANGEABLE" in (r.get("tie_reason") or "")]
    assert len(inter) == 10


def test_element_method_counts_cb5_span_2_twice_in_the_source():
    d = [r for r in ROWS if r["tie"] == L.DUP]
    assert sorted(round(r["m2"], 6) for r in d) == [0.74, 1.776]
    assert all(".R138.DUP" in r["face_id"] for r in d)
    gf_e = total(lambda r: r.get("split_of") == "R4-253" and r["tie"] == F.TIED)
    assert gf_e == pytest.approx(54.99798, abs=1e-6)                    # r4 prints 55.738 (+0.740)


def test_drawing_face_pieces_mostly_tied_split_small_and_named():
    g = lambda r: r["status_in"] == "CALCULATED" and r.get("method") == "G" and r["element"] == "BEAM"  # noqa: E731
    tied = total(lambda r: g(r) and r["tie"] == F.TIED)
    split = total(lambda r: g(r) and r["tie"] == F.SPLIT)
    assert tied + split == pytest.approx(56.357303 + 34.065 + 7.824 + 171.368085 + 93.475 + 27.746, abs=2e-3)
    assert split == pytest.approx(5.5844, abs=1e-3)
    for r in ROWS:
        if r["tie"] == F.SPLIT:
            assert r["m2"] is None and len(r["split_lines"]) >= 2      # blank, the run lines named


def test_ring_b7_faces_on_the_ring_line_and_band_0049_has_no_drawing_face():
    ring = LINES_BY_EL = {x["element_id"]: x["line_id"] for x in CAND["lines"]}
    lid = LINES_BY_EL["HL:BEAM_LEDGER:GF:BM-GF-050.r2#RING-B7"]
    soff = [r for r in ROWS if r["face_id"] == "R4-254.RING"]
    assert soff[0]["line_id"] == lid and soff[0]["m2"] == pytest.approx(0.666406)
    b49 = LINES_BY_EL["P-C:BEAMS:GF:BAND0049"]
    assert not [r for r in ROWS if r.get("line_id") == b49 and r.get("method") == "G"]   # F-T293-P2-02
    assert [r for r in ROWS if r.get("line_id") == b49 and r.get("method") == "E"]
    assert ring


def test_untied_pieces_are_the_named_ones():
    no = [r for r in ROWS if r["tie"] == F.NO_LINE]
    assert sorted(r["members"][0] for r in no) == ["UNMATCHED:GF-095", "UNMATCHED:GF-151", "UNMATCHED:GF-152",
                                                   "UNMATCHED:GF-161", "UNMATCHED:GF-167"]
    assert round(sum(r["hi"] for r in no), 3) == 0.618
    gf112 = [r for r in ROWS if r["members"][0] == "UNMATCHED:GF-112"]
    assert gf112[0]["line_element_id"] == "U-C:BEAMS:GF:BAND0030.2"      # T-241: BM-GF-062 partition face GF-112
    named = {r["face_id"] for r in ROWS if r["tie"] == F.NAMED}
    assert len(named) == 4


def test_no_face_on_a_superseded_or_absent_line_and_states_carried():
    for r in ROWS:
        if r["tie"] == F.TIED:
            assert LINES[r["line_id"]]["evidence_state"] != "NOT_APPLICABLE_WITH_EVIDENCE"
            assert r["line_v3017"]
    flagged = [r for r in ROWS if r.get("line_flag")]
    assert len(flagged) == 26 and total(lambda r: bool(r.get("line_flag"))) == pytest.approx(3.2574, abs=1e-4)
    two_f = [r for r in ROWS if r["face_id"].startswith("R4-309.COL-2F-")]
    assert all(r["line_flag"] and "BLOCKED_RFI" in r["line_v3017"] for r in two_f)


def test_held_stays_blank():
    for r in ROWS:
        if r["status"] == "HELD":
            assert r["m2"] is None


def test_committed_outputs_are_a_fresh_build():
    with tempfile.TemporaryDirectory() as d:
        L.write(Path(d))
        for f in ("FORMWORK_FACE_TO_LINE_T293_P2.csv", "T199_FORMWORK_BY_LINE_T293_P2.json", "summary_t293_p2.json"):
            assert (Path(d) / f).read_bytes() == (HERE / f).read_bytes(), f


def test_walk_records_hold_no_coordinates():
    w = json.loads((HERE / "T293P2_WALK_RECORDS.json").read_text())
    keys = set().union(*(set(r) for r in w["records"]))
    assert keys <= {"floor", "face", "pieces", "owner_kind", "owner", "owner_status", "category", "m2", "run",
                    "plan_long_m", "plan_short_m"}
    assert w["r3_checks"] == 12
