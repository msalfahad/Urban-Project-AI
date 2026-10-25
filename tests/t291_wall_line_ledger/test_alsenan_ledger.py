"""T-291 Alsenan wall-to-line ledger from committed inputs only (register v4, the extracted V3.0.15 masonry lines, the
opening table citing merged ledgers). Rebuilds without writing and pins the results (development villa; not an
accuracy claim)."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t291"
sys.path.insert(0, str(HERE))
import t291_alsenan as A  # noqa: E402
import wall_line_ledger as R  # noqa: E402

B = A.build()
F = A.outputs(B)


def test_committed_outputs_reproduce_byte_for_byte():
    for name, text in F.items():
        assert (HERE / name).read_text(encoding="utf-8") == text, name


def test_candidate_is_the_v3015_gate_b_file_and_every_masonry_line_is_listed_once():
    c = B["candidate"]
    assert c["candidate"] == "ARCH_TAKEOFF_V3.0.15"
    assert c["candidate_lines_csv_sha256"].startswith("a4dc01dd")          # T-270 r2 / T-289 V3.0.15 csv
    ids = [l["line_id"] for l in B["lines"]]
    assert len(ids) == len(set(ids)) == 28
    av = {l["line_id"] for l in B["lines"] if l["item_code"] in A.AREA_VOLUME}
    assert len(av) == 21 and {r["line_id"] for r in B["rows"]} == av and B["unmatched_lines"] == []
    assert {r["line_id"] for r in B["runs"]} == set(ids) - av                 # the 7 run (lm) lines, compared only


def test_every_register_wall_once_per_item_and_closure_zero_on_every_status():
    assert len(B["walls"]) == 76 and B["unmatched_walls"] == []
    for it in A.AREA_VOLUME:
        rows = [r for r in B["rows"] if r["item_code"] == it]
        assert sorted(r["wall_id"] for r in rows) == sorted(w["wall_id"] for w in B["walls"])
        assert all(abs(v) <= R.TOL for v in B["closures"][it].values())


def test_register_v4_totals_are_carried_exactly():
    s = json.loads(F["summary.json"])["by_status_m2"]
    assert s["VERIFIED"] == pytest.approx(297.847, abs=1e-4)
    assert s["ASSUMED — OWNER-APPROVED"] == pytest.approx(76.2187, abs=1e-4)
    # basis A drawing-confirmed 28.7331 + 1F-W18 (basis B, whole) 19.7326
    assert s["DRAWING-CONFIRMED"] == pytest.approx(28.7331 + 19.7326, abs=1e-4)
    assert s["VERIFIED"] + s["ASSUMED — OWNER-APPROVED"] + 28.7331 == pytest.approx(402.7988, abs=1e-4)
    assert s["HELD ON DROP length (m)"] == pytest.approx(7.9131, abs=1e-4)
    assert s["HELD ON DROP upper at d=0 (not a quantity)"] == pytest.approx(46.8019, abs=1e-4)
    det_b = s["VERIFIED"] + s["ASSUMED — OWNER-APPROVED"] + s["DRAWING-CONFIRMED"] + s["ESTABLISHED PART (basis B)"]
    assert det_b == pytest.approx(579.1011, abs=1e-4)


def test_drop_term_is_a_term_never_evaluated():
    drop = [r for r in B["rows"] if r["status"] == R.HELD_ON_DROP and r["item_code"] == "MAS.BLOCK"]
    assert sorted(r["wall_id"] for r in drop) == ["GF-W12", "GF-W16", "GF-W20", "GF-W31", "GF-W32", "GF-W34"]
    assert all(r["carried"] is None for r in drop)
    assert sum(r["drop_length_m"] for r in drop) == pytest.approx(7.9131, abs=1e-6)
    gf15 = next(x for x in B["summary"] if x["item_code"] == "MAS.BLOCK" and x["floor"] == "GF" and x["family"] == "0.15")
    gf20 = next(x for x in B["summary"] if x["item_code"] == "MAS.BLOCK" and x["floor"] == "GF" and x["family"] == "0.2")
    assert gf15["drop_coefficient"] + gf20["drop_coefficient"] == pytest.approx(7.9131, abs=1e-6)
    assert "x d" in gf15["line_expression"] and "x d" in gf20["line_expression"]


def test_every_verified_wall_cites_its_checker_run():
    v = [r for r in B["rows"] if r["status"] == R.VERIFIED and r["item_code"] == "MAS.BLOCK"]
    assert len(v) == 18 and all(re.match(r"Checker 2026-10-2[45] \d\d:\d\d", r["verified_by"]) for r in v)
    assert "GF-W12" not in {r["wall_id"] for r in v}                          # withdrawn by the Checker 02:00


def test_held_walls_blank_with_their_item_never_zero():
    held = [r for r in B["rows"] if r["status"] == R.HELD]
    assert held and all(r["carried"] is None and r["held_item"] for r in held)
    assert len({r["wall_id"] for r in held}) == 28


def test_conflict_increments_outside_every_total():
    inc = {r["wall_id"]: r["conflict_increment"] for r in B["rows"] if r["item_code"] == "MAS.BLOCK"
           and r["conflict_increment"]}
    assert inc == pytest.approx({"GF-W19": 0.017, "GF-W20": 0.017, "GF-W22": 0.0128, "GF-W34": 0.0139,
                                 "1F-W11": 0.017, "1F-W16": 0.017})
    assert sum(inc[w] for w in ("GF-W19", "GF-W20", "GF-W22", "GF-W34")) == pytest.approx(0.0607)


def test_openings_once_by_id_and_summing_to_the_register_deductions():
    ops = B["openings"]
    assert len({o["opening_id"] for o in ops}) == len(ops) == 71
    w18 = next(o for o in ops if o["opening_id"] == "W18")
    assert w18["host"] == "1F-W00" and w18["state"] == "DEDUCTED" and w18["deduction_m2"] == pytest.approx(1.0094)
    w03 = next(o for o in ops if o["opening_id"] == "W03")
    assert w03["state"] == "NOT_APPLICABLE" and "T-255" in w03["source"]
    assert B["deductions"]["1F-W00"] == pytest.approx(9.7354, abs=1e-4)
    assert B["deductions"]["1F-W06"] == pytest.approx(3.2885, abs=1e-4)
    with pytest.raises(R.LedgerError, match="^OPENING_TWICE"):
        R.opening_ledger(ops + [dict(w18, host="1F-W25")], B["walls"])


def test_engine_lines_carry_no_masonry_quantity():
    """the candidate's every m2 / m3 masonry line is BLOCKED (no masonry height in the drawing): T-279 replaces a
    blank, it does not correct a figure."""
    av = [l for l in B["lines"] if l["item_code"] in A.AREA_VOLUME]
    assert all(l["measured_net"] is None and l["evidence_state"] == "BLOCKED_RFI" for l in av)
    assert json.loads(F["summary.json"])["engine_lines_with_quantity"] == 0


def test_no_coordinates_or_names_in_committed_files():
    for n in F:
        t = (HERE / n).read_text(encoding="utf-8")
        assert not re.search(r"\d{5,}\.\d+", t), n                        # no drawing coordinates
    assert not re.search(r"\d{5,}\.\d+", A.CANDIDATE.read_text(encoding="utf-8"))
