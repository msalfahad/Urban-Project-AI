"""EARTHWORKS_QTY_V1 (T-350 r2, research, unwired, stdlib only): calculated earthworks quantities per zone, from the
levels and plans the drawings establish, with every unresolved factor HELD (None, never 0).

Physical elements (ERS s.2.1; owner sessions 2026-11-02 17:20 / 17:45 / 18:00):
  EXCAVATION (B1-02)  in-situ soil removed between the EXISTING ground EG and the excavation FORMATION, over the
                      excavation plan (overlapping pits as one geometric union). Finished ground never enters the depth.
                      Footing size is not pit size: the plan is the footing plus the printed blinding projection (neat)
                      plus a working space only from drawings, a specification or a documented method (else HELD by
                      name; the neat quantity is still calculated).
  BACKFILL (B1-03)    finished compacted volume returned around the buried structure up to EG = excavation minus every
                      permanent element at its actual position below EG, overlaps once (the caller's displacement
                      ledger, e.g. DISPLACEMENT_LEDGER_V1).
  LAYERS              per backfill zone, ceil(actual finished backfill depth of the zone / approved finished lift),
                      never from the excavation depth.
  MATERIAL BALANCE    dry-mass conservation (owner 17:45 (4), 18:00 (3)): procurement from the PLACEMENT TARGET dry
                      density (its own field and source), never from the acceptance minimum; imported loose m3 =
                      (required dry mass - dry mass of suitable re-used soil) / loose delivered dry density; loose
                      disposal = surplus in-situ m3 x in-situ / loose dry density; payable disposal stays IN-SITU
                      unless the contract says loose. No universal swell / shrinkage factor: a factor needs a source.
  LOGISTICS           truckloads = ceil(loose m3 / capacity): logistics only, never a measured quantity.

Statuses: DRAWING-CONFIRMED (printed values), ESTIMATED (an owner-accepted scenario or a documented estimate, with
its source), HELD (None). A HELD input makes every quantity that needs it HELD; a zero is only a calculated zero
(e.g. formation at EG), never a missing value. Nothing here names a project, a sheet or a coordinate.
"""
from __future__ import annotations

import math

METHOD_ID = "EARTHWORKS_QTY_V1"
RULE_ID, RULE_VERSION = "R-T350-2", "1.0.0"
DC, EST, HELD, CALC = "DRAWING-CONFIRMED", "ESTIMATED", "HELD", "CALCULATED"
_RANK = {DC: 0, CALC: 0, EST: 1, HELD: 2}
_UNIT = {"m": 1.0, "cm": 0.01, "mm": 0.001}
EPS = 1e-9


class Refused(ValueError):
    def __init__(self, code, msg=""):
        super().__init__(f"{code}: {msg}" if msg else code)
        self.code = code


def _r(x, n=6):
    return None if x is None else round(x + 0.0, n)


def worst(*st):
    """The weakest of several statuses (a quantity is never stronger than its weakest input)."""
    st = [s for s in st if s]
    return max(st, key=lambda s: _RANK.get(s, 2)) if st else HELD


def fact(value, status, source=None):
    """A sourced value. HELD carries no number; anything else needs a number and, unless printed, a source."""
    if status not in _RANK:
        raise Refused("UNKNOWN_STATUS", repr(status))
    if status == HELD:
        if value is not None:
            raise Refused("HELD_AS_VALUE", f"{value!r}")
        return {"value": None, "status": HELD, "source": source}
    if value is None:
        raise Refused("VALUE_MISSING", status)
    if status == EST and not source:
        raise Refused("ESTIMATE_WITHOUT_SOURCE", f"{value!r}")
    return {"value": float(value), "status": status, "source": source}


def _v(f):
    return None if f is None else f["value"]


def _s(f):
    return HELD if f is None else f["status"]


# ------------------------------------------------------------------------------------------------ geometry
def depth(eg, formation, unit="m"):
    """Excavation depth = EG - formation (finished ground is a separate datum and is not an input). A formation above
    EG is refused (that is fill, not excavation)."""
    s = _UNIT.get(unit)
    if s is None:
        raise Refused("UNIT_NOT_DECLARED", repr(unit))
    if _v(eg) is None or _v(formation) is None:
        return fact(None, HELD, "EG or formation HELD")
    d = (_v(eg) - _v(formation)) * s
    if d < -EPS:
        raise Refused("FORMATION_ABOVE_EG", f"{_v(formation)} > {_v(eg)}")
    return {"value": _r(max(d, 0.0)), "status": worst(_s(eg), _s(formation)), "source": "EG - formation"}


def _norm(rect, s):
    x0, y0, x1, y1 = (float(v) * s for v in rect)
    if abs(x1 - x0) < EPS or abs(y1 - y0) < EPS:
        raise Refused("EMPTY_RECT", repr(rect))
    return min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)


def union_area(rects, unit="m", grow=0.0):
    """Exact plan area of the union of axis-aligned rectangles (each grown by `grow` m on every side), by coordinate
    compression: overlapping pits are one excavation, counted once."""
    s = _UNIT.get(unit)
    if s is None:
        raise Refused("UNIT_NOT_DECLARED", repr(unit))
    R = [_norm(r, s) for r in rects]
    R = [(a - grow, b - grow, c + grow, d + grow) for a, b, c, d in R]
    if not R:
        return 0.0
    xs = sorted({v for r in R for v in (r[0], r[2])})
    area = 0.0
    for xa, xb in zip(xs, xs[1:]):
        iv = sorted((r[1], r[3]) for r in R if r[0] <= xa + EPS and r[2] >= xb - EPS)
        cov, cur = 0.0, None
        for a, b in iv:
            if cur is None or a > cur[1]:
                if cur:
                    cov += cur[1] - cur[0]
                cur = [a, b]
            else:
                cur[1] = max(cur[1], b)
        if cur:
            cov += cur[1] - cur[0]
        area += cov * (xb - xa)
    return _r(area, 9)


def excavation(plan_m2, dep, working_space=None):
    """In-situ excavation = plan x depth. `plan_m2` a fact (neat union plan); `working_space` a fact holding the extra
    plan (m2) a source gives, or None / HELD: the neat quantity is still returned, the working-space part is named."""
    base = None if _v(plan_m2) is None or _v(dep) is None else _r(_v(plan_m2) * _v(dep))
    out = {"neat_m3": base, "neat_status": worst(_s(plan_m2), _s(dep)) if base is not None else HELD,
           "working_space_m3": None, "working_space_status": HELD, "total_m3": None, "total_status": HELD}
    if working_space is not None and _v(working_space) is not None and base is not None:
        ws = _r(_v(working_space) * _v(dep))
        out.update(working_space_m3=ws, working_space_status=worst(_s(working_space), _s(dep)),
                   total_m3=_r(base + ws), total_status=worst(out["neat_status"], _s(working_space)))
    return out


def backfill(excavated_m3, displacement):
    """Finished compacted backfill = excavated - sum(displacement facts). Any HELD part -> HELD. Negative refused."""
    if excavated_m3 is None or _v(excavated_m3) is None or any(_v(d) is None for d in displacement):
        return fact(None, HELD, "an excavation or displacement part is HELD")
    disp = sum(_v(d) for d in displacement)
    if disp > _v(excavated_m3) + 1e-9:
        raise Refused("DISPLACEMENT_EXCEEDS_EXCAVATION", f"{disp} > {_v(excavated_m3)}")
    return {"value": _r(_v(excavated_m3) - disp), "status": worst(_s(excavated_m3), *[_s(d) for d in displacement]),
            "source": "excavated - displacement below EG"}


def layers(zone_depth, lift):
    """ceil(finished backfill depth of the zone / approved finished lift); a 0 depth is 0 layers; HELD lift -> HELD."""
    if _v(zone_depth) is None or _v(lift) is None:
        return {"value": None, "status": HELD}
    if _v(lift) <= 0:
        raise Refused("LIFT_NOT_POSITIVE", repr(_v(lift)))
    n = math.ceil(_v(zone_depth) / _v(lift) - 1e-9) if _v(zone_depth) > EPS else 0
    return {"value": n, "status": worst(_s(zone_depth), _s(lift))}


# ------------------------------------------------------------------------------------------------ material
def loose_from_insitu(insitu_m3, swell):
    """Loose excavated m3 = in-situ x (1 + swell); swell needs a source (soil report / test / documented estimate)."""
    if _v(insitu_m3) is None or _v(swell) is None:
        return {"value": None, "status": HELD}
    return {"value": _r(_v(insitu_m3) * (1.0 + _v(swell))), "status": worst(_s(insitu_m3), _s(swell))}


def loose_from_compacted(compacted_m3, factor):
    """Loose m3 to place a compacted volume = compacted x loose-to-compacted factor (sourced)."""
    if _v(compacted_m3) is None or _v(factor) is None:
        return {"value": None, "status": HELD}
    return {"value": _r(_v(compacted_m3) * _v(factor)), "status": worst(_s(compacted_m3), _s(factor))}


def truckloads(loose_m3, capacity_m3):
    """Logistics only: ceil(loose / capacity)."""
    if _v(loose_m3) is None or _v(capacity_m3) is None:
        return {"value": None, "status": HELD}
    return {"value": math.ceil(_v(loose_m3) / _v(capacity_m3) - 1e-9), "status": worst(_s(loose_m3), _s(capacity_m3))}


def dry_mass_balance(excavated_insitu, compacted_fill, rho_insitu, rho_target, rho_loose_import, rho_loose_spoil,
                     reuse_fraction, rho_acceptance=None):
    """Dry-mass conservation (owner 17:45 (4), 18:00 (3)). Densities t/m3, each a fact. `compacted_fill` = every
    compacted volume drawn from the site soil (backfill + placed fill). `reuse_fraction` = suitable share of the
    excavated soil (geotechnical evidence only; HELD by default). Acceptance density is a compliance check only:
    it is reported, never used for procurement (refused if passed as the target).
    -> required dry mass, re-used dry mass, imported loose m3, surplus in-situ m3 (payable basis) and loose m3."""
    if rho_acceptance is not None and rho_target is not None and (
            rho_target is rho_acceptance or (rho_target.get("source") and
                                             rho_target.get("source") == rho_acceptance.get("source"))):
        raise Refused("ACCEPTANCE_DENSITY_AS_PROCUREMENT", "procurement uses the placement target density, its own "
                                                           "field and source, never the acceptance minimum")
    need = [excavated_insitu, compacted_fill, rho_insitu, rho_target, reuse_fraction]
    out = {k: {"value": None, "status": HELD} for k in
           ("required_dry_t", "reused_dry_t", "imported_loose_m3", "surplus_insitu_m3", "surplus_loose_m3")}
    if any(_v(x) is None for x in need):
        return out
    st = worst(*[_s(x) for x in need])
    M = _v(compacted_fill) * _v(rho_target)
    avail = _v(excavated_insitu) * _v(rho_insitu) * _v(reuse_fraction)
    used = min(M, avail)
    out["required_dry_t"] = {"value": _r(M), "status": st}
    out["reused_dry_t"] = {"value": _r(used), "status": st}
    surplus_insitu = _v(excavated_insitu) - used / _v(rho_insitu)
    out["surplus_insitu_m3"] = {"value": _r(surplus_insitu), "status": st}
    if _v(rho_loose_import) is not None:
        out["imported_loose_m3"] = {"value": _r((M - used) / _v(rho_loose_import)), "status": worst(st, _s(rho_loose_import))}
    if _v(rho_loose_spoil) is not None:
        out["surplus_loose_m3"] = {"value": _r(surplus_insitu * _v(rho_insitu) / _v(rho_loose_spoil)),
                                   "status": worst(st, _s(rho_loose_spoil))}
    return out
