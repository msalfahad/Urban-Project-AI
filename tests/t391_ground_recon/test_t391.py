"""T-391: ground slab / ground-beam cause split. Villa V391 (hand fixture, not Alsenan): a 4.00 m x 3.30 m ground plan,
two ground beams GB1 / GB2 0.30 wide along the 4.00 m sides (printed 30 x 40, depth from the slab top), one slab panel
between their faces 4.00 x 2.70 = 10.800 m2 at T = 0.10 -> 1.080 m3, one footing 1.20 x 1.20 x 0.40 below the panel
0.28 m under the beam soffits (no shared volume). Beams 2 x 4.00 x 0.30 x 0.40 = 0.960 m3.
A plate over the whole plan 4.00 x 3.30 = 13.200 m2 x 0.10 = 1.320 m3 covers the two strips again: 2 x 4.00 x 0.30 x
0.10 = 0.240 m3 (C1: the beam owns its strip full depth)."""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t391"
sys.path.insert(0, str(HERE))
import t391_rules as R  # noqa: E402

T = 0.10


def _v391_pieces():
    return [{"id": "P1", "kind": "PANEL", "area_m2": 10.80, "owner": "GS-1"},
            {"id": "S1", "kind": "BEAM", "area_m2": 1.20, "owner": "GB1"},
            {"id": "S2", "kind": "BEAM", "area_m2": 1.20, "owner": "GB2"}]


# ---------------- normal cases (hand figures above)

def test_v391_partition_closes():
    tot = R.check_partition(_v391_pieces())
    assert tot == {"PANEL": 10.8, "BEAM": 2.4}
    assert R.slab_over_beam_overlap(10.80, 2.40, 13.20) == 0.0


def test_v391_slab_split_names_the_strip_double_count():
    sp = R.slab_cause_split(t_m=T, engine_valued_m3=1.080, other_m3=1.320, own_valued_m2=10.80,
                            engine_valued_m2=10.80, own_held_panels_m2=0.0, own_other_family_m2=0.0,
                            own_strips_m2=2.40, own_network_m2=13.20, other_area_m2=13.20)
    assert sp["residual_m3"] == -0.24
    assert sp["terms_m3"]["strips_under_other_plate"] == -0.24
    assert sp["closes"] and sp["remainder_m3"] == 0.0


def test_v391_beam_split_section_and_length():
    # other side: 0.30 x 0.60 over 8.60 m (his lengths run 0.30 into each end support): 1.548 m3
    runs = [{"id": "GB1", "state": "VALUED", "L_m": 4.0, "b_m": 0.3, "A_m2": 1.2, "D_m": 0.4, "value_m3": 0.48,
             "group": "interior 0.40"},
            {"id": "GB2", "state": "VALUED", "L_m": 4.0, "b_m": 0.3, "A_m2": 1.2, "D_m": 0.4, "value_m3": 0.48,
             "group": "interior 0.40"}]
    sp = R.beam_cause_split(runs=runs, other_b=0.3, other_d=0.6, other_length_m=8.6, drawn_bounds_m=(8.0, 9.2))
    assert sp["residual_m3"] == round(0.96 - 1.548, 6)
    assert sp["terms_m3"]["section_on_valued_runs"] == round(2 * 4.0 * 0.3 * (0.4 - 0.6), 6)   # -0.480
    assert sp["terms_m3"]["length_basis_untraced"] == round(-0.18 * 0.6, 6)                     # -0.108
    assert sp["closes"] and sp["length_inside_drawn_bounds"]


def test_v391_held_run_counts_his_part_only():
    runs = [{"id": "GB1", "state": "VALUED", "L_m": 4.0, "b_m": 0.3, "A_m2": 1.2, "D_m": 0.4, "value_m3": 0.48},
            {"id": "GB2", "state": "HELD", "L_m": 4.0, "b_m": 0.3, "value_m3": None}]
    sp = R.beam_cause_split(runs=runs, other_b=0.3, other_d=0.6, other_length_m=8.0)
    assert sp["terms_m3"]["held_runs"] == -0.72
    assert sp["closes"]


def test_held_cell_bound_excludes_shaft_and_strips():
    hb = R.bound_of_held_cell([{"kind": "PANEL", "area_m2": 10.8}, {"kind": "LIFT", "area_m2": 3.24},
                               {"kind": "BEAM", "area_m2": 1.2}], T)
    assert hb == {"slab_m2": 10.8, "not_slab_m2": 4.44, "high_m3": 1.08}


def test_rotation_and_mirror_do_not_change_the_split():
    # the split reads areas and lengths only: the same villa mirrored / rotated 90 degrees has the same pieces
    a = R.check_partition(_v391_pieces())
    b = R.check_partition(list(reversed(_v391_pieces())))
    assert a == b


# ---------------- adverse cases

def test_slab_not_deducted_over_a_beam_is_double():
    with pytest.raises(R.RefusedT391, match="DOUBLE"):
        R.slab_over_beam_overlap(13.20, 2.40, 13.20)


def test_piece_owned_twice_refused():
    p = _v391_pieces() + [{"id": "S1", "kind": "BEAM", "area_m2": 1.2, "owner": "GS-1"}]
    with pytest.raises(R.RefusedT391, match="twice"):
        R.check_partition(p)
    with pytest.raises(R.RefusedT391, match="DOUBLE"):
        R.check_partition([{"id": "S9", "kind": "BEAM", "area_m2": 1.2, "owners": ["GB1", "GS-1"]}])


def test_beam_depth_from_slab_top_twice_refused():
    assert R.beam_depth_basis("SLAB_TOP", slab_over_strip=False) == "SLAB_TOP"
    with pytest.raises(R.RefusedT391, match="twice"):
        R.beam_depth_basis("SLAB_TOP", slab_over_strip=True)
    with pytest.raises(R.RefusedT391, match="lost"):
        R.beam_depth_basis("SLAB_SOFFIT", slab_over_strip=False)


def test_held_never_zero():
    runs = [{"id": "GB2", "state": "HELD", "L_m": 4.0, "b_m": 0.3, "value_m3": 0.0}]
    with pytest.raises(R.RefusedT391, match="never 0"):
        R.beam_cause_split(runs=runs, other_b=0.3, other_d=0.6, other_length_m=4.0)
    runs = [{"id": "GB2", "state": "HELD", "L_m": 4.0, "b_m": 0.3, "value_m3": 0.36}]
    with pytest.raises(R.RefusedT391, match="carries a value"):
        R.beam_cause_split(runs=runs, other_b=0.3, other_d=0.6, other_length_m=4.0)


def test_missing_thickness_refused():
    with pytest.raises(R.RefusedT391, match="thickness"):
        R.bound_of_held_cell([{"kind": "PANEL", "area_m2": 1.0}], None)
    with pytest.raises(R.RefusedT391, match="thickness"):
        R.slab_cause_split(t_m=None, engine_valued_m3=1, other_m3=1, own_valued_m2=1, engine_valued_m2=1,
                           own_held_panels_m2=0, own_other_family_m2=0, own_strips_m2=0, own_network_m2=1,
                           other_area_m2=1)


def test_units_mm_input_does_not_close():
    # areas typed in mm2 (x 1e6) break the partition closure: refused, never silently scaled
    with pytest.raises(R.RefusedT391, match="does not close"):
        R.slab_cause_split(t_m=T, engine_valued_m3=1.08, other_m3=1.32, own_valued_m2=10.8e6, engine_valued_m2=10.8,
                           own_held_panels_m2=0, own_other_family_m2=0, own_strips_m2=2.4, own_network_m2=13.2,
                           other_area_m2=13.2)


def test_plate_below_network_cannot_name_strips():
    with pytest.raises(R.RefusedT391, match="not established"):
        R.slab_cause_split(t_m=T, engine_valued_m3=1.08, other_m3=1.20, own_valued_m2=10.8, engine_valued_m2=10.8,
                           own_held_panels_m2=0, own_other_family_m2=0, own_strips_m2=2.4, own_network_m2=13.2,
                           other_area_m2=12.0)


def test_value_not_plan_times_depth_refused():
    runs = [{"id": "GB1", "state": "VALUED", "L_m": 4.0, "b_m": 0.3, "A_m2": 1.2, "D_m": 0.4, "value_m3": 0.72}]
    with pytest.raises(R.RefusedT391, match="net plan x depth"):
        R.beam_cause_split(runs=runs, other_b=0.3, other_d=0.6, other_length_m=4.0)


# ---------------- Alsenan committed outputs (engine side only)

def test_alsenan_summary_engine_side_pinned():
    s = json.loads((HERE / "summary_t391.json").read_text(encoding="utf-8"))
    sl, bm = s["slab"], s["beams"]
    assert sl["engine_valued_m3"] == 17.240684 and bm["valued_m3"] == 27.625386      # = T-385 GS-SLAB / GB-MAIN
    assert sl["engine_held_bound_m3"] == 3.929788 and sl["held_cell_own"]["high_m3"] == 3.56054
    assert sl["own_panels_m2"] == 217.2315 and sl["own_strips_m2"] == 71.8821
    assert abs(sum(sl["cause_terms_m3"].values()) + sl["remainder_m3"] - sl["residual_m3"]) < 1e-6
    assert abs(sum(bm["cause_terms_m3"].values()) + bm["remainder_m3"] - bm["residual_m3"]) < 1e-6
    assert abs(sl["remainder_m3"]) <= R.TOL_M3 and abs(bm["remainder_m3"]) <= R.TOL_M3
    assert bm["held_lines"] == 20 and bm["lines"] == 58
    assert bm["length_inside_drawn_bounds"] is True


def test_no_freelancer_row_values_committed():
    s = (HERE / "summary_t391.json").read_text(encoding="utf-8")
    assert "freelancer" not in json.loads(s)
    assert not (HERE / "T391_PRIVATE.json").exists()


def test_own_read_every_face_once():
    o = json.loads((HERE / "OWN_GROUND_T391.json").read_text(encoding="utf-8"))
    ids = [f["face"] for f in o["faces"]]
    assert len(ids) == len(set(ids)) == 180
    bound = [k for b in o["engine_binding"] for k in b["own_faces"]]
    assert len(bound) == len(set(bound))                                          # no own face in two engine cells
    assert not any(isinstance(v, float) and abs(v) > 1e4 for f in o["faces"] for v in f.values())   # no coordinates
