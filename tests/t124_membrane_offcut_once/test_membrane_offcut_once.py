"""T-124: MEMBRANE_FOLD_V5 - owner Q-58 A roll counts with every leftover booked once, the audit of MEMBRANE_FOLD_V3 / V4
Q-58 A counts, and the ledger kept apart (installed, upturn, gross cut, laps, trims, offcut left, rolls).
Synthetic, hand-calculated cases only (none is the development villa). Roll 1.00 x 10.00 m, lap 0.10 m, upturn 0.20 m
(UP-WP-001 / 002 / 003).

D1 (pieces only, no geometry): one main strip 1.00 x 7.00 m (end 3.00 m) and four patch pieces 1.00 x 1.00 m.
    V3: three patches promised to the 3.00 m end of the main-only packing, the fourth packed with the main strip:
    7.00 + 1.00 = 8.00 m -> 1 roll. On that one roll the end is 2.00 m and the three promised pieces need 3.00 m: the
    end is booked twice -> INVALID. By hand: 7.00 + 4 x 1.00 = 11.00 m2 of full-width pieces > one 10.00 m2 roll ->
    2 rolls (roll 1: 7.00 + 3 x 1.00; roll 2: 1.00, 9.00 m left).
D2 (pieces only): main 1.00 x 6.00 m (end 1.00 x 4.00 m); patch 0.60 x 1.50 (0.90 m2) and upturn piece 0.30 x 2.50
    (0.75 m2). Largest first: the patch at x 6.00 - 7.50, y 0 - 0.60; the end shrinks to 1.00 x 2.50 (x 7.50 - 10.00)
    and the 0.40 x 1.50 strip beside the patch; the upturn piece in the 1.00 x 2.50 rest (x 7.50 - 10.00, y 0 - 0.30).
    1 roll; left 0.70 x 2.50 + 0.40 x 1.50 = 1.75 + 0.60 = 2.35 m2 = 10.00 - 6.00 - 0.90 - 0.75.
D3: a patch 0.40 x 12.00 m is longer than a roll: no plan; the layout's A / B counts are held, never one roll.
X (T-120): 11.00 x 5.50 less 1.00 x 3.00, V3 layout ALONG / LOWER: V3 claims 8 under Q-58 A with four 1.00 x 1.00 patch
    pieces (V3 cuts every patch piece 1.00 wide: across 3.10 m -> 4 pieces). V3's own 8 rolls (main 76.50 m + one
    1.00 m piece) leave 2.50 m of roll end and 0.50 m trims: three 1.00 wide pieces need 3.00 m -> INVALID; the same
    pieces booked once -> 9 rolls (76.50 + 4.00 = 80.50 m of full-width length > 80). V5's own pieces cut the last patch
    piece only 3.10 - 3 x 1.00 = 0.10 m wide, which fits the 0.50 m trim of the 0.50 m strip: 8 rolls, a real plan.
R (T-120): 10.00 x 6.00 less 7.50 x 3.15; ACROSS / OPPOSITE: mains 3 x 6.40 + 9 x 3.25 = 48.45 m in 5 rolls; the
    0.20 x 3.25 upturn piece in the 0.50 x 3.25 trim of the 0.50 m strip -> A 5 (VALID), B 6, C 6. Ledger: floor
    60.00 - 23.625 = 36.375 m2; installed = floor + 0.20 x perimeter 32.00 + 0.04 x (5 convex - 1 reflex corner) =
    36.375 + 6.40 + 0.16 = 42.935 m2 (upturn 6.56); gross cut 11 x 1.00 + 1 x 0.50 wide: 3 x 6.40 + 8 x 3.25 + 0.5 x
    3.25 + 0.20 x 3.25 = 47.475 m2; laps: side laps 2 x 0.64 + 9 x 0.325 = 4.205 + upturn piece 0.65 - its residual
    0.315 = 0.335 -> 4.54 m2; trim 0; offcut left 50.00 - 47.475 = 2.525 m2."""

from __future__ import annotations

import copy
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v213 as AV                     # noqa: E402
from engine.source import membrane_fold_v3 as F3              # noqa: E402
from engine.source import membrane_fold_v4 as F4              # noqa: E402
from engine.source import membrane_fold_v5 as F5              # noqa: E402

SPEC = dict(F5.DEFAULT)
ROOF_R = [(0, 0), (10, 0), (10, 6), (7.5, 6), (7.5, 2.85), (0, 2.85)]
ROOF_X = [(0, 0), (11, 0), (11, 5.5), (1, 5.5), (1, 2.5), (0, 2.5)]


def _xf(pts, *, scale=1.0, mirror=False, deg=0.0):
    a = math.radians(deg)
    out = []
    for x, y in pts:
        if mirror:
            x = -x
        out.append(((x * math.cos(a) - y * math.sin(a)) * scale, (x * math.sin(a) + y * math.cos(a)) * scale))
    return out


def _lay(main, patches=(), upturn=()):
    """a layout as MEMBRANE_FOLD_V3 hands it on (strips, patches) with V3's own Q-58 counts."""
    m = [{"kind": "MAIN", "width_m": w, "length_m": l, "piece_lengths_m": [l]} for w, l in main]
    u = [{"kind": F3.UPTURN_STRIP, "width_m": 1.0, "length_m": l, "piece_lengths_m": [l], "need_width_m": w}
         for w, l in upturn]
    p = [{"kind": F3.PATCH_OUTLINE, "along_m": l, "across_m": w, "m2": w * l} for w, l in patches]
    lay = {"strips": m + u, "patches": p, "main": m, "added": u}
    lay["counts"] = F3.counts(lay, SPEC)
    return lay


# ------------------------------------------------------------------------------------------------ booking once
def test_d1_v3_books_one_roll_end_twice_and_v5_needs_two_rolls():
    lay = _lay([(1.0, 7.0)], patches=[(1.0, 1.0)] * 4)
    c = lay["counts"]["Q58_A"]
    assert c["rolls"] == 1 and len(c["pieces_from_own_offcuts"]) == 3 and len(c["pieces_from_rolls"]) == 1
    au = F5.audit_v3(lay, SPEC)
    assert au["verdict"] == F5.INVALID and au["claimed"] == 1
    assert au["final_roll_ends_m"] == [2.0]
    assert any(w.startswith("ROLL_ENDS_TOO_SHORT") for w in au["why"])
    assert any(w.startswith("AREA") for w in au["why"])     # 3.00 m2 of promised pieces > the 2.00 m2 roll end
    assert au["corrected"] == 2 and au["v5_rolls"] == 2
    a = F5.plan_q58_a(lay, SPEC)
    assert a["rolls"] == 2 and a["check"] == "PASSED" and a["lower_bound"] == 2
    assert a["offcut_left_m2"] == pytest.approx(20.0 - 11.0)
    assert sorted(r["left_m"] for r in a["plan"]) in ([0.0, 9.0], [1.0, 8.0], [2.0, 7.0], [3.0, 6.0])


def test_d1_narrow_pieces_two_side_by_side_are_not_called_invalid():
    """two 0.45 m pieces can lie side by side in one roll end: the end-length test must not speak for them."""
    lay = _lay([(1.0, 8.0)], patches=[(0.45, 2.0)] * 2)
    au = F5.audit_v3(lay, SPEC)
    assert not any(w.startswith("ROLL_ENDS_TOO_SHORT") for w in au["why"])
    a = F5.plan_q58_a(lay, SPEC)                    # by hand: end 1.00 x 2.00 takes both (y 0 - 0.45, 0.45 - 0.90)
    assert a["rolls"] == 1 and len(a["pieces_from_own_offcuts"]) == 2
    ys = sorted((q["y0"], q["y1"]) for q in a["pieces_from_own_offcuts"])
    assert ys == [(0.0, 0.45), (0.45, 0.9)]


def test_d2_one_leftover_takes_two_pieces_in_sequence_and_shrinks():
    lay = _lay([(1.0, 6.0)], patches=[(0.6, 1.5)], upturn=[(0.3, 2.5)])
    a = F5.plan_q58_a(lay, SPEC)
    assert a["rolls"] == 1 and a["rounds"] == 1
    own = {q["what"]: q for q in a["pieces_from_own_offcuts"]}
    p, u = own[F3.PATCH_OUTLINE], own[F3.UPTURN_STRIP]
    assert (p["x0"], p["x1"], p["y0"], p["y1"]) == (6.0, 7.5, 0.0, 0.6)
    assert (u["x0"], u["x1"], u["y0"], u["y1"]) == (7.5, 10.0, 0.0, 0.3)
    assert u["offcut_w"] == 1.0 and u["offcut_l"] == 2.5                # the end after the patch, smaller
    left = sorted((o["width_m"], o["length_m"]) for o in a["offcuts_left"])
    assert left == [(0.4, 1.5), (0.7, 2.5)]
    assert a["offcut_left_m2"] == pytest.approx(2.35)
    assert F5.audit_v3(lay, SPEC)["verdict"] == F5.VALID


def test_d3_piece_longer_than_a_roll_is_held_never_one_roll():
    lay = _lay([(1.0, 5.0)], patches=[(0.4, 12.0)])
    with pytest.raises(F5.PieceTooLarge):
        F5.plan_q58_a(lay, SPEC)
    au = F5.audit_v3(lay, SPEC)
    assert au["verdict"] == F5.INVALID and au["corrected"] is None
    assert any(w.startswith("PIECE_LARGER_THAN_ROLL") for w in au["why"])


def test_check_plan_catches_overlap_and_outside():
    rolls = [{"roll": 1, "pieces": [{"id": "a", "w": 1.0, "l": 6.0, "x0": 0.0, "x1": 6.0, "y0": 0.0, "y1": 1.0},
                                    {"id": "b", "w": 1.0, "l": 5.0, "x0": 5.0, "x1": 10.0, "y0": 0.0, "y1": 1.0}]}]
    f = F5.check_plan(rolls, ["a", "b"], 1.0, 10.0)
    assert any(x.startswith("OVERLAP") for x in f)
    rolls[0]["pieces"][1].update(x0=6.0, x1=11.0)
    f = F5.check_plan(rolls, ["a", "b"], 1.0, 10.0)
    assert any(x.startswith("OUTSIDE_ROLL") for x in f) and not any(x.startswith("OVERLAP") for x in f)
    assert any(x.startswith("PIECES") for x in F5.check_plan(rolls, ["a", "b", "c"], 1.0, 10.0))


# ------------------------------------------------------------------------------------------------ geometric fixtures
def test_fixture_x_v3_count_invalid_corrected():
    f = F3.fold(ROOF_X)
    x = [y for y in f["layouts_v3"] if y["direction"] == F3.ALONG_LONG and y["start"] == F3.LOWER][0]
    assert x["rolls_by_basis"]["Q58_A"] == 8
    au = F5.audit_v3(x, f["spec"])
    assert au["verdict"] == F5.INVALID and au["final_roll_ends_m"] == [2.5]
    assert au["corrected"] == 9                      # V3's own pieces, each leftover once
    a = F5.plan_q58_a(x, f["spec"])                  # V5's pieces: last patch piece 0.10 wide, in a 0.50 trim
    assert a["rolls"] == 8 and a["check"] == "PASSED"
    thin = [q for q in a["pieces_from_own_offcuts"] if q["w"] == pytest.approx(0.1)]
    assert len(thin) == 1 and thin[0]["source"] == "OWN_SIDE_TRIM"


@pytest.mark.parametrize("variant", [{}, {"mirror": True}, {"deg": 90.0}, {"scale": 1000.0}])
def test_fixture_r_valid_five_rolls_with_ledger(variant):
    unit = 0.001 if variant.get("scale") else 1.0
    f = F5.fold(_xf(ROOF_R, **variant), unit_m=unit)
    ch = f["choice_v5"]
    assert ch["state"] == "HELD_Q58" and {b: x["rolls"] for b, x in ch["by_reading"].items()} == {
        "Q58_A": 5, "Q58_B": 6, "Q58_C": 6}
    assert ch["rolls_bounded"] == {"low": 5, "high": 6} and ch["q58_a"]["v4_claimed"] == 5
    lg = ch["q58_a"]["ledger"]
    assert lg["floor_m2"] == pytest.approx(36.375) and lg["installed_m2"] == pytest.approx(42.935)
    assert lg["upturn_m2"] == pytest.approx(6.56) and lg["gross_cut_m2"] == pytest.approx(47.475)
    assert lg["lap_m2"] == pytest.approx(4.54) and lg["trim_m2"] == pytest.approx(0.0)
    assert lg["offcut_left_m2"] == pytest.approx(2.525) and lg["rolls_q58_a"] == 5 and lg["balanced"]
    for y in f["layouts_v5"]:
        assert y["audit_v3_a"]["verdict"] == F5.VALID
        assert y["rolls_v5"]["Q58_A"] <= y["rolls_v5"]["Q58_B"]
        L = y["ledger"]
        assert L["gross_cut_m2"] + L["offcut_left_m2"] == pytest.approx(L["roll_m2_bought"])
        assert L["installed_m2"] == pytest.approx(L["gross_cut_m2"] - L["lap_m2"] - L["trim_m2"], abs=1e-3)


def test_v5_plan_passes_the_independent_v213_proof():
    """the V5 A plan of fixture R written back as a V3 count is proven by ARCH_TAKEOFF_V2.13's own proof code."""
    f = F3.fold(ROOF_R)
    x = [y for y in f["layouts_v3"] if y["direction"] == F3.ACROSS and y["start"] == F3.OPPOSITE][0]
    a = F5.plan_q58_a(x, f["spec"])
    y = copy.deepcopy(x)
    y["counts"]["Q58_A"] = {"rolls": a["rolls"],
                            "pieces_from_rolls": [{"what": p["what"], "w": p["w"], "l": p["l"]}
                                                  for p in a["pieces_from_rolls"] if p["what"] != "MAIN"],
                            "pieces_from_own_offcuts": [{"what": p["what"], "w": p["w"], "l": p["l"]}
                                                        for p in a["pieces_from_own_offcuts"]]}
    pr = AV.prove_q58_a(y, f["spec"])
    assert pr["proven"] and pr["rolls"] == a["rolls"] == 5


def test_v4_layouts_unchanged_and_v5_beside_them():
    f4 = F4.fold(ROOF_R)
    f5 = F5.fold(ROOF_R)
    assert [x["rolls_by_basis"] for x in f4["layouts_v4"]] == [y["rolls_v4"] for y in f5["layouts_v5"]]
    assert f5["choice_v4"] == f4["choice_v4"] and f5["method_v5"] == "MEMBRANE_FOLD_V5"


def test_rectangle_released_same_under_every_reading():
    f = F5.fold([(0, 0), (4.5, 0), (4.5, 3.0), (0, 3.0)])
    ch = f["choice_v5"]
    assert ch["state"] == "RELEASED" and ch["rolls"] == 2
    lg = ch["q58_a"]["ledger"]
    assert lg["installed_m2"] == pytest.approx(4.9 * 3.4) and lg["floor_m2"] == pytest.approx(13.5)
    assert lg["gross_cut_m2"] == pytest.approx(3 * 4.9 + 0.7 * 4.9)    # 4 strips across 3.40: 1.0, 1.0, 1.0, 0.7
    assert lg["offcut_left_m2"] == pytest.approx(20.0 - 18.13)


@pytest.mark.parametrize("spec,reason", [({"roll_length_m": None}, "MISSING_INPUT_ROLL_LENGTH_M"),
                                          ({"lap_m": 1.5}, "LAP_NOT_SMALLER_THAN_ROLL")])
def test_missing_input_is_held_never_zero(spec, reason):
    r = F5.plan([(0, 0), (3, 0), (3, 2), (0, 2)], spec=spec)
    assert r["state"] == "HELD" and r["reason"] == reason and r["choice"] is None
    assert F5.plan([], spec=None)["state"] == "HELD"


def test_rebar_product_firewall():
    """a membrane module reads no rebar / concrete product module (the product firewall of the earlier fold tasks)."""
    src = (ROOT / "engine/source/membrane_fold_v5.py").read_text(encoding="utf-8")
    for bad in ("rebar", "concrete_ledger", "slab_rebar", "urban_structural"):
        assert f"import {bad}" not in src and f"source import {bad}" not in src
