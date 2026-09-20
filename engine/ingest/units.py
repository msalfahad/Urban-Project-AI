"""Canonical units (PA05 §12).  Quantities carry a unit; adding across units
fails loudly; m2 and lm never share an additive field."""

from __future__ import annotations

UNITS = ("mm", "m", "mm2", "m2", "mm3", "m3", "lm", "nr", "kg", "ton", "KWD")
DIMENSION = {"mm": "L", "m": "L", "lm": "L_RUN", "mm2": "A", "m2": "A", "mm3": "V", "m3": "V", "nr": "N", "kg": "M", "ton": "M", "KWD": "C"}
TO_BASE = {"mm": 0.001, "m": 1.0, "lm": 1.0, "mm2": 1e-6, "m2": 1.0, "mm3": 1e-9, "m3": 1.0, "nr": 1.0, "kg": 1.0, "ton": 1000.0, "KWD": 1.0}


class UnitError(ValueError):
    pass


class Q:
    """A number with a unit.  Arithmetic across incompatible dimensions raises UnitError;
    lm (running length of a face / edge) is deliberately NOT additive with m (a coordinate length)."""

    __slots__ = ("v", "u")

    def __init__(self, v, u):
        if u not in UNITS:
            raise UnitError(f"unknown unit {u}")
        if v is not None and not isinstance(v, (int, float)):
            raise UnitError("value must be a number or None")
        self.v, self.u = v, u

    def _check(self, other):
        if not isinstance(other, Q):
            raise UnitError("both operands must carry a unit")
        if DIMENSION[self.u] != DIMENSION[other.u]:
            raise UnitError(f"cannot combine {self.u} with {other.u}")

    def to(self, u):
        if u not in UNITS or DIMENSION[u] != DIMENSION[self.u]:
            raise UnitError(f"cannot convert {self.u} to {u}")
        if self.v is None:
            return Q(None, u)
        return Q(self.v * TO_BASE[self.u] / TO_BASE[u], u)

    def __add__(self, other):
        self._check(other)
        if self.v is None or other.v is None:
            return Q(None, self.u)
        return Q(self.v + other.to(self.u).v, self.u)

    def __mul__(self, other):
        if isinstance(other, (int, float)):
            return Q(None if self.v is None else self.v * other, self.u)
        if isinstance(other, Q):
            if DIMENSION[self.u] == "L" and DIMENSION[other.u] == "L":
                a, b = self.to("m"), other.to("m")
                return Q(None if a.v is None or b.v is None else a.v * b.v, "m2")
            if {DIMENSION[self.u], DIMENSION[other.u]} == {"L_RUN", "L"}:
                a, b = self.to("lm"), other.to("m")
                return Q(None if a.v is None or b.v is None else a.v * b.v, "m2")
            if {DIMENSION[self.u], DIMENSION[other.u]} == {"A", "L"}:
                a = self.to("m2") if DIMENSION[self.u] == "A" else other.to("m2")
                b = other.to("m") if DIMENSION[self.u] == "A" else self.to("m")
                return Q(None if a.v is None or b.v is None else a.v * b.v, "m3")
        raise UnitError(f"unsupported product {self.u} x {getattr(other, 'u', type(other).__name__)}")

    def record(self):
        return {"VALUE": None if self.v is None else round(self.v, 4), "UNIT": self.u}

    def __repr__(self):
        return f"Q({self.v}, {self.u})"


def total(quantities):
    """Sum quantities of one unit; a mixed list raises."""
    qs = list(quantities)
    if not qs:
        return None
    u = qs[0].u
    out = Q(0.0, u)
    for x in qs:
        if x.u != u:
            raise UnitError(f"mixed units in a total: {u} and {x.u}")
        out = out + x
    return out


def totals_by_unit(quantities):
    by = {}
    for x in quantities:
        by.setdefault(x.u, []).append(x)
    return {u: total(v).record() for u, v in by.items()}
