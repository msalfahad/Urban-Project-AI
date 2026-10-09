"""Shell line distribution: synthetic known answers that tell layout rules apart (no project data).

A uniform surface density (area / spacing) is not a fixed set of rim-to-crown meridians: fixed meridians carry
psi0 cot(psi0 / 2) times the density, pi / 2 on a hemisphere and 2 for a very shallow cap, so the two never agree for a
cap no deeper than a hemisphere. Hoops at a spacing along the meridian do give area / spacing.
Fixed meridians crowd towards the crown; curtailing them brings the total back towards the density; whole-bar counts
are a fabrication question, never the continuous quantity."""

from __future__ import annotations

import math

import pytest

from engine.source import shell_line_distribution as D


def hemi(R=2.0):
    return D.cap_frame(R, 0.0)


def test_uniform_density_is_not_a_fixed_meridian_layout():
    R, s = 2.0, 0.15
    f = hemi(R)
    dens = D.uniform_density(f, s)["total"]
    fixed = D.fixed_meridians(f, s)["total"]
    assert dens == pytest.approx(2 * math.pi * R * R / s) and fixed == pytest.approx(math.pi ** 2 * R * R / s)
    assert fixed / dens == pytest.approx(math.pi / 2)                        # 57 % more on a hemisphere
    for psi0 in (0.05, 0.4, 0.9, 1.3):                                      # ratio = psi0 sin psi0 / (1 - cos psi0)
        g = D.cap_frame(R, R * math.cos(psi0))
        ratio = D.fixed_meridians(g, s)["total"] / D.uniform_density(g, s)["total"]
        assert ratio == pytest.approx(psi0 * math.sin(psi0) / (1 - math.cos(psi0)))
    shallow = D.cap_frame(R, R * math.cos(0.01))
    assert D.fixed_meridians(shallow, s)["total"] / D.uniform_density(shallow, s)["total"] == pytest.approx(2, abs=1e-4)
    ratios = [D.fixed_meridians(D.cap_frame(R, R * math.cos(p)), s)["total"] /
              D.uniform_density(D.cap_frame(R, R * math.cos(p)), s)["total"] for p in (0.01, 0.5, 1.0, 1.4, math.pi / 2)]
    assert all(a > b for a, b in zip(ratios, ratios[1:])) and min(ratios) == pytest.approx(math.pi / 2)  # never 1


def test_fixed_meridians_count_and_length():
    f = D.cap_frame(2.2, 0.3)
    m = D.fixed_meridians(f, 0.15)
    assert m["count"] == pytest.approx(2 * math.pi * f["rim_radius"] / 0.15)       # unrounded
    assert m["each"] == pytest.approx(2.2 * math.acos(0.3 / 2.2)) and m["total"] == pytest.approx(m["count"] * m["each"])


def test_hoops_at_meridional_spacing_give_area_over_spacing():
    f = D.cap_frame(2.2, 0.3)
    exact = D.hoops_continuous(f, 0.15)["total"]
    assert exact == pytest.approx(f["area"] / 0.15)
    errs = []
    for s in (0.3, 0.15, 0.075):
        n = int(f["meridian"] / s)                               # whole steps only, so the mid rule tiles the meridian
        mid = D.hoops_discrete(f, f["meridian"] / n, "MID")
        errs.append(abs(mid["total"] * (f["meridian"] / n) - f["area"]))
    assert errs[0] > errs[1] > errs[2] and errs[2] < 1e-3 * f["area"]          # midpoint sums converge (second order)
    rim = D.hoops_discrete(f, 0.15, "RIM")
    assert rim["total"] > exact                                  # starting on the rim biases towards the long circles


def test_spacing_shrinks_towards_the_crown_and_crowding_radius():
    f = D.cap_frame(2.0, 0.2)
    n = D.fixed_meridians(f, 0.15)["count"]
    assert D.spacing_at(f, n, f["psi0"]) == pytest.approx(0.15)
    assert D.spacing_at(f, n, 0.0) == pytest.approx(0.0, abs=1e-15)
    for clear in (0.075, 0.012):
        rho = D.crowding_radius(n, clear)
        assert 2 * math.pi * rho / n == pytest.approx(clear)


def test_termination_sits_between_density_and_no_curtailment():
    f = D.cap_frame(2.2, 0.3)
    dens = D.uniform_density(f, 0.15)["total"]
    fixed = D.fixed_meridians(f, 0.15)["total"]
    half = D.halving_curtailment(f, 0.15, 0.075)["total"]
    assert dens < half < fixed
    fine = D.halving_curtailment(f, 0.15, 0.149)["total"]               # very frequent curtailment -> the density
    assert fine == pytest.approx(dens, rel=0.01)
    coarse = D.halving_curtailment(f, 0.15, 0.001)["total"]             # almost never curtailed -> fixed meridians
    assert coarse == pytest.approx(fixed, rel=0.01)
    with pytest.raises(D.ShellLineError):
        D.halving_curtailment(f, 0.15, 0.2)


def test_fabrication_rounding_is_not_the_continuous_quantity():
    c = D.fabrication_counts(90.45, 20.64)
    assert c["meridians_whole"] == 91 and c["hoops_whole"] == 21
    assert c["meridians_continuous"] == 90.45 and c["hoops_continuous"] == 20.64
    assert D.fabrication_counts(90.0, 20.0) == {"meridians_continuous": 90.0, "meridians_whole": 90,
                                                "hoops_continuous": 20.0, "hoops_whole": 21}   # both ends of the meridian
