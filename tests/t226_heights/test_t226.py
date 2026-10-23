"""T-226: block-wall height pieces (UP-MAS-HPIECE-001), D-12 m3 ranges (UP-MAS-D12-001), column-cut audit
(UP-MAS-COLCUT-001), and the development-villa register delta.

Fixture villa T226-F (NOT Alsenan), hand truth: storey 3.60 m (slab top to slab top).
  P1  beam X1, schedule depth 0.60, drawn width 0.30 vs printed 0.25 (width CONFLICT): h = 3.60 - 0.60 = 3.00 m
  P2  unlabelled span past a column, neighbours X1 0.60 / X2 0.40, 2.00 m long: HELD, bound 2 x 3.00 .. 2 x 3.20 =
      6.000 .. 6.400 m2, no height
  P3  'X3' and 'X4 (with stair)' on one span, depths 0.75 / 0.40, 1.50 m: HELD, CONFLICT 1.5 x 2.85 .. 1.5 x 3.20 =
      4.275 .. 4.800 m2
  P4  open void over the wall: HELD (never a default height, never 0)
  P5  only an architectural section that hatches the beam with the wall: refused as a depth source -> HELD
  P6  schedule 0.60 vs structural section 0.50: CONFLICT range, HELD
  D-12: net 10.000 m2, drawn 0.20 vs column 0.25: m3 2.000 .. 2.500, never chosen; black 0.25 has no product.
  Column cut: centreline 5.00, 0.50 inside a column, run 4.50 -> cut once; run 5.00 -> the column counted as block.
"""
from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t226"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT))

import height_rules as H                     # noqa: E402
from engine.source import masonry_area_v1 as M  # noqa: E402


def piece(**k):
    base = {"length_m": 2.0, "kind": "BEAM", "marks": ["X1"], "depth_sources": [{"kind": "SCHEDULE", "depth_m": 0.60}]}
    base.update(k)
    return base


# ------------------------------------------------------------------------------------------------ fixture T226-F
def test_r4_width_conflict_does_not_hold_the_height():
    r = H.resolve_piece(piece(width_conflict=True), 3.60)
    assert r["rule"] == "R4" and r["status"] == H.DC
    assert r["height_m"] == pytest.approx(3.00, abs=1e-9)
    assert "width CONFLICT" in r["dependency"]          # carried, not forgotten


def test_r2_unlabelled_span_is_a_bound_never_a_value():
    r = H.resolve_piece(piece(marks=[], depth_sources=[], candidate_depths_m=[0.60, 0.40]), 3.60)
    assert r["status"] == H.HELD and r["height_m"] is None and r["rule"] == "R2"
    assert r["bounds_m"] == pytest.approx((6.000, 6.400))


def test_r3_two_marks_conflict_range():
    r = H.resolve_piece(piece(length_m=1.5, marks=["X3", "X4"], mark_depths_m={"X3": 0.75, "X4": 0.40},
                              depth_sources=[]), 3.60)
    assert r["status"] == H.HELD and r["rule"] == "R3" and r["height_m"] is None
    assert r["bounds_m"] == pytest.approx((4.275, 4.800))


def test_r1_nothing_drawn_above_is_held_never_default():
    r = H.resolve_piece(piece(kind="NONE", marks=[], depth_sources=[]), 3.60)
    assert r["status"] == H.HELD and r["height_m"] is None and r["bounds_m"] is None and r["rule"] == "R1"


def test_r6_architectural_section_without_outline_is_refused_as_a_source():
    r = H.resolve_piece(piece(depth_sources=[{"kind": "ARCH_SECTION_NO_OUTLINE", "depth_m": None}]), 3.60)
    assert r["status"] == H.HELD and r["rule"] == "R6"
    # and it never contradicts a printed depth either
    r2 = H.resolve_piece(piece(depth_sources=[{"kind": "SCHEDULE", "depth_m": 0.60},
                                              {"kind": "ARCH_SECTION_NO_OUTLINE", "depth_m": 0.20}]), 3.60)
    assert r2["rule"] == "R4" and r2["height_m"] == pytest.approx(3.00)


def test_r5_schedule_vs_section_conflict_is_not_picked():
    r = H.resolve_piece(piece(depth_sources=[{"kind": "SCHEDULE", "depth_m": 0.60},
                                             {"kind": "SECTION", "depth_m": 0.50}]), 3.60)
    assert r["status"] == H.HELD and r["rule"] == "R5" and r["height_m"] is None
    assert r["bounds_m"] == pytest.approx((2 * 3.00, 2 * 3.10))


def test_units_mm_depth_refused():
    with pytest.raises(ValueError):
        H.resolve_piece(piece(depth_sources=[{"kind": "SCHEDULE", "depth_m": 600}]), 3.60)
    with pytest.raises(ValueError):
        H.resolve_piece(piece(depth_sources=[{"kind": "SCHEDULE", "depth_m": 0.60}]), 3600)


def test_missing_storey_is_held_not_zero():
    r = H.resolve_piece(piece(), None)
    assert r["status"] == H.HELD and r["height_m"] is None


def test_mirror_and_rotation_invariant_gross():
    """A wall of P1 (2.0 m, h 3.00) + slab piece (1.0 m, 0.16 slab -> 3.44): gross is the same with the pieces in
    mirrored order (a rotated / mirrored plan lists them the other way round)."""
    st = {"floor_to_floor_m": 3.60, "status": M.DC}
    p1 = {"length_m": 2.0, "member": {"kind": "BEAM", "mark": "X1", "depth_m": 0.60, "status": M.DC}}
    p2 = {"length_m": 1.0, "member": {"kind": "SLAB", "mark": "S", "depth_m": 0.16, "status": M.DC}}
    w = {"id": "F1", "t_m": 0.15, "physical_length_m": 3.0, "length_status": M.DC}
    g1 = M.wall_gross({**w, "pieces": [p1, p2]}, st)
    g2 = M.wall_gross({**w, "pieces": [p2, p1]}, st)
    assert g1["gross_m2"] == pytest.approx(2.0 * 3.00 + 1.0 * 3.44) == g2["gross_m2"]


def test_r7_merged_beam_column_face_is_split_by_the_column_below():
    assert H.split_face(True, True, "X1") == "COLUMN"           # inside the column below: concrete, no block
    assert H.split_face(False, True, "X1") == "BEAM"            # beside a narrower column, under the band
    assert H.split_face(False, True, None) == "BEAM_UNLABELLED"  # adverse: band without a mark stays R2
    assert H.split_face(False, False) == "NONE"


def test_alsenan_gf_w07_end_under_cb1():
    """GF-W07 east end: 0.98 m under B1 (h 4.10) + 0.12 m under CB1 H 75 (h 3.75), scaled to the 1.10 m run."""
    d = {r["wall_id"]: r for r in _csv(HERE / "register_delta.csv")}
    hw = (0.98 * 4.10 + 0.12 * 3.75) / 1.10
    assert float(d["GF-W07"]["gross_m2"]) == pytest.approx(1.10 * hw, abs=0.0015)
    assert float(d["GF-W07"]["net_m2"]) == pytest.approx(1.10 * hw, abs=0.0015)     # no opening in the run


# ------------------------------------------------------------------------------------------------ D-12
def test_d12_range_never_chosen_and_product_flag():
    r = H.d12_range(10.0, 0.20, 0.25, "BLACK")
    assert r["status"] == "CONFLICT" and r["m3_drawn"] == pytest.approx(2.0) and r["m3_note"] == pytest.approx(2.5)
    assert "NO_STANDARD_PRODUCT" in r["flags"]
    assert H.d12_range(10.0, 0.20, 0.25, "WHITE")["flags"] == []
    h = H.d12_range(None, 0.20, 0.25, "BLACK")
    assert h["status"] == H.HELD and h["m3_drawn"] is None and h["m3_note"] is None
    assert H.d12_range(10.0, 0.25, 0.25, "WHITE")["status"] == "NO_CONFLICT"


# ------------------------------------------------------------------------------------------------ column cut
def test_column_cut_once_and_adverse_column_as_block():
    assert H.column_cut(5.0, 0.5, 4.5, ["T_STEM", "FREE_END"])[0] == "COLUMN_CUT_ONCE"
    assert H.column_cut(5.0, 0.5, 4.6, ["L", "FREE_END"], (0.1,))[0] == "COLUMN_CUT_ONCE"   # L corner square
    assert H.column_cut(5.0, 0.5, 5.0, ["FREE_END", "FREE_END"])[0] == "COLUMN_COUNTED_AS_BLOCK"
    assert H.column_cut(5.0, 0.0, 5.0, ["FREE_END", "FREE_END"])[0] == "NO_COLUMN"


# ------------------------------------------------------------------------------------------------ development villa
def _csv(p):
    return list(csv.DictReader(Path(p).open(encoding="utf-8")))


def test_alsenan_outputs_reproduce():
    r = subprocess.run([sys.executable, "-I", str(HERE / "alsenan_t226.py"), "--check"], capture_output=True, text=True)
    assert "CHECK PASS" in r.stdout, r.stdout + r.stderr


def test_alsenan_pipeline_and_register_unchanged_baseline():
    s = json.loads((HERE / "summary.json").read_text(encoding="utf-8"))
    assert s["pipeline_reproduces_T108_BY_WALL"] is True and s["builder_reproduces_register_v1"] is True
    assert s["verified_by_checker"] == 0


def test_alsenan_delta_only_r4_walls_and_held_stay_held():
    d = {r["wall_id"]: r for r in _csv(HERE / "register_delta.csv")}
    assert set(d) == {"GF-W07", "GF-W10", "1F-W05", "1F-W11", "1F-W16"}
    pr = _csv(HERE / "PIECE_RESOLUTION.csv")
    closed = {r["wall_id"] for r in pr if r["rule"] == "R4"}
    assert set(d) == closed
    for r in pr:
        if r["rule"] != "R4":
            assert r["status"] == "HELD" and r["height_m"] == ""       # never a default height
    v1 = {r["wall_id"]: r for r in _csv(ROOT / "research/agents_t225/BLOCKWORK_WALL_REGISTER_V1.csv")}
    for w in ("GF-W03", "GF-W36", "1F-W04", "2F-W02", "2F-W03", "2F-W05", "2F-W07"):
        assert w not in d and v1[w]["gross_class"] == "HELD"
    # 1F-W05: hand check 5.98 m x 3.70 + 0.22 m x 3.45 over 6.20 sampled, scaled to 6.30 m; less W14 3.920
    w5 = d["1F-W05"]
    hw = (5.98 * 3.70 + 0.22 * 3.45) / 6.20
    assert float(w5["gross_m2"]) == pytest.approx(6.30 * hw, abs=0.0015)
    assert float(w5["net_m2"]) == pytest.approx(6.30 * hw - 3.920, abs=0.0015)
    # a wall still HELD on an opening carries no net figure
    for w in ("GF-W10", "1F-W11", "1F-W16"):
        assert d[w]["net_m2"] == "" and d[w]["net_class"] == "HELD"


def test_alsenan_established_net_rises_only_by_the_delta_nets():
    s = json.loads((HERE / "summary.json").read_text(encoding="utf-8"))
    d = _csv(HERE / "register_delta.csv")
    rise = sum(float(r["net_m2"]) for r in d if r["net_m2"])
    n = s["net_established_m2"]["DRAWING-CONFIRMED"]
    assert n["after"] - n["before"] == pytest.approx(rise, abs=0.002)
    assert s["gap_after"]["gap"] == pytest.approx(s["gap_after"]["reconstructed"], abs=0.002)


def test_alsenan_column_audit_no_column_counted_as_block():
    cut = _csv(HERE / "COLUMN_CUT_AUDIT.csv")
    assert cut and not [r for r in cut if r["status"] == "COLUMN_COUNTED_AS_BLOCK"]
    for r in cut:
        if r["status"] == "UNEXPLAINED":                     # named in the report, below the 0.05 m census limit
            assert abs(float(r["residual_m"])) < float(r["in_columns_m"]) and abs(float(r["residual_m"]) - 0.075) < 0.01
    idt = {r["floor"]: r["status"] for r in _csv(HERE / "IDENTITY_BY_FLOOR.csv")}
    assert idt == {"GF": "PASS_WITH_LISTED_PIECES", "1F": "PASS", "2F": "PASS"}
