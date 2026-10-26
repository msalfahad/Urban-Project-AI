"""T-308 formwork r5 on the development villa (Alsenan; pinned; committed outputs = a fresh build). No private file
is read: the BAND0049 walk delta is committed (t308_walk_delta.py made it from the Drive copy 'ST7757 dxf.dxf')."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t308"
sys.path.insert(0, str(HERE))
import t308_r5 as M  # noqa: E402
import t308_rules as R  # noqa: E402


@pytest.fixture(scope="module")
def built():
    states, rows, out, src, keys, walk = M.build()
    return states, rows, out, M.summary(states, rows, out, src, walk), walk


def tot(s, status, method, alt=""):
    return next(t for t in s["totals"] if (t["status"], t["alternative"], t["method"]) == (status, alt, method))


def test_union_and_closure(built):
    _, rows, out, s, _ = built
    assert s["union_rows"] == 1301 and s["r5_rows"] == 1305           # + 4 BAND0049 pieces
    # union = source rows (asserted in build); r5 = merged ledgers + rule deltas (asserted in summary)
    assert s["union_row_rounding_vs_printed"]["CALCULATED||E"][0] == pytest.approx(-0.00058, abs=1e-6)


def test_cb5_span2_once(built):
    _, _, out, s, _ = built
    e = tot(s, "CALCULATED", "E")
    assert e["r4_m2"] == pytest.approx(425.20942, abs=1e-6) and e["r5_m2"] == pytest.approx(422.69342, abs=1e-6)
    d = {r["face_id"]: r for r in out}
    assert d["R4-253.R138.DUP"]["r5_status"] == d["R4-255.R138.DUP"]["r5_status"] == R.REMOVED
    assert d["R4-253.R138"]["r5_m2"] == pytest.approx(0.740) and d["R4-255.R138"]["r5_m2"] == pytest.approx(1.776)


def test_stair_rows_by_cause(built):
    c = built[3]["stair_r4_vs_r5_by_cause"]
    closable = c["r4 printed (CALCULATED rows)"] - c["HELD with its held line (R-FW-P3-1: MS1-L, E1 risers)"]
    assert closable == pytest.approx(36.447, abs=1e-6)
    assert c["r5 drawn faces CALCULATED"] == pytest.approx(32.822036, abs=1e-6)
    parts = (c["inside another member: no surface"], c["under a member whose own rows hold it (one face once)"],
             c["readings the concrete ledger retired"],
             c["HELD piece of a closable line (column exposures D-16, unmarked layer-5 pairs)"], c["r4 print rounding"])
    assert parts == pytest.approx((0.783422, 1.914913, 0.203246, 0.72295, 0.000433), abs=1e-6)
    assert closable - c["r5 drawn faces CALCULATED"] == pytest.approx(sum(parts), abs=1e-6) == pytest.approx(3.624964)


def test_band0049_ruled_from_the_drawing(built):
    _, _, out, s, walk = built
    assert walk["band_cover_of_face"] >= 0.95 and walk["other_bands_on_face"] == {}
    assert walk["unchanged_records"] == 781 and walk["merged_records"] == 785
    b = [r for r in out if r["r5_line"] == M.BAND0049_LINE and r["method"] == "G"]
    calc = sum(r["r5_m2"] for r in b if r["r5_status"] == R.CALC)
    assert calc == pytest.approx(0.376924 + 2.224174 + 0.326718, abs=1e-6)
    held = [r for r in b if r["r5_status"] == R.HELD]
    assert len(held) == 1 and held[0]["r5_hi"] == pytest.approx(0.118) and held[0]["r5_m2"] is None
    # first principles: quarter annulus R 1.300 / 1.100 (arcs 29F / 2A0), B7 D 0.75, slab 0.16
    import math
    assert 0.376924 == pytest.approx(math.pi / 4 * (1.3 ** 2 - 1.1 ** 2), abs=1e-4)
    assert 2.224174 == pytest.approx(math.pi / 2 * (1.3 + 1.1) * (0.75 - 0.16), abs=2e-4)
    assert 0.326718 == pytest.approx(math.pi / 2 * 1.3 * 0.16, abs=1e-4)
    d = {r["face_id"]: r for r in out}
    assert d["R4-275.GF-095.UNMATCHED_PLAN"]["r5_status"] == R.REMOVED
    assert d["R4-268.GF-093.JOINT_HELD_M2"]["r5_status"] == R.REMOVED


def test_tank_row_is_b15(built):
    d = {r["face_id"]: r for r in built[2]}
    assert d["R4-341"]["r5_status"] == R.REMOVED and d["R4-341"]["rule"] == "R-T308-4"
    b15 = [r for r in built[2] if r["r5_line"] == "L-713bc64aaa210610e7fe" and r["r5_status"] == R.CALC]
    assert sum(r["r5_m2"] for r in b15 if r["method"] == "E") == pytest.approx(0.540 + 5.616)


def test_hold_with_line_and_boundary(built):
    _, _, out, s, _ = built
    held = [r for r in out if r["rule"] == "R-T308-5"]
    assert len(held) == 26 and sum(r["r5_held_from"] for r in held) == pytest.approx(3.257371, abs=1e-6)
    bg = [r for r in out if r["r5_line"] == M.BOUNDARY_LINE]
    assert len(bg) == 11 and all(r["r5_status"] == R.HELD and r["r5_m2"] is None for r in bg)
    assert sum(r["r5_held_from"] or 0 for r in bg) == pytest.approx(35.256)
    assert all(r["r5_status"] != R.HELD or r["r5_m2"] is None for r in out)


def test_no_line_changed_and_states(built):
    states = built[0]
    assert states[M.BOUNDARY_LINE][0] == "BLOCKED_RFI"
    assert M.boundary_line_check() == M.BOUNDARY_LINE
    assert states[M.BAND0049_LINE][0] == "PROVISIONAL"


def test_committed_outputs_are_a_fresh_build(built, tmp_path):
    states, rows, out, s, walk = built
    M.write(states, rows, out, None, walk, outdir=tmp_path)
    for name in M.OUTPUTS:
        assert (tmp_path / name).read_bytes() == (HERE / name).read_bytes(), name


def test_no_coordinates_in_outputs():
    w = json.loads((HERE / "T308_WALK_DELTA_BAND0049.json").read_text())
    assert "wkt" not in json.dumps(w) and "pts" not in w
    for name in M.OUTPUTS:
        assert "POLYGON" not in (HERE / name).read_text()
