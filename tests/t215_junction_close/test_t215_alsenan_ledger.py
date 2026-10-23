"""T-215 development-villa ledger (research/agents_t215/T215_ENDS.csv, T215_ROW_EFFECT.csv): internal consistency of
the committed result. The drawing itself is private and not in the repository; `alsenan_t215_ends.py --check`
reproduces both files byte for byte from it (run by the worker and the Checker outside the test session)."""
import csv
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "research" / "agents_t215"


def rows(name):
    return list(csv.DictReader(open(D / name, encoding="utf-8")))


def test_every_cluster_closes_and_deltas_add_to_its_residual():
    by = {}
    for r in rows("T215_ENDS.csv"):
        by.setdefault(r["cluster"], []).append(r)
    assert sorted(by) == ["J-A", "J-B", "J-C", "J-D"]
    for cid, rs in by.items():
        res = {r["cluster_residual_m2"] for r in rs}
        assert len(res) == 1, cid
        s = sum(float(r["delta_m"]) * float(r["t_m"]) for r in rs)
        assert s == pytest.approx(float(rs[0]["cluster_residual_m2"]), abs=2e-5), cid
        assert all(float(r["cluster_unassigned_m2"]) == 0.0 and r["status"] == "CLOSED" for r in rs), cid
        assert len({r["row_id"] for r in rs}) == len(rs), f"{cid}: a wall twice in one junction"


def test_junction_piece_g_t108_1_assigned_once():
    # the GF-W22 / GF-W34 piece: unmeasured 0.0232 m2 (about 0.15 m of 0.15 wall), shared once between the two walls
    a = [r for r in rows("T215_ENDS.csv") if r["cluster"] == "J-A"]
    res = float(a[0]["cluster_residual_m2"])
    assert 0.020 < res < 0.026
    assert sum(float(r["delta_m"]) for r in a) * 0.15 == pytest.approx(res, abs=2e-5)
    assert all(float(r["delta_m"]) > 0 for r in a)


def test_bend_moves_length_without_changing_the_total():
    b = {r["row_id"]: float(r["delta_m"]) for r in rows("T215_ENDS.csv") if r["cluster"] == "J-B"}
    assert b["GF-W21"] == pytest.approx(-b["GF-W33"], abs=1e-4)


def test_structural_plan_placed_by_one_translation():
    for r in rows("T215_ENDS.csv"):
        assert float(r["st_fit_residual_mm"]) <= 5.0


def test_column_end_closes_at_zero():
    d = {r["row_id"]: float(r["delta_m"]) for r in rows("T215_ENDS.csv") if r["cluster"] == "J-D"}
    assert d["GF-W13"] == 0.0


def test_row_effect_matches_the_ends_and_never_exceeds_the_old_bound():
    ends = {}
    for r in rows("T215_ENDS.csv"):
        ends[r["row_id"]] = ends.get(r["row_id"], 0.0) + float(r["delta_m"])
    for r in rows("T215_ROW_EFFECT.csv"):
        d = float(r["delta_m"])
        assert d == pytest.approx(ends[r["row_id"]], abs=1e-4)
        assert float(r["closed_length_m"]) == pytest.approx(float(r["t108_physical_m"]) + d, abs=1e-4)
        if r["t108_held_end_max_m"]:
            assert d <= float(r["t108_held_end_max_m"]) + 1e-9, r["row_id"]
        lo, hi = float(r["d_gross_m2_min"]), float(r["d_gross_m2_max"])
        assert lo <= hi
        # a range only from a named member conflict; otherwise one drawing-confirmed value
        assert r["m2_status"].startswith("DRAWING-CONFIRMED") == (abs(hi - lo) < 5e-5)
        if abs(hi - lo) >= 5e-5:
            assert "CONFLICT" in r["m2_status"]
        # never more wall than the storey height over the moved length (plus the counted-strip correction at a column)
        assert abs(hi) <= 4.50 * abs(d) + 0.01


def test_no_coordinates_or_client_text_in_the_ledger():
    for name in ("T215_ENDS.csv", "T215_ROW_EFFECT.csv"):
        txt = (D / name).read_text(encoding="utf-8")
        assert not re.search(r"-?\d{5,}\.\d", txt), name          # no drawing coordinates
