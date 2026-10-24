"""T-272 Villa F hand fixture (synthetic, not Alsenan) and adverse cases for STIRRUP_CLOSURE_V1.

Villa F, sheet S-7 (invented): ground beam GB-F1, 0.25 wide x 0.50 deep, clear span 5.00 m between column faces.
Printed: links 'ø8' at 10 cm over 1.20 m from each face and 20 cm in the middle, 'maximum spacing' (schedule note),
first link 50 mm from the face, cover 30 mm (exact, BBS note), centreline bend radius 2d, 135-degree hooks with
10d tails.

Hand count (anchors = first / last link at 0.05 and 4.95; each gap <= its zone spacing):
  0.05, 0.15 .. 1.15 (12) | 1.25 (gap 1.15-1.25 spans both zones, <= 0.10) .. 3.65 step 0.20 (13) | 3.80 (zone 3 start,
  gap 0.15 <= 0.20 inside zone 2) (1) | 3.90 .. 4.90 (11) | 4.95 (1)  -> 38.
  Without the end rule: faces as end ties -> 0.10 .. 1.10 (11), 1.20 (1), 1.40 .. 3.60 (12), 3.80 (1), 3.90 .. 4.90 (11)
  = 36 (low); a link at each face -> 38 (high).
Hand cut length: a = 0.25 - 0.06 - 0.008 = 0.182; c' = 0.50 - 0.06 - 0.008 = 0.432; R = 2 x 8 = 0.016;
  (3 pi - 8) R = 1.424778 x 0.016 = 0.022796; tails 2 x 0.080 = 0.160;
  L = 2 x (0.182 + 0.432) + 0.022796 + 0.160 = 1.410796 m.
Hand mass: 38 x 1.410796 x 64 / 162 = 21.17937 kg.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t272"))
import t272_stirrups as S  # noqa: E402

ZONES = [(1.20, 0.10), (2.60, 0.20), (1.20, 0.10)]
FIRST = S.facet(S.PRINTED, 50, "Villa F S-7 note 4 (first link 50 mm from the face)", unit="mm")


def shape(**over):
    sh = {"b_m": 0.25, "h_m": 0.50, "d_mm": 8, "closure": "HOOKS",
          "cover": S.facet(S.PRINTED, 30, "Villa F S-7 BBS note: cover 30 mm", unit="mm"),
          "bend_radius": S.facet(S.PRINTED, 2, "Villa F S-7 BBS note: centreline radius 2d", unit="d"),
          "hook_angle": S.facet(S.PRINTED, 135, "Villa F S-7 link detail: 135 deg", unit="deg"),
          "hook_ext": S.facet(S.PRINTED, 10, "Villa F S-7 link detail: tail 10d", unit="d")}
    sh.update(over)
    return sh


# ---------------------------------------------------------------- normal case
def test_count_two_zones_printed_end_rule():
    env = S.count_envelope(ZONES, FIRST, S.MAXIMUM)
    assert env["count"] == 38 and env["status"] == S.CONFIRMED
    assert (env["low"], env["high"]) == (36, 38)


def test_cut_length_and_mass_by_hand():
    L, held = S.cut_length(shape())
    assert held == [] and L == pytest.approx(1.410796, abs=1e-6)
    rec = S.stirrup_run("GB-F1", "GB", S.count_envelope(ZONES, FIRST, S.MAXIMUM), shape())
    assert rec["kg"] == pytest.approx(21.17937, abs=1e-4) and rec["kg_status"] == S.CONFIRMED
    assert rec["kg_per_m"] == pytest.approx(64 / 162, abs=1e-6)


def test_formula_is_the_bent_bar_not_the_sharp_box():
    # 90-degree hooks: arcs 3 x 90 + 2 x 90 = 450 deg = 2.5 pi R
    sh = shape(hook_angle=S.facet(S.PRINTED, 90, "x", unit="deg"))
    L, _ = S.cut_length(sh)
    assert L == pytest.approx(2 * (0.182 + 0.432) - 8 * 0.016 + 2.5 * math.pi * 0.016 + 0.16, abs=1e-9)
    # with R = 0 and no tail the cut length collapses to the sharp perimeter (the QA reading)
    sh0 = shape(bend_radius=S.facet(S.PRINTED, 0, "x", unit="mm"), hook_ext=S.facet(S.PRINTED, 0, "x", unit="mm"))
    assert S.cut_length(sh0)[0] == pytest.approx(S.sharp_perimeter_qa(0.25, 0.50, 8, 0.03), abs=1e-12)


def test_exact_pitch_single_zone():
    env = S.count_envelope([(3.0, 0.15)], S.facet(S.PRINTED, 5, "x", unit="cm"), S.EXACT)
    assert env["count"] == 20          # floor(2.90 / 0.15) + 1


# ---------------------------------------------------------------- adverse: mirror, units
def test_mirrored_beam_same_count():
    z = [(1.0, 0.10), (4.0, 0.20)]
    for e in (None, FIRST):
        a = S.count_envelope(z, e, S.MAXIMUM if e else None)
        b = S.count_envelope(list(reversed(z)), e, S.MAXIMUM if e else None)
        assert (a["low"], a["high"], a["count"]) == (b["low"], b["high"], b["count"])
    assert S.count_envelope(z, FIRST, S.MAXIMUM)["count"] == 31


def test_units_cm_and_mm_agree_and_undeclared_refused():
    cm = shape(cover=S.facet(S.PRINTED, 3, "x", unit="cm"))
    assert S.cut_length(cm)[0] == pytest.approx(S.cut_length(shape())[0], abs=1e-12)
    with pytest.raises(S.StirrupInputError):
        S.facet(S.PRINTED, 30, "x", unit="inch")


# ---------------------------------------------------------------- adverse: missing data -> HELD, never 0
def test_hook_not_printed_is_held_never_zero():
    rec = S.stirrup_run("GB-F1", "GB", S.count_envelope(ZONES, FIRST, S.MAXIMUM),
                        shape(hook_ext=S.facet(S.NOT_PRINTED)))
    assert rec["kg"] is None and rec["kg_status"] == S.HELD and rec["cut_length_m"] is None
    assert any("hook extension" in h for h in rec["cut_length_held"])


def test_minimum_cover_is_an_envelope_not_a_size():
    L, held = S.cut_length(shape(cover=S.facet(S.MINIMUM_ONLY, 25, "note: cover >= 25 mm", unit="mm")))
    assert L is None and any("upper envelope" in h for h in held)


def test_drawn_hook_shape_only_is_held():
    L, held = S.cut_length(shape(hook_angle=S.facet(S.SHAPE_ONLY, ref="drawn tick")))
    assert L is None and held == ["hook angle drawn, not printed"]


def test_no_end_rule_gives_envelope_and_held():
    env = S.count_envelope([(5.745, 0.15)])
    assert env["count"] is None and env["status"] == S.HELD
    assert (env["low"], env["half_spacing_reading"], env["high"]) == (38, 39, 40)   # ceil(38.3) -1 / +0 / +1


def test_end_rule_without_spacing_meaning_stays_held():
    env = S.count_envelope([(3.0, 0.15)], S.facet(S.PRINTED, 5, "x", unit="cm"), None)
    assert env["count"] is None and env["status"] == S.HELD


def test_cover_larger_than_half_width_flags_designer():
    flags = S.design_flags(shape(b_m=0.12), {"soil 7 cm": 0.07})
    assert flags and "designer item" in flags[0]
    L, held = S.cut_length(shape(b_m=0.12, cover=S.facet(S.PRINTED, 7, "x", unit="cm")))
    assert L is None and "no link core" in held[0]


def test_link_drawn_without_closure_is_held_and_flagged():
    sh = shape(closure="NONE_DRAWN")
    assert S.cut_length(sh)[0] is None
    assert any("no closure" in f for f in S.design_flags(sh, {}))


# ---------------------------------------------------------------- adverse: refused inputs
def test_code_hook_value_refused():
    with pytest.raises(S.StirrupInputError):
        S.facet(S.PRINTED, 6, "a code table", provenance="CODE_OR_EXTERNAL", unit="d")
    with pytest.raises(S.StirrupInputError):
        S.facet(S.PRINTED, 6, "freelancer sheet", provenance="FREELANCER", unit="d")


def test_rate_and_default_keys_refused():
    with pytest.raises(S.StirrupInputError):
        S.cut_length(dict(shape(), kg_per_m3=90))
    with pytest.raises(S.StirrupInputError):
        S.cut_length(dict(shape(), hook_default=10))


def test_printed_facet_needs_reference():
    with pytest.raises(S.StirrupInputError):
        S.facet(S.PRINTED, 135, None, unit="deg")


# ---------------------------------------------------------------- curved run
def test_curved_run_envelope_inner_to_outer_arc():
    theta = 2.0
    env = S.curved_count_envelope(theta, 2.0, 2.4, 0.15)
    assert env["status"] == S.HELD and env["count"] is None
    assert env["low"] == math.ceil(4.0 / 0.15) - 1 and env["high"] == math.ceil(4.8 / 0.15) + 1
    on_c = S.curved_count_envelope(theta, 2.0, 2.4, 0.15, spacing_radius=2.2)
    assert (on_c["low"], on_c["high"]) == (math.ceil(4.4 / 0.15) - 1, math.ceil(4.4 / 0.15) + 1)
    with pytest.raises(S.StirrupInputError):
        S.curved_count_envelope(theta, 2.0, 2.4, 0.15, spacing_radius=2.5)
