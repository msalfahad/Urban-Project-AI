"""T-616 R-T616-1 lintel residual by opening: a non-Alsenan fixture worked by hand (normal, mirrored order), the rule's
adverse cases, and the training-villa rebuild (byte-identical; merged inputs only, no private file)."""
from __future__ import annotations

import importlib.util
import json
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t616"
sys.path.insert(0, str(HERE))
import t616_rules as R  # noqa: E402


def _load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ------------------------------------------------------------------ fixture villa Z (not Alsenan), worked by hand
# internal 15 cm group: two 0.90 doors D1 / D2 (clear margin 1.00 / 0.40 m), arch A1 1.20 (no member over it), passage
# P1 0.80 under a full-width beam; external: curved window W1 (outer R 3.00, arc 2.00, wall 0.25, piece 0.25) that we
# carry without a lintel and that he deducts as 2.00. His deduction list: internal 0.90, 1.20; external 2.00.
OURS = [
    {"id": "D1", "storey": "GF", "group": "GF_INT", "width_m": 0.90, "counts": 1},
    {"id": "D2", "storey": "GF", "group": "GF_INT", "width_m": 0.90, "counts": 1},
    {"id": "A1", "storey": "GF", "group": "GF_INT", "width_m": 1.20, "counts": 1},
    {"id": "P1", "storey": "GF", "group": "GF_INT", "width_m": 0.80, "counts": 1},
    {"id": "W1", "storey": "GF", "group": "GF_EXT", "width_m": 2.00, "counts": 0},
]
THEIRS = [{"group": "GF_INT", "widths": [0.90, 1.20]}, {"group": "GF_EXT", "widths": [2.00]}]
KEYS = {"W1": ("GF_EXT", 2.00)}
REQ_IN = {
    "D1": {"id": "D1", "host": "MASONRY", "head": "DOOR_FRAME", "beam_over": "UNKNOWN", "clear_margin_m": 1.00},
    "D2": {"id": "D2", "host": "MASONRY", "head": "DOOR_FRAME", "beam_over": "FULL_WIDTH", "clear_margin_m": 0.40},
    "A1": {"id": "A1", "host": "MASONRY", "head": "ARCH_DRAWN", "beam_over": "NONE"},
    "P1": {"id": "P1", "host": "MASONRY", "head": "HEADER_LINES", "beam_over": "FULL_WIDTH"},
    "W1": {"id": "W1", "host": "MASONRY", "head": "ARCH_DRAWN", "beam_over": "UNKNOWN",
           "curved": {"r_out_m": 3.00, "arc_m": 2.00, "wall_t_m": 0.25, "piece_w_m": 0.25}},
}


def _req():
    return {k: R.requirement(v) for k, v in REQ_IN.items()}


def test_requirement_by_hand():
    r = _req()
    assert r["D1"]["decision"] == R.REQUIRED            # door frame, 1.00 m to spare
    assert r["D2"]["decision"] == R.REQUIRED            # a beam over it does not matter: the head is 0.40 m below
    assert r["A1"]["decision"] == R.REQUIRED            # arch bounds the head, masonry both sides, no member
    assert (r["P1"]["decision"], r["P1"]["lo"], r["P1"]["hi"]) == (R.UNRESOLVED, 0, 1)
    assert r["W1"]["decision"] == R.NO_STRAIGHT_PIECE
    # sagitta by hand: theta = (2.00 + 2 x 0.15) / 3.00 = 0.766667; 3.00 x (1 - cos 0.383333) = 0.21774
    assert math.isclose(r["W1"]["sagitta_m"], 0.2177, abs_tol=1e-4)


def test_closure_by_hand():
    c = R.close_residual(OURS, THEIRS, KEYS)
    assert (c["ours_nr"], c["theirs_nr"], c["difference_nr"], c["closure_nr"]) == (4, 3, 1, 1)
    g = {x["group"]: x for x in c["groups"]}
    # 0.90: one of D1 / D2 pairs his 0.90; A1 pairs his 1.20; P1 has no row of his
    assert g["GF_INT"]["ours_only_k"] == 2
    assert g["GF_INT"]["ours_only_firm"] == ["P1"]
    assert g["GF_INT"]["ours_only_possible"] == ["D1", "D2"]
    assert g["GF_INT"]["admissible_sets"] == [["D1", "P1"], ["D2", "P1"]]
    assert g["GF_EXT"]["paired_no_lintel_ours"] == [{"ours": "W1", "theirs_w": 2.00}]
    assert (g["GF_INT"]["nr"], g["GF_EXT"]["nr"]) == (2, -1)
    v = {x["group"]: x for x in R.verdicts(c, _req(), drawn={"D1", "D2", "A1", "P1"})}
    assert v["GF_INT"]["engine_right_nr"] == [1, 1] and v["GF_INT"]["unresolved_nr"] == [1, 1]
    assert v["GF_INT"]["at_most_verdict"] == R.ENGINE_RIGHT
    assert v["GF_EXT"]["their_piece_on_no_lintel"][0]["verdict"] == R.ENGINE_RIGHT


def test_mirrored_order_invariance():
    a = R.close_residual(OURS, THEIRS, KEYS)
    b = R.close_residual(list(reversed(OURS)), [{"group": g["group"], "widths": list(reversed(g["widths"]))}
                                                for g in reversed(THEIRS)], KEYS)
    key = lambda c: sorted((g["group"], g["nr"], tuple(g["ours_only_firm"]), tuple(g["ours_only_possible"]))
                           for g in c["groups"])
    assert key(a) == key(b)


def test_nearest_width_tie_branches_never_chooses():
    ours = [{"id": i, "storey": "1F", "group": "G", "width_m": w, "counts": 1}
            for i, w in (("a", 0.80), ("b", 1.00), ("c", 1.00))]
    c = R.close_residual(ours, [{"group": "G", "widths": [0.90]}])
    g = c["groups"][0]
    assert g["ours_only_k"] == 2 and g["ours_only_firm"] == [] and g["ours_only_possible"] == ["a", "b", "c"]


def test_gentle_curve_admits_a_straight_piece():
    r = R.requirement({"id": "X", "host": "MASONRY", "head": "ARCH_DRAWN", "beam_over": "NONE",
                       "curved": {"r_out_m": 50.0, "arc_m": 1.00, "wall_t_m": 0.25, "piece_w_m": 0.20}})
    assert r["decision"] == R.REQUIRED                  # sagitta 0.0042 m <= 0.05 m of the band


def test_stock_piece_owner_rule():
    assert [R.stock_piece(w) for w in (0.80, 0.90, 1.00, 1.30, 2.45, 3.70, 3.71)] == [1.20, 1.20, 1.50, 2.50, 3.00,
                                                                                     4.00, None]


# ------------------------------------------------------------------ adverse
def test_lintel_in_a_concrete_wall_refused():
    with pytest.raises(R.ResidualError, match="RC host is refused"):
        R.requirement({"id": "C1", "host": "RC", "head": "DOOR_FRAME", "beam_over": "NONE", "claimed_count": 1})
    assert R.requirement({"id": "C1", "host": "RC", "head": "DOOR_FRAME", "beam_over": "NONE"})["decision"] == \
        R.NOT_APPLICABLE


def test_straight_piece_claimed_in_a_curved_wall_refused():
    with pytest.raises(R.ResidualError, match="curved wall refused"):
        R.requirement({**REQ_IN["W1"], "claimed_count": 1})


def test_opening_counted_in_two_storeys_refused():
    bad = OURS + [{"id": "D1", "storey": "1F", "group": "1F_INT", "width_m": 0.90, "counts": 1}]
    with pytest.raises(R.ResidualError, match="two storeys"):
        R.close_residual(bad, THEIRS, KEYS)
    with pytest.raises(R.ResidualError, match="listed twice"):
        R.close_residual(OURS + [dict(OURS[0])], THEIRS, KEYS)


def test_ours_only_opening_that_takes_no_lintel_refused():
    req = _req()
    req["P1"] = R.requirement({"id": "P1", "host": "GLAZING", "head": "NONE", "beam_over": "NONE"})
    with pytest.raises(R.ResidualError, match="take no lintel"):
        R.verdicts(R.close_residual(OURS, THEIRS, KEYS), req)


def test_held_is_never_zero_and_units_refused():
    with pytest.raises(R.ResidualError, match="not positive"):
        R.close_residual([{"id": "Z", "storey": "GF", "group": "G", "width_m": 0, "counts": 1}], [])
    with pytest.raises(R.ResidualError, match="mm / cm"):
        R.close_residual([{"id": "Z", "storey": "GF", "group": "G", "width_m": 900, "counts": 1}], [])
    with pytest.raises(R.ResidualError, match="not a number"):
        R.close_residual([{"id": "Z", "storey": "GF", "group": "G", "width_m": None, "counts": 1}], [])
    r = R.requirement({"id": "U", "host": "UNKNOWN", "head": "DOOR_FRAME", "beam_over": "NONE", "clear_margin_m": 1.0})
    assert (r["decision"], r["hi"]) == (R.UNRESOLVED, 1)    # unknown host: 0 .. 1, never 0, margin not enough


def test_key_to_a_width_not_in_his_list_refused():
    with pytest.raises(R.ResidualError, match="not in their list"):
        R.close_residual(OURS, THEIRS, {"W1": ("GF_EXT", 2.50)})


def test_unknown_vocabulary_refused():
    with pytest.raises(R.ResidualError, match="unknown"):
        R.requirement({"id": "Q", "host": "STEEL", "head": "NONE", "beam_over": "NONE"})


# ------------------------------------------------------------------ training villa (merged records only)
def test_training_villa_rebuild_and_closure():
    A = _load("t616_alsenan")
    built = A.dump(A.build())
    assert A.OUT.read_text() == built                 # byte-identical
    d = json.loads(built)
    assert (d["ours_nr"], d["theirs_nr"], d["difference_nr"], d["closure_nr"]) == (60, 54, 6, 6)
    g = {x["group"]: x for x in d["groups"]}
    assert g["GF_EXT"]["ours_only_firm"] == ["D-GF-05"]
    assert g["GF_15"]["ours_only_firm"] == ["P-GF-01"] and g["GF_15"]["ours_only_possible"] == ["A-GF-01", "D-GF-13"]
    assert g["1F_15"]["ours_only_firm"] == ["P-1F-01"] and g["1F_15"]["ours_only_k"] == 4
    assert g["1F_EXT"]["paired_no_lintel_ours"] == [{"ours": "W17", "theirs_w": 3.15}]
    assert g["SHAFT_20"]["ours_only_k"] == 0         # his 3 x 1.00 + 1.10 = the three landing doors + D-GF-08
    assert "L-GF-01" not in d["ours_only_firm"] + d["ours_only_possible"]
    assert "L-GF-01" in d["t571_engine_only"]         # the T-571 attribution this row corrects
    assert d["requirement"]["W17"]["decision"] == "NO_STRAIGHT_PIECE"
    assert d["requirement"]["P-GF-01"]["decision"] == "UNRESOLVED"
    s = d["summary"]
    assert s["established_basis_ours_only_engine_right_nr"] == [3, 5]
    assert s["statement_sign_his_minus_ours"]["total"] == -6
    assert d["beside_t571_identity"]["closure_nr"] == 6
    assert sum(len(x["widths"]) for x in A.THEIRS) == 54
