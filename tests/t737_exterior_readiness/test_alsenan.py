"""T-737 on the development villa: the committed readiness equals a rebuild from merged / pinned repository files;
stage census on V3.0.73 (3 LIVE hosts, 15 free new lines, stale 0), sources unchanged, the cited records still say
what they are cited for, parapet tops agree with the parapet concrete floors, and the 43 exterior bead rows re-bind
onto the stage lines with every arris once (310.6831 m.l by hand). Repository files only; nothing is written."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for p in ("agents_t737", "agents_t728"):
    sys.path.insert(0, str(ROOT / "research" / p))
import t737_alsenan as A  # noqa: E402
import t737_rules as R  # noqa: E402


@pytest.fixture(scope="module")
def built():
    return A.build()


def test_committed_outputs_reproduce(built):
    assert A.OUT_JSON.read_text(encoding="utf-8") == json.dumps(built, ensure_ascii=False, indent=1,
                                                                 sort_keys=True) + "\n"
    assert A.OUT_CSV.read_text(encoding="utf-8") == A.to_csv(built)


def test_pins_and_stage_identity(built):
    st = built["stage"]
    assert st["commit"] == "080ccaa5" and st["summary_blob"] == "040ed5f9a8766b1a779dc8c61d7daf22280e6c8a"  # = T-698
    assert built["stage_identity"]["faces"] == {"face_lines": 18, "faces": 126, "openings": 38}
    assert all(len(v) == 64 for v in built["pins"].values())


def test_line_census_stale_zero(built):
    assert built["line_census_counts"] == {"LIVE": 3, "LIVE_NEW": 15}
    assert built["stale_lines"] == []
    live = {x["line_id"] for x in built["line_census"] if x["census"] == R.LIVE}
    assert live == {"L-b05f70c92405dbcfbe62", "L-8bb83e16cc7b104ab88b", "L-d52c4f763b19aedf8b8b"}


def test_hosts_unchanged_v61_to_v73_and_no_facade_line_moved(built):
    h = built["host_history"]
    assert [v["hosts"] for v in h["versions"]][1:] == ["same"] * 12
    m = h["v61_to_v73"]
    assert (m["changed"], m["added"], m["removed"], m["facade_lines_moved"]) == (132, 50, 0, [])


def test_sources_unchanged(built):
    assert len(built["sources"]) == 12 and built["sources_changed"] == []


def test_evidence_verdicts(built):
    v = {e["id"]: e["verdict"] for e in built["evidence"]}
    assert v == {"E1": "AGREES", "E2": "AGREES", "E3": "AGREES", "E4": "CONFLICT", "E4b": "CONFLICT",
                 "E5": "NOT_THE_SAME_ELEMENT", "E6": "AGREES", "E6b": "AGREES", "E7": "FIXED"}


def test_parapet_tops_by_hand(built):
    t = {x["line"]: x for x in built["parapet_tops"]}
    assert abs(5.99701 * 0.30 - 1.799103) < 1e-6 and abs(9.83151 * 0.30 - 2.949453) < 1e-6
    assert abs(5.415 * 0.30 - 1.6245) < 1e-9 and abs(5.592956 * 0.30 - 1.677886) < 1e-5
    assert all(x["verdict"] == "AGREES" for x in t.values()) and len(t) == 4


def test_beads_every_row_rebound_arris_once(built):
    b = built["beads"]
    ids = {r["id"] for r in b["rows"]}
    assert len(ids) == 43 and b["rows_out"] == 51
    rec = b["reconciliation"]
    assert rec["total"] == {"ledger_m": 310.6831, "parts_m": 310.6831}       # = 183.5 + 88.5122 + 38.6709 (T-728)
    assert (rec["GF"]["ledger_m"], rec["1F"]["ledger_m"], rec["2F"]["ledger_m"]) == (183.5, 88.5122, 38.6709)
    assert rec["measured_parts_by_state"] == {"HELD_BOUND": 269.6122, "NO_HOST": 1.4, "RELEASED": 39.6709}
    assert abs(269.6122 + 1.4 + 39.6709 - 310.6831) < 1e-9
    assert all(r["host_after"] != "" for r in b["rows"])


def test_specific_splits_by_hand(built):
    s = built["beads"]["splits"]
    assert s["EXT#2F-CONVEX"]["by_line"] == {"L-d52c4f763b19aedf8b8b": 16.8,
                                             "NEW FIN.EXT.FINISH PARAPET-OUTER 2F +13.90": 2.0}   # 4 x 4.20 + 4 x 0.50
    assert s["EXT#1F-CONVEX"]["by_line"] == {"L-8bb83e16cc7b104ab88b": 37.8,
                                             "L-b05f70c92405dbcfbe62": 1.2}   # 9 x 4.20 + NE-2/SE-1 +4.30 .. +5.50
    g = s["EXT#GF-CONVEX"]["by_line"]
    assert g == {"NEW FIN.EXT.FINISH PLINTH GF": 7.4, "L-b05f70c92405dbcfbe62": 57.5,
                 "NEW FIN.EXT.FINISH PARAPET-OUTER ANNEX +4.30": 1.0, "NEW FIN.EXT.FINISH PARAPET-OUTER GF +5.50": 1.0}
    assert abs(sum(g.values()) - 66.9) < 1e-9
    assert s["EXT#GF-MOUTHS"]["by_line"]["None"] == 1.4                       # 2 x (+4.80 .. +5.50) above NE-6


def test_no_bead_released_on_a_held_host_and_none_zero(built):
    for r in built["beads"]["rows"]:
        if r["bead_state_after"] == "RELEASED":
            assert r["host_after_state"] == "RELEASED" and r["value"] > 0
        if r["bead_state_after"] == "HELD_BOUND":
            assert r["high"] > 0
        if r["host_after"] == "NO_HOST":
            assert r["bead_state_after"] == "HELD_BLANK" and r["value"] is None


def test_d_gf_07_conflict_carried_not_picked(built):
    r = [x for x in built["beads"]["rows"] if x["id"] == "D-GF-07#EXT"][0]
    assert "CONFLICT" in r["note"] and r["bead_state_after"] == "HELD_BOUND" and r["value"] is None


def test_adverse_gone_host_on_the_real_stage(built):
    stage = A.jload(A.STAGE)
    idx = [x for x in A.jload(A.IDX73)["lines"] if x["line_id"] != "L-8bb83e16cc7b104ab88b"]
    row = [r for r in stage["rows"] if r["line_id"] == "L-8bb83e16cc7b104ab88b"][0]
    c = R.classify_stage_line(row, idx, item_code="FIN.EXT.FINISH", unit="m2")
    assert c["census"] == R.GONE and c["host_now"] is None      # the 1F ARCH.FACADE neighbour is never taken
