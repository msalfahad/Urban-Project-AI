"""T-367 (R-T367-1): masonry joint mortar on a hand-calculated villa that is not the development villa (villa M367).

Hand calculation (module 0.40 x 0.20, face 0.39 x 0.19, joints 10 / 10 mm, full bedding):
  per m2 = t (1 - 0.0741 / 0.08) = 0.07375 t  -> t 0.20: 0.01475, t 0.15: 0.0110625
  bed per m2 = 5 courses x 1 m x 0.010 x t = 0.05 t; head = 12.5 x 0.19 x 0.010 x t = 0.02375 t
  W1 BLACK 0.20 VERIFIED 10.000 m2 -> 0.147500 m3 (status ASSUMED — OWNER-APPROVED: module provisional)
  W2 BLACK 0.15 DRAWING-CONFIRMED 8.000 m2 -> 0.088500
  W3 BLACK 0.15 ASSUMED — OWNER-APPROVED 6.400 m2 (part, Q-55 door) -> 0.070800
  W4 WHITE 0.20 DRAWING-CONFIRMED 12.000 m2 -> adhesive HELD (no mortar)
  W5 BLACK 0.20 HELD -> blank by name
  total installed 0.306800 m3 on 24.400 m2 black
Lay-out check: 4.00 x 2.00 x 0.20 wall = 1.600 - 100 units x 0.39 x 0.19 x 0.20 (1.482) = 0.118 m3 = 8 x 0.01475.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t367"))

import masonry_mortar_v1 as M                                              # noqa: E402


def _villa():
    return [
        {"line_id": "L-M367-020", "floor": "GF", "t_m": 0.20, "walls": [
            {"wall_id": "W1", "block_type": "BLACK", "area_m2": 10.0, "area_status": "VERIFIED", "kind": "WHOLE"},
            {"wall_id": "W4", "block_type": "WHITE", "area_m2": 12.0, "area_status": "DRAWING-CONFIRMED",
             "kind": "WHOLE"},
            {"wall_id": "W5", "block_type": "BLACK", "area_m2": None, "area_status": "HELD", "kind": "HELD WALL"}]},
        {"line_id": "L-M367-015", "floor": "GF", "t_m": 0.15, "walls": [
            {"wall_id": "W2", "block_type": "BLACK", "area_m2": 8.0, "area_status": "DRAWING-CONFIRMED",
             "kind": "WHOLE"},
            {"wall_id": "W3", "block_type": "BLACK", "area_m2": 6.4, "area_status": "ASSUMED - OWNER-APPROVED",
             "kind": "ESTABLISHED_PART"}]},
    ]


def _rows():
    out = []
    for ln in _villa():
        out += M.line_rows(ln)
    return {r["wall_id"]: r for r in out}


# ---------------------------------------------------------------- normal
def test_per_m2_by_hand():
    for t, v, bed, head in ((0.20, 0.01475, 0.010, 0.00475), (0.15, 0.0110625, 0.0075, 0.0035625)):
        p = M.per_m2(M.MODULE_BLACK, t)
        assert p["total"] == pytest.approx(v, abs=1e-12)
        assert p["identity"] == pytest.approx(v, abs=1e-12)
        assert p["bed"] == pytest.approx(bed, abs=1e-12) and p["head"] == pytest.approx(head, abs=1e-12)
        assert p["units_per_m2"] == pytest.approx(12.5)


def test_villa_by_hand():
    r = _rows()
    assert r["W1"]["mortar_m3"] == pytest.approx(0.1475, abs=1e-9)
    assert r["W2"]["mortar_m3"] == pytest.approx(0.0885, abs=1e-9)
    assert r["W3"]["mortar_m3"] == pytest.approx(0.0708, abs=1e-9)
    assert sum(x["mortar_m3"] for x in r.values() if x["mortar_m3"] is not None) == pytest.approx(0.3068, abs=1e-9)
    assert M.close(list(r.values()), 24.4) == pytest.approx(24.4)


def test_status_is_weakest_with_the_provisional_module():
    r = _rows()
    for k in ("W1", "W2", "W3"):
        assert r[k]["mortar_status"] == M.AOA                     # never VERIFIED / DC while the module is provisional
    assert r["W1"]["area_status"] == "VERIFIED"                   # the area status is kept beside it


def test_white_adhesive_held_and_held_wall_blank():
    r = _rows()
    assert r["W4"]["mortar_m3"] is None and r["W4"]["adhesive"] == "HELD"
    assert r["W5"]["mortar_m3"] is None and r["W5"]["mortar_status"] == M.HELD


def test_layout_agrees_with_identity():
    assert M.laid_volume(4.0, 2.0, M.MODULE_BLACK, 0.20) == pytest.approx(0.118, abs=1e-9)
    # a non-modular wall: lay-out within one joint strip per edge of the identity
    L, H, t = 3.13, 2.77, 0.15
    ident = L * H * M.per_m2(M.MODULE_BLACK, t)["total"]
    assert abs(M.laid_volume(L, H, M.MODULE_BLACK, t) - ident) <= (L * 0.010 + H * 0.010) * t


def test_alternative_module_beside_never_merged():
    r = _rows()
    assert r["W1"]["alt_mortar_m3"] == pytest.approx(10 * 0.20 * (1 - 0.39 * 0.20 / (0.40 * 0.21)), abs=1e-9)
    assert r["W1"]["mortar_m3"] != r["W1"]["alt_mortar_m3"]


def test_cement_sand_from_a_named_masonry_mix_only():
    out = M.cement_sand(1.0, mix=(1, 6, "owner answer Q-xx: block laying mortar 1:6"),
                        waste=(0.0, "test: no waste"),
                        derivation={"dry_factor": 1.33, "cement_kg_m3": 1440, "bag_kg": 50, "source": "Q-53 C method"})
    assert out["cement_kg"] == pytest.approx(1.33 / 7 * 1440)
    assert out["sand_m3"] == pytest.approx(1.33 * 6 / 7)
    held = M.cement_sand(1.0)
    assert held["cement_bags"] is None and len(held["why"]) == 2


# ---------------------------------------------------------------- adverse
@pytest.mark.parametrize("src", ["finish_materials_table.py 1:4", "Q-45 B wall mortar behind tiles 1:4",
                                 "Q-53 C stair bed 1:3", "porcelain bed 1:4"])
def test_finish_mix_borrowed_refused(src):
    with pytest.raises(ValueError):
        M.cement_sand(1.0, mix=(1, 4, src))


def test_mix_without_masonry_source_refused():
    with pytest.raises(ValueError):
        M.cement_sand(1.0, mix=(1, 4, "practice value"))


def test_aac_as_10mm_mortar_refused():
    with pytest.raises(ValueError):
        M.wall_row({"wall_id": "W4", "block_type": "WHITE", "area_m2": 12.0, "area_status": "DRAWING-CONFIRMED"},
                   0.20, joint_m=0.010)


def test_held_wall_as_zero_refused():
    with pytest.raises(ValueError):
        M.wall_row({"wall_id": "W5", "block_type": "BLACK", "area_m2": 0.0, "area_status": "HELD"}, 0.20)
    with pytest.raises(ValueError):
        M.wall_row({"wall_id": "W5", "block_type": "BLACK", "area_m2": 0.0, "area_status": "VERIFIED"}, 0.20)


def test_mm_thickness_refused():
    with pytest.raises(ValueError):
        M.per_m2(M.MODULE_BLACK, 150)
    with pytest.raises(ValueError):
        M.per_m2(dict(M.MODULE_BLACK, face_m=(390, 190)), 0.15)


def test_wall_twice_refused():
    ln = _villa()[1]
    ln["walls"].append(dict(ln["walls"][0]))
    with pytest.raises(ValueError):
        M.line_rows(ln)
    rows = []
    for x in _villa():
        rows += M.line_rows(x)
    rows.append(dict(rows[0]))
    with pytest.raises(ValueError):
        M.close(rows, 24.4)


def test_closure_mismatch_refused():
    rows = []
    for x in _villa():
        rows += M.line_rows(x)
    with pytest.raises(ValueError):
        M.close(rows, 24.4 + 10.0)                               # a held wall counted as 10 m2 established


def test_unknown_type_and_status():
    r = M.wall_row({"wall_id": "H1", "block_type": None, "area_m2": None, "area_status": "HELD"}, 0.40)
    assert r["mortar_status"] == M.UNKNOWN and r["mortar_m3"] is None
    with pytest.raises(ValueError):
        M.wall_row({"wall_id": "X", "block_type": "BLACK", "area_m2": 1.0, "area_status": "PROVISIONAL"}, 0.20)


def test_waste_without_source_or_as_percent_refused():
    with pytest.raises(ValueError):
        M.cement_sand(1.0, waste=(0.05, ""))
    with pytest.raises(ValueError):
        M.cement_sand(1.0, waste=(5, "x"))
