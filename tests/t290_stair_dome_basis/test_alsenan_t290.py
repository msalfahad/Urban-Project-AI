"""T-290 Alsenan stairs and domes basis ledger pins (committed inputs only; no private data)."""
from __future__ import annotations

import io
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t290"
sys.path.insert(0, str(HERE))
import stair_dome_basis as B  # noqa: E402
import t290_alsenan as A  # noqa: E402


@pytest.fixture(scope="module")
def built():
    cand, comps, rows = A.build()
    return cand, comps, {r["line_id"]: r for r in rows}, rows


def test_candidate_digest_is_the_gate_b_csv(built):
    cand = built[0]
    assert cand["candidate_lines_csv_sha256"].startswith("a4dc01dd") and cand["lines_in_candidate"] == 3699
    assert len(cand["lines"]) == 14


def test_every_stair_dome_line_once_and_residual_zero(built):
    cand, comps, rows, lst = built
    assert sorted(rows) == sorted(l["line_id"] for l in cand["lines"])
    s = A.summary(cand, comps, lst)
    assert s["residual_m3"] == {"STAIR": 0.0, "DOME": 0.0}
    assert s["engine_released_m3"] == 8.064447


def test_line_statuses(built):
    rows = built[2]
    V = ("L-67e4b0485135f84acc46", "L-bb0e57b1948175a3d5b8", "L-8ea34765d16b54898140", "L-fffa895ed96b9d6a682c")
    assert all(rows[i]["status"] == B.VERIFIED for i in V)
    assert rows["L-2416e65f053a14199cfc"]["status"] == B.DC
    assert round(rows["L-2416e65f053a14199cfc"]["drawing_qty_m3"], 6) == 0.4696
    for i in ("L-7863355dfcb68a681d2d", "L-b6b0354b7842f0ed6e41", "L-821032bc04a0b0d02133", "L-659243ed9fc2831c3ae8",
              "L-d5401fa8986900c66c37", "L-061e18cf35a4b6b33d68"):
        assert rows[i]["status"] == B.HELD and rows[i]["drawing_qty_m3"] is None      # blank, never 0
    assert {rows[i]["status"] for i in ("L-14f885e95132fa0cedec", "L-33769fb181e11dca13cc",
                                        "L-004e8e9fd032cb0aeb72")} == {B.NOT_APPLICABLE}


def test_held_lines_carry_their_closable_parts(built):
    rows = built[2]
    assert round(rows["L-7863355dfcb68a681d2d"]["closable_component_m3"], 6) == 1.227952      # MS1-LD + MS1-U VERIFIED
    assert round(rows["L-7863355dfcb68a681d2d"]["drawing_low_m3"], 6) == 2.441381             # + MS1-L A + turn lows
    assert round(rows["L-7863355dfcb68a681d2d"]["drawing_high_m3"], 6) == 2.662365
    assert round(rows["L-b6b0354b7842f0ed6e41"]["closable_component_m3"], 6) == 1.536225      # ST-02 Q-50 A cond
    assert rows["L-b6b0354b7842f0ed6e41"]["drawing_low_m3"] is None                          # RS-C has no bound
    assert round(rows["L-821032bc04a0b0d02133"]["closable_component_m3"], 6) == 0.100286      # D1 steps DC


def test_2915_label_mapped_to_line_ids(built):
    cand, comps, rows, lst = built
    s = A.summary(cand, comps, lst)
    assert s["held_closable_parts_m3"] == 2.864463
    assert s["t266_label_minus_ledger_m3"] == 0.050626        # T-258 r2: D1 wedge 0.025714 + RS-LD 0.0092 + RS-A 0.015712
    assert round(0.025714 + 0.009200 + 0.015712, 6) == 0.050626
    assert {p["line_id"] for p in s["held_closable_parts"]} == {
        "L-7863355dfcb68a681d2d", "L-b6b0354b7842f0ed6e41", "L-821032bc04a0b0d02133"}
    for p in s["held_closable_parts"]:
        assert p["evidence"]


def test_st03_is_cited_from_t289_never_rebooked(built):
    r = built[2]["L-061e18cf35a4b6b33d68"]
    assert r["ledger_owner"].startswith("T-289") and r["drawing_qty_m3"] is None and r["delta_m3"] is None
    assert round(r["engine_qty_m3"], 6) == 0.948267 and round(r["closable_component_m3"], 6) == 0.355017


def test_drums_have_no_candidate_line(built):
    cand, comps, rows, lst = built
    assert B.unbound(lst, comps) == ["DOME-A-DRUM", "DOME-B-DRUM"]


def test_one_owner_per_soffit_and_formwork_row_and_rows_exist(built):
    comps = built[1]
    seen = [r for c in comps for r in c["soffit_rows"]]
    assert len(seen) == len(set(seen))
    seen = [r for c in comps for r in c["formwork_rows"]]
    assert len(seen) == len(set(seen))
    A.check_owner_rows(comps)
    bad = [dict(c) for c in comps]
    bad[0] = dict(bad[0], soffit_rows=["ST01-NOT-A-ROW"])
    with pytest.raises(B.BasisError, match="not in LEDGER_T281"):
        A.check_owner_rows(bad)


def test_committed_csv_reproduces(built):
    buf = io.StringIO()
    import csv
    w = csv.DictWriter(buf, fieldnames=B.COLUMNS, lineterminator="\n")
    w.writeheader()
    for r in built[3]:
        w.writerow({k: B._fmt(r.get(k)) for k in B.COLUMNS})
    assert buf.getvalue() == (HERE / "BASIS_LEDGER_T290.csv").read_text(encoding="utf-8")
