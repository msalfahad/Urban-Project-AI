"""REBAR UNIT MASS - one project-wide method (generic).

Every reinforcement module (columns, beams, slabs, footings, ...) takes its kg/m from here, with the method the
PROJECT selected. No module may carry its own hidden formula.

Methods
    D2_OVER_162          kg/m = d^2 / 162              (d in mm; common site rule)
    D2_OVER_162_16       kg/m = d^2 / 162.16           (pi/4 x 7850 / 1e6 rounded to the usual constant)
    EXACT_DENSITY        kg/m = pi/4 x (d/1000)^2 x density   (density in kg/m3, required)
    STANDARD_MASS_TABLE  kg/m from a supplied table {d_mm: kg/m}; a diameter missing from the table is an error

Stdlib only.
"""

from __future__ import annotations

import math

D2_OVER_162 = "D2_OVER_162"
D2_OVER_162_16 = "D2_OVER_162_16"
EXACT_DENSITY = "EXACT_DENSITY"
STANDARD_MASS_TABLE = "STANDARD_MASS_TABLE"
METHODS = (D2_OVER_162, D2_OVER_162_16, EXACT_DENSITY, STANDARD_MASS_TABLE)


class UnitMassError(ValueError):
    pass


def validate(method_cfg):
    """method_cfg: {"method": ..., "density_kg_m3": ... (EXACT_DENSITY), "table": {...} (STANDARD_MASS_TABLE),
    "authority": ..., "selected_by": ...}. Returns the config or raises."""
    if not isinstance(method_cfg, dict) or method_cfg.get("method") not in METHODS:
        raise UnitMassError(f"unit-mass method must be one of {METHODS}")
    m = method_cfg["method"]
    if m == EXACT_DENSITY and not method_cfg.get("density_kg_m3"):
        raise UnitMassError("EXACT_DENSITY needs density_kg_m3")
    if m == STANDARD_MASS_TABLE and not method_cfg.get("table"):
        raise UnitMassError("STANDARD_MASS_TABLE needs a table")
    return method_cfg


def kg_per_m(d_mm, method_cfg):
    """kg per metre of one bar of nominal diameter d_mm under the project's method."""
    m = validate(method_cfg)["method"]
    if m == D2_OVER_162:
        return d_mm * d_mm / 162.0
    if m == D2_OVER_162_16:
        return d_mm * d_mm / 162.16
    if m == EXACT_DENSITY:
        return math.pi / 4.0 * (d_mm / 1000.0) ** 2 * method_cfg["density_kg_m3"]
    table = {float(k): v for k, v in method_cfg["table"].items()}
    if float(d_mm) not in table:
        raise UnitMassError(f"diameter {d_mm} not in the standard mass table")
    return table[float(d_mm)]


def describe(method_cfg):
    m = validate(method_cfg)["method"]
    return {D2_OVER_162: "kg/m = d^2 / 162", D2_OVER_162_16: "kg/m = d^2 / 162.16",
            EXACT_DENSITY: f"kg/m = pi/4 x d^2 x {method_cfg.get('density_kg_m3')} kg/m3",
            STANDARD_MASS_TABLE: "kg/m from the supplied standard mass table"}[m]


def assert_single_method(configs):
    """All modules of one project must use the same method - raise if two differ."""
    seen = {(c["method"], c.get("density_kg_m3"), tuple(sorted((c.get("table") or {}).items())))
            for c in configs}
    if len(seen) > 1:
        raise UnitMassError(f"more than one unit-mass method in one project: {sorted(seen, key=str)}")
    return True
