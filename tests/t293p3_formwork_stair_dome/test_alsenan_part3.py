"""T-293 part 3, Alsenan (development villa; not an accuracy claim): the stair, dome and tank rows of formwork r4 tied
piece by piece to the ARCH_TAKEOFF_V3.0.18 stair / dome lines, from committed inputs only. Re-builds without writing
and pins the engineering results."""
from __future__ import annotations

import collections
import csv
import json
import math
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t293"
sys.path.insert(0, str(HERE))
import face_line_ledger as F  # noqa: E402
import t293p3_ledger as L  # noqa: E402

CAND, LINES, SRC, OUT, HELD = L.build()
ROWS = OUT["rows"]
BY = {r["face_id"]: r for r in ROWS}
CLOSABLE = ("L-e37d81a8be8e0aa0010c", "L-67e4b0485135f84acc46", "L-2416e65f053a14199cfc", "L-bb0e57b1948175a3d5b8",
            "L-85f64587588af8537b4b", "L-056402f98a6dbbcde0a0")


def q(r):
    return r["m2"] if r["m2"] is not None else (r.get("held_from") or 0.0)


def test_scope_46_rows_once_and_closure_zero():
    assert len(SRC) == 46
    assert len({s["face_id"] for s in SRC}) == 46
    for c in OUT["closure"]:
        assert c["residual_m2"] == 0 and c["residual_lo"] == 0 and c["residual_hi"] == 0
    calc = next(c for c in OUT["closure"] if c["status"] == "CALCULATED")
    assert calc["m2"] == pytest.approx(92.728, abs=1e-9) and calc["rows"] == 21


def test_v3018_part_lines_recomputed():
    for parent, part in L.T266_PART_IDS.items():
        assert part in LINES and LINES[parent]["evidence_state"] == "BLOCKED_RFI"
    assert LINES["L-e37d81a8be8e0aa0010c"]["measured_net"] == pytest.approx(1.227952)
    assert LINES["L-056402f98a6dbbcde0a0"]["evidence_state"] == "PROVISIONAL"
    assert LINES["L-85f64587588af8537b4b"]["measured_net"] == pytest.approx(0.100286)
    assert LINES["L-2416e65f053a14199cfc"]["measured_net"] == pytest.approx(0.4696)
    assert LINES["L-061e18cf35a4b6b33d68"]["evidence_state"] == "BLOCKED_RFI"      # ST-03 HOLD


def test_tied_calculated_per_closable_line():
    want = {"L-e37d81a8be8e0aa0010c": 1.44 + 2.4 + 4.255527, "L-67e4b0485135f84acc46": 2.419 + 4.303695,
            "L-2416e65f053a14199cfc": 1.495 + 1.44, "L-bb0e57b1948175a3d5b8": 2.419 + 4.263581,
            "L-85f64587588af8537b4b": 0.84,
            "L-056402f98a6dbbcde0a0": 2.121 + 2.093071 + 0.870394 + 5 * 1.2 * 4.5 / 28 + 1.497482}
    got = collections.defaultdict(float)
    for r in ROWS:
        if r["tie"] == F.TIED and r["status"] == "CALCULATED":
            got[r["line_id"]] += r["m2"]
    for k, v in want.items():
        assert got[k] == pytest.approx(v, abs=1e-6), k
    assert sum(got[k] for k in CLOSABLE) == pytest.approx(32.822036, abs=1e-6)


def test_r4_excess_on_closable_lines_named_to_its_cause():
    """r4 prints 36.447 m2 CALCULATED on the six closable lines; 32.822 are drawn faces, 3.625 are not"""
    r4 = 0.0
    for s in SRC:
        if s["element"] == "STAIR" and s["status"] == "CALCULATED" and any(
                (r.get("split_of") or r["face_id"]) == s["face_id"] and r.get("line_id") in CLOSABLE for r in ROWS):
            r4 += s["m2"]
    assert r4 == pytest.approx(36.447, abs=1e-9)
    k = collections.defaultdict(float)
    for r in ROWS:
        if r["element"] == "STAIR" and (r.get("split_of") or r["face_id"]) in {s["face_id"] for s in SRC}:
            k[r["tie"] if r["tie"] != F.TIED else "TIED_" + r["status"]] += q(r)
    assert k[L.NO_FACE] == pytest.approx(0.783422, abs=1e-6)
    assert k[L.DUP] == pytest.approx(1.914913, abs=1e-6)
    assert k[L.RETIRED] == pytest.approx(0.203246, abs=1e-6)
    assert k[F.NO_LINE] == pytest.approx(0.648919, abs=1e-6)


def test_faces_on_held_pieces_are_blank():
    for fid, v in (("R4-317", 2.0), ("R4-318", 3.706), ("R4-329", 2.38)):
        r = BY[fid]
        assert r["status"] == "HELD" and r["m2"] is None and r["held_from"] == pytest.approx(v)
    assert BY["R4-329"]["line_id"] == "L-061e18cf35a4b6b33d68"            # ST-03 E1: HOLD line
    assert BY["R4-316"]["line_id"] == "L-7863355dfcb68a681d2d" and BY["R4-316"]["lo"] == 1.44
    for r in ROWS:
        if r["tie"] == F.TIED and r["members"][0] in HELD:
            assert r["m2"] is None


def test_in_beam_pieces_and_owner_lines():
    assert BY["R4-322.IN_BEAM"]["m2"] == pytest.approx(0.20 * 1.2 * 4.255527 / 3.72, abs=1e-6)
    assert BY["R4-328.IN_BEAM"]["m2"] == pytest.approx(0.20 * 1.2 * 4.263581 / 3.72, abs=1e-6)
    assert BY["R4-324.IN_BEAM"]["m2"] == pytest.approx(0.15 * 1.2 * 4.303695 / 3.755, abs=1e-6)
    assert BY["R4-324.COL691"]["status"] == "HELD" and BY["R4-324.COL691"]["held_from"] == pytest.approx(0.028653,
                                                                                                         abs=1e-6)


def test_duplicates_are_booked_in_part_2():
    m = L.check_dup_booked(L.p2_rows())
    assert m["GF-159"][1] == "L-88ccf8d4505411deb9e5" and m["GF-144"][1] == "L-c914cb3a65e76883a827"
    assert BY["R4-335.B3"]["tie"] == L.DUP and BY["R4-336.B3"]["tie"] == L.DUP and BY["R4-335.CA"]["tie"] == L.DUP


def test_t290_deltas_are_pointers_not_second_corrections():
    assert BY["T290-MS2-LD"]["tie"] == L.POINTER and BY["T290-RS-A"]["tie"] == L.POINTER
    assert BY["R4-326.RETIRED_0480"]["m2"] == pytest.approx(0.065, abs=1e-9)
    assert BY["R4-337.LANE"]["m2"] == pytest.approx(0.964286, abs=1e-6)


def test_domes():
    ro = (2.21 ** 2 + 1.90 ** 2) / 3.80
    assert 2 * math.pi * (ro - 0.10) * 1.80 == pytest.approx(24.15, abs=0.001)          # intrados as printed
    assert BY["R4-343"]["line_id"] == "L-8ea34765d16b54898140" and BY["R4-343"]["m2"] == 24.15
    assert BY["R4-350"]["line_id"] == "L-fffa895ed96b9d6a682c"
    assert BY["R4-345"]["line_id"] == "L-48b7d139bff681199543" and BY["R4-345"]["m2"] is None
    assert BY["R4-352"]["line_id"] == "L-ab37afa17f2ac5b0efd1" and BY["R4-352"]["m2"] is None
    for d in ("R4-346", "R4-353"):
        assert BY[d]["tie"] == F.NO_LINE and BY[d]["m2"] is None
    assert all(BY[f"R4-{i}"]["line_id"] == "L-d5401fa8986900c66c37" for i in (357, 358, 359))
    assert all(r["tie"] == F.SCENARIO for r in ROWS if r["status_in"] == "S1_NOT_RELEASED")


def test_tank_is_the_b15_beam_view():
    assert BY["R4-341"]["tie"] == L.DUPVIEW and "BM-2F-007" in BY["R4-341"]["tie_reason"]
    b15 = [r for r in L.p2_rows() if r["line_id"] == "L-713bc64aaa210610e7fe" and r["m2"]]
    assert {r["face_id"] for r in b15} >= {"R4-298.R125", "R4-299.2F-010.BEAM_SOFFIT", "R4-300.R125"}


def test_alternative_d_beside_never_summed():
    assert BY["R4-324.SOFFIT"]["alt_D_m2"] == pytest.approx(4.303695 + 0.470025, abs=1e-6)
    assert BY["R4-338.SOFFIT"]["alt_D_m2"] == pytest.approx(1.491542 + 0.424483, abs=1e-6)
    cons = F.consumer(ROWS, LINES, "V3.0.18", CAND["project"])
    for ln in cons["lines"]:
        for k, t in ln["totals"].items():
            assert "alt" not in k


def test_every_live_line_has_faces():
    s = L.summary(CAND, LINES, SRC, OUT, HELD)
    assert s["live_lines_without_faces"] == []


def test_committed_outputs_are_a_fresh_build():
    with tempfile.TemporaryDirectory() as d:
        L.write(Path(d))
        for n in ("FORMWORK_FACE_TO_LINE_T293_P3.csv", "T199_FORMWORK_BY_LINE_T293_P3.json", "summary_t293_p3.json",
                  "CANDIDATE_V3018_STAIR_DOME_LINES_T293P3.json"):
            assert (Path(d) / n).read_bytes() == (HERE / n).read_bytes(), n


def test_no_coordinates_in_outputs():
    for n in ("FORMWORK_FACE_TO_LINE_T293_P3.csv", "T199_FORMWORK_BY_LINE_T293_P3.json"):
        t = (HERE / n).read_text(encoding="utf-8")
        assert '"x"' not in t and '"y"' not in t and "coords" not in t
