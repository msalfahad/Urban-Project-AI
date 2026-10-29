"""T-335 Alsenan (development villa; not an accuracy claim): the T-295 ceiling face-to-line ledger bound to the
V3.0.21 candidate of record and cross-checked against its plaster / paint / tile lines. Rebuilds from committed inputs
without writing and pins the results."""
from __future__ import annotations

import csv
import io
import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t335"
sys.path.insert(0, str(HERE))
import t335_alsenan as A  # noqa: E402
import ceiling_cross_trade as X  # noqa: E402

B = A.build()
F = A.outputs(B)
S = json.loads(F["summary.json"])


def _rows(name):
    return list(csv.DictReader(io.StringIO(F[name])))


def test_committed_outputs_reproduce_byte_for_byte():
    for name, text in F.items():
        assert (HERE / name).read_text(encoding="utf-8") == text, name


def test_candidate_is_v3021_of_record_and_every_ceiling_line_same_as_t295():
    assert S["candidate"] == "ARCH_TAKEOFF_V3.0.21" and S["lines_total"] == 3706
    assert S["candidate_lines_json_sha256"].startswith("be22a4e4")
    assert S["candidate_lines_csv_sha256"].startswith("3548e39c")
    reb = _rows("LINE_REBIND_T335.csv")
    assert len(reb) == 36 and {r["verdict"] for r in reb} == {"SAME"}
    assert sorted(r["role"] for r in reb).count("EXTERIOR") == 5
    assert sorted(r["role"] for r in reb).count("STAIRWELL") == 2


def test_no_double_count_and_no_horizontal_face_in_a_wall_line():
    assert S["totals"]["double_count_m2"] == 0
    assert S["wall_lines_with_a_horizontal_term"] == 0
    X.validate(B["claims"], B["surfaces"], B["lines"])
    for r in _rows("CROSS_TRADE_T335.csv"):
        assert float(r["double_count_m2"]) == 0.0 and float(r["horizontal_in_wall_lines_m2"]) == 0.0, r["room_id"]
        assert float(r["gap_m2"]) == 0.0, r["room_id"]
        # every live wall line stops at the decor underside of its floor (Q-48 A) or is HELD at the annex 3.15
        for t in r["wall_tops_m"].split():
            assert float(t) in (float(r["decor_underside_m"]), 3.15), (r["room_id"], t)


def test_totals_and_band_held_not_in_any_line():
    t = S["totals"]
    assert t["decor_dc_m2"] == pytest.approx(362.006092, abs=1e-6)
    assert t["bulkhead_aoa_m2"] == pytest.approx(27.9345, abs=1e-6)
    assert t["engine_interior_ceiling_m2"] == pytest.approx(403.162928, abs=1e-6)
    assert t["wall_band_held_hi_m2"] == pytest.approx(53.8506, abs=1e-4)


def test_fill_table_for_t284():
    fill = _rows("FILL_T284_T335.csv")
    assert len(fill) == 36                                    # 36 lines = 35 keys (one group of two) + the new dressing line
    new = [r for r in fill if r["line_key"] == "NEW LINE NEEDED"]
    assert len(new) == 1 and float(new[0]["decor_dc_m2"]) == pytest.approx(2.970)
    blocked = [r for r in fill if r["v3021_state"] == "BLOCKED_RFI"]
    assert len(blocked) == 2 and all(r["before_m2"] == "" for r in blocked)    # BLANK, never 0
    grp = [r for r in fill if " + " in r["line_key"]]
    assert len(grp) == 1 and grp[0]["action"].startswith("LINE GROUP")
    ext = [r for r in fill if r["role"] == "EXTERIOR"]
    assert len(ext) == 5 and all(r["decor_dc_m2"] == "" for r in ext)
    gf = next(r for r in fill if r["line_key"] == "L-eb3be58fc760b39f0e38")
    assert float(gf["before_m2"]) == pytest.approx(110.922696) and float(gf["decor_dc_m2"]) == pytest.approx(101.137092)
    assert float(gf["bulkhead_aoa_m2"]) == pytest.approx(11.9189)
    for r in fill:
        assert "0.000000 (" not in r["held_blank"]


def test_freelancer_cells_compared_never_proof():
    fr = {r["freelancer_row"][:3]: r for r in _rows("FREELANCER_T335.csv")}
    assert float(fr["D21"]["diff_m2"]) == pytest.approx(12.0896, abs=1e-4)
    assert "dome" in fr["D22"]["held_in_pieces"]
    assert float(fr["D16"]["diff_m2"]) == pytest.approx(0.1003, abs=1e-4)


def test_no_coordinates_or_names_committed():
    blob = (HERE / "CANDIDATE_V3021_T335.json").read_text(encoding="utf-8")
    assert "room_name" not in blob and not re.search(r'"(x|y)"\s*:', blob)
    assert not re.search(r"[؀-ۿ]", blob + "".join(F.values()))
