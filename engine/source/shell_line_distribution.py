"""SHELL LINE DISTRIBUTION - how lines laid on a spherical cap add up under different layout rules (generic, stdlib).

A spherical cap surface of radius R is cut by a plane at distance d above its centre (d may be negative). Its polar
half-angle is psi0 = acos(d / R), its rim radius a = R sin psi0, its area A = 2 pi R^2 (1 - cos psi0) and a meridian
from the rim to the crown is R psi0 long.

Layout rules for one family of lines at a nominal spacing s:
  uniform_density        total = A / s. The spacing is s everywhere on the surface. For meridians this needs lines that
                         stop continuously towards the crown, so it is an idealised density, not a buildable layout.
  fixed_meridians        N = 2 pi a / s meridians (unrounded), each rim to crown: total = N R psi0. The spacing is s at
                         the rim only; it shrinks as sin(psi) towards the crown, where every meridian meets. Against the
                         density, fixed / density = psi0 sin psi0 / (1 - cos psi0) = psi0 cot(psi0 / 2): 2 for a very
                         shallow cap, pi / 2 on a hemisphere, so for a cap no deeper than a hemisphere the two never agree.
  hoops_continuous       circles at spacing s along the meridian: total = A / s exactly (the integral of 2 pi rho ds / s).
  hoops_discrete         a finite set of circles at spacing s along the meridian, from a stated start: sum of 2 pi rho.
  halving_curtailment    a stated test rule, not a source: meridians start at spacing s at the rim and every other one
                         stops wherever the spacing falls to s_min; repeated to the crown. Unrounded counts.
  crowding_radius        where fixed meridians come closer than a stated clear spacing: rho = c N / (2 pi).
Fabrication counts (whole bars, whole circles) are a different question from a continuous quantity; fabrication_counts()
reports the rounded figures beside the continuous ones and never replaces them.

Nothing here names a project, a sheet or a handle.
"""

from __future__ import annotations

import math


class ShellLineError(ValueError):
    pass


def cap_frame(R, d):
    if R <= 0 or not -R < d < R:
        raise ShellLineError("need R > 0 and -R < d < R")
    psi0 = math.acos(d / R)
    return {"R": R, "d": d, "psi0": psi0, "rim_radius": R * math.sin(psi0), "area": 2 * math.pi * R * R * (1 - d / R),
            "meridian": R * psi0, "rim_circumference": 2 * math.pi * R * math.sin(psi0)}


def _s(s):
    if s <= 0:
        raise ShellLineError("spacing must be positive")
    return s


def uniform_density(frame, s):
    return {"rule": "UNIFORM_DENSITY", "total": frame["area"] / _s(s)}


def fixed_meridians(frame, s):
    n = frame["rim_circumference"] / _s(s)
    return {"rule": "FIXED_MERIDIANS", "count": n, "each": frame["meridian"], "total": n * frame["meridian"]}


def spacing_at(frame, n, psi):
    """spacing between n meridians at polar angle psi (0 = crown)"""
    return 2 * math.pi * frame["R"] * math.sin(psi) / n


def crowding_radius(n, clear):
    """plan radius inside which n meridians are closer than `clear` (centre to centre)"""
    return clear * n / (2 * math.pi)


def hoops_continuous(frame, s):
    return {"rule": "HOOPS_CONTINUOUS", "count": frame["meridian"] / _s(s), "total": frame["area"] / s}


def hoops_discrete(frame, s, start="RIM", count=None):
    """circles at spacing s along the meridian. start RIM: the first circle on the rim, then every s towards the crown;
    MID: the first at s/2. count: number of circles (default: as many as fit on the meridian)."""
    m = frame["meridian"]
    first = 0.0 if start == "RIM" else s / 2.0
    if count is None:
        count = int(math.floor((m - first) / _s(s) + 1e-12)) + 1
    tot, pos = 0.0, []
    for k in range(count):
        u = first + k * s
        if u > m + 1e-12:
            raise ShellLineError("more circles than fit on the meridian")
        psi = frame["psi0"] - u / frame["R"]
        rho = frame["R"] * math.sin(max(0.0, psi))
        pos.append(rho)
        tot += 2 * math.pi * rho
    return {"rule": f"HOOPS_DISCRETE_{start}", "count": count, "total": tot, "radii": pos}


def halving_curtailment(frame, s, s_min):
    """meridians at spacing s on the rim; every other one stops where the spacing reaches s_min; repeated to the crown"""
    if not 0 < s_min < _s(s):
        raise ShellLineError("need 0 < s_min < s")
    R, psi = frame["R"], frame["psi0"]
    n = frame["rim_circumference"] / s
    tot, levels = 0.0, []
    while n > 1e-9 and psi > 1e-12:
        rho_stop = s_min * n / (2 * math.pi)                 # spacing 2 pi rho / n falls to s_min here
        psi_stop = math.asin(min(1.0, rho_stop / R)) if rho_stop < R * math.sin(psi) else psi
        tot += n * R * (psi - psi_stop)
        levels.append({"count": n, "from_psi": psi, "to_psi": psi_stop})
        keep = n * s_min / s                                 # the remaining lines restore spacing s at that radius
        psi, n = psi_stop, keep
        if len(levels) > 1_000_000:                          # sin(psi) falls by s_min / s per level; never truncate silently
            raise ShellLineError("curtailment did not reach the crown")
    return {"rule": "HALVING_CURTAILMENT", "total": tot, "levels": levels}


def fabrication_counts(meridian_count, hoop_count):
    return {"meridians_continuous": meridian_count, "meridians_whole": math.ceil(meridian_count - 1e-12),
            "hoops_continuous": hoop_count, "hoops_whole": math.floor(hoop_count + 1e-12) + 1}
