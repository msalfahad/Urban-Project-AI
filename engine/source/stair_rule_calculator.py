"""STAIR RULE CALCULATOR - the owner stair rule UP-STAIR-015 (URBAN_RULES 1.6.0, owner 2026-10-21): riser / tread
counts, stair type, required length and fit check from a floor height and an available length, plus a check mode for
a drawn stair (generic; stdlib only; no drawing reading; not wired into any method).

    design(floor_height, stair_width, available_length=None, max_riser=None, tread=None, landing_depth=None,
           tread_buildup=None, unit="m")
        the owner method for a stair the drawings do not draw (owner S-1): risers = ceil(H / max_riser), uniform
        actual riser, single flight (treads = risers - 1, length = treads x tread) and U (flights ceil / floor of
        risers / 2, total treads = risers - 2, length = (flight1 - 1) x tread + landing_depth), the fit result and
        the BOQ lines. Released lines carry ASSUMED — OWNER-APPROVED with the rule record as the source.
    check_drawn(floor_height, drawn_risers, drawn_treads=None, drawn_tread_depth=None, drawn_flights=1,
                drawn_riser_heights=None, max_riser=None, unit="m")
        owner S-1 = DRAWING GOVERNS: the drawn counts are kept; the rule only reports findings (count differs,
        riser above 0.16, tread under 0.28, inconsistent tread count, non-uniform risers). Never a quantity.
    rule_record()                       the UP-STAIR-015 record read from rules/owner_decisions/URBAN_RULES_1.6.0.json

Arithmetic is exact (decimal): 4.48 / 0.16 is 28 risers, never 29; limit comparisons carry a 1e-9 m tolerance
(rule record "arithmetic"). Inputs in m, or in mm with unit="mm"; an omitted max_riser / tread / tread_buildup is the
rule default 0.16 / 0.30 / 0.030 m whatever the unit (a default is never re-read as mm). Units are never summed
(UP-STAIR-004).

Statuses (WORKFLOW_CONTROLS s.5): ASSUMED — OWNER-APPROVED for a line the rule gives; HELD with a cause when the
type cannot be chosen (no available length) or the stair does not fit. A held line is never 0: its quantity is None
and the candidate values per type are listed beside it.
"""

from __future__ import annotations

import json
import math
from decimal import Decimal, InvalidOperation, ROUND_CEILING, ROUND_FLOOR
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RULE_FILE = ROOT / "rules" / "owner_decisions" / "URBAN_RULES_1.6.0.json"
RULE_ID = "UP-STAIR-015"
RULE_SET = "URBAN_RULES 1.6.0"
SOURCE = "docs/agents/OWNER_RULE_STAIRS_2026-10-21.md (agents/control); " + RULE_SET + " " + RULE_ID

ASSUMED = "ASSUMED — OWNER-APPROVED"
HELD = "HELD"
SINGLE, U_TYPE = "SINGLE", "U"
FITS_SINGLE, FITS_U, DOES_NOT_FIT, NOT_CHECKED = "FITS_SINGLE", "FITS_U", "DOES_NOT_FIT", "NOT_CHECKED"

DEFAULT_MAX_RISER = Decimal("0.16")
DEFAULT_TREAD = Decimal("0.30")
RISER_LIMIT = Decimal("0.16")          # rule step 6: warn when actual_riser > 0.16
TREAD_MIN = Decimal("0.28")            # rule step 6: warn when tread < 0.28
TREAD_MAX = Decimal("0.30")            # rule terms: tread allowed 0.28 - 0.30
TREAD_BUILDUP = Decimal("0.030")       # UP-STAIR-006 tread marble 30 mm (S-2 / UP-STAIR-003)
TOL = Decimal("1e-9")


class StairRuleError(ValueError):
    pass


@lru_cache(maxsize=None)
def _rule_file():
    return json.loads(RULE_FILE.read_text(encoding="utf-8"))


def rule_record():
    d = _rule_file()
    if d.get("base", {}).get("version") != "1.5.0":
        raise StairRuleError("URBAN_RULES 1.6.0 must overlay 1.5.0")
    for r in d["records"]:
        if r["rule_id"] == RULE_ID:
            if r["status"] != "OWNER_APPROVED":
                raise StairRuleError(f"{RULE_ID} is not owner-approved in {RULE_SET}")
            return json.loads(json.dumps(r))
    raise StairRuleError(f"{RULE_ID} is not in {RULE_SET}")


def _dec(value, name, unit, positive=True, allow_zero=False):
    if isinstance(value, bool) or value is None:
        raise StairRuleError(f"{name} is required (got {value!r})")
    if isinstance(value, float):
        if not math.isfinite(value):
            raise StairRuleError(f"{name} must be finite (got {value!r})")
        d = Decimal(repr(value))       # shortest repr: 4.48 -> Decimal('4.48'), not the binary expansion
    else:
        try:
            d = Decimal(str(value))
        except (InvalidOperation, ValueError):
            raise StairRuleError(f"{name} is not a number (got {value!r})") from None
        if not d.is_finite():
            raise StairRuleError(f"{name} must be finite (got {value!r})")
    if unit == "mm":
        d = d / 1000
    elif unit != "m":
        raise StairRuleError(f"unit must be 'm' or 'mm' (got {unit!r})")
    if positive and (d < 0 or (d == 0 and not allow_zero)):
        raise StairRuleError(f"{name} must be {'>= 0' if allow_zero else '> 0'} (got {value!r} {unit})")
    return d


def _ceil(q):
    """ceil with the rule's 1e-9 tolerance: an exact quotient stays itself."""
    return int((q - TOL).to_integral_value(rounding=ROUND_CEILING))


def _f(d, places=6):
    return None if d is None else float(round(d, places))


def risers_for(floor_height, max_riser):
    """rule steps 1-2 on decimals (m): -> (risers, actual_riser)."""
    n = max(_ceil(floor_height / max_riser), 1)
    return n, floor_height / n


def arrangements(risers, tread, landing_depth):
    """rule steps 3-4: the single flight and the U arrangement (U is None below 2 risers: no second flight)."""
    single = {"type": SINGLE, "flights": [risers], "treads": risers - 1,
              "treads_per_flight": [risers - 1], "required_length": (risers - 1) * tread, "landings": 0}
    if risers < 2:
        return single, None
    f1 = int((Decimal(risers) / 2).to_integral_value(rounding=ROUND_CEILING))
    f2 = int((Decimal(risers) / 2).to_integral_value(rounding=ROUND_FLOOR))
    u = {"type": U_TYPE, "flights": [f1, f2], "treads": risers - 2, "treads_per_flight": [f1 - 1, f2 - 1],
         "required_length": (f1 - 1) * tread + landing_depth, "landings": 1}
    return single, u


def fit(single, u, available_length):
    """rule step 5 -> (result, chosen arrangement or None, needs_at_least)."""
    if available_length is None:
        return NOT_CHECKED, None, None
    if single["required_length"] <= available_length + TOL:
        return FITS_SINGLE, single, None
    if u is not None and u["required_length"] <= available_length + TOL:
        return FITS_U, u, None
    need = min(a["required_length"] for a in (single, u) if a is not None)
    return DOES_NOT_FIT, None, need


def _warnings(actual_riser, tread, unit_note=""):
    w = []
    if actual_riser > RISER_LIMIT + TOL:
        w.append({"code": "RISER_ABOVE_LIMIT", "value_m": _f(actual_riser), "limit_m": float(RISER_LIMIT),
                  "text": f"actual riser {_f(actual_riser, 4)} m > {RISER_LIMIT} m (rule step 6)"})
    if tread is not None and tread < TREAD_MIN - TOL:
        w.append({"code": "TREAD_BELOW_MIN", "value_m": _f(tread), "limit_m": float(TREAD_MIN),
                  "text": f"tread {_f(tread, 4)} m < {TREAD_MIN} m (rule step 6)"})
    if tread is not None and tread > TREAD_MAX + TOL:
        w.append({"code": "TREAD_ABOVE_ALLOWED_RANGE", "value_m": _f(tread), "limit_m": float(TREAD_MAX),
                  "text": f"tread {_f(tread, 4)} m outside the allowed 0.28 - 0.30 m (rule terms)"})
    return w


def _view(a):
    if a is None:
        return None
    return {"type": a["type"], "flights": list(a["flights"]), "treads": a["treads"],
            "treads_per_flight": list(a["treads_per_flight"]), "required_length_m": _f(a["required_length"]),
            "landings": a["landings"]}


def _line(item, unit, qty, status, cause=None, candidates=None, formula=""):
    rec = {"item": item, "unit": unit, "quantity": qty if status != HELD else None, "status": status,
           "rule": RULE_ID, "rule_set": RULE_SET, "source": SOURCE, "formula": formula}
    if status == HELD:
        rec["held_cause"] = cause
        rec["candidates"] = candidates or {}
    return rec


def design(floor_height, stair_width, available_length=None, max_riser=None, tread=None,
           landing_depth=None, tread_buildup=None, unit="m"):
    """the owner method for an UNDRAWN stair (owner S-1). Returns the counts, both arrangements, the fit result,
    the warnings and the BOQ lines (UP-STAIR-004: m2, nr and m kept as separate lines, never summed)."""
    H = _dec(floor_height, "floor_height", unit)
    W = _dec(stair_width, "stair_width", unit)
    mr = DEFAULT_MAX_RISER if max_riser is None else _dec(max_riser, "max_riser", unit)
    t = DEFAULT_TREAD if tread is None else _dec(tread, "tread", unit)
    ld = W if landing_depth is None else _dec(landing_depth, "landing_depth", unit)
    L = None if available_length is None else _dec(available_length, "available_length", unit, allow_zero=True)
    b = TREAD_BUILDUP if tread_buildup is None else _dec(tread_buildup, "tread_buildup", unit, allow_zero=True)

    n, h = risers_for(H, mr)
    single, u = arrangements(n, t, ld)
    result, chosen, need = fit(single, u, L)
    warnings = _warnings(h, t)
    if result == DOES_NOT_FIT:
        warnings.append({"code": "NOT_ENOUGH_SPACE", "needs_at_least_m": _f(need), "available_m": _f(L),
                         "text": f"space is not enough, needs at least {_f(need, 2):.2f} m (rule step 5)",
                         "text_ar": f"المساحة ما تكفي، تحتاج على الأقل {_f(need, 2):.2f} م"})
    visible = h - b
    if visible <= 0:
        raise StairRuleError(f"tread build-up {b} m leaves no visible riser on an actual riser of {h} m")

    def by_type(fn):
        return {a["type"]: _f(fn(a)) for a in (single, u) if a is not None}

    if result == DOES_NOT_FIT:
        all_cause, type_cause = "STAIR_DOES_NOT_FIT", "STAIR_DOES_NOT_FIT"
    elif result == NOT_CHECKED:
        all_cause, type_cause = None, "AVAILABLE_LENGTH_NOT_GIVEN"
    else:
        all_cause, type_cause = None, None

    def status(type_dependent):
        if all_cause or (type_dependent and type_cause):
            return HELD, all_cause or type_cause
        return ASSUMED, None

    lines = []
    st, cause = status(False)
    lines.append(_line("riser pieces", "nr", n, st, cause, {"ANY": n}, "risers = ceil(H / max_riser)"))
    lines.append(_line("riser cladding (visible riser)", "m2", _f(n * visible * W), st, cause,
                       {"ANY": _f(n * visible * W)},
                       "risers x (actual_riser - tread build-up) x stair_width (S-2, UP-STAIR-003 / -006)"))
    st, cause = status(True)
    tq = chosen["treads"] if chosen else None
    lines.append(_line("tread pieces", "nr", tq, st, cause, by_type(lambda a: a["treads"]),
                       "single: risers - 1; U: risers - 2"))
    lines.append(_line("tread cladding", "m2", _f(tq * t * W) if chosen else None, st, cause,
                       by_type(lambda a: a["treads"] * t * W), "treads x tread x stair_width"))
    landing_m2 = ld * 2 * W
    if chosen is not None and chosen["type"] == SINGLE:
        landing = {"item": "mid landing", "unit": "m2", "quantity": None, "status": "NOT_APPLICABLE",
                   "rule": RULE_ID, "rule_set": RULE_SET, "source": SOURCE,
                   "formula": "a single straight flight has no mid landing"}
    else:
        cand = {U_TYPE: _f(landing_m2)} if u is not None else {}
        if chosen is not None:      # U chosen
            landing = _line("mid landing", "m2", _f(landing_m2), ASSUMED, formula="landing_depth x (2 x stair_width)")
        else:
            landing = _line("mid landing", "m2", None, HELD, type_cause, cand, "landing_depth x (2 x stair_width)")
    lines.append(landing)

    return {"rule": RULE_ID, "rule_set": RULE_SET, "mode": "DESIGN (undrawn stair, owner S-1)",
            "inputs_m": {"floor_height": _f(H), "stair_width": _f(W), "available_length": _f(L),
                         "max_riser": _f(mr), "tread": _f(t), "landing_depth": _f(ld), "tread_buildup": _f(b)},
            "risers": n, "actual_riser_m": _f(h), "visible_riser_m": _f(visible),
            "single": _view(single), "u": _view(u),
            "fit": result, "stair_type": chosen["type"] if chosen else None,
            "treads": tq, "required_length_m": _f(chosen["required_length"]) if chosen else None,
            "needs_at_least_m": _f(need), "warnings": warnings, "lines": lines}


def check_drawn(floor_height, drawn_risers, drawn_treads=None, drawn_tread_depth=None, drawn_flights=1,
                drawn_riser_heights=None, max_riser=None, unit="m"):
    """owner S-1: the drawing governs; the rule CHECKS it. Returns findings only (never a quantity)."""
    H = _dec(floor_height, "floor_height", unit)
    mr = DEFAULT_MAX_RISER if max_riser is None else _dec(max_riser, "max_riser", unit)
    if isinstance(drawn_risers, bool) or not isinstance(drawn_risers, int) or drawn_risers < 1:
        raise StairRuleError(f"drawn_risers must be a whole number >= 1 (got {drawn_risers!r})")
    if isinstance(drawn_flights, bool) or not isinstance(drawn_flights, int) or not 1 <= drawn_flights <= drawn_risers:
        raise StairRuleError(f"drawn_flights must be a whole number in 1 .. drawn_risers (got {drawn_flights!r})")
    t = None if drawn_tread_depth is None else _dec(drawn_tread_depth, "drawn_tread_depth", unit)
    rule_n, rule_h = risers_for(H, mr)
    drawn_h = H / drawn_risers
    findings = []
    if drawn_risers != rule_n:
        findings.append({"code": "RISER_COUNT_DIFFERS", "drawn": drawn_risers, "rule": rule_n,
                         "text": f"drawn {drawn_risers} risers, the rule gives {rule_n} (ceil(H / {mr}))"})
    for w in _warnings(drawn_h, t):
        findings.append(dict(w, code="DRAWN_" + w["code"]))
    expected_treads = drawn_risers - drawn_flights
    if drawn_treads is not None:
        if isinstance(drawn_treads, bool) or not isinstance(drawn_treads, int) or drawn_treads < 0:
            raise StairRuleError(f"drawn_treads must be a whole number >= 0 (got {drawn_treads!r})")
        if drawn_treads != expected_treads:
            findings.append({"code": "TREAD_COUNT_INCONSISTENT", "drawn": drawn_treads, "expected": expected_treads,
                             "text": f"drawn {drawn_treads} treads; {drawn_risers} risers in {drawn_flights} "
                                     f"flight(s) give {expected_treads} (rule steps 3 / 4 / 7)"})
    if drawn_riser_heights is not None:
        hs = [_dec(x, "drawn_riser_heights", unit) for x in drawn_riser_heights]
        if len(hs) != drawn_risers:
            findings.append({"code": "RISER_HEIGHT_LIST_COUNT_DIFFERS", "listed": len(hs), "drawn": drawn_risers})
        if hs and max(hs) - min(hs) > TOL:
            findings.append({"code": "NON_UNIFORM_RISERS", "min_m": _f(min(hs)), "max_m": _f(max(hs)),
                             "text": "rule step 2: all risers equal"})
        if hs and abs(sum(hs) - H) > TOL * len(hs):
            findings.append({"code": "RISER_SUM_DIFFERS_FROM_FLOOR_HEIGHT", "sum_m": _f(sum(hs)), "floor_height_m": _f(H)})
        for x in hs:
            if x > RISER_LIMIT + TOL:
                findings.append({"code": "DRAWN_RISER_ABOVE_LIMIT_LISTED", "value_m": _f(x), "limit_m": float(RISER_LIMIT)})
                break
    return {"rule": RULE_ID, "rule_set": RULE_SET, "mode": "CHECK (drawn stair, owner S-1: the drawing governs)",
            "governs": "DRAWING", "kept": {"risers": drawn_risers, "treads": drawn_treads, "flights": drawn_flights,
                                           "tread_depth_m": _f(t)},
            "drawn_actual_riser_m": _f(drawn_h), "rule_risers": rule_n, "rule_actual_riser_m": _f(rule_h),
            "rule_treads_for_drawn_flights": rule_n - drawn_flights,
            "findings": findings, "flagged": bool(findings), "quantities": None,
            "note": "a check result only: the drawn counts are kept, nothing here is a BOQ quantity"}
