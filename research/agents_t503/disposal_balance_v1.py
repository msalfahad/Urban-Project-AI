"""DISPOSAL_BALANCE_V1 (T-503, lane S, research, unwired, stdlib only): the B1-04 DISPOSAL quantity as ONE explicit
material balance over the earthworks lines of a candidate, every term bound to a line id, with the suitable share,
the densities and the bulking each a separate sourced fact. Rule R-T503-1 (every villa).

PHYSICAL ELEMENT (ERS s.2.1): disposal is the excavated soil that leaves the site = every in-situ m3 excavated minus
the in-situ m3 of SUITABLE excavated soil placed back as compacted fill (backfill round the buried structure and any
placed fill, e.g. a raised fill under the ground slab). Imported fill is the compacted fill demand that the re-used
soil does not cover. Both come from the same balance, never separately (owner 2026-11-02 17:20 (2), 17:45 (4)):

    k                 = rho_target / rho_insitu            in-situ m3 of soil per compacted m3 (dry-mass conservation)
    reused_insitu     = min(s x E, k x D)                  s = suitable share (geotechnical evidence only)
    disposal_insitu   = E - reused_insitu                  payable basis IN SITU unless the contract says loose
    import_compacted  = D - reused_insitu / k              (= D when s = 0, whatever k)
    import_dry_t      = import_compacted x rho_target      procurement from the PLACEMENT TARGET, never acceptance
    import_loose_m3   = import_dry_t / rho_loose_import    (a delivered loose density, its own fact)
    disposal_loose_m3 = disposal_insitu x bulking          bulking only MEASURED (or measured rho_insitu / rho_loose)
    truckloads        = ceil(loose / capacity)             logistics only, never a quantity

E (excavation, in-situ m3) and D (compacted fill demand, m3) are sums of candidate lines, each VALUED (one figure),
RANGED (low .. high) or HELD (blank). The result is a RANGE over the parameter box, each end evaluated at its own
extreme (disposal rises with E and falls with s, k, D; import rises with D and k and falls with s and E):

    disposal high = f(E_high, D_low,  s_low,  k)       disposal low = f(E_low, D_high, s_high, k)
    import   high = g(D_high, E_low,  s_low,  k)       import   low = g(D_low, E_high, s_high, k)

The E and D ranges are treated as independent (an outer envelope, named); no end is picked because it is larger.
Without geotechnical evidence s is the bound 0 .. 1 (never a default share): the s = 0 end (no suitable soil) needs
no density and is pure geometry; the s > 0 end needs k and stays HELD, naming the missing inputs, until both densities
exist. A HELD line makes the sums OPEN (the known part is a lower bound: zones are disjoint, R-T497, and never
negative); an end whose direction an open sum cannot bound (opposite qualifiers, or a LOW end bounded only from above) is HELD; an AT_LEAST 0 is HELD (no information). A zero
is reported only as a CALCULATED zero with every term closed. Missing never becomes 0. Nothing names a project.
"""
from __future__ import annotations

import math

METHOD_ID = "DISPOSAL_BALANCE_V1"
RULE_ID, RULE_VERSION = "R-T503-1", "1.0.0"
DC, MEAS, CALC = "DRAWING-CONFIRMED", "MEASURED", "CALCULATED"
EST, SPEC, PV, HELD = "ESTIMATED", "PROPOSED-SPEC", "PARTIALLY VERIFIED", "HELD"
GEOTECH = "GEOTECHNICAL"                       # a suitability fact: only from geotechnical evidence
_RANK = {DC: 0, MEAS: 0, CALC: 0, GEOTECH: 0, PV: 1, EST: 1, SPEC: 1, HELD: 2}
EXC, FILL = "EXCAVATION_INSITU", "FILL_COMPACTED"
EXACT, AT_LEAST, AT_MOST = "EXACT", "AT_LEAST", "AT_MOST"
IN_SITU, LOOSE = "IN_SITU", "LOOSE"
_DENS_UNIT = {"t/m3": 1.0, "kg/m3": 0.001}
RHO_MIN, RHO_MAX = 0.8, 2.8                   # t/m3: a unit guard on soil dry densities, not a value
TOL = 1e-6


class Refused(ValueError):
    def __init__(self, code, msg=""):
        super().__init__(f"{code}: {msg}" if msg else code)
        self.code = code


def _r(x, n=6):
    return None if x is None else round(x + 0.0, n)


def _base(status):
    if status is None:
        return HELD
    return PV if str(status).startswith(PV) else status


def worst(*st):
    st = [_base(s) for s in st if s]
    for s in st:
        if s not in _RANK:
            raise Refused("UNKNOWN_STATUS", repr(s))
    return max(st, key=lambda s: _RANK[s]) if st else HELD


# ================================================================================================ facts
def term(line_id, role, low=None, high=None, status=HELD, zone=None, held_parts=()):
    """One candidate line in the balance. VALUED: low == high; RANGED: low < high; HELD: both None (blank)."""
    if not line_id or not str(line_id).startswith("L-"):
        raise Refused("UNBOUND_TERM", f"every term is a candidate line id, got {line_id!r}")
    if role not in (EXC, FILL):
        raise Refused("UNKNOWN_ROLE", repr(role))
    worst(status)
    if (low is None) != (high is None):
        raise Refused("HALF_RANGE", f"{line_id}: a range needs both ends or none")
    if low is None:
        if _base(status) != HELD:
            raise Refused("BLANK_NOT_HELD", f"{line_id}: a blank line must be HELD")
    else:
        low, high = float(low), float(high)
        if low < -TOL or high < low - TOL:
            raise Refused("BAD_RANGE", f"{line_id}: {low} .. {high}")
        if _base(status) == HELD and low == high:
            raise Refused("HELD_AS_VALUE", f"{line_id}: a HELD status with one figure")
    return {"line_id": line_id, "role": role, "low": low, "high": high, "status": status, "zone": zone,
            "held_parts": list(held_parts)}


def density(value, status, source=None, kind=None, unit="t/m3"):
    """A dry density fact. kind: INSITU / PLACEMENT_TARGET / LOOSE_IMPORT / LOOSE_SPOIL / ACCEPTANCE."""
    if unit not in _DENS_UNIT:
        raise Refused("UNIT_NOT_DECLARED", repr(unit))
    if status == HELD or value is None:
        if value is not None:
            raise Refused("HELD_AS_VALUE", repr(value))
        return {"value": None, "status": HELD, "source": source, "kind": kind}
    worst(status)
    if not source:
        raise Refused("DENSITY_WITHOUT_SOURCE", f"{kind} {value}")
    v = float(value) * _DENS_UNIT[unit]
    if not RHO_MIN <= v <= RHO_MAX:
        raise Refused("DENSITY_UNIT", f"{kind} {v} t/m3 outside {RHO_MIN} .. {RHO_MAX}: wrong unit?")
    return {"value": v, "status": status, "source": source, "kind": kind}


def suitability(low=None, high=None, status=HELD, source=None):
    """Suitable share of the excavated soil. Only geotechnical evidence fixes it; without it the bound is 0 .. 1
    (status HELD), never a default share. A drawing note naming the fill source is design intent, not suitability."""
    if status == HELD:
        if low is not None or high is not None:
            raise Refused("HELD_AS_VALUE", "suitability HELD carries no share")
        return {"low": 0.0, "high": 1.0, "status": HELD, "source": source or "no geotechnical evidence: bound 0 .. 1",
                "evidence": False}
    if status != GEOTECH:
        raise Refused("SUITABILITY_NOT_GEOTECHNICAL", f"{status}: suitability only from geotechnical evidence")
    if not source or low is None:
        raise Refused("SUITABILITY_WITHOUT_EVIDENCE", repr(source))
    high = low if high is None else high
    if not 0.0 <= low <= high <= 1.0:
        raise Refused("BAD_SHARE", f"{low} .. {high}")
    return {"low": float(low), "high": float(high), "status": GEOTECH, "source": source, "evidence": True}


def bulking(factor=None, status=HELD, source=None):
    """Loose / in-situ volume ratio of the spoil: MEASURED only (owner 17:45 (4)); a published or estimated factor
    is refused (no universal swell factor)."""
    if status == HELD or factor is None:
        return {"value": None, "status": HELD, "source": source}
    if status != MEAS:
        raise Refused("BULKING_NOT_MEASURED", f"{status}: loose m3 only from measured bulking")
    if not source or not 1.0 <= float(factor) <= 2.0:
        raise Refused("BAD_BULKING", f"{factor!r} / {source!r}")
    return {"value": float(factor), "status": MEAS, "source": source}


# ================================================================================================ sums
def _sum(terms, role):
    ts = [t for t in terms if t["role"] == role]
    closed = [t for t in ts if t["low"] is not None]
    held = [t for t in ts if t["low"] is None]
    parts = [f"{t['line_id']}: {p}" for t in closed for p in t["held_parts"]]
    return {"low": _r(sum(t["low"] for t in closed)), "high": _r(sum(t["high"] for t in closed)),
            "open": bool(held), "held_lines": [t["line_id"] for t in held], "held_parts": parts,
            "lines": [t["line_id"] for t in ts], "status": worst(*[t["status"] for t in closed]) if closed else HELD}


def _end(value, qual, status, missing, scenario, zero_ok=True):
    if value is None or (qual == "HELD"):
        return {"value": None, "qualifier": "HELD", "status": HELD, "missing": missing, "scenario": scenario}
    if qual == AT_LEAST and value <= TOL:
        return {"value": None, "qualifier": "HELD", "status": HELD,
                "missing": missing + ["AT_LEAST 0 carries no information"], "scenario": scenario}
    out = {"value": _r(max(value, 0.0)), "qualifier": qual, "status": status, "missing": missing, "scenario": scenario}
    if out["value"] == 0.0:
        out["calculated_zero"] = True
    return out


def _combine(*q):
    q = {x for x in q if x != EXACT}
    if not q:
        return EXACT
    return q.pop() if len(q) == 1 else "HELD"


def _disposal(E, Eopen, D, Dopen, s, k, st, scenario, missing_k):
    """disposal = E - min(sE, kD). E open -> AT_LEAST (rises with E); D open -> AT_MOST unless supply-bound."""
    if s == 0.0:
        return _end(E, AT_LEAST if Eopen else EXACT, st, [], scenario)
    if k is None:
        return _end(None, "HELD", HELD, missing_k, scenario)
    sup, dem = s * E, k * D
    qd = EXACT if (not Dopen or sup <= dem) else AT_MOST
    qe = AT_LEAST if Eopen else EXACT
    q = _combine(qe, qd)
    return _end(E - min(sup, dem), q, st, missing_k if q == "HELD" else [], scenario)


def _import(D, Dopen, E, Eopen, s, k, st, scenario, missing_k):
    """import (compacted) = D - min(sE, kD) / k. D open -> AT_LEAST; E open -> AT_MOST unless demand-bound."""
    if s == 0.0:
        return _end(D, AT_LEAST if Dopen else EXACT, st, [], scenario)
    if k is None:
        return _end(None, "HELD", HELD, missing_k, scenario)
    sup, dem = s * E, k * D
    qd = AT_LEAST if Dopen else EXACT
    qe = EXACT if (not Eopen or sup >= dem) else AT_MOST
    q = _combine(qd, qe)
    return _end(D - min(sup, dem) / k, q, st, missing_k if q == "HELD" else [], scenario)


# ================================================================================================ balance
def balance(terms, rho_insitu, rho_target, suit, rho_loose_import=None, bulk=None, contract_basis=None,
            truck_capacity_m3=None, rho_acceptance=None):
    """The B1-04 balance. Returns the E and D sums, the disposal and import ranges (each end with its value,
    qualifier, status, missing inputs and scenario), loose / payable / truckloads beside, and the conservation
    check at every computed end."""
    ids = [t["line_id"] for t in terms]
    if len(ids) != len(set(ids)):
        raise Refused("TERM_TWICE", "a candidate line enters the balance once")
    if not any(t["role"] == EXC for t in terms):
        raise Refused("NO_EXCAVATION", "a disposal balance needs excavation lines")
    if rho_target and rho_target.get("kind") == "ACCEPTANCE":
        raise Refused("ACCEPTANCE_DENSITY_AS_PROCUREMENT", "the placement target is its own fact")
    if rho_acceptance and rho_target and rho_target.get("value") is not None and (
            rho_target is rho_acceptance or (rho_target.get("source") == rho_acceptance.get("source"))):
        raise Refused("ACCEPTANCE_DENSITY_AS_PROCUREMENT", "procurement uses the placement target density")
    if rho_insitu and rho_insitu.get("value") is not None and rho_insitu["status"] != MEAS:
        raise Refused("INSITU_DENSITY_NOT_MEASURED", "the in-situ dry density is a measured soil property")
    if contract_basis not in (None, IN_SITU, LOOSE):
        raise Refused("UNKNOWN_CONTRACT_BASIS", repr(contract_basis))
    Es, Ds = _sum(terms, EXC), _sum(terms, FILL)
    if Es["low"] is None or (Es["low"] == 0 and Es["open"] and not Es["high"]):
        raise Refused("NO_EXCAVATION_QUANTITY", "every excavation line is HELD: nothing to balance")
    ri, rt = (rho_insitu or {}).get("value"), (rho_target or {}).get("value")
    k = None if ri is None or rt is None else rt / ri
    missing_k = [n for n, v in (("in-situ dry density (MEASURED, e.g. field density test of the excavated "
                                 "soil)", ri), ("placement target dry density of the fill (its own field and "
                                                "source)", rt)) if v is None]
    s_lo, s_hi = suit["low"], suit["high"]
    Ds0 = _sum(terms, FILL)
    if not suit["evidence"]:
        missing_k = missing_k + ["suitable share of the excavated soil (geotechnical classification against the "
                                 "fill specification; bound 0 .. 1 meanwhile)"]
    if Ds0["open"]:
        missing_k = missing_k + [f"fill demand of the HELD fill lines {' '.join(Ds0['held_lines'])} (each can draw "
                                 f"site soil)"]
    if Es_open_lines := _sum(terms, EXC)["held_lines"]:
        missing_k = missing_k + [f"excavation of the HELD lines {' '.join(Es_open_lines)}"]
    st = worst(Es["status"], Ds["status"] if Ds["lines"] else None)
    stk = worst(st, (rho_insitu or {}).get("status"), (rho_target or {}).get("status"), suit["status"]
                if suit["evidence"] else None)
    Dlo = Ds["low"] if Ds["low"] is not None else 0.0      # a fill sum with every line HELD is fully OPEN
    Dhi = Ds["high"] if Ds["high"] is not None else 0.0
    Dopen = Ds["open"]
    sc_hi = f"suitable share {s_lo:g} (excavation high, fill low)"
    sc_lo = f"suitable share {s_hi:g} (excavation low, fill high)"
    if Dopen and not Ds["low"] and s_hi > 0 and k is not None:
        dl_lo = _end(None, "HELD", HELD, missing_k + ["every fill line HELD: the re-use cannot be bounded"], sc_lo)
    else:
        dl_lo = _disposal(Es["low"], Es["open"], Dhi, Dopen, s_hi, k, stk if s_hi else st, sc_lo, missing_k)
    dl_hi = _disposal(Es["high"], Es["open"], Dlo, Dopen, s_lo, k, stk if s_lo else st, sc_hi, missing_k)
    im_hi = _import(Dhi, Dopen, Es["low"], Es["open"], s_lo, k, stk if s_lo else st,
                    f"suitable share {s_lo:g} (fill high, excavation low)", missing_k)
    im_lo = _import(Dlo, Dopen, Es["high"], Es["open"], s_hi, k, stk if s_hi else st,
                    f"suitable share {s_hi:g} (fill low, excavation high)", missing_k)
    # a LOW end that an open sum bounds only from above ("at most") bounds nothing: HELD with the missing inputs
    if dl_lo["qualifier"] == AT_MOST:
        dl_lo = _end(None, "HELD", HELD, missing_k, sc_lo)
    if im_lo["qualifier"] == AT_MOST:
        im_lo = _end(None, "HELD", HELD, missing_k, im_lo["scenario"])
    if not Ds["lines"]:
        im_hi = im_lo = _end(None, "HELD", HELD, ["no fill line in the balance"], "no fill demand bound")
    for a, b, what in ((dl_lo, dl_hi, "disposal"), (im_lo, im_hi, "import")):
        if a["value"] is not None and b["value"] is not None and a["value"] > b["value"] + TOL:
            raise AssertionError(f"{what}: low end {a['value']} above high end {b['value']}")
    out ={"method": METHOD_ID, "rule": f"{RULE_ID} {RULE_VERSION}", "excavation": Es, "fill_demand": Ds,
           "k_insitu_per_compacted": _r(k), "suitable_share": suit,
           "disposal_insitu_m3": {"low": dl_lo, "high": dl_hi},
           "import_compacted_m3": {"low": im_lo, "high": im_hi}}
    out["state"] = ("VALUED" if all(e["qualifier"] == EXACT for e in (dl_lo, dl_hi)) and
                    dl_lo["value"] == dl_hi["value"] else
                    "BOUNDED" if all(e["value"] is not None for e in (dl_lo, dl_hi)) else "HELD_RANGE")
    out["single_number"] = out["state"] == "VALUED"
    # beside the quantity: dry mass, loose, payable, logistics
    imp = {}
    for side, e in (("low", im_lo), ("high", im_hi)):
        if e["value"] is None or rt is None:
            imp[side] = {"dry_t": None, "loose_m3": None, "missing": e["missing"] + ([] if rt else missing_k[-1:])}
            continue
        dry = e["value"] * rt
        rl = (rho_loose_import or {}).get("value")
        imp[side] = {"dry_t": _r(dry), "loose_m3": _r(dry / rl) if rl else None, "qualifier": e["qualifier"],
                     "missing": [] if rl else ["loose delivered dry density of the import (its own fact)"]}
    out["import_material"] = imp
    bf = (bulk or {}).get("value")
    loose = {}
    for side, e in (("low", dl_lo), ("high", dl_hi)):
        loose[side] = (None if e["value"] is None or bf is None else _r(e["value"] * bf))
    out["disposal_loose_m3"] = {"low": loose["low"], "high": loose["high"],
                                "missing": [] if bf else ["MEASURED bulking of the spoil (loose / in-situ)"]}
    basis = contract_basis or IN_SITU
    out["payable"] = {"basis": basis, "basis_source": "contract" if contract_basis else "contract silent: in situ",
                      "low": dl_lo["value"] if basis == IN_SITU else loose["low"],
                      "high": dl_hi["value"] if basis == IN_SITU else loose["high"]}
    if basis == LOOSE and bf is None:
        out["payable"]["missing"] = ["contract measures loose: MEASURED bulking HELD"]
    if truck_capacity_m3:
        out["truckloads_logistics_only"] = {s: (None if loose[s] is None else
                                                math.ceil(loose[s] / float(truck_capacity_m3) - 1e-9))
                                            for s in ("low", "high")}
    # conservation check at every end evaluated with a closed k (dry mass in = dry mass out)
    out["conservation"] = []
    if k is not None:
        for (E, D, s) in ((Es["low"], Dhi, s_hi), (Es["high"], Dlo, s_lo)):
            reused = min(s * E, k * D)
            disp, imp_c = E - reused, D - reused / k
            lhs = E * ri
            rhs = disp * ri + reused * ri
            fill_mass = D * rt
            got = reused * ri + imp_c * rt
            if abs(lhs - rhs) > TOL or abs(fill_mass - got) > TOL:
                raise AssertionError("dry-mass conservation broken")
            out["conservation"].append({"E": _r(E), "D": _r(D), "s": s, "reused_insitu_m3": _r(reused),
                                        "closes": True})
    return out


def describe_end(e, unit="m3"):
    if e["value"] is None:
        return f"HELD ({'; '.join(e['missing'])})"
    q = {"EXACT": "", "AT_LEAST": "at least ", "AT_MOST": "at most "}[e["qualifier"]]
    return f"{q}{e['value']:.6f} {unit} [{e['status']}]"
