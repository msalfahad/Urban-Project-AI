"""T-787 rule DOME_EXTRADOS_V1 (proposed; company roof default owner 2026-11-13, UP-WP-ROOF-001; any villa).

Physical element: the exposed OUTER face (extrados) of one concrete dome shell, from its springing plane (top of the
ring beam / drum, where the printed chord is taken) to the crown. It is a surface of its own, not part of the flat roof:
the flat-roof layers stop at the dome base with an upturn (ROOF_LAYER_AREA_V1, T-780) and the dome footprint is
already deducted there, so an extrados line never double counts the flat roof.

    spherical cap through the springing circle (outer chord c, a = c / 2) and the outer crown (rise h):
        R = (a^2 + h^2) / 2h,  extrados A = 2 pi R h = pi (a^2 + h^2)

Evidence order for (c, h): a printed dome section of THIS dome (DRAWING-READ) > the printed section of a dome the
architect draws with the identical outline (DEFAULT, same element type) > nothing (HELD range). A height dimension on an
ELEVATION is the part visible above the parapet line, not the rise: it is refused as a rise (T-787 finding: the 2.15 of
the 2F dome was read as a rise in T-780's beside note).

Rise missing (chord known): HELD, never 0, range low = pi a^2 (rise -> 0, the flat disc it covers) .. high = 2 pi a^2
(hemisphere, rise = a), or pi (a^2 + h_max^2) when a bound h_max is printed / drawn.

Layers on the extrados (company roof default): membrane and protection = the extrados area each (DEFAULT); the falls
screed and the insulation sit only where a section prints them on the shell (none printed -> no line, designer item);
the flat-roof finish (tiles) does not apply to a curved shell.
"""
from __future__ import annotations

import math


class DomeRuleError(ValueError):
    pass


def _pos(v, what):
    if v is None or isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v <= 0:
        raise DomeRuleError(f"{what} missing or not positive: {v!r} (HELD, never 0)")
    return float(v)


def extrados(chord_m, rise_m):
    """outer spherical-cap area (m2) from the printed OUTER chord at the springing plane and the rise to the outer crown.

    Units: metres only. A chord above 30 m or a rise above the chord reads as mm / a misread and is refused."""
    c = _pos(chord_m, "dome chord")
    h = _pos(rise_m, "dome rise")
    if c > 30:
        raise DomeRuleError(f"dome chord {c} m: units (mm read as m?)")
    if h > c:
        raise DomeRuleError(f"dome rise {h} > chord {c}: not a dome shell, or the rise is an elevation height")
    a = c / 2.0
    return {"a_m": a, "rise_m": h, "R_m": (a * a + h * h) / (2.0 * h), "area_m2": math.pi * (a * a + h * h)}


def extrados_range(chord_m, rise_max_m=None):
    """HELD range when the rise is not printed: low = flat disc pi a^2, high = hemisphere 2 pi a^2 (or the printed max)."""
    c = _pos(chord_m, "dome chord")
    if c > 30:
        raise DomeRuleError(f"dome chord {c} m: units (mm read as m?)")
    a = c / 2.0
    hi = 2 * math.pi * a * a if rise_max_m is None else math.pi * (a * a + _pos(rise_max_m, "rise bound") ** 2)
    return {"class": "HELD", "low": math.pi * a * a, "high": hi}


def refuse_elevation_height(source):
    """a height read on an elevation (visible above the parapet line) is not a rise"""
    if source == "ELEVATION":
        raise DomeRuleError("an elevation height is the part above the parapet line, not the rise: use a section")
    return source


def dome_layers(area_m2):
    """company roof default layers that sit on a shell: membrane + protection = the extrados area (DEFAULT)"""
    a = _pos(area_m2, "extrados area")
    return {"FIN.WP.ROOF": a, "FIN.ROOF.PROTECTION": a}
